"""Options Lab API routes.

Provides option chain lookup, strategy generation, paper execution, and position
management. Broker integrations will be added in phase 2.
"""

from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.db import get_db
from core.logging import get_logger
from models.auth import User
from models.options import OptionPosition, OptionsStrategyRecord
from services.options_pricing import get_option_chain, get_underlying_quote
from services.options_strategy import (
    bull_call_spread,
    bear_put_spread,
    iron_condor,
    straddle,
    strangle,
    calculate_strategy_metrics,
    strategy_to_dict,
    OptionsStrategy,
    OptionsLeg,
    _nearest_expiry,
)

router = APIRouter(prefix="/options", tags=["Options Lab"])
logger = get_logger(__name__)

DEFAULT_LOT_SIZE = 1  # US equity options: 1 contract = 100 shares, but for paper we keep it simple


# ---------------------------------------------------------------------------
# 1. Option chain
# ---------------------------------------------------------------------------

@router.get("/chain/{underlying}")
def option_chain(underlying: str, expiry: str | None = Query(None)):
    """Best-effort option chain for an underlying."""
    return get_option_chain(underlying, expiry)


# ---------------------------------------------------------------------------
# 2. Strategy builder
# ---------------------------------------------------------------------------

@router.get("/strategies/{strategy_name}")
def build_strategy(
    strategy_name: str,
    underlying: str = Query(...),
    expiry: str | None = Query(None),
    atm_strike: float | None = Query(None),
    width: float | None = Query(None),
    near_width: float | None = Query(None),
    far_width: float | None = Query(None),
    lower_strike: float | None = Query(None),
    upper_strike: float | None = Query(None),
    lots: int = Query(1, ge=1),
    direction: str = Query("BUY"),
):
    """Generate a multi-leg option strategy without executing it."""
    underlying = underlying.upper().strip()
    if expiry is None:
        expiry = _nearest_expiry(underlying)

    # Resolve ATM if not supplied
    if atm_strike is None:
        spot, _, _ = get_underlying_quote(underlying)
        atm_strike = round(spot, 2)

    try:
        if strategy_name == "straddle":
            strat = straddle(underlying, expiry, atm_strike, lots, direction)
        elif strategy_name == "strangle":
            if width is None:
                width = round(atm_strike * 0.02, 2)
            strat = strangle(underlying, expiry, atm_strike, width, lots, direction)
        elif strategy_name == "iron_condor":
            near = near_width or round(atm_strike * 0.02, 2)
            far = far_width or round(atm_strike * 0.05, 2)
            strat = iron_condor(underlying, expiry, atm_strike, near, far, lots)
        elif strategy_name == "bull_call_spread":
            if lower_strike is None or upper_strike is None:
                lower_strike = lower_strike or round(atm_strike * 0.98, 2)
                upper_strike = upper_strike or round(atm_strike * 1.02, 2)
            strat = bull_call_spread(underlying, expiry, lower_strike, upper_strike, lots)
        elif strategy_name == "bear_put_spread":
            if lower_strike is None or upper_strike is None:
                lower_strike = lower_strike or round(atm_strike * 0.98, 2)
                upper_strike = upper_strike or round(atm_strike * 1.02, 2)
            strat = bear_put_spread(underlying, expiry, upper_strike, lower_strike, lots)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy_name}")

        calculate_strategy_metrics(strat, lot_size=DEFAULT_LOT_SIZE)
        return strategy_to_dict(strat)
    except Exception as exc:
        logger.error(f"Strategy build failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# 3. Paper execution
# ---------------------------------------------------------------------------

@router.post("/strategy/buy")
def buy_strategy(
    user_id: str = Query(...),
    strategy_name: str = Query(...),
    underlying: str = Query(...),
    expiry: str = Query(...),
    lots: int = Query(1, ge=1),
    direction: str = Query("BUY"),
    width: float | None = Query(None),
    near_width: float | None = Query(None),
    far_width: float | None = Query(None),
    lower_strike: float | None = Query(None),
    upper_strike: float | None = Query(None),
    db: Session = Depends(get_db),
):
    """Execute a paper option strategy: deduct net premium and store legs."""
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be valid integer.")

    user = db.query(User).filter(User.id == user_big_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    underlying = underlying.upper().strip()
    spot, _, _ = get_underlying_quote(underlying)
    atm_strike = round(spot, 2)

    if strategy_name == "straddle":
        strat = straddle(underlying, expiry, atm_strike, lots, direction)
    elif strategy_name == "strangle":
        width = width or round(atm_strike * 0.02, 2)
        strat = strangle(underlying, expiry, atm_strike, width, lots, direction)
    elif strategy_name == "iron_condor":
        near = near_width or round(atm_strike * 0.02, 2)
        far = far_width or round(atm_strike * 0.05, 2)
        strat = iron_condor(underlying, expiry, atm_strike, near, far, lots)
    elif strategy_name == "bull_call_spread":
        lower = lower_strike or round(atm_strike * 0.98, 2)
        upper = upper_strike or round(atm_strike * 1.02, 2)
        strat = bull_call_spread(underlying, expiry, lower, upper, lots)
    elif strategy_name == "bear_put_spread":
        lower = lower_strike or round(atm_strike * 0.98, 2)
        upper = upper_strike or round(atm_strike * 1.02, 2)
        strat = bear_put_spread(underlying, expiry, upper, lower, lots)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {strategy_name}")

    calculate_strategy_metrics(strat, lot_size=DEFAULT_LOT_SIZE)
    cost = abs(strat.net_premium) * DEFAULT_LOT_SIZE

    if strat.net_premium < 0 and user.balance < cost:
        raise HTTPException(status_code=400, detail=f"Insufficient funds: need ${cost:.2f}, balance ${user.balance:.2f}")

    # Record strategy snapshot
    record = OptionsStrategyRecord(
        user_id=user_big_id,
        name=strat.name,
        underlying=strat.underlying,
        expiry=strat.expiry,
        legs_json=json.dumps(strategy_to_dict(strat)["legs"]),
        total_premium=strat.net_premium,
        max_profit=strat.max_profit,
        max_loss=strat.max_loss,
        breakeven_upper=strat.breakeven_upper,
        breakeven_lower=strat.breakeven_lower,
    )
    db.add(record)
    db.flush()  # get record.id

    # Debit/credit cash
    if strat.net_premium < 0:
        user.balance -= cost
    else:
        user.balance += cost  # net credit strategy

    # Store individual legs
    for idx, leg in enumerate(strat.legs):
        position = OptionPosition(
            user_id=user_big_id,
            underlying=leg.underlying,
            expiry=leg.expiry,
            strike=leg.strike,
            option_type=leg.option_type,
            side=leg.side,
            quantity=leg.quantity * DEFAULT_LOT_SIZE,
            premium=leg.premium,
            currency="USD",
            exchange_rate_used=1.0,
            lot_size=DEFAULT_LOT_SIZE,
            strategy_name=strat.name,
            strategy_record_id=record.id,
            leg_index=idx,
        )
        db.add(position)

    db.commit()

    return {
        "message": f"Paper strategy '{strat.name}' executed.",
        "strategy_id": record.id,
        "net_premium": strat.net_premium,
        "new_balance": round(user.balance, 2),
        "legs": strategy_to_dict(strat)["legs"],
    }


# ---------------------------------------------------------------------------
# 4. Portfolio / open positions
# ---------------------------------------------------------------------------

@router.get("/portfolio/{user_id}")
def get_options_portfolio(user_id: str, db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be valid integer.")

    records = (
        db.query(OptionsStrategyRecord)
        .filter(OptionsStrategyRecord.user_id == user_big_id)
        .filter(OptionsStrategyRecord.status == "OPEN")
        .order_by(OptionsStrategyRecord.timestamp.desc())
        .all()
    )

    result = []
    for rec in records:
        legs = json.loads(rec.legs_json) if rec.legs_json else []
        # Current P/L estimate using latest spot
        spot, _, _ = get_underlying_quote(rec.underlying)
        current_value = 0.0
        for leg in legs:
            intrinsic = _intrinsic_value(spot, leg["strike"], leg["option_type"])
            sign = 1 if leg["side"] == "BUY" else -1
            current_value += sign * intrinsic * leg["quantity"]

        result.append({
            "id": rec.id,
            "name": rec.name,
            "underlying": rec.underlying,
            "expiry": rec.expiry,
            "total_premium": rec.total_premium,
            "max_profit": rec.max_profit,
            "max_loss": rec.max_loss,
            "breakeven_upper": rec.breakeven_upper,
            "breakeven_lower": rec.breakeven_lower,
            "spot": round(spot, 2),
            "estimated_value": round(current_value, 2),
            "timestamp": rec.timestamp.isoformat() if rec.timestamp else None,
            "legs": legs,
        })
    return result


def _intrinsic_value(spot: float, strike: float, option_type: str) -> float:
    if option_type == "CE":
        return max(0.0, spot - strike)
    return max(0.0, strike - spot)


# ---------------------------------------------------------------------------
# 5. Close position
# ---------------------------------------------------------------------------

@router.delete("/position/{position_id}")
def close_strategy(position_id: int, user_id: str = Query(...), db: Session = Depends(get_db)):
    try:
        user_big_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id must be valid integer.")

    record = db.query(OptionsStrategyRecord).filter(
        OptionsStrategyRecord.id == position_id,
        OptionsStrategyRecord.user_id == user_big_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    if record.status != "OPEN":
        raise HTTPException(status_code=400, detail="Strategy already closed.")

    # Simple close: reverse the net premium at current intrinsic value estimate
    spot, _, _ = get_underlying_quote(record.underlying)
    legs = json.loads(record.legs_json) if record.legs_json else []
    settle_value = 0.0
    for leg in legs:
        intrinsic = _intrinsic_value(spot, leg["strike"], leg["option_type"])
        sign = 1 if leg["side"] == "BUY" else -1
        settle_value += sign * intrinsic * leg["quantity"]

    pnl = round(settle_value + record.total_premium, 2)

    user = db.query(User).filter(User.id == user_big_id).first()
    if user:
        user.balance += pnl

    record.status = "CLOSED"
    db.query(OptionPosition).filter(
        OptionPosition.strategy_record_id == position_id
    ).update({"status": "CLOSED"})
    db.commit()

    return {
        "message": f"Closed strategy '{record.name}'",
        "pnl": pnl,
        "new_balance": round(user.balance, 2) if user else None,
    }


# ---------------------------------------------------------------------------
# 6. Supported brokers (phase-2 stub)
# ---------------------------------------------------------------------------

@router.get("/brokers")
def supported_brokers():
    """Brokers available for live integration in phase 2."""
    return {
        "enabled": False,
        "supported": [
            "Zerodha", "Upstox", "Angel One", "Fyers", "Dhan", "Groww",
            "Kotak", "IIFL", "5paisa", "AliceBlue", "Shoonya", "Motilal",
            "IBKR", "Alpaca", "Tradier", "Saxo",
        ],
        "note": "Live broker integration is planned for phase 2. Paper trading is active now.",
    }
