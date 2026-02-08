import importlib
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.cli import Config


def make_mock_result(tweets, next_result=None):
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter(tweets))
    result.next = AsyncMock(return_value=next_result)
    result.__bool__ = MagicMock(return_value=True)
    result.cursor = None
    return result


def make_mock_tweet(id="123", text="Test tweet", screen_name="test",
                    in_reply_to=None):
    mock_tweet = MagicMock()
    mock_tweet.id = id
    mock_tweet.text = text
    mock_tweet.user.name = "Test"
    mock_tweet.user.screen_name = screen_name
    mock_tweet.created_at = "2024-03-15"
    mock_tweet.favorite_count = 10
    mock_tweet.retweet_count = 5
    mock_tweet.reply_count = 2
    mock_tweet.media = None
    mock_tweet.in_reply_to = in_reply_to
    return mock_tweet


@pytest.mark.asyncio
async def test_end_to_end(tmp_path, capsys):
    output_dir = str(tmp_path / "bookmarks")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    mock_tweet = make_mock_tweet()
    mock_result = make_mock_result([mock_tweet], next_result=None)

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result)

    mock_downloader = MagicMock()
    mock_downloader.download_all = AsyncMock(return_value=(0, 0))

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        import scrape
        importlib.reload(scrape)
        await scrape.main()

    assert os.path.isdir(output_dir)

    # Verify markdown file was written
    md_file = os.path.join(output_dir, "@test-123.md")
    assert os.path.isfile(md_file)

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert content.startswith("---\n")
    assert 'handle: "test"' in content
    assert "Test tweet" in content
    assert "is_thread: false" in content

    output = capsys.readouterr().out
    assert "Done. 1 bookmarks saved to" in output


@pytest.mark.asyncio
async def test_end_to_end_with_thread(tmp_path, capsys):
    output_dir = str(tmp_path / "bookmarks")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    # A non-reply and a reply bookmark
    tweet_normal = make_mock_tweet(id="100", text="Normal tweet")
    tweet_reply = make_mock_tweet(id="200", text="Reply tweet", in_reply_to="199")
    mock_result = make_mock_result([tweet_normal, tweet_reply], next_result=None)

    # Mock the tweet object returned by get_tweet_by_id for thread resolution
    parent_tweet = make_mock_tweet(id="199", text="Parent tweet", in_reply_to=None)
    reply_tweet_obj = MagicMock()
    reply_tweet_obj.id = "200"
    reply_tweet_obj.reply_to = [parent_tweet]
    reply_tweet_obj.in_reply_to = "199"

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result)
    mock_client.get_tweet_by_id = AsyncMock(return_value=reply_tweet_obj)

    mock_downloader = MagicMock()
    mock_downloader.download_all = AsyncMock(return_value=(0, 0))

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        import scrape
        importlib.reload(scrape)
        await scrape.main()

    # Normal tweet: no thread
    normal_file = os.path.join(output_dir, "@test-100.md")
    with open(normal_file, "r", encoding="utf-8") as f:
        normal_content = f.read()
    assert "is_thread: false" in normal_content

    # Reply tweet: has thread sections
    reply_file = os.path.join(output_dir, "@test-200.md")
    with open(reply_file, "r", encoding="utf-8") as f:
        reply_content = f.read()
    assert "is_thread: true" in reply_content
    assert "thread_length: 2" in reply_content
    assert "## Tweet 1 of 2 (thread start)" in reply_content
    assert "## Tweet 2 of 2 (bookmarked)" in reply_content

    output = capsys.readouterr().out
    assert "Resolving thread 1/1" in output
    assert "Done. 2 bookmarks saved to" in output


@pytest.mark.asyncio
async def test_end_to_end_with_media(tmp_path, capsys):
    output_dir = str(tmp_path / "bookmarks")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    mock_photo = MagicMock()
    mock_photo.type = "photo"
    mock_photo.media_url = "https://pbs.twimg.com/photo.jpg"

    tweet = make_mock_tweet(id="300", text="Tweet with image")
    tweet.media = [mock_photo]

    mock_result = make_mock_result([tweet], next_result=None)

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result)

    mock_downloader = MagicMock()
    mock_downloader.download_all = AsyncMock(return_value=(1, 0))

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        import scrape
        importlib.reload(scrape)
        await scrape.main()

    md_file = os.path.join(output_dir, "@test-300.md")
    assert os.path.isfile(md_file)

    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "![image](media/300_0.jpg)" in content
    assert "Tweet with image" in content

    # Verify media downloader was called
    mock_downloader.download_all.assert_called_once()

    output = capsys.readouterr().out
    assert "Found 1 media items to download" in output
    assert "Downloaded 1 media files (0 already existed)" in output


@pytest.mark.asyncio
async def test_end_to_end_resumability(tmp_path, capsys):
    """Run once, then run again — second run skips already-scraped bookmarks."""
    output_dir = str(tmp_path / "bookmarks")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    mock_tweet = make_mock_tweet(id="123", text="Test tweet")
    mock_result = make_mock_result([mock_tweet], next_result=None)
    mock_result.cursor = "scroll:page1"

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result)

    mock_downloader = MagicMock()
    mock_downloader.download_all = AsyncMock(return_value=(0, 0))

    # First run
    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        import scrape
        importlib.reload(scrape)
        await scrape.main()

    # Verify manifest.json was created
    manifest_path = os.path.join(output_dir, "manifest.json")
    assert os.path.isfile(manifest_path)
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    assert "123" in manifest["scraped_ids"]

    capsys.readouterr()  # clear output

    # Second run — same tweet returned by API
    mock_result2 = make_mock_result([mock_tweet], next_result=None)
    mock_result2.cursor = "scroll:page1"
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result2)

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        importlib.reload(scrape)
        await scrape.main()

    output = capsys.readouterr().out
    assert "Skipped 1 existing markdown files" in output


@pytest.mark.asyncio
async def test_end_to_end_skip_existing_markdown(tmp_path, capsys):
    """Pre-create a markdown file; verify the scraper doesn't overwrite it."""
    output_dir = str(tmp_path / "bookmarks")
    os.makedirs(output_dir, exist_ok=True)

    # Pre-create the markdown file with custom content
    md_file = os.path.join(output_dir, "@test-123.md")
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("original content")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    mock_tweet = make_mock_tweet(id="123", text="Test tweet")
    mock_result = make_mock_result([mock_tweet], next_result=None)
    mock_result.cursor = "scroll:page1"

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=mock_result)

    mock_downloader = MagicMock()
    mock_downloader.download_all = AsyncMock(return_value=(0, 0))

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config), \
         patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock), \
         patch("scraper.media.MediaDownloader", return_value=mock_downloader):
        import scrape
        importlib.reload(scrape)
        await scrape.main()

    # Verify the file was NOT overwritten
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == "original content"

    output = capsys.readouterr().out
    assert "Skipped 1 existing markdown files" in output
