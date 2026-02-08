import asyncio
import time
from typing import Callable

from twikit.errors import TooManyRequests


def _extract_tweets(result) -> list[dict]:
    bookmarks = []
    for tweet in result:
        bookmarks.append({
            "id": tweet.id,
            "text": tweet.text,
            "author": f"{tweet.user.name} (@{tweet.user.screen_name})",
            "handle": tweet.user.screen_name,
            "created_at": tweet.created_at,
            "likes": tweet.favorite_count,
            "retweets": tweet.retweet_count,
            "replies": tweet.reply_count,
            "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
            "has_media": bool(tweet.media),
            "is_reply": tweet.in_reply_to is not None,
            "in_reply_to": tweet.in_reply_to,
        })
    return bookmarks


async def fetch_bookmarks(client, on_progress: Callable[[int], None] | None = None) -> list[dict]:
    result = await client.get_bookmarks(count=20)

    bookmarks = _extract_tweets(result)
    if on_progress:
        on_progress(len(bookmarks))
    print(f"Fetched {len(bookmarks)} bookmarks so far...")

    while True:
        await asyncio.sleep(2)
        try:
            next_result = await result.next()
        except TooManyRequests as e:
            wait_seconds = 60
            if e.rate_limit_reset is not None:
                wait_seconds = max(e.rate_limit_reset - int(time.time()), 1)
            print(f"Rate limited, waiting {wait_seconds}s...")
            await asyncio.sleep(wait_seconds)
            next_result = await result.next()

        if not next_result:
            break

        result = next_result
        new_tweets = _extract_tweets(result)
        if not new_tweets:
            break

        bookmarks.extend(new_tweets)
        if on_progress:
            on_progress(len(bookmarks))
        print(f"Fetched {len(bookmarks)} bookmarks so far...")

    return bookmarks
