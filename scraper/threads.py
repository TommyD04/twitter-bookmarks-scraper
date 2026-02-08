import asyncio
import time

from twikit.errors import TooManyRequests, TweetNotAvailable


def _tweet_to_dict(tweet) -> dict:
    return {
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
    }


def _placeholder(tweet_id: str) -> dict:
    return {
        "id": tweet_id,
        "text": "[Tweet unavailable]",
        "author": "Unknown (@unknown)",
        "handle": "unknown",
        "created_at": "",
        "likes": 0,
        "retweets": 0,
        "replies": 0,
        "url": f"https://x.com/i/status/{tweet_id}",
        "has_media": False,
        "is_reply": False,
        "in_reply_to": None,
    }


async def _fetch_tweet_with_backoff(client, tweet_id: str):
    try:
        return await client.get_tweet_by_id(tweet_id)
    except TooManyRequests as e:
        wait_seconds = 60
        if e.rate_limit_reset is not None:
            wait_seconds = max(e.rate_limit_reset - int(time.time()), 1)
        print(f"Rate limited during thread resolution, waiting {wait_seconds}s...")
        await asyncio.sleep(wait_seconds)
        return await client.get_tweet_by_id(tweet_id)


class ThreadResolver:
    def __init__(self, client):
        self.client = client
        self._cache = {}  # tweet_id -> tweet dict

    async def resolve(self, bookmark: dict) -> list[dict]:
        """Returns ordered list of tweet dicts [root, ..., parent, bookmark].
        For non-replies, returns [bookmark]."""
        if bookmark["in_reply_to"] is None:
            return [bookmark]

        # Fetch the full tweet object to access .reply_to
        try:
            tweet_obj = await _fetch_tweet_with_backoff(self.client, bookmark["id"])
        except TweetNotAvailable:
            return [bookmark]

        parents = []

        # Primary: use .reply_to attribute (list of parent tweets from API)
        if hasattr(tweet_obj, "reply_to") and tweet_obj.reply_to:
            for parent_tweet in tweet_obj.reply_to:
                pid = parent_tweet.id
                if pid not in self._cache:
                    self._cache[pid] = _tweet_to_dict(parent_tweet)
                parents.append(self._cache[pid])
        else:
            # Fallback: walk in_reply_to chain manually
            current_reply_to = bookmark["in_reply_to"]
            while current_reply_to:
                if current_reply_to in self._cache:
                    parents.append(self._cache[current_reply_to])
                    # Continue walking from cached tweet's parent
                    current_reply_to = self._cache[current_reply_to].get("in_reply_to")
                    continue

                await asyncio.sleep(1)
                try:
                    parent_obj = await _fetch_tweet_with_backoff(self.client, current_reply_to)
                    parent_dict = _tweet_to_dict(parent_obj)
                    self._cache[current_reply_to] = parent_dict
                    parents.append(parent_dict)
                    current_reply_to = parent_obj.in_reply_to
                except TweetNotAvailable:
                    placeholder = _placeholder(current_reply_to)
                    self._cache[current_reply_to] = placeholder
                    parents.append(placeholder)
                    break

            parents.reverse()

        # Cache the bookmark itself
        self._cache[bookmark["id"]] = bookmark

        return parents + [bookmark]
