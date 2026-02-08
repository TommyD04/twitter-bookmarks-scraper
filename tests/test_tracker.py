import json
import os

from scraper.tracker import ProgressTracker


def test_load_no_manifest(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    assert tracker.get_cursor() is None
    assert tracker.is_scraped("123") is False


def test_save_and_load(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    tracker.mark_scraped("123")
    tracker.mark_scraped("456")
    tracker.save_cursor("scroll:abc123")
    tracker.save()

    tracker2 = ProgressTracker(str(tmp_path))
    tracker2.load()
    assert tracker2.is_scraped("123")
    assert tracker2.is_scraped("456")
    assert tracker2.get_cursor() == "scroll:abc123"


def test_is_scraped(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    assert tracker.is_scraped("999") is False
    tracker.mark_scraped("999")
    assert tracker.is_scraped("999") is True


def test_mark_scraped(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    tracker.mark_scraped("42")
    assert tracker.is_scraped("42") is True


def test_mark_scraped_idempotent(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    tracker.mark_scraped("42")
    tracker.mark_scraped("42")
    tracker.save()

    with open(os.path.join(str(tmp_path), "manifest.json"), "r") as f:
        data = json.load(f)
    assert data["scraped_ids"].count("42") == 1


def test_save_cursor_and_get_cursor(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    tracker.save_cursor("scroll:xyz789")
    tracker.save()

    tracker2 = ProgressTracker(str(tmp_path))
    tracker2.load()
    assert tracker2.get_cursor() == "scroll:xyz789"


def test_cursor_defaults_none(tmp_path):
    tracker = ProgressTracker(str(tmp_path))
    tracker.load()
    assert tracker.get_cursor() is None
