import asyncio
import os
import sys

from scraper.cli import parse_args
from scraper.auth import login
from scraper.fetcher import fetch_bookmarks
from scraper.media import MediaDownloader
from scraper.renderer import render_bookmark, bookmark_filename
from scraper.threads import ThreadResolver
from scraper.tracker import ProgressTracker


async def main():
    config = parse_args()

    os.makedirs(config.output, exist_ok=True)

    tracker = ProgressTracker(config.output)
    tracker.load()

    try:
        client = await login(config)
    except Exception as e:
        print(f"Login failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        bookmarks = await fetch_bookmarks(client, tracker=tracker)
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

    # Download media
    downloader = MediaDownloader(config.output)
    media_count = sum(
        len(bm.get("media_items", [])) for bm in bookmarks
    ) + sum(
        len(t.get("media_items", []))
        for thread in threads.values()
        for t in thread
    )
    if media_count:
        print(f"Found {media_count} media items to download")
        downloaded, skipped = await downloader.download_all(
            bookmarks, threads,
            on_progress=lambda i, total: (
                print(f"Downloading media {i}/{total}...")
                if i % 10 == 0 or i == total else None
            ),
        )
        print(f"Downloaded {downloaded} media files ({skipped} already existed)")

    total = len(bookmarks)
    skipped_md = 0
    written = 0
    for i, bm in enumerate(bookmarks, 1):
        if tracker.is_scraped(bm["id"]):
            skipped_md += 1
            continue
        filename = bookmark_filename(bm)
        filepath = os.path.join(config.output, filename)
        if os.path.isfile(filepath):
            skipped_md += 1
            tracker.mark_scraped(bm["id"])
            continue
        md = render_bookmark(bm, thread=threads.get(bm["id"]))
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)
        tracker.mark_scraped(bm["id"])
        written += 1
        if written % 10 == 0 or i == total:
            print(f"Writing {i}/{total} markdown files...")

    if skipped_md:
        print(f"Skipped {skipped_md} existing markdown files")

    tracker.save()
    print(f"Done. {total} bookmarks saved to {config.output}/")


if __name__ == "__main__":
    asyncio.run(main())
