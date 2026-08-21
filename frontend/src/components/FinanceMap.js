import React, { useEffect, useRef, useState } from 'react';
import { API_BASE_URL } from '../config/api';

/**
 * Available marker filters for the finance map.
 * @type {Array<{key: string, label: string}>}
 */
const FILTER_OPTIONS = [
  { key: 'all', label: 'All' },
  { key: 'exchange', label: 'Exchanges' },
  { key: 'central_bank', label: 'Central Banks' },
];

/** Color used for stock exchange markers. */
const EXCHANGE_COLOR = '#1a4a2e';
/** Color used for central bank markers. */
const BANK_COLOR = '#1a3a5c';

/** CartoDB light tile layer URL used as the base map. */
const TILE_LAYER_URL =
  'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

/** CartoDB tile layer attribution string. */
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

/**
 * Polls the global window object until the Leaflet library (`window.L`)
 * becomes available, or until the provided timeout expires.
 *
 * @param {number} [timeout=5000] - Maximum time to wait, in milliseconds.
 * @returns {Promise<typeof import('leaflet')>} Resolves with the Leaflet object.
 * @throws {Error} If Leaflet does not load within the timeout.
 */
function waitForLeaflet(timeout = 5000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();

    /**
     * Recursively checks for the Leaflet global. Uses a short interval
     * to avoid blocking the main thread.
     */
    const check = () => {
      if (typeof window !== 'undefined' && window.L) {
        resolve(window.L);
        return;
      }

      if (Date.now() - startTime > timeout) {
        reject(new Error('Leaflet failed to load'));
        return;
      }

      setTimeout(check, 100);
    };

    check();
  });
}

/**
 * Renders an HTML string for a Leaflet popup based on a marker's metadata.
 *
 * @param {Object} marker - The marker data object.
 * @param {boolean} isExchange - Whether the marker represents an exchange.
 * @param {string} color - CSS color used for the popup header.
 * @returns {string} HTML content for the popup.
 */
function buildPopupHtml(marker, isExchange, color) {
  const location = [
    marker.city || '',
    marker.city && marker.country ? ', ' : '',
    marker.country || '',
  ].join('');

  const detail = isExchange
    ? `Tier: ${marker.tier || 'N/A'}`
    : `Type: ${marker.bankType || 'N/A'}`;

  const extraLines = [
    marker.marketCap ? `Market Cap: $${marker.marketCap}T` : '',
    marker.currency ? `Currency: ${marker.currency}` : '',
    marker.tradingHours ? `Hours: ${marker.tradingHours}` : '',
  ]
    .filter(Boolean)
    .join('<br/>');

  return `
    <div style="font-family:'DM Sans',sans-serif;min-width:180px">
      <div style="font-size:13px;font-weight:700;margin-bottom:4px;color:${color}">
        ${marker.shortName || marker.name}
      </div>
      <div style="font-size:11px;color:#555;line-height:1.4">
        ${location}<br/>
        ${detail}<br/>
        ${extraLines}
      </div>
      ${
        marker.description
          ? `<div style="margin-top:6px;font-size:11px;color:#777;border-top:1px solid #eee;padding-top:4px">${marker.description}</div>`
          : ''
      }
    </div>
  `;
}

/**
 * FinanceMap component.
 *
 * Displays an interactive Leaflet map of financial institutions (stock
 * exchanges and central banks). Fetches geographic data from the backend,
 * allows filtering by institution type, and renders circle markers with
 * informational popups.
 *
 * @returns {JSX.Element} The rendered map component.
 */
