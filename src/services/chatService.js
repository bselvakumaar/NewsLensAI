import { request } from './httpClient';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TOPIC_TO_BACKEND = {
  Politics: 'Politics',
  Finance: 'Business',
  World: 'General',
  Tech: 'Technology',
  Sports: 'Sports',
};

function normalizeConfidence(scoreOrLabel) {
  if (typeof scoreOrLabel === 'string') {
    const normalized = scoreOrLabel.trim().toLowerCase();
    if (normalized === 'high' || normalized === 'medium' || normalized === 'low') {
      return normalized.charAt(0).toUpperCase() + normalized.slice(1);
    }
  }

  const numeric = Number(scoreOrLabel);
  if (!Number.isNaN(numeric)) {
    if (numeric >= 0.75) return 'High';
    if (numeric >= 0.45) return 'Medium';
  }

  return 'Low';
}

function normalizeChatPayload(payload = {}) {
  return {
    summary: payload.summary || payload.answer || 'I do not have a verified update yet.',
    region: payload.region || 'Global',
    sources: Array.isArray(payload.sources) ? payload.sources : [],
    confidence: normalizeConfidence(payload.confidence),
    last_updated: payload.last_updated || new Date().toISOString(),
  };
}

async function sendChatMessage({ sessionId, query, topic }) {
  const mappedTopic = TOPIC_TO_BACKEND[topic] || null;
  const body = JSON.stringify({
    session_id: sessionId,
    query,
    topic: mappedTopic,
  });

  const payload = await request('/api/chat', {
    baseUrl: API_BASE_URL,
    method: 'POST',
    headers: {
      'X-Session-ID': sessionId || 'default',
    },
    body,
    dedupeKey: `chat:${sessionId}:${query.trim().toLowerCase()}:${mappedTopic || 'all'}`,
  });

  return normalizeChatPayload(payload);
}

export { sendChatMessage, normalizeChatPayload };
