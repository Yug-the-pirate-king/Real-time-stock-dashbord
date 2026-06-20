from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import yfinance as yf
import requests
from cachetools import TTLCache, cached
import concurrent.futures
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

from database import SessionLocal
from models.auth import User
from models.trading import Portfolio, TransactionHistory

router = APIRouter(prefix="/trade", tags=["Trading Operations"])

EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY", "")
EXCHANGE_RATE_API_URL = "https://v6.exchangerate-api.com/v6/{key}/latest/{from_currency}"
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d87v551r01qmhakhgmd0d87v551r01qmhakhgmdg")

# Global caches
query_cache = TTLCache(maxsize=500, ttl=60)
price_cache = TTLCache(maxsize=1000, ttl=30)
market_cache = TTLCache(maxsize=1, ttl=30)
exchange_rate_cache = TTLCache(maxsize=50, ttl=3600)
stock_info_cache = TTLCache(maxsize=200, ttl=300)

# ==========================================
# COUNTRY & CURRENCY DETECTION
# ==========================================

TICKER_SUFFIX_MAP = {
    ".NS": ("INR", "IN"), ".BO": ("INR", "IN"),
    ".TO": ("CAD", "CA"), ".V": ("CAD", "CA"),
    ".L": ("GBP", "GB"),
    ".T": ("JPY", "JP"), ".TYO": ("JPY", "JP"),
    ".HK": ("HKD", "HK"),
    ".SS": ("CNY", "CN"), ".SZ": ("CNY", "CN"),
    ".AX": ("AUD", "AU"),
    ".SI": ("SGD", "SG"),
    ".MX": ("MXN", "MX"),
    ".SA": ("BRL", "BR"),
    ".F": ("EUR", "DE"), ".DE": ("EUR", "DE"),
    ".PA": ("EUR", "FR"), ".MC": ("EUR", "ES"),
    ".AS": ("EUR", "NL"), ".MI": ("EUR", "IT"),
    ".SW": ("CHF", "CH"), ".ST": ("SEK", "SE"),
    ".CO": ("DKK", "DK"), ".HE": ("EUR", "FI"),
    ".KS": ("KRW", "KR"), ".KQ": ("KRW", "KR"),
    ".TW": ("TWD", "TW"),
    ".JK": ("IDR", "ID"),
}

COUNTRY_FLAGS = {
    "US": "🇺🇸", "IN": "🇮🇳", "CA": "🇨🇦", "GB": "🇬🇧", "JP": "🇯🇵",
    "HK": "🇭🇰", "CN": "🇨🇳", "AU": "🇦🇺", "SG": "🇸🇬", "MX": "🇲🇽",
    "BR": "🇧🇷", "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸", "NL": "🇳🇱",
    "IT": "🇮🇹", "CH": "🇨🇭", "SE": "🇸🇪", "DK": "🇩🇰", "FI": "🇫🇮",
    "KR": "🇰🇷", "TW": "🇹🇼", "ID": "🇮🇩", "RU": "🇷🇺", "ZA": "🇿🇦",
}


def detect_currency_and_country(ticker: str) -> tuple[str, str]:
    """Detect (currency, country_code) from ticker suffix. Falls back to yfinance .info if ambiguous."""
    ticker_up = ticker.upper()
    for suffix, (curr, cc) in TICKER_SUFFIX_MAP.items():
        if ticker_up.endswith(suffix):
            return curr, cc
    return "USD", "US"