export default function FinanceMap() {
  // Ref for the DOM element that will host the Leaflet map.
  const mapContainerRef = useRef(null);
  // Ref to the Leaflet map instance, used across effects.
  const mapInstanceRef = useRef(null);

  const [ready, setReady] = useState(false);
  const [markers, setMarkers] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all' | 'exchange' | 'central_bank'

  /**
   * Effect 1: Fetch geographic marker data once when the component mounts.
   *
   * Sends a request to the /finance/geo endpoint and normalizes the response
   * into an array of markers. The `cancelled` flag prevents state updates
   * after the component has unmounted.
   */
  useEffect(() => {
    let cancelled = false;

    async function fetchGeo() {
      try {
        const response = await fetch(`${API_BASE_URL}/finance/geo`);
        const data = await response.json();

        if (!cancelled) {
          setMarkers(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error('Geo fetch failed:', err);
      }
    }

    fetchGeo();

    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Effect 2: Initialise the Leaflet map instance once the container is
   * available and the Leaflet script has loaded from the CDN.
   *
   * Cleans up by removing the map instance on unmount to free resources
   * and avoid memory leaks.
   */
  useEffect(() => {
    let destroyed = false;
    let map = null;

    async function initMap() {
      try {
        const L = await waitForLeaflet();

        // Abort if the component unmounted or the DOM container is gone.
        if (destroyed || !mapContainerRef.current) {
          return;
        }

        // Create the map centered on the world with a low zoom level.
        map = L.map(mapContainerRef.current).setView([20, 0], 2);

        // Add the light-themed CartoDB base tile layer.
        L.tileLayer(TILE_LAYER_URL, {
          attribution: TILE_ATTRIBUTION,
          subdomains: 'abcd',
          maxZoom: 19,
        }).addTo(map);

        // Expose the instance to the marker effect and mark the map ready.
        mapInstanceRef.current = map;
        setReady(true);
      } catch (err) {
        console.error('Map init failed:', err);
      }
    }

    initMap();

    return () => {
      destroyed = true;

      if (map) {
        map.remove();
        map = null;
      }

      mapInstanceRef.current = null;
    };
  }, []);

  /**
   * Effect 3: Render or update markers whenever the dataset or active
   * filter changes.
   *
   * Clears previously rendered circle markers (but leaves the tile layer
   * intact) and draws only the markers matching the selected filter.
   */
  useEffect(() => {
    const map = mapInstanceRef.current;
    const L = window.L;

    // Wait until the map is fully initialised and Leaflet is available.
    if (!map || !L || !ready) {
      return;
    }

    // Remove old circle markers. We deliberately keep tile layers.
    map.eachLayer((layer) => {
      if (layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // Determine which markers are visible under the current filter.
    const visibleMarkers = markers.filter((marker) => {
      if (filter === 'all') {
        return true;
      }
      return marker.type === filter;
    });

    // Render each visible marker on the map.
    visibleMarkers.forEach((marker) => {
      // Skip markers that lack coordinates to avoid Leaflet errors.
      if (marker.lat == null || marker.lon == null) {
        return;
      }

      const isExchange = marker.type === 'exchange';
      const color = isExchange ? EXCHANGE_COLOR : BANK_COLOR;
      const radius = isExchange ? 8 : 6;

      const circleMarker = L.circleMarker([marker.lat, marker.lon], {
        radius,
        fillColor: color,
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85,
      }).addTo(map);

      // Attach a popup containing formatted metadata.
      circleMarker.bindPopup(buildPopupHtml(marker, isExchange, color));
    });
  }, [markers, filter, ready]);

  return (
    <div>
      {/* Filter controls: choose which marker types to display. */}
      <div className="map-controls">
        {FILTER_OPTIONS.map((option) => (
          <button
            key={option.key}
            className={`news-cat-btn ${filter === option.key ? 'active' : ''}`}
            onClick={() => setFilter(option.key)}
            aria-pressed={filter === option.key}
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Map container. Shows a loading indicator until Leaflet is ready. */}
      <div ref={mapContainerRef} className="finance-map">
        {!ready && (
          <div
            className="td-loading"
            style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            Loading map…
          </div>
        )}
      </div>

      {/* Legend explaining marker colors. */}
      <div className="map-legend">
        <div className="map-legend-item">
          <span className="map-dot" style={{ background: EXCHANGE_COLOR }} />
          <span className="map-legend-label">Stock Exchange</span>
        </div>
        <div className="map-legend-item">
          <span className="map-dot" style={{ background: BANK_COLOR }} />
          <span className="map-legend-label">Central Bank</span>
        </div>
      </div>
    </div>
  );
}