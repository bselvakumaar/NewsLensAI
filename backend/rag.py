"""
RAG (Retrieval-Augmented Generation) Module
Integrates Vertex AI Embeddings, Cloud SQL pgvector, and Gemini LLM
"""

import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime

import vertexai
from vertexai.language_models import TextEmbeddingModel, TextGenerationModel

logger = logging.getLogger(__name__)

NO_VERIFIED_INFO_MESSAGE = "I don't have verified information on this topic yet."

# Initialize Vertex AI
PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'newslensai-mvp')
REGION = 'asia-south1'

try:
    vertexai.init(project=PROJECT_ID, location=REGION)
    logger.info(f"✓ Vertex AI initialized for project: {PROJECT_ID}")
except Exception as e:
    logger.warning(f"Vertex AI initialization warning: {str(e)}")

# Global model instances
embedding_model = None
gemini_model = None


def get_embedding_model():
    """Get or initialize the Text Embeddings model"""
    global embedding_model
    try:
        if embedding_model is None:
            embedding_model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")
            logger.info("✓ Text Embeddings model loaded")
        return embedding_model
    except Exception as e:
        logger.error(f"Failed to load embedding model: {str(e)}")
        return None


def get_gemini_model():
    """Get or initialize the Gemini model"""
    global gemini_model
    try:
        if gemini_model is None:
            gemini_model = TextGenerationModel.from_pretrained("text-bison@002")
            logger.info("✓ Gemini text generation model loaded")
        return gemini_model
    except Exception as e:
        logger.error(f"Failed to load Gemini model: {str(e)}")
        # Fallback: return a placeholder that will use context-only responses
        logger.warning("Will use context-only responses without LLM generation")
        return None


async def generate_embeddings(text: str) -> Optional[List[float]]:
    """
    Generate embeddings for text using Vertex AI Embeddings API
    
    Args:
        text: Text to embed
        
    Returns:
        List of embedding floats (768 dimensions)
    """
    try:
        model = get_embedding_model()
        if not model:
            logger.warning("Embedding model not available, skipping embeddings")
            return None
        
        embeddings = model.get_embeddings([text])
        if embeddings and len(embeddings) > 0:
            embedding_vector = embeddings[0].values
            logger.info(f"✓ Generated embedding with {len(embedding_vector)} dimensions")
            return embedding_vector
        else:
            logger.warning("Empty embeddings returned")
            return None
            
    except Exception as e:
        logger.error(f"Embeddings generation error: {str(e)}")
        return None


async def similarity_search(
    query: str,
    article_chunks: List[Dict],
    top_k: int = 5
) -> List[Dict]:
    """
    Find most similar article chunks to query using embeddings
    
    This is a mock implementation for MVP.
    In production, use pgvector similarity search in Cloud SQL.
    
    Args:
        query: User query/question
        article_chunks: List of article chunks with text
        top_k: Number of top results to return
        
    Returns:
        Top K similar chunks with metadata
    """
    try:
        if not article_chunks:
            logger.warning("No article chunks available for similarity search")
            return []
        
        # For now, return top articles by relevance of keywords
        # TODO: Implement actual embedding-based similarity search
        words = query.lower().split()
        
        scored_chunks = []
        for chunk in article_chunks:
            text = chunk.get('text', '').lower()
            # Simple word overlap scoring
            score = sum(1 for word in words if word in text)
            if score > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'score': score
                })
        
        # Sort by score and return top K
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        results = [item['chunk'] for item in scored_chunks[:top_k]]
        
        logger.info(f"✓ Found {len(results)} similar articles (top {top_k})")
        return results
        
    except Exception as e:
        logger.error(f"Similarity search error: {str(e)}")
        return []


