from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from .fetchers import fetch_alpha_vantage_quote, fetch_fred_series, fetch_yahoo_finance_quote
from .normalize import utc_now
from .quality import evaluate_records

DEFAULT_TICKERS = ["NVDA", "AAPL", "MSFT"]
DEFAULT_FRED_SERIES = {
    "GDP": {"metric_name": "Gross Domestic Product", "units": "Billions of Dollars", "frequency": "quarterly"},
    "CPIAUCSL": {"metric_name": "Consumer Price Index", "units": "Index 1982-1984=100", "frequency": "monthly"},
    "UNRATE": {"metric_name": "Unemployment Rate", "units": "Percent", "frequency": "monthly"},
}


def load_config(path: str | None) -> Dict[str, Any]:
    if not path:
        return {"tickers": DEFAULT_TICKERS, "fred_series": DEFAULT_FRED_SERIES, "output_folder": "output", "tolerance_pct": 2.0}
    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)
    return {
        "tickers": config.get("tickers", DEFAULT_TICKERS),
        "fred_series": config.get("fred_series", DEFAULT_FRED_SERIES),
        "output_folder": config.get("output_folder", "output"),
        "tolerance_pct": config.get("tolerance_pct", 2.0),
    }


def collect_records(tickers: List[str], fred_series: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for ticker in tickers:
        symbol = ticker.strip().upper()
        if not symbol:
            continue
        records.extend(fetch_yahoo_finance_quote(symbol))
        records.extend(fetch_alpha_vantage_quote(symbol))
    for series_id, metadata in fred_series.items():
        records.extend(fetch_fred_series(series_id, metadata["metric_name"], metadata["units"], metadata["frequency"]))
    return records


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def write_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["data_source", "timestamp", "symbol", "metric_name", "metric_value", "units", "frequency", "provider_timestamp", "status", "message"]
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def build_ai_interpretation(records: List[Dict[str, Any]], quality_report: Dict[str, Any]) -> Dict[str, Any]:
    text = (
        "The monitored companies show current market data from multiple providers, while FRED macroeconomic indicators provide context for GDP, inflation, and unemployment. "
        f"The current overall data-quality status is {quality_report['overall_status']}. "
        "Business users should treat Warning or Fail results as signals to review missing values, stale observations, API failures, or provider price differences before using the data in dashboards, models, or investment analysis."
    )
    review = [
        "The interpretation is descriptive and should not be treated as investment advice.",
        "Provider price differences may come from timing, delayed quotes, adjusted prices, or API limitations.",
        "Macroeconomic indicators are updated less frequently than stock prices, so freshness thresholds differ by frequency.",
    ]
    return {"draft_interpretation": text, "independent_review": review}


def run_pipeline(config_path: str | None = None) -> Dict[str, Any]:
    config = load_config(config_path)
    output_folder = Path(config["output_folder"])
    records = collect_records(config["tickers"], config["fred_series"])
    quality_report = evaluate_records(records, tolerance_pct=float(config.get("tolerance_pct", 2.0)))
    interpretation = build_ai_interpretation(records, quality_report)
    metadata = {"refresh_time_utc": utc_now(), "tickers": config["tickers"]}
    payload = {"metadata": metadata, "records": records, "quality_report": quality_report, "interpretation": interpretation}
    write_json(output_folder / "standardized_records.json", payload)
    write_csv(output_folder / "standardized_records.csv", records)
    write_json(output_folder / "quality_report.json", quality_report)
    write_json(output_folder / "ai_interpretation_review.json", interpretation)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    args = parser.parse_args()
    payload = run_pipeline(args.config)
    print(json.dumps({"refresh_time_utc": payload["metadata"]["refresh_time_utc"], "record_count": len(payload["records"]), "overall_status": payload["quality_report"]["overall_status"]}, indent=2))


if __name__ == "__main__":
    main()
