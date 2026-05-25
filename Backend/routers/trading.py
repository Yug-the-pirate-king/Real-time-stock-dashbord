from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import BigInteger
from sqlalchemy.orm import Session
import yfinance as yf
import requests
from cachetools import TTLCache, cached
import concurrent.futures

# Import the shared database connector and your structural model blueprints
from database import SessionLocal
from models.auth import User
from models.trading import Portfolio, TransactionHistory

# Define the router ONCE
router = APIRouter(prefix="/trade", tags=["Trading Operations"])

# Global caches to prevent rate limiting and optimize performance
query_cache = TTLCache(maxsize=500, ttl=60) 
price_cache = TTLCache(maxsize=1000, ttl=30)
market_cache = TTLCache(maxsize=1, ttl=30) # Caches the watchlist dashboard for 30 seconds

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
            prev_close = fast_info.previous_close
            
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