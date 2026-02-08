import json
import os


class ProgressTracker:
    def __init__(self, output_dir: str):
        self._path = os.path.join(output_dir, "manifest.json")
        self._scraped_ids: set[str] = set()
        self._cursor: str | None = None

    def load(self):
        if os.path.isfile(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._scraped_ids = set(data.get("scraped_ids", []))
            self._cursor = data.get("cursor")
        else:
            self._scraped_ids = set()
            self._cursor = None

    def is_scraped(self, tweet_id: str) -> bool:
        return tweet_id in self._scraped_ids

    def mark_scraped(self, tweet_id: str):
        self._scraped_ids.add(tweet_id)

    def save_cursor(self, cursor: str | None):
        self._cursor = cursor

    def get_cursor(self) -> str | None:
        return self._cursor

    def save(self):
        data = {
            "scraped_ids": sorted(self._scraped_ids),
            "cursor": self._cursor,
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
