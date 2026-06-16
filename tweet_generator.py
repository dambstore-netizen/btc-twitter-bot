"""
tweet_generator.py
Generates a 4-tweet thread for Twitter/X using Claude API.

Thread structure:
  1/4 — price + headline + teaser
  2/4 — key levels (support/resistance)
  3/4 — indicator summary in plain language
  4/4 — CTA to Patreon + hashtags
"""

import os
import anthropic
from datetime import datetime


def _safe(value, fmt=None, fallback="N/A"):
    if value is None:
        return fallback
    try:
        return format(value, fmt) if fmt else str(value)
    except (ValueError, TypeError):
        return fallback


def generate_thread(data: dict, indicators: dict) -> list:
    """
    Generate a 4-tweet thread for Twitter/X.
    Returns a list of 4 strings, each under 280 chars.
    """
    client      = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ticker      = data.get("ticker", {})
    fg          = data.get("fear_greed", {})
    global_data = data.get("global_data", {})
    date_str    = datetime.now().strftime("%B %d, %Y")

    price    = ticker.get("price")
    pct      = ticker.get("price_change_pct")
    high_24h = ticker.get("high_24h")
    low_24h  = ticker.get("low_24h")
    vol_usdt = ticker.get("volume_usdt")
    rsi      = indicators.get("rsi")
    ema20    = indicators.get("ema20", 0) or 0
    ema50    = indicators.get("ema50", 0) or 0
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    bb_mid   = indicators.get("bb_mid")
    macd_h   = indicators.get("macd_hist", 0) or 0
    fg_val   = fg.get("value")
    fg_label = fg.get("label", "")
    dominance = global_data.get("btc_dominance")

    ema_status   = "EMA20 above EMA50 (bullish)" if ema20 > ema50 else "EMA20 below EMA50 (bearish)"
    macd_status  = "bullish momentum" if macd_h > 0 else "bearish momentum"
    patreon_url  = os.getenv("PATREON_URL", "patreon.com/yourpage")

    prompt = f"""You are a professional crypto analyst writing a 4-tweet Twitter/X thread about Bitcoin. Today is {date_str}.

MARKET DATA:
- Price: ${_safe(price, ',.2f')} ({_safe(pct, '+.2f')}% 24h)
- 24h High: ${_safe(high_24h, ',.2f')} | Low: ${_safe(low_24h, ',.2f')}
- Volume (24h): ${_safe(vol_usdt, ',.0f')}
- BTC Dominance: {_safe(dominance, '.1f')}%
- Fear & Greed: {_safe(fg_val)} ({fg_label})

TECHNICAL INDICATORS:
- RSI(14): {_safe(rsi, '.1f')}
- {ema_status}
- EMA20: ${_safe(ema20, ',.2f')} | EMA50: ${_safe(ema50, ',.2f')}
- Bollinger Upper: ${_safe(bb_upper, ',.2f')} | Mid: ${_safe(bb_mid, ',.2f')} | Lower: ${_safe(bb_lower, ',.2f')}
- MACD: {macd_status}

Write EXACTLY 4 tweets separated by the delimiter ---TWEET--- between each.

TWEET 1 (hook — max 260 chars):
Start with the date and price. Mention the single most important technical observation today.
End with "Thread below" and a thread emoji. Make it punchy — traders should want to read on.

TWEET 2 (key levels — max 260 chars):
Start with a target emoji. Title: "Key levels to watch:"
List resistance and support levels clearly with the actual prices.
End with one sentence on what the price location between these levels means.

TWEET 3 (indicators — max 260 chars):
Start with a chart emoji. Title: "Indicators:"
Summarize RSI, EMA, MACD and Fear & Greed in bullet-point style.
End with one honest sentence on the overall bias (long/short/neutral) and why.

TWEET 4 (CTA — max 260 chars):
Start with a lock emoji. Say the full analysis with chart and exact entry/exit levels is on Patreon.
Include this exact URL on its own line: {patreon_url}
End with: #Bitcoin #BTC #CryptoAnalysis #TechnicalAnalysis

RULES:
- Plain text only — no markdown, no asterisks
- Each tweet must be under 260 characters (leaving room for the thread numbering)
- Emojis are fine and encouraged
- Prices must use the exact numbers from the data above
- Do not invent data — if something is N/A, skip it"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    raw    = message.content[0].text.strip()
    tweets = [t.strip() for t in raw.split("---TWEET---")]

    result = []
    for i, tweet in enumerate(tweets[:4], 1):
        numbered = f"{tweet}\n\n{i}/4"
        if len(numbered) > 280:
            numbered = tweet[:270] + f"\n\n{i}/4"
        result.append(numbered)

    while len(result) < 4:
        result.append(f"[tweet {len(result)+1}/4 not generated]")

    return result
