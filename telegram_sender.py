"""
telegram_sender.py
Sends the BTC chart image, analysis text, and tweet draft to Telegram.
"""

import os
import requests


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"
MAX_CAPTION  = 1024
MAX_MESSAGE  = 4096


def _url(method: str) -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    return TELEGRAM_API.format(token=token, method=method)


def _send_photo(chat_id: str, photo_path: str):
    with open(photo_path, "rb") as f:
        resp = requests.post(
            _url("sendPhoto"),
            data={"chat_id": chat_id},
            files={"photo": f},
            timeout=30,
        )
    resp.raise_for_status()


def _send_message(chat_id: str, text: str):
    chunks = [text[i : i + MAX_MESSAGE] for i in range(0, len(text), MAX_MESSAGE)]
    for chunk in chunks:
        resp = requests.post(
            _url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        resp.raise_for_status()


def send_analysis(chart_path: str, analysis_text: str):
    """Send chart image + full analysis."""
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")
    if not chat_id:
        raise EnvironmentError("TELEGRAM_CHAT_ID is not set.")

    print("  -> Sending chart image...")
    _send_photo(chat_id, chart_path)

    print("  -> Sending analysis text...")
    _send_message(chat_id, analysis_text)

    print("  -> Telegram delivery complete.")


def send_tweet_draft(tweet_text: str):
    """Send the ready-to-post tweet as a separate Telegram message."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    separator = "─" * 30
    message   = f"{separator}\n🐦 TWEET DRAFT — copy & post on X/Twitter:\n{separator}\n\n{tweet_text}"

    print("  -> Sending tweet draft...")
    _send_message(chat_id, message)

