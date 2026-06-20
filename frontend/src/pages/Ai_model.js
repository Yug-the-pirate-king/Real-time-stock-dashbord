import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config/api';
import Chart from 'chart.js/auto';

export default function Ai_model({ user }) {
  const [ticker, setTicker] = useState('AAPL');
  const [period, setPeriod] = useState('1mo');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  const periods = [
    { key: '1mo', label: '1 Month' },
    { key: '3mo', label: '3 Months' },
    { key: '6mo', label: '6 Months' },
    { key: '1y', label: '1 Year' },
  ];

  useEffect(() => {
    fetchAnalysis();
  }, []);

  useEffect(() => {
    if (!data || !chartRef.current) return;
    if (chartInstance.current) chartInstance.current.destroy();

    const prices = data.prices_usd || [];
    const labels = data.dates || [];

    // Compute SMAs
    const sma = (arr, window) => {
      const res = [];
      for (let i = 0; i < arr.length; i++) {
        if (i + 1 < window) { res.push(null); continue; }
        const slice = arr.slice(i - window + 1, i + 1);
        res.push(slice.reduce((a, b) => a + b, 0) / window);
      }
      return res;
    };

    const sma20 = sma(prices, Math.min(20, prices.length));
    const sma50 = sma(prices, Math.min(50, prices.length));

    const ctx = chartRef.current.getContext('2d');
    chartInstance.current = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Price',
            data: prices,
            borderColor: '#0e0e0e',
            backgroundColor: 'transparent',
            tension: 0.2,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: '#0e0e0e',
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2,
            borderWidth: 1.5,
            segment: {
              borderColor: ctx => ctx.p0.parsed.y <= ctx.p1.parsed.y ? '#16a34a' : '#dc2626'
            }
          },
          {
            label: 'SMA Short',
            data: sma20,
            borderColor: '#2d6b45',
            backgroundColor: 'transparent',
            tension: 0.2,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 1.5,
            borderDash: [4, 4],
          },
          {
            label: 'SMA Long',
            data: sma50,
            borderColor: '#1a3a5c',
            backgroundColor: 'transparent',
            tension: 0.2,
            pointRadius: 0,
            pointHoverRadius: 4,
            borderWidth: 1.5,
            borderDash: [2, 2],
          },
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: { display: true, labels: { boxWidth: 10, font: { size: 11 } } },
          tooltip: {
            backgroundColor: 'rgba(14,14,14,0.92)',
            titleFont: { family: "'Syne', sans-serif", size: 13 },
            bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
            padding: 10,
            cornerRadius: 8,
            displayColors: true,
            callbacks: {
              title: (items) => {
                const lbl = items[0]?.label;
                const d = new Date(lbl);
                if (isNaN(d)) return lbl;
                return d.toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
              },
              label: (ctx) => `${ctx.dataset.label}: $${Number(ctx.raw || 0).toFixed(2)}`,
            }
          }
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: 8, font: { size: 10, family: "'JetBrains Mono', monospace" }, color: 'var(--text-muted)', maxRotation: 0, autoSkip: true },
            grid: { display: false },
          },
          y: {
            ticks: { font: { size: 10, family: "'JetBrains Mono', monospace" }, color: 'var(--text-muted)', callback: (val) => '$' + Number(val).toFixed(0) },
            grid: { color: '#f0f0eb' },
          }
        }
      }
    });
  }, [data]);

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/trade/history-data/${encodeURIComponent(ticker)}?period=${period}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error('AI fetch failed:', err);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  // Simple signal generator
  const computeSignal = () => {
    if (!data || !data.prices_usd) return null;
    const prices = data.prices_usd;
    const sma = (arr, w) => arr.slice(-w).reduce((a,b)=>a+b,0)/w;
    if (prices.length < 10) return null;
    const short = sma(prices, 10);
    const long = sma(prices, Math.min(30, prices.length));
    if (short > long * 1.01) return { text: 'Bullish Momentum', color: 'var(--green)' };
    if (short < long * 0.99) return { text: 'Bearish Momentum', color: 'var(--red)' };
    return { text: 'Neutral / Consolidation', color: 'var(--text-muted)' };
  };

  const signal = computeSignal();

  return (
    <div>
      <div className="td-section-label" style={{ marginTop: 0 }}>Technical Analysis & Signals</div>

      <div className="ai-controls">
        <input
          className="td-search-box"
          style={{ maxWidth: '220px', marginBottom: 0 }}
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker (e.g. AAPL)"
        />
        <div className="ai-periods">
          {periods.map(p => (
            <button
              key={p.key}
              className={`ai-period-btn ${period === p.key ? 'active' : ''}`}
              onClick={() => setPeriod(p.key)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <button className="td-btn-buy" onClick={fetchAnalysis} disabled={loading}>
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </div>

      {signal && (
        <div className="ai-signal-bar">
          <span>Signal:</span>
          <span style={{ color: signal.color, fontWeight: 700, marginLeft: '8px' }}>{signal.text}</span>
        </div>
      )}

      <div className="ai-chart-card">
        <div style={{ height: '320px' }}>
          <canvas ref={chartRef} />
        </div>
      </div>

      {!data && !loading && (
        <div className="td-empty-state">Enter a ticker and press Analyze to generate signals.</div>
      )}

      {data && (
        <div className="ai-stats-row">
          <div className="td-stat-card">
            <div className="td-stat-label">Highest</div>
            <div className="td-stat-val">${Math.max(...data.prices_usd).toFixed(2)}</div>
          </div>
          <div className="td-stat-card">
            <div className="td-stat-label">Lowest</div>
            <div className="td-stat-val">${Math.min(...data.prices_usd).toFixed(2)}</div>
          </div>
          <div className="td-stat-card">
            <div className="td-stat-label">Period Change</div>
            <div className="td-stat-val">
              {((data.prices_usd[data.prices_usd.length - 1] - data.prices_usd[0]) / data.prices_usd[0] * 100).toFixed(2)}%
            </div>
          </div>
          <div className="td-stat-card">
            <div className="td-stat-label">Data Points</div>
            <div className="td-stat-val">{data.prices_usd.length}</div>
          </div>
        </div>
      )}
    </div>
  );
}
