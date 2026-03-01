"""
RSS Feed Parser Integration
Free, no API key needed
Works with BBC, Reuters, NDTV, TheHindu, etc.
"""

import feedparser
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "India": {
        "Politics": [
            "https://feeds.thehindu.com/thehindu/national/?format=xml",
            "https://feeds.reuters.com/news/indianews",
        ],
        "Technology": [
            "https://feeds.thehindu.com/thehindu/biz/science/?format=xml",
        ],
        "Business": [
            "https://feeds.thehindu.com/thehindu/biz/?format=xml",
            "https://feeds2.bloomberg.com/news/business.rss",
        ],
        "Sports": [
            "https://feeds.thehindu.com/thehindu/sport/?format=xml",
        ],
        "General": [
            "https://feeds.thehindu.com/thehindu/?format=xml",
        ],
    },
    "Global": {
        "Technology": [
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://feeds.techcrunch.com/",
        ],
        "Business": [
            "https://feeds2.bloomberg.com/news/business.rss",
        ],
        "Politics": [
            "https://feeds.bbc.co.uk/news/world/rss.xml",
            "https://feeds.reuters.com/news/todaysnews",
        ],
        "Sports": [
            "https://feeds.bbc.co.uk/sport/rss.xml",
        ],
        "General": [
            "https://feeds.bbc.co.uk/news/rss.xml",
        ],
    },
}


async def fetch_from_rss(
    region: str = "India",
    topic: str = None,
    limit: int = 12
) -> List[Dict]:
    """
    Fetch news from RSS feeds
    No API key required. 100% free.
    """
    
    try:
        region_feeds = RSS_FEEDS.get(region, RSS_FEEDS["Global"])
        topic_key = topic or "General"
        feed_urls = region_feeds.get(topic_key, region_feeds.get("General", []))
        
        if not feed_urls:
            logger.warning(f"No RSS feeds configured for {region}/{topic_key}")
            return []
        
        articles = []
        
        for feed_url in feed_urls:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:limit]:
                    published = entry.get("published_parsed")
                    published_at = datetime(*published[:6]).isoformat() if published else datetime.utcnow().isoformat()
                    
                    articles.append({
                        "id": hash(entry.get("link", "")) % 2147483647,
                        "title": entry.get("title", ""),
                        "content": entry.get("summary", "")[:500],
                        "summary": entry.get("summary", "")[:200],
                        "source": feed.feed.get("title", "RSS Feed"),
                        "region": region,
                        "topic": topic or "General",
                        "published_at": published_at,
                        "url": entry.get("link", ""),
                        "image_url": "",
                    })
                    
                    if len(articles) >= limit:
                        break
                
                if len(articles) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"RSS feed parse error ({feed_url}): {str(e)}")
                continue
        
        logger.info(f"✓ Fetched {len(articles)} articles from RSS feeds")
        return articles[:limit]
        
    except Exception as e:
        logger.error(f"RSS fetch error: {str(e)}")
        return []
