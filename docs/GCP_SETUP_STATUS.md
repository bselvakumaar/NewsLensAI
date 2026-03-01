# 🚀 NewsLensAI - GCP Setup Complete!

## ✅ What Was Created

### 1. **Google Cloud Project**
- ✅ Project ID: `newslensai`
- ✅ Region: `asia-south1` (India)
- ✅ Billing: **Enabled**

### 2. **Google Cloud APIs Enabled** (9 total)
- ✅ Cloud Run (backend deployment)
- ✅ Cloud SQL (database)
- ✅ Redis Memorystore (caching)
- ✅ Vertex AI (LLM - Gemini)
- ✅ Cloud Build (CI/CD)
- ✅ Cloud Scheduler (jobs)
- ✅ Cloud Storage (file uploads)
- ✅ Cloud Logging (monitoring)
- ✅ Compute (instances)

### 3. **Cloud SQL Database**
- ✅ Instance: `newslensai-db`
- ✅ Database: `newslensai`
- ✅ IP Address: **34.93.239.139**
- ✅ Credentials: postgres / NewsLensAI@123456
- ✅ Version: PostgreSQL 15
- ⏳ Tables: Need to create (see below)

### 4. **Redis Cache** (Creating)
- 🔄 Instance: `newslensai-redis`
- 🔄 Size: 1 GB
- 🔄 Tier: Basic (free)
- 🔄 Getting IP address...

### 5. **Cloud Storage Buckets**
- ✅ `gs://newslensai-uploads/` (for uploads)
- ✅ `gs://newslensai-archives/` (for archives)

### 6. **FastAPI Backend** (Local)
- ✅ Location: `backend/` directory
- ✅ Framework: FastAPI + Uvicorn
- ✅ Files:
  - `main.py` - API endpoints
  - `requirements.txt` - Dependencies
  - `.env` - Configuration
  - `Dockerfile` - Container setup
  - `README.md` - Documentation

---

## 🎯 Current Status

```
newsLensAI/
├── client/                    ✅ React Frontend (Running)
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── config/
│   └── .env                   ✅ Updated
│
├── backend/                   ✅ FastAPI Backend (Created)
│   ├── main.py                ✅ API endpoints
│   ├── requirements.txt        ✅ Dependencies
│   ├── .env                    ✅ Configuration
│   ├── Dockerfile             ✅ Container
│   └── README.md              ✅ Documentation
│
├── docs/
│   ├── NewsLensAI_FRD_Technical_Document.docx
│   └── NewsLensAI_PRD.md
│
└── GCP Project: newslensai    ✅ Ready

Cloud Resources:
├── Cloud SQL: newslensai-db   ✅ Database IP: 34.93.239.139
├── Redis: newslensai-redis    🔄 (Creating, check IP below)
├── Storage: 2 buckets         ✅ Created
├── Vertex AI: Enabled         ✅ Ready for LLM
└── Cloud Run: Ready           ✅ For deployment
```

---

## 📋 **Immediate Next Steps** (Today)

### Step 1: Get Redis IP Address

```powershell
gcloud redis instances describe newslensai-redis --region=asia-south1 --format="value(host)"
```

Copy the output and update `backend/.env`:
```env
REDIS_HOST=<paste-redis-ip-here>
```

### Step 2: Create Database Tables

Connect to your database:
```bash
gcloud sql connect newslensai-db --user=postgres
```

When prompted for password, enter: `NewsLensAI@123456`

Then paste and run this SQL (see `backend/README.md` for full script):

```sql
-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Create articles table
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
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chunks (for embeddings)
CREATE TABLE article_chunks (
  id SERIAL PRIMARY KEY,
  article_id INT REFERENCES articles(id),
  chunk_text TEXT,
  embedding_vector vector(768),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create sentiment table
CREATE TABLE sentiment_scores (
  id SERIAL PRIMARY KEY,
  entity VARCHAR(255),
  score FLOAT,
  positive_count INT DEFAULT 0,
  neutral_count INT DEFAULT 0,
  negative_count INT DEFAULT 0,
  date DATE DEFAULT CURRENT_DATE
);

-- Create sessions table
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) UNIQUE,
  user_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_articles_published ON articles(published_at DESC);
CREATE INDEX idx_articles_region ON articles(region);
CREATE INDEX idx_chunks_article ON article_chunks(article_id);
CREATE INDEX idx_chunks_vector ON article_chunks USING ivfflat (embedding_vector vector_cosine_ops);
CREATE INDEX idx_sentiment_entity ON sentiment_scores(entity);
CREATE INDEX idx_sessions_id ON sessions(session_id);
```

