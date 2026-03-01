# NewsLensAI Clean GCP Learning Guide

## 1. Goal
This document is a clean, practical guide to learn and deploy NewsLensAI on Google Cloud Platform (GCP), using your current working setup.

Current date context: March 1, 2026.

---

## 2. Current Working State (Your Project)

### Backend (Cloud Run)
- Service: `newslensai-backend`
- Region: `asia-south1`
- URL: `https://newslensai-backend-677264443909.asia-south1.run.app`
- Health endpoint: `https://newslensai-backend-677264443909.asia-south1.run.app/health`

### Frontend (Cloud Storage static hosting)
- Bucket: `gs://newslensai-web-677264443909`
- Live URL: `https://storage.googleapis.com/newslensai-web-677264443909/index.html`

### Local Frontend API target
- File: `client/.env`
- Variable: `REACT_APP_API_URL=https://newslensai-backend-677264443909.asia-south1.run.app`

---

## 3. Architecture (Simple)
- React frontend is built into static files.
- Static files are hosted in Cloud Storage.
- API requests from frontend go to FastAPI on Cloud Run.
- Cloud Run container runs `uvicorn` and must listen on port `PORT` (default 8080 in Cloud Run).

---

## 4. One-Time GCP Setup (Project Level)

```powershell
gcloud auth login
gcloud config set project newslensai
gcloud config set run/region asia-south1

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com storage.googleapis.com secretmanager.googleapis.com
```

What you learn:
- `run.googleapis.com`: deploy backend service
- `cloudbuild.googleapis.com`: build container from source
- `artifactregistry.googleapis.com`: stores built images
- `storage.googleapis.com`: static hosting bucket
- `secretmanager.googleapis.com`: secure env vars/secrets

---

## 5. Backend Deployment (Cloud Run)

### Correct command (important)
Always deploy from backend folder, not repo root.

```powershell
gcloud run deploy newslensai-backend --source d:\Training\working\NewsLesAI\backend --allow-unauthenticated --region asia-south1 --platform managed --memory 512Mi --cpu 1 --timeout 300
```

### Why previous deployment failed
1. Deploy from repo root caused buildpack error (`missing-entrypoint`).
2. Container startup failed because Cloud Run expects app to bind to `PORT=8080`.

### Dockerfile rule for Cloud Run
Use:
- `COPY . .` (so all modules are available)
- Start command with `${PORT:-8080}`

---

## 6. Frontend Deployment (Cloud Storage)

### Build
```powershell
cd d:\Training\working\NewsLesAI\client
npm run build
```

### Publish
```powershell
gsutil mb -p newslensai -l asia-south1 gs://newslensai-web-677264443909
gsutil -m rsync -r -d d:\Training\working\NewsLesAI\client\build gs://newslensai-web-677264443909
gsutil web set -m index.html -e index.html gs://newslensai-web-677264443909
gsutil iam ch allUsers:objectViewer gs://newslensai-web-677264443909
```

### Verify
```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://storage.googleapis.com/newslensai-web-677264443909/index.html"
```

---

## 7. Clean Update Workflow (Daily)

### Backend change
1. Edit backend code.
2. Redeploy:
```powershell
gcloud run deploy newslensai-backend --source d:\Training\working\NewsLesAI\backend --allow-unauthenticated --region asia-south1 --platform managed
```

### Frontend change
1. Edit client code.
2. Rebuild and sync:
```powershell
cd d:\Training\working\NewsLesAI\client
npm run build
gsutil -m rsync -r -d build gs://newslensai-web-677264443909
```

---

## 8. Important Security Fixes (Do This Next)

1. Do not keep secrets in `.env` committed to repo.
2. Rotate exposed DB password immediately.
3. Move sensitive values to Secret Manager.

Example:
```powershell
echo -n "<NEW_DB_PASSWORD>" | gcloud secrets create DB_PASSWORD --data-file=-
```

Then attach secrets in Cloud Run:
```powershell
gcloud run services update newslensai-backend --region asia-south1 --set-secrets DB_PASSWORD=DB_PASSWORD:latest
```

---

## 9. Next Learning Milestones (Recommended Order)

1. **Custom domain + HTTPS + CDN**
- Put Cloud Storage bucket behind HTTPS Load Balancer + Cloud CDN.
- Learn URL maps, backend bucket, managed SSL cert.

2. **CI/CD**
- On push to GitHub: auto-build frontend and sync to bucket.
- Auto-deploy backend to Cloud Run.

3. **Cloud Run service hardening**
- Set min/max instances.
- Add request timeout and concurrency tuning.
- Add health and structured logging.

4. **Observability**
- Use Cloud Logging filters by service/revision.
- Create alert policies for 5xx or high latency.

---

## 10. Troubleshooting Quick Table

### A) Build failed: missing entrypoint
Cause: wrong `--source` path.
Fix: deploy from `backend` folder.

### B) Revision not ready: container failed to listen on PORT=8080
Cause: app bound to 8000 only.
Fix: run uvicorn on `${PORT:-8080}`.

### C) Frontend opens but API fails (CORS/network)
Check:
- backend URL in `client/.env`
- Cloud Run service URL reachable
- browser network tab for failing endpoint

---

## 11. Useful Commands Cheat Sheet

```powershell
# Show current project
gcloud config get-value project

# List Cloud Run services
gcloud run services list --region asia-south1

# Describe backend service
gcloud run services describe newslensai-backend --region asia-south1

# Tail recent backend logs
gcloud run services logs read newslensai-backend --region asia-south1 --limit 100

# List recent builds
gcloud builds list --region asia-south1 --limit 10

# Show one build details
gcloud builds describe <BUILD_ID> --region asia-south1
```

---

## 12. What To Do Right Now

1. Keep this deployment as baseline.
2. Rotate DB password and move secrets to Secret Manager.
3. Decide next track:
- Track A: custom domain + CDN
- Track B: GitHub CI/CD automation

---

This guide is intentionally short and practical. It matches your live resources and can be used as your daily deployment playbook while you learn GCP.
