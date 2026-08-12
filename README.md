# Financial Data Reliability Monitor

## Overview

This project expands the West Matrix API connectivity checker into a monitoring tool that records provider reliability, validates returned values, compares stock prices, and produces a summary report.

## Providers

- FRED
- Yahoo Finance
- Alpha Vantage

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your API keys to `.env`.

## Run

```bash
python reliability_monitor.py NVDA
```

Use another ticker without editing the source code:

```bash
python reliability_monitor.py AAPL
python reliability_monitor.py MSFT
```

Optional FRED series:

```bash
python reliability_monitor.py NVDA --fred-series CPIAUCSL
```

## Output

Each run appends records to `data/connectivity_log.csv` with provider, timestamp, status, response time, returned value, error message, and symbol.

A summary report is written to `output/summary_report.json` with provider success rate, average response time, most recent successful check, and Yahoo Finance vs. Alpha Vantage price differences.

## Testing

```bash
pytest -q
```

The test suite uses mocked API responses and covers numeric conversion, missing API keys, FRED parsing, Yahoo empty data, Alpha Vantage rate-limit handling, and cross-provider price comparison.

## Assumptions

- Yahoo Finance uses the most recent available closing price.
- Alpha Vantage uses the `GLOBAL_QUOTE` endpoint.
- FRED defaults to GDP unless another series is supplied.
- API keys are stored in `.env` and excluded from GitHub.

## Known Limitations

- Free API tiers may impose rate limits.
- Provider prices may differ because of update timing.
- Network conditions affect response-time measurements.
- Historical reliability depends on how often the monitor is run.
