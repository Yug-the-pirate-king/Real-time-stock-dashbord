from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from core.db import get_db, SessionLocal
from core.config import get_settings
from core.logging import get_logger
from models.auth import User
from models.trading import Portfolio, TransactionHistory
from services.market_data import get_provider, COUNTRY_FLAGS, YFinanceProvider

router = APIRouter(prefix="/trade", tags=["Trading Operations"])
logger = get_logger(__name__)
settings = get_settings()
provider = get_provider()


def _format_change(change_pct: Optional[float]) -> str:
    if change_pct is None:
        return "0.00%"
    return f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"


def _quote_to_market_row(quote, ui_data: dict) -> dict:
    return {
        "ticker": quote.ticker,
        "name": quote.name or ui_data.get("name", quote.ticker),
        "price": round(quote.price, 2),
        "icon": ui_data.get("icon", quote.flag),
        "category": ui_data.get("category", quote.sector or "Equity"),
        "change": _format_change(quote.change_pct),
        "currency": quote.currency,
        "country": quote.country,
        "flag": quote.flag,
        "exchange": quote.exchange,
    }


# ==========================================
# 1. BUY ENGINE
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

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    user = db.query(User).filter(User.id == user_big_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    quote = provider.get_quote(ticker)
    if quote is None:
        raise HTTPException(status_code=400, detail=f"Market data unavailable for {ticker}")

    current_price_native = quote.price / YFinanceProvider.get_exchange_rate(quote.currency, "USD")
    current_price_usd = quote.price
    rate_used = YFinanceProvider.get_exchange_rate(quote.currency, "USD")

    total_cost_usd = current_price_usd * quantity
    if user.balance < total_cost_usd:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Cost: ${round(total_cost_usd, 2)}, Balance: ${round(user.balance, 2)}"
        )

    user.balance -= total_cost_usd

    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == user_big_id,
        Portfolio.ticker == ticker
    ).first()

    if portfolio_item:
        new_total_shares = portfolio_item.shares_owned + quantity
        new_total_cost_usd = (portfolio_item.shares_owned * portfolio_item.average_buy_price) + total_cost_usd
        portfolio_item.average_buy_price = new_total_cost_usd / new_total_shares
        portfolio_item.shares_owned = new_total_shares
        portfolio_item.total_cost_basis_usd = new_total_cost_usd

        old_orig_cost = (portfolio_item.original_avg_buy_price or 0.0) * (new_total_shares - quantity)
        new_orig_cost = current_price_native * quantity
        portfolio_item.original_avg_buy_price = (old_orig_cost + new_orig_cost) / new_total_shares
        portfolio_item.last_exchange_rate = rate_used
        portfolio_item.exchange = quote.exchange
        portfolio_item.currency = quote.currency
        portfolio_item.country = quote.country
        portfolio_item.sector = quote.sector
        portfolio_item.industry = quote.industry
    else:
        new_holding = Portfolio(
            user_id=user_big_id,
            ticker=ticker,
            shares_owned=quantity,
            average_buy_price=current_price_usd,
            currency=quote.currency,
            country=quote.country,
            exchange=quote.exchange,
            original_avg_buy_price=current_price_native,
            last_exchange_rate=rate_used,
            total_cost_basis_usd=total_cost_usd,
            sector=quote.sector,
            industry=quote.industry,
        )
        db.add(new_holding)

    history_log = TransactionHistory(
        user_id=user_big_id,
        ticker=ticker,
        action="BUY",
        shares=quantity,
        price_per_share=current_price_usd,
        currency=quote.currency,
        country=quote.country,
        exchange=quote.exchange,
        original_price_per_share=current_price_native,
        exchange_rate_used=rate_used,
        total_value_usd=total_cost_usd,
    )
    db.add(history_log)

    db.commit()
    return {
        "message": f"Successfully bought {quantity} shares of {ticker}!",
        "new_balance": round(user.balance, 2),
        "currency": quote.currency,
        "country": quote.country,
        "price_usd": round(current_price_usd, 2),
        "price_native": round(current_price_native, 2),
    }


