"""Data standardization and financial snapshot pipeline for West Matrix.

This script fetches data from three external sources:
1. FRED macroeconomic API
2. Yahoo Finance through yfinance
3. Alpha Vantage market data API

It then converts each API response into a common JSON schema and exports both
JSON and CSV output files for downstream applications or AI models.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests
import yfinance as yf
from dotenv import load_dotenv

# Load local secrets from .env. The .env file should never be committed.
load_dotenv()

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

SCHEMA_FIELDS = [
    "data_source",
    "timestamp",
    "symbol",
    "metric_name",
    "metric_value",
    "units",
    "frequency",
]


def utc_now() -> str:
    """Return the current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def to_float(value: Any) -> Optional[float]:
    """Safely convert API strings/numbers into floats."""
    if value in (None, "", "."):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_record(
    data_source: str,
    timestamp: str,
    symbol: Optional[str],
    metric_name: str,
    metric_value: Any,
    units: str,
    frequency: str,
) -> Dict[str, Any]:
    """Create one standardized observation.

    The goal is to turn very different API response formats into a single
    predictable schema that can be consumed by analytics code or AI models.
    """
    return {
        "data_source": data_source,
        "timestamp": timestamp,
        "symbol": symbol,
        "metric_name": metric_name,
        "metric_value": to_float(metric_value),
        "units": units,
        "frequency": frequency,
    }


