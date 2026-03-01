import React, { useState, useRef, useEffect } from 'react';
import '../styles/ChatInterface.css';

const ChatInterface = ({ onSendMessage, isLoading, sessionId }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      content: 'Welcome to NewsLensAI! 👋 Ask me anything about India & Global news. I\'ll provide verified, citation-backed responses.',
      timestamp: new Date(),
      sources: [],
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: messages.length + 1,
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await onSendMessage(inputValue, sessionId);
      
      const botMessage = {
        id: messages.length + 2,
        type: 'bot',
        content: response.answer || 'Sorry, I could not process your query. Please try again.',
        timestamp: new Date(),
        sources: response.sources || [],
        region: response.region || 'Global',
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: messages.length + 2,
        type: 'bot',
        content: `Error: ${error.message}. Please ensure the backend is running.`,
        timestamp: new Date(),
        sources: [],
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'bot',
        content: 'Chat cleared. Ask me anything about India & Global news!',
        timestamp: new Date(),
        sources: [],
      },
    ]);
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <div className="header-content">
          <h1>📰 NewsLensAI</h1>
          <p className="subtitle">Verified News Intelligence Platform</p>
        </div>
        <button className="clear-btn" onClick={handleClearChat} title="Clear chat history">
          🔄 Clear
        </button>
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message message-${message.type}`}
          >
            <div className="message-avatar">
              {message.type === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
              {message.sources && message.sources.length > 0 && (
                <div className="message-sources">
                  <div className="sources-label">📌 Sources:</div>
                  <ul>
                    {message.sources.map((source, idx) => (
                      <li key={idx}>
                        <strong>{source.title || 'Untitled'}</strong>
                        <br />
                        <small>
                          {source.source} -{' '}
                          {new Date(source.published_at).toLocaleDateString()}
                        </small>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {message.region && message.type === 'bot' && (
                <div className="message-region">
                  🌍 Region: <strong>{message.region}</strong>
                </div>
              )}
              <div className="message-time">
                {message.timestamp.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message message-bot loading">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask about India & Global news... (e.g., 'What's the latest on the budget?')"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isLoading}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={isLoading || !inputValue.trim()}
          title="Send message"
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </form>

      <div className="chat-suggestions">
        <p className="suggestions-label">Try asking:</p>
        <div className="suggestion-pills">
          <button
            className="suggestion-pill"
            onClick={() => setInputValue('What are the latest political developments in India?')}
          >
            📍 Politics
          </button>
          <button
            className="suggestion-pill"
            onClick={() => setInputValue('What economic news is trending today?')}
          >
            💰 Economy
          </button>
          <button
            className="suggestion-pill"
            onClick={() => setInputValue('Latest tech news in India?')}
          >
            💻 Technology
          </button>
          <button
            className="suggestion-pill"
            onClick={() => setInputValue('Any sports news today?')}
          >
            ⚽ Sports
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
