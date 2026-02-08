import asyncio
import os
import sys

from scraper.cli import parse_args
from scraper.auth import login
from scraper.fetcher import fetch_bookmarks
from scraper.renderer import render_bookmark, bookmark_filename
from scraper.threads import ThreadResolver


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

    # Resolve threads for reply bookmarks
    replies = [bm for bm in bookmarks if bm.get("in_reply_to")]
    threads = {}
    if replies:
        resolver = ThreadResolver(client)
        for i, bm in enumerate(replies, 1):
            print(f"Resolving thread {i}/{len(replies)}...")
            try:
                threads[bm["id"]] = await resolver.resolve(bm)
            except Exception as e:
                print(f"Warning: thread resolution failed for {bm['id']}: {e}")

    total = len(bookmarks)
    for i, bm in enumerate(bookmarks, 1):
        md = render_bookmark(bm, thread=threads.get(bm["id"]))
        filename = bookmark_filename(bm)
        filepath = os.path.join(config.output, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        if i % 10 == 0 or i == total:
            print(f"Writing {i}/{total} markdown files...")

    print(f"Done. {total} bookmarks saved to {config.output}/")


if __name__ == "__main__":
    asyncio.run(main())
