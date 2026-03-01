# GCP Setup Actions - Clean Reference Guide

## Overview
This document provides a clean, organized log of all Google Cloud Platform (GCP) actions performed for NewsLensAI MVP project, with explanations and learning notes.

---

## 1. AUTHENTICATION & PROJECT SETUP

### 1.1 Initialize GCP Authentication
```bash
gcloud auth application-default login --quiet
```
**What it does**: Sets up Application Default Credentials (ADC) for GCP
- Allows Python/SDK to authenticate with GCP without explicit keys
- Stores credentials locally for local development
- **Learning**: Required before using Cloud SQL Connector in Python scripts

**Output**: Browser opens → User logs in → Credentials saved locally

---

## 2. API ENABLEMENT

### 2.1 Enable 9 Essential APIs
```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  cloudscheduler.googleapis.com \
  storage-api.googleapis.com \
  logging.googleapis.com \
  compute.googleapis.com
```

**What it does**: Activates cloud services for the GCP project

| API | Purpose | Status |
|-----|---------|--------|
| run.googleapis.com | Cloud Run (serverless deployment) | ✓ Enabled |
| sqladmin.googleapis.com | Cloud SQL management | ✓ Enabled |
| redis.googleapis.com | Memorystore Redis | ✓ Enabled |
| aiplatform.googleapis.com | Vertex AI (LLM/embeddings) | ✓ Enabled |
| cloudbuild.googleapis.com | Cloud Build (CI/CD) | ✓ Enabled |
| cloudscheduler.googleapis.com | Cloud Scheduler (cron jobs) | ✓ Enabled |
| storage-api.googleapis.com | Cloud Storage | ✓ Enabled |
| logging.googleapis.com | Cloud Logging | ✓ Enabled |
| compute.googleapis.com | Compute Engine | ✓ Enabled |

**Learning**: 
- Must enable APIs before creating resources that depend on them
- Some APIs have dependencies (e.g., Cloud SQL needs Service Networking)
- Can enable multiple APIs in one command for efficiency

**Duration**: ~30 seconds

### 2.2 Enable Service Networking API (Dependency)
```bash
gcloud services enable servicenetworking.googleapis.com
```

**What it does**: Enables private IP connections for Cloud SQL
- **Why needed**: Cloud SQL requires this for private networking
- **Learning**: Got "Service Networking API not enabled" error initially
- **Solution**: Enable this API before creating Cloud SQL

**Output**: Operation finished successfully

---

## 3. CLOUD SQL (DATABASE)

### 3.1 Create Cloud SQL Instance
```bash
gcloud sql instances create newslensai-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --root-password=NewsLensAI@123456
```

**What it does**: Creates a PostgreSQL 15 database instance in Google Cloud
- `--database-version=POSTGRES_15`: PostgreSQL version 15
- `--tier=db-f1-micro`: Free tier machine (0.6GB RAM, 1 shared vCPU)
- `--region=asia-south1`: India region (for latency optimization)
- `--root-password`: Root user password for postgres account

**Output**:
```
Instance: newslensai-db
Status: RUNNABLE
IP Address: 34.93.239.139
Location: asia-south1-c
```

**Parameters Breakdown**:
| Parameter | Value | Reason |
|-----------|-------|--------|
| Instance Name | newslensai-db | Identifier for the instance |
| Database Version | POSTGRES_15 | Latest stable PostgreSQL |
| Machine Type | db-f1-micro | Free tier eligible |
| Region | asia-south1 | Closest to India market |
| Password | NewsLensAI@123456 | Root access |

**Learning**:
- Free tier includes small database instances
- IP 34.93.239.139 automatically assigned
- Instance takes 5-10 minutes to fully initialize
- Authorization needed later if connecting from outside GCP

**Duration**: 5-10 minutes

**Verify Command**:
```bash
gcloud sql instances describe newslensai-db --format="table(databaseVersion,state,ipAddresses[0].ipAddress)"
```

---

### 3.2 Create Application Database
```bash
gcloud sql databases create newslensai \
  --instance=newslensai-db
```

**What it does**: Creates a new database within the Cloud SQL instance
- Instance: newslensai-db (already created in step 3.1)
- Database name: newslensai (for the application)

**Output**:
```
Database created successfully
instance: newslensai-db
name: newslensai
project: newslensai
```

**Learning**:
- Instance has default 'postgres' database (system)
- This creates application-specific database
- Tables will be created in this database

**Verify Command**:
```bash
gcloud sql databases list --instance=newslensai-db
```

**Output**:
```
NAME          CHARSET  COLLATION
postgres      UTF8     en_US.UTF8
newslensai    UTF8     en_US.UTF8
```

---

## 4. REDIS CACHE

### 4.1 Create Redis Instance
```bash
gcloud redis instances create newslensai-redis \
  --size=1 \
  --region=asia-south1 \
  --tier=basic \
  --redis-version=redis_7_2
```

**What it does**: Creates an in-memory Redis cache for session storage and caching

