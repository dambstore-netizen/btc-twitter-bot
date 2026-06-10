 """
tweet_generator.py
Generates a short tweet for Twitter/X using Claude API.
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


def generate_tweet(data: dict, indicators: dict) -> str:
    client   = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ticker   = data.get("ticker", {})
    fg       = data.get("fear_greed", {})
    date_str = datetime.now().strftime("%b %d, %Y")

    price    = ticker.get("price")
    pct      = ticker.get("price_change_pct")
    rsi      = indicators.get("rsi")
    ema20    = indicators.get("ema20", 0) or 0
    ema50    = indicators.get("ema50", 0) or 0
    bb_upper = indicators.get("bb_upper")
    bb_lower = indicators.get("bb_lower")
    fg_val   = fg.get("value")
    fg_label = fg.get("label", "")

    ema_status  = "EMA20 > EMA50 ✅" if ema20 > ema50 else "EMA20 < EMA50 ⚠️"
    patreon_url = os.getenv("PATREON_URL", "patreon.com/yourpage")

    prompt = f"""Write a single Bitcoin tweet for Twitter/X. Today is {date_str}.

Market data:
- Price: ${_safe(price, ',.0f')} ({_safe(pct, '+.2f')}% 24h)
- RSI(14): {_safe(rsi, '.1f')}
- {ema_status}
- BB Upper: ${_safe(bb_upper, ',.0f')} | BB Lower: ${_safe(bb_lower, ',.0f')}
- Fear & Greed: {_safe(fg_val)} ({fg_label})

Rules:
- Write ONLY the tweet body — no explanations, no quotes
- Maximum 200 characters for the body
- Start with BTC price and % change
- Include 1 key technical insight
- End with one short directional outlook
- Professional but punchy — crypto Twitter style
- No markdown, no asterisks, emojis are fine"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    body     = message.content[0].text.strip()
    hashtags = "#Bitcoin #BTC #Crypto #CryptoAnalysis"
    cta      = f"Full analysis 👇\n{patreon_url}"
    tweet    = f"{body}\n\n{cta}\n\n{hashtags}"

    if len(tweet) > 280:
        tweet = tweet[:277] + "..."

    return tweet