Exit with: `\q`

### Step 3: Test Backend Locally

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py
```

Backend starts on: **http://localhost:8000**

### Step 4: Test API

In another PowerShell:
```powershell
# Health check
curl http://localhost:8000/health

# Chat API
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"session_id\":\"test\",\"query\":\"Tell me about India news\"}'
```

### Step 5: Connect Frontend to Backend

React frontend is already set to use `http://localhost:8000` in `.env`.

Start frontend in another terminal:
```powershell
cd client
npm start
# Opens http://localhost:3000
```

---

## 📊 GCP Resources Summary

| Resource | Name | Status | Details |
|----------|------|--------|---------|
| **Project** | newslensai | ✅ Active | Billing enabled |
| **Cloud SQL** | newslensai-db | ✅ Ready | IP: 34.93.239.139 |
| **Database** | newslensai | ✅ Ready | Tables: pending |
| **Redis** | newslensai-redis | 🔄 Creating | Check IP |
| **Storage** | newslensai-uploads | ✅ Ready | gs://newslensai-uploads/ |
| **Storage** | newslensai-archives | ✅ Ready | gs://newslensai-archives/ |
| **Cloud Run** | - | ✅ Ready | Deploy via Docker |
| **Vertex AI** | Gemini 1.5 Flash | ✅ Ready | For LLM calls |

---

## 🔐 Credentials Reference

**Database:**
- Host: `34.93.239.139`
- Database: `newslensai`
- User: `postgres`
- Password: `NewsLensAI@123456`

**Redis:**
- Host: (Get from `gcloud redis instances describe`)
- Port: `6379`

**GCP Project:**
- Project ID: `newslensai`
- Region: `asia-south1`

---

## 🚀 **Architecture Now**

```
┌─────────────────────────────────────────────┐
│       React Frontend (localhost:3000)       │
│  ChatInterface | NewsDisplay | Sentiment    │
└────────────────────┬────────────────────────┘
                     │
                 (api calls)
                     │
                     ▼
┌─────────────────────────────────────────────┐
│      FastAPI Backend (localhost:8000)       │
│  /api/chat | /api/news | /api/sentiment    │
└────────────────────┬────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌─────────┐
   │ Cloud  │  │ Redis  │  │ Vertex  │
   │  SQL   │  │ Cache  │  │   AI    │
   └────────┘  └────────┘  │ (LLM)   │
                           └─────────┘
```

---

## ⏱️ Time to Deployment

- **Local Testing**: ~5 minutes (setup backend + test)
- **Database Tables**: ~2 minutes (run SQL)
- **Cloud Run Deployment**: ~5 minutes (docker build + deploy)
- **Full Setup**: ~12 minutes

---

## 📚 Documentation

- **Frontend**: `client/README.md`
- **Backend**: `backend/README.md`  
- **Setup Guide**: `SETUP_GUIDE.md`
- **Quick Reference**: `QUICK_REFERENCE.md`
- **Product Strategy**: `docs/NewsLensAI_PRD.md`

---

## ✨ What's Next?

1. ⏳ Get Redis IP address
2. ⏳ Create database tables
3. ⏳ Test backend locally
4. ⏳ Test frontend ↔ backend connection
5. ⏳ Deploy to Cloud Run
6. ⏳ Add Vertex AI integration
7. ⏳ Go live!

---

**Status**: GCP Infrastructure Complete ✅  
**Frontend**: Running ✅  
**Backend**: Ready for testing ⏳  
**Next**: Database tables + Local testing

**Reply when Redis is created or when you need clarification!** 🚀
