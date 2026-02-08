import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.fetcher import fetch_bookmarks


def make_mock_tweet(id="123", text="Hello world", name="Test User",
                    screen_name="testuser", created_at="2024-03-15",
                    favorite_count=450, retweet_count=83, reply_count=12,
                    media=None, in_reply_to=None):
    tweet = MagicMock()
    tweet.id = id
    tweet.text = text
    tweet.user.name = name
    tweet.user.screen_name = screen_name
    tweet.created_at = created_at
    tweet.favorite_count = favorite_count
    tweet.retweet_count = retweet_count
    tweet.reply_count = reply_count
    tweet.media = media
    tweet.in_reply_to = in_reply_to
    return tweet


def make_mock_result(tweets, next_result=None):
    """Create a mock result object that is iterable and has .next()."""
    result = MagicMock()
    result.__iter__ = MagicMock(return_value=iter(tweets))
    result.next = AsyncMock(return_value=next_result)
    # Make bool(result) truthy
    result.__bool__ = MagicMock(return_value=True)
    return result


@pytest.mark.asyncio
async def test_fetch_bookmarks_converts_tweets():
    mock_tweets = [
        make_mock_tweet(),
        make_mock_tweet(id="456", text="Second tweet", screen_name="other",
                        media=[MagicMock(type="photo", media_url="https://example.com/photo.jpg")],
                        in_reply_to="789"),
    ]
    result = make_mock_result(mock_tweets, next_result=None)
    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock):
        bookmarks = await fetch_bookmarks(client)

    assert len(bookmarks) == 2
    assert bookmarks[0]["id"] == "123"
    assert bookmarks[0]["text"] == "Hello world"
    assert bookmarks[0]["author"] == "Test User (@testuser)"
    assert bookmarks[0]["url"] == "https://x.com/testuser/status/123"
    assert bookmarks[0]["has_media"] is False
    assert bookmarks[0]["is_reply"] is False

    assert bookmarks[0]["in_reply_to"] is None
    assert bookmarks[0]["media_items"] == []
    assert bookmarks[1]["has_media"] is True
    assert bookmarks[1]["is_reply"] is True
    assert bookmarks[1]["in_reply_to"] == "789"
    assert len(bookmarks[1]["media_items"]) == 1
    assert bookmarks[1]["media_items"][0]["type"] == "photo"


@pytest.mark.asyncio
async def test_fetch_bookmarks_empty():
    result = make_mock_result([], next_result=None)
    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock):
        bookmarks = await fetch_bookmarks(client)
    assert bookmarks == []


@pytest.mark.asyncio
async def test_fetch_bookmarks_pagination():
    page1_tweets = [make_mock_tweet(id="1"), make_mock_tweet(id="2")]
    page2_tweets = [make_mock_tweet(id="3")]

    page2_result = make_mock_result(page2_tweets, next_result=None)
    page1_result = make_mock_result(page1_tweets, next_result=page2_result)

    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=page1_result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock):
        bookmarks = await fetch_bookmarks(client)

    assert len(bookmarks) == 3
    assert [b["id"] for b in bookmarks] == ["1", "2", "3"]


@pytest.mark.asyncio
async def test_fetch_bookmarks_delay_between_pages():
    page2_result = make_mock_result([make_mock_tweet(id="2")], next_result=None)
    page1_result = make_mock_result([make_mock_tweet(id="1")], next_result=page2_result)

    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=page1_result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await fetch_bookmarks(client)

    # sleep(2) called at least once between pages
    sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
    assert 2 in sleep_args


@pytest.mark.asyncio
async def test_fetch_bookmarks_429_backoff():
    from twikit.errors import TooManyRequests

    page1_tweets = [make_mock_tweet(id="1")]
    page1_result = make_mock_result(page1_tweets)

    reset_time = int(time.time()) + 10
    error = TooManyRequests("rate limited", headers={"x-rate-limit-reset": str(reset_time)})

    page2_result = make_mock_result([make_mock_tweet(id="2")], next_result=None)
    # First .next() raises 429, second .next() succeeds
    page1_result.next = AsyncMock(side_effect=[error, page2_result])

    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=page1_result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        bookmarks = await fetch_bookmarks(client)

    assert len(bookmarks) == 2
    # Verify a sleep > 2 was called (the backoff sleep)
    sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
    assert any(s > 2 for s in sleep_args)


@pytest.mark.asyncio
async def test_fetch_bookmarks_progress_callback():
    page2_result = make_mock_result([make_mock_tweet(id="2")], next_result=None)
    page1_result = make_mock_result([make_mock_tweet(id="1")], next_result=page2_result)

    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=page1_result)

    progress_counts = []

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock):
        await fetch_bookmarks(client, on_progress=lambda n: progress_counts.append(n))

    assert progress_counts == [1, 2]


@pytest.mark.asyncio
async def test_media_items_extracted():
    """Verify media_items field is present and correctly structured."""
    mock_photo = MagicMock()
    mock_photo.type = "photo"
    mock_photo.media_url = "https://pbs.twimg.com/media/photo1.jpg"

    mock_video = MagicMock()
    mock_video.type = "video"
    mock_stream = MagicMock()
    mock_stream.url = "https://video.twimg.com/vid.mp4"
    mock_video.streams = [mock_stream]

    tweet = make_mock_tweet(id="500", media=[mock_photo, mock_video])
    result = make_mock_result([tweet], next_result=None)
    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=result)

    with patch("scraper.fetcher.asyncio.sleep", new_callable=AsyncMock):
        bookmarks = await fetch_bookmarks(client)

    items = bookmarks[0]["media_items"]
    assert len(items) == 2

    assert items[0]["type"] == "photo"
    assert items[0]["url"] == "https://pbs.twimg.com/media/photo1.jpg"
    assert items[0]["filename"] == "500_0.jpg"

    assert items[1]["type"] == "video"
    assert items[1]["url"] == "https://video.twimg.com/vid.mp4"
    assert items[1]["filename"] == "500_1.mp4"
