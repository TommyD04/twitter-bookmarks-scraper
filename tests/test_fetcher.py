from unittest.mock import AsyncMock, MagicMock

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


@pytest.mark.asyncio
async def test_fetch_bookmarks_converts_tweets():
    mock_tweets = [
        make_mock_tweet(),
        make_mock_tweet(id="456", text="Second tweet", screen_name="other",
                        media=[{"type": "photo"}], in_reply_to="789"),
    ]
    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=mock_tweets)

    result = await fetch_bookmarks(client)

    assert len(result) == 2
    assert result[0]["id"] == "123"
    assert result[0]["text"] == "Hello world"
    assert result[0]["author"] == "Test User (@testuser)"
    assert result[0]["url"] == "https://x.com/testuser/status/123"
    assert result[0]["has_media"] is False
    assert result[0]["is_reply"] is False

    assert result[1]["has_media"] is True
    assert result[1]["is_reply"] is True


@pytest.mark.asyncio
async def test_fetch_bookmarks_empty():
    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=[])

    result = await fetch_bookmarks(client)
    assert result == []


@pytest.mark.asyncio
async def test_fetch_bookmarks_no_pagination():
    mock_tweets = MagicMock()
    mock_tweets.__iter__ = MagicMock(return_value=iter([make_mock_tweet()]))
    mock_tweets.next = AsyncMock()

    client = MagicMock()
    client.get_bookmarks = AsyncMock(return_value=mock_tweets)

    await fetch_bookmarks(client)

    mock_tweets.next.assert_not_called()
