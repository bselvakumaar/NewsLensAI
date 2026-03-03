"""
NewsLensAI Backend API
RAG-powered News Intelligence Platform

Endpoints:
- POST /api/chat - Chat with RAG-backed responses
- GET /api/news - Fetch latest news
- GET /api/sentiment - Get sentiment analysis
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import logging
from datetime import datetime
import uuid
import asyncio
import re

# News sources
from news_sources import (
    fetch_from_newsapi,
    fetch_from_guardian,
    fetch_from_rss,
    get_test_articles
)

# RAG pipeline
from rag import rag_pipeline
from article_store import (
    get_ingestion_snapshot,
    ingest_from_web,
    infer_topic_from_query,
    is_cache_stale,
    normalize_topic,
    query_articles,
)

# Admin API
from admin_api import (
    add_news_source,
    list_news_sources,
    update_news_source,
    delete_news_source,
    start_ingestion,
    get_ingestion_status,
    get_admin_stats
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCHEDULER_INGEST_TOKEN = os.getenv("SCHEDULER_INGEST_TOKEN", "")
INGESTION_RUNTIME_SETTINGS = {
    "external_ingestion_enabled": os.getenv("EXTERNAL_INGESTION_ENABLED", "true").lower() == "true",
    "auto_ingestion_enabled": os.getenv("AUTO_INGEST_ENABLED", "true").lower() == "true",
}
NEWS_KEYWORDS = {
    "news", "india", "global", "politics", "policy", "election", "finance", "economy",
    "market", "stock", "world", "international", "war", "diplomacy", "tech",
    "technology", "ai", "sports", "cricket", "football", "headline", "breaking",
    "trend", "today", "latest", "update", "government", "budget", "inflation",
    "sensex", "nifty"
}
FALLBACK_SCOPE_MESSAGE = "NewsLensAI focuses only on India & Global News."


def _is_out_of_scope_query(query: str) -> bool:
    tokens = re.findall(r"[a-zA-Z0-9]+", (query or "").lower())
    if not tokens:
        return True
    if "how" in tokens and "you" in tokens:
        return True
    return not any(token in NEWS_KEYWORDS for token in tokens)


def _assert_scheduler_token(request: Request):
    """Validate scheduler bearer token when configured."""
    if not SCHEDULER_INGEST_TOKEN:
        return
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {SCHEDULER_INGEST_TOKEN}"
    if auth != expected:
        raise HTTPException(status_code=401, detail="Unauthorized scheduler token")

# Initialize FastAPI app
app = FastAPI(
    title="NewsLensAI Backend API",
    version="1.0.0",
    description="RAG-powered News Intelligence Platform"
)

# CORS Configuration (allow frontend requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Models ====================

class ChatRequest(BaseModel):
    session_id: str
    query: str
    topic: Optional[str] = None
    region: Optional[str] = "India"

class ChatResponse(BaseModel):
    summary: str
    answer: Optional[str] = None
    sources: List[dict] = []
    region: str = "India"
    confidence: str = "Low"
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Article(BaseModel):
    id: int
    title: str
    source: str
    region: str
    topic: str
    published_at: str
    url: Optional[str] = None

class SentimentItem(BaseModel):
    entity: str
    score: float
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    date: Optional[str] = None

class NewsSourceRequest(BaseModel):
    name: str
    source_type: str  # 'rss', 'newsapi', 'guardian', 'manual'
    url: str
    region: str = "India"
    topic: Optional[str] = None
    is_active: Optional[bool] = True

class UpdateSourceRequest(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    topic: Optional[str] = None

class IngestionRequest(BaseModel):
    source_id: Optional[str] = None  # If None, ingest from all active sources
    regions: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    limit_per_fetch: int = 12

class IngestionSettingsUpdate(BaseModel):
    external_ingestion_enabled: Optional[bool] = None
    auto_ingestion_enabled: Optional[bool] = None

# ==================== Routes ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "NewsLensAI Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "gcp_project": os.getenv("GCP_PROJECT_ID", "newslensai"),
        "environment": os.getenv("ENV", "development")
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint with RAG (Retrieval-Augmented Generation) support
    
    Steps:
    1. Fetch relevant articles from news sources
    2. Search for similar articles to user query
    3. Pass context + query to Vertex AI Gemini LLM
    4. Return answer with source citations
    
    Args:
        request: ChatRequest with session_id and query
        
    Returns:
        ChatResponse with answer and sources
    """
    try:
        if _is_out_of_scope_query(request.query):
            return ChatResponse(
                summary=FALLBACK_SCOPE_MESSAGE,
                answer=FALLBACK_SCOPE_MESSAGE,
                sources=[],
                region=request.region or "India",
                confidence="Low",
                last_updated=datetime.utcnow().isoformat()
            )

        logger.info(
            f"Chat request - Session: {request.session_id}, Query: {request.query}, "
            f"Region: {request.region}, Topic: {request.topic}"
        )
        
        # Fetch available articles from live ingestion cache first.
        region = request.region or "India"
        normalized_topic = normalize_topic(request.topic)
        inferred_topic = infer_topic_from_query(request.query)
        effective_topic = inferred_topic or normalized_topic
        available_articles = query_articles(
            region=region,
            topic=effective_topic,
            limit=80,
            query=request.query,
        )

        # If cache is empty/stale, refresh from web and retry.
        if not available_articles or is_cache_stale(max_age_minutes=15):
            await ingest_from_web()
            available_articles = query_articles(
                region=region,
                topic=effective_topic,
                limit=80,
                query=request.query,
            )

        # Last fallback: direct fetch + test data.
        if not available_articles:
            try:
                available_articles = await fetch_from_rss(
                    region=region,
                    topic=effective_topic,
                    limit=20
                )
                if not available_articles:
                    available_articles = get_test_articles(
                        region=region,
                        topic=effective_topic,
                        limit=20
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch direct fallback articles: {str(e)}")
                available_articles = get_test_articles(
                    region=region,
                    topic=effective_topic,
                    limit=20
                )
        
        logger.info(f"Articles available for RAG: {len(available_articles)}")
        
        # Run RAG pipeline
        rag_response = await rag_pipeline(
            query=request.query,
            available_articles=available_articles,
            region=region
        )
        
        # Extract sources for response
        sources = []
        if rag_response.get('sources'):
            for source in rag_response['sources'][:3]:
                sources.append({
                    "title": source.get("title", "Untitled"),
                    "source": source.get("source", "Unknown"),
                    "published_at": source.get("published_at", datetime.utcnow().isoformat()),
                    "url": source.get("url", ""),
                })
        
        summary = rag_response.get('summary') or rag_response.get('answer') or "Unable to process your query"
        last_updated = rag_response.get('last_updated', datetime.utcnow().isoformat())

        return ChatResponse(
            summary=summary,
            answer=summary,
            sources=sources,
            region=rag_response.get('region', 'India'),
            confidence=rag_response.get('confidence', 'Low'),
            last_updated=last_updated
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        # Fallback response
        return ChatResponse(
            summary=f"I encountered an error: {str(e)}. Please try again.",
            answer=f"I encountered an error: {str(e)}. Please try again.",
            sources=[],
            region="India",
            confidence="Low",
            last_updated=datetime.utcnow().isoformat()
        )

@app.get("/api/news")
async def get_news(
    region: str = "India",
    topic: Optional[str] = None,
    limit: int = 12,
    source: Optional[str] = None
):
    """
    Get latest news articles with automatic fallback strategy
    
    Query parameters:
        region: Filter by region (India, Global, etc)
        topic: Optional filter by topic (Politics, Technology, Business, Sports, etc)
        limit: Max number of articles to return (default: 12)
        source: Force specific source - "newsapi", "guardian", "rss", "test"
                If not specified, tries all in order: RSS > NewsAPI > Guardian > Test
    
    Returns:
        List of articles with metadata and source information
    """
    try:
        logger.info(f"News request - Region: {region}, Topic: {topic}, Source: {source}, Limit: {limit}")
        normalized_topic = normalize_topic(topic)

        cached_articles = query_articles(
            region=region,
            topic=normalized_topic,
            limit=limit,
        )
        if cached_articles:
            return {
                "articles": cached_articles,
                "total": len(cached_articles),
                "limit": limit,
                "region": region,
                "topic": normalized_topic or "All",
                "source_used": "live_cache",
                "message": "Fetched from auto-ingested web cache",
                "ingestion": get_ingestion_snapshot(),
            }

        await ingest_from_web()
        cached_articles = query_articles(
            region=region,
            topic=normalized_topic,
            limit=limit,
        )
        if cached_articles:
            return {
                "articles": cached_articles,
                "total": len(cached_articles),
                "limit": limit,
                "region": region,
                "topic": normalized_topic or "All",
                "source_used": "live_cache_after_refresh",
                "message": "Fetched after on-demand web ingestion",
                "ingestion": get_ingestion_snapshot(),
            }
        
        articles = []
        sources_tried = []
        
        # Define source priority if not specified
        if source:
            source_priority = [source]
        else:
            # Default fallback order: RSS (free, fast) > NewsAPI > Test Data
            source_priority = ["rss", "newsapi", "test"]
        
        # Try each source in priority order
        for news_source in source_priority:
            try:
                if news_source.lower() == "newsapi":
                    articles = await fetch_from_newsapi(region, normalized_topic, limit)
                    sources_tried.append("NewsAPI.org")
                    
                elif news_source.lower() == "guardian":
                    articles = await fetch_from_guardian(region, normalized_topic, limit)
                    sources_tried.append("The Guardian")
                    
                elif news_source.lower() == "rss":
                    articles = await fetch_from_rss(region, normalized_topic, limit)
                    sources_tried.append("RSS Feeds")
                    
                elif news_source.lower() == "test":
                    articles = get_test_articles(region, normalized_topic, limit)
                    sources_tried.append("Test Data")
                
                # If we got articles, return them
                if articles:
                    logger.info(f"✓ News from {news_source}: {len(articles)} articles")
                    return {
                        "articles": articles,
                        "total": len(articles),
                        "limit": limit,
                        "region": region,
                        "topic": normalized_topic or "All",
                        "sources_tried": sources_tried,
                        "source_used": news_source,
                        "message": f"Fetched from {news_source}" + (f" (fallback from {', '.join(sources_tried[:-1])})" if len(sources_tried) > 1 else "")
                    }
                
            except Exception as e:
                logger.warning(f"Failed to fetch from {news_source}: {str(e)}")
                sources_tried.append(f"{news_source} (failed)")
                continue
        
        # Fallback: return test data if all sources fail
        logger.warning(f"All sources failed. Using test data.")
        articles = get_test_articles(region, normalized_topic, limit)
        
        return {
            "articles": articles,
            "total": len(articles),
            "limit": limit,
            "region": region,
            "topic": normalized_topic or "All",
            "sources_tried": sources_tried,
            "source_used": "test (fallback)",
            "message": "All external sources failed. Returning test data.",
            "warning": "Configure API keys for production use"
        }
        
    except Exception as e:
        logger.error(f"News API error: {str(e)}", exc_info=True)
        # Even on error, try to return test data
        try:
            articles = get_test_articles(region, normalized_topic, limit)
            return {
                "articles": articles,
                "error": str(e),
                "source_used": "test (emergency fallback)",
            }
        except:
            raise HTTPException(status_code=500, detail="Unable to fetch news from any source")

@app.get("/api/sentiment")
async def get_sentiment(
    entity: Optional[str] = None,
    region: str = "India",
    days: int = 7
):
    """
    Get sentiment analysis for entities
    
    Query sentiment_scores table and return aggregated sentiment data.
    
    Args:
        entity: Optional specific entity to analyze
        region: Filter by region
        days: Number of days to look back
        
    Returns:
        Sentiment data with scores and trends
    """
    try:
        logger.info(f"Sentiment request - Entity: {entity}, Region: {region}, Days: {days}")
        
        # TODO: Query Cloud SQL sentiment_scores table
        # SELECT * FROM sentiment_scores
        # WHERE (entity = entity OR entity IS NULL)
        # AND date >= NOW() - interval 'X days'
        # ORDER BY date DESC
        
        # Mock response for development
        return {
            "sentiments": [
                {
                    "entity": entity or "Prime Minister",
                    "score": 0.45,  # Range: -1 (negative) to +1 (positive)
                    "positive_count": 120,
                    "neutral_count": 80,
                    "negative_count": 50,
                    "date": datetime.utcnow().isoformat()
                }
            ],
            "region": region,
            "days": days,
            "interpretation": {
                "0.45": "Moderately Positive"
            }
        }
    except Exception as e:
        logger.error(f"Sentiment API error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Admin API Routes ====================

@app.post("/api/admin/sources")
async def admin_add_source(request: NewsSourceRequest):
    """Add a new news source"""
    try:
        logger.info(f"Adding news source: {request.name}")
        result = await add_news_source(
            name=request.name,
            source_type=request.source_type,
            url=request.url,
            region=request.region,
            topic=request.topic
        )
        return result
    except Exception as e:
        logger.error(f"Error adding source: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/sources")
async def admin_list_sources():
    """List all news sources"""
    try:
        result = await list_news_sources()
        return result
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/sources/{source_id}")
async def admin_update_source(source_id: str, request: UpdateSourceRequest):
    """Update a news source"""
    try:
        logger.info(f"Updating source: {source_id}")
        result = await update_news_source(
            source_id=source_id,
            name=request.name,
            is_active=request.is_active,
            topic=request.topic
        )
        return result
    except Exception as e:
        logger.error(f"Error updating source: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/admin/sources/{source_id}")
async def admin_delete_source(source_id: str):
    """Delete a news source"""
    try:
        logger.info(f"Deleting source: {source_id}")
        result = await delete_news_source(source_id)
        return result
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/ingest")
async def admin_start_ingest(request: IngestionRequest):
    """Start ingestion from specific or all sources"""
    try:
        logger.info(f"Starting ingestion - Source: {request.source_id or 'all'}")
        legacy_result = await start_ingestion(source_id=request.source_id)
        live_result = await ingest_from_web(
            regions=request.regions,
            topics=[normalize_topic(t) for t in request.topics] if request.topics else None,
            limit_per_fetch=request.limit_per_fetch,
        )
        return {
            "status": "success",
            "legacy": legacy_result,
            "live_ingestion": live_result,
        }
    except Exception as e:
        logger.error(f"Error starting ingestion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/ingest-settings")
async def admin_get_ingest_settings():
    """Get runtime ingestion control flags."""
    return {
        "external_ingestion_enabled": INGESTION_RUNTIME_SETTINGS["external_ingestion_enabled"],
        "auto_ingestion_enabled": INGESTION_RUNTIME_SETTINGS["auto_ingestion_enabled"],
        "scheduler_token_configured": bool(SCHEDULER_INGEST_TOKEN),
    }

@app.put("/api/admin/ingest-settings")
async def admin_update_ingest_settings(payload: IngestionSettingsUpdate):
    """Update runtime ingestion control flags without redeploy."""
    if payload.external_ingestion_enabled is not None:
        INGESTION_RUNTIME_SETTINGS["external_ingestion_enabled"] = payload.external_ingestion_enabled
    if payload.auto_ingestion_enabled is not None:
        INGESTION_RUNTIME_SETTINGS["auto_ingestion_enabled"] = payload.auto_ingestion_enabled

    return {
        "status": "success",
        "settings": {
            "external_ingestion_enabled": INGESTION_RUNTIME_SETTINGS["external_ingestion_enabled"],
            "auto_ingestion_enabled": INGESTION_RUNTIME_SETTINGS["auto_ingestion_enabled"],
        }
    }

@app.post("/api/admin/ingest/scheduler-trigger")
async def scheduler_ingest_trigger(request: Request):
    """Cloud Scheduler endpoint for external ingestion trigger."""
    _assert_scheduler_token(request)

    if not INGESTION_RUNTIME_SETTINGS["external_ingestion_enabled"]:
        return {
            "status": "skipped",
            "reason": "external_ingestion_disabled",
            "ingestion": get_ingestion_snapshot(),
        }

    result = await ingest_from_web()
    return {
        "status": "success",
        "trigger": "scheduler",
        "ingestion": result,
    }

@app.get("/api/admin/ingest-live-status")
async def admin_ingest_live_status():
    """Get status of automatic live web ingestion cache"""
    return get_ingestion_snapshot()

@app.get("/api/admin/ingestion-status")
async def admin_ingest_status():
    """Get ingestion job status and logs"""
    try:
        result = await get_ingestion_status()
        return result
    except Exception as e:
        logger.error(f"Error getting ingestion status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/stats")
async def admin_get_stats():
    """Get admin statistics and dashboard data"""
    try:
        result = await get_admin_stats()
        return result
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Original Admin Endpoint (Legacy) ====================

@app.post("/api/sessions")
async def create_session(user_id: Optional[str] = None):
    """
    Create a new chat session
    
    Args:
        user_id: Optional user identifier
        
    Returns:
        Session ID and metadata
    """
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Created session: {session_id}, User: {user_id or 'anonymous'}")
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "ttl_minutes": 1440  # 24 hours
        }
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Startup/Shutdown ====================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    """Manage app startup and shutdown"""
    auto_ingest_task = None
    stop_event = asyncio.Event()

    async def auto_ingest_loop():
        interval_minutes = int(os.getenv("AUTO_INGEST_INTERVAL_MINUTES", "15"))
        logger.info(f"Auto-ingestion loop started (every {interval_minutes} minutes)")
        while not stop_event.is_set():
            try:
                await ingest_from_web()
            except Exception as e:
                logger.error(f"Auto-ingestion loop error: {str(e)}")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval_minutes * 60)
            except asyncio.TimeoutError:
                continue

    # Startup
    logger.info("NewsLensAI Backend starting up...")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"Project: {os.getenv('GCP_PROJECT_ID', 'newslensai')}")
    if INGESTION_RUNTIME_SETTINGS["auto_ingestion_enabled"]:
        auto_ingest_task = asyncio.create_task(auto_ingest_loop())
    yield
    # Shutdown
    stop_event.set()
    if auto_ingest_task:
        auto_ingest_task.cancel()
        try:
            await auto_ingest_task
        except asyncio.CancelledError:
            pass
    logger.info("NewsLensAI Backend shutting down...")

# Update app with lifespan
app.router.lifespan_context = lifespan

# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    env = os.getenv("ENV", "development")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=(env == "development")
    )
