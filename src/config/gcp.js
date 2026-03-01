// Google Cloud Platform Configuration
// Setup for free tier development and deployment

const GCP_CONFIG = {
  // Project Configuration
  PROJECT_ID: process.env.REACT_APP_GCP_PROJECT_ID || 'newslensai-dev',
  REGION: process.env.REACT_APP_GCP_REGION || 'asia-south1', // India region for lower latency
  ENVIRONMENT: process.env.REACT_APP_ENV || 'development',

  // Cloud Run Configuration (Free Tier: 180,000 vCPU-seconds/month)
  CLOUD_RUN: {
    SERVICE_NAME: 'newslensai-backend',
    MEMORY: '512Mi', // 512MB memory - free tier sufficient
    CPU: '1', // 1 vCPU
    TIMEOUT: '300s', // 5 minutes
    CONCURRENCY: 80, // Max concurrent requests
  },

  // Vertex AI Configuration (Free tier LLM credits available)
  VERTEX_AI: {
    MODEL_NAME: 'gemini-1.5-flash', // Fast, cost-effective for free tier
    TEMPERATURE: 0.7,
    MAX_TOKENS: 1024,
    TOP_K: 40,
    TOP_P: 0.95,
    LOCATION: 'asia-south1', // India region
  },

  // Vertex Embeddings Configuration
  EMBEDDINGS: {
    MODEL_NAME: 'text-embedding-004',
    DIMENSIONS: 768,
    BATCH_SIZE: 100,
    LOCATION: 'asia-south1',
  },

  // Vector Database - pgvector (Free Tier PostgreSQL on Cloud SQL)
  VECTOR_DB: {
    TYPE: 'postgresql', // Using pgvector with Cloud SQL
    HOST: process.env.REACT_APP_DB_HOST || 'localhost',
    PORT: 5432,
    DATABASE: 'newslensai',
    VECTOR_SIZE: 768,
    SIMILARITY_METRIC: 'cosine', // Cosine similarity for embeddings
  },

  // Cloud SQL Configuration (Free Tier: 1 shared-core instance, 0.6GB RAM, 10GB storage)
  CLOUD_SQL: {
    NAME: 'newslensai-postgres',
    TIER: 'db-f1-micro', // Free tier
    VERSION: 'POSTGRES_15',
    STORAGE_GB: 10, // Free tier limit
    STORAGE_TYPE: 'PD_SSD',
    BACKUP_LOCATION: 'asia-south1',
  },

  // Redis Cache Configuration (Free Tier via Memorystore)
  REDIS: {
    INSTANCE_NAME: 'newslensai-redis',
    MEMORY_SIZE_GB: 1, // Free tier (0.5-1 GB)
    REGION: 'asia-south1',
    TIER: 'basic', // Basic tier for free usage
  },

  // Cloud Storage Configuration (Free Tier: 5GB/month free)
  STORAGE: {
    BUCKET_NAME: 'newslensai-dev-uploads',
    ARCHIVE_BUCKET: 'newslensai-archives',
    LOCATION: 'asia-south1',
  },

  // Cloud Scheduler Configuration (Free Tier: 3 jobs)
  SCHEDULER: {
    TIMEZONE: 'Asia/Kolkata',
    NEWS_INGEST_SCHEDULE: '0 */30 * * * *', // Every 30 minutes
    SENTIMENT_UPDATE_SCHEDULE: '0 0 * * *', // Daily at midnight
    CLEANUP_SCHEDULE: '0 2 * * 0', // Weekly cleanup
  },

  // Secrets Manager
  SECRETS: {
    NEWS_API_KEY: 'projects/PROJECT_ID/secrets/news-api-key/versions/latest',
    LLM_API_KEY: 'projects/PROJECT_ID/secrets/vertex-ai-key/versions/latest',
    DB_PASSWORD: 'projects/PROJECT_ID/secrets/db-password/versions/latest',
  },

  // Monitoring & Logging (Free Tier: 50GB/month free logs)
  MONITORING: {
    LOG_LEVEL: 'INFO',
    METRICS_ENABLED: true,
    TRACE_ENABLED: true,
    ERROR_REPORTING_ENABLED: true,
  },

  // Frontend API Configuration
  API: {
    BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
    TIMEOUT: 10000, // 10 seconds
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000, // 1 second
  },

  // Feature Flags
  FEATURES: {
    CHAT_ENABLED: true,
    SENTIMENT_ANALYSIS: false, // Phase 2
    POLITICAL_DASHBOARD: false, // Phase 2
    FINANCIAL_INTELLIGENCE: false, // Phase 2
    WHATSAPP_BOT: false, // Phase 3
    ELECTION_TRACKER: false, // Phase 3
  },
};

