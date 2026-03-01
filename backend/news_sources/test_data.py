"""
Test Data - Direct Insert into Cloud SQL
No API key required. For MVP testing only.
"""

from datetime import datetime, timedelta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

TEST_ARTICLES = [
    {
        "title": "India's Budget 2026: Major Economic Reforms Announced",
        "content": "The Finance Minister unveiled the 2026-27 budget with focus on green energy, infrastructure, and digital transformation. Tax incentives announced for tech startups...",
        "summary": "India's Budget 2026 focuses on green energy and tech sector growth",
        "source": "The Hindu",
        "region": "India",
        "topic": "Politics",
        "published_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "url": "https://www.thehindu.com/business/budget/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "Tech Giants Invest in Indian AI Startup Ecosystem",
        "content": "Google, Microsoft, and Amazon announce joint initiatives to boost AI research in India. New $500M fund created for emerging startups...",
        "summary": "Tech giants announce $500M fund for Indian AI startups",
        "source": "TechCrunch",
        "region": "India",
        "topic": "Technology",
        "published_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
        "url": "https://techcrunch.com/tag/india/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "Sensex Reaches All-Time High as FII Inflows Continue",
        "content": "The Bombay Stock Exchange's BSE Sensex index crosses 75,000 mark for the first time. Strong FII inflows support market growth...",
        "summary": "BSE Sensex crosses 75,000 on strong FII inflows",
        "source": "Business Today",
        "region": "India",
        "topic": "Business",
        "published_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "url": "https://www.businesstoday.in/markets/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "India Beats England in Cricket World Cup Qualifier",
        "content": "India's cricket team defeats England by 45 runs in an exciting World Cup qualifier match. Virat Kohli scores 89 runs...",
        "summary": "India beats England in World Cup cricket qualifier",
        "source": "Cricbuzz",
        "region": "India",
        "topic": "Sports",
        "published_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "url": "https://www.cricbuzz.com/cricket-news/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "New Bollywood Film Breaks Box Office Records",
        "content": "The latest Bollywood release shatters opening weekend records with ₹250 crore collection. Critics praise storyline and performances...",
        "summary": "New Bollywood film breaks box office records",
        "source": "NDTV",
        "region": "India",
        "topic": "Entertainment",
        "published_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
        "url": "https://www.ndtv.com/entertainment/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "Indian Scientists Discover New Species in Western Ghats",
        "content": "Researchers from IIT Bombay discover three new species of frogs in the Western Ghats region. Important for biodiversity conservation...",
        "summary": "New frog species discovered in Western Ghats",
        "source": "The Hindu Science",
        "region": "India",
        "topic": "Science",
        "published_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
        "url": "https://www.thehindu.com/sci-tech/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "India Launches First National Health Insurance Forum",
        "content": "Government launches comprehensive health insurance scheme covering 500 million citizens. Premium subsidized for low-income groups...",
        "summary": "New national health insurance covers 500M citizens",
        "source": "Times of India",
        "region": "India",
        "topic": "Health",
        "published_at": (datetime.utcnow() - timedelta(hours=7)).isoformat(),
        "url": "https://timesofindia.indiatimes.com/health/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "OpenAI Releases GPT-5: Major Breakthrough in AI",
        "content": "OpenAI announces GPT-5 with reasoning capabilities approaching human level. New benchmarks set for AI performance...",
        "summary": "OpenAI releases GPT-5 with advanced reasoning",
        "source": "TechCrunch",
        "region": "Global",
        "topic": "Technology",
        "published_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
        "url": "https://techcrunch.com/tag/ai/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "Global Markets Surge on Positive Economic Data",
        "content": "Major indices worldwide post gains following strong Q4 economic reports. Inflation moderates further...",
        "summary": "Global markets surge on positive economic data",
        "source": "Reuters",
        "region": "Global",
        "topic": "Business",
        "published_at": (datetime.utcnow() - timedelta(hours=9)).isoformat(),
        "url": "https://www.reuters.com/markets/",
        "image_url": "https://via.placeholder.com/400x250",
    },
    {
        "title": "FIFA World Cup 2026: Draw Announced",
        "content": "The World Cup draw reveals exciting group matchups. Argentina, France, and Brazil land in tough groups...",
        "summary": "World Cup 2026 draw announced with group matchups",
        "source": "BBC Sport",
        "region": "Global",
        "topic": "Sports",
        "published_at": (datetime.utcnow() - timedelta(hours=10)).isoformat(),
        "url": "https://www.bbc.com/sport/football/",
        "image_url": "https://via.placeholder.com/400x250",
    },
]


def get_test_articles(
    region: str = "India",
    topic: str = None,
    limit: int = 12
) -> List[Dict]:
    """
    Get test articles filtered by region and topic
    """
    
    try:
        articles = []
        
        for article in TEST_ARTICLES:
            # Filter by region
            if article["region"] != region and region != "Global":
                if article["region"] != "Global":
                    continue
            
            # Filter by topic
            if topic and article["topic"] != topic:
                continue
            
            articles.append(article)
        
        logger.info(f"✓ Loaded {len(articles)} test articles ({region}/{topic or 'All'})")
        return articles[:limit]
        
    except Exception as e:
        logger.error(f"Test data load error: {str(e)}")
        return []
