"""Option pricing and chain helpers backed by yfinance.

yfinance provides option chains for US equities. International index options
(e.g. NIFTY) are not available through yfinance, so we gracefully fall back to
synthetic/estimated data for demo purposes. Broker integrations (phase 2) can
replace this provider with real-time F&O chains.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import yfinance as yf

from services.market_data import YFinanceProvider, COUNTRY_FLAGS
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OptionContract:
    underlying: str
    ticker: str                 # e.g. "AAPL250718C240"
    option_type: str            # "CE" or "PE"
    strike: float
    expiry: str                 # ISO date
    last_price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    implied_volatility: Optional[float] = None
    open_interest: Optional[int] = None
    volume: Optional[int] = None
    currency: str = "USD"
    exchange: str = "Unknown"


# -----------------------------------------------------------------------------
# yfinance chain provider
# -----------------------------------------------------------------------------

def _yfinance_expirations(ticker: str) -> List[str]:
    try:
        t = yf.Ticker(ticker.upper())
        return list(t.options)  # list of ISO date strings
    except Exception as exc:
        logger.warning(f"Failed to fetch option expirations for {ticker}: {exc}")
        return []


def _yfinance_chain(ticker: str, expiry: str) -> Optional[Tuple[List[OptionContract], List[OptionContract]]]:
    """Return (calls, puts) for a specific expiry using yfinance."""
    try:
        t = yf.Ticker(ticker.upper())
        chain = t.option_chain(expiry)
    except Exception as exc:
        logger.warning(f"Failed to fetch option chain for {ticker} {expiry}: {exc}")
        return None

    def _row_to_contract(row, option_type: str) -> OptionContract:
        # yfinance columns: contractSymbol, lastTradeDate, strike, lastPrice, bid, ask,
        # change, percentChange, volume, openInterest, impliedVolatility, inTheMoney,
        # contractSize, currency
        return OptionContract(
            underlying=ticker.upper(),
            ticker=str(row.get("contractSymbol", "")),
            option_type=option_type,
            strike=float(row.get("strike", 0)),
            expiry=expiry,
            last_price=float(row.get("lastPrice", 0) or 0),
            bid=_safe_float(row.get("bid")),
            ask=_safe_float(row.get("ask")),
            implied_volatility=_safe_float(row.get("impliedVolatility")),
            open_interest=_safe_int(row.get("openInterest")),
            volume=_safe_int(row.get("volume")),
            currency=str(row.get("currency", "USD")),
            exchange="OPT",
        )

    calls = [_row_to_contract(row, "CE") for _, row in chain.calls.iterrows()]
    puts = [_row_to_contract(row, "PE") for _, row in chain.puts.iterrows()]
    return calls, puts


def _safe_float(val) -> Optional[float]:
    try:
        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None
        return float(val)
    except Exception:
        return None


def _safe_int(val) -> Optional[int]:
    try:
        if val is None:
            return None
        return int(val)
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Public helpers
# -----------------------------------------------------------------------------

def get_underlying_quote(underlying: str) -> Tuple[float, str, str]:
    """Return (spot_price_usd, currency, country)."""
    provider = YFinanceProvider()
    quote = provider.get_quote(underlying)
    if quote:
        return quote.price, quote.currency, quote.country
    return 0.0, "USD", "US"


def get_option_chain(underlying: str, expiry: Optional[str] = None) -> Dict:
    """Best-effort option chain for an underlying.

    Returns a dict with:
      - underlying, spot, currency, exchange, expiry
      - calls / puts lists nearest to ATM first
      - fallback flag if yfinance had no data
    """
    underlying = underlying.upper().strip()
    expirations = _yfinance_expirations(underlying)

    if not expirations:
        # Build a synthetic chain for demo / unsupported tickers
        return _synthetic_chain(underlying, expiry)

    selected_expiry = expiry if expiry in expirations else expirations[0]
    chain = _yfinance_chain(underlying, selected_expiry)

    if not chain:
        return _synthetic_chain(underlying, selected_expiry)

    calls, puts = chain
    spot, currency, country = get_underlying_quote(underlying)
    atm = _atm_strike(calls + puts, spot)

    calls_sorted = sorted(calls, key=lambda c: abs(c.strike - atm))
    puts_sorted = sorted(puts, key=lambda p: abs(p.strike - atm))

    return {
        "underlying": underlying,
        "spot": round(spot, 2),
        "currency": currency,
        "country": country,
        "flag": COUNTRY_FLAGS.get(country, "🌍"),
        "expiry": selected_expiry,
        "expirations": expirations,
        "atm": round(atm, 2),
        "fallback": False,
        "calls": [c.__dict__ for c in calls_sorted[:20]],
        "puts": [p.__dict__ for p in puts_sorted[:20]],
    }


def get_contract_for_strike(
    underlying: str,
    expiry: str,
    option_type: str,
    target_strike: float,
) -> Optional[OptionContract]:
    """Pick the live contract closest to a target strike."""
    chain = _yfinance_chain(underlying, expiry)
    if not chain:
        return None
    pool = chain[0] if option_type == "CE" else chain[1]
    if not pool:
        return None
    return min(pool, key=lambda c: abs(c.strike - target_strike))


def _atm_strike(contracts: List[OptionContract], spot: float) -> float:
    if not contracts:
        return spot
    return min((c.strike for c in contracts), key=lambda s: abs(s - spot))


# -----------------------------------------------------------------------------
# Synthetic fallback for unsupported tickers
# -----------------------------------------------------------------------------

def _synthetic_chain(underlying: str, expiry: Optional[str]) -> Dict:
    """Generate a plausible option chain when yfinance has no option data.

    This keeps the Options Lab usable for international demo tickers.
    Premiums are rough Black-Scholes estimates for ATM options.
    """
    provider = YFinanceProvider()
    quote = provider.get_quote(underlying)
    spot = quote.price if quote else 100.0
    currency = quote.currency if quote else "USD"
    country = quote.country if quote else "US"
    atm = round(spot, 2)

    if expiry is None:
        # Default to ~30 days out formatted as ISO date
        from datetime import timedelta
        expiry = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")

    strike_step = _strike_step(spot)
    strikes = [round(atm + (i - 5) * strike_step, 2) for i in range(11)]

    calls = []
    puts = []
    for strike in strikes:
        # Approx 1 year IV ~ 30%, scale time to 30 days
        tau = 30 / 365.0
        iv = 0.30
        premium_call = _black_scholes(spot, strike, tau, 0.05, iv, "CE")
        premium_put = _black_scholes(spot, strike, tau, 0.05, iv, "PE")
        compact_expiry = expiry.replace("-", "")[2:]  # 25-07-18 -> 250718
        symbol = f"{underlying}{compact_expiry}C{int(strike)}" if strike == int(strike) else f"{underlying}{compact_expiry}C{strike}"
        calls.append(OptionContract(
            underlying=underlying,
            ticker=symbol,
            option_type="CE",
            strike=strike,
            expiry=expiry,
            last_price=round(premium_call, 2),
            currency=currency,
            exchange="SYNTH",
        ).__dict__)
        symbol = f"{underlying}{compact_expiry}P{int(strike)}" if strike == int(strike) else f"{underlying}{compact_expiry}P{strike}"
        puts.append(OptionContract(
            underlying=underlying,
            ticker=symbol,
            option_type="PE",
            strike=strike,
            expiry=expiry,
            last_price=round(premium_put, 2),
            currency=currency,
            exchange="SYNTH",
        ).__dict__)

    return {
        "underlying": underlying,
        "spot": round(spot, 2),
        "currency": currency,
        "country": country,
        "flag": COUNTRY_FLAGS.get(country, "🌍"),
        "expiry": expiry,
        "expirations": [expiry],
        "atm": round(atm, 2),
        "fallback": True,
        "calls": calls,
        "puts": puts,
    }


def _strike_step(spot: float) -> float:
    if spot < 50:
        return 2.5
    if spot < 200:
        return 5.0
    if spot < 500:
        return 10.0
    if spot < 1000:
        return 20.0
    return 50.0


def _black_scholes(S: float, K: float, T: float, r: float, sigma: float, opt_type: str) -> float:
    """European option price (used for fallback estimates only)."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, S - K) if opt_type == "CE" else max(0.0, K - S)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    from scipy.stats import norm  # type: ignore
    if opt_type == "CE":
        return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
