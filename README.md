# BTC Daily Analysis Bot

Generates a professional Bitcoin analysis every morning and sends it to Telegram.
Includes a dark-themed chart (candlestick + BB + EMA + RSI + MACD) and an AI-written
analysis in English, ready to publish on Patreon.

---

## What it sends

1. **Chart image** — candlestick (60d), Bollinger Bands, EMA 20/50, Volume, RSI, MACD
2. **Analysis text** with:
   - Market snapshot (price, volume, dominance)
   - Technical analysis (trend, key levels)
   - Indicator breakdown
   - Fear & Greed + funding rate sentiment
   - Top news headlines
   - Short-term outlook

---

## Setup

### 1. Clone / copy the project files

```
btc_daily_analysis/
├── main.py
├── data_fetcher.py
├── chart_generator.py
├── analysis_generator.py
├── telegram_sender.py
├── requirements.txt
├── railway.toml
└── .env.example
```

### 2. Get your API keys

| Key | Where to get it | Required? |
|-----|-----------------|-----------|
| `ANTHROPIC_API_KEY` | console.anthropic.com | ✅ Yes |
| `TELEGRAM_BOT_TOKEN` | @BotFather on Telegram | ✅ Yes |
| `TELEGRAM_CHAT_ID` | See step 3 below | ✅ Yes |
| `CRYPTOPANIC_API_KEY` | cryptopanic.com/developers/api | Optional |

### 3. Create your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **token** (looks like `123456789:AAFxxxxxxxx`)
4. Start a conversation with your new bot (send any message)
5. Get your Chat ID by opening this URL in a browser:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
6. Look for `"chat":{"id": 123456789}` — that number is your Chat ID

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your actual keys
```

### 5. Test locally

```bash
pip install -r requirements.txt
python main.py
```

---

## Deploy on Railway

1. Push the project to a GitHub repo
2. In Railway, create a **New Project → Deploy from GitHub repo**
3. Select this repo
4. Go to **Settings → Variables** and add all your `.env` keys
5. Go to **Settings → Deploy** and set it as a **Cron Job**
6. Set the cron schedule:
   - `0 7 * * *` → 07:00 UTC (Winter Portugal time ✅)
   - `0 6 * * *` → 07:00 WEST (Summer Portugal time ✅)

That's it. Railway will run `python main.py` every morning automatically.

---

## Data sources

| Data | Source | Cost |
|------|--------|------|
| OHLCV + Funding Rate | Binance API | Free, no key needed |
| Fear & Greed Index | alternative.me | Free, no key needed |
| BTC Dominance | CoinGecko | Free, no key needed |
| News | CryptoPanic | Free API key |
| Analysis text | Claude API (Anthropic) | Paid (very low cost per run) |

---

## Troubleshooting

**Bot doesn't send anything:**
- Make sure you sent at least one message TO the bot before checking getUpdates
- Verify the Chat ID is correct (no extra spaces)

**Chart is blank or errors:**
- The `ta` library needs at least 50 candles — should be fine with 90

**CoinGecko rate limit:**
- CoinGecko's free tier can throttle. If it fails, the analysis still runs without dominance data.
