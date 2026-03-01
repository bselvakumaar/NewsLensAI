# NewsLensAI MVP - Setup & Deployment Guide

## 📋 Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Google Cloud Free Tier Setup](#google-cloud-free-tier-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Learning Path](#learning-path)

---

## Local Development Setup

### Step 1: Install Prerequisites

**On Windows:**
```bash
# Install Node.js from https://nodejs.org/
# Verify installation
node --version
npm --version

# Install Python 3.8+ from https://python.org/
python --version
```

**On macOS/Linux:**
```bash
# Using Homebrew
brew install node python@3.11

# Verify
node --version
npm --version
python3 --version
```

### Step 2: Setup React Frontend

```bash
# Navigate to project root
cd d:\Training\working\NewsLesAI

# Client is already created, install dependencies
cd client
npm install

# Copy and configure environment
cp .env.example .env
# Edit .env with text editor
```

### Step 3: Start Development Server

```bash
# From client directory
npm start

# Opens http://localhost:3000 automatically
# Hot reload enabled - changes auto-refresh
```

### Step 4: Create Mock Backend (Optional)

For testing without backend:

```bash
# Install mock server (json-server)
npm install -g json-server

# Create db.json with mock data
# See next section for sample data
```

---

## Google Cloud Free Tier Setup

### Step 1: Create GCP Account & Project

```bash
# Visit https://cloud.google.com/free
# Create new account or sign in

# Once logged in, create project
gcloud init

# Follow prompts to authenticate
gcloud auth login

# Set project
gcloud config set project newslensai-dev
```

### Step 2: Enable Required APIs

```bash
# Enable all required APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  scheduler.googleapis.com \
  storage-api.googleapis.com \
  logging.googleapis.com \
  compute.googleapis.com

# Verify
gcloud services list --enabled
```

### Step 3: Create Cloud SQL PostgreSQL Instance

```bash
# Create instance (1 vCPU, 0.6GB RAM - free tier)
gcloud sql instances create newslensai-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --network=default \
  --availability-type=zonal \
  --storage-auto-increase

# Create database
gcloud sql databases create newslensai \
  --instance=newslensai-postgres

# Get connection details
gcloud sql instances describe newslensai-postgres
```

### Step 4: Connect & Setup Database

```bash
# Connect to instance (requires Cloud SQL Proxy or Cloud Console)
gcloud sql connect newslensai-postgres --user=postgres

# In PostgreSQL prompt, run:
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables (see DDL below)
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title VARCHAR(500),
  content TEXT,
  source VARCHAR(100),
  region VARCHAR(50),
  topic VARCHAR(50),
  published_at TIMESTAMP,
  url VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE article_chunks (
  id SERIAL PRIMARY KEY,
  article_id INT REFERENCES articles(id),
  chunk_text TEXT,
  embedding_vector vector(768),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_region ON articles(region);
CREATE INDEX idx_articles_topic ON articles(topic);
CREATE INDEX idx_chunks_vector ON article_chunks USING ivfflat (embedding_vector vector_cosine_ops);
```

### Step 5: Create Redis Cache

```bash
# Create Redis instance (1GB - free tier eligible)
gcloud redis instances create newslensai-redis \
  --size=1 \
  --region=asia-south1 \
  --memory-size-gb=1 \
  --tier=basic \
  --redis-version=7.0

# Get connection details
gcloud redis instances describe newslensai-redis --region=asia-south1
```

### Step 6: Create Cloud Storage Buckets

```bash
# Create buckets
gsutil mb -l asia-south1 gs://newslensai-dev-uploads
gsutil mb -l asia-south1 gs://newslensai-dev-archives

# Configure CORS for web access
echo '[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "DELETE"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]' > cors.json

gsutil cors set cors.json gs://newslensai-dev-uploads
gsutil cors set cors.json gs://newslensai-dev-archives
```

---

## Backend Deployment

### Step 1: Create Backend Project Structure

```bash
mkdir backend
cd backend

# Create FastAPI project (create these files:)
touch main.py
touch requirements.txt
touch .env
touch Dockerfile
touch .dockerignore
```

### Step 2: Create Basic FastAPI Backend

**backend/main.py:**
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

