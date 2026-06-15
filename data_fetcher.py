"""
data_fetcher.py — v3 (Yahoo Finance)
Uses yfinance for OHLCV/price — works from any server globally.
"""

import os
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime


FEAR_GREED_URL = "https://api.alternative.me/fng/"
COINGECKO_URL  = "https://api.coingecko.com/api/v3/global"


def get_ohlcv(symbol="BTC-USD", period="90d", interval="1d"):
    """Fetch daily OHLCV candles from Yahoo Finance."""
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df.rename(columns={"date": "timestamp"}, inplace=True)
        if df["timestamp"].dt.tz is not None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
        df["quote_volume"] = df["volume"] * df["close"]
        return df[["timestamp", "open", "high", "low", "close", "volume", "quote_volume"]]
    except Exception as e:
        print(f"  [!] OHLCV fetch failed: {e}")
        return None


def get_24h_ticker(symbol="BTC-USD"):
    """Get 24h price stats from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)

        # Use 5d daily to ensure at least 2 complete candles
        hist = ticker.history(period="5d", interval="1d")
        if len(hist) < 2:
            return {}

        cur   = hist.iloc[-1]
        prev  = hist.iloc[-2]
        price = float(cur["Close"])
        pct   = (price - float(prev["Close"])) / float(prev["Close"]) * 100

        # Use 1d intraday for accurate today high/low/volume
        intra = ticker.history(period="1d", interval="1h")
        if not intra.empty:
            high_24h   = float(intra["High"].max())
            low_24h    = float(intra["Low"].min())
            volume_btc = float(intra["Volume"].sum())
        else:
            high_24h   = float(cur["High"])
            low_24h    = float(cur["Low"])
            volume_btc = float(cur["Volume"])

        return {
            "price":            price,
            "price_change_pct": round(pct, 2),
            "volume_btc":       volume_btc,
            "volume_usdt":      volume_btc * price,
            "high_24h":         high_24h,
            "low_24h":          low_24h,
            "open_24h":         float(cur["Open"]),
        }
    except Exception as e:
        print(f"  [!] 24h ticker fetch failed: {e}")
        return {}


def get_fear_greed():
    """Fetch the Crypto Fear & Greed Index from alternative.me."""
    try:
        resp = requests.get(FEAR_GREED_URL, params={"limit": 1}, timeout=10)
        resp.raise_for_status()
        item = resp.json()["data"][0]
        return {"value": int(item["value"]), "label": item["value_classification"]}
    except Exception as e:
        print(f"  [!] Fear & Greed fetch failed: {e}")
        return {}


def get_global_data():
    """Fetch BTC dominance from CoinGecko with retries."""
    headers = {
        "accept": "application/json",
        "user-agent": "Mozilla/5.0 (compatible; BTC-Analysis-Bot/1.0)"
    }
    for attempt in range(3):
        try:
            resp = requests.get(COINGECKO_URL, headers=headers, timeout=10)
            if resp.status_code == 429:
                print(f"  [!] CoinGecko rate limit, waiting 15s...")
                time.sleep(15)
                continue
            resp.raise_for_status()
            d = resp.json()["data"]
            return {
                "btc_dominance":        round(d["market_cap_percentage"].get("btc", 0), 2),
                "total_market_cap_usd": d["total_market_cap"].get("usd", 0),
            }
        except Exception as e:
            print(f"  [!] CoinGecko fetch failed (attempt {attempt+1}): {e}")
            time.sleep(5)
    return {}


def get_news(api_key=None, limit=5):
    """Fetch latest BTC news from CryptoPanic (optional)."""
    if not api_key:
        return []
    try:
        resp = requests.get(
            "https://cryptopanic.com/api/v1/posts/",
            params={"auth_token": api_key, "currencies": "BTC", "kind": "news", "public": "true"},
            timeout=10
        )
        resp.raise_for_status()
        return [
            {"title": item["title"], "source": item["source"]["title"]}
            for item in resp.json().get("results", [])[:limit]
        ]
    except Exception as e:
        print(f"  [!] News fetch failed: {e}")
        return []


def fetch_all_data():
    """Master function — fetches everything and returns a single dict."""
    print("  -> OHLCV data (Yahoo Finance)...")
    df = get_ohlcv()

    print("  -> 24h ticker (Yahoo Finance)...")
    ticker = get_24h_ticker()

    print("  -> Fear & Greed Index (alternative.me)...")
    fear_greed = get_fear_greed()

    print("  -> Global market data (CoinGecko)...")
    global_data = get_global_data()

    print("  -> News (CryptoPanic)...")
    news = get_news(api_key=os.getenv("CRYPTOPANIC_API_KEY"))

    return {
        "df":           df,
        "ticker":       ticker,
        "funding_rate": None,
        "fear_greed":   fear_greed,
        "global_data":  global_data,
        "news":         news,
        "generated_at": datetime.now(),
    }
