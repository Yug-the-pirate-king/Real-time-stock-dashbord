from fastapi import APIRouter, Query
from cachetools import TTLCache
import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import yfinance as yf
from typing import List, Dict, Any
import concurrent.futures
from datetime import datetime
import os

from data.finance_geo import STOCK_EXCHANGES, CENTRAL_BANKS, FEEDS

router = APIRouter(prefix="/finance", tags=["Finance Monitor"])

rss_cache = TTLCache(maxsize=200, ttl=600)
brief_cache = TTLCache(maxsize=1, ttl=300)
alerts_cache = TTLCache(maxsize=1, ttl=120)

# Finnhub key fallback (same as trading.py)
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "d87v551r01qmhakhgmd0d87v551r01qmhakhgmdg")

# Tickers scanned for breaking alerts
ALERT_TICKERS = [
    "AAPL", "TSLA", "NVDA", "AMD", "COIN", "META", "AMZN", "GOOG",
    "BTC-USD", "ETH-USD", "CL=F", "GC=F", "SI=F", "MSFT", "NFLX",
]

# Watchlist used for daily brief
BRIEF_TICKERS = ["AAPL", "MSFT", "TSLA", "NVDA", "SPY", "QQQ", "GLD", "USO"]


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    try:
        soup = BeautifulSoup(raw, "html.parser")
        return soup.get_text(separator=" ").strip()
    except Exception:
        return raw


def _parse_rss(xml_text: str) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return items

    # RSS 2.0 path
    channel = root.find("channel")
    if channel is not None:
        for item in channel.findall("item"):
            title = item.findtext("title", default="")
            link = item.findtext("link", default="")
            desc = item.findtext("description", default="")
            pub = item.findtext("pubDate", default="")
            source = item.findtext("source", default="")
            items.append(
                {
                    "headline": _strip_html(title),
                    "url": link.strip(),
                    "summary": _strip_html(desc),
                    "source": source.strip(),
                    "datetime": pub.strip(),
                }
            )
        return items

    # Atom fallback
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        link_el = entry.find("atom:link", ns)
        link = link_el.get("href") if link_el is not None else ""
        desc = (
            entry.findtext("atom:summary", default="", namespaces=ns)
            or entry.findtext("atom:content", default="", namespaces=ns)
        )
        pub = (
            entry.findtext("atom:published", default="", namespaces=ns)
            or entry.findtext("atom:updated", default="", namespaces=ns)
        )
        source = ""
        if link:
            from urllib.parse import urlparse

            source = urlparse(link).netloc.replace("www.", "")
        items.append(
            {
                "headline": _strip_html(title),
                "url": link.strip(),
                "summary": _strip_html(desc),
                "source": source,
                "datetime": pub.strip(),
            }
        )
    return items


def _fetch_feed(feed_url: str) -> List[Dict[str, str]]:
    if feed_url in rss_cache:
        return rss_cache[feed_url]
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; StockPulseBot/1.0)"}
        resp = requests.get(feed_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            parsed = _parse_rss(resp.text)
            rss_cache[feed_url] = parsed
            return parsed
    except Exception as e:
        print(f"RSS fetch failed for {feed_url}: {e}")
    return []


@router.get("/news")
def get_finance_news(
    category: str = Query("general"),
    limit: int = Query(15, ge=1, le=50),
):
    """Return finance news. General proxies Finnhub; others use curated RSS feeds."""
    if category == "general":
        if not FINNHUB_API_KEY:
            return []
        try:
            url = "https://finnhub.io/api/v1/news"
            params = {"category": "general", "token": FINNHUB_API_KEY}
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                trimmed = []
                for item in data[:limit]:
                    trimmed.append(
                        {
                            "headline": item.get("headline", ""),
                            "source": item.get("source", ""),
                            "summary": item.get("summary", ""),
                            "url": item.get("url", ""),
                            "image": item.get("image", ""),
                            "datetime": item.get("datetime"),
                            "category": "general",
                        }
                    )
                return trimmed
        except Exception as e:
            print(f"Finnhub general news failed: {e}")
        return []

    feeds = FEEDS.get(category, [])
    if not feeds:
        return []

    all_items: List[Dict[str, Any]] = []
    seen = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(_fetch_feed, f["url"]): f["name"] for f in feeds}
        for future in concurrent.futures.as_completed(futures):
            source_name = futures[future]
            try:
                items = future.result()
                for it in items:
                    key = it["headline"].lower().strip()
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    it["source"] = it["source"] or source_name
                    it["category"] = category
                    all_items.append(it)
            except Exception:
                continue

    return all_items[:limit]


