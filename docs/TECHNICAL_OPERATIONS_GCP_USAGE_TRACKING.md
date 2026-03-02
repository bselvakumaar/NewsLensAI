# NewsLensAI Technical Operations Document

## 1. Purpose
This document defines the technical architecture, GCP resource inventory, and production operations model for NewsLensAI with focus on:

- Resource usage tracking
- Cost tracking
- Performance tracking
- External ingestion control
- Incident response runbooks

This is aligned with the current project codebase as of 2026-03-02.

---

## 2. System Architecture

### 2.1 Application Components
- Frontend: React static build hosted in Google Cloud Storage
- Backend: FastAPI service on Cloud Run (`newslensai-backend`)
- Retrieval/LLM: RAG pipeline with retrieved article context
- News ingestion:
  - Internal loop (backend runtime auto-ingestion)
  - External scheduler trigger endpoint (Cloud Scheduler)
- Data source fetchers:
  - RSS feeds
  - NewsAPI (if key configured)
  - Guardian API (if key configured)
  - Test fallback data

### 2.2 Data Flow
1. User sends query from UI to `/api/chat`.
2. Backend checks live ingested article cache.
3. If cache is stale or empty, backend ingests fresh web data.
4. RAG pipeline retrieves relevant articles and generates structured response.
5. Response returns summary, region, sources, confidence, last_updated.

### 2.3 Key Runtime Controls
- `EXTERNAL_INGESTION_ENABLED`: allows/disables external scheduler-triggered ingestion
- `AUTO_INGEST_ENABLED`: allows/disables internal periodic ingestion loop
- `AUTO_INGEST_INTERVAL_MINUTES`: ingestion loop interval
- `SCHEDULER_INGEST_TOKEN`: auth token for scheduler trigger endpoint

---

## 3. GCP Resource Inventory

## 3.1 Core Resources (from current project docs/code)
- Project: `newslensai`
- Region: `asia-south1`
- Cloud Run service: `newslensai-backend`
- Cloud SQL instance: `newslensai-db` (PostgreSQL)
- Memorystore Redis: `newslensai-redis`
- Storage buckets:
  - `gs://newslensai-web-677264443909` (frontend static hosting)
  - `gs://newslensai-uploads`
  - `gs://newslensai-archives`
- Cloud Scheduler job (recommended): `newslensai-external-ingest`

## 3.2 Required APIs
- `run.googleapis.com`
- `cloudbuild.googleapis.com`
- `artifactregistry.googleapis.com`
- `storage.googleapis.com`
- `sqladmin.googleapis.com`
- `redis.googleapis.com`
- `cloudscheduler.googleapis.com`
- `monitoring.googleapis.com`
- `logging.googleapis.com`
- `billingbudgets.googleapis.com`

Enable check:

```powershell
gcloud services list --enabled --project newslensai
```

---

## 4. Backend Endpoints for Ingestion Control

## 4.1 Existing Operational Endpoints
- `POST /api/admin/ingest`
- `GET /api/admin/ingest-live-status`
- `GET /api/admin/ingest-settings`
- `PUT /api/admin/ingest-settings`
- `POST /api/admin/ingest/scheduler-trigger`

## 4.2 Scheduler Trigger Authentication
Set backend env:

```env
SCHEDULER_INGEST_TOKEN=<long-random-secret>
```

Scheduler sends:

```http
Authorization: Bearer <same-secret>
```

---

## 5. Cloud Scheduler Setup and Control

The repository includes:
- `scripts/setup_scheduler.ps1`

### 5.1 Create job
```powershell
.\scripts\setup_scheduler.ps1 `
  -Action create `
  -ProjectId newslensai `
  -Region asia-south1 `
  -ServiceName newslensai-backend `
  -JobName newslensai-external-ingest `
  -Schedule "*/30 * * * *" `
  -TimeZone "Asia/Kolkata" `
  -SchedulerToken "<YOUR_SECRET>"
```

