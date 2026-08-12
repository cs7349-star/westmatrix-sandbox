from unittest.mock import Mock, patch
import pandas as pd
import reliability_monitor as rm


def test_safe_float_valid():
    assert rm.safe_float("123.45") == 123.45


def test_safe_float_invalid():
    assert rm.safe_float("abc") is None


def test_fred_missing_key():
    with patch.object(rm, "FRED_API_KEY", None):
        result = rm.check_fred()
    assert result["status"] == "fail"
    assert "Missing FRED_API_KEY" in result["error_message"]


def test_fred_valid_response():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"observations": [{"value": "."}, {"value": "31000.5"}]}
    with patch.object(rm, "FRED_API_KEY", "test"), patch("reliability_monitor.requests.get", return_value=response):
        result = rm.check_fred()
    assert result["status"] == "success"
    assert result["returned_value"] == 31000.5


def test_alpha_vantage_rate_limit():
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"Note": "Rate limit reached"}
    with patch.object(rm, "ALPHA_VANTAGE_API_KEY", "test"), patch("reliability_monitor.requests.get", return_value=response):
        result = rm.check_alpha_vantage("NVDA")
    assert result["status"] == "fail"
    assert "rate limit" in result["error_message"].lower()


def test_yahoo_empty_data():
    ticker = Mock()
    ticker.history.return_value = pd.DataFrame()
    with patch("reliability_monitor.yf.Ticker", return_value=ticker):
        result = rm.check_yahoo("NVDA")
    assert result["status"] == "fail"


def test_summary_price_difference():
    rows = [
        {"provider": "Yahoo Finance", "timestamp": "2026-08-01T00:00:00+00:00", "status": "success", "response_time": "0.5", "returned_value": "100", "error_message": "", "symbol": "NVDA"},
        {"provider": "Alpha Vantage", "timestamp": "2026-08-01T00:00:01+00:00", "status": "success", "response_time": "0.7", "returned_value": "102", "error_message": "", "symbol": "NVDA"},
    ]
    report = rm.summarize(rows, "NVDA")
    assert report["price_difference"]["absolute_difference"] == 2.0
