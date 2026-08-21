# AI Regulatory Change Testing & Model Risk Assessment

## Purpose
Formal testing framework for an AI regulatory-change analysis component.

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
python run_evaluation.py
pytest -q
streamlit run dashboard.py
```

## Metrics
- Overall accuracy
- False-positive rate
- Missed-change rate
- Control-mapping accuracy
- Human-review accuracy

## Contents
- 12 predefined regulatory-change scenarios
- Automated evaluation script
- Performance dashboard
- Automated tests
- 1–2 page model-risk assessment

## Limitations
The scenarios are synthetic and should be expanded with legally reviewed regulatory examples before production use. Human review remains required for high-impact or ambiguous changes.
