# NewsLensAI Backend - Setup & Deployment Guide

## 📋 Overview

This is the FastAPI backend for NewsLensAI - a RAG-powered news intelligence platform.

**Features:**
- ✅ RESTful API with FastAPI
- ✅ Cloud SQL PostgreSQL database
- ✅ Redis caching
- ✅ Vertex AI Gemini LLM integration (ready)
- ✅ RAG (Retrieval-Augmented Generation) pipeline (ready)

**Google Cloud Infrastructure:**
- Cloud SQL: `newslensai-db` (PostgreSQL 15, India region)
- Redis: `newslensai-redis` (1GB, Memorystore)
- Cloud Run: Ready for deployment
- Vertex AI: Ready for LLM calls

---

## 🚀 Local Development Setup

### Step 1: Create Virtual Environment

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Edit `.env` file with your settings:

```env
GCP_PROJECT_ID=newslensai
DB_HOST=34.93.239.139           # Your Cloud SQL IP
DB_PORT=5432
DB_NAME=newslensai
DB_USER=postgres
DB_PASSWORD=NewsLensAI@123456
PORT=8000
ENV=development
```

### Step 4: Run Development Server

```bash
python main.py
# or with auto-reload:
uvicorn main:app --reload
```

Server runs on: **http://localhost:8000**

### Step 5: Test the API

```bash
# Health check
curl http://localhost:8000/health

# Send chat query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","query":"What is the latest India news?"}'

# Get news
curl http://localhost:8000/api/news?region=India&limit=5

# Get sentiment
curl http://localhost:8000/api/sentiment?entity=PrimeMinister
```

---

## 🗄️ Database Setup

### Current Status
✅ Cloud SQL instance created: `newslensai-db`
✅ Database created: `newslensai`
⏳ Tables: Need to create

### Create Tables (SQL)

Connect to your database and run:

```bash
gcloud sql connect newslensai-db --user=postgres
```

Then run these SQL commands:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Articles table
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  summary TEXT,
  source VARCHAR(100),
  region VARCHAR(50),
  topic VARCHAR(50),
  published_at TIMESTAMP NOT NULL,
  url VARCHAR(500),
  image_url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Article chunks for embeddings
CREATE TABLE article_chunks (
  id SERIAL PRIMARY KEY,
  article_id INT REFERENCES articles(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  embedding_vector vector(768),
  chunk_index INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment scores
CREATE TABLE sentiment_scores (
  id SERIAL PRIMARY KEY,
  entity VARCHAR(255),
  score FLOAT,  -- Range: -1 to 1
  positive_count INT DEFAULT 0,
  neutral_count INT DEFAULT 0,
  negative_count INT DEFAULT 0,
  date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat sessions
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) UNIQUE NOT NULL,
  user_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_region ON articles(region);
CREATE INDEX idx_articles_topic ON articles(topic);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_chunks_article ON article_chunks(article_id);
CREATE INDEX idx_chunks_vector ON article_chunks USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists=100);
CREATE INDEX idx_sentiment_entity ON sentiment_scores(entity);
CREATE INDEX idx_sentiment_date ON sentiment_scores(date);
CREATE INDEX idx_sessions_id ON sessions(session_id);
```

### Connect from Backend

Update the connection string in `.env`:

```env
DB_HOST=34.93.239.139
DB_PORT=5432
DB_NAME=newslensai
DB_USER=postgres
DB_PASSWORD=NewsLensAI@123456
```

---

## 🔴 Redis Setup

### Check Redis Status

```bash
gcloud redis instances describe newslensai-redis --region=asia-south1
```

Get the IP address and port, then update `.env`:

```env
REDIS_HOST=<your-redis-ip>
REDIS_PORT=6379
```

### Connect from Backend

```python
import redis
cache = redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')))
```

---

## 🤖 Vertex AI Setup (LLM Integration)

### Enable Vertex AI API

✅ Already enabled in the project!

### Install Google Cloud SDK

```bash
# Already have gcloud installed from earlier
gcloud --version
```

### Setup Vertex AI in Backend

In `main.py`, the RAG integration will look like:

```python
from vertexai.generative_models import GenerativeModel

# Initialize
model = GenerativeModel("gemini-1.5-flash")

# Call LLM
response = model.generate_content(
    f"Context: {context}\n\nQuestion: {query}"
)
```

---

## 📦 API Endpoints

### Health Check
```
GET /health
Response: {"status": "healthy", "version": "1.0.0", ...}
```

### Chat (RAG)
```
POST /api/chat
Body: {"session_id": "...", "query": "..."}
Response: {"answer": "...", "sources": [...], "region": "..."}
```

### News
```
GET /api/news?region=India&topic=Politics&limit=12
Response: {"articles": [...], "total": 123}
```

### Sentiment
```
GET /api/sentiment?entity=PrimeMinister&days=7
Response: {"sentiments": [...], "region": "..."}
```

### Create Session
```
POST /api/sessions?user_id=optional
Response: {"session_id": "...", "created_at": "..."}
```

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t newslensai-backend:latest .
```

### Run Locally with Docker

```bash
docker run -p 8000:8000 \
  -e GCP_PROJECT_ID=newslensai \
  -e DB_HOST=34.93.239.139 \
  -e DB_PASSWORD=NewsLensAI@123456 \
  newslensai-backend:latest
```

### Deploy to Cloud Run

```bash
# From backend directory
gcloud run deploy newslensai-backend \
  --source . \
  --platform managed \
  --region asia-south1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=newslensai,DB_HOST=34.93.239.139,DB_PASSWORD=NewsLensAI@123456"

# Get the URL
gcloud run services describe newslensai-backend --region asia-south1 --format="value(status.url)"
```

---

## 🔗 Connect Frontend to Backend

Once deployed, update `client/.env`:

```env
# For local development:
REACT_APP_API_URL=http://localhost:8000

# For Cloud Run deployment:
REACT_APP_API_URL=https://newslensai-backend-xxx.run.app
```

Then restart React:
```bash
cd client
npm start
```

---

## 📊 Key Resources

| Resource | Status | Details |
|----------|--------|---------|
| Cloud SQL | ✅ Ready | `newslensai-db`, IP: 34.93.239.139 |
| Database | ✅ Created | `newslensai` database ready |
| Tables | ⏳ To Create | Run SQL above |
| Redis | ✅ Creating | Check status below |
| Vertex AI | ✅ Enabled | Ready for LLM calls |
| Cloud Run | ✅ Ready | Deploy the Docker image |

---

## 🧪 Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
# Test database connection
python -c "import psycopg2; conn = psycopg2.connect('...'); print('Connected!')"

# Test Redis connection
python -c "import redis; r = redis.Redis(...); print(r.ping())"

# Test Vertex AI
python -c "from vertexai.generative_models import GenerativeModel; m = GenerativeModel('gemini-1.5-flash'); print('Ready')"
```

---

## 📈 Performance Monitoring

### Cloud Logging

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=newslensai-backend" --limit=50
```

### Cloud Monitoring

View in Console: https://console.cloud.google.com/monitoring

---

## 🚀 Next Steps

1. ✅ Backend created
2. ⏳ Create database tables (SQL commands above)
3. ⏳ Get Redis IP and update `.env`
4. ⏳ Test API locally
5. ⏳ Integrate with Vertex AI
6. ⏳ Deploy to Cloud Run
7. ⏳ Connect frontend to Cloud Run

---

**Backend Status**: Ready for local testing  
**Database**: Ready (tables need creation)  
**Next**: Connect to frontend and test!
