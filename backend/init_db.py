#!/usr/bin/env python3
"""
Script to initialize NewsLensAI database tables
Uses Cloud SQL Python Connector for secure connection
"""
from google.cloud.sql.connector import Connector

# Database connection parameters
db_config = {
    'project_id': 'newslensai',
    'region': 'asia-south1',
    'instance': 'newslensai-db',
    'db_user': 'postgres',
    'db_password': 'NewsLensAI@123456',
    'db_name': 'newslensai'
}

# SQL commands to create tables
sql_commands = """
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
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
CREATE TABLE IF NOT EXISTS article_chunks (
  id SERIAL PRIMARY KEY,
  article_id INT REFERENCES articles(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  embedding_vector vector(768),
  chunk_index INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sentiment scores
CREATE TABLE IF NOT EXISTS sentiment_scores (
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
CREATE TABLE IF NOT EXISTS sessions (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255) UNIQUE NOT NULL,
  user_id VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region);
CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_chunks_article ON article_chunks(article_id);
CREATE INDEX IF NOT EXISTS idx_chunks_vector ON article_chunks USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists=100);
CREATE INDEX IF NOT EXISTS idx_sentiment_entity ON sentiment_scores(entity);
CREATE INDEX IF NOT EXISTS idx_sentiment_date ON sentiment_scores(date);
CREATE INDEX IF NOT EXISTS idx_sessions_id ON sessions(session_id);
"""

def init_db():
    """Initialize database tables using Cloud SQL Connector"""
    try:
        # Initialize Connector
        print("Initializing Cloud SQL Connector...")
        connector = Connector()
        
        # Create connection
        print("Connecting to Cloud SQL database...")
        connection = connector.connect(
            instance_connection_string=f"{db_config['project_id']}:{db_config['region']}:{db_config['instance']}",
            driver="psycopg2",
            user=db_config['db_user'],
            password=db_config['db_password'],
            db=db_config['db_name']
        )
        
        cursor = connection.cursor()
        
        # Split commands and execute them one by one
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for i, command in enumerate(commands, 1):
            print(f"Executing command {i}/{len(commands)}...")
            cursor.execute(command)
            connection.commit()
        
        cursor.close()
        connection.close()
        connector.close()
        
        print("\n✅ Database initialization completed successfully!")
        print("\nCreated:")
        print("  - Extension: pgvector")
        print("  - Tables: articles, article_chunks, sentiment_scores, sessions")
        print("  - Indexes: 9 indexes for performance")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_db()

