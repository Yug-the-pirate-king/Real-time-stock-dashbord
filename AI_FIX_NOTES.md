# AI Fix — Issue #1: Performance: Identify and optimize bottlenecks

**Issue body:**

This is an automated issue created by the AI agent to track planned code quality improvements. The AI will fix this in a subsequent run.

---

**AI-proposed fix:**

**Root cause analysis**

The most common performance collapse in a real-time stock dashboard is **high-frequency price updates triggering full React re-render trees** on every tick:

1. **Un-throttled state updates** – every WebSocket/polling message immediately calls `setState`, so React re-renders the whole app at the message rate.
2. **No memoization boundaries** – `StockList`, `StockChart`, and every row re-render even when their own props have not changed.
3. **Large lists rendered to the DOM** – rendering hundreds of stock rows without virtualization blocks the main thread.
4. **Charts redraw the entire history** – passing a growing history array into the chart on every tick causes expensive SVG/Canvas re-layouts.
5. **Repeated API/polling work** – requests fire before previous ones resolve, causing duplicate network and parse work.

Below are concrete fixes for the assumed structure of this repo (a React frontend with WebSocket or REST polling). Adjust the paths to match the actual layout.

---

### 1. Throttle and batch real-time updates
**File:** `src/hooks/useStockData.js`

Replace per-message `setState` with a batched flush, and keep only the last N history points.

```diff
-import { useEffect, useState } from 'react';
+import { useEffect, useRef, useState, useCallback, useMemo } from 'react';

-export function useStockData() {
-  const [stocks, setStocks] = useState([]);
+export function useStockData({ throttleMs = 1000, maxHistory = 200 } = {}) {
+  const [stocks, setStocks] = useState({});
+  const pendingRef = useRef([]);
+  const timerRef = useRef(null);

+  const flush = useCallback(() => {
+    if (pendingRef.current.length === 0) return;
+    const batch = pendingRef.current;
+    pendingRef.current = [];
+
+    setStocks(prev => {
+      const next = { ...prev };
+      for (const update of batch) {
+        const prevEntry = next[update.ticker] || { history: [] };
+        next[update.ticker] = {
+          ...prevEntry,
+          ...update,
+          history: [
+            ...prevEntry.history.slice(-maxHistory + 1),
+            { price: update.price, time: update.time },
+          ],
+        };
+      }
+      return next;
+    });
+  }, [maxHistory]);

   useEffect(() => {
-    const id = setInterval(async () => {
-      const res = await fetch('/api/stocks');
-      const data = await res.json();
-      setStocks(data);
-    }, 1000);
-    return () => clearInterval(id);
-  }, []);
-
-  return stocks;
+    const socket = new WebSocket('wss://your-feed');
+
+    const handleMessage = (event) => {
+      const update = JSON.parse(event.data);
+      pendingRef.current.push(update);
+      if (!timerRef.current) {
+        timerRef.current = setTimeout(() => {
+          flush();
+          timerRef.current = null;
+        }, throttleMs);
+      }
+    };
+
+    socket.addEventListener('message', handleMessage);
+    return () => {
+      socket.close();
+      if (timerRef.current) clearTimeout(timerRef.current);
+    };
+  }, [flush, throttleMs]);
+
+  // Stable array reference only changes when data actually changes
+  return useMemo(() => Object.values(stocks), [stocks]);
 }
```

---

### 2. Virtualize the stock list and memoize rows
**Files:** `src/components/StockList.jsx` and `src/components/StockRow.jsx`

```diff
 // src/components/StockList.jsx
-import React from 'react';
+import React, { useCallback } from 'react';
+import { FixedSizeList as List } from 'react-window';
 import StockRow from './StockRow';

-export default function StockList({ stocks, onSelect }) {
-  return (
-    <ul className="stock-list">
-      {stocks.map(stock => (
-        <StockRow
-          key={stock.ticker}
-          stock={stock}
-          onClick={() => onSelect(stock.ticker)}
-        />
-      ))}
-    </ul>
-  );
-}
+const StockList = React.memo(({ stocks, onSelect }) => {
+  const Row = useCallback(
+    ({ index, style }) => (
+      <StockRow
+        style={style}
+        stock={stocks[index]}
+        onSelect={onSelect}
+      />
+    ),
+    [stocks, onSelect]
+  );
+
+  return (
+    <List
+      className="stock-list"
+      height={600}
+      itemCount={stocks.length}
+      itemSize={56}
+      width="100%"
+    >
+      {Row}
+    </List>
+  );
+});
+
+export default StockList;
```

