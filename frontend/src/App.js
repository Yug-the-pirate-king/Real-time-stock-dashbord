import React, { useState } from 'react';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import TradingDesk from './pages/TradingDesk';
import NewsFeed from './pages/NewsFeed';
import AiModel from './pages/Ai_model';
import './styles/global.css';

const VIEWS = [
  { id: 'trading-desk', label: 'Trading Desk' },
  { id: 'news-feed',    label: 'News Feed'    },
  { id: 'ai-model',     label: 'AI Predictions'},
];

export default function App() {
  const [user, setUser]       = useState(null);
  const [phase, setPhase]     = useState('landing');
  const [view, setView]       = useState('trading-desk');

  if (phase === 'landing') return <LandingPage onStart={() => setPhase('auth')} />;
  if (phase === 'auth')    return <Login onLoginSuccess={u => { setUser(u); setPhase('app'); }} />;

  const activeLabel = VIEWS.find(v => v.id === view)?.label;

  return (
    <div className="desk-wrapper">

      <aside className="sidebar">
        <a className="sidebar-logo" href="#">
          <span className="logo-dot" />
          StockPulse
        </a>

        <span className="nav-section-label">Navigation</span>

        {VIEWS.map(v => (
          <button
            key={v.id}
            className={`side-btn${view === v.id ? ' active' : ''}`}
            onClick={() => setView(v.id)}
          >
            {v.label}
          </button>
        ))}

        <div className="sidebar-user">
          <p className="user-label">Logged in as</p>
          <p className="user-name">{user?.username || 'Trader'}</p>
        </div>
      </aside>

      <div className="main-wrap">
        <header className="topbar">
          <span className="topbar-title">{activeLabel}</span>
          <div className="topbar-status">
            <span className="status-dot" />
            <span className="status-text">Markets open</span>
          </div>
        </header>

        <main className="view-content">
          {view === 'trading-desk' && <TradingDesk user={user} />}
          {view === 'news-feed'    && <NewsFeed    user={user} />}
          {view === 'ai-model'     && <AiModel     user={user} />}
        </main>
      </div>

    </div>
  );
}