"""
twitter_poster.py
Posts the BTC chart + tweet to Twitter/X using Tweepy.
Uses v1.1 API for media upload and v2 for posting the tweet.
"""

import os
import tweepy


def post_to_twitter(chart_path: str, tweet_text: str):
    """
    Upload the chart image and post the tweet.

    Args:
        chart_path: Path to the PNG chart file
        tweet_text: Full tweet string (max 280 chars)
    """
    api_key      = os.getenv("TWITTER_API_KEY")
    api_secret   = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        raise EnvironmentError("One or more TWITTER_* environment variables are missing.")

    # v1.1 API — needed for media upload
    auth  = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
    api_v1 = tweepy.API(auth)

    print("  -> Uploading chart to Twitter...")
    media = api_v1.media_upload(filename=chart_path)

    # v2 Client — for posting the tweet
    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_secret
    )

    print("  -> Posting tweet...")
    response = client.create_tweet(
        text=tweet_text,
        media_ids=[media.media_id]
    )

    tweet_id = response.data["id"]
    print(f"  -> Tweet posted: https://x.com/i/web/status/{tweet_id}")
    return tweet_id