**Parameters Breakdown**:
| Parameter | Value | Purpose |
|-----------|-------|---------|
| size | 1 | Size tier (maps to capacity) |
| region | asia-south1 | Same region as database |
| tier | basic | Basic tier (free tier eligible) |
| redis-version | redis_7_2 | Redis 7.2 version |

**Output**:
```
Name: newslensai-redis
Status: READY
Host: 10.167.145.131
Port: 6379
Version: REDIS_7_2
Size: 1GB
Tier: BASIC
```

**Learning**:
- Redis version format is specific: `redis_7_2` NOT `7.0`
- Instance takes 5-10 minutes to be READY
- 10.167.145.131 is a private IP (internal GCP network)
- Used for caching chat sessions, frequently accessed articles
- Port 6379 is standard Redis port

**Initial Challenge**: 
- First attempt with `--redis-version=7.0` failed
- Solution: Use enum format `redis_7_2`

**Verify Command**:
```bash
gcloud redis instances list --region=asia-south1
gcloud redis instances describe newslensai-redis --region=asia-south1 --format="table(host,port,displayName)"
```

**Requirements Note**: Must specify `--region` for Redis commands

---

## 5. CLOUD STORAGE

### 5.1 Create Storage Buckets
```bash
gsutil mb -l asia-south1 gs://newslensai-uploads
gsutil mb -l asia-south1 gs://newslensai-archives
```

**What it does**: Creates two Google Cloud Storage buckets for file storage
- `gsutil`: Google Cloud Storage utility
- `mb`: Make Bucket command
- `-l asia-south1`: Location (India region)

**Buckets Created**:

| Bucket | Purpose |
|--------|---------|
| gs://newslensai-uploads | User-uploaded files (images, documents) |
| gs://newslensai-archives | Archive older articles and data |

**Output**:
```
Creating gs://newslensai-uploads/...
Creating gs://newslensai-archives/...
```

**Learning**:
- Bucket names must be globally unique
- Location set to asia-south1 for consistency
- Free tier includes 5GB/month storage

**Verify Command**:
```bash
gsutil ls
```

**Output**:
```
gs://newslensai-archives/
gs://newslensai-uploads/
```

---

## 6. RESOURCE VERIFICATION & INSPECTION

### 6.1 List All Redis Instances
```bash
gcloud redis instances list --region=asia-south1
```

**Output**:
```
INSTANCE_NAME      VERSION    REGION       TIER   SIZE_GB  HOST            PORT  NETWORK  RESERVED_IP        STATUS
newslensai-redis   REDIS_7_2  asia-south1  BASIC  1        10.167.145.131  6379  default  10.167.145.128/29  READY
```

---

### 6.2 List All SQL Instances
```bash
gcloud sql instances list
```

**Output**:
```
NAME            DATABASE_VERSION  LOCATION       TIER         PRIMARY_ADDRESS  STATUS
newslensai-db   POSTGRES_15       asia-south1-c  db-f1-micro  34.93.239.139    RUNNABLE
```

---

### 6.3 Get SQL Instance Details
```bash
gcloud sql instances describe newslensai-db --format="table(databaseVersion,state,ipAddresses[0].ipAddress)"
```

**Output**:
```
DATABASE_VERSION  STATE     IP_ADDRESS
POSTGRES_15       RUNNABLE  34.93.239.139
```

---

## 7. CONNECTION & CREDENTIALS

### Database Connection Info
```
Host: 34.93.239.139
Port: 5432
Database: newslensai
Username: postgres
Password: NewsLensAI@123456
```

### Redis Connection Info
```
Host: 10.167.145.131
Port: 6379
Database: 0 (default)
```

---

## 8. COMMAND SYNTAX PATTERNS

### Pattern 1: Resource Creation (Generic)
```bash
gcloud <service> <resource-type> create <name> --<option>=value
```

**Examples**:
- `gcloud sql instances create newslensai-db ...`
- `gcloud redis instances create newslensai-redis ...`

---

### Pattern 2: Listing Resources
```bash
gcloud <service> <resource-type> list [--region=<region>]
```

**Examples**:
- `gcloud sql instances list` (global)
- `gcloud redis instances list --region=asia-south1` (region-specific)

---

### Pattern 3: Getting Details
```bash
gcloud <service> <resource-type> describe <name> --format="<format>"
```

**Examples**:
- `gcloud sql instances describe newslensai-db --format="table(...)"`
- `gcloud redis instances describe newslensai-redis --region=asia-south1 --format="table(host,port)"`

---

### Pattern 4: Enabling Services
```bash
gcloud services enable <service1.googleapis.com> <service2.googleapis.com> ...
```

---

### Pattern 5: Cloud Storage (gsutil)
```bash
gsutil mb -l <region> gs://<bucket-name>
gsutil ls
```

---

## 9. COMMON ERRORS & SOLUTIONS

### Error 1: Service Networking API Not Enabled
```
ERROR: (gcloud.sql.instances.create) Error while connecting to the Cloud Resource Manager service
```
**Solution**: `gcloud services enable servicenetworking.googleapis.com`

---

### Error 2: Invalid Redis Version Format
```
ERROR: (gcloud.redis.instances.create) Invalid value for '[--redis-version]': '7.0'
```
**Solution**: Use enum format: `--redis-version=redis_7_2` (not `7.0`)

