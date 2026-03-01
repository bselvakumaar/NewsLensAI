import React, { useState, useEffect, useCallback, useMemo } from 'react';
import '../styles/AdminPanel.css';

const API_TIMEOUT_MESSAGE = 'Unable to reach admin service. Check if backend is running.';

const INITIAL_SOURCE_FORM = {
  name: '',
  source_type: 'rss',
  url: '',
  region: 'India',
  topic: 'General',
};

const INITIAL_FILTERS = {
  region: 'All',
  topic: 'All',
  status: 'All',
  query: '',
};

const SOURCE_TYPE_OPTIONS = [
  { value: 'rss', label: 'RSS Feed' },
  { value: 'newsapi', label: 'NewsAPI' },
  { value: 'guardian', label: 'Guardian API' },
  { value: 'manual', label: 'Manual Upload' },
];

const REGION_OPTIONS = ['India', 'Global', 'USA', 'UK'];
const TOPIC_OPTIONS = ['General', 'Politics', 'Technology', 'Business', 'Sports', 'Entertainment', 'Health', 'Science'];

const formatDate = (dateValue) => {
  if (!dateValue) return 'Never';
  return new Date(dateValue).toLocaleDateString('en-IN');
};

const formatDateTime = (dateValue) => {
  if (!dateValue) return '-';
  return new Date(dateValue).toLocaleString('en-IN');
};

