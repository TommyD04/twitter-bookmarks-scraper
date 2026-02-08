import os
from unittest.mock import AsyncMock, patch

import pytest

from scraper.media import MediaDownloader


def make_bookmark(id="123", media_items=None):
    return {
        "id": id,
        "text": "Hello",
        "author": "Test (@test)",
        "handle": "test",
        "created_at": "2024-03-15",
        "likes": 10,
        "retweets": 5,
        "replies": 2,
        "url": f"https://x.com/test/status/{id}",
        "has_media": bool(media_items),
        "is_reply": False,
        "in_reply_to": None,
        "media_items": media_items or [],
    }


def make_media_item(tweet_id="123", index=0, type="photo"):
    ext = "jpg" if type == "photo" else "mp4"
    return {
        "type": type,
        "url": f"https://pbs.twimg.com/{tweet_id}_{index}.{ext}",
        "filename": f"{tweet_id}_{index}.{ext}",
    }


def test_download_creates_media_dir(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    MediaDownloader(output_dir)
    assert os.path.isdir(os.path.join(output_dir, "media"))


@pytest.mark.asyncio
async def test_download_photo(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    downloader = MediaDownloader(output_dir)

    item = make_media_item(type="photo")
    bm = make_bookmark(media_items=[item])

    mock_resp = AsyncMock()
    mock_resp.content = b"fake-image-data"
    mock_resp.raise_for_status = lambda: None

    with patch("scraper.media.httpx.AsyncClient") as mock_client_cls, \
         patch("scraper.media.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        downloaded, skipped = await downloader.download_all([bm], {})

    assert downloaded == 1
    assert skipped == 0
    assert os.path.isfile(os.path.join(output_dir, "media", "123_0.jpg"))


@pytest.mark.asyncio
async def test_download_video(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    downloader = MediaDownloader(output_dir)

    item = make_media_item(type="video")
    bm = make_bookmark(media_items=[item])

    mock_resp = AsyncMock()
    mock_resp.content = b"fake-video-data"
    mock_resp.raise_for_status = lambda: None

    with patch("scraper.media.httpx.AsyncClient") as mock_client_cls, \
         patch("scraper.media.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        downloaded, skipped = await downloader.download_all([bm], {})

    assert downloaded == 1
    assert skipped == 0
    assert os.path.isfile(os.path.join(output_dir, "media", "123_0.mp4"))


@pytest.mark.asyncio
async def test_skip_existing(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    downloader = MediaDownloader(output_dir)

    # Pre-create the file
    filepath = os.path.join(output_dir, "media", "123_0.jpg")
    with open(filepath, "wb") as f:
        f.write(b"existing")

    item = make_media_item(type="photo")
    bm = make_bookmark(media_items=[item])

    with patch("scraper.media.asyncio.sleep", new_callable=AsyncMock):
        downloaded, skipped = await downloader.download_all([bm], {})

    assert downloaded == 0
    assert skipped == 1
    # File content unchanged
    with open(filepath, "rb") as f:
        assert f.read() == b"existing"


@pytest.mark.asyncio
async def test_download_deduplicates_across_threads(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    downloader = MediaDownloader(output_dir)

    item = make_media_item(tweet_id="999", type="photo")
    shared_tweet = make_bookmark(id="999", media_items=[item])

    # Same tweet appears in two thread chains and in bookmarks
    threads = {
        "a": [shared_tweet, make_bookmark(id="a")],
        "b": [shared_tweet, make_bookmark(id="b")],
    }

    mock_resp = AsyncMock()
    mock_resp.content = b"image-data"
    mock_resp.raise_for_status = lambda: None

    with patch("scraper.media.httpx.AsyncClient") as mock_client_cls, \
         patch("scraper.media.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        downloaded, skipped = await downloader.download_all([shared_tweet], threads)

    # Only downloaded once despite appearing in multiple places
    assert downloaded == 1


@pytest.mark.asyncio
async def test_download_progress_callback(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir)
    downloader = MediaDownloader(output_dir)

    items = [make_media_item(index=0), make_media_item(index=1)]
    bm = make_bookmark(media_items=items)

    mock_resp = AsyncMock()
    mock_resp.content = b"data"
    mock_resp.raise_for_status = lambda: None

    progress_calls = []

    with patch("scraper.media.httpx.AsyncClient") as mock_client_cls, \
         patch("scraper.media.asyncio.sleep", new_callable=AsyncMock):
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await downloader.download_all(
            [bm], {},
            on_progress=lambda i, total: progress_calls.append((i, total)),
        )

    assert progress_calls == [(1, 2), (2, 2)]
