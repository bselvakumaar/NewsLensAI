const DEFAULT_TIMEOUT_MS = 5000;
const inFlightRequests = new Map();

function toError(code, message, meta = {}) {
  const error = new Error(message);
  error.code = code;
  error.meta = meta;
  return error;
}

async function request(path, options = {}) {
  const {
    baseUrl,
    method = 'GET',
    headers = {},
    body,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    dedupeKey,
  } = options;

  const requestKey = dedupeKey || `${method}:${path}:${body || ''}`;
  if (inFlightRequests.has(requestKey)) {
    return inFlightRequests.get(requestKey);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const fetchPromise = (async () => {
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body,
        signal: controller.signal,
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw toError('api_error', `API Error: ${response.status} ${response.statusText}`, {
          status: response.status,
          payload,
          path,
          method,
        });
      }

      return payload;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw toError('timeout', 'Request timed out after 5 seconds', {
          path,
          method,
          timeoutMs,
        });
      }

      if (error.code) {
        throw error;
      }

      throw toError('network_error', error.message || 'Network request failed', {
        path,
        method,
      });
    } finally {
      clearTimeout(timeoutId);
      inFlightRequests.delete(requestKey);
    }
  })();

  inFlightRequests.set(requestKey, fetchPromise);
  return fetchPromise;
}

export { request, toError };
