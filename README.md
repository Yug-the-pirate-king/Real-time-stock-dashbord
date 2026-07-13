# Stock Simulator & Predictor

A full-stack web application for simulating stock trading with AI-powered predictions. Built with FastAPI backend and React frontend featuring 3D visualizations. Now includes a **Finance Monitor** with global exchange data, central bank tracking, RSS news feeds, live market alerts, and an interactive **world map**.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Setup](#manual-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Features](#features)
- [Database Schema](#database-schema)

## 🏗️ Architecture Overview

This is a **full-stack web application** with a clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│         (Docker: localhost:80 / Dev: localhost:3000)        │
├─────────────────────────────────────────────────────────────┤
│                    HTTP/REST API Layer                      │
│              (CORS enabled for frontend origins)              │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                         │
│         (Docker: localhost:8000 / Dev: localhost:8000)      │
├─────────────────────────────────────────────────────────────┤
│                    SQLAlchemy ORM                           │
├─────────────────────────────────────────────────────────────┤
│                   SQLite Database                           │
├─────────────────────────────────────────────────────────────┤
│              Finance Monitor (World Monitor Data)           │
│   RSS Feeds · Exchanges · Central Banks · Alerts · World Map │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
stock_-Simulator_-Predictor/
│
├── docker-compose.yml                # Docker orchestration
├── .dockerignore                     # Docker ignore rules
│
├── Backend/                          # FastAPI Backend
│   ├── Dockerfile                    # Backend container image
│   ├── .dockerignore                 # Backend Docker ignore
│   ├── main.py                       # FastAPI application entry point
│   ├── database.py                   # SQLAlchemy setup & database engine
│   ├── data/
│   │   ├── __init__.py
│   │   └── finance_geo.py            # Finance geography data (exchanges, central banks, feeds)
│   ├── models/                       # Database ORM models
│   │   ├── __init__.py
│   │   ├── auth.py                   # User model & password utilities
│   │   └── trading.py                # Portfolio & TransactionHistory models
│   ├── routers/                      # API endpoint routes
│   │   ├── __init__.py
│   │   ├── auth.py                   # Authentication endpoints
│   │   ├── trading.py                # Trading endpoints
│   │   └── finance_monitor.py        # Finance Monitor endpoints (news, exchanges, banks, brief, alerts)
│   ├── requirements.txt              # Python dependencies
│   └── venv/                         # Python virtual environment (manual only)
│
└── frontend/                         # React Frontend
    ├── Dockerfile                      # Frontend container image (multi-stage nginx)
    ├── .dockerignore                   # Frontend Docker ignore
    ├── nginx.conf                      # SPA nginx config (try_files)
    ├── package.json                    # Node.js dependencies
    ├── public/                         # Static assets
    │   ├── index.html
    │   ├── manifest.json
    │   └── robots.txt
    ├── src/                          # React source code
    │   ├── App.js                    # Main React component (sidebar navigation)
    │   ├── index.js                  # Entry point
    │   ├── config/
    │   │   └── api.js                # API_BASE_URL config (localhost vs prod)
    │   ├── components/               # Reusable UI components
    │   │   ├── Antigravity.js        # 3D visualization component
    │   │   └── FinanceMap.js         # Interactive world map (exchanges + central banks)
    │   ├── pages/                    # Page components
    │   │   ├── LandingPage.js        # Home page
    │   │   ├── Login.js              # Authentication page
    │   │   ├── TradingDesk.js        # Stock trading interface with charts
    │   │   ├── Ai_model.js           # AI predictions page
    │   │   └── NewsFeed.js           # Finance Monitor (news, exchanges, banks, brief, alerts)
    │   └── styles/                   # CSS stylesheets
    │       ├── global.css            # Global styles + Finance Monitor styles
    │       ├── landing.css
    │       ├── trading-desk-new.css
    │       ├── ai.css
    │       └── news.css
    ├── package-lock.json
    └── node_modules/                 # Node.js dependencies
```

## 🛠️ Technologies Used

### Backend
- **Framework**: FastAPI 0.136+
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Bcrypt password hashing
- **External APIs**: yfinance (stock data), Finnhub (news)
- **Finance Data**: World Monitor finance variant extraction
- **CORS**: Enabled for frontend integration
- **Container**: Docker + Python 3.11 slim

### Frontend
- **Library**: React 19.2.6
- **Charts**: Chart.js + Recharts
- **3D Graphics**: Three.js 0.184.0 with @react-three/fiber
- **Icons**: React Icons 5.6.0
- **Build Tool**: React Scripts 5.0.1 / nginx 1.25
- **Package Manager**: npm
- **Container**: Docker multi-stage (node → nginx alpine)

## 📋 Prerequisites

### Option A — Docker (Recommended)
- **Docker Desktop** installed and running
- That's it — no Python, Node, or npm needed on your machine

### Option B — Manual Development
- **Python 3.8+** (for backend)
- **Node.js 16+** & **npm** (for frontend)
- **Windows, macOS, or Linux**

---

## 🐳 Quick Start (Docker)

The fastest way to run the entire application is with Docker Compose.

### Step 1: Clone / navigate to project root
```bash
cd stock_-Simulator_-Predictor
```

### Step 2: Start everything
```bash
Uncaught runtime errors:
×
ERROR
Failed to fetch
TypeError: Failed to fetch
    at seedAndLoad (http://localhost:3000/static/js/bundle.js:2373:13)
    at http://localhost:3000/static/js/bundle.js:2368:5
    at Object.react_stack_bottom_frame (http://localhost:3000/static/js/bundle.js:39019:18)
    at runWithFiberInDEV (http://localhost:3000/static/js/bundle.js:26306:68)
    at commitHookEffectListMount (http://localhost:3000/static/js/bundle.js:32310:157)
    at commitHookPassiveMountEffects (http://localhost:3000/static/js/bundle.js:32347:56)
    at commitPassiveMountOnFiber (http://localhost:3000/static/js/bundle.js:33361:25)
    at recursivelyTraversePassiveMountEffects (http://localhost:3000/static/js/bundle.js:33344:7)
    at commitPassiveMountOnFiber (http://localhost:3000/static/js/bundle.js:33418:9)
    at recursivelyTraversePassiveMountEffects (http://localhost:3000/static/js/bundle.js:33344:7)
ERROR
Failed to fetch
TypeError: Failed to fetch
    at seedAndLoad (http://localhost:3000/static/js/bundle.js:2373:13)
    at http://localhost:3000/static/js/bundle.js:2368:5
    at Object.react_stack_bottom_frame (http://localhost:3000/static/js/bundle.js:39019:18)
    at runWithFiberInDEV (http://localhost:3000/static/js/bundle.js:26306:68)
    at commitHookEffectListMount (http://localhost:3000/static/js/bundle.js:32310:157)
    at commitHookPassiveMountEffects (http://localhost:3000/static/js/bundle.js:32347:56)
    at reconnectPassiveEffects (http://localhost:3000/static/js/bundle.js:33451:9)
    at doubleInvokeEffectsOnFiber (http://localhost:3000/static/js/bundle.js:34733:127)
    at runWithFiberInDEV (http://localhost:3000/static/js/bundle.js:26306:68)
    at recursivelyTraverseAndDoubleInvokeEffectsInDEV (http://localhost:3000/static/js/bundle.js:34726:72)
```

> **First run** will build both containers. Subsequent runs are instant.

### Step 3: Open in browser
- **Frontend:** http://localhost
- **API Docs:** http://localhost:8000/docs

### Useful Docker Commands
```bash
# Run in background
docker compose up -d --build

# View live logs
docker compose logs -f

# Stop everything
docker compose down

# Stop and wipe the database volume (fresh start)
docker compose down -v
```

### What's running
| Service | Container Name | Port | Description |
|---------|----------------|------|-------------|
| `backend` | `stockpulse-backend` | 8000 | FastAPI + uvicorn |
| `frontend` | `stockpulse-frontend` | 80 | nginx serving React SPA |

### How the containers talk
- The frontend in the browser calls `http://localhost:8000` directly.
- CORS in `main.py` is pre-configured for `http://localhost` (nginx frontend).
- The SQLite database is persisted in a Docker volume (`stockpulse-db`).

---

## 🚀 Manual Setup

If you prefer running without Docker (for hot-reload development):

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd Backend
   ```

2. **Create a Python virtual environment** (if not already created):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Return to project root**:
   ```bash
   cd ..
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Return to project root**:
   ```bash
   cd ..
   ```

---

## ▶️ Running the Application

### Option A — Docker (already running after `docker compose up`)
Nothing more to do. Visit http://localhost

### Option B — Manual Development

#### Start the Backend

1. **Activate Python virtual environment**:
   ```bash
   cd Backend
   venv\Scripts\activate     # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

2. **Start the Uvicorn server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend will be available at: **http://localhost:8000**

   **Interactive API docs**: http://localhost:8000/docs

#### Start the Frontend

In a **new terminal**:

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Start the development server**:
   ```bash
   npm start
   ```

   The frontend will automatically open at: **http://localhost:3000**

---

## 📡 API Documentation

### Available at: `http://localhost:8000/docs` (Swagger UI)

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Authenticate user |
| `GET` | `/auth/profile` | Get current user profile |

### Trading
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/trade/market` | Live watchlist prices |
| `GET` | `/trade/search` | Search global stocks (Yahoo Finance) |
| `GET` | `/trade/price/{ticker}` | Single ticker live price |
| `GET` | `/trade/metrics/{ticker}` | Financial metrics (P/E, market cap, EPS, etc.) |
| `GET` | `/trade/history-data/{ticker}` | Historical prices for charts |
| `GET` | `/trade/portfolio/{user_id}` | User's holdings |
| `GET` | `/trade/history/{user_id}` | Transaction history |
| `GET` | `/trade/portfolio-prices/{user_id}` | Live portfolio prices |
| `POST` | `/trade/buy` | Buy shares |
| `POST` | `/trade/sell` | Sell shares |

### Finance Monitor (from World Monitor data)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/finance/news?category=&limit=` | Finance news (general→Finnhub, others→curated RSS) |
| `GET` | `/finance/exchanges` | Global stock exchanges (NYSE, NASDAQ, LSE, NSE, JPX, etc.) |
| `GET` | `/finance/central-banks` | Central banks & institutions (Fed, ECB, BoJ, IMF, BIS, etc.) |
| `GET` | `/finance/brief` | Auto-generated daily brief from yfinance watchlist |
| `GET` | `/finance/geo` | Combined geo-locations of exchanges + central banks (lat/lon) |
| `GET` | `/finance/alerts?threshold=` | Breaking alerts for large intraday moves |

### General
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Server status endpoint |
| `GET` | `/trade/news` | Legacy news proxy (Finnhub) |

---

## ✨ Features

### User Authentication
- Secure user registration with bcrypt password hashing
- Login system with session management
- Starting virtual balance of $100,000 for paper trading

### Trading Functionality
- **Buy stocks**: Purchase shares with virtual currency (with automatic USD conversion for international tickers)
- **Sell stocks**: Liquidate positions at current market prices
- **Portfolio tracking**: Monitor holdings, average buy prices, country flags, and exchange info
- **Transaction history**: Complete audit trail with exchange rates and original/native prices
- **Currency conversion**: Automatic detection and conversion for 20+ currencies (INR, GBP, JPY, EUR, CNY, etc.)

### Market Data
- Real-time stock data via **yfinance**
- International ticker support: `.NS`, `.L`, `.DE`, `.T`, `.HK`, etc.
- 10-symbol global watchlist (AAPL, MSFT, TSLA, NVDA, SPY, RELIANCE.NS, TCS.NS, SAP.DE, SONY, BABA)
- Detailed stock metrics (market cap, P/E ratios, dividend yield, beta, EPS, volume, 52-week range)
- Interactive charts with Chart.js (color-coded by trend)

### Finance Monitor (World Monitor Integration)
- **Market News**: 12 curated finance categories — General, Markets, Forex, Bonds, Commodities, Crypto, Central Banks, Economic, IPO/M&A, Derivatives, Regulation, Analysis
- **World Map**: Interactive Leaflet map plotting 29 stock exchanges and 14 central banks with popup details (tier, market cap, trading hours, currency)
- **Global Exchanges**: 29 exchanges with tier badges (mega/major/emerging), trading hours, market cap, and timezone
- **Central Banks**: 14 major institutions (Fed, ECB, BoJ, PBoC, SNB, RBI, IMF, BIS, etc.)
- **Daily Brief**: Auto-generated market summary with mood (bullish/bearish/neutral), top gainer/loser, and narrative
- **Breaking Alerts**: Real-time scans for intraday moves exceeding configurable thresholds

### UI/UX Features
- **3D Visualizations**: Antigravity component for immersive experience
- **Multiple pages**: Landing page, login, trading desk, AI models, Finance Monitor
- **Responsive design**: Collapsible sidebar, global CSS styling system
- **React component architecture**: Modular and maintainable code
- **International flair**: Country flags and currency badges on every stock card

## 💾 Database Schema

### Users Table
```
users
├── id (PRIMARY KEY)
├── username (UNIQUE)
├── password_hash
└── balance (default: 100000.0)
```

### Portfolios Table
```
portfolios
├── id (PRIMARY KEY)
├── user_id (FOREIGN KEY → users.id)
├── ticker
├── shares_owned
├── average_buy_price
├── currency
├── country
├── exchange
├── original_avg_buy_price
├── last_exchange_rate
└── total_cost_basis_usd
```

### Transaction History Table
```
transaction_history
├── id (PRIMARY KEY)
├── user_id (FOREIGN KEY → users.id)
├── ticker
├── action (BUY/SELL)
├── shares
├── price_per_share
├── currency
├── country
├── exchange
├── original_price_per_share
├── exchange_rate_used
├── total_value_usd
└── timestamp
```

---

## 🔒 Security Notes

- Passwords are hashed using bcrypt before storage
- CORS is configured to accept requests from `http://localhost:3000` and `http://localhost`
- Database uses foreign keys to maintain referential integrity
- SQLAlchemy provides SQL injection protection
- Docker `.dockerignore` files prevent sensitive files (`.env`, `venv`, `node_modules`) from entering images

---

## 📝 Development Tips

### Backend Development
- API automatically reloads on file changes (with `--reload`)
- Use Swagger UI at `/docs` for testing endpoints
- Check SQLite database in backend folder for data persistence
- The `data/finance_geo.py` file holds static finance geography — edit directly for new exchanges or feeds

### Frontend Development
- Hot reload enabled for React changes (`npm start`)
- Browser opens automatically on `npm start`
- Check browser DevTools for debugging
- `frontend/src/config/api.js` controls where the frontend sends API calls

### Docker Development
- Edit backend code → `docker compose up --build` to rebuild
- Edit frontend code → rebuild with `docker compose up --build`
- For rapid backend iteration, mount the code as a volume (modify `docker-compose.yml` volumes)

---

## 🐛 Troubleshooting

### Port already in use
- **Backend**: Change port in uvicorn command: `--port 8001`
- **Frontend**: Set PORT env variable: `PORT=3001 npm start`
- **Docker**: Edit `docker-compose.yml` ports mapping, e.g., `"8080:80"`

### CORS errors
- Ensure backend is running and accessible at `http://localhost:8000`
- Check `frontend/src/config/api.js` points to the correct URL
- Verify `origins` in `Backend/main.py` includes your frontend origin

### Database errors
- Delete `.db` files in backend to reset database
- In Docker, run `docker compose down -v` to wipe the volume

### Docker build failures
- Make sure Docker Desktop is running
- Try `docker compose build --no-cache`
- Check that `frontend/node_modules` exists before building (or let Docker download it)

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [Three.js Guide](https://threejs.org/docs/)
- [yfinance Library](https://github.com/ranaroussi/yfinance)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [World Monitor Finance Variant](https://finance.worldmonitor.app) *(source of finance geography data)*

---

**Happy Trading! 📈**
