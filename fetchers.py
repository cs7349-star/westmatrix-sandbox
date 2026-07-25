from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from .normalize import normalize_record, utc_now

load_dotenv()

REQUEST_TIMEOUT = 20


def fetch_fred_series(series_id: str, metric_name: str, units: str, frequency: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return [normalize_record("FRED", utc_now(), series_id, metric_name, None, units, frequency, status="api_failure", message="missing_api_key")]
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 429:
            return [normalize_record("FRED", utc_now(), series_id, metric_name, None, units, frequency, status="rate_limited", message="rate_limited")]
        response.raise_for_status()
        payload = response.json()
        observations = payload.get("observations", [])
        if not observations:
            return [normalize_record("FRED", utc_now(), series_id, metric_name, None, units, frequency, status="api_failure", message="no_observations")]
        observation = observations[0]
        return [normalize_record("FRED", utc_now(), series_id, metric_name, observation.get("value"), units, frequency, provider_timestamp=observation.get("date"), status="success")]
    except Exception as exc:
        return [normalize_record("FRED", utc_now(), series_id, metric_name, None, units, frequency, status="api_failure", message=str(exc))]


def fetch_alpha_vantage_quote(ticker: str) -> List[Dict[str, Any]]:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return [normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", None, "USD", "daily", status="api_failure", message="missing_api_key")]
    url = "https://www.alphavantage.co/query"
    params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key}
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 429:
            return [normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", None, "USD", "daily", status="rate_limited", message="rate_limited")]
        response.raise_for_status()
        payload = response.json()
        if "Note" in payload or "Information" in payload:
            return [normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", None, "USD", "daily", status="rate_limited", message=payload.get("Note") or payload.get("Information"))]
        quote = payload.get("Global Quote", {})
        if not quote:
            return [normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", None, "USD", "daily", status="api_failure", message="empty_quote")]
        trade_date = quote.get("07. latest trading day")
        return [
            normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", quote.get("05. price"), "USD", "daily", trade_date, "success"),
            normalize_record("Alpha Vantage", utc_now(), ticker, "Previous Close", quote.get("08. previous close"), "USD", "daily", trade_date, "success"),
        ]
    except Exception as exc:
        return [normalize_record("Alpha Vantage", utc_now(), ticker, "Current Price", None, "USD", "daily", status="api_failure", message=str(exc))]


def fetch_yahoo_finance_quote(ticker: str) -> List[Dict[str, Any]]:
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.fast_info
        timestamp = datetime.now(timezone.utc).date().isoformat()
        records = [
            normalize_record("Yahoo Finance", utc_now(), ticker, "Current Price", getattr(info, "last_price", None), "USD", "daily", timestamp, "success"),
            normalize_record("Yahoo Finance", utc_now(), ticker, "Previous Close", getattr(info, "previous_close", None), "USD", "daily", timestamp, "success"),
            normalize_record("Yahoo Finance", utc_now(), ticker, "Market Cap", getattr(info, "market_cap", None), "USD", "daily", timestamp, "success"),
            normalize_record("Yahoo Finance", utc_now(), ticker, "52 Week High", getattr(info, "year_high", None), "USD", "daily", timestamp, "success"),
            normalize_record("Yahoo Finance", utc_now(), ticker, "52 Week Low", getattr(info, "year_low", None), "USD", "daily", timestamp, "success"),
        ]
        if all(record["metric_value"] is None for record in records):
            return [normalize_record("Yahoo Finance", utc_now(), ticker, "Current Price", None, "USD", "daily", status="api_failure", message="empty_quote")]
        return records
    except Exception as exc:
        message = str(exc)
        status = "rate_limited" if "429" in message or "Too Many Requests" in message else "api_failure"
        return [normalize_record("Yahoo Finance", utc_now(), ticker, "Current Price", None, "USD", "daily", status=status, message=message)]
