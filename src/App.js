import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import NewsDisplay from './components/NewsDisplay';
import SentimentDashboard from './components/SentimentDashboard';
import AdminPanel from './components/AdminPanel';
import NewsLensAIAPI from './services/api';
import { sendChatMessage } from './services/chatService';
import GCP_CONFIG from './config/gcp';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [latestNews, setLatestNews] = useState([]);
  const [sentimentData, setSentimentData] = useState([]);
  const [apiStatus, setApiStatus] = useState('checking');
  const [activeTab, setActiveTab] = useState('chat');

  // Initialize session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const newSessionId = await NewsLensAIAPI.createSession();
        if (newSessionId) {
          setSessionId(newSessionId);
          localStorage.setItem('newsLensAI_sessionId', newSessionId);
        } else {
          // Fallback to random session ID for development
          const fallbackId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          setSessionId(fallbackId);
          localStorage.setItem('newsLensAI_sessionId', fallbackId);
        }
      } catch (error) {
        console.error('Session initialization error:', error);
      }
    };

    initializeSession();
  }, []);

  // Check API health on mount
  useEffect(() => {
    const checkAPIHealth = async () => {
      try {
        const isHealthy = await NewsLensAIAPI.healthCheck();
        setApiStatus(isHealthy ? 'connected' : 'disconnected');
      } catch (error) {
        console.error('API health check failed:', error);
        setApiStatus('error');
      }
    };

    checkAPIHealth();
    // Check health every 30 seconds
    const healthInterval = setInterval(checkAPIHealth, 30000);
    return () => clearInterval(healthInterval);
  }, []);

  // Fetch latest news on tab change
  useEffect(() => {
    if (activeTab === 'news') {
      fetchLatestNews();
    }
  }, [activeTab]);

  // Fetch sentiment data on tab change
  useEffect(() => {
    if (activeTab === 'sentiment') {
      fetchSentimentData();
    }
  }, [activeTab]);

  const handleSendMessage = async ({ query, sessionId: sid, topic }) => {
    setIsLoading(true);
    try {
      const response = await sendChatMessage({
        sessionId: sid,
        query,
        topic,
      });
      setIsLoading(false);
      return response;
    } catch (error) {
      setIsLoading(false);
      console.error('[NewsLensAI/UI]', {
        scope: 'send_message',
        code: error.code || 'chat_error',
        message: error.message,
        meta: error.meta || null,
      });
      throw error;
    }
  };

  const fetchLatestNews = async () => {
    setIsLoading(true);
    try {
      const articles = await NewsLensAIAPI.getNews({ limit: 12, region: 'India' });
      setLatestNews(articles);
    } catch (error) {
      console.error('Error fetching news:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSentimentData = async () => {
    setIsLoading(true);
    try {
      const sentiments = await NewsLensAIAPI.getSentiment({
        region: 'India',
        days: 7,
      });
      setSentimentData(sentiments);
    } catch (error) {
      console.error('Error fetching sentiment data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="app-sidebar">
        <div className="sidebar-header">
          <h1>📰 NewsLensAI</h1>
          <p className="version">MVP v1.0</p>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            title="Chat with NewsLensAI"
          >
            💬 Chat
          </button>
          <button
            className={`nav-item ${activeTab === 'news' ? 'active' : ''}`}
            onClick={() => setActiveTab('news')}
            title="Browse latest news"
          >
            📰 News
          </button>
          <button
            className={`nav-item ${activeTab === 'sentiment' ? 'active' : ''}`}
            onClick={() => setActiveTab('sentiment')}
            title="View sentiment analysis (Phase 2)"
            disabled={!GCP_CONFIG.FEATURES.SENTIMENT_ANALYSIS}
          >
            📊 Sentiment
            <span className="badge">Soon</span>
          </button>
          <button
            className={`nav-item ${activeTab === 'admin' ? 'active' : ''}`}
            onClick={() => setActiveTab('admin')}
            title="Admin control panel"
          >
            🔧 Admin
          </button>
        </nav>

        <div className="sidebar-status">
          <div className={`status-indicator ${apiStatus}`}></div>
          <div className="status-text">
            <p className="status-label">API Status</p>
            <p className="status-value">
              {apiStatus === 'connected' && '🟢 Connected'}
              {apiStatus === 'disconnected' && '🟡 Offline'}
              {apiStatus === 'checking' && '⏳ Checking...'}
              {apiStatus === 'error' && '🔴 Error'}
            </p>
          </div>
        </div>

        <div className="sidebar-info">
          <h3>ℹ️ About MVP</h3>
          <ul>
            <li>✅ Conversational AI with RAG</li>
            <li>✅ Citation-backed responses</li>
            <li>✅ Real-time news ingestion</li>
            <li>✅ Multi-turn conversations</li>
            <li>🚀 Sentiment analysis (Phase 2)</li>
            <li>🚀 WhatsApp bot (Phase 3)</li>
          </ul>
        </div>

        <div className="sidebar-gcp">
          <h3>☁️ Google Cloud</h3>
          <p className="config">
            Project: <strong>{GCP_CONFIG.PROJECT_ID}</strong>
            <br />
            Region: <strong>{GCP_CONFIG.REGION}</strong>
            <br />
            Model: <strong>{GCP_CONFIG.VERTEX_AI.MODEL_NAME}</strong>
            <br />
            DB: <strong>pgvector + Cloud SQL</strong>
          </p>
          <button className="docs-btn" onClick={() => alert(require('./config/gcp').GCP_DEPLOYMENT_GUIDE)}>
            📖 Deployment Docs
          </button>
        </div>
      </div>

      <div className="app-main">
        {activeTab === 'chat' && (
          <ChatInterface
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            sessionId={sessionId}
          />
        )}

        {activeTab === 'news' && (
          <div className="content-wrapper">
            <NewsDisplay
              articles={latestNews}
              isLoading={isLoading}
              title="📰 Latest India & Global News"
            />
          </div>
        )}

        {activeTab === 'sentiment' && (
          <div className="content-wrapper">
            <SentimentDashboard data={sentimentData} isLoading={isLoading} />
          </div>
        )}

        {activeTab === 'admin' && (
          <div className="content-wrapper">
            <AdminPanel apiBaseUrl="http://localhost:8000" />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
