import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { API_BASE_URL } from '../config/api';
import '../styles/options-lab.css';
import {
  FaFlask,
  FaList,
  FaBriefcase,
} from 'react-icons/fa';

const STRATEGIES = [
  { key: 'straddle', label: 'Long Straddle', short: 'Straddle' },
  { key: 'strangle', label: 'Long Strangle', short: 'Strangle' },
  { key: 'iron_condor', label: 'Iron Condor', short: 'Iron Condor' },
  { key: 'bull_call_spread', label: 'Bull Call Spread', short: 'Bull Call' },
  { key: 'bear_put_spread', label: 'Bear Put Spread', short: 'Bear Put' },
];

export default function OptionsLab({ user }) {
  const [tab, setTab] = useState('builder');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);

  // Builder state
  const [underlying, setUnderlying] = useState('AAPL');
  const [strategyName, setStrategyName] = useState('straddle');
  const [expiry, setExpiry] = useState('');
  const [lots, setLots] = useState(1);
  const [width, setWidth] = useState('');
  const [nearWidth, setNearWidth] = useState('');
  const [farWidth, setFarWidth] = useState('');
  const [lowerStrike, setLowerStrike] = useState('');
  const [upperStrike, setUpperStrike] = useState('');
  const [preview, setPreview] = useState(null);

  // Chain + portfolio state
  const [chain, setChain] = useState(null);
  const [portfolio, setPortfolio] = useState([]);

  const userId = user?.id ? String(user.id) : null;

  const fetchChain = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/options/chain/${underlying}${expiry ? `?expiry=${expiry}` : ''}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Chain fetch failed');
      setChain(data);
    } catch (err) {
      showToast(err.message, 'error');
      setChain(null);
    } finally {
      setLoading(false);
    }
  }, [underlying, expiry]);

  const fetchPortfolio = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/options/portfolio/${userId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Portfolio fetch failed');
      setPortfolio(Array.isArray(data) ? data : []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    if (tab === 'chain') fetchChain();
    if (tab === 'portfolio') fetchPortfolio();
  }, [tab, fetchChain, fetchPortfolio]);

  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const buildQuery = () => {
    const params = new URLSearchParams({
      underlying,
      lots: String(lots),
      direction: 'BUY',
    });
    if (expiry) params.set('expiry', expiry);
    if (strategyName === 'strangle' && width) params.set('width', width);
    if (strategyName === 'iron_condor') {
      if (nearWidth) params.set('near_width', nearWidth);
      if (farWidth) params.set('far_width', farWidth);
    }
    if (['bull_call_spread', 'bear_put_spread'].includes(strategyName)) {
      if (lowerStrike) params.set('lower_strike', lowerStrike);
      if (upperStrike) params.set('upper_strike', upperStrike);
    }
    return params.toString();
  };

  const previewStrategy = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/options/strategies/${strategyName}?${buildQuery()}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Preview failed');
      setPreview(data);
    } catch (err) {
      showToast(err.message, 'error');
      setPreview(null);
    } finally {
      setLoading(false);
    }
  };

  const buyStrategy = async () => {
    if (!userId) {
      showToast('Please log in to trade options.', 'error');
      return;
    }
    if (!preview) {
      showToast('Preview a strategy first.', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/options/strategy/buy?user_id=${userId}&strategy_name=${strategyName}&${buildQuery()}`,
        { method: 'POST' }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Order failed');
      showToast(data.message, 'success');
      setPreview(null);
      setTab('portfolio');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const closeStrategy = async (id) => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/options/position/${id}?user_id=${userId}`,
        { method: 'DELETE' }
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Close failed');
      showToast(`Closed: PnL $${data.pnl?.toFixed(2) ?? '-'}`, 'success');
      fetchPortfolio();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const extraFields = useMemo(() => {
    if (strategyName === 'straddle') return null;
    if (strategyName === 'strangle') {
      return (
        <div className="opt-field">
          <label>OTM Width</label>
          <input
            type="number"
            step="0.5"
            placeholder="Auto"
            value={width}
            onChange={(e) => setWidth(e.target.value)}
          />
        </div>
      );
    }
    if (strategyName === 'iron_condor') {
      return (
        <>
          <div className="opt-field">
            <label>Near Width</label>
            <input
              type="number"
              step="0.5"
              placeholder="Auto"
              value={nearWidth}
              onChange={(e) => setNearWidth(e.target.value)}
            />
          </div>
          <div className="opt-field">
            <label>Far Width</label>
            <input
              type="number"
              step="0.5"
              placeholder="Auto"
              value={farWidth}
              onChange={(e) => setFarWidth(e.target.value)}
            />
          </div>
        </>
      );
    }
    return (
      <>
        <div className="opt-field">
          <label>Lower Strike</label>
          <input
            type="number"
            step="0.5"
            placeholder="Auto"
            value={lowerStrike}
            onChange={(e) => setLowerStrike(e.target.value)}
          />
        </div>
        <div className="opt-field">
          <label>Upper Strike</label>
          <input
            type="number"
            step="0.5"
            placeholder="Auto"
            value={upperStrike}
            onChange={(e) => setUpperStrike(e.target.value)}
          />
        </div>
      </>
    );
  }, [strategyName, width, nearWidth, farWidth, lowerStrike, upperStrike]);

  return (
    <div className="opt-shell">
      {toast && (
        <div className={`opt-toast opt-toast-${toast.type}`}>{toast.message}</div>
      )}

      <div className="opt-tabs">
        <button
          className={`opt-tab ${tab === 'builder' ? 'active' : ''}`}
          onClick={() => setTab('builder')}
        >
          <FaFlask style={{ marginRight: 8 }} /> Strategy Builder
        </button>
        <button
          className={`opt-tab ${tab === 'chain' ? 'active' : ''}`}
          onClick={() => setTab('chain')}
        >
          <FaList style={{ marginRight: 8 }} /> Option Chain
        </button>
        <button
          className={`opt-tab ${tab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setTab('portfolio')}
        >
          <FaBriefcase style={{ marginRight: 8 }} /> Open Positions
        </button>
      </div>

      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div className="opt-spinner" />
          <span style={{ color: 'var(--gray-500)', fontSize: 13 }}>Loading…</span>
        </div>
      )}

      {tab === 'builder' && (
        <>
          <div className="opt-card">
            <h3>Build a Strategy</h3>
            <div className="opt-form-row">
              <div className="opt-field">
                <label>Underlying</label>
                <input
                  type="text"
                  value={underlying}
                  onChange={(e) => setUnderlying(e.target.value.toUpperCase())}
                />
              </div>
              <div className="opt-field">
                <label>Strategy</label>
                <select
                  value={strategyName}
                  onChange={(e) => {
                    setStrategyName(e.target.value);
                    setPreview(null);
                    setWidth('');
                    setNearWidth('');
                    setFarWidth('');
                    setLowerStrike('');
                    setUpperStrike('');
                  }}
                >
                  {STRATEGIES.map((s) => (
                    <option key={s.key} value={s.key}>{s.label}</option>
                  ))}
                </select>
              </div>
              <div className="opt-field">
                <label>Expiry (ISO)</label>
                <input
                  type="text"
                  placeholder="Auto"
                  value={expiry}
                  onChange={(e) => setExpiry(e.target.value)}
                />
              </div>
              <div className="opt-field">
                <label>Lots</label>
                <input
                  type="number"
                  min="1"
                  value={lots}
                  onChange={(e) => setLots(parseInt(e.target.value) || 1)}
                />
              </div>
              {extraFields}
              <button className="opt-btn opt-btn-secondary" onClick={previewStrategy}>
                Preview
              </button>
            </div>
          </div>

          {preview && (
            <div className="opt-card">
              <h3>{preview.name}</h3>
              <div className="opt-metrics">
                <div className="opt-metric">
                  <div className="opt-metric-label">Net Premium</div>
                  <div className="opt-metric-value">
                    {preview.net_premium >= 0 ? '+' : ''}${preview.net_premium?.toFixed(2)}
                  </div>
                </div>
                <div className="opt-metric">
                  <div className="opt-metric-label">Max Profit</div>
                  <div className="opt-metric-value">
                    {preview.max_profit !== null && preview.max_profit !== undefined
                      ? `$${preview.max_profit.toFixed(2)}`
                      : '—'}
                  </div>
                </div>
                <div className="opt-metric">
                  <div className="opt-metric-label">Max Loss</div>
                  <div className="opt-metric-value">
                    {preview.max_loss !== null && preview.max_loss !== undefined
                      ? `$${Math.abs(preview.max_loss).toFixed(2)}`
                      : '—'}
                  </div>
                </div>
                <div className="opt-metric">
                  <div className="opt-metric-label">Breakevens</div>
                  <div className="opt-metric-value">
                    {preview.breakeven_lower || preview.breakeven_upper
                      ? `${preview.breakeven_lower ?? '—'} / ${preview.breakeven_upper ?? '—'}`
                      : '—'}
                  </div>
                </div>
              </div>

              <table className="opt-legs-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Type</th>
                    <th>Strike</th>
                    <th>Qty</th>
                    <th>Premium</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.legs.map((leg, i) => (
                    <tr key={i}>
                      <td>{leg.symbol}</td>
                      <td>
                        <span className={`opt-tag opt-tag-${leg.side.toLowerCase()}`}>
                          {leg.side}
                        </span>
                      </td>
                      <td>
                        <span className={`opt-tag opt-tag-${leg.option_type.toLowerCase()}`}>
                          {leg.option_type}
                        </span>
                      </td>
                      <td>${leg.strike.toFixed(2)}</td>
                      <td>{leg.quantity}</td>
                      <td>${leg.premium.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                <button className="opt-btn opt-btn-primary" onClick={buyStrategy}>
                  Execute Paper Trade
                </button>
                <button
                  className="opt-btn opt-btn-secondary"
                  onClick={() => setPreview(null)}
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'chain' && (
        <div className="opt-card">
          <h3>Option Chain for {underlying}</h3>
          <div className="opt-form-row" style={{ marginBottom: 16 }}>
            <div className="opt-field">
              <label>Underlying</label>
              <input
                type="text"
                value={underlying}
                onChange={(e) => setUnderlying(e.target.value.toUpperCase())}
              />
            </div>
            <div className="opt-field">
              <label>Expiry</label>
              <input
                type="text"
                placeholder={chain?.expiry ?? 'Auto'}
                value={expiry}
                onChange={(e) => setExpiry(e.target.value)}
              />
            </div>
            <button className="opt-btn opt-btn-secondary" onClick={fetchChain}>
              Fetch
            </button>
          </div>

          {chain?.fallback && (
            <div className="opt-fallback-note">
              Live option chain unavailable. Showing synthetic estimates for demo purposes.
            </div>
          )}

          {chain && (
            <div style={{ marginBottom: 12, fontSize: 13, color: 'var(--gray-500)' }}>
              Spot: <strong>${chain.spot}</strong> · Expiry: <strong>{chain.expiry}</strong> · ATM: <strong>${chain.atm}</strong>
            </div>
          )}

          {chain && (
            <div className="opt-chain-grid">
              <div className="opt-chain-col">
                <h4>Calls (CE)</h4>
                <table className="opt-legs-table">
                  <thead>
                    <tr>
                      <th>Strike</th>
                      <th>Premium</th>
                      <th>IV</th>
                      <th>OI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(chain.calls || []).slice(0, 10).map((c, i) => (
                      <tr key={`c-${i}`}>
                        <td>${c.strike.toFixed(2)}</td>
                        <td>${c.last_price.toFixed(2)}</td>
                        <td>{c.implied_volatility ? (c.implied_volatility * 100).toFixed(1) + '%' : '—'}</td>
                        <td>{c.open_interest ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="opt-chain-col">
                <h4>Puts (PE)</h4>
                <table className="opt-legs-table">
                  <thead>
                    <tr>
                      <th>Strike</th>
                      <th>Premium</th>
                      <th>IV</th>
                      <th>OI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(chain.puts || []).slice(0, 10).map((p, i) => (
                      <tr key={`p-${i}`}>
                        <td>${p.strike.toFixed(2)}</td>
                        <td>${p.last_price.toFixed(2)}</td>
                        <td>{p.implied_volatility ? (p.implied_volatility * 100).toFixed(1) + '%' : '—'}</td>
                        <td>{p.open_interest ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'portfolio' && (
        <div className="opt-card">
          <h3>Open Option Strategies</h3>
          {!userId ? (
            <div className="opt-empty">Log in to view option positions.</div>
          ) : portfolio.length === 0 ? (
            <div className="opt-empty">
              <div className="opt-empty-icon"><FaBriefcase /></div>
              No open option strategies yet.
            </div>
          ) : (
            <div className="opt-strategy-grid">
              {portfolio.map((pos) => (
                <div className="opt-strategy-card" key={pos.id}>
                  <h4>{pos.name}</h4>
                  <div className="opt-strategy-meta">
                    {pos.underlying} · {pos.expiry} · Spot ${pos.spot}
                  </div>
                  <div className="opt-metrics">
                    <div className="opt-metric">
                      <div className="opt-metric-label">Net Premium</div>
                      <div className="opt-metric-value">
                        {pos.total_premium >= 0 ? '+' : ''}${pos.total_premium.toFixed(2)}
                      </div>
                    </div>
                    <div className="opt-metric">
                      <div className="opt-metric-label">Est. Value</div>
                      <div className="opt-metric-value">${pos.estimated_value.toFixed(2)}</div>
                    </div>
                  </div>
                  <table className="opt-legs-table">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Side</th>
                        <th>Strike</th>
                        <th>Qty</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pos.legs.map((leg, i) => (
                        <tr key={i}>
                          <td>
                            <span className={`opt-tag opt-tag-${leg.option_type.toLowerCase()}`}>
                              {leg.option_type}
                            </span>
                          </td>
                          <td>{leg.side}</td>
                          <td>${leg.strike.toFixed(2)}</td>
                          <td>{leg.quantity}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <button
                    className="opt-btn opt-btn-danger"
                    style={{ marginTop: 12, width: '100%' }}
                    onClick={() => closeStrategy(pos.id)}
                  >
                    Close Strategy
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
