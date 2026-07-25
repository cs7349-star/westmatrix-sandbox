from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline import DEFAULT_FRED_SERIES, build_ai_interpretation, collect_records
from src.quality import evaluate_records

st.set_page_config(page_title="West Matrix Data Quality Monitor", layout="wide")
st.title("West Matrix Financial Data Quality Monitor")

input_tickers = st.sidebar.text_input("Stock tickers", "NVDA,AAPL,MSFT")
tolerance_pct = st.sidebar.slider("Provider price difference tolerance (%)", 0.5, 10.0, 2.0, 0.5)
run_button = st.sidebar.button("Refresh Data")

tickers = [ticker.strip().upper() for ticker in input_tickers.split(",") if ticker.strip()]

if run_button:
    with st.spinner("Collecting data and running quality checks..."):
        records = collect_records(tickers, DEFAULT_FRED_SERIES)
        quality_report = evaluate_records(records, tolerance_pct=tolerance_pct)
        interpretation = build_ai_interpretation(records, quality_report)
        Path("output").mkdir(exist_ok=True)
        with open("output/dashboard_latest.json", "w", encoding="utf-8") as file:
            json.dump({"records": records, "quality_report": quality_report, "interpretation": interpretation}, file, indent=2)
else:
    sample_path = Path("output/sample_dashboard_latest.json")
    if sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as file:
            sample = json.load(file)
        records = sample["records"]
        quality_report = sample["quality_report"]
        interpretation = sample["interpretation"]
    else:
        records = []
        quality_report = {"overall_status": "Warning", "issues": [], "status_by_source": {}, "provider_price_comparison": {}}
        interpretation = {"draft_interpretation": "Run the dashboard to generate a current interpretation.", "independent_review": []}

col1, col2, col3 = st.columns(3)
col1.metric("Overall Status", quality_report.get("overall_status", "Unknown"))
col2.metric("Records", len(records))
col3.metric("Issues", len(quality_report.get("issues", [])))

if records:
    df = pd.DataFrame(records)
    market = df[df["symbol"].isin(tickers)]
    macro = df[df["data_source"].eq("FRED")]
    st.subheader("Current Market Data")
    st.dataframe(market, use_container_width=True)
    st.subheader("Macroeconomic Indicators")
    st.dataframe(macro, use_container_width=True)
else:
    st.info("No records loaded yet.")

st.subheader("Provider Price Comparison")
st.json(quality_report.get("provider_price_comparison", {}))

st.subheader("Data Quality by Source")
st.json(quality_report.get("status_by_source", {}))

st.subheader("Warnings and Failed Checks")
st.json(quality_report.get("issues", []))

st.subheader("Business Interpretation")
st.write(interpretation.get("draft_interpretation", ""))

st.subheader("Independent Review of AI Draft")
for item in interpretation.get("independent_review", []):
    st.write(f"- {item}")
