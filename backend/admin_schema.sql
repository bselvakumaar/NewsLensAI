-- NewsLensAI Admin Schema Extensions
-- Extends setup_tables.sql with admin features

-- News sources management
CREATE TABLE IF NOT EXISTS news_sources (
  id SERIAL PRIMARY KEY,
  source_id VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  source_type VARCHAR(50),  -- rss, newsapi, guardian, manual
  url TEXT NOT NULL,
  region VARCHAR(50),
  topic VARCHAR(100),
  is_active BOOLEAN DEFAULT true,
  article_count INT DEFAULT 0,
  added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_ingested TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingestion jobs tracking  
CREATE TABLE IF NOT EXISTS ingestion_jobs (
  id SERIAL PRIMARY KEY,
  job_id VARCHAR(255) UNIQUE NOT NULL,
  source_id VARCHAR(255) NOT NULL REFERENCES news_sources(source_id) ON DELETE CASCADE,
  status VARCHAR(50),  -- pending, in_progress, completed, failed
  articles_fetched INT DEFAULT 0,
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  error_message TEXT,
  FOREIGN KEY (source_id) REFERENCES news_sources(source_id)
);

-- Ingestion logs (detailed)
CREATE TABLE IF NOT EXISTS ingestion_logs (
  id SERIAL PRIMARY KEY,
  job_id VARCHAR(255) NOT NULL REFERENCES ingestion_jobs(job_id) ON DELETE CASCADE,
  log_message TEXT,
  log_level VARCHAR(20),  -- info, warning, error
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_news_sources_region ON news_sources(region);
CREATE INDEX IF NOT EXISTS idx_news_sources_active ON news_sources(is_active);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_source ON ingestion_jobs(source_id);