# ==========================================
# 2. SELL ENGINE
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

    ticker = ticker.upper().strip()
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero.")

    user = db.query(User).filter(User.id == user_big_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    portfolio_item = db.query(Portfolio).filter(
        Portfolio.user_id == user_big_id,
        Portfolio.ticker == ticker
    ).first()
    if not portfolio_item or portfolio_item.shares_owned < quantity:
        current_holdings = portfolio_item.shares_owned if portfolio_item else 0.0
        raise HTTPException(
            status_code=400,
            detail=f"You don't own enough shares of {ticker}. Trying to sell: {quantity}, You own: {round(current_holdings, 4)}"
        )

    quote = provider.get_quote(ticker)
    if quote is None:
        raise HTTPException(status_code=400, detail=f"Market data unavailable for {ticker}")

    current_price_native = quote.price / YFinanceProvider.get_exchange_rate(quote.currency, "USD")
    current_price_usd = quote.price
    rate_used = YFinanceProvider.get_exchange_rate(quote.currency, "USD")

    total_revenue_usd = current_price_usd * quantity
    user.balance += total_revenue_usd

    portfolio_item.shares_owned -= quantity
    if portfolio_item.shares_owned > 0:
        sold_ratio = quantity / (portfolio_item.shares_owned + quantity)
        portfolio_item.total_cost_basis_usd -= portfolio_item.total_cost_basis_usd * sold_ratio
        portfolio_item.average_buy_price = portfolio_item.total_cost_basis_usd / portfolio_item.shares_owned
    else:
        portfolio_item.total_cost_basis_usd = 0.0
        portfolio_item.average_buy_price = 0.0

    if portfolio_item.shares_owned <= 0.0001:
        db.delete(portfolio_item)

    history_log = TransactionHistory(
        user_id=user_big_id,
        ticker=ticker,
        action="SELL",
        shares=quantity,
        price_per_share=current_price_usd,
        currency=quote.currency,
        country=quote.country,
        exchange=quote.exchange,
        original_price_per_share=current_price_native,
        exchange_rate_used=rate_used,
        total_value_usd=total_revenue_usd,
    )
    db.add(history_log)

    db.commit()
    return {
        "message": f"Successfully sold {quantity} shares of {ticker}!",
        "new_balance": round(user.balance, 2),
        "currency": quote.currency,
        "country": quote.country,
        "price_usd": round(current_price_usd, 2),
        "price_native": round(current_price_native, 2),
    }


# ==========================================
# 3. PORTFOLIO & HISTORY
# ==========================================
@router.get("/portfolio/{user_id}")
def get_user_portfolio(user_id: str, db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer sequence.")

    items = db.query(Portfolio).filter(Portfolio.user_id == user_big_id).all()
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "ticker": item.ticker,
            "shares_owned": item.shares_owned,
            "average_buy_price": item.average_buy_price,
            "currency": item.currency or "USD",
            "country": item.country or "US",
            "original_avg_buy_price": item.original_avg_buy_price or item.average_buy_price,
            "last_exchange_rate": item.last_exchange_rate or 1.0,
            "total_cost_basis_usd": item.total_cost_basis_usd or (item.shares_owned * item.average_buy_price),
            "exchange": item.exchange or "Unknown",
            "sector": item.sector,
            "industry": item.industry,
        })
    return result


