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
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem('trader_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const [phase, setPhase] = useState(() => {
    const savedUser = localStorage.getItem('trader_user');
    return savedUser ? 'app' : 'landing';
  });

  const [view, setView] = useState('trading-desk');
  
  // Track completely open/collapsed state
  const [isCollapsed, setIsCollapsed] = useState(false);

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
        localStorage.setItem('trader_user', JSON.stringify(u));
        setUser(u); 
        setPhase('app'); 
      }} 
    />
  );

  const activeLabel = VIEWS.find(v => v.id === view)?.label;

  return (
    <div className={`desk-wrapper ${isCollapsed ? 'sidebar-hidden' : ''}`}>
      
      {/* Floating Toggle Button: Stays visible at the edge of the viewport when sidebar is gone */}
      <button 
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="sidebar-global-toggle"
        title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
      >
        {isCollapsed ? '➔' : '✕'}
      </button>

      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-content-wrapper">
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
            <button onClick={handleLogout} className="signout-link-btn">
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      <div className="main-wrap">
        <header className="topbar">
          {/* Margin adjusts dynamically to not hide behind the floating button */}
          <span className="topbar-title" style={{ marginLeft: isCollapsed ? '45px' : '0px' }}>
            {activeLabel}
          </span>
          <div className="topbar-status">
            <span className="status-dot" />
            <span className="status-text">Markets open</span>
          </div>
        </header>

        <main className="view-content">
          {view === 'trading-desk' && <TradingDesk user={user} setUser={setUser} />}
          {view === 'news-feed'    && <NewsFeed    user={user} />}
          {view === 'ai-model'     && <AiModel     user={user} />}
        </main>
      </div>

    </div>
  );
}