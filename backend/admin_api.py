"""
Admin API Module for NewsLensAI
Manages news sources, article ingestion, and system monitoring
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Store ingestion logs in memory (will be saved to DB later)
INGESTION_LOGS = []
NEWS_SOURCES = []


class SourceType(str, Enum):
    """Supported news source types"""
    RSS = "rss"
    NEWSAPI = "newsapi"
    GUARDIAN = "guardian"
    MANUAL = "manual"


class IngestionStatus(str, Enum):
    """Ingestion job status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class NewsSource:
    """News source configuration"""
    
    def __init__(
        self,
        source_id: str,
        name: str,
        source_type: SourceType,
        url: str,
        region: str,
        topic: Optional[str] = None,
        is_active: bool = True,
        added_at: Optional[datetime] = None
    ):
        self.source_id = source_id
        self.name = name
        self.source_type = source_type
        self.url = url
        self.region = region
        self.topic = topic
        self.is_active = is_active
        self.added_at = added_at or datetime.utcnow()
        self.last_ingested = None
        self.article_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "url": self.url,
            "region": self.region,
            "topic": self.topic,
            "is_active": self.is_active,
            "added_at": self.added_at.isoformat(),
            "last_ingested": self.last_ingested.isoformat() if self.last_ingested else None,
            "article_count": self.article_count,
        }


class IngestionJob:
    """Ingestion job tracking"""
    
    def __init__(
        self,
        job_id: str,
        source_id: str,
        status: IngestionStatus = IngestionStatus.PENDING,
        started_at: Optional[datetime] = None
    ):
        self.job_id = job_id
        self.source_id = source_id
        self.status = status
        self.started_at = started_at or datetime.utcnow()
        self.completed_at = None
        self.articles_fetched = 0
        self.errors = []
        self.logs = []
    
    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "source_id": self.source_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "articles_fetched": self.articles_fetched,
            "errors": self.errors,
            "logs": self.logs,
        }


# ==================== Source Management ====================

