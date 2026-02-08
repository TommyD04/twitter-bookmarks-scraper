import asyncio
import os

import httpx


class MediaDownloader:
    def __init__(self, output_dir: str):
        self.media_dir = os.path.join(output_dir, "media")
        os.makedirs(self.media_dir, exist_ok=True)
        self._downloaded = 0
        self._skipped = 0

    async def download_all(self, bookmarks, threads, on_progress=None):
        """Download media for all bookmarks and their thread parents."""
        # Collect all tweet dicts, deduplicate by tweet ID
        seen = set()
        all_tweets = []
        for bm in bookmarks:
            if bm["id"] not in seen:
                seen.add(bm["id"])
                all_tweets.append(bm)
        for thread in threads.values():
            for tweet in thread:
                if tweet["id"] not in seen:
                    seen.add(tweet["id"])
                    all_tweets.append(tweet)

        # Collect all media items
        items = []
        for tweet in all_tweets:
            for item in tweet.get("media_items", []):
                if item.get("url"):
                    items.append(item)

        total = len(items)
        for i, item in enumerate(items, 1):
            if on_progress:
                on_progress(i, total)
            await self._download_item(item)
            if i < total:
                await asyncio.sleep(0.5)

        return self._downloaded, self._skipped

    async def _download_item(self, item: dict) -> bool:
        """Download a single media item. Returns True if downloaded, False if skipped."""
        filepath = os.path.join(self.media_dir, item["filename"])
        if os.path.exists(filepath):
            self._skipped += 1
            return False

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.get(item["url"], follow_redirects=True)
                    resp.raise_for_status()
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                self._downloaded += 1
                return True
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.HTTPStatusError) as e:
                if attempt < 2:
                    wait = (attempt + 1) * 5
                    print(f"Download failed for {item['filename']}, retrying in {wait}s: {e}")
                    await asyncio.sleep(wait)
                else:
                    print(f"Download failed for {item['filename']} after 3 attempts, skipping: {e}")
                    return False