async def get_rag_response(
    query: str,
    context_articles: List[Dict],
    region: str = "Global"
) -> Dict:
    """
    Generate RAG-augmented response using Vertex AI Gemini
    
    Args:
        query: User query
        context_articles: Retrieved article chunks with citations
        region: Geographic region for context
        
    Returns:
        Dict with answer, sources, and metadata
    """
    try:
        if not context_articles:
            # Mandatory fallback for missing verified context.
            return {
                'summary': NO_VERIFIED_INFO_MESSAGE,
                'answer': NO_VERIFIED_INFO_MESSAGE,
                'sources': [],
                'region': region,
                'confidence': 'Low',
                'last_updated': datetime.utcnow().isoformat()
            }
        
        # Build context from retrieved articles
        context_text = "\n\n".join([
            f"Article: {article.get('title', 'Untitled')}\n"
            f"Source: {article.get('source', 'Unknown')}\n"
            f"Date: {article.get('published_at', 'Unknown')}\n"
            f"Content: {article.get('content', article.get('summary', ''))[:500]}"
            for article in context_articles[:5]  # Limit to top 5
        ])
        
        # Strict instruction to prevent hallucinations beyond retrieved context.
        prompt = f"""System instruction:
You must answer strictly using retrieved news context. If not found, say: I don't have verified information on this topic yet.

You are NewsLensAI, a news intelligence assistant specializing in {region} news.
Use only facts present in the retrieved context below.

--- START CONTEXT ---
{context_text}
--- END CONTEXT ---

User Query: {query}

Response rules:
1) Summarize only what is present in context
2) Do not invent facts
3) If context is insufficient, return exactly: I don't have verified information on this topic yet.
4) Keep response concise and factual

Answer:"""
        
        # Call Gemini LLM
        model = get_gemini_model()
        if not model:
            logger.warning("Gemini model not available, returning context summary")
            fallback_summary = context_articles[0].get('summary') or NO_VERIFIED_INFO_MESSAGE
            return {
                'summary': fallback_summary,
                'answer': fallback_summary,
                'sources': context_articles[:3],
                'region': region,
                'confidence': 'Medium',
                'last_updated': datetime.utcnow().isoformat()
            }
        
        response = model.predict(
            prompt,
            temperature=0.2,
            max_output_tokens=512,
            top_p=0.8,
            top_k=40
        )

        answer = response.text.strip() if response and response.text else NO_VERIFIED_INFO_MESSAGE
        if not answer:
            answer = NO_VERIFIED_INFO_MESSAGE

        confidence = "High" if len(context_articles) >= 3 else "Medium"
        
        logger.info(f"✓ Generated RAG response for query: {query[:50]}...")
        
        return {
            'summary': answer,
            'answer': answer,
            'sources': context_articles[:5],  # Return top sources
            'region': region,
            'confidence': confidence,
            'last_updated': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RAG response generation error: {str(e)}")
        # Fallback response
        if context_articles:
            fallback = context_articles[0]
            fallback_summary = fallback.get('summary', fallback.get('content', '')[:200]) or NO_VERIFIED_INFO_MESSAGE
            return {
                'summary': fallback_summary,
                'answer': fallback_summary,
                'sources': context_articles[:2],
                'region': region,
                'confidence': 'Medium',
                'last_updated': datetime.utcnow().isoformat()
            }
        else:
            return {
                'summary': NO_VERIFIED_INFO_MESSAGE,
                'answer': NO_VERIFIED_INFO_MESSAGE,
                'sources': [],
                'region': region,
                'confidence': 'Low',
                'last_updated': datetime.utcnow().isoformat()
            }


async def rag_pipeline(
    query: str,
    available_articles: List[Dict],
    region: str = "Global"
) -> Dict:
    """
    Complete RAG pipeline:
    1. Search for relevant articles
    2. Extract context from top matches
    3. Generate answer using Gemini with context
    
    Args:
        query: User question
        available_articles: All available articles to search
        region: Geographic region
        
    Returns:
        Complete RAG response with citations
    """
    try:
        logger.info(f"Starting RAG pipeline for query: {query[:50]}...")
        
        # Step 1: Search for similar articles
        if not available_articles:
            logger.warning("No articles available for RAG search")
            return {
                'summary': NO_VERIFIED_INFO_MESSAGE,
                'answer': NO_VERIFIED_INFO_MESSAGE,
                'sources': [],
                'region': region,
                'confidence': 'Low',
                'last_updated': datetime.utcnow().isoformat()
            }
        
        similar_articles = await similarity_search(query, available_articles, top_k=5)
        
        # Step 2: Get RAG response
        rag_response = await get_rag_response(query, similar_articles, region)
        
        return rag_response
        
    except Exception as e:
        logger.error(f"RAG pipeline error: {str(e)}", exc_info=True)
        return {
            'summary': f"Error processing your query. Please try again: {str(e)}",
            'answer': f"Error processing your query. Please try again: {str(e)}",
            'sources': [],
            'region': region,
            'confidence': 'Low',
            'last_updated': datetime.utcnow().isoformat()
        }
