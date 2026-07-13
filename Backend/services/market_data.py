"""Market data provider abstraction.

The app consumes market data through this service so the underlying provider
(yfinance today, Polygon/Alpaca tomorrow) can be swapped without touching
business logic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests
import yfinance as yf

from core.cache import cache_get, cache_set
from core.config import get_settings
from core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

COUNTRY_FLAGS = {
    "US": "🇺🇸", "IN": "🇮🇳", "CA": "🇨🇦", "GB": "🇬🇧", "JP": "🇯🇵",
    "HK": "🇭🇰", "CN": "🇨🇳", "AU": "🇦🇺", "SG": "🇸🇬", "MX": "🇲🇽",
    "BR": "🇧🇷", "DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸", "NL": "🇳🇱",
    "IT": "🇮🇹", "CH": "🇨🇭", "SE": "🇸🇪", "DK": "🇩🇰", "FI": "🇫🇮",
    "KR": "🇰🇷", "TW": "🇹🇼", "ID": "🇮🇩", "RU": "🇷🇺", "ZA": "🇿🇦",
    "SA": "🇸🇦", "TH": "🇹🇭", "PE": "🇵🇪", "EG": "🇪🇬", "NZ": "🇳🇿",
    "IL": "🇮🇱", "NG": "🇳🇬",
}

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

_hardcoded_fallback_rates = {
    "USD": 1.0, "INR": 0.012, "CAD": 0.74, "GBP": 1.27, "JPY": 0.0067,
    "HKD": 0.128, "CNY": 0.138, "AUD": 0.66, "SGD": 0.74, "MXN": 0.059,
    "BRL": 0.20, "EUR": 1.09, "CHF": 1.12, "SEK": 0.096, "DKK": 0.146,
    "KRW": 0.00076, "TWD": 0.031, "IDR": 0.000064, "RUB": 0.011, "ZAR": 0.053,
    "SAR": 0.267, "THB": 0.028, "PHP": 0.017, "MYR": 0.22, "VND": 0.000039,
}


@dataclass
class StockQuote:
    ticker: str
    name: str
    price: float
    currency: str
    country: str
    flag: str
    exchange: str
    change_pct: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    volume: Optional[int] = None
    market_cap: Optional[int] = None
    type: str = "EQUITY"


class MarketDataProvider:
    """Abstract market data provider."""

    def get_quote(self, ticker: str) -> Optional[StockQuote]:
        raise NotImplementedError

    def get_history(self, ticker: str, period: str = "1mo") -> Optional[Dict]:
        raise NotImplementedError

    def search(self, query: str, limit: int = 8) -> List[StockQuote]:
        raise NotImplementedError


class YFinanceProvider(MarketDataProvider):
    """yfinance-backed provider.  Free, robust, and requires no API key."""

    def __init__(self):
        self._info_cache_ns = "stock_info"
        self._price_cache_ns = "price"

    # ------------------------------------------------------------------
    # Currency / country helpers
    # ------------------------------------------------------------------
    @staticmethod
    def detect_currency_and_country(ticker: str) -> tuple[str, str]:
        ticker_up = ticker.upper()
        for suffix, (curr, cc) in TICKER_SUFFIX_MAP.items():
            if ticker_up.endswith(suffix):
                return curr, cc
        return "USD", "US"

    @staticmethod
    def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float:
        from_c = from_currency.upper()
        to_c = to_currency.upper()
        if from_c == to_c:
            return 1.0

        cache_key = f"{from_c}_{to_c}"
        cached = cache_get("exchange_rate", cache_key)
        if cached is not None:
            return float(cached)

        rate: Optional[float] = None
        api_key = settings.exchange_rate_api_key
        if api_key:
            try:
                url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_c}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("result") == "success":
                        rate = data.get("conversion_rates", {}).get(to_c)
            except Exception as exc:
                logger.warning(f"ExchangeRate-API failed for {from_c}>{to_c}: {exc}")

        if rate is None:
            from_r = _hardcoded_fallback_rates.get(from_c, 1.0)
            to_r = _hardcoded_fallback_rates.get(to_c, 1.0)
            rate = from_r / to_r if to_r else 1.0
            logger.warning(f"Using approximate rate {from_c}>{to_c} = {rate}")

        cache_set("exchange_rate", cache_key, rate, ttl=settings.rate_cache_ttl)
        return float(rate)

    @classmethod
    def convert_to_usd(cls, price: Optional[float], ticker_or_currency: str) -> float:
        if price is None:
            return 0.0
        token = ticker_or_currency.upper()
        if len(token) == 3:
            if token == "USD":
                return float(price)
            rate = cls.get_exchange_rate(token, "USD")
            return float(price) * rate
        detected, _ = cls.detect_currency_and_country(token)
        if detected == "USD":
            return float(price)
        rate = cls.get_exchange_rate(detected, "USD")
        return float(price) * rate

    # ------------------------------------------------------------------
    # Info fetching
    # ------------------------------------------------------------------
    def enrich_info(self, ticker: str) -> Dict:
        cache_key = ticker.upper()
        cached = cache_get(self._info_cache_ns, cache_key)
        if cached is not None:
            return cached

        detected_curr, detected_cc = self.detect_currency_and_country(ticker)
        info = {
            "currency": detected_curr,
            "country": detected_cc,
            "flag": COUNTRY_FLAGS.get(detected_cc, "🌍"),
            "name": ticker.upper(),
            "sector": None,
            "industry": None,
            "exchange": "Unknown",
            "type": "EQUITY",
        }

        try:
            t = yf.Ticker(ticker)
            fast_info = t.fast_info
            t_info = t.info or {}

            info["name"] = (
                t_info.get("longName")
                or t_info.get("shortName")
                or fast_info.get("longName", ticker.upper())
            )
            if t_info.get("currency"):
                info["currency"] = t_info["currency"]
            if t_info.get("country"):
                info["country"] = t_info["country"]
            info["sector"] = t_info.get("sector")
            info["industry"] = t_info.get("industry")
            info["exchange"] = t_info.get("exchange", "Unknown")
            info["type"] = t_info.get("quoteType", "EQUITY")
            info["market_cap"] = t_info.get("marketCap")
            info["volume"] = t_info.get("volume") or t_info.get("regularMarketVolume")
            info["avg_volume"] = t_info.get("averageVolume")
            info["day_high"] = t_info.get("dayHigh") or t_info.get("regularMarketDayHigh")
            info["day_low"] = t_info.get("dayLow") or t_info.get("regularMarketDayLow")
            info["fifty_two_week_high"] = t_info.get("fiftyTwoWeekHigh")
            info["fifty_two_week_low"] = t_info.get("fiftyTwoWeekLow")
            info["beta"] = t_info.get("beta")
            info["pe_trailing"] = t_info.get("trailingPE")
            info["pe_forward"] = t_info.get("forwardPE")
            info["dividend_yield"] = t_info.get("dividendYield")
            info["eps"] = t_info.get("trailingEps")
            info["flag"] = COUNTRY_FLAGS.get(info["country"], "🌍")
        except Exception as exc:
            logger.warning(f"enrich_info fallback for {ticker}: {exc}")

        cache_set(self._info_cache_ns, cache_key, info, ttl=settings.info_cache_ttl)
        return info

    # ------------------------------------------------------------------
    # Quote
    # ------------------------------------------------------------------
    def get_quote(self, ticker: str) -> Optional[StockQuote]:
        cache_key = f"{ticker.upper()}:quote"
        cached = cache_get(self._price_cache_ns, cache_key)
        if cached is not None:
            return StockQuote(**cached)

        try:
            info = self.enrich_info(ticker)
            t = yf.Ticker(ticker.upper())
            hist = t.history(period="1d")
            if hist.empty:
                return None

            native = float(hist["Close"].iloc[-1])
            prev = None
            try:
                prev = float(t.fast_info.previous_close)
            except Exception:
                pass

            usd = self.convert_to_usd(native, info["currency"])
            prev_usd = self.convert_to_usd(prev, info["currency"]) if prev else None
            change_pct = None
            if prev_usd and prev_usd > 0:
                change_pct = ((usd - prev_usd) / prev_usd) * 100

            quote = StockQuote(
                ticker=ticker.upper(),
                name=info.get("name", ticker.upper()),
                price=round(usd, 4),
                currency=info.get("currency", "USD"),
                country=info.get("country", "US"),
                flag=COUNTRY_FLAGS.get(info.get("country", "US"), "🌍"),
                exchange=info.get("exchange", "Unknown"),
                change_pct=round(change_pct, 2) if change_pct is not None else None,
                sector=info.get("sector"),
                industry=info.get("industry"),
                volume=info.get("volume"),
                market_cap=info.get("market_cap"),
                type=info.get("type", "EQUITY"),
            )
            cache_set(self._price_cache_ns, cache_key, quote.__dict__, ttl=settings.price_cache_ttl)
            return quote
        except Exception as exc:
            logger.warning(f"Failed to quote {ticker}: {exc}")
            return None

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def get_history(self, ticker: str, period: str = "1mo") -> Optional[Dict]:
        valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}
        if period not in valid_periods:
            period = "1mo"

        cache_key = f"{ticker.upper()}:{period}:history"
        cached = cache_get("history", cache_key)
        if cached is not None:
            return cached

        try:
            info = self.enrich_info(ticker)
            t = yf.Ticker(ticker.upper())
            hist = t.history(period=period)
            if hist.empty:
                return None

            closes = hist["Close"].tolist()
            volumes = hist.get("Volume", []).tolist()
            dates = hist.index.strftime("%Y-%m-%d").tolist()

            result = {
                "ticker": ticker.upper(),
                "currency": info.get("currency", "USD"),
                "country": info.get("country", "US"),
                "flag": COUNTRY_FLAGS.get(info.get("country", "US"), "🌍"),
                "exchange": info.get("exchange", "Unknown"),
                "period": period,
                "dates": dates,
                "prices_native": [round(p, 4) for p in closes],
                "prices_usd": [round(self.convert_to_usd(p, info["currency"]), 4) for p in closes],
                "volume": [int(v) if v and v == v else 0 for v in volumes],  # NaN guard
            }
            cache_set("history", cache_key, result, ttl=settings.price_cache_ttl)
            return result
        except Exception as exc:
            logger.warning(f"Failed history for {ticker}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def search(self, query: str, limit: int = 8) -> List[StockQuote]:
        cache_key = f"{query.lower()}:{limit}"
        cached = cache_get("search", cache_key)
        if cached is not None:
            return [StockQuote(**q) for q in cached]

        try:
            search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount={limit}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(search_url, headers=headers, timeout=5)
            if resp.status_code != 200:
                return []

            quotes = [
                q for q in resp.json().get("quotes", [])
                if q.get("quoteType") in ["EQUITY", "ETF"]
            ]
            results: List[StockQuote] = []
            for q in quotes:
                symbol = q.get("symbol")
                if not symbol:
                    continue
                quote = self.get_quote(symbol)
                if quote:
                    quote.name = q.get("shortname") or q.get("longname") or quote.name
                    results.append(quote)

            cache_set("search", cache_key, [r.__dict__ for r in results], ttl=settings.search_cache_ttl)
            return results
        except Exception as exc:
            logger.warning(f"Search failed for '{query}': {exc}")
            return []


# Singleton provider instance — replace this line to swap data source globally.
_provider: MarketDataProvider = YFinanceProvider()


def get_provider() -> MarketDataProvider:
    return _provider


def set_provider(provider: MarketDataProvider) -> None:
    global _provider
    _provider = provider
