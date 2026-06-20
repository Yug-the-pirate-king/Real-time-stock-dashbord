import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/api';

export default function NewsFeed({ user }) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('general');

  const categories = [
    { key: 'general', label: 'General' },
    { key: 'forex', label: 'Forex' },
    { key: 'crypto', label: 'Crypto' },
    { key: 'merger', label: 'M&A' },
  ];

  useEffect(() => {
    let cancelled = false;
    async function fetchNews() {
      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/trade/news?category=${category}`);
        const data = await res.json();
        if (!cancelled) setArticles(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('News fetch failed:', err);
        if (!cancelled) setArticles([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchNews();
    return () => { cancelled = true; };
  }, [category]);

  const formatDate = (unix) => {
    if (!unix) return '';
    const d = new Date(unix * 1000);
    return d.toLocaleString();
  };

  return (
    <div>
      <div className="td-section-label" style={{ marginTop: 0 }}>Market Intelligence</div>

      <div className="news-categories">
        {categories.map(cat => (
          <button
            key={cat.key}
            className={`news-cat-btn ${category === cat.key ? 'active' : ''}`}
            onClick={() => setCategory(cat.key)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="td-loading">Loading headlines…</div>
      ) : articles.length === 0 ? (
        <div className="td-empty-state">No news available right now. Try again shortly.</div>
      ) : (
        <div className="news-grid">
          {articles.map((item, idx) => (
            <a
              key={idx}
              className="news-card-item"
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {item.image && (
                <div className="news-image-wrap">
                  <img src={item.image} alt="" loading="lazy" />
                </div>
              )}
              <div className="news-card-body">
                <div className="news-card-meta">
                  <span className="news-source">{item.source}</span>
                  <span className="news-time">{formatDate(item.datetime)}</span>
                </div>
                <div className="news-headline">{item.headline}</div>
                <p className="news-summary">{item.summary}</p>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
