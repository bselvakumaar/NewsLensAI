import { request } from './httpClient';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function logApiError(scope, error, extra = {}) {
  console.error('[NewsLensAI/API]', {
    scope,
    code: error.code || 'unknown_error',
    message: error.message,
    meta: error.meta || null,
    ...extra,
  });
}

class NewsLensAIAPI {
  static async getNews(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (filters.region) queryParams.append('region', filters.region);
      if (filters.topic) queryParams.append('topic', filters.topic);
      if (filters.limit) queryParams.append('limit', filters.limit);

      const data = await request(`/api/news?${queryParams.toString()}`, {
        baseUrl: API_BASE_URL,
      });

      return data.articles || [];
    } catch (error) {
      logApiError('getNews', error, { filters });
      return [];
    }
  }

  static async getSentiment(filters = {}) {
    try {
      const queryParams = new URLSearchParams();
      if (filters.entity) queryParams.append('entity', filters.entity);
      if (filters.region) queryParams.append('region', filters.region);
      if (filters.days) queryParams.append('days', filters.days);

      const data = await request(`/api/sentiment?${queryParams.toString()}`, {
        baseUrl: API_BASE_URL,
      });

      return data.sentiments || [];
    } catch (error) {
      logApiError('getSentiment', error, { filters });
      return [];
    }
  }

  static async createSession(userId = null) {
    try {
      const data = await request('/api/sessions', {
        baseUrl: API_BASE_URL,
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      });
      return data.session_id;
    } catch (error) {
      logApiError('createSession', error, { userId });
      return null;
    }
  }

  static async getAdminStats() {
    try {
      return await request('/api/admin/stats', {
        baseUrl: API_BASE_URL,
        headers: {
          'X-Admin-Token': process.env.REACT_APP_ADMIN_TOKEN || '',
        },
      });
    } catch (error) {
      logApiError('getAdminStats', error);
      return null;
    }
  }

  static async healthCheck() {
    try {
      await request('/health', {
        baseUrl: API_BASE_URL,
      });
      return true;
    } catch (error) {
      logApiError('healthCheck', error);
      return false;
    }
  }
}

export default NewsLensAIAPI;
