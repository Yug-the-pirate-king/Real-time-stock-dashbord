import React, { useState, useEffect } from 'react';
import '../styles/trading.css'

export default function TradingDesk({ user, setUser }) {
  // Local state just for the trading desk sub-views
  const [deskView, setDeskView] = useState('depot'); // 'depot' or 'market'
  const [portfolio, setPortfolio] = useState([]);
  const [tradeQuantities, setTradeQuantities] = useState({});

  // Mock data (will be replaced by Finnhub API later)
  const marketStocks = [
    { name: "Swiss Life AG", ticker: "SLHN", category: "Finance", price: 340.78, change: "-0.34%", icon: "💵" },
    { name: "Spotify", ticker: "SPOT", category: "Technology", price: 117.67, change: "-17.05%", icon: "🚀" },
    { name: "Wind Power AG", ticker: "WIND", category: "Energy", price: 236.14, change: "+1.20%", icon: "⚡" },
    { name: "SolarCity", ticker: "SCTY", category: "Energy", price: 14.60, change: "+0.50%", icon: "☀️" }
  ];

  const fetchUserData = async () => {
    if (!user) return;
    try {
      const portRes = await fetch(`http://127.0.0.1:8000/trade/portfolio/${user.id}`);
      const portData = await portRes.json();
      setPortfolio(Array.isArray(portData) ? portData : []);
    } catch (err) {
      console.error("Error updating assets:", err);
    }
  };

  useEffect(() => {
    fetchUserData();
    // eslint-disable-next-line
  }, [user]);

  const handleQuickTrade = async (ticker, action) => {
    const qty = parseFloat(tradeQuantities[ticker]) || 1;
    const endpoint = action === 'BUY' ? 'buy' : 'sell';
    
    try {
      const response = await fetch(
        `http://127.0.0.1:8000/trade/${endpoint}?user_id=${user.id}&ticker=${ticker}&quantity=${qty}`,
        { method: 'POST' }
      );
      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        // Update user state at the App.js level to reflect the new balance everywhere
        setUser(prev => ({ ...prev, balance: data.new_balance }));
        fetchUserData();
      } else {
        alert(data.detail || "Transaction rejected.");
      }
    } catch (err) {
      alert("Cannot connect to trading engine backend.");
    }
  };

  const handleQuantityChange = (ticker, value) => {
    setTradeQuantities(prev => ({ ...prev, [ticker]: value }));
  };

  const calculateStockBalance = () => {
    return portfolio.reduce((sum, item) => sum + (item.shares_owned * item.average_buy_price), 0);
  };

  return (
    <div>
      <div className="construction-banner">
        <span style={{ marginRight: '10px', fontSize: '1.1rem' }}>⚠️</span> 
        <strong>SYSTEM STATUS: UNDER CONSTRUCTION</strong> — Sandbox broker engine integration is actively running in simulated evaluation mode.
      </div>

      {/* TRADING DESK SUB-NAVIGATION */}
      <div className="desk-tabs">
        <button 
          className={`tab-btn ${deskView === 'depot' ? 'active' : ''}`}
          onClick={() => setDeskView('depot')}
        >
          My Depot
        </button>
        <button 
          className={`tab-btn ${deskView === 'market' ? 'active' : ''}`}
          onClick={() => setDeskView('market')}
        >
          Market Explorer
        </button>
      </div>

      {/* DEPOT VIEW */}
      {deskView === 'depot' && (
        <div>
          <div className="top-card-grid">
            <div className="stat-card">
              <span style={{fontSize: '2rem'}}>🐷</span>
              <div>
                <label className="card-label">Cash Account Balance</label>
                <p className="card-val">${user?.balance?.toLocaleString(undefined, {minimumFractionDigits: 2}) || '0.00'}</p>
              </div>
            </div>
            <div className="stat-card">
              <span style={{fontSize: '2rem'}}>📊</span>
              <div>
                <label className="card-label">Stock Asset Balance</label>
                <p className="card-val">${calculateStockBalance().toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
              </div>
            </div>
          </div>

          <div className="chart-grid">
            <div className="chart-card">
              <h3 style={{fontFamily: "'DM Serif Display', serif"}}>Capital Development</h3>
              <div className="mock-chart-area">
                <div className="mock-bar"></div>
                <p style={{position: 'absolute', bottom: '10px', left: '10px', color: '#888', fontSize: '0.85rem'}}>Real-time capital index tracker active</p>
              </div>
            </div>
            <div className="chart-card">
              <h3 style={{fontFamily: "'DM Serif Display', serif"}}>Share of Stocks</h3>
              <div className="mock-pie-area">
                <div className="circle-pie"></div>
              </div>
            </div>
          </div>

          <h3 style={{marginTop: '30px', marginBottom: '15px', fontFamily: "'DM Serif Display', serif"}}>Current Positions Assets</h3>
          {portfolio.length === 0 ? (
            <p style={{color: '#888', fontStyle: 'italic'}}>Your depot asset positions ledger is currently empty.</p>
          ) : (
            <div className="asset-card-grid">
              {portfolio.map(item => {
                const match = marketStocks.find(s => s.ticker === item.ticker) || { icon: "📈", name: item.ticker };
                return (
                  <div key={item.id} className="asset-mini-card">
                    <div style={{fontSize: '2.5rem'}}>{match.icon}</div>
                    <div style={{flex: 1}}>
                      <h4>{match.name}</h4>
                      <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#444', marginTop: '5px'}}>
                        <span>Price: <strong>${item.average_buy_price.toFixed(2)}</strong></span>
                        <span>Owning: <strong>{item.shares_owned}</strong></span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* MARKET VIEW */}
      {deskView === 'market' && (
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
          {marketStocks.map((stock) => {
            const ownedItem = portfolio.find(p => p.ticker === stock.ticker);
            return (
              <div key={stock.ticker} className="market-row-card">
                <div>
                  <h3 style={{fontFamily: "'DM Serif Display', serif", fontSize: '22px'}}>{stock.name}</h3>
                  <p style={{margin: '4px 0'}}>Price: <strong>${stock.price}</strong></p>
                  <p style={{fontSize: '14px', color: '#666'}}>Category: {stock.icon} {stock.category}</p>
                  <p style={{fontSize: '14px', color: stock.change.startsWith('+') ? 'green' : 'red'}}>Change: {stock.change}</p>
                  <p style={{margin: '6px 0', fontSize: '14px'}}>Owning: <strong>{ownedItem ? ownedItem.shares_owned : 0}</strong></p>
                  
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px'}}>
                    <button onClick={() => handleQuickTrade(stock.ticker, 'BUY')} className="action-btn">➕ Buy</button>
                    <input 
                      type="number" 
                      value={tradeQuantities[stock.ticker] || 1} 
                      onChange={(e) => handleQuantityChange(stock.ticker, e.target.value)}
                      className="inline-input" 
                    />
                    <button onClick={() => handleQuickTrade(stock.ticker, 'SELL')} className="action-btn">➖ Sell</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}