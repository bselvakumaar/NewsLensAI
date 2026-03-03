import React, { useEffect, useMemo, useRef, useState } from 'react';
import useDebouncedValue from '../hooks/useDebouncedValue';
import { FALLBACK_SCOPE_MESSAGE, getGuardrailError } from '../utils/guardrails';
import '../styles/ChatInterface.css';

const TOPICS = ['All', 'Politics', 'Finance', 'World', 'Tech', 'Sports'];
const TRENDING_TODAY = [
  'What are the top India political headlines today?',
  'How did global markets close today?',
  'What is the latest in India tech and AI news?',
  'What are the biggest world news developments right now?',
  'Give me today\'s key sports headlines.',
];

const INITIAL_BOT_MESSAGE = {
  id: 'welcome',
  type: 'bot',
  summary: 'Welcome to NewsLensAI. Ask about India and global news, and I will answer using verified context.',
  region: 'India',
  confidence: 'High',
  sources: [],
  lastUpdated: new Date().toISOString(),
  timestamp: new Date().toISOString(),
  status: 'ok',
};

function nextId(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

const ChatInterface = ({ onSendMessage, isLoading, sessionId }) => {
  const [messages, setMessages] = useState([INITIAL_BOT_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [activeTopic, setActiveTopic] = useState('All');
  const [lastRequest, setLastRequest] = useState(null);
  const messagesEndRef = useRef(null);
  const debouncedInput = useDebouncedValue(inputValue, 250);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const liveGuardrailError = useMemo(
    () => getGuardrailError(debouncedInput, activeTopic),
    [debouncedInput, activeTopic]
  );

  const upsertBotMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const applyFeedback = (messageId, feedback) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, feedback } : msg))
    );
  };

  const sendQuery = async (query, topic) => {
    const normalizedQuery = query.trim();
    const guardrailError = getGuardrailError(normalizedQuery, topic);

    if (guardrailError) {
      upsertBotMessage({
        id: nextId('guardrail'),
        type: 'bot',
        summary: guardrailError,
        region: 'India | Global',
        confidence: 'Low',
        sources: [],
        lastUpdated: new Date().toISOString(),
        timestamp: new Date().toISOString(),
        status: 'ok',
      });
      return;
    }

    setLastRequest({ query: normalizedQuery, topic });

    const userMessage = {
      id: nextId('user'),
      type: 'user',
      content: normalizedQuery,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await onSendMessage({
        query: normalizedQuery,
        sessionId,
        topic,
      });

      upsertBotMessage({
        id: nextId('bot'),
        type: 'bot',
        summary: response.summary,
        region: response.region || 'Global',
        confidence: response.confidence || 'Low',
        sources: response.sources || [],
        lastUpdated: response.last_updated || new Date().toISOString(),
        timestamp: new Date().toISOString(),
        status: 'ok',
      });
    } catch (error) {
      console.error('[NewsLensAI/UI]', {
        scope: 'chat_send',
        code: error.code || 'chat_error',
        message: error.message,
        meta: error.meta || null,
        query: normalizedQuery,
        topic,
      });

      upsertBotMessage({
        id: nextId('error'),
        type: 'bot',
        summary: 'We could not fetch a verified response right now.',
        region: 'India | Global',
        confidence: 'Low',
        sources: [],
        lastUpdated: new Date().toISOString(),
        timestamp: new Date().toISOString(),
        status: 'error',
        canRetry: true,
      });
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (isLoading) return;
    await sendQuery(inputValue, activeTopic);
  };

  const handleRetry = async () => {
    if (!lastRequest || isLoading) return;
    await sendQuery(lastRequest.query, lastRequest.topic);
  };

  const handleClearChat = () => {
    setMessages([
      {
        ...INITIAL_BOT_MESSAGE,
        id: nextId('welcome'),
        summary: 'Chat cleared. Ask about India and global news.',
      },
    ]);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-content">
          <h1>NewsLensAI</h1>
          <p className="subtitle">Verified India and Global News Assistant</p>
        </div>
        <button className="clear-btn" onClick={handleClearChat} title="Clear chat history">
          Clear
        </button>
      </div>

      <div className="topic-filter-row">
        {TOPICS.map((topic) => (
          <button
            key={topic}
            type="button"
            className={`topic-btn ${activeTopic === topic ? 'active' : ''}`}
            onClick={() => setActiveTopic(topic)}
            disabled={isLoading}
          >
            {topic}
          </button>
        ))}
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <div key={message.id} className={`message message-${message.type}`}>
            <div className="message-avatar">{message.type === 'user' ? 'You' : 'AI'}</div>
            <div className="message-content">
              {message.type === 'user' && <div className="message-text">{message.content}</div>}

              {message.type === 'bot' && (
                <>
                  <div className="response-header">
                    <span className="response-region">Region: {message.region}</span>
                    <span className="response-confidence">Confidence: {message.confidence}</span>
                    <span className="response-updated">
                      Last Updated: {new Date(message.lastUpdated).toLocaleString()}
                    </span>
                  </div>

                  <div className="message-text">{message.summary || FALLBACK_SCOPE_MESSAGE}</div>

                  <div className="message-sources">
                    <div className="sources-label">Source List</div>
                    {message.sources && message.sources.length > 0 ? (
                      <ul>
                        {message.sources.map((source, idx) => (
                          <li key={`${message.id}_source_${idx}`}>
                            <a href={source.url || '#'} target="_blank" rel="noreferrer">
                              {source.title || 'Untitled Source'}
                            </a>
                            <small>
                              {source.published_at
                                ? new Date(source.published_at).toLocaleString()
                                : 'Unknown publish time'}
                            </small>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="sources-empty">No linked source available for this response.</p>
                    )}
                  </div>

                  <div className="feedback-row">
                    <button
                      type="button"
                      className={`feedback-btn ${message.feedback === 'up' ? 'selected' : ''}`}
                      onClick={() => applyFeedback(message.id, 'up')}
                    >
                      Thumb Up
                    </button>
                    <button
                      type="button"
                      className={`feedback-btn ${message.feedback === 'down' ? 'selected' : ''}`}
                      onClick={() => applyFeedback(message.id, 'down')}
                    >
                      Thumb Down
                    </button>
                    {message.status === 'error' && message.canRetry && (
                      <button type="button" className="retry-btn" onClick={handleRetry}>
                        Retry
                      </button>
                    )}
                  </div>
                </>
              )}

              <div className="message-time">
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message message-bot loading">
            <div className="message-avatar">AI</div>
            <div className="message-content">
              <div className="loading-wrapper">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span className="loading-label">Generating verified response...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask about India and global news..."
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          disabled={isLoading}
        />
        <button type="submit" className="send-btn" disabled={isLoading || !inputValue.trim()}>
          Send
        </button>
      </form>

      <div className="chat-suggestions">
        <p className="suggestions-label">Trending Today</p>
        <div className="suggestion-pills">
          {TRENDING_TODAY.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="suggestion-pill"
              onClick={() => setInputValue(prompt)}
              disabled={isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
        {inputValue.trim().length > 0 && liveGuardrailError && (
          <p className="guardrail-hint" role="alert">
            {liveGuardrailError}
          </p>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