// Deployment Instructions for Google Cloud Free Tier
export const GCP_DEPLOYMENT_GUIDE = `
=== NewsLensAI Deployment Guide (Google Cloud Free Tier) ===

1. SETUP GOOGLE CLOUD PROJECT
   gcloud init
   gcloud config set project newslensai-dev
   gcloud auth login

2. ENABLE REQUIRED APIs
   gcloud services enable run.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   gcloud services enable redis.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable scheduler.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable logging.googleapis.com

3. CREATE CLOUD SQL INSTANCE (PostgreSQL Free Tier)
   gcloud sql instances create newslensai-postgres \\
     --database-version=POSTGRES_15 \\
     --tier=db-f1-micro \\
     --region=asia-south1 \\
     --network=default \\
     --availability-type=zonal

4. CREATE DATABASE & TABLES
   gcloud sql databases create newslensai --instance=newslensai-postgres
   
   # Connect and run DDL scripts
   gcloud sql connect newslensai-postgres --user=postgres

5. ENABLE pgvector EXTENSION
   CREATE EXTENSION vector;

6. CREATE REDIS INSTANCE (Memorystore)
   gcloud redis instances create newslensai-redis \\
     --size=1 \\
     --region=asia-south1 \\
     --memory-size-gb=1 \\
     --tier=basic \\
     --redis-version=7.0

7. CREATE STORAGE BUCKETS
   gsutil mb -l asia-south1 gs://newslensai-dev-uploads
   gsutil mb -l asia-south1 gs://newslensai-archives

8. SET UP SERVICE ACCOUNT
   gcloud iam service-accounts create newslensai-backend \\
     --description="NewsLensAI Backend" \\
     --display-name="NewsLensAI Backend"
   
   gcloud projects add-iam-policy-binding newslensai-dev \\
     --member=serviceAccount:newslensai-backend@newslensai-dev.iam.gserviceaccount.com \\
     --role=roles/cloudsql.client
   
   gcloud projects add-iam-policy-binding newslensai-dev \\
     --member=serviceAccount:newslensai-backend@newslensai-dev.iam.gserviceaccount.com \\
     --role=roles/ai.user

9. DEPLOY BACKEND TO CLOUD RUN
   gcloud run deploy newslensai-backend \\
     --source . \\
     --platform managed \\
     --region asia-south1 \\
     --memory 512Mi \\
     --cpu 1 \\
     --timeout 300 \\
     --service-account newslensai-backend@newslensai-dev.iam.gserviceaccount.com \\
     --set-env-vars "GCP_PROJECT_ID=newslensai-dev,DB_HOST=127.0.0.1" \\
     --allow-unauthenticated

10. SETUP CLOUD SCHEDULER JOBS
    gcloud scheduler jobs create pubsub news-ingest \\
      --schedule="0 */30 * * * *" \\
      --topic=news-ingestion \\
      --message-body='{"action":"ingest"}'

11. DEPLOY FRONTEND (React) TO CLOUD STORAGE + CLOUD CDN
    npm run build
    gsutil -m cp -r build/* gs://newslensai-dev-uploads/
    gsutil web set -m index.html -e 404.html gs://newslensai-dev-uploads

12. SETUP CLOUD CDN (Optional, for faster delivery)
    # Create backend for bucket
    gcloud compute backend-buckets create newslensai-frontend \\
      --gcs-uri-prefix=gs://newslensai-dev-uploads

13. MONITOR & LOGS
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=newslensai-backend"

FREE TIER QUOTAS & LIMITS:
- Cloud Run: 180,000 vCPU-seconds/month = ~1500 hours
- Vertex AI (LLM): $300 free credits for new users
- Cloud SQL: 1 shared-core instance, 0.6GB RAM, 10GB storage
- Cloud Storage: 5GB/month egress, 1M PUT requests
- Cloud Scheduler: 3 jobs
- Cloud Logging: 50GB/month ingestion
- Compute: 1 f1-micro instance free each month

COST ESTIMATE (Monthly):
- Cloud Run: ~$0 (within free tier)
- Cloud SQL: ~$0 (within free tier)
- Vertex AI: ~$0 (within free credits for first month)
- Storage: ~$0 (minimal egress)
- Total: $0-$50/month during development
`;

export default GCP_CONFIG;
