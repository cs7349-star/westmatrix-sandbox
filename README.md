# West Matrix Financial Data Quality Monitor

This project extends the West Matrix sandbox into a reusable financial-data monitoring product. It collects market data for at least three public companies from Yahoo Finance and Alpha Vantage, collects GDP, CPI, and unemployment indicators from FRED, stores the results in a standardized schema, runs automated data-quality checks, and displays results in a Streamlit dashboard.

## Project Structure

```text
westmatrix_project3
├── app.py
├── run_pipeline.py
├── config.example.json
├── requirements.txt
├── Dockerfile
├── .env.example
├── src/
│   ├── fetchers.py
│   ├── normalize.py
│   ├── pipeline.py
│   └── quality.py
├── tests/
│   └── test_quality.py
├── output/
│   ├── standardized_records.json
│   ├── standardized_records.csv
│   ├── quality_report.json
│   ├── ai_interpretation_review.json
│   └── sample_dashboard_latest.json
└── docs/
    ├── executive_summary.md
    ├── demo_presentation.md
    └── demo_script.md
```

## Standardized Schema

Each record uses this shared structure:

```json
{
  "data_source": "Yahoo Finance",
  "timestamp": "2026-07-25T18:55:00+00:00",
  "symbol": "NVDA",
  "metric_name": "Current Price",
  "metric_value": 171.3,
  "units": "USD",
  "frequency": "daily",
  "provider_timestamp": "2026-07-24",
  "status": "success",
  "message": null
}
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your keys to `.env`:

```env
FRED_API_KEY=your_fred_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

Do not upload `.env` to GitHub.

## Run the Pipeline

Default tickers are `NVDA`, `AAPL`, and `MSFT`.

```bash
python run_pipeline.py
```

Run with a custom configuration:

```bash
python run_pipeline.py --config config.example.json
```

## Run the Dashboard

```bash
streamlit run app.py
```

The dashboard includes an input field for changing tickers without editing Python source code.

## Run Tests

```bash
pytest
```

The test file covers numeric conversion, schema validation, missing values, invalid numeric values, stale dates, duplicates, provider price differences, and API failure handling.

## Data-Quality Rules

| Check | Rule | Status Impact |
|---|---|---|
| Missing or null values | Required schema fields must not be missing or null | Fail |
| Duplicate records | Same source, symbol, metric, and observation date cannot repeat | Warning |
| Invalid numeric values | Numeric fields must be parseable and non-negative for financial/economic metrics | Fail |
| Stale dates | Daily market data should be recent; monthly and quarterly indicators use wider thresholds | Warning |
| API failures/rate limits | Missing keys, failed requests, or rate limits are captured | Fail |
| Provider differences | Yahoo and Alpha Vantage prices are compared against a tolerance | Warning |
| Schema compliance | Required fields must exist in each output record | Fail |

## Output Files

| File | Purpose |
|---|---|
| `output/standardized_records.json` | Main JSON output with records, quality report, and interpretation |
| `output/standardized_records.csv` | CSV version of standardized records |
| `output/quality_report.json` | Data-quality results and Pass/Warning/Fail status |
| `output/ai_interpretation_review.json` | AI-drafted interpretation and independent review notes |
| `output/sample_dashboard_latest.json` | Sample dashboard input data |

## Troubleshooting

If FRED or Alpha Vantage returns `missing_api_key`, check that `.env` exists and contains the correct key names. If Yahoo Finance or Alpha Vantage returns a rate-limit message, wait and rerun the script. If the dashboard opens but shows sample data, click `Refresh Data` after configuring the API keys.
