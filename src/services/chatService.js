import { request } from './httpClient';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TOPIC_TO_BACKEND = {
  All: null,
  Politics: 'Politics',
  Finance: 'Business',
  World: null,
  Tech: 'Technology',
  Sports: 'Sports',
};

const QUERY_TOPIC_HINTS = {
  Technology: ['tech', 'technology', 'ai', 'artificial', 'software', 'startup', 'semiconductor'],
  Business: ['finance', 'business', 'market', 'economy', 'stock', 'stocks', 'trade', 'rupee'],
  Politics: ['politics', 'political', 'election', 'policy', 'government', 'parliament', 'budget'],
  Sports: ['sport', 'sports', 'cricket', 'football', 'ipl', 'match', 'olympic'],
};

function inferTopicFromQuery(query = '') {
  const tokens = (query.toLowerCase().match(/[a-z0-9]+/g) || []);
  if (!tokens.length) return null;

  let winner = null;
  let bestScore = 0;

  Object.entries(QUERY_TOPIC_HINTS).forEach(([topic, hints]) => {
    const score = tokens.reduce((acc, token) => (hints.includes(token) ? acc + 1 : acc), 0);
    if (score > bestScore) {
      bestScore = score;
      winner = topic;
    }
  });

  return bestScore > 0 ? winner : null;
}

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
  const selectedTopic = TOPIC_TO_BACKEND[topic];
  const inferredTopic = inferTopicFromQuery(query);
  const mappedTopic = inferredTopic || selectedTopic || null;
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
    timeoutMs: 20000,
    dedupeKey: `chat:${sessionId}:${query.trim().toLowerCase()}:${mappedTopic || 'all'}`,
  });

  return normalizeChatPayload(payload);
}

export { sendChatMessage, normalizeChatPayload };
