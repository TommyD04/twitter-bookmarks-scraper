import asyncio
import os
import sys

from scraper.cli import parse_args
from scraper.auth import login
from scraper.fetcher import fetch_bookmarks


async def main():
    config = parse_args()

    os.makedirs(config.output, exist_ok=True)

    try:
        client = await login(config)
    except Exception as e:
        print(f"Login failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        bookmarks = await fetch_bookmarks(client)
    except Exception as e:
        print(f"Failed to fetch bookmarks: {e}", file=sys.stderr)
        sys.exit(1)

    for bm in bookmarks:
        text = bm["text"]
        if len(text) > 140:
            text = text[:140] + "..."
        print(f"[@{bm['handle']}] {bm['created_at']}")
        print(text)
        print(f"Likes: {bm['likes']} | Retweets: {bm['retweets']} | Replies: {bm['replies']}")
        print(bm["url"])
        print("\u2500" * 40)

    print(f"\nFetched {len(bookmarks)} bookmarks from first page.")


if __name__ == "__main__":
    asyncio.run(main())
