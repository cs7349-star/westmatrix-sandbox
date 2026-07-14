"""West Matrix connectivity verification script.

This script verifies that the local sandbox can connect to FRED, Yahoo Finance,
and Alpha Vantage. It prints a JSON status report instead of crashing if one
service is temporarily unavailable or an API key is missing.
"""

from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from typing import Any, Dict

import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_fred() -> Dict[str, Any]:
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return {
            "status": "missing_api_key",
            "message": "Set FRED_API_KEY in the .env file before running this check.",
        }

    try:
        response = requests.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": "GDP",
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        obs = data.get("observations", [{}])[0]
        return {
            "status": "success",
            "provider": "FRED",
            "series_id": "GDP",
            "latest_observation": {"date": obs.get("date"), "value": obs.get("value")},
        }
    except Exception as exc:
        return {"status": "error", "provider": "FRED", "message": str(exc)}


def check_yahoo_finance(symbol: str = "NVDA") -> Dict[str, Any]:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if hist.empty:
            raise RuntimeError("No Yahoo Finance price history returned.")
        latest_close = float(hist["Close"].dropna().iloc[-1])
        return {
            "status": "success",
            "provider": "Yahoo Finance",
            "symbol": symbol,
            "latest_close": latest_close,
        }
    except Exception as exc:
        return {"status": "error", "provider": "Yahoo Finance", "message": str(exc)}


def check_alpha_vantage(symbol: str = "NVDA") -> Dict[str, Any]:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {
            "status": "missing_api_key",
            "message": "Set ALPHA_VANTAGE_API_KEY in the .env file before running this check.",
        }

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        quote = data.get("Global Quote", {})
        if not quote:
            return {"status": "error", "provider": "Alpha Vantage", "message": data}
        return {
            "status": "success",
            "provider": "Alpha Vantage",
            "symbol": quote.get("01. symbol", symbol),
            "price": quote.get("05. price"),
            "trading_day": quote.get("07. latest trading day"),
        }
    except Exception as exc:
        return {"status": "error", "provider": "Alpha Vantage", "message": str(exc)}


def main() -> None:
    result = {
        "project": "West Matrix Local Sandbox",
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "timestamp_utc": utc_now(),
        },
        "checks": {
            "fred": check_fred(),
            "yahoo_finance": check_yahoo_finance(),
            "alpha_vantage": check_alpha_vantage(),
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
