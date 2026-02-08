import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.auth import login
from scraper.cli import Config


@pytest.fixture
def config(tmp_path):
    return Config(
        output=str(tmp_path),
        username="user1",
        email="e@mail.com",
        password="pass123",
    )


@pytest.mark.asyncio
async def test_login_no_cookies(config, capsys):
    mock_client = MagicMock()
    mock_client.login = AsyncMock()
    mock_client.save_cookies = MagicMock()

    with patch("scraper.auth.Client", return_value=mock_client):
        client = await login(config)

    mock_client.login.assert_called_once_with(
        auth_info_1="user1",
        auth_info_2="e@mail.com",
        password="pass123",
    )
    cookies_path = os.path.join(config.output, "cookies.json")
    mock_client.save_cookies.assert_called_once_with(cookies_path)
    assert client is mock_client
    assert "Logging in..." in capsys.readouterr().out


@pytest.mark.asyncio
async def test_login_with_existing_cookies(config, capsys):
    cookies_path = os.path.join(config.output, "cookies.json")
    with open(cookies_path, "w") as f:
        f.write("{}")

    mock_client = MagicMock()
    mock_client.load_cookies = MagicMock()

    with patch("scraper.auth.Client", return_value=mock_client):
        client = await login(config)

    mock_client.load_cookies.assert_called_once_with(cookies_path)
    mock_client.login.assert_not_called() if hasattr(mock_client, "login") else None
    assert "Using saved session..." in capsys.readouterr().out