async def add_news_source(
    name: str,
    source_type: str,
    url: str,
    region: str,
    topic: Optional[str] = None
) -> Dict:
    """Add a new news source"""
    try:
        source_id = f"source_{len(NEWS_SOURCES) + 1}_{datetime.utcnow().timestamp()}"
        
        source = NewsSource(
            source_id=source_id,
            name=name,
            source_type=SourceType(source_type),
            url=url,
            region=region,
            topic=topic,
        )
        
        NEWS_SOURCES.append(source)
        logger.info(f"✓ Added news source: {name} ({source_type})")
        
        return {
            "status": "success",
            "message": f"News source '{name}' added successfully",
            "source": source.to_dict()
        }
    except Exception as e:
        logger.error(f"Error adding news source: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


async def list_news_sources() -> List[Dict]:
    """List all news sources"""
    try:
        return [source.to_dict() for source in NEWS_SOURCES]
    except Exception as e:
        logger.error(f"Error listing sources: {str(e)}")
        return []


async def update_news_source(source_id: str, **updates) -> Dict:
    """Update a news source"""
    try:
        source = next((s for s in NEWS_SOURCES if s.source_id == source_id), None)
        if not source:
            return {"status": "error", "message": "Source not found"}
        
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        logger.info(f"✓ Updated source: {source.name}")
        return {
            "status": "success",
            "message": f"Source updated",
            "source": source.to_dict()
        }
    except Exception as e:
        logger.error(f"Error updating source: {str(e)}")
        return {"status": "error", "message": str(e)}


async def delete_news_source(source_id: str) -> Dict:
    """Delete a news source"""
    try:
        global NEWS_SOURCES
        source = next((s for s in NEWS_SOURCES if s.source_id == source_id), None)
        if not source:
            return {"status": "error", "message": "Source not found"}
        
        NEWS_SOURCES = [s for s in NEWS_SOURCES if s.source_id != source_id]
        logger.info(f"✓ Deleted source: {source.name}")
        
        return {
            "status": "success",
            "message": f"Source '{source.name}' deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting source: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== Ingestion Management ====================

async def start_ingestion(source_id: Optional[str] = None) -> Dict:
    """
    Trigger article ingestion
    
    Args:
        source_id: Specific source to ingest from (None = all active sources)
        
    Returns:
        Ingestion job details
    """
    try:
        if source_id:
            sources = [s for s in NEWS_SOURCES if s.source_id == source_id and s.is_active]
            if not sources:
                return {"status": "error", "message": "Source not found or inactive"}
        else:
            sources = [s for s in NEWS_SOURCES if s.is_active]
        
        jobs = []
        for source in sources:
            job = IngestionJob(
                job_id=f"job_{len(INGESTION_LOGS) + 1}",
                source_id=source.source_id,
                status=IngestionStatus.IN_PROGRESS
            )
            
            # TODO: Actually fetch articles based on source type
            # For MVP, just log the job
            job.logs.append(f"Starting ingestion from {source.name}")
            job.articles_fetched = 5  # Mock
            job.status = IngestionStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            
            source.last_ingested = datetime.utcnow()
            source.article_count += job.articles_fetched
            
            INGESTION_LOGS.append(job)
            jobs.append(job.to_dict())
            
            logger.info(f"✓ Ingestion completed for {source.name}: {job.articles_fetched} articles")
        
        return {
            "status": "success",
            "message": f"Started ingestion for {len(sources)} source(s)",
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error starting ingestion: {str(e)}")
        return {"status": "error", "message": str(e)}


async def get_ingestion_status(job_id: Optional[str] = None) -> Dict:
    """Get ingestion job status"""
    try:
        if job_id:
            job = next((j for j in INGESTION_LOGS if j.job_id == job_id), None)
            if not job:
                return {"status": "error", "message": "Job not found"}
            return job.to_dict()
        else:
            # Return recent jobs
            recent_jobs = sorted(
                INGESTION_LOGS,
                key=lambda x: x.started_at,
                reverse=True
            )[:10]
            return [job.to_dict() for job in recent_jobs]
    except Exception as e:
        logger.error(f"Error getting ingestion status: {str(e)}")
        return {"status": "error", "message": str(e)}


# ==================== Article Management ====================

async def list_articles(
    region: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict]:
    """List articles (from sources)"""
    try:
        # TODO: Query from Cloud SQL
        # For MVP, return info about sources
        articles = []
        for source in NEWS_SOURCES:
            if region and source.region != region:
                continue
            if topic and source.topic != topic:
                continue
            
            articles.append({
                "id": source.source_id,
                "title": source.name,
                "source": source.source_type.value,
                "region": source.region,
                "topic": source.topic,
                "article_count": source.article_count,
                "last_updated": source.last_ingested.isoformat() if source.last_ingested else None,
            })
        
        return articles[offset:offset + limit]
    except Exception as e:
        logger.error(f"Error listing articles: {str(e)}")
        return []


async def get_admin_stats() -> Dict:
    """Get admin dashboard statistics"""
    try:
        active_sources = sum(1 for s in NEWS_SOURCES if s.is_active)
        total_articles = sum(s.article_count for s in NEWS_SOURCES)
        total_jobs = len(INGESTION_LOGS)
        successful_jobs = sum(1 for j in INGESTION_LOGS if j.status == IngestionStatus.COMPLETED)
        
        return {
            "total_sources": len(NEWS_SOURCES),
            "active_sources": active_sources,
            "total_articles": total_articles,
            "total_ingestion_jobs": total_jobs,
            "successful_jobs": successful_jobs,
            "failed_jobs": total_jobs - successful_jobs,
            "last_ingestion": INGESTION_LOGS[-1].completed_at.isoformat() if INGESTION_LOGS else None,
        }
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}")
        return {}
