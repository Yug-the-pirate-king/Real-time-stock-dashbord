from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import yfinance as yf

# Import the shared database connector and your structural model blueprints
from database import SessionLocal
from models.auth import User
from models.trading import Portfolio, TransactionHistory

router = APIRouter(prefix="/trade", tags=["Trading Operations"])

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
def buy_stock(user_id: int, ticker: str, quantity: float, db: Session = Depends(get_db)):
    ticker = ticker.upper()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Fetch live stock market price
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if data.empty:
        raise HTTPException(status_code=400, detail=f"Invalid ticker symbol: {ticker}")
    current_price = data['Close'].iloc[-1]
    
    # Financial math check
    total_cost = current_price * quantity
    if user.balance < total_cost:
        raise HTTPException(status_code=400, detail=f"Insufficient funds. Cost: ${round(total_cost, 2)}, Balance: ${round(user.balance, 2)}")
        
    # Deduct cash from user's wallet balance
    user.balance -= total_cost
    
    # Update portfolio holdings
    portfolio_item = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.ticker == ticker).first()
    if portfolio_item:
        # User already owns this stock -> Calculate new average buy price
        new_total_shares = portfolio_item.shares_owned + quantity
        total_investment = (portfolio_item.shares_owned * portfolio_item.average_buy_price) + total_cost
        portfolio_item.average_buy_price = total_investment / new_total_shares
        portfolio_item.shares_owned = new_total_shares
    else:
        # Brand new ticker holding for this user
        new_holding = Portfolio(user_id=user_id, ticker=ticker, shares_owned=quantity, average_buy_price=current_price)
        db.add(new_holding)
        
    # Write a permanent receipt to the ledger with automatic timestamp
    history_log = TransactionHistory(user_id=user_id, ticker=ticker, action="BUY", shares=quantity, price_per_share=current_price)
    db.add(history_log)
    
    db.commit()
    return {"message": f"Successfully bought {quantity} shares of {ticker}!", "new_balance": round(user.balance, 2)}


# ==========================================
# 2. THE SELL ENGINE
# ==========================================
@router.post("/sell")
def sell_stock(user_id: int, ticker: str, quantity: float, db: Session = Depends(get_db)):
    ticker = ticker.upper()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    # Check if the user even owns this stock ticker
    portfolio_item = db.query(Portfolio).filter(Portfolio.user_id == user_id, Portfolio.ticker == ticker).first()
    if not portfolio_item or portfolio_item.shares_owned < quantity:
        current_holdings = portfolio_item.shares_owned if portfolio_item else 0.0
        raise HTTPException(status_code=400, detail=f"You don't own enough shares of {ticker}. Trying to sell: {quantity}, You own: {current_holdings}")
        
    # Fetch live stock market price to cash out at
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if data.empty:
        raise HTTPException(status_code=400, detail="Error fetching market price.")
    current_price = data['Close'].iloc[-1]
    
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
    history_log = TransactionHistory(user_id=user_id, ticker=ticker, action="SELL", shares=quantity, price_per_share=current_price)
    db.add(history_log)
    
    db.commit()
    return {"message": f"Successfully sold {quantity} shares of {ticker}!", "new_balance": round(user.balance, 2)}


# ==========================================
# 3. THE UTILITY GETTERS (For Frontend Display)
# ==========================================
@router.get("/portfolio/{user_id}")
def get_user_portfolio(user_id: int, db: Session = Depends(get_db)):
    return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

@router.get("/history/{user_id}")
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    return db.query(TransactionHistory).filter(TransactionHistory.user_id == user_id).order_by(TransactionHistory.timestamp.desc()).all()