def enrich_stock_info(ticker: str) -> dict:
    """Fetch metadata from yfinance with caching. Returns dict with currency, country, sector, name."""
    cache_key = ticker.upper()
    if cache_key in stock_info_cache:
        return stock_info_cache[cache_key]

    detected_curr, detected_cc = detect_currency_and_country(ticker)
    info = {
        "currency": detected_curr,
        "country": detected_cc,
        "flag": COUNTRY_FLAGS.get(detected_cc, "🌍"),
        "name": ticker.upper(),
        "sector": "Unknown",
        "exchange": "Unknown",
        "type": "Stock",
    }

    try:
        t = yf.Ticker(ticker)
        fast_info = t.fast_info
        t_info = t.info or {}

        # Override with real data when available
        info["name"] = t_info.get("longName") or t_info.get("shortName") or fast_info.get("longName", ticker.upper())
        if "currency" in t_info and t_info["currency"]:
            info["currency"] = t_info["currency"]
        if "country" in t_info and t_info["country"]:
            info["country"] = t_info["country"]
        if "sector" in t_info:
            info["sector"] = t_info["sector"]
        if "exchange" in t_info:
            info["exchange"] = t_info["exchange"]
        if "quoteType" in t_info:
            info["type"] = t_info["quoteType"]

        # Financial metrics (best-effort; not all tickers have them)
        info["market_cap"] = t_info.get("marketCap")
        info["pe_trailing"] = t_info.get("trailingPE")
        info["pe_forward"] = t_info.get("forwardPE")
        info["dividend_yield"] = t_info.get("dividendYield")
        info["volume"] = t_info.get("volume") or t_info.get("regularMarketVolume")
        info["avg_volume"] = t_info.get("averageVolume")
        info["day_high"] = t_info.get("dayHigh") or t_info.get("regularMarketDayHigh")
        info["day_low"] = t_info.get("dayLow") or t_info.get("regularMarketDayLow")
        info["fifty_two_week_high"] = t_info.get("fiftyTwoWeekHigh")
        info["fifty_two_week_low"] = t_info.get("fiftyTwoWeekLow")
        info["beta"] = t_info.get("beta")
        info["eps"] = t_info.get("trailingEps")
        info["sector"] = t_info.get("sector") or info["sector"]
        info["industry"] = t_info.get("industry")

        info["flag"] = COUNTRY_FLAGS.get(info["country"], "🌍")
    except Exception as e:
        print(f"enrich_stock_info fallback for {ticker}: {e}")

    stock_info_cache[cache_key] = info
    return info


# ==========================================
# EXCHANGE RATES
# ==========================================

_hardcoded_fallback_rates = {
    "USD": 1.0, "INR": 0.012, "CAD": 0.74, "GBP": 1.27, "JPY": 0.0067,
    "HKD": 0.128, "CNY": 0.138, "AUD": 0.66, "SGD": 0.74, "MXN": 0.059,
    "BRL": 0.20, "EUR": 1.09, "CHF": 1.12, "SEK": 0.096, "DKK": 0.146,
    "KRW": 0.00076, "TWD": 0.031, "IDR": 0.000064, "RUB": 0.011, "ZAR": 0.053,
}


def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
    """Fetch exchange rate with caching and fallback layers."""
    from_c = from_currency.upper()
    to_c = to_currency.upper()

    if from_c == to_c:
        return 1.0

    cache_key = f"{from_c}_{to_c}"
    if cache_key in exchange_rate_cache:
        return exchange_rate_cache[cache_key]

    # Layer 1: ExchangeRate-API
    if EXCHANGE_RATE_API_KEY:
        try:
            url = EXCHANGE_RATE_API_URL.format(key=EXCHANGE_RATE_API_KEY, from_currency=from_c)
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("result") == "success" and "conversion_rates" in data:
                    rate = data["conversion_rates"].get(to_c)
                    if rate:
                        exchange_rate_cache[cache_key] = float(rate)
                        return float(rate)
        except Exception as e:
            print(f"ExchangeRate-API failed for {from_c}>{to_c}: {e}")

    # Layer 2: Hardcoded approximate fallback
    from_rate = _hardcoded_fallback_rates.get(from_c, 1.0)
    to_rate = _hardcoded_fallback_rates.get(to_c, 1.0)
    approx = from_rate / to_rate if to_rate else 1.0
    print(f"Warning: Using approximate rate {from_c}>{to_c} = {approx}")
    exchange_rate_cache[cache_key] = approx
    return approx


def convert_to_usd(price: float, ticker_or_currency: str) -> float:
    """Convert price to USD based on ticker or explicit currency string."""
    if price is None:
        return 0.0
    curr = ticker_or_currency.upper()
    if len(curr) == 3:  # Already a currency code
        if curr == "USD":
            return float(price)
        rate = get_exchange_rate(curr, "USD")
        return float(price) * rate
    # Otherwise treat as ticker
    detected, _ = detect_currency_and_country(curr)
    if detected == "USD":
        return float(price)
    rate = get_exchange_rate(detected, "USD")
    return float(price) * rate


