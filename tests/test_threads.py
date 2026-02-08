import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.threads import ThreadResolver, _tweet_to_dict, _placeholder


def make_bookmark(**overrides):
    defaults = {
        "id": "100",
        "text": "Reply tweet",
        "author": "Test User (@testuser)",
        "handle": "testuser",
        "created_at": "2024-03-15",
        "likes": 10,
        "retweets": 5,
        "replies": 2,
        "url": "https://x.com/testuser/status/100",
        "has_media": False,
        "is_reply": True,
        "in_reply_to": "99",
    }
    defaults.update(overrides)
    return defaults


def make_mock_tweet(id="99", text="Parent tweet", name="Parent",
                    screen_name="parent", created_at="2024-03-14",
                    favorite_count=20, retweet_count=3, reply_count=1,
                    media=None, in_reply_to=None, reply_to=None):
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
    tweet.reply_to = reply_to
    return tweet


@pytest.mark.asyncio
async def test_non_reply_returns_single():
    client = MagicMock()
    resolver = ThreadResolver(client)
    bm = make_bookmark(in_reply_to=None, is_reply=False)

    result = await resolver.resolve(bm)

    assert result == [bm]
    client.get_tweet_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_reply_resolves_via_reply_to():
    root_tweet = make_mock_tweet(id="98", text="Root", in_reply_to=None)
    parent_tweet = make_mock_tweet(id="99", text="Parent", in_reply_to="98")

    # The bookmarked tweet object has reply_to with parent chain
    bookmark_tweet_obj = make_mock_tweet(
        id="100", text="Reply tweet",
        in_reply_to="99",
        reply_to=[root_tweet, parent_tweet],
    )

    client = MagicMock()
    client.get_tweet_by_id = AsyncMock(return_value=bookmark_tweet_obj)

    resolver = ThreadResolver(client)
    bm = make_bookmark()

    with patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock):
        result = await resolver.resolve(bm)

    assert len(result) == 3
    assert result[0]["id"] == "98"
    assert result[0]["text"] == "Root"
    assert result[1]["id"] == "99"
    assert result[1]["text"] == "Parent"
    assert result[2] == bm


@pytest.mark.asyncio
async def test_fallback_manual_walk():
    """When reply_to is empty, walk in_reply_to chain manually."""
    bookmark_tweet_obj = make_mock_tweet(
        id="100", text="Reply",
        in_reply_to="99",
        reply_to=[],  # empty — triggers fallback
    )
    parent_tweet_obj = make_mock_tweet(
        id="99", text="Parent",
        in_reply_to=None,
    )

    client = MagicMock()
    client.get_tweet_by_id = AsyncMock(side_effect=[bookmark_tweet_obj, parent_tweet_obj])

    resolver = ThreadResolver(client)
    bm = make_bookmark()

    with patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock):
        result = await resolver.resolve(bm)

    assert len(result) == 2
    assert result[0]["id"] == "99"
    assert result[1] == bm


@pytest.mark.asyncio
async def test_cache_hit():
    """Second resolve for same parent doesn't re-fetch."""
    root_tweet = make_mock_tweet(id="98", text="Root", in_reply_to=None)
    parent_tweet = make_mock_tweet(id="99", text="Parent", in_reply_to="98")

    tweet_obj = make_mock_tweet(
        id="100", reply_to=[root_tweet, parent_tweet], in_reply_to="99",
    )
    tweet_obj2 = make_mock_tweet(
        id="200", reply_to=[root_tweet, parent_tweet], in_reply_to="99",
    )

    client = MagicMock()
    client.get_tweet_by_id = AsyncMock(side_effect=[tweet_obj, tweet_obj2])

    resolver = ThreadResolver(client)
    bm1 = make_bookmark(id="100")
    bm2 = make_bookmark(id="200", url="https://x.com/testuser/status/200")

    with patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock):
        r1 = await resolver.resolve(bm1)
        r2 = await resolver.resolve(bm2)

    # Both resolved, parents came from cache on second call
    assert r1[0]["id"] == "98"
    assert r2[0]["id"] == "98"
    # Same dict objects from cache
    assert r1[0] is r2[0]


@pytest.mark.asyncio
async def test_deleted_parent_placeholder():
    from twikit.errors import TweetNotAvailable

    bookmark_tweet_obj = make_mock_tweet(
        id="100", text="Reply",
        in_reply_to="99",
        reply_to=[],  # fallback path
    )

    client = MagicMock()
    client.get_tweet_by_id = AsyncMock(
        side_effect=[bookmark_tweet_obj, TweetNotAvailable("gone")]
    )

    resolver = ThreadResolver(client)
    bm = make_bookmark()

    with patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock):
        result = await resolver.resolve(bm)

    assert len(result) == 2
    assert result[0]["text"] == "[Tweet unavailable]"
    assert result[0]["id"] == "99"
    assert result[1] == bm


@pytest.mark.asyncio
async def test_rate_limit_backoff():
    from twikit.errors import TooManyRequests

    reset_time = int(time.time()) + 10
    error = TooManyRequests("rate limited", headers={"x-rate-limit-reset": str(reset_time)})

    bookmark_tweet_obj = make_mock_tweet(
        id="100", reply_to=[], in_reply_to="99",
    )
    parent_tweet_obj = make_mock_tweet(id="99", in_reply_to=None)

    client = MagicMock()
    # First call succeeds (get bookmark tweet), second call (get parent) hits 429 then succeeds
    client.get_tweet_by_id = AsyncMock(
        side_effect=[bookmark_tweet_obj, error, parent_tweet_obj]
    )

    resolver = ThreadResolver(client)
    bm = make_bookmark()

    with patch("scraper.threads.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await resolver.resolve(bm)

    assert len(result) == 2
    # Verify backoff sleep was called
    sleep_args = [call.args[0] for call in mock_sleep.call_args_list]
    assert any(s > 2 for s in sleep_args)
