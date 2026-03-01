# News Sources Configuration Guide

This module provides 4 different news fetching options with automatic fallback strategy. You can test and compare all of them.

---

## 📋 Quick Comparison

| Option | Cost | Limit | Setup | Latency | Real Data |
|--------|------|-------|-------|---------|-----------|
| **RSS Feeds** | Free | Unlimited | Easy | Low | ✅ Yes |
| **NewsAPI** | Free | 100/day | Signup | Medium | ✅ Yes |
| **Guardian API** | Free | 300/day | Signup | Medium | ✅ Yes |
| **Test Data** | Free | Unlimited | None | N/A | ⚠️ Mock |

---

## 🔄 Usage & Testing

### Option 1: RSS Feeds (Recommended for MVP)
**✅ Fully working, zero setup required**

```bash
# Test directly
curl "http://localhost:8000/api/news?region=India&topic=Technology&source=rss"

# Automatic (tries RSS first)
curl "http://localhost:8000/api/news?region=India&topic=Technology"
```

**Configured feeds:**
- India: The Hindu, Reuters
- Global: BBC, Reuters, TechCrunch, ArsTechnica

**Pros:**
- ✅ 100% free, unlimited requests
- ✅ No API key required
- ✅ Fast, low latency
- ✅ Multiple sources

**Cons:**
- Feed availability depends on publisher
- Sometimes RSS format inconsistencies

---

### Option 2: NewsAPI.org
**✅ Works with API key**

```bash
# 1. Get free key at https://newsapi.org/
# 2. Add to .env file
NEWSAPI_KEY=your_key_here

# 3. Test
curl "http://localhost:8000/api/news?region=India&topic=Technology&source=newsapi"
```

**Free tier includes:**
- 100 requests per day
- 40+ news sources
- English news only
- 30-day history

**Pros:**
- ✅ Well-structured data
- ✅ Good coverage
- ✅ Reliable API

**Cons:**
- Limited daily requests
- Requires signup
- Limited to English

---

### Option 3: The Guardian API
**✅ Works with API key**

```bash
# 1. Get free key at https://open.theguardian.com/
# 2. Add to .env file
GUARDIAN_API_KEY=your_key_here

# 3. Test
curl "http://localhost:8000/api/news?region=Global&topic=Politics&source=guardian"
```

**Free tier includes:**
- 300 requests per day (after signup)
- High-quality editorial content
- Global coverage
- Good search capabilities

**Pros:**
- ✅ High-quality content
- ✅ Good daily limit
- ✅ Professional journalism

**Cons:**
- Requires signup (takes 10 minutes)
- More limited sources than NewsAPI
- Focused on Guardian content

---

### Option 4: Test Data
**✅ Always works, for development**

```bash
# Test with mock data
curl "http://localhost:8000/api/news?region=India&topic=Technology&source=test"
```

**Includes:**
- 10 pre-written articles
- India & Global articles
- Various topics

**Pros:**
- ✅ Always available
- ✅ No setup required
- ✅ Deterministic responses

**Cons:**
- ⚠️ Mock data only
- Not real news
- Limited articles

---

## 🔄 Automatic Fallback Strategy

If you don't specify `source`, the API tries them in this order:

```
1. RSS          (try first - fastest, free)
   ↓ if fails
2. NewsAPI      (if configured)
   ↓ if fails
3. Guardian     (if configured)
   ↓ if fails
4. Test Data    (always works as fallback)
```

**Example:**
```bash
# Doesn't specify source - tries RS first, then fallbacks
curl "http://localhost:8000/api/news?region=India&topic=Politics&limit=12"

# Response will show which source was used:
{
  "source_used": "rss",
  "sources_tried": ["RSS Feeds"],
  "articles": [...],
  "message": "Fetched from rss"
}
```

---

## 🚀 Setup Instructions

### 1. RSS Feeds (No Setup)
✅ **Already configured - works immediately**

### 2. NewsAPI Setup
```bash
# 1. Go to https://newsapi.org/
# 2. Click "Get API Key" and signup (free)
# 3. Copy your API key
# 4. Add to .env:
NEWSAPI_KEY=your_key_here

# 5. Restart backend
python main.py
```

### 3. Guardian API Setup
```bash
# 1. Go to https://open.theguardian.com/
# 2. Click "Register for free"
# 3. Complete signup (takes ~10 minutes)
# 4. Get your API key
# 5. Add to .env:
GUARDIAN_API_KEY=your_key_here

# 6. Restart backend
python main.py
```

### 4. Install new dependencies
```bash
cd backend
pip install -r requirements.txt
```

---

## 📊 Testing All 4 Options

### Test Script
```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Run tests
curl "http://localhost:8000/api/news?source=rss&limit=5"
curl "http://localhost:8000/api/news?source=newsapi&limit=5"
curl "http://localhost:8000/api/news?source=guardian&limit=5"
curl "http://localhost:8000/api/news?source=test&limit=5"

# Or use Swagger UI: http://localhost:8000/docs
```

### Swagger UI Testing
1. Go to `http://localhost:8000/docs`
2. Find `/api/news` endpoint
3. Click "Try it out"
4. Set `source=rss` (or newsapi, guardian, test)
5. Click "Execute"

---

## 🔧 Configuration File Locations

- **RSS Feeds**: `backend/news_sources/rss_fetcher.py` (line ~15: `RSS_FEEDS` dict)
- **NewsAPI**: `backend/news_sources/newsapi_fetcher.py` (line ~23: `TOPIC_MAPPING`)
- **Guardian API**: `backend/news_sources/guardian_fetcher.py` (line ~17: `TOPIC_MAPPING`)
- **Test Data**: `backend/news_sources/test_data.py` (line ~8: `TEST_ARTICLES`)

---

## 🐛 Troubleshooting

### "401 Unauthorized" from NewsAPI
```
✓ Solution: Check NEWSAPI_KEY in .env is correct
```

### "503 Service Unavailable" from RSS
```
✓ Solution: RSS feed might be down. API will fallback to next source
```

### All sources return 0 articles
```
✓ Solution: Check region/topic filters match available data
✓ Use source=test to verify backend is working
```

### Need to add more RSS feeds
```
✓ Edit: backend/news_sources/rss_fetcher.py
✓ Add URL to RSS_FEEDS dict under appropriate region/topic
```

---

## 📈 Recommended for Production

**Hybrid approach:**
1. ✅ Use RSS as primary (free, fast)
2. ✅ Use NewsAPI as backup (better structured)
3. ✅ Cache results in Redis for 1 hour
4. ✅ Never rely on test data

---

## 📝 File Structure

```
backend/
├── news_sources/
│   ├── __init__.py           # Module entry point
│   ├── rss_fetcher.py        # RSS parser (FREE)
│   ├── newsapi_fetcher.py    # NewsAPI client
│   ├── guardian_fetcher.py   # Guardian API client
│   └── test_data.py          # Mock articles
├── main.py                   # Updated with all sources
├── requirements.txt          # Added httpx, feedparser
├── .env.example             # Configuration template
└── README.md
```

---

## ✅ Next Steps

1. **Choose primary source** based on your needs
2. **Get API keys** (if using NewsAPI or Guardian)
3. **Test with Swagger UI** at `http://localhost:8000/docs`
4. **Configure integration** for production
5. **Set up caching** for frequently requested topics

---

**Questions?** Check the main.py `/api/news` endpoint for all parameter options!
