# Demo Script

1. Open the GitHub repository and show the organized folders: `src`, `tests`, `output`, and `docs`.
2. Open `.env.example` and explain that real API keys are stored locally in `.env`, not uploaded to GitHub.
3. Run `python run_pipeline.py` and show the terminal output with record count and overall status.
4. Open `output/standardized_records.json` and show the standardized schema.
5. Open `output/quality_report.json` and show Pass, Warning, or Fail results.
6. Run `pytest` and show that the automated data-quality tests pass.
7. Run `streamlit run app.py` and open the dashboard.
8. Change the ticker input field, refresh the dashboard, and show that users can change companies without editing Python source code.
9. Show the provider price comparison and explain how Yahoo Finance and Alpha Vantage differences are flagged.
10. Show the business interpretation and the independent review notes.
