"""
NewsLensAI Backend API
RAG-powered News Intelligence Platform

Endpoints:
- POST /api/chat - Chat with RAG-backed responses
- GET /api/news - Fetch latest news
- GET /api/sentiment - Get sentiment analysis
- GET /health - Health check
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import logging
from datetime import datetime
import uuid

# News sources
from news_sources import (
    fetch_from_newsapi,
    fetch_from_guardian,
    fetch_from_rss,
    get_test_articles
)

# RAG pipeline
from rag import rag_pipeline

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

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    region: str = "Global"

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
        logger.info(f"Chat request - Session: {request.session_id}, Query: {request.query}")
        
        # Fetch available articles from news sources
        # In production, these would come from Cloud SQL
        available_articles = []
        
        try:
            # Try RSS first (fastest)
            available_articles = await fetch_from_rss(region="India", limit=20)
            if not available_articles:
                # Fallback to test data
                available_articles = get_test_articles(region="India", limit=20)
        except Exception as e:
            logger.warning(f"Failed to fetch articles: {str(e)}")
            # Use test data as fallback
            available_articles = get_test_articles(region="India", limit=20)
        
        logger.info(f"Articles available for RAG: {len(available_articles)}")
        
        # Run RAG pipeline
        rag_response = await rag_pipeline(
            query=request.query,
            available_articles=available_articles,
            region="India"
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
        
        return ChatResponse(
            answer=rag_response.get('answer', "Unable to process your query"),
            sources=sources,
            region=rag_response.get('region', 'India')
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        # Fallback response
        return ChatResponse(
            answer=f"I encountered an error: {str(e)}. Please try again.",
            sources=[],
            region="India"
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
                    articles = await fetch_from_newsapi(region, topic, limit)
                    sources_tried.append("NewsAPI.org")
                    
                elif news_source.lower() == "guardian":
                    articles = await fetch_from_guardian(region, topic, limit)
                    sources_tried.append("The Guardian")
                    
                elif news_source.lower() == "rss":
                    articles = await fetch_from_rss(region, topic, limit)
                    sources_tried.append("RSS Feeds")
                    
                elif news_source.lower() == "test":
                    articles = get_test_articles(region, topic, limit)
                    sources_tried.append("Test Data")
                
                # If we got articles, return them
                if articles:
                    logger.info(f"✓ News from {news_source}: {len(articles)} articles")
                    return {
                        "articles": articles,
                        "total": len(articles),
                        "limit": limit,
                        "region": region,
                        "topic": topic or "All",
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
        articles = get_test_articles(region, topic, limit)
        
        return {
            "articles": articles,
            "total": len(articles),
            "limit": limit,
            "region": region,
            "topic": topic or "All",
            "sources_tried": sources_tried,
            "source_used": "test (fallback)",
            "message": "All external sources failed. Returning test data.",
            "warning": "Configure API keys for production use"
        }
        
    except Exception as e:
        logger.error(f"News API error: {str(e)}", exc_info=True)
        # Even on error, try to return test data
        try:
            articles = get_test_articles(region, topic, limit)
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
        result = await start_ingestion(source_id=request.source_id)
        return result
    except Exception as e:
        logger.error(f"Error starting ingestion: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

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
    # Startup
    logger.info("NewsLensAI Backend starting up...")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"Project: {os.getenv('GCP_PROJECT_ID', 'newslensai')}")
    yield
    # Shutdown
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
