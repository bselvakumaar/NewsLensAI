# NewsLensAI CI/CD Setup (GitHub Actions -> GCP)

This guide explains exactly how CI/CD is initiated and how deployment happens.

## 1. Where CI/CD is initiated
- Trigger file: `.github/workflows/deploy-gcp.yml`
- Trigger events:
  - Push to `master`
  - Manual run from GitHub Actions (`workflow_dispatch`)

When you push code to `master`, GitHub Actions starts automatically.

## 2. What this pipeline deploys
- `deploy-frontend` job:
  - Builds React app (`npm ci`, `npm run build`)
  - Uploads `build/` to Cloud Storage bucket via `gsutil rsync`
- `deploy-backend` job:
  - Runs when `backend/Dockerfile` exists in the same GitHub repo
  - Deploys backend source to Cloud Run with `gcloud run deploy --source ./backend`
  
Current status in this repo: `backend/` is included, so backend deployment is active in CI/CD.

## 3. Required GitHub Secrets
Create these in GitHub:
- Repo -> `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`

Required secrets:
1. `GCP_SA_KEY`
2. `GCP_PROJECT_ID`
3. `GCP_REGION`
4. `GCS_BUCKET`
5. `REACT_APP_API_URL`
6. `CLOUD_RUN_SERVICE`

Recommended values for your project:
- `GCP_PROJECT_ID`: `newslensai`
- `GCP_REGION`: `asia-south1`
- `GCS_BUCKET`: `newslensai-web-677264443909`
- `REACT_APP_API_URL`: `https://newslensai-backend-677264443909.asia-south1.run.app`
- `CLOUD_RUN_SERVICE`: `newslensai-backend`

## 4. Create Service Account for CI/CD
Run these commands locally:

```powershell
gcloud config set project newslensai

gcloud iam service-accounts create github-deployer `
  --display-name=\"GitHub Actions Deployer\"

gcloud projects add-iam-policy-binding newslensai `
  --member=\"serviceAccount:github-deployer@newslensai.iam.gserviceaccount.com\" `
  --role=\"roles/storage.admin\"

gcloud projects add-iam-policy-binding newslensai `
  --member=\"serviceAccount:github-deployer@newslensai.iam.gserviceaccount.com\" `
  --role=\"roles/run.admin\"

gcloud projects add-iam-policy-binding newslensai `
  --member=\"serviceAccount:github-deployer@newslensai.iam.gserviceaccount.com\" `
  --role=\"roles/cloudbuild.builds.editor\"

gcloud projects add-iam-policy-binding newslensai `
  --member=\"serviceAccount:github-deployer@newslensai.iam.gserviceaccount.com\" `
  --role=\"roles/artifactregistry.writer\"

gcloud projects add-iam-policy-binding newslensai `
  --member=\"serviceAccount:github-deployer@newslensai.iam.gserviceaccount.com\" `
  --role=\"roles/iam.serviceAccountUser\"
```

Create key file:
```powershell
gcloud iam service-accounts keys create github-deployer-key.json `
  --iam-account=github-deployer@newslensai.iam.gserviceaccount.com
```

Open `github-deployer-key.json`, copy full JSON content, save it in GitHub secret `GCP_SA_KEY`.

## 5. How deployment happens after push
1. You push to `master`.
2. GitHub Action starts.
3. Frontend build is created with production env vars.
4. Build artifacts sync to `gs://<GCS_BUCKET>`.
5. Static site live at:
   - `https://storage.googleapis.com/<GCS_BUCKET>/index.html`
6. If backend folder exists in repo, backend gets redeployed to Cloud Run.

## 6. Verify in GitHub and GCP
- GitHub:
  - `Actions` tab -> `Deploy To GCP` workflow run
- GCP:
  - Storage bucket objects updated
  - (Optional) Cloud Run new revision if backend job runs

## 7. Manual fallback commands
If Actions fails, deploy manually:

Frontend:
```powershell
npm run build
gsutil -m rsync -r -d build gs://newslensai-web-677264443909
```

Backend:
```powershell
gcloud run deploy newslensai-backend --source d:\\Training\\working\\NewsLesAI\\backend --allow-unauthenticated --region asia-south1 --platform managed
```

## 8. Security note
- `GCP_SA_KEY` is sensitive. Never commit JSON key files.
- Long-term best practice: move to Workload Identity Federation (keyless auth).
