"""
telegram_sender.py
Sends the BTC chart, full analysis, and Twitter thread draft to Telegram.

Destinations:
  TELEGRAM_CHAT_ID     — your private chat (full analysis + chart + thread)
  TELEGRAM_CHANNEL_ID  — public BitMagnet channel (teaser only)
"""

import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MAX_MESSAGE  = 4096


def _url(method: str) -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    return TELEGRAM_API.format(token=token, method=method)


def _send_message(chat_id: str, text: str):
    chunks = [text[i:i+MAX_MESSAGE] for i in range(0, len(text), MAX_MESSAGE)]
    for chunk in chunks:
        resp = requests.post(
            _url("sendMessage"),
            json={"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True},
            timeout=15,
        )
        resp.raise_for_status()


def _send_photo(chat_id: str, photo_path: str):
    with open(photo_path, "rb") as f:
        resp = requests.post(
            _url("sendPhoto"),
            data={"chat_id": chat_id},
            files={"photo": f},
            timeout=30,
        )
    resp.raise_for_status()


def send_analysis(chart_path: str, analysis_text: str, teaser_text: str = None):
    """
    Send to both destinations:
      - Private chat: chart + full analysis
      - Public channel: teaser only (if TELEGRAM_CHANNEL_ID is set)
    """
    token      = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id    = os.getenv("TELEGRAM_CHAT_ID")
    channel_id = os.getenv("TELEGRAM_CHANNEL_ID")

    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")
    if not chat_id:
        raise EnvironmentError("TELEGRAM_CHAT_ID is not set.")

    # --- Private chat: full analysis ---
    print("  -> [Private] Sending chart image...")
    _send_photo(chat_id, chart_path)

    print("  -> [Private] Sending full analysis...")
    _send_message(chat_id, analysis_text)

    # --- Public channel: teaser ---
    if channel_id and teaser_text:
        print("  -> [Channel] Sending teaser...")
        _send_message(channel_id, teaser_text)
    elif channel_id and not teaser_text:
        print("  -> [Channel] Skipped — no teaser text provided.")
    else:
        print("  -> [Channel] Skipped — TELEGRAM_CHANNEL_ID not set.")


def send_tweet_thread(tweets: list):
    """
    Send the 4-tweet thread to the private chat only,
    each tweet as a separate clearly labelled message.
    """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    sep     = "─" * 30
    header  = f"{sep}\n X THREAD — copy & post tweet by tweet:\n{sep}"

    print("  -> Sending thread header...")
    _send_message(chat_id, header)

    for i, tweet in enumerate(tweets, 1):
        msg = f"TWEET {i}/4\n\n{tweet}"
        print(f"  -> Sending tweet {i}/4...")
        _send_message(chat_id, msg)