@router.get("/history/{user_id}")
def get_user_history(user_id: str, db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer sequence.")

    items = db.query(TransactionHistory).filter(
        TransactionHistory.user_id == user_big_id
    ).order_by(TransactionHistory.timestamp.desc()).all()

    result = []
    for item in items:
        result.append({
            "id": item.id,
            "ticker": item.ticker,
            "action": item.action,
            "shares": item.shares,
            "price_per_share": item.price_per_share,
            "currency": item.currency or "USD",
            "country": item.country or "US",
            "original_price_per_share": item.original_price_per_share or item.price_per_share,
            "exchange_rate_used": item.exchange_rate_used or 1.0,
            "total_value_usd": item.total_value_usd or (item.shares * item.price_per_share),
            "exchange": item.exchange or "Unknown",
            "timestamp": item.timestamp.isoformat() if item.timestamp else None,
        })
    return result


# ==========================================
# 4. MARKET DATA & WATCHLIST
# ==========================================
WATCHLIST = {
    "AAPL": {"name": "Apple Inc.", "icon": "🍎", "category": "Technology", "country": "US"},
    "MSFT": {"name": "Microsoft Corp", "icon": "🪟", "category": "Technology", "country": "US"},
    "TSLA": {"name": "Tesla Inc.", "icon": "🚗", "category": "Automotive", "country": "US"},
    "NVDA": {"name": "Nvidia Corp", "icon": "💻", "category": "Semiconductors", "country": "US"},
    "SPY":  {"name": "S&P 500 ETF", "icon": "📈", "category": "Index", "country": "US"},
    "RELIANCE.NS": {"name": "Reliance Industries", "icon": "⛽", "category": "Energy", "country": "IN"},
    "TCS.NS": {"name": "Tata Consultancy", "icon": "💼", "category": "Technology", "country": "IN"},
    "SAP.DE": {"name": "SAP SE", "icon": "🌐", "category": "Technology", "country": "DE"},
    "SONY": {"name": "Sony Group", "icon": "🎮", "category": "Consumer", "country": "JP"},
    "BABA": {"name": "Alibaba Group", "icon": "🛒", "category": "E-Commerce", "country": "CN"},
}


@router.get("/market")
def get_real_market_data():
    """Returns live prices for the default global watchlist."""
    market_data = []
    for ticker_symbol, ui_data in WATCHLIST.items():
        try:
            quote = provider.get_quote(ticker_symbol)
            if quote is None:
                continue
            market_data.append(_quote_to_market_row(quote, ui_data))
        except Exception as e:
            logger.warning(f"Failed to fetch {ticker_symbol}: {e}")
    return market_data


# ==========================================
# 5. SEARCH ENGINE
# ==========================================
@router.get("/search")
def search_global_stocks(query: str = Query(..., min_length=1)):
    """Searches Yahoo Finance with caching."""
    try:
        results = provider.search(query, limit=8)
        return [
            {
                "ticker": r.ticker,
                "name": r.name,
                "price": round(r.price, 2),
                "exchange": r.exchange,
                "type": r.type,
                "icon": r.flag,
                "category": r.sector or r.exchange,
                "change": _format_change(r.change_pct),
                "currency": r.currency,
                "country": r.country,
                "flag": r.flag,
            }
            for r in results
        ]
    except Exception as e:
        logger.warning(f"Search failed for '{query}': {e}")
        return []


# ==========================================
# 6. PORTFOLIO LIVE PRICES
# ==========================================
@router.get("/portfolio-prices/{user_id}")
def get_portfolio_live_prices(user_id: str, db: Session = Depends(get_db)):
    """Fetch live prices for all stocks in user's portfolio."""
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be a valid integer.")

    portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user_big_id).all()
    if not portfolio_items:
        return []

    portfolio_prices = []
    for item in portfolio_items:
        try:
            quote = provider.get_quote(item.ticker)
            if quote is None:
                raise ValueError("No quote")

            portfolio_prices.append({
                "ticker": item.ticker,
                "price": round(quote.price, 2),
                "change": _format_change(quote.change_pct),
                "shares_owned": item.shares_owned,
                "average_buy_price": round(item.average_buy_price, 2),
                "currency": quote.currency,
                "country": quote.country,
                "flag": quote.flag,
                "exchange": quote.exchange,
            })
        except Exception as e:
            logger.warning(f"Failed to fetch price for {item.ticker}: {e}")
            portfolio_prices.append({
                "ticker": item.ticker,
                "price": round(item.average_buy_price, 2),
                "change": "0.00%",
                "shares_owned": item.shares_owned,
                "average_buy_price": round(item.average_buy_price, 2),
                "currency": item.currency or "USD",
                "country": item.country or "US",
                "flag": COUNTRY_FLAGS.get(item.country or "US", "🌍"),
                "exchange": item.exchange or "Unknown",
            })

    return portfolio_prices


