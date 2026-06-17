"""
analysis_generator.py
Uses the Claude API to generate a professional BTC daily analysis
based on all collected market data and technical indicators.
"""

import os
import anthropic
from datetime import datetime


def _safe(value, fmt=None, fallback="N/A"):
    """Safely format a value, returning fallback on None or error."""
    if value is None:
        return fallback
    try:
        return format(value, fmt) if fmt else str(value)
    except (ValueError, TypeError):
        return fallback


def _build_prompt(data: dict, indicators: dict) -> str:
    ticker      = data.get("ticker", {})
    fear_greed  = data.get("fear_greed", {})
    global_data = data.get("global_data", {})
    funding     = data.get("funding_rate")
    news        = data.get("news", [])
    date_str    = datetime.now().strftime("%B %d, %Y")

    news_lines = "\n".join(
        [f"- {n['title']} ({n['source']})" for n in news[:5]]
    ) if news else "No news available at this time."

    macd_val  = indicators.get("macd", 0) or 0
    macd_sig  = indicators.get("macd_signal", 0) or 0
    macd_hist = indicators.get("macd_hist", 0) or 0
    macd_direction = "bullish crossover" if macd_val > macd_sig else "bearish crossover"
    macd_momentum  = "increasing" if macd_hist > 0 else "decreasing"

    rsi_val = indicators.get("rsi", 50) or 50
    if rsi_val >= 70:
        rsi_zone = "overbought territory"
    elif rsi_val <= 30:
        rsi_zone = "oversold territory"
    else:
        rsi_zone = "neutral zone"

    ema20 = indicators.get("ema20") or 0
    ema50 = indicators.get("ema50") or 0
    ema_status = "above" if ema20 > ema50 else "below"

    if funding is not None:
        if funding > 0.05:
            funding_sentiment = "heavily long (overheated longs, potential long squeeze risk)"
        elif funding > 0:
            funding_sentiment = "slightly positive (mild bullish bias)"
        elif funding < -0.05:
            funding_sentiment = "heavily short (potential short squeeze risk)"
        else:
            funding_sentiment = "slightly negative (mild bearish bias)"
    else:
        funding_sentiment = "data unavailable"

    prompt = f"""You are a professional cryptocurrency market analyst writing a daily Bitcoin briefing for Patreon subscribers. These are informed retail investors and traders who want clear, actionable, and insightful analysis — not hype.

Today is {date_str}.

=== MARKET DATA ===
Current Price:    ${_safe(ticker.get('price'), ',.2f')}
24h Change:       {_safe(ticker.get('price_change_pct'), '+.2f')}%
24h High:         ${_safe(ticker.get('high_24h'), ',.2f')}
24h Low:          ${_safe(ticker.get('low_24h'), ',.2f')}
24h Volume (USD): ${_safe(ticker.get('volume_usdt'), ',.0f')}
BTC Dominance:    {_safe(global_data.get('btc_dominance'), '.2f')}%
Total Market Cap: ${_safe((global_data.get('total_market_cap_usd') or 0) / 1e12, '.2f')}T

=== TECHNICAL INDICATORS (Daily) ===
Price:            ${_safe(indicators.get('price'), ',.2f')}
RSI (14):         {_safe(rsi_val, '.2f')} — {rsi_zone}
MACD:             {_safe(macd_val, '.4f')} | Signal: {_safe(macd_sig, '.4f')} | Hist: {_safe(macd_hist, '.4f')} — {macd_direction}, momentum {macd_momentum}
Bollinger Upper:  ${_safe(indicators.get('bb_upper'), ',.2f')}
Bollinger Mid:    ${_safe(indicators.get('bb_mid'), ',.2f')}
Bollinger Lower:  ${_safe(indicators.get('bb_lower'), ',.2f')}
EMA 20:           ${_safe(ema20, ',.2f')} ({ema_status} EMA 50)
EMA 50:           ${_safe(ema50, ',.2f')}

=== SENTIMENT & ON-CHAIN ===
Fear & Greed:     {_safe(fear_greed.get('value'))} / 100 ({_safe(fear_greed.get('label'))})
Funding Rate:     {_safe(funding, '+.4f') if funding is not None else 'N/A'}% — {funding_sentiment}

=== LATEST NEWS ===
{news_lines}

---

Write a professional daily Bitcoin analysis using EXACTLY this structure. Write in plain text only — no markdown symbols like **, *, #, or backticks. Use the emoji section headers as shown. Be specific with price levels. Sound like a seasoned analyst, not a hype account. Target length: 380-450 words.

📊 BITCOIN DAILY ANALYSIS — {date_str.upper()}

💰 MARKET SNAPSHOT
[4 concise bullet points covering: current price & 24h change, 24h high/low range, volume, and BTC dominance]

📈 TECHNICAL ANALYSIS
[2 focused paragraphs. Cover: current trend direction, where price sits relative to key MAs and Bollinger Bands, what the EMA relationship implies. Be specific with price levels. No filler sentences.]

🎯 KEY LEVELS TO WATCH
[4-5 bullet points with specific support and resistance prices derived from the data above. Label each clearly as Support or Resistance.]

📉 INDICATOR BREAKDOWN
[One sentence per indicator — RSI, MACD, Bollinger Bands, EMA cross — each with a specific interpretation, not just description.]

🧠 SENTIMENT & ON-CHAIN
[2-3 sentences interpreting Fear & Greed and funding rate together. What does the combination tell us about market positioning?]

📰 MARKET HEADLINES
[List the top news items as bullet points. One sentence each. Skip if no news available.]

🔮 SHORT-TERM OUTLOOK
[2 paragraphs. Paragraph 1: the most likely scenario given all signals. Paragraph 2: the key level or event that would invalidate this view, and what the alternative scenario looks like.]

⚠️ This analysis is for educational purposes only and does not constitute financial advice. Always do your own research before making investment decisions.
"""
    return prompt


def generate_analysis(data: dict, indicators: dict) -> str:
    """Generate the BTC daily analysis text using Claude API."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    prompt = _build_prompt(data, indicators)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text
