import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config/api';
import '../styles/trading-desk-new.css';
import Chart from 'chart.js/auto';
import { MdOutlineSavings } from "react-icons/md";
import { SiCardmarket } from "react-icons/si";
import { FaSearchDollar, FaHistory } from "react-icons/fa";

export default function TradingDesk({ user, setUser }) {
  const [activeTab, setActiveTab] = useState('depot');
  const [portfolio, setPortfolio] = useState([]);
  const [marketStocks, setMarketStocks] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [transactionHistory, setTransactionHistory] = useState([]);
  const [tradeQuantities, setTradeQuantities] = useState({});
  const [isSearching, setIsSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  const priceChartRef = useRef(null);
  const pieChartRef = useRef(null);
  const priceChartInstance = useRef(null);
  const pieChartInstance = useRef(null);
  const [currentChartTicker, setCurrentChartTicker] = useState('AAPL');

  // Fetch market data on mount
  useEffect(() => {
    loadMarketData();
  }, []);

  // Fetch user portfolio and history when user changes
  useEffect(() => {
    if (user?.id) {
      fetchUserPortfolio();
      
      // Auto-refresh portfolio prices every 30 seconds
      const interval = setInterval(fetchUserPortfolio, 30000);
      return () => clearInterval(interval);
    }
  }, [user?.id]);

  const loadMarketData = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/trade/market`);
      const data = await res.json();
      setMarketStocks(Array.isArray(data) ? data : []);
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch market data:', err);
      setLoading(false);
    }
  };

  const fetchUserPortfolio = async () => {
    try {
      // FIXED: Force user.id to be evaluated explicitly as a String parameter
      const safeUserId = String(user.id);
      
      const [portRes, histRes, pricesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/trade/portfolio/${safeUserId}`),
        fetch(`${API_BASE_URL}/trade/history/${safeUserId}`),
        fetch(`${API_BASE_URL}/trade/portfolio-prices/${safeUserId}`)
      ]);
      const portData = await portRes.json();
      const histData = await histRes.json();
      const pricesData = await pricesRes.json();
      
      setPortfolio(Array.isArray(portData) ? portData : []);
      setTransactionHistory(Array.isArray(histData) ? histData : []);
      
      // Convert portfolio prices to market stock format for live price display
      const portfolioPrices = Array.isArray(pricesData) ? pricesData.map(item => ({
        ticker: item.ticker,
        name: item.ticker,
        price: item.price,
        change: item.change,
        icon: "📈",
        category: "Portfolio"
      })) : [];
      
      setMarketStocks(portfolioPrices);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    }
  };

  const handleSearch = async (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (query.trim().length < 1) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(`${API_BASE_URL}/trade/search?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      setSearchResults(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const executeTrade = async (ticker, action) => {
    const qty = parseFloat(tradeQuantities[ticker]) || 1;
    const endpoint = action === 'BUY' ? 'buy' : 'sell';

    if (qty <= 0) {
      alert('Quantity must be greater than 0');
      return;
    }

    try {
      // FIXED: Treat the User ID strictly as a text String sequence during template building
      const safeUserId = String(user.id);

      const res = await fetch(
        `${API_BASE_URL}/trade/${endpoint}?user_id=${safeUserId}&ticker=${ticker}&quantity=${qty}`,
        { method: 'POST' }
      );

      const data = await res.json();

      if (res.ok) {
        alert(data.message);
        setUser(prev => ({
          ...prev,
          balance: data.new_balance
        }));
        
        // Keep string parsing persistent across session updates
        localStorage.setItem('trader_user', JSON.stringify({ ...user, id: safeUserId, balance: data.new_balance }));
        setTradeQuantities(prev => ({ ...prev, [ticker]: 1 }));
        fetchUserPortfolio();
        loadMarketData();
      } else {
        alert(data.detail || 'Transaction failed');
      }
    } catch (err) {
      alert('Failed to execute trade');
      console.error(err);
    }
  };

  const calculateStockValue = () => {
    return portfolio.reduce((sum, item) => {
      const stockData = marketStocks.find(s => s.ticker === item.ticker);
      const price = stockData ? stockData.price : item.average_buy_price;
      return sum + item.shares_owned * price;
    }, 0);
  };

  const calculateCostBasis = () => {
    return portfolio.reduce((sum, item) => sum + item.shares_owned * item.average_buy_price, 0);
  };

  const stockValue = calculateStockValue();
  const costBasis = calculateCostBasis();
  const totalPortfolio = user?.balance + stockValue;
  const dayPnL = stockValue - costBasis;
  const dayPnLPct = costBasis > 0 ? (dayPnL / costBasis * 100) : 0;

  const renderMarketRows = (stocks) => {
    return stocks.map(stock => {
      const owned = portfolio.find(p => p.ticker === stock.ticker);
      const ownedShares = owned ? owned.shares_owned : 0;
      const isUp = !stock.change.toString().startsWith('-');

      return (
        <div key={stock.ticker} className="td-market-row">
          <div className="td-mrow-left">
            <div className="td-mrow-ticker">{stock.ticker}</div>
            <div className="td-mrow-name">{stock.name}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Category: {stock.icon} {stock.category}
            </div>
          </div>
          <div className="td-mrow-center">
            <div className="td-mrow-price">${Number(stock.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div className={`td-mrow-chg ${isUp ? 'up' : 'dn'}`}>{stock.change}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Owned: {ownedShares}</div>
          </div>
          <div className="td-mrow-right">
            <button className="td-btn-buy" onClick={() => executeTrade(stock.ticker, 'BUY')}>Buy</button>
            <input
              className="td-qty-input"
              type="number"
              min="1"
              value={tradeQuantities[stock.ticker] || 1}
              onChange={(e) => setTradeQuantities(prev => ({ ...prev, [stock.ticker]: e.target.value }))}
            />
            <button className="td-btn-sell" onClick={() => executeTrade(stock.ticker, 'SELL')}>Sell</button>
          </div>
        </div>
      );
    });
  };

  return (
    <div className="td-shell">
      <div className="td-tabs">
        <button
          className={`td-tab ${activeTab === 'depot' ? 'active' : ''}`}
          onClick={() => setActiveTab('depot')}
        >
          <MdOutlineSavings /> My Depot
        </button>
        <button
          className={`td-tab ${activeTab === 'market' ? 'active' : ''}`}
          onClick={() => setActiveTab('market')}
        >
          <SiCardmarket /> Market
        </button>
        <button
          className={`td-tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          <FaSearchDollar /> Search
        </button>
        <button
          className={`td-tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <FaHistory /> History
        </button>
      </div>

      {activeTab === 'depot' && (
        <div>
          <div className="td-stat-row">
            <div className="td-stat-card">
              <div className="td-stat-label">Cash Balance</div>
              <div className="td-stat-val" id="s-cash">
                ${user?.balance?.toLocaleString(undefined, { minimumFractionDigits: 2 }) || '0.00'}
              </div>
              <div className="td-stat-sub">Available to trade</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Stock Value</div>
              <div className="td-stat-val">
                ${stockValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <div className="td-stat-sub">Mark to market</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Total Portfolio</div>
              <div className="td-stat-val">
                ${totalPortfolio.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <div className="td-stat-sub">Net worth</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Day P&L</div>
              <div className={`td-stat-val ${dayPnL >= 0 ? 'green' : 'red'}`}>
                {dayPnL >= 0 ? '+' : ''}${Math.abs(dayPnL).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <div className={`td-stat-sub ${dayPnL >= 0 ? 'up' : 'dn'}`}>
                {dayPnL >= 0 ? '+' : ''}{dayPnLPct.toFixed(2)}%
              </div>
            </div>
          </div>

          <div className="td-section-label">Current Positions</div>
          {portfolio.length === 0 ? (
            <div className="td-empty-state">No open positions. Start trading from the Market tab.</div>
          ) : (
            <div className="td-portfolio-grid">
              {portfolio.map(item => {
                const stockData = marketStocks.find(s => s.ticker === item.ticker);
                const currentPrice = stockData ? stockData.price : item.average_buy_price;
                const mktValue = item.shares_owned * currentPrice;
                const pnl = mktValue - item.shares_owned * item.average_buy_price;
                const pnlPct = (pnl / (item.shares_owned * item.average_buy_price) * 100).toFixed(2);
                const pnlColor = pnl >= 0 ? 'var(--green)' : 'var(--red)';

                return (
                  <div key={item.id} className="td-pos-card">
                    <div className="td-pos-ticker">{item.ticker}</div>
                    <div className="td-pos-name">{stockData?.name || item.ticker}</div>
                    <div className="td-pos-row">
                      <span>Shares</span>
                      <span>{item.shares_owned}</span>
                    </div>
                    <div className="td-pos-row">
                      <span>Avg Cost</span>
                      <span>${item.average_buy_price.toFixed(2)}</span>
                    </div>
                    <div className="td-pos-row">
                      <span>Cur Price</span>
                      <span>${currentPrice.toFixed(2)}</span>
                    </div>
                    <div className="td-pos-row">
                      <span>Mkt Value</span>
                      <span>${mktValue.toFixed(2)}</span>
                    </div>
                    <div className="td-pos-row" style={{ marginTop: '8px', paddingTop: '8px', borderTop: '0.5px solid var(--border)' }}>
                      <span>P&L</span>
                      <span style={{ color: pnlColor, fontWeight: '700' }}>
                        {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)} ({pnlPct}%)
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {activeTab === 'market' && (
        <div>
          <div className="td-section-label">Live Market Prices</div>
          {loading ? (
            <div className="td-loading">Fetching live quotes…</div>
          ) : marketStocks.length === 0 ? (
            <div className="td-empty-state">No market data available</div>
          ) : (
            <div className="td-market-list">
              {renderMarketRows(marketStocks)}
            </div>
          )}
        </div>
      )}

      {activeTab === 'search' && (
        <div>
          <input
            className="td-search-box"
            type="text"
            placeholder="Search by ticker or company name (e.g. AAPL, Tesla)…"
            value={searchQuery}
            onChange={handleSearch}
          />
          {isSearching && <div className="td-loading">Searching live data…</div>}
          {searchResults.length === 0 && searchQuery && !isSearching && (
            <div className="td-empty-state">No results found for "{searchQuery}"</div>
          )}
          {searchResults.length > 0 && (
            <div className="td-market-list">
              {renderMarketRows(searchResults)}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div>
          <div className="td-section-label">Transaction History</div>
          {transactionHistory.length === 0 ? (
            <div className="td-empty-state">No transactions yet. Start trading to build your history.</div>
          ) : (
            <table className="td-hist-table">
              <thead>
                <tr>
                  <th>Date/Time</th>
                  <th>Action</th>
                  <th>Ticker</th>
                  <th>Qty</th>
                  <th>Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {transactionHistory.map((tx, idx) => {
                  const totalValue = (tx.shares * tx.price_per_share).toFixed(2);
                  const timestamp = new Date(tx.timestamp).toLocaleString();

                  return (
                    <tr key={idx}>
                      <td style={{ fontSize: '12px', color: 'var(--text-sec)' }}>{timestamp}</td>
                      <td>
                        <span className={tx.action === 'BUY' ? 'td-badge-buy' : 'td-badge-sell'}>
                          {tx.action}
                        </span>
                      </td>
                      <td style={{ fontWeight: '700' }}>{tx.ticker}</td>
                      <td>{tx.shares}</td>
                      <td>${tx.price_per_share.toFixed(2)}</td>
                      <td style={{ fontWeight: '700' }}>${totalValue}</td>
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