```diff
 // src/components/StockRow.jsx
-import React from 'react';
+import React, { useCallback } from 'react';

-const StockRow = ({ stock, onClick }) => {
-  return (
-    <li onClick={onClick} className={stock.change >= 0 ? 'up' : 'down'}>
-      <span>{stock.ticker}</span>
-      <span>{stock.price.toFixed(2)}</span>
-    </li>
-  );
-};
+const StockRow = React.memo(({ stock, style, onSelect }) => {
+  const handleClick = useCallback(() => onSelect(stock.ticker), [
+    onSelect,
+    stock.ticker,
+  ]);
+
+  return (
+    <div style={style} onClick={handleClick} className={stock.change >= 0 ? 'up' : 'down'}>
+      <span>{stock.ticker}</span>
+      <span>{stock.price.toFixed(2)}</span>
+    </div>
+  );
+});
+
 export default StockRow;
```

> If `react-window` is not installed, add it: `npm install react-window`.

---

### 3. Memoize chart data and down-sample history
**File:** `src/components/StockChart.jsx`

```diff
 // src/components/StockChart.jsx
-import React from 'react';
+import React, { useMemo } from 'react';
 import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

-const StockChart = ({ history }) => {
-  return (
-    <ResponsiveContainer width="100%" height={300}>
-      <LineChart data={history}>
-        <XAxis dataKey="time" />
-        <YAxis domain={['auto', 'auto']} />
-        <Tooltip />
-        <Line type="monotone" dataKey="price" stroke="#8884d8" dot={false} />
-      </LineChart>
-    </ResponsiveContainer>
-  );
-};
+const StockChart = React.memo(({ history }) => {
+  const chartData = useMemo(() => history.slice(-100), [history]);
+
+  return (
+    <ResponsiveContainer width="100%" height={300}>
+      <LineChart data={chartData}>
+        <XAxis dataKey="time" />
+        <YAxis domain={['auto', 'auto']} />
+        <Tooltip />
+        <Line type="monotone" dataKey="price" stroke="#8884d8" dot={false} isAnimationActive={false} />
+      </LineChart>
+    </ResponsiveContainer>
+  );
+});
+
 export default StockChart;
```

---

### 4. Deduplicate REST/polling requests
**File:** `src/utils/api.js`

```diff
 // src/utils/api.js
+let pendingPromise = null;
+
 export async function fetchStocks(signal) {
-  const res = await fetch('/api/stocks', { signal });
-  return res.json();
+  if (pendingPromise) return pendingPromise;
+
+  pendingPromise = fetch('/api/stocks', { signal })
+    .then(r => r.json())
+    .finally(() => {
+      pendingPromise = null;
+    });
+
+  return pendingPromise;
 }
```

---

### 5. Prevent parent-level re-render churn
**File:** `src/App.jsx`

```diff
 // src/App.jsx
-import { useState } from 'react';
+import { useState, useCallback, useMemo } from 'react';
 import StockList from './components/StockList';
 import StockChart from './components/StockChart';
 import { useStockData } from './hooks/useStockData';

 const App = () => {
   const stocks = useStockData({ throttleMs: 1000, maxHistory: 200 });
   const [selectedTicker, setSelectedTicker] = useState(null);

+  const handleSelect = useCallback((ticker) => {
+    setSelectedTicker(ticker);
+  }, []);
+
+  const selectedStock = useMemo(
+    () => stocks.find(s => s.ticker === selectedTicker),
+    [stocks, selectedTicker]
+  );
+
   return (
     <div className="app">
-      <StockList stocks={stocks} onSelect={setSelectedTicker} />
-      {selectedTicker && (
-        <StockChart history={stocks.find(s => s.ticker === selectedTicker)?.history || []} />
-      )}
+      <StockList stocks={stocks} onSelect={handleSelect} />
+      {selectedStock && <StockChart history={selectedStock.history} />}
     </div>
   );
 };
```

---

## Follow-up actions

1. **Profile before/after**  
   - Use React DevTools Profiler and Chrome Performance tab to confirm render time drops.  
   - Target: main-thread long tasks under 50 ms and list scroll at 60 fps.

2. **Add performance budgets in CI**  
   ```json
   // package.json
   "performance-budget": {
     "maxBundleSize": "250kb",
     "maxFirstContentfulPaint": "1.5s"
   }
   ```

3. **Down-sample on the server** if history grows beyond a few hundred points. Returning every tick to the client does not scale.

4. **Move heavy calculations off the main thread** if you add technical indicators (moving averages, etc.). Use a Web Worker in `src/workers/indicators.worker.js`.

5. **Consider binary WebSocket frames** (e.g., MsgPack) and per-ticker update batching on the backend if message volume is very high.

6. **Write regression tests** that assert the number of renders does not explode when feed messages arrive.