app = FastAPI(title="NewsLensAI Backend", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    session_id: str
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list = []
    region: str = "Global"

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # TODO: Implement RAG logic with Vertex AI
    return ChatResponse(
        answer="This is a test response. Backend integration needed.",
        sources=[],
        region="Global"
    )

@app.get("/api/news")
async def get_news(region: str = "India", topic: str = None, limit: int = 12):
    # TODO: Fetch from Cloud SQL
    return {"articles": []}

@app.get("/api/sentiment")
async def get_sentiment(entity: str = None, region: str = "India", days: int = 7):
    # TODO: Fetch sentiment analysis from Cloud SQL
    return {"sentiments": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**backend/requirements.txt:**
```
fastapi==0.104.1
uvicorn==0.24.1
google-cloud-sql==1.4.3
google-cloud-redis==2.13.1
google-cloud-aiplatform==1.41.0
google-cloud-logging==3.8.0
python-dotenv==1.0.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
pydantic==2.5.0
```

### Step 3: Containerize Backend

**backend/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**backend/.dockerignore:**
```
__pycache__
*.pyc
.env
.git
.gitignore
venv/
```

### Step 4: Deploy to Cloud Run

```bash
# From backend directory
cd backend

# Build and push
gcloud run deploy newslensai-backend \
  --source . \
  --platform managed \
  --region asia-south1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=newslensai-dev,DB_HOST=cloudsql,REDIS_HOST=memorystore"

# Get service URL
gcloud run services describe newslensai-backend --region asia-south1
```

---

## Frontend Deployment

### Step 1: Build React App

```bash
cd client
npm run build

# Build output in ./build directory (~3.5MB)
# Optimized for production
```

### Step 2: Deploy to Cloud Storage + Cloud CDN

```bash
# Upload to storage
gsutil -m cp -r build/* gs://newslensai-dev-uploads/

# Configure as website
gsutil web set -m index.html -e 404.html gs://newslensai-dev-uploads/

# Make public (optional)
gsutil iam ch allUsers:objectViewer gs://newslensai-dev-uploads
```

### Step 3: Setup Cloud CDN (Optional)

```bash
# Create backend bucket
gcloud compute backend-buckets create newslensai-frontend \
  --gcs-uri-prefix=gs://newslensai-dev-uploads

# Create load balancer with CDN
gcloud compute url-maps create newslensai-lb \
  --default-service newslensai-frontend

gcloud compute target-https-proxies create newslensai-https \
  --url-map=newslensai-lb \
  --ssl-certificates=newslensai-cert

gcloud compute forwarding-rules create newslensai-fr \
  --global \
  --target-https-proxy=newslensai-https \
  --address=newslensai-ip \
  --ports=443
```

---

## Learning Path

### Week 1: React Fundamentals
- [ ] Components & JSX
- [ ] State & Props
- [ ] Hooks (useState, useEffect)
- [ ] Styling with CSS

**Resources:**
- React Docs: https://react.dev
- React Tutorial: https://www.reactjs.org/docs/hello-world.html

### Week 2: Google Cloud Basics
- [ ] Cloud Run deployment
- [ ] Cloud SQL setup
- [ ] Identity & Authentication
- [ ] Logging & Monitoring

**Resources:**
- GCP Free Tier: https://cloud.google.com/free
- Cloud Run Quickstart: https://cloud.google.com/run/docs/quickstarts
- Cloud SQL Guide: https://cloud.google.com/sql/docs

### Week 3: API Integration
- [ ] RESTful APIs
- [ ] Fetch API & Async/Await
- [ ] Error Handling
- [ ] CORS Configuration

**Resources:**
- MDN REST API: https://developer.mozilla.org/en-US/docs/Glossary/REST
- Fetch API: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API

### Week 4: Vertex AI Integration
- [ ] Vertex AI setup
- [ ] LLM API calls
- [ ] Embeddings generation
- [ ] RAG implementation

**Resources:**
- Vertex AI Docs: https://cloud.google.com/vertex-ai/docs
- Gemini API: https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts

### Week 5+: Production Readiness
- [ ] Performance optimization
- [ ] Security hardening
- [ ] CI/CD setup (GitHub Actions)
- [ ] Monitoring & Alerts

---

## Cost Tracking

### Monthly Free Tier Quotas

| Service | Free Tier | Usage | Cost |
|---------|-----------|-------|------|
| Cloud Run | 180,000 vCPU-sec | ~1500 hrs | $0 |
| Cloud SQL | f1-micro, 10GB | Shared CPU | $0 |
| Vertex AI | $300 credits | LLM API | $0 |
| Cloud Storage | 5GB/month egress | < 1GB | $0 |
| Cloud Scheduler | 3 jobs | 3 jobs | $0 |
| Cloud Logging | 50GB/month | < 10GB | $0 |
| Redis | 1GB basic | 250MB/month | $0 |
| **Total** | | | **$0/month** |

### Cost Warnings

To avoid unexpected charges:
1. Set up billing alerts at $10
2. Review Cloud SQL backup settings
3. Monitor Cloud Storage egress
4. Enable Cloud Scheduler pause after limits

---

## Troubleshooting

### Cloud SQL Connection Issues
```bash
# Test connection
gcloud sql connect newslensai-postgres --user=postgres

# Check firewall
gcloud sql instances patch newslensai-postgres \
  --allowed-networks=0.0.0.0/0
```

### API Deployment Fails
```bash
# Check logs
gcloud run logs read newslensai-backend --region=asia-south1

# Rebuild
gcloud run deploy newslensai-backend \
  --source . \
  --region asia-south1 \
  --no-cache
```

### Frontend CORS Errors
```bash
# Verify CORS on backend
curl -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/api/chat -v

# Backend must include CORS headers
```

---

## Next Steps

1. ✅ Create UI (DONE - you're here!)
2. Next: Build FastAPI backend with Vertex AI integration
3. Then: Connect frontend to backend
4. Finally: Deploy to GCP free tier

**Estimated Timeline**: 4-6 weeks for full MVP with learning

---

**DocumenVersion**: 1.0
**Last Updated**: March 2026