@router.get("/exchanges")
def get_exchanges():
    """Static list of global stock exchanges."""
    return STOCK_EXCHANGES


@router.get("/central-banks")
def get_central_banks():
    """Static list of major central banks and institutions."""
    return CENTRAL_BANKS


@router.get("/brief")
def get_daily_brief():
    """Auto-generated daily brief from yfinance watchlist."""
    cache_key = "brief"
    if cache_key in brief_cache:
        return brief_cache[cache_key]

    items = []
    gainer = {"ticker": "-", "change": -999.0}
    loser = {"ticker": "-", "change": 999.0}
    spy_change = 0.0

    for ticker in BRIEF_TICKERS:
        try:
            t = yf.Ticker(ticker)
            fast = t.fast_info
            price = fast.last_price
            prev = fast.previous_close
            change_pct = ((price - prev) / prev) * 100 if prev else 0.0
            items.append(
                {
                    "ticker": ticker,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "prev_close": round(prev, 2) if prev else None,
                }
            )
            if change_pct > gainer["change"]:
                gainer = {"ticker": ticker, "change": round(change_pct, 2)}
            if change_pct < loser["change"]:
                loser = {"ticker": ticker, "change": round(change_pct, 2)}
            if ticker == "SPY":
                spy_change = round(change_pct, 2)
        except Exception:
            continue

    mood = (
        "bullish"
        if spy_change > 0.5
        else "bearish"
        if spy_change < -0.5
        else "neutral"
    )

    narrative_parts = [f"Markets are {mood} today."]
    if gainer["ticker"] != "-":
        narrative_parts.append(
            f"Top gainer: {gainer['ticker']} (+{gainer['change']}%)."
        )
    if loser["ticker"] != "-":
        narrative_parts.append(
            f"Top laggard: {loser['ticker']} ({loser['change']}%)."
        )
    narrative_parts.append(
        f"S&P 500 (SPY) is {'up' if spy_change >= 0 else 'down'} {abs(spy_change):.2f}%."
    )

    brief = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "mood": mood,
        "spy_change": spy_change,
        "top_gainer": gainer if gainer["ticker"] != "-" else None,
        "top_loser": loser if loser["ticker"] != "-" else None,
        "watchlist_summary": items,
        "narrative": " ".join(narrative_parts),
    }
    brief_cache[cache_key] = brief
    return brief


@router.get("/geo")
def get_finance_geo():
    """Return all finance geo-located entities (exchanges + central banks) for map plotting."""
    geo_points = []
    for ex in STOCK_EXCHANGES:
        geo_points.append(
            {
                "id": ex["id"],
                "type": "exchange",
                "name": ex["name"],
                "shortName": ex.get("shortName", ""),
                "city": ex.get("city", ""),
                "country": ex.get("country", ""),
                "lat": ex.get("lat"),
                "lon": ex.get("lon"),
                "tier": ex.get("tier"),
                "marketCap": ex.get("marketCap"),
                "tradingHours": ex.get("tradingHours"),
                "timezone": ex.get("timezone"),
                "description": ex.get("description", ""),
            }
        )
    for bank in CENTRAL_BANKS:
        geo_points.append(
            {
                "id": bank["id"],
                "type": "central_bank",
                "name": bank["name"],
                "shortName": bank.get("shortName", ""),
                "city": bank.get("city", ""),
                "country": bank.get("country", ""),
                "lat": bank.get("lat"),
                "lon": bank.get("lon"),
                "bankType": bank.get("type"),
                "currency": bank.get("currency"),
                "description": bank.get("description", ""),
            }
        )
    return geo_points


@router.get("/alerts")
def get_breaking_alerts(threshold: float = Query(2.5)):
    """Return tickers with intraday moves exceeding the threshold %."""
    cache_key = f"alerts_{threshold}"
    if cache_key in alerts_cache:
        return alerts_cache[cache_key]

    alerts = []
    for ticker in ALERT_TICKERS:
        try:
            t = yf.Ticker(ticker)
            fast = t.fast_info
            price = fast.last_price
            prev = fast.previous_close
            if not prev:
                continue
            change_pct = ((price - prev) / prev) * 100
            if abs(change_pct) >= threshold:
                severity = "critical" if abs(change_pct) >= 5.0 else "warning"
                alerts.append(
                    {
                        "ticker": ticker,
                        "price": round(price, 2),
                        "change_pct": round(change_pct, 2),
                        "severity": severity,
                        "message": f"{ticker} is {'up' if change_pct > 0 else 'down'} {abs(change_pct):.2f}% at ${round(price, 2)}",
                    }
                )
        except Exception:
            continue

    alerts.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    alerts_cache[cache_key] = alerts
    return alerts
