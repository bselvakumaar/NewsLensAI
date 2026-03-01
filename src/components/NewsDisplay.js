import React from 'react';
import '../styles/NewsDisplay.css';

const NewsDisplay = ({ articles, isLoading, title }) => {
  const truncateText = (text, length) => {
    return text.length > length ? text.substring(0, length) + '...' : text;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="news-display">
      <div className="news-header">
        <h2>{title || '📰 Latest News'}</h2>
        {isLoading && <span className="loading-badge">Loading...</span>}
      </div>

      {articles && articles.length > 0 ? (
        <div className="articles-grid">
          {articles.map((article, idx) => (
            <div key={idx} className="article-card">
              {(article.image_url || article.image) && (
                <img src={article.image_url || article.image} alt={article.title} className="article-image" />
              )}
              <div className="article-content">
                <div className="article-meta">
                  <span className="article-source">
                    📌 {article.source || 'Unknown Source'}
                  </span>
                  <span className="article-topic">
                    🏷️ {article.topic || 'General'}
                  </span>
                  <span className="article-region">
                    🌍 {article.region || 'Global'}
                  </span>
                </div>
                <h3 className="article-title">{article.title}</h3>
                <p className="article-description">
                  {truncateText(article.description || article.content, 150)}
                </p>
                <div className="article-footer">
                  <span className="article-date">
                    {formatDate(article.published_at || new Date())}
                  </span>
                  {article.url && (
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="article-link"
                    >
                      Read More →
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <p>📭 No articles available yet</p>
          <small>Articles will appear here as they are ingested from news sources</small>
        </div>
      )}
    </div>
  );
};

export default NewsDisplay;
