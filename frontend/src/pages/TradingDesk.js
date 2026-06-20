import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config/api';
import '../styles/trading-desk-new.css';
import Chart from 'chart.js/auto';

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
  const [toasts, setToasts] = useState([]);
  const [receipt, setReceipt] = useState(null);

  const [detailTicker, setDetailTicker] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailMetrics, setDetailMetrics] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailPeriod, setDetailPeriod] = useState('1mo');

  const chartCanvasRef = useRef(null);
  const chartInstanceRef = useRef(null);
  const searchTimeout = useRef(null);
  const receiptTimer = useRef(null);

  useEffect(() => {
    if (user?.id) {
      fetchUserData();
      const interval = setInterval(fetchUserData, 30000);
      return () => clearInterval(interval);
    }
  }, [user?.id]);

  useEffect(() => {
    if (!detailData || !chartCanvasRef.current) return;
    if (chartInstanceRef.current) chartInstanceRef.current.destroy();
    const ctx = chartCanvasRef.current.getContext('2d');
    const prices = detailData.prices_usd || detailData.prices_native || [];
    const labels = detailData.dates || prices.map((_, i) => i);

    chartInstanceRef.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: `${detailData.ticker} Price`,
          data: prices,
          borderColor: (ctx) => {
            const v = ctx.p0?.parsed?.y ?? 0;
            const vNext = ctx.p1?.parsed?.y ?? 0;
            return vNext >= v ? '#2d6b45' : '#C0392B';
          },
          backgroundColor: 'rgba(45,107,69,0.06)',
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: '#2d6b45',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          fill: true,
          segment: {
            borderColor: ctx => ctx.p0.parsed.y <= ctx.p1.parsed.y ? '#2d6b45' : '#C0392B'
          },
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(14,14,14,0.92)',
            titleFont: { family: "'Syne', sans-serif", size: 13 },
            bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
            padding: 10,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              title: (items) => {
                const lbl = items[0]?.label;
                const d = new Date(lbl);
                if (isNaN(d)) return lbl;
                return d.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
              },
              label: (ctx) => {
                return ` Price: $${Number(ctx.raw).toFixed(2)}`;
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: { display: false },
            ticks: {
              maxTicksLimit: 6,
              font: { size: 10, family: "'JetBrains Mono', monospace" },
              color: 'var(--text-muted)',
              maxRotation: 0,
              autoSkip: true,
            }
          },
          y: {
            display: true,
            grid: { color: '#f0f0eb' },
            ticks: {
              font: { size: 10, family: "'JetBrains Mono', monospace" },
              color: 'var(--text-muted)',
              callback: (val) => '$' + Number(val).toFixed(0),
            }
          }
        }
      }
    });
  }, [detailData]);

  const addToast = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  };

  const showReceipt = (data, action) => {
    if (receiptTimer.current) clearTimeout(receiptTimer.current);
    setReceipt({ ...data, action });
    receiptTimer.current = setTimeout(() => setReceipt(null), 8000);
  };

  const fetchUserData = async () => {
    try {
      const safeUserId = String(user.id);
      const [portRes, histRes, pricesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/trade/portfolio/${safeUserId}`),
        fetch(`${API_BASE_URL}/trade/history/${safeUserId}`),
        fetch(`${API_BASE_URL}/trade/portfolio-prices/${safeUserId}`),
      ]);
      let portData = await portRes.json();
      const histData = await histRes.json();
      const pricesData = await pricesRes.json();

      if (Array.isArray(portData) && Array.isArray(pricesData)) {
        portData = portData.map(item => {
          const live = pricesData.find(p => p.ticker === item.ticker);
          return live
            ? { ...item, current_price: live.price, change: live.change, flag: live.flag, country: live.country, currency: live.currency || item.currency, exchange: live.exchange || item.exchange }
            : item;
        });
      }
      setPortfolio(Array.isArray(portData) ? portData : []);
      setTransactionHistory(Array.isArray(histData) ? histData : []);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    }
  };

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    setSearchResults([]);

    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (query.trim().length < 1) {
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    searchTimeout.current = setTimeout(async () => {
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
    }, 350);
  };

  const executeTrade = async (ticker, action) => {
    const qty = parseFloat(tradeQuantities[ticker]) || 1;
    const endpoint = action === 'BUY' ? 'buy' : 'sell';

    if (qty <= 0 || isNaN(qty)) {
      addToast('Quantity must be greater than 0', 'error');
      return;
    }

    try {
      const safeUserId = String(user.id);
      const res = await fetch(
        `${API_BASE_URL}/trade/${endpoint}?user_id=${safeUserId}&ticker=${encodeURIComponent(ticker)}&quantity=${qty}`,
        { method: 'POST' }
      );
      const data = await res.json();

      if (res.ok) {
        addToast(data.message, 'success');
        setUser(prev => ({ ...prev, balance: data.new_balance }));
        localStorage.setItem('trader_user', JSON.stringify({ ...user, id: safeUserId, balance: data.new_balance }));
        setTradeQuantities(prev => ({ ...prev, [ticker]: 1 }));
        showReceipt(data, action);
        fetchUserData();
        if (detailTicker === ticker) {
          loadDetail(ticker, detailPeriod);
        }
      } else {
        addToast(data.detail || 'Transaction failed', 'error');
      }
    } catch (err) {
      addToast('Failed to execute trade', 'error');
      console.error(err);
    }
  };

  const loadDetail = async (ticker, period = '1mo') => {
    setDetailTicker(ticker);
    setDetailLoading(true);
    try {
      const [priceRes, histRes, metricsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/trade/price/${encodeURIComponent(ticker)}`),
        fetch(`${API_BASE_URL}/trade/history-data/${encodeURIComponent(ticker)}?period=${period}`),
        fetch(`${API_BASE_URL}/trade/metrics/${encodeURIComponent(ticker)}`),
      ]);
      const priceData = await priceRes.json();
      const histData = await histRes.json();
      const metricsData = await metricsRes.json();
      setDetailData({ ...histData, currentPrice: priceData.price_usd, name: priceData.name });
      setDetailMetrics(metricsData);
    } catch (err) {
      console.error('Detail fetch failed:', err);
      setDetailData(null);
      setDetailMetrics(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const calculateStockValue = () => {
    return portfolio.reduce((sum, item) => {
      const price = item.current_price ?? item.average_buy_price;
      return sum + item.shares_owned * price;
    }, 0);
  };

  const calculateCostBasis = () => {
    return portfolio.reduce((sum, item) => sum + (item.total_cost_basis_usd || item.shares_owned * item.average_buy_price), 0);
  };

  const stockValue = calculateStockValue();
  const costBasis = calculateCostBasis();
  const totalPortfolio = (user?.balance || 0) + stockValue;
  const dayPnL = stockValue - costBasis;
  const dayPnLPct = costBasis > 0 ? (dayPnL / costBasis * 100) : 0;

  const renderMetric = (label, value) => (
    <div className="td-metric-cell" key={label}>
      <div className="td-metric-label">{label}</div>
      <div className="td-metric-value">{value ?? '—'}</div>
    </div>
  );

  const renderMarketRows = (stocks) => {
    return stocks.map(stock => {
      const owned = portfolio.find(p => p.ticker === stock.ticker);
      const ownedShares = owned ? owned.shares_owned : 0;
      const chgStr = String(stock.change || '0.00%');
      const isUp = !chgStr.startsWith('-');

      return (
        <div key={stock.ticker} className="td-market-row">
          <div className="td-mrow-left" onClick={() => loadDetail(stock.ticker)} style={{ cursor: 'pointer' }}>
            <div className="td-mrow-ticker">{stock.ticker}</div>
            <div className="td-mrow-name">{stock.name}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              {stock.flag} {stock.country} · {stock.currency} · {stock.exchange} · {stock.icon} {stock.category}
            </div>
          </div>
          <div className="td-mrow-center">
            <div className="td-mrow-price">${Number(stock.price).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
            <div className={`td-mrow-chg ${isUp ? 'up' : 'dn'}`}>{stock.change}</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Owned: {ownedShares}</div>
          </div>
          <div className="td-mrow-right" onClick={e => e.stopPropagation()}>
            <button className="td-btn-buy" onClick={() => executeTrade(stock.ticker, 'BUY')}>Buy</button>
            <input
              className="td-qty-input"
              type="number"
              min="1"
              step="1"
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
      {/* Toasts */}
      <div className="td-toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`td-toast td-toast-${t.type}`}>{t.message}</div>
        ))}
      </div>

      {/* Receipt Banner */}
      {receipt && (
        <div className="td-receipt-banner">
          <div className="td-receipt-header">
            <span className="td-receipt-badge">{receipt.action}</span>
            <span className="td-receipt-title">{receipt.message}</span>
            <button className="td-receipt-close" onClick={() => setReceipt(null)}>✕</button>
          </div>
          <div className="td-receipt-grid">
            <div className="td-receipt-cell"><span>Ticker</span><strong>{receipt.ticker}</strong></div>
            <div className="td-receipt-cell"><span>Exchange</span><strong>{receipt.exchange}</strong></div>
            <div className="td-receipt-cell"><span>Currency</span><strong>{receipt.currency}</strong></div>
            <div className="td-receipt-cell"><span>Shares</span><strong>{receipt.shares}</strong></div>
            <div className="td-receipt-cell"><span>Price (Native)</span><strong>{receipt.price_native?.toFixed(2)} {receipt.currency}</strong></div>
            <div className="td-receipt-cell"><span>Price (USD)</span><strong>${receipt.price_usd?.toFixed(2)}</strong></div>
            <div className="td-receipt-cell"><span>Rate Used</span><strong>{receipt.rate_used?.toFixed(4) ?? '-'}</strong></div>
            <div className="td-receipt-cell"><span>New Balance</span><strong>${receipt.new_balance?.toFixed(2)}</strong></div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailTicker && (
        <div className="td-modal-overlay" onClick={() => setDetailTicker(null)}>
          <div className="td-modal" onClick={e => e.stopPropagation()}>
            <div className="td-modal-header">
              <div>
                <div className="td-modal-ticker">{detailTicker}</div>
                <div className="td-modal-name">{detailData?.name}</div>
              </div>
              <button className="td-modal-close" onClick={() => setDetailTicker(null)}>✕</button>
            </div>
            {detailLoading ? (
              <div className="td-loading">Loading chart & metrics…</div>
            ) : detailData ? (
              <>
                <div className="td-modal-meta">
                  <span className="td-badge-currency">{detailData.flag} {detailData.country}</span>
                  <span className="td-badge-currency">{detailData.currency}</span>
                  <span className="td-badge-currency">{detailData.exchange || 'Unknown'}</span>
                  <span className="td-badge-currency">Current: ${detailData.currentPrice?.toFixed(2)}</span>
                </div>

                {/* Metrics Grid */}
                {detailMetrics && (
                  <div className="td-metrics-grid">
                    {renderMetric('Market Cap', detailMetrics.market_cap)}
                    {renderMetric('P/E (TTM)', detailMetrics.pe_trailing)}
                    {renderMetric('P/E (Fwd)', detailMetrics.pe_forward)}
                    {renderMetric('EPS', detailMetrics.eps)}
                    {renderMetric('Div Yield', detailMetrics.dividend_yield ? `${detailMetrics.dividend_yield}%` : null)}
                    {renderMetric('Volume', detailMetrics.volume)}
                    {renderMetric('Avg Vol', detailMetrics.avg_volume)}
                    {renderMetric('Day High', detailMetrics.day_high)}
                    {renderMetric('Day Low', detailMetrics.day_low)}
                    {renderMetric('52W High', detailMetrics.fifty_two_week_high)}
                    {renderMetric('52W Low', detailMetrics.fifty_two_week_low)}
                    {renderMetric('Beta', detailMetrics.beta)}
                    {renderMetric('Sector', detailMetrics.sector)}
                    {renderMetric('Industry', detailMetrics.industry)}
                  </div>
                )}

                {/* Period Selector */}
                <div className="td-chart-controls" style={{ marginTop: '16px' }}>
                  {['1mo','3mo','6mo','1y'].map(p => (
                    <button
                      key={p}
                      className={`td-period-btn ${detailPeriod === p ? 'active' : ''}`}
                      onClick={() => { setDetailPeriod(p); loadDetail(detailTicker, p); }}
                    >
                      {p === '1mo' ? '1M' : p === '3mo' ? '3M' : p === '6mo' ? '6M' : '1Y'}
                    </button>
                  ))}
                </div>

                <div className="td-chart-wrap" style={{ height: '240px', marginTop: '8px' }}>
                  <canvas ref={chartCanvasRef} />
                </div>

                <div className="td-modal-actions">
                  <button className="td-btn-buy" onClick={() => { executeTrade(detailTicker, 'BUY'); }}>Buy</button>
                  <button className="td-btn-sell" onClick={() => { executeTrade(detailTicker, 'SELL'); }}>Sell</button>
                </div>
              </>
            ) : (
              <div className="td-empty-state">No data available</div>
            )}
          </div>
        </div>
      )}

      <div className="td-tabs">
        <button className={`td-tab ${activeTab === 'depot' ? 'active' : ''}`} onClick={() => setActiveTab('depot')}>My Depot</button>
        <button className={`td-tab ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>Search</button>
        <button className={`td-tab ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>History</button>
      </div>

      {activeTab === 'depot' && (
        <div>
          <div className="td-stat-row">
            <div className="td-stat-card">
              <div className="td-stat-label">Cash Balance</div>
              <div className="td-stat-val" id="s-cash">${(user?.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
              <div className="td-stat-sub">Available to trade</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Stock Value</div>
              <div className="td-stat-val">${stockValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
              <div className="td-stat-sub">Mark to market</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Total Portfolio</div>
              <div className="td-stat-val">${totalPortfolio.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
              <div className="td-stat-sub">Net worth</div>
            </div>
            <div className="td-stat-card">
              <div className="td-stat-label">Unrealized P&L</div>
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
            <div className="td-empty-state">No open positions. Start trading from the Search tab.</div>
          ) : (
            <div className="td-portfolio-grid">
              {portfolio.map(item => {
                const currentPrice = item.current_price ?? item.average_buy_price;
                const mktValue = item.shares_owned * currentPrice;
                const cb = item.total_cost_basis_usd || (item.shares_owned * item.average_buy_price);
                const pnl = mktValue - cb;
                const pnlPct = cb > 0 ? (pnl / cb * 100).toFixed(2) : '0.00';
                const pnlColor = pnl >= 0 ? 'var(--green)' : 'var(--red)';

                return (
                  <div
                    key={item.id}
                    className="td-pos-card"
                    onClick={() => loadDetail(item.ticker)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="td-pos-ticker">{item.ticker}</div>
                    <div className="td-pos-name">
                      {item.flag || '🌍'} {item.country || 'US'} · {item.currency || 'USD'} · {item.exchange || 'Unknown'}
                    </div>
                    <div className="td-pos-row"><span>Shares</span><span>{item.shares_owned}</span></div>
                    <div className="td-pos-row"><span>Avg Cost (USD)</span><span>${item.average_buy_price?.toFixed(2)}</span></div>
                    {item.original_avg_buy_price ? (
                      <div className="td-pos-row"><span>Avg Cost ({item.currency})</span><span>{item.original_avg_buy_price?.toFixed(2)}</span></div>
                    ) : null}
                    <div className="td-pos-row"><span>Cur Price</span><span>${currentPrice.toFixed(2)}</span></div>
                    <div className="td-pos-row"><span>Mkt Value</span><span>${mktValue.toFixed(2)}</span></div>
                    <div className="td-pos-row" style={{ marginTop: '8px', paddingTop: '8px', borderTop: '0.5px solid var(--border)' }}>
                      <span>Unrealized P&L</span>
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

      {activeTab === 'search' && (
        <div>
          <input
            className="td-search-box"
            type="text"
            placeholder="Search by ticker or company name (e.g. AAPL, Tesla, RELIANCE.NS)…"
            value={searchQuery}
            onChange={handleSearch}
          />
          {isSearching && <div className="td-loading">Searching live data…</div>}
          {searchResults.length === 0 && searchQuery && !isSearching && (
            <div className="td-empty-state">No results found for "{searchQuery}"</div>
          )}
          {searchResults.length > 0 && (
            <div className="td-market-list">{renderMarketRows(searchResults)}</div>
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
                  <th>Exchange</th>
                  <th>Qty</th>
                  <th>Price (Native)</th>
                  <th>Price (USD)</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {transactionHistory.map((tx, idx) => {
                  const totalValue = (tx.shares * tx.price_per_share).toFixed(2);
                  const ts = tx.timestamp ? new Date(tx.timestamp).toLocaleString() : '-';
                  return (
                    <tr key={idx}>
                      <td style={{ fontSize: '12px', color: 'var(--text-sec)' }}>{ts}</td>
                      <td><span className={tx.action === 'BUY' ? 'td-badge-buy' : 'td-badge-sell'}>{tx.action}</span></td>
                      <td style={{ fontWeight: '700' }}>{tx.ticker}</td>
                      <td><span className="td-badge-currency">{tx.exchange || 'Unknown'}</span></td>
                      <td>{tx.shares}</td>
                      <td>{tx.original_price_per_share?.toFixed(2) || '-'} {tx.currency}</td>
                      <td>${tx.price_per_share?.toFixed(2)}</td>
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
