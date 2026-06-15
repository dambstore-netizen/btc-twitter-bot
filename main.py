"""
main.py — BTC Telegram Analysis Bot
Sends daily BTC chart + full AI analysis + 4-tweet thread to Telegram.

Deploy on Railway as a Cron Job: 0 7 * * *
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def check_env():
    required = ["ANTHROPIC_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    missing  = [k for k in required if not os.getenv(k)]
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        print("  Copy .env.example to .env and fill in your keys.")
        sys.exit(1)


def run():
    check_env()

    print()
    print("=" * 55)
    print(f"  BTC DAILY ANALYSIS BOT")
    print(f"  {datetime.now().strftime('%Y-%m-%d  %H:%M UTC')}")
    print("=" * 55)

    # 1. Fetch data
    print("\n[1/5] Fetching market data...")
    from data_fetcher import fetch_all_data
    data = fetch_all_data()

    if data["df"] is None or data["df"].empty:
        print("[FATAL] Could not fetch OHLCV data. Aborting.")
        sys.exit(1)

    print(f"       OK — {len(data['df'])} candles, {len(data['news'])} news items")

    # 2. Generate chart
    print("\n[2/5] Generating chart...")
    from chart_generator import generate_chart
    chart_path, indicators = generate_chart(data["df"])
    print(f"       RSI: {indicators['rsi']}  |  "
          f"EMA20: ${indicators['ema20']:,.0f}  |  "
          f"EMA50: ${indicators['ema50']:,.0f}")

    # 3. Generate full Patreon analysis
    print("\n[3/5] Generating AI analysis (Claude)...")
    from analysis_generator import generate_analysis
    analysis = generate_analysis(data, indicators)
    print(f"       Generated {len(analysis)} characters")

    # 4. Generate 4-tweet thread
    print("\n[4/5] Generating X thread (Claude)...")
    from tweet_generator import generate_thread
    tweets = generate_thread(data, indicators)
    print(f"       Generated {len(tweets)} tweets")

    # 5. Send everything to Telegram
    print("\n[5/5] Sending to Telegram...")
    from telegram_sender import send_analysis, send_tweet_thread
    send_analysis(chart_path, analysis)
    send_tweet_thread(tweets)

    print()
    print("=" * 55)
    print(f"  Done at {datetime.now().strftime('%H:%M:%S UTC')}")
    print("=" * 55)
    print()


if __name__ == "__main__":
    run()
