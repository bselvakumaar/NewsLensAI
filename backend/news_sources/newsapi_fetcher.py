"""
NewsAPI.org Integration
Free: 100 requests/day
Categories: business, entertainment, general, health, science, sports, technology
"""

import httpx
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
NEWSAPI_BASE = "https://newsapi.org/v2"

REGION_MAPPING = {
    "India": "in",
    "USA": "us",
    "UK": "gb",
    "Global": "us",  # Default
}

TOPIC_MAPPING = {
    "Politics": "general",
    "Technology": "technology",
    "Business": "business",
    "Sports": "sports",
    "Entertainment": "entertainment",
    "Health": "health",
    "Science": "science",
}


async def fetch_from_newsapi(
    region: str = "India",
    topic: str = None,
    limit: int = 12
) -> List[Dict]:
    """
    Fetch news from NewsAPI.org
    
    Requires NEWSAPI_KEY environment variable
    Get free key at https://newsapi.org/
    """
    
    if not NEWSAPI_KEY:
        logger.warning("NEWSAPI_KEY not set. Get free key from https://newsapi.org/")
        return []
    
    try:
        country = REGION_MAPPING.get(region, "in")
        category = TOPIC_MAPPING.get(topic, "general")
        
        url = f"{NEWSAPI_BASE}/top-headlines"
        params = {
            "apiKey": NEWSAPI_KEY,
            "country": country,
            "category": category,
            "pageSize": limit,
            "sortBy": "publishedAt"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
        data = response.json()
        
        if data.get("status") != "ok":
            logger.error(f"NewsAPI error: {data.get('message')}")
            return []
        
        articles = []
        for article in data.get("articles", []):
            articles.append({
                "id": hash(article["url"]) % 2147483647,
                "title": article.get("title", ""),
                "content": article.get("description", ""),
                "summary": article.get("description", "")[:200],
                "source": article.get("source", {}).get("name", "NewsAPI"),
                "region": region,
                "topic": topic or "General",
                "published_at": article.get("publishedAt", datetime.utcnow().isoformat()),
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage", ""),
            })
        
        logger.info(f"✓ Fetched {len(articles)} articles from NewsAPI")
        return articles
        
    except Exception as e:
        logger.error(f"NewsAPI fetch error: {str(e)}")
        return []
