"""
data_fetcher.py
Fetches all market data needed for the BTC daily analysis.
Sources: Binance, Alternative.me, CoinGecko, CryptoPanic
"""

import os
import requests
import pandas as pd
from datetime import datetime


BINANCE_SPOT   = "https://api.binance.com/api/v3"
BINANCE_FUTURES = "https://fapi.binance.com/fapi/v1"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
COINGECKO_URL  = "https://api.coingecko.com/api/v3/global"


def get_ohlcv(symbol="BTCUSDT", interval="1d", limit=90):
    """
    Fetch daily OHLCV candles from Binance (no API key needed).
    Returns a DataFrame with columns: timestamp, open, high, low, close, volume
    """
    try:
        resp = requests.get(
            f"{BINANCE_SPOT}/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=10
        )
        resp.raise_for_status()
        cols = [
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ]
        df = pd.DataFrame(resp.json(), columns=cols)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        for c in ["open", "high", "low", "close", "volume", "quote_volume"]:
            df[c] = df[c].astype(float)
        return df[["timestamp", "open", "high", "low", "close", "volume", "quote_volume"]]
    except Exception as e:
        print(f"  [!] OHLCV fetch failed: {e}")
        return None


def get_24h_ticker(symbol="BTCUSDT"):
    """Fetch 24h ticker statistics from Binance."""
    try:
        resp = requests.get(
            f"{BINANCE_SPOT}/ticker/24hr",
            params={"symbol": symbol},
            timeout=10
        )
        resp.raise_for_status()
        d = resp.json()
        return {
            "price":            float(d["lastPrice"]),
            "price_change_pct": float(d["priceChangePercent"]),
            "volume_btc":       float(d["volume"]),
            "volume_usdt":      float(d["quoteVolume"]),
            "high_24h":         float(d["highPrice"]),
            "low_24h":          float(d["lowPrice"]),
            "open_24h":         float(d["openPrice"]),
        }
    except Exception as e:
        print(f"  [!] 24h ticker fetch failed: {e}")
        return {}


def get_funding_rate(symbol="BTCUSDT"):
    """Fetch latest perpetual futures funding rate from Binance."""
    try:
        resp = requests.get(
            f"{BINANCE_FUTURES}/fundingRate",
            params={"symbol": symbol, "limit": 1},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[-1]["fundingRate"]) * 100  # as percentage
        return None
    except Exception as e:
        print(f"  [!] Funding rate fetch failed: {e}")
        return None


def get_fear_greed():
    """Fetch the Crypto Fear & Greed Index from alternative.me."""
    try:
        resp = requests.get(FEAR_GREED_URL, params={"limit": 1}, timeout=10)
        resp.raise_for_status()
        item = resp.json()["data"][0]
        return {
            "value": int(item["value"]),
            "label": item["value_classification"],
        }
    except Exception as e:
        print(f"  [!] Fear & Greed fetch failed: {e}")
        return {}


def get_global_data():
    """Fetch BTC dominance and total market cap from CoinGecko (no API key needed)."""
    try:
        resp = requests.get(COINGECKO_URL, timeout=10)
        resp.raise_for_status()
        d = resp.json()["data"]
        return {
            "btc_dominance": round(d["market_cap_percentage"].get("btc", 0), 2),
            "total_market_cap_usd": d["total_market_cap"].get("usd", 0),
        }
    except Exception as e:
        print(f"  [!] CoinGecko fetch failed: {e}")
        return {}


def get_news(api_key=None, limit=5):
    """
    Fetch latest BTC news from CryptoPanic.
    Requires a free API key from https://cryptopanic.com/developers/api/
    Returns empty list if no key is configured.
    """
    if not api_key:
        return []
    try:
        resp = requests.get(
            "https://cryptopanic.com/api/v1/posts/",
            params={
                "auth_token": api_key,
                "currencies": "BTC",
                "kind": "news",
                "public": "true",
            },
            timeout=10
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return [
            {
                "title":  item["title"],
                "source": item["source"]["title"],
            }
            for item in results[:limit]
        ]
    except Exception as e:
        print(f"  [!] News fetch failed: {e}")
        return []


def fetch_all_data():
    """
    Master function: fetches everything and returns a single dict.
    """
    print("  -> OHLCV data (Binance)...")
    df = get_ohlcv()

    print("  -> 24h ticker (Binance)...")
    ticker = get_24h_ticker()

    print("  -> Funding rate (Binance Futures)...")
    funding_rate = get_funding_rate()

    print("  -> Fear & Greed Index (alternative.me)...")
    fear_greed = get_fear_greed()

    print("  -> Global market data (CoinGecko)...")
    global_data = get_global_data()

    print("  -> News (CryptoPanic)...")
    news = get_news(api_key=os.getenv("CRYPTOPANIC_API_KEY"))

    return {
        "df":          df,
        "ticker":      ticker,
        "funding_rate": funding_rate,
        "fear_greed":  fear_greed,
        "global_data": global_data,
        "news":        news,
        "generated_at": datetime.now(),
    }