### 5.2 Pause external ingestion
```powershell
.\scripts\setup_scheduler.ps1 -Action pause -ProjectId newslensai -Region asia-south1
```

### 5.3 Resume external ingestion
```powershell
.\scripts\setup_scheduler.ps1 -Action resume -ProjectId newslensai -Region asia-south1
```

### 5.4 Runtime stop without touching Scheduler
```powershell
Invoke-RestMethod `
  -Method Put `
  -Uri "https://<CLOUD_RUN_URL>/api/admin/ingest-settings" `
  -ContentType "application/json" `
  -Body '{"external_ingestion_enabled": false}'
```

Set to true to re-enable.

---

## 6. Resource Usage Tracking Strategy

Track usage at 3 layers:

- Cost/billing layer: spend by service/resource label
- Platform layer: Cloud Run, Cloud SQL, Redis, GCS utilization
- Application layer: API latency/error/ingestion freshness

## 6.1 Standard Labels (strongly recommended)
Apply labels to all resources:
- `app=newslensai`
- `env=prod` (or `dev`)
- `owner=<team-or-user>`
- `component=backend|frontend|db|cache|storage|scheduler`
- `cost_center=<value>`

Example:
```powershell
gcloud run services update newslensai-backend `
  --region asia-south1 `
  --update-labels app=newslensai,env=prod,component=backend,owner=team-ai
```

---

## 7. Cost Tracking (Billing + BigQuery)

## 7.1 Budget alerts
Create budget (example):

```powershell
gcloud billing budgets create `
  --billing-account=<BILLING_ACCOUNT_ID> `
  --display-name="NewsLensAI Monthly Budget" `
  --budget-amount=25USD `
  --threshold-rule=percent=0.5 `
  --threshold-rule=percent=0.8 `
  --threshold-rule=percent=1.0
```

## 7.2 Billing export to BigQuery
1. In Billing Console, enable detailed cost export.
2. Target dataset: `billing_export`.
3. Use SQL for daily tracking.

### Query: Daily cost by service (last 30 days)
```sql
SELECT
  DATE(usage_start_time) AS usage_date,
  service.description AS service_name,
  SUM(cost) AS cost_usd
FROM `PROJECT_ID.billing_export.gcp_billing_export_v1_*`
WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY usage_date, service_name
ORDER BY usage_date DESC, cost_usd DESC;
```

### Query: Cloud Run cost trend
```sql
SELECT
  DATE(usage_start_time) AS usage_date,
  sku.description AS sku_name,
  SUM(cost) AS cost_usd
FROM `PROJECT_ID.billing_export.gcp_billing_export_v1_*`
WHERE service.description = 'Cloud Run'
  AND DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY usage_date, sku_name
ORDER BY usage_date DESC, cost_usd DESC;
```

---

## 8. Monitoring Dashboards (Cloud Monitoring)

Create one dashboard: `NewsLensAI Ops`.

## 8.1 Cloud Run widgets
- Request count
- Request latency (p50, p95, p99)
- 4xx/5xx error count
- Container instance count
- CPU utilization
- Memory utilization

## 8.2 Cloud SQL widgets
- CPU utilization
- Memory utilization
- Disk utilization
- Connections
- Query latency

## 8.3 Redis widgets
- Memory usage
- Connected clients
- Evictions
- CPU usage

## 8.4 Ingestion freshness widgets
- Custom log-based metric:
  - Last successful ingestion timestamp
  - Ingestion status counts (success/failed/skipped)

---

## 9. Logging and Structured Tracking

## 9.1 Current structured logs in app
The app logs structured objects for API/UI/backend errors and ingestion.

## 9.2 Add log filters

Cloud Run errors:
```text
resource.type="cloud_run_revision"
resource.labels.service_name="newslensai-backend"
severity>=ERROR
```

