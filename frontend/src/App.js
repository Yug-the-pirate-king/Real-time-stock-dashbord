import React, { useState } from 'react';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import TradingDesk from './pages/TradingDesk';
import NewsFeed from './pages/NewsFeed';
import Ai_model from './pages/Ai_model';
import './styles/global.css'; 

export default function App() {
  const [user, setUser] = useState(null); 
  const [appPhase, setAppPhase] = useState('landing'); 
  const [currentView, setCurrentView] = useState('trading-desk'); 

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setAppPhase('terminal'); 
  };

  // Switch statement to conditionally render the correct page component
  const renderView = () => {
    switch (currentView) {
      case 'trading-desk':
        return <TradingDesk user={user} />;
      case 'news-feed':
        return <NewsFeed user={user} />;
      case 'ai-model':
        return <Ai_model user={user} />;
      default:
        return <TradingDesk user={user} />;
    }
  };

  // ==========================================
  // PHASE 1: LANDING SCREEN
  // ==========================================
  if (appPhase === 'landing') {
    return <LandingPage onStart={() => setAppPhase('auth')} />;
  }

  // ==========================================
  // PHASE 2: LOGIN/REGISTER WALL
  // ==========================================
  if (appPhase === 'auth' && !user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  // ==========================================
  // PHASE 3: MAIN APPLICATION WITH SIDEBAR
  // ==========================================
  return (
    <div className="desk-wrapper">
      
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <h2 className="sidebar-title">StockPulse</h2>
        
        <button 
          onClick={() => setCurrentView('trading-desk')} 
          className="side-btn" 
          style={{ backgroundColor: currentView === 'trading-desk' ? '#3e3e3e' : 'transparent' }}
        >
          💼 TRADING DESK
        </button>
        
        <button 
          onClick={() => setCurrentView('news-feed')} 
          className="side-btn" 
          style={{ backgroundColor: currentView === 'news-feed' ? '#3e3e3e' : 'transparent' }}
        >
          📰 NEWS FEED
        </button>
        
        <button 
          onClick={() => setCurrentView('ai-model')} 
          className="side-btn" 
          style={{ backgroundColor: currentView === 'ai-model' ? '#3e3e3e' : 'transparent' }}
        >
          🤖 AI PREDICTIONS
        </button>
        
        {/* User Mini Stats (Simplified for the layout shell) */}
        <div className="mini-stats">
          <p>LOGGED IN AS: <br/><strong>{user?.username || 'Trader'}</strong></p>
        </div>
      </aside>

      {/* DYNAMIC CONTENT AREA */}
      <main className="view-content">
        {renderView()}
      </main>
      
    </div>
  );
}