# Stock Simulator & Predictor

A full-stack web application for simulating stock trading with AI-powered predictions. Built with FastAPI backend and React frontend featuring 3D visualizations.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Features](#features)
- [Database Schema](#database-schema)

## 🏗️ Architecture Overview

This is a **full-stack web application** with a clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend                         │
│         (localhost:3000 - Single Page Application)          │
├─────────────────────────────────────────────────────────────┤
│                    HTTP/REST API Layer                      │
│              (CORS enabled for localhost:3000)              │
├─────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                         │
│         (localhost:8000 - Uvicorn Development Server)       │
├─────────────────────────────────────────────────────────────┤
│                    SQLAlchemy ORM                           │
├─────────────────────────────────────────────────────────────┤
│                   SQLite Database                           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
stock_-Simulator_-Predictor/
│
├── Backend/                          # FastAPI Backend
│   ├── main.py                      # FastAPI application entry point
│   ├── database.py                  # SQLAlchemy setup & database engine
│   ├── models/                      # Database ORM models
│   │   ├── __init__.py
│   │   ├── auth.py                  # User model & password utilities
│   │   └── trading.py               # Portfolio & TransactionHistory models
│   ├── routers/                     # API endpoint routes
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication endpoints
│   │   └── trading.py               # Trading endpoints
│   └── venv/                        # Python virtual environment
│
└── frontend/                        # React Frontend
    ├── package.json                 # Node.js dependencies
    ├── public/                      # Static assets
    │   ├── index.html
    │   ├── manifest.json
    │   └── robots.txt
    ├── src/                         # React source code
    │   ├── App.js                   # Main React component
    │   ├── index.js                 # Entry point
    │   ├── components/              # Reusable UI components
    │   │   └── Antigravity.js       # 3D visualization component
    │   ├── pages/                   # Page components
    │   │   ├── LandingPage.js       # Home page
    │   │   ├── Login.js             # Authentication page
    │   │   ├── TradingDesk.js       # Stock trading interface
    │   │   ├── Ai_model.js          # AI predictions page
    │   │   └── NewsFeed.js          # News feed page
    │   └── styles/                  # CSS stylesheets
    │       ├── global.css           # Global styles
    │       ├── landing.css
    │       ├── trading.css
    │       ├── ai.css
    │       └── news.css
    └── node_modules/                # Node.js dependencies
```

## 🛠️ Technologies Used

### Backend
- **Framework**: FastAPI 0.100+
- **Server**: Uvicorn (ASGI)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Bcrypt password hashing
- **External APIs**: yfinance (stock data)
- **CORS**: Enabled for frontend integration

### Frontend
- **Library**: React 19.2.6
- **3D Graphics**: Three.js 0.184.0 with @react-three/fiber
- **Icons**: React Icons 5.6.0
- **Build Tool**: React Scripts 5.0.1
- **Package Manager**: npm

## 📋 Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** & **npm** (for frontend)
- **Windows, macOS, or Linux**

## 🚀 Installation & Setup

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
   pip install fastapi uvicorn sqlalchemy bcrypt yfinance
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

## ▶️ Running the Application

### Start the Backend

1. **Activate Python virtual environment**:
   ```bash
   cd Backend
   venv\Scripts\activate
   ```

2. **Start the Uvicorn server**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The backend will be available at: **http://localhost:8000**

   **Interactive API docs**: http://localhost:8000/docs

### Start the Frontend

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

## 📡 API Documentation

### Available at: `http://localhost:8000/docs` (Swagger UI)

### Key Endpoints

#### Authentication
- `POST /auth/register` - Create a new user account
- `POST /auth/login` - Authenticate user (returns credentials)
- `GET /auth/profile` - Get current user profile

#### Trading
- `GET /trading/portfolio` - Get user's stock holdings
- `GET /trading/history` - Get transaction history
- `POST /trading/buy` - Execute a buy order
- `POST /trading/sell` - Execute a sell order
- `GET /trading/quote/<ticker>` - Get current stock price

#### General
- `GET /` - Server status endpoint

## ✨ Features

### User Authentication
- Secure user registration with bcrypt password hashing
- Login system with session management
- Starting virtual balance of $100,000 for paper trading

### Trading Functionality
- **Buy stocks**: Purchase shares with virtual currency
- **Sell stocks**: Liquidate positions at current market prices
- **Portfolio tracking**: Monitor holdings and average buy prices
- **Transaction history**: Complete audit trail of all trades

### Data Integration
- Real-time stock data via **yfinance**
- Support for any publicly traded ticker symbol
- Historical price tracking and analysis

### UI/UX Features
- **3D Visualizations**: Antigravity component for immersive experience
- **Multiple pages**: Landing page, login, trading desk, AI models, news feed
- **Responsive design**: Global CSS styling system
- **React component architecture**: Modular and maintainable code

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
└── average_buy_price
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
└── timestamp
```

## 🔒 Security Notes

- Passwords are hashed using bcrypt before storage
- CORS is configured to accept requests only from `http://localhost:3000`
- Database uses foreign keys to maintain referential integrity
- SQLAlchemy provides SQL injection protection

## 📝 Development Tips

### Backend Development
- API automatically reloads on file changes (with `--reload`)
- Use Swagger UI at `/docs` for testing endpoints
- Check SQLite database in backend folder for data persistence

### Frontend Development
- Hot reload enabled for React changes
- Browser opens automatically on `npm start`
- Check browser DevTools for debugging

## 🐛 Troubleshooting

**Port already in use**:
- Backend: Change port in uvicorn command: `--port 8001`
- Frontend: Set PORT env variable: `PORT=3001 npm start`

**CORS errors**:
- Ensure backend is running on `http://localhost:8000`
- Check that frontend is running on `http://localhost:3000`

**Database errors**:
- Delete `.db` files in backend to reset database
- Ensure models are imported before `Base.metadata.create_all()`

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [React Documentation](https://react.dev/)
- [Three.js Guide](https://threejs.org/docs/)
- [yfinance Library](https://github.com/ranaroussi/yfinance)

---

**Happy Trading! 📈**