def fetch_fred_latest(
    series_id: str,
    metric_name: str,
    units: str,
    frequency: str,
) -> Dict[str, Any]:
    """Fetch the most recent observation for a FRED series."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("Missing FRED_API_KEY. Add it to your local .env file.")

    response = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    observations = data.get("observations", [])
    if not observations:
        raise RuntimeError(f"No observations returned for FRED series {series_id}.")

    latest = observations[0]
    return normalize_record(
        data_source="FRED",
        timestamp=latest.get("date"),
        symbol=series_id,
        metric_name=metric_name,
        metric_value=latest.get("value"),
        units=units,
        frequency=frequency,
    )


def fetch_alpha_vantage_quote(symbol: str) -> List[Dict[str, Any]]:
    """Fetch latest quote data from Alpha Vantage and normalize it."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing ALPHA_VANTAGE_API_KEY. Add it to your local .env file.")

    response = requests.get(
        "https://www.alphavantage.co/query",
        params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    quote = data.get("Global Quote", {})
    if not quote:
        raise RuntimeError(f"Alpha Vantage did not return quote data: {data}")

    trade_date = quote.get("07. latest trading day", utc_now())
    return [
        normalize_record(
            "Alpha Vantage",
            trade_date,
            symbol,
            "Latest Trading Price",
            quote.get("05. price"),
            "USD",
            "daily",
        ),
        normalize_record(
            "Alpha Vantage",
            trade_date,
            symbol,
            "Previous Close",
            quote.get("08. previous close"),
            "USD",
            "daily",
        ),
        normalize_record(
            "Alpha Vantage",
            trade_date,
            symbol,
            "Trading Volume",
            quote.get("06. volume"),
            "Shares",
            "daily",
        ),
    ]


def safe_fast_info_value(fast_info: Any, key: str) -> Any:
    """Read yfinance fast_info values across dict/object variants."""
    try:
        if isinstance(fast_info, dict):
            return fast_info.get(key)
        return getattr(fast_info, key)
    except Exception:
        return None


def fetch_yahoo_snapshot(symbol: str) -> List[Dict[str, Any]]:
    """Fetch stock snapshot fields from Yahoo Finance and normalize them."""
    ticker = yf.Ticker(symbol)
    fast_info = ticker.fast_info
    timestamp = utc_now()

    fields = [
        ("Current Stock Price", safe_fast_info_value(fast_info, "last_price"), "USD"),
        ("Previous Close", safe_fast_info_value(fast_info, "previous_close"), "USD"),
        ("Market Capitalization", safe_fast_info_value(fast_info, "market_cap"), "USD"),
        ("52 Week High", safe_fast_info_value(fast_info, "year_high"), "USD"),
        ("52 Week Low", safe_fast_info_value(fast_info, "year_low"), "USD"),
    ]

    records = []
    for metric_name, value, units in fields:
        if value is not None:
            records.append(
                normalize_record(
                    "Yahoo Finance",
                    timestamp,
                    symbol,
                    metric_name,
                    value,
                    units,
                    "daily",
                )
            )
    if not records:
        raise RuntimeError("Yahoo Finance did not return usable fast_info fields.")
    return records


def export_json(records: Any, path: Path) -> None:
    """Write JSON output with readable indentation."""
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")


def export_csv(records: Iterable[Dict[str, Any]], path: Path, fieldnames: List[str]) -> None:
    """Write a list of dictionaries to CSV."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, "") for key in fieldnames})


def build_financial_snapshot(symbol: str, company_name: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build a simple company + macro snapshot from standardized records."""
    lookup = {(row["data_source"], row["symbol"], row["metric_name"]): row for row in records}

    def value(source: str, sym: str, metric: str) -> Optional[float]:
        row = lookup.get((source, sym, metric))
        return None if row is None else row.get("metric_value")

    def record(source: str, sym: str, metric: str) -> Optional[Dict[str, Any]]:
        return lookup.get((source, sym, metric))

    # Prefer Yahoo for broad stock snapshot fields; use Alpha as a fallback for price.
    current_price = value("Yahoo Finance", symbol, "Current Stock Price")
    if current_price is None:
        current_price = value("Alpha Vantage", symbol, "Latest Trading Price")

    previous_close = value("Yahoo Finance", symbol, "Previous Close")
    if previous_close is None:
        previous_close = value("Alpha Vantage", symbol, "Previous Close")

    return {
        "company": company_name,
        "symbol": symbol,
        "generated_at_utc": utc_now(),
        "market_data": {
            "current_stock_price_usd": current_price,
            "previous_close_usd": previous_close,
            "market_cap_usd": value("Yahoo Finance", symbol, "Market Capitalization"),
            "fifty_two_week_high_usd": value("Yahoo Finance", symbol, "52 Week High"),
            "fifty_two_week_low_usd": value("Yahoo Finance", symbol, "52 Week Low"),
        },
        "macro_data": {
            "gdp": record("FRED", "GDP", "Gross Domestic Product"),
            "cpi": record("FRED", "CPIAUCSL", "Consumer Price Index for All Urban Consumers"),
            "unemployment_rate": record("FRED", "UNRATE", "Unemployment Rate"),
        },
    }


def flatten_snapshot(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert the snapshot into a simple CSV-friendly row format."""
    rows: List[Dict[str, Any]] = []
    for metric, value in snapshot["market_data"].items():
        rows.append(
            {
                "section": "market_data",
                "metric": metric,
                "value": value,
                "units": "USD",
                "date_or_timestamp": snapshot["generated_at_utc"],
                "source_symbol": snapshot["symbol"],
            }
        )
    for name, record in snapshot["macro_data"].items():
        if record:
            rows.append(
                {
                    "section": "macro_data",
                    "metric": name,
                    "value": record.get("metric_value"),
                    "units": record.get("units"),
                    "date_or_timestamp": record.get("timestamp"),
                    "source_symbol": record.get("symbol"),
                }
            )
    return rows


def main() -> None:
    company_symbol = "NVDA"
    company_name = "NVIDIA Corporation"

    records: List[Dict[str, Any]] = []

    # FRED macro indicators: GDP, CPI, and unemployment as an extra indicator.
    fred_series = [
        (
            "GDP",
            "Gross Domestic Product",
            "Billions of Dollars, Seasonally Adjusted Annual Rate",
            "quarterly",
        ),
        (
            "CPIAUCSL",
            "Consumer Price Index for All Urban Consumers",
            "Index 1982-1984=100, Seasonally Adjusted",
            "monthly",
        ),
        ("UNRATE", "Unemployment Rate", "Percent, Seasonally Adjusted", "monthly"),
    ]
    for series_id, metric_name, units, frequency in fred_series:
        records.append(fetch_fred_latest(series_id, metric_name, units, frequency))

    # Market data from both Yahoo Finance and Alpha Vantage.
    try:
        records.extend(fetch_yahoo_snapshot(company_symbol))
    except Exception as exc:
        print(f"Warning: Yahoo Finance failed: {exc}")

    try:
        records.extend(fetch_alpha_vantage_quote(company_symbol))
    except Exception as exc:
        print(f"Warning: Alpha Vantage failed: {exc}")

    snapshot = build_financial_snapshot(company_symbol, company_name, records)

    export_json(records, OUTPUT_DIR / "standardized_data.json")
    export_csv(records, OUTPUT_DIR / "standardized_data.csv", SCHEMA_FIELDS)

    export_json(snapshot, OUTPUT_DIR / "financial_snapshot.json")
    export_csv(
        flatten_snapshot(snapshot),
        OUTPUT_DIR / "financial_snapshot.csv",
        ["section", "metric", "value", "units", "date_or_timestamp", "source_symbol"],
    )

    print(json.dumps({"status": "success", "records_exported": len(records), "output_dir": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()
