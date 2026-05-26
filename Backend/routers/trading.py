from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import BigInteger
from sqlalchemy.orm import Session
import yfinance as yf
import requests
from cachetools import TTLCache, cached
import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()

# Import the shared database connector and your structural model blueprints
from database import SessionLocal
from models.auth import User
from models.trading import Portfolio, TransactionHistory

# Define the router ONCE
router = APIRouter(prefix="/trade", tags=["Trading Operations"])

# Exchange Rate API configuration
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")
EXCHANGE_RATE_API_URL = "https://v6.exchangerate-api.com/v6/{key}/latest"

# Global caches to prevent rate limiting and optimize performance
query_cache = TTLCache(maxsize=500, ttl=60) 
price_cache = TTLCache(maxsize=1000, ttl=30)
market_cache = TTLCache(maxsize=1, ttl=30) # Caches the watchlist dashboard for 30 seconds
exchange_rate_cache = TTLCache(maxsize=50, ttl=3600)  # Cache exchange rates for 1 hour

# ==========================================
# CURRENCY DETECTION & CONVERSION
# ==========================================

def detect_currency_from_ticker(ticker: str) -> str:
    """Detect currency based on ticker suffix/exchange"""
    ticker = ticker.upper()
    
    # Indian exchanges
    if ticker.endswith(('.NS', '.BO')):
        return 'INR'
    # Canadian exchange
    elif ticker.endswith('.TO'):
        return 'CAD'
    # London exchange
    elif ticker.endswith('.L'):
        return 'GBP'
    # Tokyo exchange
    elif ticker.endswith('.T'):
        return 'JPY'
    # Hong Kong exchange
    elif ticker.endswith('.HK'):
        return 'HKD'
    # Shanghai/Shenzhen
    elif ticker.endswith(('.SS', '.SZ')):
        return 'CNY'
    # Australia
    elif ticker.endswith('.AX'):
        return 'AUD'
    # Singapore
    elif ticker.endswith('.SI'):
        return 'SGD'
    # Mexico
    elif ticker.endswith('.MX'):
        return 'MXN'
    # Brazil
    elif ticker.endswith('.SA'):
        return 'BRL'
    # Default to USD for US exchanges
    else:
        return 'USD'