# Database helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 1. BUY ENGINE (Improved)
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

    # Fetch live market data
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            raise HTTPException(status_code=400, detail=f"Invalid ticker symbol: {ticker}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Market data unavailable for {ticker}: {str(e)}")

    # Detect currency/nation and get enriched info
    info = enrich_stock_info(ticker)
    currency = info.get("currency", "USD")
    country = info.get("country", "US")

    # Prices
    current_price_native = float(data["Close"].iloc[-1])
    current_price_usd = convert_to_usd(current_price_native, currency)
    rate_used = get_exchange_rate(currency, "USD")

    # Cost calculation
    total_cost_usd = current_price_usd * quantity
    if user.balance < total_cost_usd:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds. Cost: ${round(total_cost_usd, 2)}, Balance: ${round(user.balance, 2)}"
        )

    # Deduct balance
    user.balance -= total_cost_usd

    # Portfolio update
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

        # Weighted average original price
        old_orig_cost = portfolio_item.original_avg_buy_price * (new_total_shares - quantity)
        new_orig_cost = current_price_native * quantity
        portfolio_item.original_avg_buy_price = (old_orig_cost + new_orig_cost) / new_total_shares
        portfolio_item.last_exchange_rate = rate_used
        portfolio_item.exchange = info.get("exchange", "Unknown")
    else:
        new_holding = Portfolio(
            user_id=user_big_id,
            ticker=ticker,
            shares_owned=quantity,
            average_buy_price=current_price_usd,
            currency=currency,
            country=country,
            exchange=info.get("exchange", "Unknown"),
            original_avg_buy_price=current_price_native,
            last_exchange_rate=rate_used,
            total_cost_basis_usd=total_cost_usd,
        )
        db.add(new_holding)

    # Transaction history
    history_log = TransactionHistory(
        user_id=user_big_id,
        ticker=ticker,
        action="BUY",
        shares=quantity,
        price_per_share=current_price_usd,
        currency=currency,
        country=country,
        exchange=info.get("exchange", "Unknown"),
        original_price_per_share=current_price_native,
        exchange_rate_used=rate_used,
        total_value_usd=total_cost_usd,
    )
    db.add(history_log)

    db.commit()
    return {
        "message": f"Successfully bought {quantity} shares of {ticker}!",
        "new_balance": round(user.balance, 2),
        "currency": currency,
        "country": country,
        "price_usd": round(current_price_usd, 2),
        "price_native": round(current_price_native, 2),
    }


