// API Service for NewsLensAI Backend Integration
// This service handles all communication with the FastAPI backend running on Google Cloud Run

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class NewsLensAIAPI {
  // Chat endpoint - sends query and receives RAG-backed response
  static async sendChatMessage(sessionId, query) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': sessionId || 'default',
        },
        body: JSON.stringify({
          session_id: sessionId,
          query: query,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return {
        answer: data.answer || '',
        sources: data.sources || [],
        region: data.region || 'Global',
      };
    } catch (error) {
      console.error('Chat API Error:', error);
      throw error;
    }
  }

  // Fetch latest news with optional filters
  static async getNews(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (filters.region) queryParams.append('region', filters.region);
      if (filters.topic) queryParams.append('topic', filters.topic);
      if (filters.limit) queryParams.append('limit', filters.limit);

      const response = await fetch(
        `${API_BASE_URL}/api/news?${queryParams.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      return data.articles || [];
    } catch (error) {
      console.error('News API Error:', error);
      return [];
    }
  }

  // Get sentiment analysis for specific entity or general trends
  static async getSentiment(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (filters.entity) queryParams.append('entity', filters.entity);
      if (filters.region) queryParams.append('region', filters.region);
      if (filters.days) queryParams.append('days', filters.days);

      const response = await fetch(
        `${API_BASE_URL}/api/sentiment?${queryParams.toString()}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      return data.sentiments || [];
    } catch (error) {
      console.error('Sentiment API Error:', error);
      return [];
    }
  }

  // Create new session
  static async createSession(userId = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      return data.session_id;
    } catch (error) {
      console.error('Session API Error:', error);
      return null;
    }
  }

  // Get admin stats (development only)
  static async getAdminStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/stats`, {
        method: 'GET',
        headers: {
          'X-Admin-Token': process.env.REACT_APP_ADMIN_TOKEN || '',
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Admin Stats Error:', error);
      return null;
    }
  }

  // Health check
  static async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
      });
      return response.ok;
    } catch (error) {
      console.error('Health Check Error:', error);
      return false;
    }
  }
}

export default NewsLensAIAPI;
