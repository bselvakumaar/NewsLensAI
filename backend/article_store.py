"""
Live article ingestion and in-memory retrieval store.

This keeps the current architecture (stateless API + RAG), while adding
automatic web ingestion so chat/news endpoints can use fresher context.
"""

import asyncio
import logging
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
}
_LOCK = asyncio.Lock()

TOPIC_MAP = {
    "Finance": "Business",
    "Tech": "Technology",
    "World": "General",
}

DEFAULT_TOPICS = ["Politics", "Business", "Technology", "Sports", "General"]
DEFAULT_REGIONS = ["India", "Global"]


def normalize_topic(topic: Optional[str]) -> Optional[str]:
    if not topic:
        return None
    return TOPIC_MAP.get(topic, topic)


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

    regions = regions or DEFAULT_REGIONS
    topics = topics or DEFAULT_TOPICS

    try:
        fetched: List[Dict] = []
        source_counts: Dict[str, int] = {}

        for region in regions:
            for topic in topics:
                batch = await _fetch_for_region_topic(region, topic, limit_per_fetch)
                fetched.extend(batch)
                for article in batch:
                    source_name = article.get("source", "Unknown")
                    source_counts[source_name] = source_counts.get(source_name, 0) + 1

        deduped = _dedupe_articles(fetched)

        # Newest-first where published_at is available.
        deduped.sort(key=lambda x: x.get("published_at", ""), reverse=True)

        async with _LOCK:
            _ARTICLES = deduped
            _LAST_INGEST_AT = datetime.utcnow()
            _INGEST_META = {
                "total_articles": len(deduped),
                "sources": source_counts,
                "last_run_status": "success",
                "last_error": None,
            }

        logger.info(f"Ingestion complete: {len(deduped)} deduped articles")
        return get_ingestion_snapshot()
    except Exception as exc:
        logger.error(f"Ingestion failed: {str(exc)}", exc_info=True)
        async with _LOCK:
            _INGEST_META["last_run_status"] = "failed"
            _INGEST_META["last_error"] = str(exc)
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
    words = [w for w in (query or "").lower().split() if len(w) > 2]

    filtered = []
    for article in _ARTICLES:
        if region and article.get("region") not in {region, "Global"}:
            continue
        if normalized_topic and article.get("topic") != normalized_topic:
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
        if score > 0:
            scored.append((score, article))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in scored[:limit]]
