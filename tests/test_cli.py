import pytest
from scraper.cli import parse_args


def test_output_required():
    with pytest.raises(SystemExit):
        parse_args([])


def test_all_args_provided():
    config = parse_args([
        "--output", "./out",
        "--username", "user1",
        "--email", "e@mail.com",
        "--password", "pass123",
    ])
    assert config.output == "./out"
    assert config.username == "user1"
    assert config.email == "e@mail.com"
    assert config.password == "pass123"


def test_missing_credentials_prompts(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "prompted_value")
    monkeypatch.setattr("getpass.getpass", lambda _: "prompted_pass")

    config = parse_args(["--output", "./out"])
    assert config.username == "prompted_value"
    assert config.email == "prompted_value"
    assert config.password == "prompted_pass"
