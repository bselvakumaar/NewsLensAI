const NEWS_KEYWORDS = [
  'news',
  'india',
  'global',
  'politics',
  'policy',
  'election',
  'finance',
  'economy',
  'market',
  'stocks',
  'world',
  'war',
  'diplomacy',
  'tech',
  'technology',
  'ai',
  'sports',
  'cricket',
  'football',
  'headline',
  'today',
  'update',
  'government',
  'budget',
  'inflation',
];

const FALLBACK_SCOPE_MESSAGE = 'NewsLensAI focuses only on India & Global News.';

function isEmptyQuery(query) {
  return !query || !query.trim();
}

function isOutOfScopeQuery(query) {
  if (isEmptyQuery(query)) {
    return false;
  }

  const normalized = query.toLowerCase();
  return !NEWS_KEYWORDS.some((keyword) => normalized.includes(keyword));
}

function getGuardrailError(query) {
  if (isEmptyQuery(query)) {
    return 'Please enter a news-related question before sending.';
  }

  if (isOutOfScopeQuery(query)) {
    return FALLBACK_SCOPE_MESSAGE;
  }

  return null;
}

export { FALLBACK_SCOPE_MESSAGE, getGuardrailError, isOutOfScopeQuery, isEmptyQuery };