def get_exchange_rate(from_currency: str, to_currency: str = 'USD') -> float:
    """Fetch exchange rate with caching"""
    if from_currency == to_currency:
        return 1.0
    
    cache_key = f"{from_currency}_{to_currency}"
    
    # Check cache first
    if cache_key in exchange_rate_cache:
        return exchange_rate_cache[cache_key]
    
    if not EXCHANGE_RATE_API_KEY:
        print(f"Warning: EXCHANGE_RATE_API_KEY not set. Using 1:1 conversion for {from_currency} to {to_currency}")
        return 1.0
    
    try:
        url = EXCHANGE_RATE_API_URL.format(key=EXCHANGE_RATE_API_KEY)
        params = {'base': from_currency}
        response = requests.get(url + f"/{from_currency}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'conversion_rates' in data:
                rate = data['conversion_rates'].get(to_currency, 1.0)
                exchange_rate_cache[cache_key] = rate
                return rate
    except Exception as e:
        print(f"Error fetching exchange rate for {from_currency}/{to_currency}: {e}")
    
    return 1.0

def convert_to_usd(price: float, ticker: str) -> float:
    """Convert price to USD based on ticker's currency"""
    currency = detect_currency_from_ticker(ticker)
    if currency == 'USD':
        return price
    
    rate = get_exchange_rate(currency, 'USD')
    return price * rate

# Database connection helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 1. THE BUY ENGINE
# ==========================================
@router.post("/buy")
def buy_stock(
    user_id: str = Query(...), 
    ticker: str = Query(...), 
    quantity: float = Query(...), 
    db: Session = Depends(get_db)
):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer.")
    
    ticker = ticker.upper()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_big_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Fetch live stock market price
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if data.empty:
        raise HTTPException(status_code=400, detail=f"Invalid ticker symbol: {ticker}")
        
    # FIXED: Explicitly cast to native standard Python float to prevent NumPy schema compilation errors
    current_price = float(data['Close'].iloc[-1])
    
    # Convert to USD if stock is from another country
    current_price = convert_to_usd(current_price, ticker)
    
    # Financial math check
    total_cost = current_price * quantity
    if user.balance < total_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Cost: ${round(total_cost, 2)}, Balance: ${round(user.balance, 2)}")
        
    # Deduct cash from user's wallet balance
    user.balance -= total_cost
    
    # Update portfolio holdings
    portfolio_item = db.query(Portfolio).filter(Portfolio.user_id == user_big_id, Portfolio.ticker == ticker).first()
    if portfolio_item:
        # User already owns this stock -> Calculate new average buy price
        new_total_shares = portfolio_item.shares_owned + quantity
        total_investment = (portfolio_item.shares_owned * portfolio_item.average_buy_price) + total_cost
        portfolio_item.average_buy_price = total_investment / new_total_shares
        portfolio_item.shares_owned = new_total_shares
    else:
        # Brand new ticker holding for this user
        new_holding = Portfolio(user_id=user_big_id, ticker=ticker, shares_owned=quantity, average_buy_price=current_price)
        db.add(new_holding)
        
    # Write a permanent receipt to the ledger with automatic timestamp
    history_log = TransactionHistory(user_id=user_big_id, ticker=ticker, action="BUY", shares=quantity, price_per_share=current_price)
    db.add(history_log)
    
    db.commit()
    return {"message": f"Successfully bought {quantity} shares of {ticker}!", "new_balance": round(user.balance, 2)}


# ==========================================
# 2. THE SELL ENGINE
# ==========================================
@router.post("/sell")
def sell_stock(
    user_id: str = Query(...), 
    ticker: str = Query(...), 
    quantity: float = Query(...), 
    db: Session = Depends(get_db)
):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer.")
    
    ticker = ticker.upper()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_big_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Check if the user even owns this stock ticker
    portfolio_item = db.query(Portfolio).filter(Portfolio.user_id == user_big_id, Portfolio.ticker == ticker).first()
    if not portfolio_item or portfolio_item.shares_owned < quantity:
        current_holdings = portfolio_item.shares_owned if portfolio_item else 0.0
        raise HTTPException(status_code=400, detail=f"You don't own enough shares of {ticker}. Trying to sell: {quantity}, You own: {current_holdings}")
        
    # Fetch live stock market price to cash out at
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if data.empty:
        raise HTTPException(status_code=400, detail="Error fetching market price.")
        
    # FIXED: Explicitly cast to native standard Python float to prevent NumPy schema compilation errors
    current_price = float(data['Close'].iloc[-1])
    
    # Convert to USD if stock is from another country
    current_price = convert_to_usd(current_price, ticker)
    
    # Financial math calculation
    total_revenue = current_price * quantity
    
    # Add cash back into user's wallet balance
    user.balance += total_revenue
    
    # Deduct shares from portfolio holdings
    portfolio_item.shares_owned -= quantity
    
    # Clean up optimization: If they sold 100% of their shares, remove the row entirely
    if portfolio_item.shares_owned == 0:
        db.delete(portfolio_item)
        
    # Write a permanent receipt to the ledger with automatic timestamp
    history_log = TransactionHistory(user_id=user_big_id, ticker=ticker, action="SELL", shares=quantity, price_per_share=current_price)
    db.add(history_log)
    
    db.commit()
    return {"message": f"Successfully sold {quantity} shares of {ticker}!", "new_balance": round(user.balance, 2)}


# ==========================================
# 3. THE UTILITY GETTERS (For Frontend Display)
# ==========================================
@router.get("/portfolio/{user_id}")
def get_user_portfolio(user_id: str, db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer sequence.")
        
    return db.query(Portfolio).filter(Portfolio.user_id == user_big_id).all()


@router.get("/history/{user_id}")
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer sequence.")
        
    return db.query(TransactionHistory).filter(TransactionHistory.user_id == user_big_id).order_by(TransactionHistory.timestamp.desc()).all()


# ==========================================
# 4. MARKET DATA & GLOBAL WATCHLIST
# ==========================================
WATCHLIST = {
    "AAPL": {"name": "Apple Inc.", "icon": "🍎", "category": "Technology"},
    "MSFT": {"name": "Microsoft Corp", "icon": "🪟", "category": "Technology"},
    "TSLA": {"name": "Tesla Inc.", "icon": "🚗", "category": "Automotive"},
    "NVDA": {"name": "Nvidia Corp", "icon": "💻", "category": "Semiconductors"},
    "SPY":  {"name": "S&P 500 ETF", "icon": "📈", "category": "Index"}
}

@router.get("/market")
@cached(cache=market_cache) # Added: Prevents multiple quick refreshes from rate-limiting your app
def get_real_market_data():
    """Returns live prices for the default watchlist."""
    market_data = []
    tickers_string = " ".join(WATCHLIST.keys())
    yf_tickers = yf.Tickers(tickers_string)
    
    for ticker_symbol, ui_data in WATCHLIST.items():
        try:
            ticker_obj = yf_tickers.tickers[ticker_symbol]
            fast_info = ticker_obj.fast_info
            
            current_price = fast_info.last_price
            # Convert to USD if stock is from another country
            current_price = convert_to_usd(current_price, ticker_symbol)
            prev_close = fast_info.previous_close
            # Also convert prev_close for accurate percentage change
            if prev_close:
                prev_close = convert_to_usd(prev_close, ticker_symbol)
            
            if prev_close and prev_close > 0:
                change_percent = ((current_price - prev_close) / prev_close) * 100
                change_str = f"+{change_percent:.2f}%" if change_percent >= 0 else f"{change_percent:.2f}%"
            else:
                change_str = "0.00%"
            
            market_data.append({
                "ticker": ticker_symbol,
                "name": ui_data["name"],
                "price": round(current_price, 2),
                "icon": ui_data["icon"],
                "category": ui_data["category"],
                "change": change_str
            })
        except Exception as e:
            print(f"Failed to fetch {ticker_symbol}: {e}")
            
    return market_data


# ==========================================
# 5. SEARCH ENGINE
# ==========================================
def fetch_price_data(quote):
    """Helper function to process a single ticker."""
    ticker_symbol = quote['symbol']
    if ticker_symbol in price_cache:
        return price_cache[ticker_symbol]
        
    try:
        ticker_obj = yf.Ticker(ticker_symbol)
        fast_info = ticker_obj.fast_info
        
        current_price = getattr(fast_info, 'last_price', None)
        prev_close = getattr(fast_info, 'previous_close', None)
        
        if not current_price:
            return None
        
        # Convert to USD if stock is from another country
        current_price = convert_to_usd(current_price, ticker_symbol)
        if prev_close:
            prev_close = convert_to_usd(prev_close, ticker_symbol)
            
        change_str = "0.00%"
        if prev_close and prev_close > 0:
            change_percent = ((current_price - prev_close) / prev_close) * 100
            change_str = f"+{change_percent:.2f}%" if change_percent >= 0 else f"{change_percent:.2f}%"
            
        exchange = quote.get('exchange', 'Unknown')
        icon = "🇮🇳" if ticker_symbol.endswith(('.NS', '.BO')) else "🌍"
        
        result = {
            "ticker": ticker_symbol,
            "name": quote.get('shortname', ticker_symbol),
            "price": round(current_price, 2),
            "exchange": exchange,
            "type": quote.get('quoteType', 'Stock'),
            "icon": icon,
            "category": exchange, 
            "change": change_str
        }
        
        price_cache[ticker_symbol] = result
        return result
        
    except Exception as e:
        print(f"Skipping {ticker_symbol}: {e}")
        return None

@router.get("/search")
@cached(cache=query_cache) 
def search_global_stocks(query: str = Query(..., min_length=3)):
    """Searches Yahoo Finance with caching and parallel processing."""
    try:
        search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=5) 
        
        if response.status_code != 200:
            return []
            
        quotes = [q for q in response.json().get('quotes', []) if q.get('quoteType') in ['EQUITY', 'ETF']]
        live_results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(fetch_price_data, quotes)
            for res in results:
                if res:
                    live_results.append(res)
                    
        return live_results

    except Exception as e:
        print(f"Search failed for '{query}': {e}")
        return []