"""
Live article ingestion and in-memory retrieval store.

This keeps the current architecture (stateless API + RAG), while adding
automatic web ingestion so chat/news endpoints can use fresher context.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from news_sources import fetch_from_guardian, fetch_from_newsapi, fetch_from_rss, get_test_articles

logger = logging.getLogger(__name__)

# In-memory cache (can be replaced with Cloud SQL/Redis later).
_ARTICLES: List[Dict] = []
_LAST_INGEST_AT: Optional[datetime] = None
_INGEST_META: Dict = {
    "total_articles": 0,
    "sources": {},
    "last_run_status": "never",
    "last_error": None,
    "progress": {
        "state": "idle",
        "run_id": None,
        "current_stage": "idle",
        "stages": ["fetching", "cleansing", "indexing", "completed"],
        "completed_stages": [],
        "percent": 0,
        "total_batches": 0,
        "processed_batches": 0,
        "fetched_articles": 0,
        "deduped_articles": 0,
        "indexed_articles": 0,
        "active_region": None,
        "active_topic": None,
        "started_at": None,
        "updated_at": None,
        "completed_at": None,
    },
}
_LOCK = asyncio.Lock()
_INGESTION_MUTEX = asyncio.Lock()

TOPIC_MAP = {
    "Finance": "Business",
    "Tech": "Technology",
}

DEFAULT_TOPICS = ["Politics", "Business", "Technology", "Sports", "General"]
DEFAULT_REGIONS = ["India", "Global"]
STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "what", "latest", "today",
    "news", "headline", "headlines", "update", "updates", "india", "global",
    "from", "about", "into", "over", "under", "your", "have", "has",
}
TOPIC_HINTS = {
    "Technology": {"tech", "technology", "ai", "artificial", "software", "startup", "semiconductor"},
    "Business": {"finance", "business", "economy", "economic", "market", "markets", "stock", "stocks", "trade"},
    "Politics": {"politics", "political", "government", "policy", "parliament", "election", "budget"},
    "Sports": {"sports", "sport", "cricket", "football", "ipl", "match", "olympic"},
}


def normalize_topic(topic: Optional[str]) -> Optional[str]:
    if not topic:
        return None
    if topic in {"All", "World", "General"}:
        return None
    return TOPIC_MAP.get(topic, topic)


def _tokenize(text: Optional[str]) -> List[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def infer_topic_from_query(query: Optional[str]) -> Optional[str]:
    tokens = _tokenize(query)
    if not tokens:
        return None

    best_topic = None
    best_score = 0
    for topic, hints in TOPIC_HINTS.items():
        score = sum(1 for token in tokens if token in hints)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic if best_score > 0 else None


def _article_key(article: Dict) -> str:
    url = (article.get("url") or "").strip().lower()
    if url:
        return url
    title = (article.get("title") or "").strip().lower()
    source = (article.get("source") or "").strip().lower()
    return f"{source}|{title}"


def _dedupe_articles(articles: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for item in articles:
        key = _article_key(item)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


async def _fetch_for_region_topic(region: str, topic: str, limit: int) -> List[Dict]:
    merged: List[Dict] = []
    sources_hit = []

    # Keep fast source first.
    rss_articles = await fetch_from_rss(region=region, topic=topic, limit=limit)
    if rss_articles:
        merged.extend(rss_articles)
        sources_hit.append("rss")

    # Add API sources if configured.
    newsapi_articles = await fetch_from_newsapi(region=region, topic=topic, limit=limit)
    if newsapi_articles:
        merged.extend(newsapi_articles)
        sources_hit.append("newsapi")

    guardian_articles = await fetch_from_guardian(region=region, topic=topic, limit=limit)
    if guardian_articles:
        merged.extend(guardian_articles)
        sources_hit.append("guardian")

    if not merged:
        # Safe fallback for local/dev continuity.
        merged = get_test_articles(region=region, topic=topic, limit=limit)
        if not merged:
            # Some datasets use specific topic names only; allow all topics fallback.
            merged = get_test_articles(region=region, topic=None, limit=limit)
        sources_hit.append("test")

    logger.info(
        f"Ingestion fetch region={region} topic={topic}: {len(merged)} raw articles from {sources_hit}"
    )
    return merged


async def ingest_from_web(
    regions: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    limit_per_fetch: int = 12,
) -> Dict:
    """Fetch fresh articles from web sources and replace cache."""
    global _ARTICLES, _LAST_INGEST_AT, _INGEST_META

    async with _INGESTION_MUTEX:
        regions = regions or DEFAULT_REGIONS
        topics = topics or DEFAULT_TOPICS
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat()
        total_batches = len(regions) * len(topics)

        try:
            fetched: List[Dict] = []
            source_counts: Dict[str, int] = {}

            async with _LOCK:
                _INGEST_META["last_run_status"] = "running"
                _INGEST_META["last_error"] = None
                _INGEST_META["progress"] = {
                    "state": "running",
                    "run_id": run_id,
                    "current_stage": "fetching",
                    "stages": ["fetching", "cleansing", "indexing", "completed"],
                    "completed_stages": [],
                    "percent": 5,
                    "total_batches": total_batches,
                    "processed_batches": 0,
                    "fetched_articles": 0,
                    "deduped_articles": 0,
                    "indexed_articles": 0,
                    "active_region": None,
                    "active_topic": None,
                    "started_at": started_at,
                    "updated_at": started_at,
                    "completed_at": None,
                }

            for region_index, region in enumerate(regions):
                for topic_index, topic in enumerate(topics):
                    batch = await _fetch_for_region_topic(region, topic, limit_per_fetch)
                    fetched.extend(batch)
                    for article in batch:
                        source_name = article.get("source", "Unknown")
                        source_counts[source_name] = source_counts.get(source_name, 0) + 1

                    processed_batches = (region_index * len(topics)) + topic_index + 1
                    percent = 5 + int((processed_batches / max(total_batches, 1)) * 60)
                    async with _LOCK:
                        _INGEST_META["progress"].update({
                            "current_stage": "fetching",
                            "processed_batches": processed_batches,
                            "fetched_articles": len(fetched),
                            "active_region": region,
                            "active_topic": topic,
                            "percent": min(percent, 70),
                            "updated_at": datetime.utcnow().isoformat(),
                        })

            async with _LOCK:
                _INGEST_META["progress"].update({
                    "current_stage": "cleansing",
                    "completed_stages": ["fetching"],
                    "percent": 78,
                    "updated_at": datetime.utcnow().isoformat(),
                })

            deduped = _dedupe_articles(fetched)
            deduped.sort(key=lambda x: x.get("published_at", ""), reverse=True)

            async with _LOCK:
                _INGEST_META["progress"].update({
                    "current_stage": "indexing",
                    "completed_stages": ["fetching", "cleansing"],
                    "deduped_articles": len(deduped),
                    "percent": 90,
                    "updated_at": datetime.utcnow().isoformat(),
                })

            indexed_articles = len(deduped)
            completed_at = datetime.utcnow().isoformat()
            async with _LOCK:
                _ARTICLES = deduped
                _LAST_INGEST_AT = datetime.utcnow()
                _INGEST_META["total_articles"] = len(deduped)
                _INGEST_META["sources"] = source_counts
                _INGEST_META["last_run_status"] = "success"
                _INGEST_META["last_error"] = None
                _INGEST_META["progress"].update({
                    "state": "success",
                    "current_stage": "completed",
                    "completed_stages": ["fetching", "cleansing", "indexing", "completed"],
                    "percent": 100,
                    "indexed_articles": indexed_articles,
                    "active_region": None,
                    "active_topic": None,
                    "completed_at": completed_at,
                    "updated_at": completed_at,
                })

            logger.info(f"Ingestion complete: {len(deduped)} deduped articles")
            return get_ingestion_snapshot()
        except Exception as exc:
            logger.error(f"Ingestion failed: {str(exc)}", exc_info=True)
            failed_at = datetime.utcnow().isoformat()
            async with _LOCK:
                _INGEST_META["last_run_status"] = "failed"
                _INGEST_META["last_error"] = str(exc)
                _INGEST_META["progress"].update({
                    "state": "failed",
                    "current_stage": "failed",
                    "updated_at": failed_at,
                    "completed_at": failed_at,
                })
            return get_ingestion_snapshot()


def get_ingestion_snapshot() -> Dict:
    return {
        "last_ingest_at": _LAST_INGEST_AT.isoformat() if _LAST_INGEST_AT else None,
        **_INGEST_META,
    }


def is_cache_stale(max_age_minutes: int = 15) -> bool:
    if _LAST_INGEST_AT is None:
        return True
    return datetime.utcnow() - _LAST_INGEST_AT > timedelta(minutes=max_age_minutes)


def query_articles(
    region: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 50,
    query: Optional[str] = None,
) -> List[Dict]:
    normalized_topic = normalize_topic(topic)
    inferred_topic = infer_topic_from_query(query) if not normalized_topic else None
    effective_topic = normalized_topic or inferred_topic
    words = [
        token
        for token in _tokenize(query)
        if len(token) > 2 and token not in STOPWORDS
    ]

    filtered = []
    for article in _ARTICLES:
        if region and article.get("region") not in {region, "Global"}:
            continue
        if effective_topic and article.get("topic") != effective_topic:
            continue
        filtered.append(article)

    if not words:
        return filtered[:limit]

    scored = []
    for article in filtered:
        text = " ".join([
            article.get("title", ""),
            article.get("summary", ""),
            article.get("content", ""),
        ]).lower()
        score = sum(1 for w in words if w in text)
        if effective_topic and article.get("topic") == effective_topic:
            score += 2
        if score > 0:
            scored.append((score, article.get("published_at", ""), article))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [article for _, _, article in scored[:limit]]
