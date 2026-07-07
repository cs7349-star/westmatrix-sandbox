"""
West Matrix sandbox connectivity verification script.

Purpose:
- Confirm that the local Python environment is working.
- Confirm access to external macroeconomic and financial data sources.
- Print a standard JSON result that can be submitted as proof of setup.

Services tested:
1. FRED API
2. Yahoo Finance via yfinance
3. Alpha Vantage API

Before running:
- Create a .env file based on .env.example.
- Add FRED_API_KEY and ALPHA_VANTAGE_API_KEY.
"""

from __future__ import annotations

import json
import os
import platform
from datetime import datetime, timezone
from typing import Any, Dict

import requests
import yfinance as yf
from dotenv import load_dotenv


REQUEST_TIMEOUT_SECONDS = 20


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def build_result(status: str, **kwargs: Any) -> Dict[str, Any]:
    """Small helper to standardize JSON result objects."""
    result = {"status": status}
    result.update(kwargs)
    return result


def check_fred() -> Dict[str, Any]:
    """Verify FRED API connectivity using the GDP series."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_fred_api_key_here":
        return build_result(
            "missing_api_key",
            message="Set FRED_API_KEY in the .env file before running this check.",
        )

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "GDP",
        "api_key": api_key,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        observations = data.get("observations", [])
        if not observations:
            return build_result("error", message="FRED returned no observations.")

        latest = observations[0]
        return build_result(
            "success",
            provider="FRED",
            series_id="GDP",
            latest_observation={
                "date": latest.get("date"),
                "value": latest.get("value"),
            },
        )
    except requests.RequestException as exc:
        return build_result("error", provider="FRED", message=str(exc))
    except ValueError as exc:
        return build_result("error", provider="FRED", message=f"Invalid JSON response: {exc}")


def check_yahoo_finance() -> Dict[str, Any]:
    """Verify Yahoo Finance connectivity using Microsoft ticker history."""
    symbol = "MSFT"
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period="5d")

        if history.empty:
            return build_result("error", provider="Yahoo Finance", message="No price history returned.")

        latest_row = history.tail(1).iloc[0]
        latest_index = history.tail(1).index[0]

        return build_result(
            "success",
            provider="Yahoo Finance",
            symbol=symbol,
            latest_date=str(latest_index.date()) if hasattr(latest_index, "date") else str(latest_index),
            latest_close=round(float(latest_row["Close"]), 4),
        )
    except Exception as exc:  # yfinance can raise different exception types depending on network/data issue.
        return build_result("error", provider="Yahoo Finance", message=str(exc))


def check_alpha_vantage() -> Dict[str, Any]:
    """Verify Alpha Vantage API connectivity using IBM global quote."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key or api_key == "your_alpha_vantage_key_here":
        return build_result(
            "missing_api_key",
            message="Set ALPHA_VANTAGE_API_KEY in the .env file before running this check.",
        )

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": "IBM",
        "apikey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

        if "Note" in data:
            return build_result("rate_limited", provider="Alpha Vantage", message=data["Note"])

        if "Error Message" in data:
            return build_result("error", provider="Alpha Vantage", message=data["Error Message"])

        quote = data.get("Global Quote", {})
        if not quote:
            return build_result("error", provider="Alpha Vantage", message="No Global Quote returned.")

        return build_result(
            "success",
            provider="Alpha Vantage",
            symbol=quote.get("01. symbol", "IBM"),
            price=quote.get("05. price"),
            trading_day=quote.get("07. latest trading day"),
        )
    except requests.RequestException as exc:
        return build_result("error", provider="Alpha Vantage", message=str(exc))
    except ValueError as exc:
        return build_result("error", provider="Alpha Vantage", message=f"Invalid JSON response: {exc}")


def main() -> None:
    """Run all checks and print a single JSON object."""
    load_dotenv()

    output = {
        "project": "West Matrix Local Sandbox",
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "timestamp_utc": utc_now_iso(),
        },
        "checks": {
            "fred": check_fred(),
            "yahoo_finance": check_yahoo_finance(),
            "alpha_vantage": check_alpha_vantage(),
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
