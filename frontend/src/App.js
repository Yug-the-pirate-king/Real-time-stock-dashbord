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
  // 1. Initialize user state from localStorage if it exists
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('trader_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  // 2. Automatically skip landing/auth phases if a user is already cached
  const [phase, setPhase] = useState(() => {
    const savedUser = localStorage.getItem('trader_user');
    return savedUser ? 'app' : 'landing';
  });

  const [view, setView] = useState('trading-desk');

  // 3. Helper to handle manual sign-outs cleanly
  const handleLogout = (e) => {
    e.preventDefault();
    localStorage.removeItem('trader_user');
    setUser(null);
    setPhase('landing');
  };

  if (phase === 'landing') return <LandingPage onStart={() => setPhase('auth')} />;
  
  if (phase === 'auth') return (
    <Login 
      onLoginSuccess={u => { 
        // Save to cache on successful sign-in
        localStorage.setItem('trader_user', JSON.stringify(u));
        setUser(u); 
        setPhase('app'); 
      }} 
    />
  );

  const activeLabel = VIEWS.find(v => v.id === view)?.label;

  return (
    <div className="desk-wrapper">

      <aside className="sidebar">
        {/* Changed href from "landingPage" to preventing accidental reloads */}
        <a className="sidebar-logo" href="#" onClick={(e) => e.preventDefault()}>
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
          <button 
            onClick={handleLogout}
            style={{
              background: 'none',
              border: 'none',
              color: '#ff4d4d',
              cursor: 'pointer',
              padding: '0',
              fontSize: '12px',
              marginTop: '5px',
              textAlign: 'left',
              textDecoration: 'underline'
            }}
          >
            Sign Out
          </button>
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
          {/* setUser is safely wired up here now */}
          {view === 'trading-desk' && <TradingDesk user={user} setUser={setUser} />}
          {view === 'news-feed'    && <NewsFeed    user={user} />}
          {view === 'ai-model'     && <AiModel     user={user} />}
        </main>
      </div>

    </div>
  );
}