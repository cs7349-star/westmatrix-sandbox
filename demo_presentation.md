# Presentation Outline

## Slide 1: Project Goal
Financial Data Quality Monitor and Executive Dashboard for West Matrix.

## Slide 2: Data Sources
Yahoo Finance and Alpha Vantage provide market data. FRED provides GDP, CPI, and unemployment indicators.

## Slide 3: Standardized Schema
All data is converted into one schema with source, timestamp, symbol, metric name, value, units, and frequency.

## Slide 4: Quality Checks
The monitor checks missing values, duplicates, invalid numbers, stale dates, API failures, rate limits, provider differences, and schema compliance.

## Slide 5: Dashboard
The Streamlit dashboard displays market data, macro indicators, provider differences, quality status, warnings, refresh time, and business interpretation.

## Slide 6: Testing
Automated tests cover numeric conversion, schema validation, missing values, invalid numeric values, stale records, duplicates, provider differences, and API failures.

## Slide 7: Business Interpretation
The system drafts a short interpretation, then reviews it for unsupported, broad, or misleading statements.

## Slide 8: Recommendations
Use the dashboard as a controlled data-quality layer before analytics or AI workflows. Add scheduling and alerts for production use.