# ==========================================
# 2. SELL ENGINE (Improved)
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

    # Fetch current market price
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            raise HTTPException(status_code=400, detail="Error fetching market price.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Market data unavailable for {ticker}: {str(e)}")

    info = enrich_stock_info(ticker)
    currency = info.get("currency", "USD")
    country = info.get("country", "US")

    current_price_native = float(data["Close"].iloc[-1])
    current_price_usd = convert_to_usd(current_price_native, currency)
    rate_used = get_exchange_rate(currency, "USD")

    total_revenue_usd = current_price_usd * quantity

    # Credit user
    user.balance += total_revenue_usd

    # Update portfolio
    portfolio_item.shares_owned -= quantity
    # Proportionally reduce cost basis to keep avg buy price stable on partial sells
    if portfolio_item.shares_owned > 0:
        sold_ratio = quantity / (portfolio_item.shares_owned + quantity)
        portfolio_item.total_cost_basis_usd -= portfolio_item.total_cost_basis_usd * sold_ratio
        portfolio_item.average_buy_price = portfolio_item.total_cost_basis_usd / portfolio_item.shares_owned
    else:
        portfolio_item.total_cost_basis_usd = 0.0
        portfolio_item.average_buy_price = 0.0

    # Cleanup if effectively empty (float tolerance)
    if portfolio_item.shares_owned <= 0.0001:
        db.delete(portfolio_item)

    # Transaction history
    history_log = TransactionHistory(
        user_id=user_big_id,
        ticker=ticker,
        action="SELL",
        shares=quantity,
        price_per_share=current_price_usd,
        currency=currency,
        country=country,
        exchange=info.get("exchange", "Unknown"),
        original_price_per_share=current_price_native,
        exchange_rate_used=rate_used,
        total_value_usd=total_revenue_usd,
    )
    db.add(history_log)

    db.commit()
    return {
        "message": f"Successfully sold {quantity} shares of {ticker}!",
        "new_balance": round(user.balance, 2),
        "currency": currency,
        "country": country,
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
@cached(cache=market_cache)
def get_real_market_data():
    """Returns live prices for the default global watchlist."""
    market_data = []
    tickers_string = " ".join(WATCHLIST.keys())

    try:
        yf_tickers = yf.Tickers(tickers_string)
    except Exception as e:
        print(f"Tickers init failed: {e}")
        yf_tickers = None

    for ticker_symbol, ui_data in WATCHLIST.items():
        try:
            if yf_tickers and ticker_symbol in yf_tickers.tickers:
                ticker_obj = yf_tickers.tickers[ticker_symbol]
            else:
                ticker_obj = yf.Ticker(ticker_symbol)

            fast_info = ticker_obj.fast_info
            current_price = fast_info.last_price
            prev_close = fast_info.previous_close

            info = enrich_stock_info(ticker_symbol)
            currency = info.get("currency", "USD")
            country = info.get("country", ui_data.get("country", "US"))

            current_price_usd = convert_to_usd(current_price, currency)
            prev_close_usd = convert_to_usd(prev_close, currency) if prev_close else None

            if prev_close_usd and prev_close_usd > 0:
                change_pct = ((current_price_usd - prev_close_usd) / prev_close_usd) * 100
                change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
            else:
                change_str = "0.00%"

            market_data.append({
                "ticker": ticker_symbol,
                "name": ui_data["name"],
                "price": round(current_price_usd, 2),
                "icon": ui_data["icon"],
                "category": ui_data["category"],
                "change": change_str,
                "currency": currency,
                "country": country,
                "flag": COUNTRY_FLAGS.get(country, "🌍"),
                "exchange": info.get("exchange", "Unknown"),
            })
        except Exception as e:
            print(f"Failed to fetch {ticker_symbol}: {e}")

    return market_data


# ==========================================
# 5. SEARCH ENGINE
# ==========================================

def fetch_price_data(quote):
    ticker_symbol = quote.get("symbol")
    if not ticker_symbol:
        return None

    if ticker_symbol in price_cache:
        return price_cache[ticker_symbol]

    try:
        info = enrich_stock_info(ticker_symbol)
        currency = info.get("currency", "USD")
        country = info.get("country", "US")

        ticker_obj = yf.Ticker(ticker_symbol)
        fast_info = ticker_obj.fast_info

        current_price = getattr(fast_info, "last_price", None)
        prev_close = getattr(fast_info, "previous_close", None)

        if not current_price:
            return None

        current_price_usd = convert_to_usd(current_price, currency)
        prev_close_usd = convert_to_usd(prev_close, currency) if prev_close else None

        change_str = "0.00%"
        if prev_close_usd and prev_close_usd > 0:
            change_pct = ((current_price_usd - prev_close_usd) / prev_close_usd) * 100
            change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

        exchange = quote.get("exchange", "Unknown")
        qtype = quote.get("quoteType", "Stock")

        result = {
            "ticker": ticker_symbol,
            "name": quote.get("shortname") or quote.get("longname") or ticker_symbol,
            "price": round(current_price_usd, 2),
            "exchange": exchange,
            "type": qtype,
            "icon": COUNTRY_FLAGS.get(country, "🌍"),
            "category": exchange,
            "change": change_str,
            "currency": currency,
            "country": country,
            "flag": COUNTRY_FLAGS.get(country, "🌍"),
        }
        price_cache[ticker_symbol] = result
        return result
    except Exception as e:
        print(f"Skipping {ticker_symbol}: {e}")
        return None


@router.get("/search")
@cached(cache=query_cache)
def search_global_stocks(query: str = Query(..., min_length=1)):
    """Searches Yahoo Finance with caching and parallel processing."""
    try:
        search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(search_url, headers=headers, timeout=5)

        if response.status_code != 200:
            return []

        quotes = [q for q in response.json().get("quotes", []) if q.get("quoteType") in ["EQUITY", "ETF"]]
        live_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = executor.map(fetch_price_data, quotes)
            for res in results:
                if res:
                    live_results.append(res)

        return live_results
    except Exception as e:
        print(f"Search failed for '{query}': {e}")
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
    tickers = [item.ticker for item in portfolio_items]

    for item in portfolio_items:
        try:
            ticker_obj = yf.Ticker(item.ticker)
            fast_info = ticker_obj.fast_info
            current_price = fast_info.last_price
            prev_close = fast_info.previous_close

            info = enrich_stock_info(item.ticker)
            currency = info.get("currency", item.currency or "USD")
            country = info.get("country", item.country or "US")

            current_price_usd = convert_to_usd(current_price, currency)
            prev_close_usd = convert_to_usd(prev_close, currency) if prev_close else None

            if prev_close_usd and prev_close_usd > 0:
                change_pct = ((current_price_usd - prev_close_usd) / prev_close_usd) * 100
                change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"
            else:
                change_str = "0.00%"

            portfolio_prices.append({
                "ticker": item.ticker,
                "price": round(current_price_usd, 2),
                "change": change_str,
                "shares_owned": item.shares_owned,
                "average_buy_price": round(item.average_buy_price, 2),
                "currency": currency,
                "country": country,
                "flag": COUNTRY_FLAGS.get(country, "🌍"),
                "exchange": info.get("exchange", "Unknown"),
            })
        except Exception as e:
            print(f"Failed to fetch price for {item.ticker}: {e}")
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
    try:
        t = yf.Ticker(ticker.upper())
        data = t.history(period="1d")
        if data.empty:
            raise HTTPException(status_code=404, detail="Ticker not found or no data.")

        info = enrich_stock_info(ticker)
        currency = info.get("currency", "USD")
        country = info.get("country", "US")

        native = float(data["Close"].iloc[-1])
        usd = convert_to_usd(native, currency)

        return {
            "ticker": ticker.upper(),
            "price_native": round(native, 4),
            "price_usd": round(usd, 4),
            "currency": currency,
            "country": country,
            "flag": COUNTRY_FLAGS.get(country, "🌍"),
            "name": info.get("name", ticker.upper()),
            "exchange": info.get("exchange", "Unknown"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 7b. STOCK METRICS
# ==========================================
@router.get("/metrics/{ticker}")
def get_stock_metrics(ticker: str):
    """Returns key financial metrics for a ticker."""
    try:
        info = enrich_stock_info(ticker)
        t = yf.Ticker(ticker.upper())
        data = t.history(period="1d")
        current_price = None
        if not data.empty:
            current_price = float(data["Close"].iloc[-1])

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
            except:
                return None

        metrics = {
            "ticker": ticker.upper(),
            "name": info.get("name"),
            "currency": info.get("currency", "USD"),
            "country": info.get("country", "US"),
            "flag": info.get("flag", "🌍"),
            "exchange": info.get("exchange", "Unknown"),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry"),
            "price_native": round(current_price, 2) if current_price else None,
            "price_usd": round(convert_to_usd(current_price, info.get("currency", "USD")), 2) if current_price else None,
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
def get_stock_history(ticker: str, period: str = Query("1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y)$")):
    """Returns historical closing prices for sparkline/chart rendering."""
    try:
        t = yf.Ticker(ticker.upper())
        hist = t.history(period=period)
        if hist.empty:
            raise HTTPException(status_code=404, detail="No historical data.")

        info = enrich_stock_info(ticker)
        currency = info.get("currency", "USD")

        closes = hist["Close"].tolist()
        dates = hist.index.strftime("%Y-%m-%d").tolist()

        return {
            "ticker": ticker.upper(),
            "currency": currency,
            "country": info.get("country", "US"),
            "flag": COUNTRY_FLAGS.get(info.get("country", "US"), "🌍"),
            "exchange": info.get("exchange", "Unknown"),
            "dates": dates,
            "prices_native": [round(p, 2) for p in closes],
            "prices_usd": [round(convert_to_usd(p, currency), 2) for p in closes],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 9. NEWS FEED
# ==========================================
@router.get("/news")
def get_market_news(category: str = Query("general", pattern="^(general|forex|crypto|merger)$")):
    """Proxy Finnhub market news to avoid exposing API key on frontend."""
    if not FINNHUB_API_KEY:
        return []
    try:
        url = "https://finnhub.io/api/v1/news"
        params = {"category": category, "token": FINNHUB_API_KEY}
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            # Trim to essentials
            trimmed = []
            for item in data[:15]:
                trimmed.append({
                    "headline": item.get("headline", ""),
                    "source": item.get("source", ""),
                    "summary": item.get("summary", ""),
                    "url": item.get("url", ""),
                    "image": item.get("image", ""),
                    "datetime": item.get("datetime"),
                    "category": item.get("category", ""),
                })
            return trimmed
        return []
    except Exception as e:
        print(f"News fetch failed: {e}")
        return []
