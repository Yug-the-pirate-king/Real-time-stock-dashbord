import React, { useState } from 'react';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import TradingDesk from './pages/TradingDesk';
import NewsFeed from './pages/NewsFeed';
import AiModel from './pages/Ai_model';
import './styles/global.css';
import { GoSidebarExpand, GoSidebarCollapse } from "react-icons/go";
import { AiOutlineStock } from "react-icons/ai";
import { FaBrain } from "react-icons/fa";
import { FaRegNewspaper } from "react-icons/fa";

const VIEWS = [
  { id: 'trading-desk', label: 'Trading Desk', icon: AiOutlineStock },
  { id: 'news-feed',    label: 'News Feed',    icon: FaRegNewspaper },
  { id: 'ai-model',     label: 'AI Signals',   icon: FaBrain },
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

  const activeView = VIEWS.find(v => v.id === view);
  const activeLabel = activeView?.label;

  return (
    <div className={`desk-wrapper ${isCollapsed ? 'sidebar-hidden' : ''}`}>
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="sidebar-global-toggle"
        title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
      >
        {isCollapsed ? <GoSidebarCollapse /> : <GoSidebarExpand />}
      </button>

      <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-content-wrapper">
          <a className="sidebar-logo" href="#" onClick={(e) => e.preventDefault()}>
            <span className="logo-dot" />
            StockPulse
          </a>

          <span className="nav-section-label">Workspace</span>

          {VIEWS.map(v => {
            const Icon = v.icon;
            return (
              <button
                key={v.id}
                className={`side-btn${view === v.id ? ' active' : ''}`}
                onClick={() => setView(v.id)}
              >
                <Icon style={{ fontSize: '17px' }} />
                {v.label}
              </button>
            );
          })}

          <div className="sidebar-user">
            <div className="sidebar-user-top">
              <div className="user-avatar">{user?.username?.charAt(0)?.toUpperCase() || 'T'}</div>
              <div>
                <p className="user-label">Operator</p>
                <p className="user-name">{user?.username || 'Trader'}</p>
              </div>
            </div>
            <button onClick={handleLogout} className="signout-link-btn">
              Disconnect Session
            </button>
          </div>
        </div>
      </aside>

      <div className="main-wrap">
        <header className="topbar">
          <div className="topbar-left">
            <span className="topbar-title" style={{ marginLeft: isCollapsed ? '45px' : '0px' }}>
              {activeLabel}
            </span>
          </div>
          <div className="topbar-right">
            <span className="topbar-live-badge">
              <span className="topbar-live-dot" />
              Live Market
            </span>
            <button className="topbar-refresh-btn" onClick={() => window.location.reload()} title="Refresh">
              ↻
            </button>
            <div className="topbar-balance-pill">
              <span className="topbar-balance-label">Balance</span>
              <span className="topbar-balance-value">
                ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
              </span>
            </div>
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
