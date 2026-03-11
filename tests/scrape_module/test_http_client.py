"""Tests for scrape.http_client — delay and 429 retry behaviour."""
import time
from unittest.mock import MagicMock, call, patch

import pytest
import requests

from scrape.http_client import fetch


def _make_response(status_code: int, text: str = "ok", headers: dict = None):
    r = MagicMock(spec=requests.Response)
    r.status_code = status_code
    r.text = text
    r.headers = headers or {}
    if status_code >= 400:
        http_err = requests.exceptions.HTTPError(response=r)
        r.raise_for_status.side_effect = http_err
    else:
        r.raise_for_status.return_value = None
    return r


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_returns_text_on_success(mock_get, mock_sleep):
    mock_get.return_value = _make_response(200, text="<html/>")

    result = fetch("https://example.com/")

    assert result == "<html/>"


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_sleeps_before_request(mock_get, mock_sleep):
    """The fixed polite delay fires before the request is made."""
    mock_get.return_value = _make_response(200)

    call_order = []
    mock_sleep.side_effect = lambda _: call_order.append("sleep")
    mock_get.side_effect = lambda *a, **kw: call_order.append("get") or _make_response(200)

    fetch("https://example.com/")

    assert call_order[0] == "sleep"
    assert call_order[1] == "get"


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_retries_on_429_and_succeeds(mock_get, mock_sleep):
    """A single 429 causes one retry; success on the second attempt."""
    mock_get.side_effect = [
        _make_response(429, headers={"Retry-After": "5"}),
        _make_response(200, text="retried"),
    ]

    result = fetch("https://example.com/")

    assert result == "retried"
    assert mock_get.call_count == 2


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_logs_warning_on_429(mock_get, mock_sleep, caplog, capsys):
    """A 429 response emits a logger.warning and a printed message."""
    import logging
    mock_get.side_effect = [
        _make_response(429, headers={"Retry-After": "5"}),
        _make_response(200),
    ]

    with caplog.at_level(logging.WARNING, logger="scrape.http_client"):
        fetch("https://example.com/")

    assert any("429" in r.message and "example.com" in r.message for r in caplog.records)
    stdout = capsys.readouterr().out
    assert "429" in stdout
    assert "example.com" in stdout
    assert "Retry-After: 5" in stdout


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_honours_retry_after_header(mock_get, mock_sleep):
    """Waits exactly Retry-After + 1 second when the header is present."""
    mock_get.side_effect = [
        _make_response(429, headers={"Retry-After": "10"}),
        _make_response(200),
    ]

    fetch("https://example.com/")

    # sleep calls: initial delay + retry-after wait
    sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
    assert 11.0 in sleep_calls  # 10 + 1


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_uses_exponential_backoff_without_retry_after(mock_get, mock_sleep):
    """Falls back to exponential backoff (2^(attempt+1)) when no Retry-After."""
    mock_get.side_effect = [
        _make_response(429, headers={}),
        _make_response(200),
    ]

    fetch("https://example.com/")

    sleep_calls = [c.args[0] for c in mock_sleep.call_args_list]
    assert 2 in sleep_calls  # 2^(0+1) = 2


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_raises_after_max_retries(mock_get, mock_sleep):
    """After exhausting retries, raises the 429 HTTPError."""
    from shared.config import REQUEST_MAX_RETRIES

    mock_get.return_value = _make_response(429)

    with pytest.raises(requests.exceptions.HTTPError):
        fetch("https://example.com/")

    assert mock_get.call_count == REQUEST_MAX_RETRIES + 1


@patch("scrape.http_client.time.sleep")
@patch("scrape.http_client.requests.get")
def test_fetch_raises_immediately_on_404(mock_get, mock_sleep):
    """Non-429 errors are not retried — they raise immediately."""
    mock_get.return_value = _make_response(404)

    with pytest.raises(requests.exceptions.HTTPError):
        fetch("https://example.com/")

    assert mock_get.call_count == 1
