param(
  [ValidateSet("create","pause","resume","delete","run-now")]
  [string]$Action = "create",
  [string]$ProjectId = "newslensai",
  [string]$Region = "asia-south1",
  [string]$ServiceName = "newslensai-backend",
  [string]$JobName = "newslensai-external-ingest",
  [string]$Schedule = "*/30 * * * *",
  [string]$TimeZone = "Asia/Kolkata",
  [string]$SchedulerToken = ""
)

$serviceUrl = (gcloud run services describe $ServiceName --region $Region --project $ProjectId --format "value(status.url)")
if (-not $serviceUrl) {
  throw "Could not resolve Cloud Run URL for service '$ServiceName'."
}

$targetUri = "$serviceUrl/api/admin/ingest/scheduler-trigger"

switch ($Action) {
  "create" {
    if (-not $SchedulerToken) {
      Write-Warning "SchedulerToken is empty. Endpoint auth is optional, but recommended."
    }
    gcloud scheduler jobs create http $JobName `
      --project=$ProjectId `
      --location=$Region `
      --schedule="$Schedule" `
      --time-zone="$TimeZone" `
      --http-method=POST `
      --uri="$targetUri" `
      --headers="Authorization=Bearer $SchedulerToken,Content-Type=application/json" `
      --message-body="{}"
  }
  "pause" {
    gcloud scheduler jobs pause $JobName --project=$ProjectId --location=$Region
  }
  "resume" {
    gcloud scheduler jobs resume $JobName --project=$ProjectId --location=$Region
  }
  "delete" {
    gcloud scheduler jobs delete $JobName --project=$ProjectId --location=$Region --quiet
  }
  "run-now" {
    gcloud scheduler jobs run $JobName --project=$ProjectId --location=$Region
  }
}

Write-Host "Done: $Action on job '$JobName'"
