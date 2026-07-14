# West Matrix Local Sandbox

This repository sets up a clean Python sandbox for connecting to external financial and macroeconomic data sources without using any internal production database.

## What this includes

- Python virtual environment workflow
- Optional Docker workflow
- `requirements.txt` with required packages
- `.env.example` for API-key configuration
- `verify_connectivity.py` to test:
  - FRED macroeconomic data API
  - Yahoo Finance market data through `yfinance`
  - Alpha Vantage market data API
- Standard JSON output showing whether each connection succeeded

## 1. Create the local Python environment

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

## 2. Add API keys

Copy the example environment file:

```bash
cp .env.example .env
```

Then edit `.env` and add your free keys:

```env
FRED_API_KEY=b173556aee1710d182c3ddde9eeb6b99
ALPHA_VANTAGE_API_KEY=UOSPZCUL2J34FD2V
```

Yahoo Finance is tested using the `yfinance` Python package and does not require an API key for this connectivity test.

## 3. Run the verification script

```bash
python verify_connectivity.py
```

Expected output format:

```json
{
  "environment": {
    "python_version": "3.x.x",
    "timestamp_utc": "..."
  },
  "checks": {
    "fred": {
      "status": "success",
      "series_id": "GDP",
      "latest_observation": {
        "date": "...",
        "value": "..."
      }
    },
    "yahoo_finance": {
      "status": "success",
      "symbol": "MSFT",
      "latest_close": 123.45
    },
    "alpha_vantage": {
      "status": "success",
      "symbol": "IBM",
      "price": "..."
    }
  }
}
```

If an API key is missing or invalid, the script prints a clear JSON error for that service instead of crashing.

## 4. Optional Docker run

Build the image:

```bash
docker build -t westmatrix-sandbox .
```

Run it with your `.env` file:

```bash
docker run --rm --env-file .env westmatrix-sandbox
```

## GitHub submission suggestion

After testing locally:

```bash
git init
git add .
git commit -m "Initialize West Matrix sandbox environment"
```

Then create a GitHub repository and push the files.

## Files to submit

- GitHub repository link
- `verify_connectivity.py`
- `requirements.txt`
- Screenshot or copied JSON output from running `python verify_connectivity.py`
