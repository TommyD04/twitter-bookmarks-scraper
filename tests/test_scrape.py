import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.cli import Config


@pytest.mark.asyncio
async def test_end_to_end(tmp_path, capsys):
    output_dir = str(tmp_path / "bookmarks")

    mock_config = Config(
        output=output_dir,
        username="user1",
        email="e@mail.com",
        password="pass123",
    )

    mock_tweet = MagicMock()
    mock_tweet.id = "123"
    mock_tweet.text = "Test tweet"
    mock_tweet.user.name = "Test"
    mock_tweet.user.screen_name = "test"
    mock_tweet.created_at = "2024-03-15"
    mock_tweet.favorite_count = 10
    mock_tweet.retweet_count = 5
    mock_tweet.reply_count = 2
    mock_tweet.media = None
    mock_tweet.in_reply_to = None

    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()
    mock_client.get_bookmarks = AsyncMock(return_value=[mock_tweet])

    with patch("scraper.auth.Client", return_value=mock_client), \
         patch("scraper.cli.parse_args", return_value=mock_config):
        from scrape import main
        await main()

    assert os.path.isdir(output_dir)
    output = capsys.readouterr().out
    assert "[@test]" in output
    assert "Fetched 1 bookmarks from first page." in output
