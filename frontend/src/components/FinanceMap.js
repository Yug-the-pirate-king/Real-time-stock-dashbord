import React, { useEffect, useRef, useState } from 'react';
import { API_BASE_URL } from '../config/api';

/* ─── Wait for Leaflet to load from CDN ───────────────── */
function waitForLeaflet(timeout = 5000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      if (typeof window !== 'undefined' && window.L) {
        resolve(window.L);
        return;
      }
      if (Date.now() - start > timeout) {
        reject(new Error('Leaflet failed to load'));
        return;
      }
      setTimeout(check, 100);
    };
    check();
  });
}

export default function FinanceMap() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [markers, setMarkers] = useState([]);
  const [filter, setFilter] = useState('all'); // all | exchange | central_bank

  /* 1. Fetch geo data once on mount */
  useEffect(() => {
    let cancelled = false;
    async function fetchGeo() {
      try {
        const res = await fetch(`${API_BASE_URL}/finance/geo`);
        const data = await res.json();
        if (!cancelled) setMarkers(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Geo fetch failed:', err);
      }
    }
    fetchGeo();
    return () => { cancelled = true; };
  }, []);

  /* 2. Initialise Leaflet map (waits for window.L) */
  useEffect(() => {
    let destroyed = false;
    let map = null;

    async function init() {
      try {
        const L = await waitForLeaflet();
        if (destroyed || !mapRef.current) return;

        map = L.map(mapRef.current).setView([20, 0], 2);

        L.tileLayer(
          'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
          {
            attribution:
              '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 19,
          }
        ).addTo(map);

        mapInstanceRef.current = map;
        setReady(true);
      } catch (err) {
        console.error('Map init failed:', err);
      }
    }

    init();

    return () => {
      destroyed = true;
      if (map) {
        map.remove();
        map = null;
      }
      mapInstanceRef.current = null;
    };
  }, []);

  /* 3. Draw / redraw markers when data or filter changes */
  useEffect(() => {
    const map = mapInstanceRef.current;
    const L = window.L;
    if (!map || !L || !ready) return;

    // Remove old circle-markers (keep tile layer)
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    const visible = markers.filter((m) => {
      if (filter === 'all') return true;
      return m.type === filter;
    });

    visible.forEach((m) => {
      if (m.lat == null || m.lon == null) return;

      const isExchange = m.type === 'exchange';
      const color = isExchange ? '#1a4a2e' : '#1a3a5c';
      const radius = isExchange ? 8 : 6;

      const popupHtml = `
        <div style="font-family:'DM Sans',sans-serif;min-width:180px">
          <div style="font-size:13px;font-weight:700;margin-bottom:4px;color:${color}">
            ${m.shortName || m.name}
          </div>
          <div style="font-size:11px;color:#555;line-height:1.4">
            ${m.city || ''}${m.city && m.country ? ', ' : ''}${m.country || ''}<br/>
            ${isExchange ? `Tier: ${m.tier || 'N/A'}` : `Type: ${m.bankType || 'N/A'}`}
            <br/>
            ${m.marketCap ? `Market Cap: $${m.marketCap}T<br/>` : ''}
            ${m.currency ? `Currency: ${m.currency}<br/>` : ''}
            ${m.tradingHours ? `Hours: ${m.tradingHours}<br/>` : ''}
          </div>
          ${
            m.description
              ? `<div style="margin-top:6px;font-size:11px;color:#777;border-top:1px solid #eee;padding-top:4px">${m.description}</div>`
              : ''
          }
        </div>
      `;

      const marker = L.circleMarker([m.lat, m.lon], {
        radius,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      }).addTo(map);

      marker.bindPopup(popupHtml);
    });
  }, [markers, filter, ready]);

  return (
    <div>
      <div className="map-controls">
        {[
          { key: 'all', label: 'All' },
          { key: 'exchange', label: 'Exchanges' },
          { key: 'central_bank', label: 'Central Banks' },
        ].map((f) => (
          <button
            key={f.key}
            className={`news-cat-btn ${filter === f.key ? 'active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div ref={mapRef} className="finance-map">
        {!ready && (
          <div className="td-loading" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            Loading map…
          </div>
        )}
      </div>

      <div className="map-legend">
        <div className="map-legend-item">
          <span className="map-dot" style={{ background: '#1a4a2e' }} />
          <span className="map-legend-label">Stock Exchange</span>
        </div>
        <div className="map-legend-item">
          <span className="map-dot" style={{ background: '#1a3a5c' }} />
          <span className="map-legend-label">Central Bank</span>
        </div>
      </div>
    </div>
  );
}