Scheduler-trigger events:
```text
resource.type="cloud_run_revision"
resource.labels.service_name="newslensai-backend"
jsonPayload.trigger="scheduler"
```

## 9.3 Useful log command
```powershell
gcloud logging read `
  "resource.type=cloud_run_revision AND resource.labels.service_name=newslensai-backend" `
  --project=newslensai `
  --limit=100 `
  --format=json
```

---

## 10. Alerting Policies

Create alerting policies for:

- Cloud Run 5xx error rate > 2% for 5 minutes
- Cloud Run p95 latency > 2s for 10 minutes
- Cloud Run instance saturation (max instances near limit)
- Cloud SQL CPU > 80% for 10 minutes
- Cloud SQL storage > 85%
- Redis memory > 80%
- Ingestion failures >= 3 consecutive runs
- Ingestion freshness stale > 60 minutes
- Budget threshold reached (50%, 80%, 100%)

Notification channels:
- Email
- Slack/Webhook
- PagerDuty (if used)

---

## 11. SLO/SLI Recommendations

## 11.1 Chat API
- Availability SLO: 99.5%
- Latency SLO: p95 < 2.5s
- Error budget tracked monthly

## 11.2 Ingestion
- Freshness SLO: latest ingest < 30 minutes old
- Success SLO: >= 98% successful scheduler runs

---

## 12. Operations Runbooks

## 12.1 Stop outside ingestion immediately
Option A: runtime flag
```powershell
Invoke-RestMethod -Method Put -Uri "https://<CLOUD_RUN_URL>/api/admin/ingest-settings" -ContentType "application/json" -Body '{"external_ingestion_enabled": false}'
```

Option B: pause scheduler
```powershell
.\scripts\setup_scheduler.ps1 -Action pause -ProjectId newslensai -Region asia-south1
```

## 12.2 Resume outside ingestion
Option A:
```powershell
Invoke-RestMethod -Method Put -Uri "https://<CLOUD_RUN_URL>/api/admin/ingest-settings" -ContentType "application/json" -Body '{"external_ingestion_enabled": true}'
```

Option B:
```powershell
.\scripts\setup_scheduler.ps1 -Action resume -ProjectId newslensai -Region asia-south1
```

## 12.3 Force immediate ingestion
```powershell
Invoke-RestMethod -Method Post -Uri "https://<CLOUD_RUN_URL>/api/admin/ingest" -ContentType "application/json" -Body '{"regions":["India","Global"],"topics":["Politics","Business","Technology","Sports","General"],"limit_per_fetch":12}'
```

---

## 13. Security Controls

- Restrict CORS in production to frontend domain only
- Store `SCHEDULER_INGEST_TOKEN` and other secrets in Secret Manager
- Use least-privilege service accounts for Cloud Run and Scheduler
- Disable unauthenticated admin endpoints where possible
- Mask sensitive env values in logs

---

## 14. Capacity and Cost Optimization

- Use Cloud Run min instances = 0 for low traffic
- Set max instances to cap spend
- Use request timeout limits conservatively
- Keep ingestion interval at 15-30 minutes unless high-frequency use case
- Prefer RSS for broad coverage with low API cost
- Use caching to avoid repeated upstream fetches

---

## 15. Known Gaps and Next Improvements

- Ingestion cache is currently in-memory, not persistent across container restarts
- Runtime settings are in-memory and reset on instance restart
- Recommended next step:
  - Persist article cache + settings in Cloud SQL or Redis
  - Add auth on admin APIs
  - Add Monitoring dashboard JSON and Terraform-managed alerts

---

## 16. Quick Daily Ops Checklist

Run once daily:

1. Check scheduler status (`ENABLED/PAUSED`)
2. Check `GET /api/admin/ingest-live-status` freshness
3. Review Cloud Run error logs (last 24h)
4. Review Cloud SQL CPU/storage trend
5. Review daily cost by service from BigQuery export
6. Verify budget threshold notifications

