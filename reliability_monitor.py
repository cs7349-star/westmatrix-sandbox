import argparse
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
LOG_PATH = Path("data/connectivity_log.csv")
REPORT_PATH = Path("output/summary_report.json")
FIELDNAMES = ["provider", "timestamp", "status", "response_time", "returned_value", "error_message", "symbol"]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def safe_float(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def retry_call(func, attempts=3, delay=1.0):
    last_error = None
    for attempt in range(attempts):
        try:
            return func()
        except Exception as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(delay * (attempt + 1))
    raise last_error


def check_fred(series_id="GDP"):
    start = time.perf_counter()
    result = {"provider": "FRED", "timestamp": utc_now(), "status": "fail", "response_time": 0.0, "returned_value": None, "error_message": "", "symbol": series_id}
    if not FRED_API_KEY:
        result["error_message"] = "Missing FRED_API_KEY"
        result["response_time"] = round(time.perf_counter() - start, 4)
        return result
    try:
        def call():
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json", "sort_order": "desc", "limit": 10},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        data = retry_call(call)
        observations = data.get("observations", [])
        valid = next((obs for obs in observations if safe_float(obs.get("value")) is not None), None)
        if not valid:
            raise ValueError("No valid FRED observations returned")
        result["status"] = "success"
        result["returned_value"] = safe_float(valid["value"])
    except Exception as exc:
        result["error_message"] = str(exc)
    result["response_time"] = round(time.perf_counter() - start, 4)
    return result


def check_yahoo(symbol):
    start = time.perf_counter()
    result = {"provider": "Yahoo Finance", "timestamp": utc_now(), "status": "fail", "response_time": 0.0, "returned_value": None, "error_message": "", "symbol": symbol}
    try:
        def call():
            history = yf.Ticker(symbol).history(period="5d")
            if history.empty:
                raise ValueError("No Yahoo Finance data returned")
            return history
        history = retry_call(call)
        close = safe_float(history["Close"].dropna().iloc[-1])
        if close is None:
            raise ValueError("Invalid Yahoo Finance closing price")
        result["status"] = "success"
        result["returned_value"] = close
    except Exception as exc:
        result["error_message"] = str(exc)
    result["response_time"] = round(time.perf_counter() - start, 4)
    return result


def check_alpha_vantage(symbol):
    start = time.perf_counter()
    result = {"provider": "Alpha Vantage", "timestamp": utc_now(), "status": "fail", "response_time": 0.0, "returned_value": None, "error_message": "", "symbol": symbol}
    if not ALPHA_VANTAGE_API_KEY:
        result["error_message"] = "Missing ALPHA_VANTAGE_API_KEY"
        result["response_time"] = round(time.perf_counter() - start, 4)
        return result
    try:
        def call():
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        data = retry_call(call)
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage rate limit: {data['Note']}")
        if "Information" in data:
            raise RuntimeError(f"Alpha Vantage message: {data['Information']}")
        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
        price = safe_float(data.get("Global Quote", {}).get("05. price"))
        if price is None:
            raise ValueError("No valid Alpha Vantage price returned")
        result["status"] = "success"
        result["returned_value"] = price
    except Exception as exc:
        result["error_message"] = str(exc)
    result["response_time"] = round(time.perf_counter() - start, 4)
    return result


def append_log(records, path=LOG_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        if not exists:
            writer.writeheader()
        writer.writerows(records)


def read_log(path=LOG_PATH):
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize(records, symbol):
    providers = {}
    for provider in ["FRED", "Yahoo Finance", "Alpha Vantage"]:
        rows = [r for r in records if r.get("provider") == provider]
        successes = [r for r in rows if r.get("status") == "success"]
        times = [safe_float(r.get("response_time")) for r in rows]
        times = [v for v in times if v is not None]
        providers[provider] = {
            "checks": len(rows),
            "success_rate": round((len(successes) / len(rows)) * 100, 2) if rows else 0.0,
            "average_response_time": round(sum(times) / len(times), 4) if times else None,
            "most_recent_successful_check": max((r["timestamp"] for r in successes), default=None),
        }
    yahoo = [r for r in records if r.get("provider") == "Yahoo Finance" and r.get("symbol") == symbol and r.get("status") == "success"]
    alpha = [r for r in records if r.get("provider") == "Alpha Vantage" and r.get("symbol") == symbol and r.get("status") == "success"]
    price_difference = None
    if yahoo and alpha:
        y = safe_float(yahoo[-1].get("returned_value"))
        a = safe_float(alpha[-1].get("returned_value"))
        if y is not None and a is not None:
            price_difference = {
                "symbol": symbol,
                "yahoo_price": y,
                "alpha_vantage_price": a,
                "absolute_difference": round(abs(y - a), 4),
                "percentage_difference": round(abs(y - a) / ((y + a) / 2) * 100, 4) if (y + a) else None,
            }
    return {"generated_at": utc_now(), "symbol": symbol, "providers": providers, "price_difference": price_difference}


def save_report(report, path=REPORT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="NVDA")
    parser.add_argument("--fred-series", default="GDP")
    args = parser.parse_args()
    symbol = args.symbol.upper()
    current = [check_fred(args.fred_series), check_yahoo(symbol), check_alpha_vantage(symbol)]
    append_log(current)
    report = summarize(read_log(), symbol)
    save_report(report)
    print(json.dumps({"latest_checks": current, "summary": report}, indent=2))


if __name__ == "__main__":
    main()