---

### Error 3: Region Required for Redis
```
ERROR: (gcloud.redis.instances.list) Error parsing [region]. The [region] resource is not properly specified
```
**Solution**: Explicitly specify region: `--region=asia-south1`

---

### Error 4: Billing Not Connected
```
ERROR: Billing account not found
```
**Solution**: Enable billing in GCP Console → Set up billing account

---

## 10. OPTIMIZATION & BEST PRACTICES

### Used
✓ **Batch API Enablement**: Enabled 9 APIs in one command
✓ **Region Consistency**: All resources in asia-south1
✓ **Free Tier**: All resources within free tier limits
✓ **Descriptive Names**: Clear naming (newslensai-db, newslensai-redis)
✓ **Security**: Strong password for database
✓ **Verification**: Checked status after each creation

### Recommendations
- Use `--format="table(...)"` for readable output
- Always specify `--region` explicitly
- Enable required APIs before resource creation
- Verify resource status after creation
- Document all credentials securely
- Consider using Infrastructure as Code (Terraform) for production

---

## 11. TIMELINE & EXECUTION

| Step | Command | Duration | Status |
|------|---------|----------|--------|
| 1 | Enable 9 APIs | ~30s | ✓ Success |
| 2 | Enable Service Networking | ~20s | ✓ Success |
| 3 | Create Cloud SQL Instance | ~8min | ✓ Success (IP: 34.93.239.139) |
| 4 | Create Database | ~5s | ✓ Success (newslensai) |
| 5 | Create Redis Instance | ~10min | ✓ Success (Host: 10.167.145.131) |
| 6 | Create Storage Buckets | ~5s | ✓ Success (2 buckets) |

**Total Setup Time**: ~20 minutes (parallelizable to ~10 min)

---

## 12. WHAT YOU LEARNED

### GCP Fundamentals
- ✓ How to enable services via CLI
- ✓ How to create managed databases
- ✓ How to set up caching layers
- ✓ How to use Cloud Storage
- ✓ How to format and query resources
- ✓ Regional resource organization

### CLI Patterns
- ✓ `gcloud` syntax for different services
- ✓ Format strings for output customization
- ✓ Error troubleshooting and solutions
- ✓ Dependency management (Service Networking)

### Best Practices
- ✓ Consistent region selection
- ✓ Free tier optimization
- ✓ Resource naming conventions
- ✓ Verification after creation

---

## 13. QUICK REFERENCE COMMANDS

```bash
# Check all enabled services
gcloud services list --enabled

# Check enabled APIs
gcloud services list --enabled | grep -E "(sql|redis|run|aiplatform)"

# List all Cloud SQL instances
gcloud sql instances list

# List all Redis instances (region required)
gcloud redis instances list --region=asia-south1

# List all storage buckets
gsutil ls

# Get specific resource details
gcloud sql instances describe newslensai-db
gcloud redis instances describe newslensai-redis --region=asia-south1

# Set default project
gcloud config set project newslensai

# View current configuration
gcloud config list
```

---

## 14. ARCHITECTURE DIAGRAM

```
┌─────────────────── GCP PROJECT: newslensai ────────────────────┐
│                                                                  │
│  ┌──────────────────┐  ┌─────────────────┐  ┌─────────────┐   │
│  │   Cloud SQL      │  │  Memorystore    │  │Cloud Storage│   │
│  │  (PostgreSQL 15) │  │    (Redis 7.2)  │  │  (2 buckets)│   │
│  │                  │  │                 │  │             │   │
│  │ Instance:        │  │ Instance:       │  │ Buckets:    │   │
│  │ newslensai-db    │  │ newslensai-redis│  │ -uploads    │   │
│  │                  │  │                 │  │ -archives   │   │
│  │ IP: 34.93.       │  │ IP: 10.167.     │  │             │   │
│  │     239.139      │  │     145.131     │  │             │   │
│  │                  │  │                 │  │             │   │
│  │ Port: 5432       │  │ Port: 6379      │  │ Type: gs:// │   │
│  │                  │  │                 │  │             │   │
│  │ Database:        │  │ Tier: Basic     │  │ Size: 5GB/  │   │
│  │ newslensai       │  │                 │  │ month free  │   │
│  │                  │  │ Size: 1GB       │  │             │   │
│  │ Tier: f1-micro   │  │                 │  │             │   │
│  │ (free)           │  │ (free)          │  │ (free)      │   │
│  └──────────────────┘  └─────────────────┘  └─────────────┘   │
│                                                                  │
│  All services in region: asia-south1                            │
│  All APIs enabled: 9 total                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Summary

You've successfully set up a complete GCP infrastructure with:
- ✓ 9 APIs enabled
- ✓ PostgreSQL database with 4 tables ready
- ✓ Redis caching layer
- ✓ Cloud Storage for files
- ✓ All within free tier limits
- ✓ All automated via gcloud CLI

**Key Learning**: GCP CLI is powerful for Infrastructure as Code. These commands can be scripted, version-controlled, and replicated across environments.

