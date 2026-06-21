import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../config/api';
import {
  FaNewspaper,
  FaGlobe,
  FaUniversity,
  FaBullhorn,
  FaFileAlt,
} from 'react-icons/fa';

export default function FinanceMonitor({ user }) {
  const [tab, setTab] = useState('news');
  const [newsCat, setNewsCat] = useState('general');
  const [articles, setArticles] = useState([]);
  const [exchanges, setExchanges] = useState([]);
  const [banks, setBanks] = useState([]);
  const [brief, setBrief] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);

  const newsCategories = [
    { key: 'general', label: 'General' },
    { key: 'markets', label: 'Markets' },
    { key: 'forex', label: 'Forex' },
    { key: 'bonds', label: 'Bonds' },
    { key: 'commodities', label: 'Commodities' },
    { key: 'crypto', label: 'Crypto' },
    { key: 'centralbanks', label: 'Central Banks' },
    { key: 'economic', label: 'Economic' },
    { key: 'ipo', label: 'IPO / M&A' },
    { key: 'derivatives', label: 'Derivatives' },
    { key: 'regulation', label: 'Regulation' },
    { key: 'analysis', label: 'Analysis' },
  ];

  const tabs = [
    { id: 'news', label: 'Market News', icon: FaNewspaper },
    { id: 'exchanges', label: 'Exchanges', icon: FaGlobe },
    { id: 'banks', label: 'Central Banks', icon: FaUniversity },
    { id: 'brief', label: 'Daily Brief', icon: FaFileAlt },
    { id: 'alerts', label: 'Alerts', icon: FaBullhorn },
  ];

  useEffect(() => {
    if (tab === 'news') fetchNews(newsCat);
    if (tab === 'exchanges') fetchExchanges();
    if (tab === 'banks') fetchBanks();
    if (tab === 'brief') fetchBrief();
    if (tab === 'alerts') fetchAlerts();
  }, [tab, newsCat]);

  async function fetchNews(cat) {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/finance/news?category=${cat}&limit=15`);
      const data = await res.json();
      setArticles(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('News fetch failed:', err);
      setArticles([]);
    } finally {
      setLoading(false);
    }
  }

  async function fetchExchanges() {
    if (exchanges.length) return;
    try {
      const res = await fetch(`${API_BASE_URL}/finance/exchanges`);
      const data = await res.json();
      setExchanges(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchBanks() {
    if (banks.length) return;
    try {
      const res = await fetch(`${API_BASE_URL}/finance/central-banks`);
      const data = await res.json();
      setBanks(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchBrief() {
    if (brief) return;
    try {
      const res = await fetch(`${API_BASE_URL}/finance/brief`);
      const data = await res.json();
      setBrief(data);
    } catch (err) {
      console.error(err);
    }
  }

  async function fetchAlerts() {
    try {
      const res = await fetch(`${API_BASE_URL}/finance/alerts?threshold=2.0`);
      const data = await res.json();
      setAlerts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setAlerts([]);
    }
  }

  const formatDate = (value) => {
    if (!value) return '';
    const num = Number(value);
    const d = Number.isNaN(num) ? new Date(value) : new Date(num * 1000);
    try {
      return d.toLocaleString();
    } catch {
      return String(value);
    }
  };

  return (
    <div>
      <div className="td-section-label" style={{ marginTop: 0 }}>
        Finance Monitor
      </div>

      <div className="fm-tabs">
        {tabs.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              className={`fm-tab-btn ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <Icon style={{ fontSize: 14 }} />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === 'news' && (
        <div>
          <div className="news-categories">
            {newsCategories.map((cat) => (
              <button
                key={cat.key}
                className={`news-cat-btn ${newsCat === cat.key ? 'active' : ''}`}
                onClick={() => setNewsCat(cat.key)}
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
                      <span className="news-source">{item.source || item.category}</span>
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
      )}

      {tab === 'exchanges' && (
        <div>
          <div className="exchange-grid">
            {exchanges.map((ex) => (
              <div key={ex['id']} className="exchange-card">
                <div className="exchange-tier">{ex['tier']}</div>
                <div className="exchange-name">
                  {ex['name']}{' '}
                  <span className="exchange-short">{ex['shortName']}</span>
                </div>
                <div className="exchange-meta">
                  {ex['city']}, {ex['country']} · {ex['tradingHours'] || 'N/A'}{' '}
                  {ex['timezone'] ? `(${ex['timezone']})` : ''}
                </div>
                {ex['marketCap'] && (
                  <div className="exchange-cap">Market Cap: ${ex['marketCap']}T</div>
                )}
                <div className="exchange-desc">{ex['description']}</div>
              </div>
            ))}
          </div>
          {exchanges.length === 0 && (
            <div className="td-empty-state">Loading exchange data…</div>
          )}
        </div>
      )}

      {tab === 'banks' && (
        <div>
          <div className="bank-grid">
            {banks.map((b) => (
              <div key={b['id']} className="bank-card">
                <div className="bank-type">{b['type']}</div>
                <div className="bank-name">
                  {b['name']} <span className="bank-short">{b['shortName']}</span>
                </div>
                <div className="bank-meta">
                  {b['city']}, {b['country']}{' '}
                  {b['currency'] ? `· Currency: ${b['currency']}` : ''}
                </div>
                <div className="bank-desc">{b['description']}</div>
              </div>
            ))}
          </div>
          {banks.length === 0 && (
            <div className="td-empty-state">Loading central bank data…</div>
          )}
        </div>
      )}

      {tab === 'brief' && (
        <div>
          {!brief ? (
            <div className="td-loading">Generating daily brief…</div>
          ) : (
            <div className="brief-panel">
              <div className="brief-mood">{brief.mood.toUpperCase()}</div>
              <div className="brief-narrative">{brief.narrative}</div>
              <div className="brief-ts">
                Generated at {new Date(brief.generated_at).toLocaleString()}
              </div>
              <div className="grid-4" style={{ marginTop: 16 }}>
                {brief.watchlist_summary.map((s) => (
                  <div key={s.ticker} className="card">
                    <div className="card-label">{s.ticker}</div>
                    <div className="card-val">${s.price}</div>
                    <div
                      className={`card-change ${s.change_pct >= 0 ? 'up' : 'dn'}`}
                    >
                      {s.change_pct >= 0 ? '+' : ''}
                      {s.change_pct}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'alerts' && (
        <div>
          {alerts.length === 0 ? (
            <div className="td-empty-state">No significant moves detected right now.</div>
          ) : (
            <div className="alert-list">
              {alerts.map((a, i) => (
                <div key={i} className={`alert-item ${a.severity}`}>
                  <div className="alert-ticker">{a.ticker}</div>
                  <div className="alert-message">{a.message}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
