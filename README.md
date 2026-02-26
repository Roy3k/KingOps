# KingOps — Intelligent Household Financial Dashboard

A Python + Streamlit dashboard for financial independence acceleration, built for the King family. Implements Balance Sheet Integrity, Cash Flow & Allocation Efficiency, Risk & Insurance, and Behavioral Leakage detection.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Data

- **Vault/**: Store financial CSVs, PDFs, and other sensitive data here. Contents are gitignored by default.
- **Config**: Edit `config.yaml` to point to Plan and Register CSV paths.

## Frameworks

1. **Balance Sheet Integrity (F1)**: Net worth with confidence bands, integrity queue
2. **Cash Flow & Allocation (F2)**: Budget vs actual, variance drivers, allocation Sankey
3. **Risk & Insurance (F3)**: Coverage map, renewal calendar
4. **Behavioral Leakage (F7)**: Subscriptions, fragmentation, uncategorized queue
