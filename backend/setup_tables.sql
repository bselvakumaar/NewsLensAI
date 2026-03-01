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
  score FLOAT,
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
