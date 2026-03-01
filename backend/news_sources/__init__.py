"""
News Sources Module
Provides multiple news fetching options with automatic fallback
"""

from .newsapi_fetcher import fetch_from_newsapi
from .guardian_fetcher import fetch_from_guardian
from .rss_fetcher import fetch_from_rss
from .test_data import get_test_articles

__all__ = [
    "fetch_from_newsapi",
    "fetch_from_guardian", 
    "fetch_from_rss",
    "get_test_articles",
]
