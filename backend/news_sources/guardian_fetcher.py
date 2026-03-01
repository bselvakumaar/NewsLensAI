"""
The Guardian API Integration (DEPRECATED - site issues)
Alternative: Use NewsAPI or RSS instead

If you want to use Guardian:
Get key at https://www.theguardian.com/open-platform
Documentation: https://open.theguardian.com/documentation/
"""

import httpx
import os
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

GUARDIAN_KEY = os.getenv("GUARDIAN_API_KEY", "")
GUARDIAN_BASE = "https://open.theguardian.com/api/proxy"

TOPIC_MAPPING = {
    "Politics": "politics",
    "Technology": "technology",
    "Business": "business",
    "Sports": "sport",
    "Entertainment": "film",
    "Health": "lifeandstyle",
    "Science": "science",
    "General": "world",
}


async def fetch_from_guardian(
    region: str = "India",
    topic: str = None,
    limit: int = 12
) -> List[Dict]:
    """
    Fetch news from The Guardian API
    
    Requires GUARDIAN_API_KEY environment variable
    Get free key at https://open.theguardian.com/
    """
    
    if not GUARDIAN_KEY:
        logger.warning("GUARDIAN_API_KEY not set. Get free key from https://open.theguardian.com/")
        return []
    
    try:
        section = TOPIC_MAPPING.get(topic, "world")
        
        url = f"{GUARDIAN_BASE}"
        params = {
            "api-key": GUARDIAN_KEY,
            "section": section,
            "page-size": limit,
            "format": "json",
            "show-fields": "thumbnail,trailText,byline"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
        
        data = response.json()
        
        if data.get("response", {}).get("status") != "ok":
            logger.error(f"Guardian API error")
            return []
        
        articles = []
        for result in data.get("response", {}).get("results", []):
            fields = result.get("fields", {})
            articles.append({
                "id": hash(result["id"]) % 2147483647,
                "title": result.get("webTitle", ""),
                "content": fields.get("trailText", ""),
                "summary": fields.get("trailText", "")[:200],
                "source": "The Guardian",
                "region": region,
                "topic": topic or "General",
                "published_at": result.get("webPublicationDate", datetime.utcnow().isoformat()),
                "url": result.get("webUrl", ""),
                "image_url": fields.get("thumbnail", ""),
            })
        
        logger.info(f"✓ Fetched {len(articles)} articles from The Guardian")
        return articles
        
    except Exception as e:
        logger.error(f"Guardian API fetch error: {str(e)}")
        return []