const AdminPanel = ({ apiBaseUrl = 'http://localhost:8000' }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sources, setSources] = useState([]);
  const [ingestionLogs, setIngestionLogs] = useState([]);
  const [stats, setStats] = useState(null);

  const [sourceForm, setSourceForm] = useState(INITIAL_SOURCE_FORM);
  const [formErrors, setFormErrors] = useState({});
  const [isFormDirty, setIsFormDirty] = useState(false);

  const [filters, setFilters] = useState(INITIAL_FILTERS);

  const [loading, setLoading] = useState({
    dashboard: false,
    sources: false,
    logs: false,
    action: false,
  });

  const [feedback, setFeedback] = useState({ type: '', message: '' });

  const setLoadingState = useCallback((key, value) => {
    setLoading((prev) => ({ ...prev, [key]: value }));
  }, []);

  const clearFeedback = useCallback(() => {
    setFeedback({ type: '', message: '' });
  }, []);

  const fetchJson = useCallback(
    async (path, options) => {
      try {
        const response = await fetch(`${apiBaseUrl}${path}`, options);
        const contentType = response.headers.get('content-type') || '';

        let payload;
        if (contentType.includes('application/json')) {
          payload = await response.json();
        } else {
          const text = await response.text();
          payload = { status: 'error', message: text || 'Unexpected server response' };
        }

        if (!response.ok) {
          const message = payload?.message || payload?.detail || `Request failed with status ${response.status}`;
          throw new Error(message);
        }

        return payload;
      } catch (error) {
        const message = error?.message || API_TIMEOUT_MESSAGE;
        throw new Error(message);
      }
    },
    [apiBaseUrl]
  );

  const loadStats = useCallback(async () => {
    setLoadingState('dashboard', true);
    try {
      const result = await fetchJson('/api/admin/stats');
      setStats(result || {});
    } catch (error) {
      setFeedback({ type: 'error', message: `Stats load failed: ${error.message}` });
    } finally {
      setLoadingState('dashboard', false);
    }
  }, [fetchJson, setLoadingState]);

  const loadSources = useCallback(async () => {
    setLoadingState('sources', true);
    try {
      const result = await fetchJson('/api/admin/sources');
      setSources(Array.isArray(result) ? result : []);
    } catch (error) {
      setFeedback({ type: 'error', message: `Sources load failed: ${error.message}` });
    } finally {
      setLoadingState('sources', false);
    }
  }, [fetchJson, setLoadingState]);

  const loadLogs = useCallback(async () => {
    setLoadingState('logs', true);
    try {
      const result = await fetchJson('/api/admin/ingestion-status');
      setIngestionLogs(Array.isArray(result) ? result : []);
    } catch (error) {
      setFeedback({ type: 'error', message: `Logs load failed: ${error.message}` });
    } finally {
      setLoadingState('logs', false);
    }
  }, [fetchJson, setLoadingState]);

  const loadAll = useCallback(async () => {
    await Promise.all([loadStats(), loadSources(), loadLogs()]);
  }, [loadStats, loadSources, loadLogs]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (activeTab === 'dashboard') {
        loadStats();
        return;
      }

      if (activeTab === 'logs') {
        loadLogs();
      }
    }, 20000);

    return () => clearInterval(intervalId);
  }, [activeTab, loadStats, loadLogs]);

  const validateSourceForm = useCallback(() => {
    const errors = {};

    if (!sourceForm.name.trim()) {
      errors.name = 'Source name is required';
    }

    if (!sourceForm.url.trim()) {
      errors.url = 'Source URL is required';
    }

    try {
      // Validate URL format to prevent backend rejections for malformed input.
      // eslint-disable-next-line no-new
      new URL(sourceForm.url);
    } catch {
      errors.url = 'Enter a valid URL (example: https://example.com/feed.xml)';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  }, [sourceForm]);

  const onFormChange = useCallback((field, value) => {
    setSourceForm((prev) => ({ ...prev, [field]: value }));
    setIsFormDirty(true);

    if (formErrors[field]) {
      setFormErrors((prev) => ({ ...prev, [field]: '' }));
    }

    if (feedback.type === 'error') {
      clearFeedback();
    }
  }, [formErrors, feedback.type, clearFeedback]);

  const handleAddSource = useCallback(
    async (event) => {
      event.preventDefault();
      clearFeedback();

      if (!validateSourceForm()) {
        return;
      }

      setLoadingState('action', true);

      try {
        const payload = {
          ...sourceForm,
          name: sourceForm.name.trim(),
          url: sourceForm.url.trim(),
        };

        const result = await fetchJson('/api/admin/sources', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (result.status !== 'success' || !result.source) {
          throw new Error(result.message || 'Unable to add source');
        }

        setSources((prev) => [result.source, ...prev]);
        setSourceForm(INITIAL_SOURCE_FORM);
        setFormErrors({});
        setIsFormDirty(false);
        setFeedback({ type: 'success', message: `Source "${result.source.name}" added successfully.` });

        loadStats();
      } catch (error) {
        setFeedback({ type: 'error', message: `Add source failed: ${error.message}` });
      } finally {
        setLoadingState('action', false);
      }
    },
    [clearFeedback, fetchJson, loadStats, setLoadingState, sourceForm, validateSourceForm]
  );

  const handleDeleteSource = useCallback(
    async (sourceId, sourceName) => {
      if (!window.confirm(`Delete source "${sourceName}"? This cannot be undone.`)) {
        return;
      }

      clearFeedback();
      setLoadingState('action', true);

      try {
        const result = await fetchJson(`/api/admin/sources/${sourceId}`, {
          method: 'DELETE',
        });

        if (result.status !== 'success') {
          throw new Error(result.message || 'Delete failed');
        }

        setSources((prev) => prev.filter((source) => source.source_id !== sourceId));
        setFeedback({ type: 'success', message: `Source "${sourceName}" deleted.` });

        loadStats();
      } catch (error) {
        setFeedback({ type: 'error', message: `Delete failed: ${error.message}` });
      } finally {
        setLoadingState('action', false);
      }
    },
    [clearFeedback, fetchJson, loadStats, setLoadingState]
  );

  const handleToggleActive = useCallback(
    async (source) => {
      clearFeedback();
      setLoadingState('action', true);

      try {
        const result = await fetchJson(`/api/admin/sources/${source.source_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ is_active: !source.is_active }),
        });

        if (result.status !== 'success' || !result.source) {
          throw new Error(result.message || 'Status update failed');
        }

        setSources((prev) => prev.map((item) => (item.source_id === source.source_id ? result.source : item)));
      } catch (error) {
        setFeedback({ type: 'error', message: `Status update failed: ${error.message}` });
      } finally {
        setLoadingState('action', false);
      }
    },
    [clearFeedback, fetchJson, setLoadingState]
  );

  const handleStartIngestion = useCallback(
    async (sourceId = null) => {
      clearFeedback();
      setLoadingState('action', true);

      try {
        const result = await fetchJson('/api/admin/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source_id: sourceId }),
        });

        if (result.status !== 'success') {
          throw new Error(result.message || 'Ingestion failed to start');
        }

        setFeedback({
          type: 'success',
          message: sourceId ? 'Ingestion started for selected source.' : 'Ingestion started for all active sources.',
        });

        await Promise.all([loadStats(), loadLogs(), loadSources()]);
      } catch (error) {
        setFeedback({ type: 'error', message: `Ingestion request failed: ${error.message}` });
      } finally {
        setLoadingState('action', false);
      }
    },
    [clearFeedback, fetchJson, loadLogs, loadSources, loadStats, setLoadingState]
  );

  const filteredSources = useMemo(() => {
    const query = filters.query.trim().toLowerCase();

    return sources.filter((source) => {
      const regionMatch = filters.region === 'All' || source.region === filters.region;
      const topicMatch = filters.topic === 'All' || source.topic === filters.topic;
      const statusMatch =
        filters.status === 'All' ||
        (filters.status === 'Active' && source.is_active) ||
        (filters.status === 'Inactive' && !source.is_active);

      const queryMatch =
        !query ||
        source.name?.toLowerCase().includes(query) ||
        source.url?.toLowerCase().includes(query) ||
        source.source_type?.toLowerCase().includes(query);

      return regionMatch && topicMatch && statusMatch && queryMatch;
    });
  }, [filters, sources]);

  const derivedStats = useMemo(() => {
    const totalSources = stats?.total_sources ?? sources.length;
    const activeSources = stats?.active_sources ?? sources.filter((source) => source.is_active).length;
    const totalArticles = stats?.total_articles ?? sources.reduce((sum, source) => sum + (source.article_count || 0), 0);

    return {
      totalSources,
      activeSources,
      inactiveSources: Math.max(totalSources - activeSources, 0),
      totalArticles,
      successfulJobs: stats?.successful_jobs ?? 0,
      failedJobs: stats?.failed_jobs ?? 0,
      lastIngestion: stats?.last_ingestion,
    };
  }, [sources, stats]);

  const tabCounts = useMemo(() => {
    const pendingOrRunning = ingestionLogs.filter((log) => ['pending', 'in_progress'].includes(log.status)).length;

    return {
      sources: sources.length,
      logs: ingestionLogs.length,
      pendingOrRunning,
    };
  }, [ingestionLogs, sources.length]);

  return (
    <div className="admin-panel">
      <div className="admin-shell">
        <header className="admin-header">
          <div>
            <h1>Admin Control Panel</h1>
            <p className="subtitle">Manage news resources, ingestion operations, and platform health.</p>
          </div>

          <div className="admin-header-actions">
            <button
              className="btn btn-secondary"
              onClick={loadAll}
              disabled={loading.dashboard || loading.sources || loading.logs || loading.action}
            >
              Refresh Data
            </button>
            <button
              className="btn btn-primary"
              onClick={() => handleStartIngestion()}
              disabled={loading.action}
            >
              Ingest All Sources
            </button>
          </div>
        </header>

        <nav className="admin-tabs" aria-label="Admin sections">
          <button
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            type="button"
          >
            Dashboard
          </button>
          <button
            className={`tab-btn ${activeTab === 'sources' ? 'active' : ''}`}
            onClick={() => setActiveTab('sources')}
            type="button"
          >
            Sources
            <span className="tab-count">{tabCounts.sources}</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
            type="button"
          >
            Logs
            <span className="tab-count">{tabCounts.logs}</span>
          </button>
          {tabCounts.pendingOrRunning > 0 && (
            <span className="tab-indicator">{tabCounts.pendingOrRunning} running</span>
          )}
        </nav>

        {feedback.message && (
          <div className={`admin-feedback ${feedback.type}`} role="status" aria-live="polite">
            {feedback.message}
          </div>
        )}

        <main className="admin-content">
          {activeTab === 'dashboard' && (
            <section className="admin-section">
              <div className="section-header">
                <h2>Dashboard</h2>
                {loading.dashboard && <span className="inline-loading">Updating metrics...</span>}
              </div>

              <div className="stats-grid">
                <article className="stat-card">
                  <p className="stat-label">Total Sources</p>
                  <p className="stat-value">{derivedStats.totalSources}</p>
                </article>
                <article className="stat-card">
                  <p className="stat-label">Active Sources</p>
                  <p className="stat-value">{derivedStats.activeSources}</p>
                </article>
                <article className="stat-card">
                  <p className="stat-label">Inactive Sources</p>
                  <p className="stat-value">{derivedStats.inactiveSources}</p>
                </article>
                <article className="stat-card">
                  <p className="stat-label">Total Articles</p>
                  <p className="stat-value">{derivedStats.totalArticles}</p>
                </article>
                <article className="stat-card">
                  <p className="stat-label">Successful Ingestions</p>
                  <p className="stat-value">{derivedStats.successfulJobs}</p>
                </article>
                <article className="stat-card">
                  <p className="stat-label">Failed Ingestions</p>
                  <p className="stat-value">{derivedStats.failedJobs}</p>
                </article>
              </div>

              <div className="admin-callout">
                <p><strong>Last ingestion:</strong> {formatDateTime(derivedStats.lastIngestion)}</p>
                <p>Dashboard and logs auto-refresh every 20 seconds. Sources are refreshed manually to avoid form interruptions.</p>
              </div>
            </section>
          )}

          {activeTab === 'sources' && (
            <section className="admin-section">
              <div className="section-header sources-header">
                <div>
                  <h2>News Sources</h2>
                  <p className="section-subtitle">Stable form workflow with search and filters for large source catalogs.</p>
                </div>
                <button className="btn btn-secondary" type="button" onClick={loadSources} disabled={loading.sources || loading.action}>
                  Refresh Sources
                </button>
              </div>

              <div className="sources-layout">
                <aside className="source-form-card">
                  <h3>Add New Source</h3>
                  <p className="section-subtitle">Create a source resource without leaving the panel.</p>

                  <form className="source-form" onSubmit={handleAddSource}>
                    <div className="form-group">
                      <label htmlFor="source-name">Source Name</label>
                      <input
                        id="source-name"
                        type="text"
                        placeholder="e.g., Reuters World"
                        value={sourceForm.name}
                        onChange={(event) => onFormChange('name', event.target.value)}
                        required
                        aria-invalid={Boolean(formErrors.name)}
                      />
                      {formErrors.name && <p className="input-error">{formErrors.name}</p>}
                    </div>

                    <div className="form-group">
                      <label htmlFor="source-url">URL / Feed Link</label>
                      <input
                        id="source-url"
                        type="url"
                        placeholder="https://example.com/feed.xml"
                        value={sourceForm.url}
                        onChange={(event) => onFormChange('url', event.target.value)}
                        required
                        aria-invalid={Boolean(formErrors.url)}
                      />
                      {formErrors.url && <p className="input-error">{formErrors.url}</p>}
                    </div>

                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="source-type">Type</label>
                        <select
                          id="source-type"
                          value={sourceForm.source_type}
                          onChange={(event) => onFormChange('source_type', event.target.value)}
                        >
                          {SOURCE_TYPE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="source-region">Region</label>
                        <select
                          id="source-region"
                          value={sourceForm.region}
                          onChange={(event) => onFormChange('region', event.target.value)}
                        >
                          {REGION_OPTIONS.map((region) => (
                            <option key={region} value={region}>
                              {region}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="form-group">
                      <label htmlFor="source-topic">Topic</label>
                      <select
                        id="source-topic"
                        value={sourceForm.topic}
                        onChange={(event) => onFormChange('topic', event.target.value)}
                      >
                        {TOPIC_OPTIONS.map((topic) => (
                          <option key={topic} value={topic}>
                            {topic}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="form-actions">
                      <button type="submit" className="btn btn-primary" disabled={loading.action}>
                        Add Source
                      </button>
                      <button
                        type="button"
                        className="btn btn-ghost"
                        disabled={!isFormDirty || loading.action}
                        onClick={() => {
                          setSourceForm(INITIAL_SOURCE_FORM);
                          setFormErrors({});
                          setIsFormDirty(false);
                          clearFeedback();
                        }}
                      >
                        Reset
                      </button>
                    </div>
                  </form>
                </aside>

                <div className="sources-table-card">
                  <div className="filter-bar">
                    <input
                      type="search"
                      placeholder="Search by name, url, or type"
                      value={filters.query}
                      onChange={(event) => setFilters((prev) => ({ ...prev, query: event.target.value }))}
                    />

                    <select
                      value={filters.region}
                      onChange={(event) => setFilters((prev) => ({ ...prev, region: event.target.value }))}
                    >
                      <option value="All">All Regions</option>
                      {REGION_OPTIONS.map((region) => (
                        <option key={region} value={region}>
                          {region}
                        </option>
                      ))}
                    </select>

                    <select
                      value={filters.topic}
                      onChange={(event) => setFilters((prev) => ({ ...prev, topic: event.target.value }))}
                    >
                      <option value="All">All Topics</option>
                      {TOPIC_OPTIONS.map((topic) => (
                        <option key={topic} value={topic}>
                          {topic}
                        </option>
                      ))}
                    </select>

                    <select
                      value={filters.status}
                      onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
                    >
                      <option value="All">All Status</option>
                      <option value="Active">Active</option>
                      <option value="Inactive">Inactive</option>
                    </select>
                  </div>

                  {loading.sources ? (
                    <p className="empty-state">Loading sources...</p>
                  ) : (
                    <div className="table-wrap">
                      <table className="sources-table">
                        <thead>
                          <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Region</th>
                            <th>Topic</th>
                            <th>Status</th>
                            <th>Articles</th>
                            <th>Last Ingested</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredSources.length === 0 && (
                            <tr>
                              <td colSpan="8" className="empty-table-cell">
                                No sources found for the current filter.
                              </td>
                            </tr>
                          )}

                          {filteredSources.map((source) => (
                            <tr key={source.source_id}>
                              <td>
                                <p className="source-name">{source.name}</p>
                                <p className="source-url">{source.url}</p>
                              </td>
                              <td>
                                <span className="badge">{source.source_type}</span>
                              </td>
                              <td>{source.region || '-'}</td>
                              <td>{source.topic || '-'}</td>
                              <td>
                                <button
                                  type="button"
                                  className={`status-btn ${source.is_active ? 'active' : 'inactive'}`}
                                  onClick={() => handleToggleActive(source)}
                                  disabled={loading.action}
                                >
                                  {source.is_active ? 'Active' : 'Inactive'}
                                </button>
                              </td>
                              <td>{source.article_count || 0}</td>
                              <td>{formatDate(source.last_ingested)}</td>
                              <td>
                                <div className="row-actions">
                                  <button
                                    type="button"
                                    className="btn btn-small btn-secondary"
                                    onClick={() => handleStartIngestion(source.source_id)}
                                    disabled={loading.action}
                                  >
                                    Ingest
                                  </button>
                                  <button
                                    type="button"
                                    className="btn btn-small btn-danger"
                                    onClick={() => handleDeleteSource(source.source_id, source.name)}
                                    disabled={loading.action}
                                  >
                                    Delete
                                  </button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {activeTab === 'logs' && (
            <section className="admin-section">
              <div className="section-header">
                <h2>Ingestion Logs</h2>
                {loading.logs && <span className="inline-loading">Refreshing logs...</span>}
              </div>

              <div className="logs-container">
                {ingestionLogs.length === 0 ? (
                  <p className="empty-state">No ingestion jobs available.</p>
                ) : (
                  ingestionLogs.map((log) => (
                    <article key={log.job_id} className={`log-item log-${log.status}`}>
                      <div className="log-header">
                        <span className={`status-badge ${log.status}`}>{String(log.status || 'unknown').toUpperCase()}</span>
                        <span className="log-time">Started: {formatDateTime(log.started_at)}</span>
                      </div>

                      <div className="log-details">
                        <p><strong>Job ID:</strong> {log.job_id}</p>
                        <p><strong>Source:</strong> {log.source_id}</p>
                        <p><strong>Articles fetched:</strong> {log.articles_fetched || 0}</p>
                        <p><strong>Completed:</strong> {formatDateTime(log.completed_at)}</p>

                        {Array.isArray(log.errors) && log.errors.length > 0 && (
                          <div className="errors">
                            <strong>Errors</strong>
                            {log.errors.map((errorText, index) => (
                              <p key={`${log.job_id}-err-${index}`}>{errorText}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    </article>
                  ))
                )}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminPanel;
