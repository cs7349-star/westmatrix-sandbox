# West Matrix Local Sandbox

This repository sets up a clean local Python sandbox for connecting to external financial and macroeconomic data sources, normalizing the raw API responses, and exporting standardized output files that can be consumed by downstream applications or AI models.

The project uses only external public data sources and does not connect to any internal production database.

## Project structure

```text
westmatrix-sandbox/
├── verify_connectivity.py          # Phase 1: API connectivity test
├── data_standardization.py         # Phase 2: normalization + financial snapshot pipeline
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Optional containerized run
├── .env.example                    # Example environment variables, no real keys
├── .gitignore                      # Prevents .env and virtual env files from being committed
├── writeup.md                      # Brief 1-2 page project explanation
└── output/
    ├── standardized_data.json      # Sample standardized JSON output
    ├── standardized_data.csv       # Sample standardized CSV output
    ├── financial_snapshot.json     # Sample company + macro snapshot JSON
    └── financial_snapshot.csv      # Sample company + macro snapshot CSV
```

## Data sources

The pipeline standardizes data from three external providers:

1. **FRED**
   - Gross Domestic Product (`GDP`)
   - Consumer Price Index (`CPIAUCSL`)
   - Unemployment Rate (`UNRATE`)
2. **Yahoo Finance**
   - Current stock price
   - Previous close
   - Market capitalization
   - 52-week high and low
3. **Alpha Vantage**
   - Latest trading price
   - Previous close
   - Trading volume

The sample financial snapshot uses **NVIDIA Corporation (`NVDA`)**.

## Common JSON schema

Each normalized observation uses this schema:

```json
{
  "data_source": "FRED",
  "timestamp": "2026-01-01",
  "symbol": "GDP",
  "metric_name": "Gross Domestic Product",
  "metric_value": 31865.721,
  "units": "Billions of Dollars, Seasonally Adjusted Annual Rate",
  "frequency": "quarterly"
}
```

### Schema fields

| Field | Description |
|---|---|
| `data_source` | Source provider, such as FRED, Yahoo Finance, or Alpha Vantage |
| `timestamp` | Observation date or timestamp from the provider |
| `symbol` | Stock ticker or economic series ID |
| `metric_name` | Human-readable name of the metric |
| `metric_value` | Numeric value after conversion |
| `units` | Unit of measurement, such as USD or Percent |
| `frequency` | Data frequency, such as daily, monthly, or quarterly |

## Setup instructions

Create and activate a local Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Add API keys

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and add your own keys:

```env
FRED_API_KEY=your_fred_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

Do **not** commit `.env` to GitHub. The `.gitignore` file is included to prevent that.

## Run Phase 1: connectivity test

```bash
python verify_connectivity.py
```

This prints a JSON status report showing whether FRED, Yahoo Finance, and Alpha Vantage are reachable.

## Run Phase 2: data standardization and financial snapshot

```bash
python data_standardization.py
```

This generates or refreshes the following files:

```text
output/standardized_data.json
output/standardized_data.csv
output/financial_snapshot.json
output/financial_snapshot.csv
```

## Example outputs

The repository includes sample output files in the `output/` folder. These files demonstrate the normalized schema and the NVIDIA financial snapshot format.

## Optional Docker run

Build the image:

```bash
docker build -t westmatrix-sandbox .
```

Run it with your `.env` file:

```bash
docker run --rm --env-file .env westmatrix-sandbox
```

## Notes

Yahoo Finance can sometimes return a temporary rate-limit error. The script catches this and continues with the other data sources when possible. FRED and Alpha Vantage require valid local API keys.