# ==========================================
# 7. SINGLE STOCK PRICE
# ==========================================
@router.get("/price/{ticker}")
def get_single_price(ticker: str):
    """Quick endpoint for a single ticker's live USD price and metadata."""
    quote = provider.get_quote(ticker)
    if quote is None:
        raise HTTPException(status_code=404, detail="Ticker not found or no data.")

    native = quote.price / YFinanceProvider.get_exchange_rate(quote.currency, "USD") if quote.currency != "USD" else quote.price
    return {
        "ticker": quote.ticker,
        "price_native": round(native, 4),
        "price_usd": round(quote.price, 4),
        "currency": quote.currency,
        "country": quote.country,
        "flag": quote.flag,
        "name": quote.name,
        "exchange": quote.exchange,
    }


# ==========================================
# 7b. STOCK METRICS
# ==========================================
@router.get("/metrics/{ticker}")
def get_stock_metrics(ticker: str):
    """Returns key financial metrics for a ticker."""
    try:
        info = provider.enrich_info(ticker)
        quote = provider.get_quote(ticker)

        def fmt(val, div=1):
            if val is None:
                return None
            try:
                v = float(val) / div
                if abs(v) >= 1_000_000_000:
                    return f"{v/1_000_000_000:.2f}B"
                if abs(v) >= 1_000_000:
                    return f"{v/1_000_000:.2f}M"
                if abs(v) >= 1_000:
                    return f"{v/1_000:.2f}K"
                return f"{v:.2f}"
            except Exception:
                return None

        current_price = quote.price if quote else None

        metrics = {
            "ticker": ticker.upper(),
            "name": info.get("name"),
            "currency": info.get("currency", "USD"),
            "country": info.get("country", "US"),
            "flag": info.get("flag", "🌍"),
            "exchange": info.get("exchange", "Unknown"),
            "sector": info.get("sector") or "Unknown",
            "industry": info.get("industry"),
            "price_native": round(current_price / YFinanceProvider.get_exchange_rate(info.get("currency", "USD"), "USD"), 2) if current_price else None,
            "price_usd": round(current_price, 2) if current_price else None,
            "market_cap": fmt(info.get("market_cap")),
            "market_cap_raw": info.get("market_cap"),
            "pe_trailing": round(info["pe_trailing"], 2) if info.get("pe_trailing") else None,
            "pe_forward": round(info["pe_forward"], 2) if info.get("pe_forward") else None,
            "eps": round(info["eps"], 2) if info.get("eps") else None,
            "dividend_yield": round(info["dividend_yield"] * 100, 2) if info.get("dividend_yield") else None,
            "volume": fmt(info.get("volume")),
            "volume_raw": info.get("volume"),
            "avg_volume": fmt(info.get("avg_volume")),
            "day_high": round(info["day_high"], 2) if info.get("day_high") else None,
            "day_low": round(info["day_low"], 2) if info.get("day_low") else None,
            "fifty_two_week_high": round(info["fifty_two_week_high"], 2) if info.get("fifty_two_week_high") else None,
            "fifty_two_week_low": round(info["fifty_two_week_low"], 2) if info.get("fifty_two_week_low") else None,
            "beta": round(info["beta"], 2) if info.get("beta") else None,
        }
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Metrics unavailable for {ticker}: {e}")


# ==========================================
# 8. STOCK HISTORY SPARKLINE
# ==========================================
@router.get("/history-data/{ticker}")
def get_stock_history(ticker: str, period: str = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y)$")):
    """Returns historical closing prices for sparkline/chart rendering."""
    result = provider.get_history(ticker, period)
    if result is None:
        raise HTTPException(status_code=404, detail="No historical data.")
    # Round for smaller payload
    result["prices_native"] = [round(p, 2) for p in result["prices_native"]]
    result["prices_usd"] = [round(p, 2) for p in result["prices_usd"]]
    return result
