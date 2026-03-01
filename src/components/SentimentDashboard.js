import React, { useState, useEffect } from 'react';
import '../styles/SentimentDashboard.css';

const SentimentDashboard = ({ data, isLoading }) => {
  const [selectedEntity, setSelectedEntity] = useState(null);

  const sentimentColor = (score) => {
    if (score > 0.5) return '#4CAF50'; // Positive - Green
    if (score < -0.5) return '#F44336'; // Negative - Red
    return '#FFC107'; // Neutral - Amber
  };

  const sentimentLabel = (score) => {
    if (score > 0.5) return 'Positive 👍';
    if (score < -0.5) return 'Negative 👎';
    return 'Neutral 😐';
  };

  return (
    <div className="sentiment-dashboard">
      <div className="dashboard-header">
        <h2>📊 Sentiment Analytics</h2>
        <p className="disclaimer">Real-time sentiment tracking based on verified news</p>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing sentiment...</p>
        </div>
      ) : data && data.length > 0 ? (
        <div className="sentiment-grid">
          {data.map((item, idx) => (
            <div
              key={idx}
              className={`sentiment-card ${selectedEntity === idx ? 'active' : ''}`}
              onClick={() => setSelectedEntity(selectedEntity === idx ? null : idx)}
            >
              <div className="sentiment-header">
                <h3>{item.entity || 'Unknown Entity'}</h3>
                <span className="sentiment-badge" style={{ backgroundColor: sentimentColor(item.score) }}>
                  {sentimentLabel(item.score)}
                </span>
              </div>

              <div className="sentiment-meter">
                <div className="meter-bar">
                  <div
                    className="meter-fill"
                    style={{
                      width: `${((item.score + 1) / 2) * 100}%`,
                      backgroundColor: sentimentColor(item.score),
                    }}
                  ></div>
                </div>
                <div className="meter-labels">
                  <span>Negative</span>
                  <span className="score-value">{item.score.toFixed(2)}</span>
                  <span>Positive</span>
                </div>
              </div>

              <div className="sentiment-stats">
                <div className="stat">
                  <span className="label">📈 Positive</span>
                  <span className="value">{item.positive_count || 0}</span>
                </div>
                <div className="stat">
                  <span className="label">😐 Neutral</span>
                  <span className="value">{item.neutral_count || 0}</span>
                </div>
                <div className="stat">
                  <span className="label">📉 Negative</span>
                  <span className="value">{item.negative_count || 0}</span>
                </div>
              </div>

              {selectedEntity === idx && item.recent_mentions && (
                <div className="recent-mentions">
                  <p className="mentions-label">💬 Recent Mentions</p>
                  <ul>
                    {item.recent_mentions.slice(0, 3).map((mention, mIdx) => (
                      <li key={mIdx}>{mention}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="sentiment-date">
                <small>📅 Updated: {new Date(item.date).toLocaleDateString()}</small>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>📭 No sentiment data available yet</p>
          <small>Sentiment analysis will appear once news is ingested and analyzed</small>
        </div>
      )}
    </div>
  );
};

export default SentimentDashboard;
