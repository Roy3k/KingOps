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

## Quick panel

```bash
python scripts/quick_panel.py      # net worth, debts, fixed costs, 6-month category spending
python scripts/quick_panel.py 12   # same, over 12 months
```

## Data

- **Refreshing**: export Plan + Register from YNAB, drop the two CSVs in the repo root or `Vault/`, and point `config.yaml` at them. Balances are each account's running balance as of the export date in the filename (`... as of YYYY-MM-DD ...`); later-dated rows are scheduled entries and are left out.

- **Vault/**: Store financial CSVs, PDFs, and other sensitive data here. Contents are gitignored by default.
- **Config**: Edit `config.yaml` to point to Plan and Register CSV paths.

## Frameworks

1. **Balance Sheet Integrity (F1)**: Net worth with confidence bands, integrity queue
2. **Cash Flow & Allocation (F2)**: Budget vs actual, variance drivers, 6-month spending by category, allocation Sankey
   - **Obligations**: Debts (balance, APR, payment activity) and recurring fixed costs
3. **Risk & Insurance (F3)**: Coverage map, renewal calendar
4. **Behavioral Leakage (F7)**: Subscriptions, fragmentation, uncategorized queue
