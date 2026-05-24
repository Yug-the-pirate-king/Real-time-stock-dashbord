import React, { useState, useEffect } from 'react';
import { MdOutlineEnergySavingsLeaf } from "react-icons/md";
import { RiStockFill } from "react-icons/ri";
import { IoSearchCircle } from "react-icons/io5";
import { FaHistory } from "react-icons/fa";
import { MdOutlineSavings } from "react-icons/md";
import '../styles/trading.css'

export default function TradingDesk({ user, setUser }) {
  // Local state just for the trading desk sub-views
  const [deskView, setDeskView] = useState('depot'); // 'depot', 'market', 'search', or 'history'
  const [portfolio, setPortfolio] = useState([]);
  const [tradeQuantities, setTradeQuantities] = useState({});
  const [transactionHistory, setTransactionHistory] = useState([]);

  const [marketStocks, setMarketStocks] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // Fetch market data on component mount
  useEffect(() => {
    fetch("http://127.0.0.1:8000/trade/market")
      .then(res => res.json())
      .then(data => {
        console.log("Market Data:", data);
        
        if (Array.isArray(data)) {
          setMarketStocks(data);
        } else if (data && Array.isArray(data.stocks)) {
          setMarketStocks(data.stocks);
        } else {
          console.error("Expected an array but received:", data);
          setMarketStocks([]);
        }
      })
      .catch(err => {
        console.error("Failed to fetch market data:", err);
        setMarketStocks([]);
      });
  }, []);

  const fetchUserData = async () => {
    if (!user) return;
    try {
      const portRes = await fetch(`http://127.0.0.1:8000/trade/portfolio/${user.id}`);
      const portData = await portRes.json();
      setPortfolio(Array.isArray(portData) ? portData : []);
      
      const histRes = await fetch(`http://127.0.0.1:8000/trade/history/${user.id}`);
      const histData = await histRes.json();
      setTransactionHistory(Array.isArray(histData) ? histData : []);
    } catch (err) {
      console.error("Error fetching user data:", err);
    }
  };

  useEffect(() => {
    fetchUserData();
    // eslint-disable-next-line
  }, [user]);

  const handleSearch = async (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    if (query.trim().length < 1) {
      setSearchResults([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await fetch(`http://127.0.0.1:8000/trade/search?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSearchResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Search failed:", err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

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

      // Update React state + keep localStorage synced
      setUser(prev => {
        const updatedUser = {
          ...prev,
          balance: data.new_balance
        };

        localStorage.setItem(
          'trader_user',
          JSON.stringify(updatedUser)
        );

        return updatedUser;
      });

      fetchUserData();
    } else {
      alert(data.detail || "Transaction rejected.");
    }

  } catch (err) {
    alert("Cannot connect to trading engine backend.");
    console.error(err);
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
      {/* TRADING DESK SUB-NAVIGATION */}
      <div className="desk-tabs">
        <button 
          className={`tab-btn ${deskView === 'depot' ? 'active' : ''}`}
          onClick={() => setDeskView('depot')}
        >
          <MdOutlineEnergySavingsLeaf /> My Depot
        </button>
        <button 
          className={`tab-btn ${deskView === 'market' ? 'active' : ''}`}
          onClick={() => setDeskView('market')}
        >
          <RiStockFill /> Market Explorer
        </button>
        <button 
          className={`tab-btn ${deskView === 'search' ? 'active' : ''}`}
          onClick={() => setDeskView('search')}
        >
          <IoSearchCircle /> Search Stocks
        </button>
        <button 
          className={`tab-btn ${deskView === 'history' ? 'active' : ''}`}
          onClick={() => setDeskView('history')}
        >
          <FaHistory /> Transaction History
        </button>
      </div>

      {/* DEPOT VIEW */}
      {deskView === 'depot' && (
        <div>
          <div className="top-card-grid">
            <div className="stat-card">
              <span style={{fontSize: '2rem'}}><MdOutlineSavings /></span>
              <div>
                <label className="card-label">Cash Account Balance</label>
                <p className="card-val">${user?.balance?.toLocaleString(undefined, {minimumFractionDigits: 2}) || '0.00'}</p>
              </div>
            </div>
            <div className="stat-card">
              <span style={{fontSize: '2rem'}}><RiStockFill /></span>
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

      {/* SEARCH VIEW */}
      {deskView === 'search' && (
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
          <div style={{marginBottom: '20px'}}>
            <input 
              type="text" 
              placeholder="Search stocks by ticker or name (e.g., AAPL, Tesla)..."
              value={searchQuery}
              onChange={handleSearch}
              className="inline-input"
              style={{width: '100%', padding: '12px', fontSize: '16px'}}
            />
            {isSearching && <p style={{color: '#888', marginTop: '8px'}}>🔍 Searching...</p>}
          </div>

          {searchResults.length === 0 && searchQuery && !isSearching && (
            <p style={{color: '#888', fontStyle: 'italic'}}>No stocks found for "{searchQuery}". Try another search.</p>
          )}

          {searchResults.map((stock) => {
            const ownedItem = portfolio.find(p => p.ticker === stock.ticker);
            return (
              <div key={stock.ticker} className="market-row-card">
                <div>
                  <h3 style={{fontFamily: "'DM Serif Display', serif", fontSize: '22px'}}>{stock.name}</h3>
                  <p style={{margin: '4px 0'}}>Ticker: <strong>{stock.ticker}</strong></p>
                  <p style={{margin: '4px 0'}}>Price: <strong>${stock.price}</strong></p>
                  <p style={{fontSize: '14px', color: '#666'}}>Exchange: {stock.exchange} | Type: {stock.type}</p>
                  <p style={{margin: '6px 0', fontSize: '14px'}}>Owning: <strong>{ownedItem ? ownedItem.shares_owned : 0}</strong></p>
                  
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px'}}>
                    <button onClick={() => handleQuickTrade(stock.ticker, 'BUY')} className="action-btn">➕ Buy</button>
                    <input 
                      type="number" 
                      value={tradeQuantities[stock.ticker] || 1} 
                      onChange={(e) => handleQuantityChange(stock.ticker, e.target.value)}
                      className="inline-input" 
                      style={{width: '60px'}}
                    />
                    <button onClick={() => handleQuickTrade(stock.ticker, 'SELL')} className="action-btn">➖ Sell</button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TRANSACTION HISTORY VIEW */}
      {deskView === 'history' && (
        <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
          <h3 style={{fontFamily: "'DM Serif Display', serif"}}>📋 Transaction History</h3>
          
          {transactionHistory.length === 0 ? (
            <p style={{color: '#888', fontStyle: 'italic'}}>No transactions yet. Start trading to build your history!</p>
          ) : (
            <table style={{width: '100%', borderCollapse: 'collapse', backgroundColor: '#f9f9f9', borderRadius: '8px', overflow: 'hidden'}}>
              <thead>
                <tr style={{backgroundColor: '#2c3e50', color: 'white', textAlign: 'left'}}>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Date & Time</th>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Action</th>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Ticker</th>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Shares</th>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Price per Share</th>
                  <th style={{padding: '12px', borderBottom: '2px solid #34495e'}}>Total Value</th>
                </tr>
              </thead>
              <tbody>
                {transactionHistory.map((tx, idx) => {
                  const totalValue = (tx.shares * tx.price_per_share).toFixed(2);
                  const timestamp = new Date(tx.timestamp).toLocaleString();
                  const actionColor = tx.action === 'BUY' ? '#27ae60' : '#e74c3c';
                  
                  return (
                    <tr key={idx} style={{borderBottom: '1px solid #ecf0f1'}}>
                      <td style={{padding: '12px'}}>{timestamp}</td>
                      <td style={{padding: '12px', fontWeight: 'bold', color: actionColor}}>{tx.action}</td>
                      <td style={{padding: '12px', fontWeight: 'bold'}}>{tx.ticker}</td>
                      <td style={{padding: '12px'}}>{tx.shares}</td>
                      <td style={{padding: '12px'}}>${tx.price_per_share.toFixed(2)}</td>
                      <td style={{padding: '12px', fontWeight: 'bold'}}>${totalValue}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}