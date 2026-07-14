"""Option strategy builder engine.

Ported from FinceptTerminal/fincept-qt/src/trading/OptionsStrategyBuilder and
adapted for the StockPulse web backend. All strikes and premiums are in USD by
default; the caller can convert back to native currency when displaying.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from services.options_pricing import get_option_chain, get_contract_for_strike
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OptionsLeg:
    symbol: str                 # Tradable / placeholder symbol
    exchange: str
    side: str                   # "BUY" or "SELL"
    quantity: int               # Number of lots
    strike: float
    option_type: str            # "CE" or "PE"
    expiry: str                 # ISO date
    underlying: str
    premium: float = 0.0        # USD per lot


@dataclass
class OptionsStrategy:
    name: str
    legs: List[OptionsLeg] = field(default_factory=list)
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    breakeven_upper: Optional[float] = None
    breakeven_lower: Optional[float] = None
    net_premium: float = 0.0
    underlying: str = ""
    expiry: str = ""


def _nearest_expiry(underlying: str, preferred: Optional[str] = None) -> str:
    chain = get_option_chain(underlying)
    if preferred and preferred in chain.get("expirations", []):
        return preferred
    return chain.get("expiry", (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d"))


def _leg(
    underlying: str,
    expiry: str,
    strike: float,
    option_type: str,
    side: str,
    lots: int,
) -> OptionsLeg:
    contract = get_contract_for_strike(underlying, expiry, option_type, strike)
    if contract:
        return OptionsLeg(
            symbol=contract.ticker,
            exchange=contract.exchange,
            side=side,
            quantity=lots,
            strike=contract.strike,
            option_type=contract.option_type,
            expiry=expiry,
            underlying=underlying,
            premium=contract.last_price,
        )
    # Fallback: build a human-readable placeholder
    return OptionsLeg(
        symbol=_build_option_symbol(underlying, expiry, strike, option_type),
        exchange="OPT",
        side=side,
        quantity=lots,
        strike=strike,
        option_type=option_type,
        expiry=expiry,
        underlying=underlying,
        premium=0.0,
    )


def _build_option_symbol(underlying: str, expiry: str, strike: float, option_type: str) -> str:
    d = datetime.fromisoformat(expiry) if isinstance(expiry, str) else expiry
    month = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
             "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"][d.month - 1]
    short_expiry = f"{d.day:02d}{month}{str(d.year)[-2:]}"
    strike_str = str(int(strike)) if float(strike).is_integer() else str(strike)
    return f"{underlying.upper()}{short_expiry}{option_type.upper()}{strike_str}"


def _compact_expiry(expiry: str) -> str:
    d = datetime.fromisoformat(expiry)
    month = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
             "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"][d.month - 1]
    return f"{d.day:02d}{month}{str(d.year)[-2:]}"


# -----------------------------------------------------------------------------
# Strategy factories
# -----------------------------------------------------------------------------

def straddle(
    underlying: str,
    expiry: str,
    atm_strike: float,
    lots: int = 1,
    direction: str = "BUY",
) -> OptionsStrategy:
    """Long / short ATM straddle."""
    side = "BUY" if direction == "BUY" else "SELL"
    return OptionsStrategy(
        name="Long Straddle" if direction == "BUY" else "Short Straddle",
        legs=[
            _leg(underlying, expiry, atm_strike, "CE", side, lots),
            _leg(underlying, expiry, atm_strike, "PE", side, lots),
        ],
        underlying=underlying,
        expiry=expiry,
    )


def strangle(
    underlying: str,
    expiry: str,
    atm_strike: float,
    width: float,
    lots: int = 1,
    direction: str = "BUY",
) -> OptionsStrategy:
    """Long / short strangle using OTM strikes."""
    side = "BUY" if direction == "BUY" else "SELL"
    return OptionsStrategy(
        name="Long Strangle" if direction == "BUY" else "Short Strangle",
        legs=[
            _leg(underlying, expiry, atm_strike + width, "CE", side, lots),
            _leg(underlying, expiry, atm_strike - width, "PE", side, lots),
        ],
        underlying=underlying,
        expiry=expiry,
    )


def iron_condor(
    underlying: str,
    expiry: str,
    atm_strike: float,
    near_width: float,
    far_width: float,
    lots: int = 1,
) -> OptionsStrategy:
    """Short iron condor (net credit)."""
    return OptionsStrategy(
        name="Iron Condor",
        legs=[
            _leg(underlying, expiry, atm_strike + near_width, "CE", "SELL", lots),
            _leg(underlying, expiry, atm_strike + far_width, "CE", "BUY", lots),
            _leg(underlying, expiry, atm_strike - near_width, "PE", "SELL", lots),
            _leg(underlying, expiry, atm_strike - far_width, "PE", "BUY", lots),
        ],
        underlying=underlying,
        expiry=expiry,
    )


def bull_call_spread(
    underlying: str,
    expiry: str,
    lower_strike: float,
    upper_strike: float,
    lots: int = 1,
) -> OptionsStrategy:
    """Debit bull call spread."""
    return OptionsStrategy(
        name="Bull Call Spread",
        legs=[
            _leg(underlying, expiry, lower_strike, "CE", "BUY", lots),
            _leg(underlying, expiry, upper_strike, "CE", "SELL", lots),
        ],
        underlying=underlying,
        expiry=expiry,
    )


def bear_put_spread(
    underlying: str,
    expiry: str,
    upper_strike: float,
    lower_strike: float,
    lots: int = 1,
) -> OptionsStrategy:
    """Debit bear put spread."""
    return OptionsStrategy(
        name="Bear Put Spread",
        legs=[
            _leg(underlying, expiry, upper_strike, "PE", "BUY", lots),
            _leg(underlying, expiry, lower_strike, "PE", "SELL", lots),
        ],
        underlying=underlying,
        expiry=expiry,
    )


# -----------------------------------------------------------------------------
# Strategy metadata / payoff helpers
# -----------------------------------------------------------------------------

def calculate_strategy_metrics(strategy: OptionsStrategy, lot_size: int = 1) -> OptionsStrategy:
    """Compute net premium and best-effort max profit/loss / breakevens."""
    net = 0.0
    for leg in strategy.legs:
        sign = 1 if leg.side == "BUY" else -1
        net += sign * leg.premium * leg.quantity * lot_size
    strategy.net_premium = round(net, 2)

    strikes = sorted({leg.strike for leg in strategy.legs})

    # Debit vertical spreads
    if strategy.name in ("Bull Call Spread", "Bear Put Spread") and len(strikes) == 2:
        width = abs(strikes[1] - strikes[0])
        if net < 0:  # debit
            strategy.max_profit = round((width * lot_size) + net, 2)
            strategy.max_loss = round(-net, 2)
        else:  # credit
            strategy.max_profit = round(net, 2)
            strategy.max_loss = round(-(width * lot_size) + net, 2)

    # Straddle
    if "Straddle" in strategy.name:
        if strategy.name.startswith("Long"):
            strategy.max_loss = round(-net if net < 0 else 0, 2)
            if net < 0:
                strategy.breakeven_upper = round(strategy.legs[0].strike - net / lot_size, 2)
                strategy.breakeven_lower = round(strategy.legs[0].strike + net / lot_size, 2)
        else:
            strategy.max_profit = round(net if net > 0 else 0, 2)
            if net > 0:
                strategy.breakeven_upper = round(strategy.legs[0].strike + net / lot_size, 2)
                strategy.breakeven_lower = round(strategy.legs[0].strike - net / lot_size, 2)

    # Strangle
    if "Strangle" in strategy.name and len(strikes) >= 2:
        call_strike = max(leg.strike for leg in strategy.legs if leg.option_type == "CE")
        put_strike = min(leg.strike for leg in strategy.legs if leg.option_type == "PE")
        if strategy.name.startswith("Long"):
            strategy.max_loss = round(-net if net < 0 else 0, 2)
            if net < 0:
                strategy.breakeven_upper = round(call_strike - net / lot_size, 2)
                strategy.breakeven_lower = round(put_strike + net / lot_size, 2)
        else:
            strategy.max_profit = round(net if net > 0 else 0, 2)
            if net > 0:
                strategy.breakeven_upper = round(call_strike + net / lot_size, 2)
                strategy.breakeven_lower = round(put_strike - net / lot_size, 2)

    # Iron condor
    if strategy.name == "Iron Condor" and len(strikes) == 4:
        ce_strikes = sorted(leg.strike for leg in strategy.legs if leg.option_type == "CE")
        pe_strikes = sorted(leg.strike for leg in strategy.legs if leg.option_type == "PE")
        if len(ce_strikes) == 2 and len(pe_strikes) == 2:
            wing_width_ce = abs(ce_strikes[1] - ce_strikes[0])
            wing_width_pe = abs(pe_strikes[1] - pe_strikes[0])
            max_wing = max(wing_width_ce, wing_width_pe)
            strategy.max_profit = round(net, 2) if net > 0 else 0
            strategy.max_loss = round(-(max_wing * lot_size) + net, 2)
            strategy.breakeven_upper = round(ce_strikes[0] + net / lot_size, 2)
            strategy.breakeven_lower = round(pe_strikes[1] - net / lot_size, 2)

    return strategy


def strategy_to_dict(strategy: OptionsStrategy) -> Dict:
    return {
        "name": strategy.name,
        "underlying": strategy.underlying,
        "expiry": strategy.expiry,
        "net_premium": strategy.net_premium,
        "max_profit": strategy.max_profit,
        "max_loss": strategy.max_loss,
        "breakeven_upper": strategy.breakeven_upper,
        "breakeven_lower": strategy.breakeven_lower,
        "legs": [
            {
                "symbol": leg.symbol,
                "exchange": leg.exchange,
                "side": leg.side,
                "quantity": leg.quantity,
                "strike": leg.strike,
                "option_type": leg.option_type,
                "expiry": leg.expiry,
                "underlying": leg.underlying,
                "premium": leg.premium,
            }
            for leg in strategy.legs
        ],
    }
