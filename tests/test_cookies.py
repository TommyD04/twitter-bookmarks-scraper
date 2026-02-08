import json

import pytest

from scraper.cookies import load_browser_cookies


def test_parse_netscape_cookies_txt(tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        ".twitter.com\tTRUE\t/\tTRUE\t0\tauth_token\tabc123\n"
        ".twitter.com\tTRUE\t/\tTRUE\t0\tct0\txyz789\n"
    )
    result = load_browser_cookies(str(cookie_file))
    assert result == {"auth_token": "abc123", "ct0": "xyz789"}


def test_parse_netscape_skips_comments(tmp_path):
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        "# comment line\n"
        ".twitter.com\tTRUE\t/\tTRUE\t0\tauth_token\tabc123\n"
    )
    result = load_browser_cookies(str(cookie_file))
    assert result == {"auth_token": "abc123"}


def test_parse_browser_json(tmp_path):
    cookie_file = tmp_path / "cookies.json"
    data = [
        {"name": "auth_token", "value": "abc123", "domain": ".twitter.com"},
        {"name": "ct0", "value": "xyz789", "domain": ".twitter.com"},
    ]
    cookie_file.write_text(json.dumps(data))
    result = load_browser_cookies(str(cookie_file))
    assert result == {"auth_token": "abc123", "ct0": "xyz789"}


def test_auto_detects_format(tmp_path):
    # JSON input
    json_file = tmp_path / "cookies.json"
    json_file.write_text(json.dumps([{"name": "a", "value": "1"}]))
    assert load_browser_cookies(str(json_file)) == {"a": "1"}

    # Netscape input
    txt_file = tmp_path / "cookies.txt"
    txt_file.write_text(".x.com\tTRUE\t/\tTRUE\t0\tb\t2\n")
    assert load_browser_cookies(str(txt_file)) == {"b": "2"}


def test_invalid_file_raises(tmp_path):
    # Non-existent file
    with pytest.raises(FileNotFoundError):
        load_browser_cookies(str(tmp_path / "nope.txt"))

    # Malformed content (no valid cookies)
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("just some random text\n")
    with pytest.raises(ValueError, match="No cookies found"):
        load_browser_cookies(str(bad_file))

    # Malformed JSON
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("[{bad json")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_browser_cookies(str(bad_json))
