# VELORA AI — Intelligence Beyond Data

A premium, enterprise-quality AI-powered business analytics platform built with Python, Dash, and scikit-learn. Designed as a Data Science portfolio piece and live demo.

---

## Features

- **Overview Dashboard** — KPI cards (revenue, profit, margin, orders, AOV, growth), executive summary generated from real data, period-over-period comparison
- **Sales Analytics** — Daily/weekly/monthly trends, category & regional breakdown, channel analysis, searchable product tables, CSV export
- **Revenue & Profit** — Revenue vs profit trends, cost analysis, anomaly detection (rolling z-score), regional profitability
- **Forecasting** — ML model (Ridge regression with lag + calendar features) vs seasonal naive baseline, MAE/RMSE/MAPE comparison, 90% prediction intervals, strict chronological train/test split
- **AI Analyst** — Chat interface with demo mode (answers from real data, no API calls) and live mode (OpenAI / Anthropic) 
- **Reports** — KPI summary, executive summary, CSV + HTML export
- **Data Sources** — CSV upload with validation (required columns, types, nulls, negatives, duplicates), column mapping, reset to sample
- **Settings** — Dark/light theme toggle, currency, AI status
- Responsive, dark-by-default, fully keyboard-accessible

---

## Screenshots

> Add screenshots here after running the app.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Dash 2.17 + Plotly 5.22 |
| UI components | Dash Bootstrap Components |
| Data | pandas 2.2, NumPy 1.26 |
| ML / Forecasting | scikit-learn 1.5 |
| Testing | pytest 8.2 |
| Environment | python-dotenv |

---

## Setup

**Requirements:** Python 3.11+, Mac/Linux/Windows

```bash
cd velora-ai
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.

---

## Adding an API Key (enable live AI)

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your key:
   ```
   OPENAI_API_KEY=sk-...
   # or
   ANTHROPIC_API_KEY=sk-ant-...
   ```
3. Restart the app. The Settings page will show **Live AI mode active**.

The key is never displayed, logged, or included in any output.

---

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

23 tests covering: KPI calculations, profit/margin formulas, period comparisons, data validation, forecast train/test split (no leakage), and demo-mode AI responses.

---

## Project Structure

```
velora-ai/
├── app.py                  # Entry point, routing, layout
├── config.py               # Colors, page list, column names
├── requirements.txt
├── .env.example            # Placeholder env vars (no real keys)
├── .gitignore
├── data/
│   └── sample_sales.csv    # 18,000 rows, 2 years
├── assets/
│   └── velora.css          # Full visual theme
├── components/
│   ├── sidebar.py          # Collapsible navigation
│   ├── topbar.py           # Date picker, theme toggle
│   └── kpi_card.py         # Reusable KPI card
├── pages/
│   ├── overview.py
│   ├── sales.py
│   ├── revenue.py
│   ├── forecast.py
│   ├── ai_analyst.py
│   ├── reports.py
│   ├── datasources.py
│   └── settings.py
├── services/
│   ├── data_loader.py      # Load, validate, parse CSV
│   ├── metrics.py          # KPI, period comparison, formatting
│   ├── chart_theme.py      # Shared Plotly theme
│   ├── forecasting.py      # ML model + baseline + intervals
│   ├── ai_client.py        # AI Analyst, demo + live mode
│   └── generate_data.py    # Sample data generator
└── tests/
    └── test_metrics.py     # 23 pytest tests
```

---

## Known Limitations

- Forecast uses Ridge regression; deep seasonality or complex patterns may need SARIMA/Prophet
- The step-by-step future forecast in `forecast_future` is slow for long horizons (90 days)
- No persistent user settings across browser sessions (session-only)
- PDF export not implemented; HTML report is the formatted deliverable
- The AI demo mode covers common question types; edge-case questions fall back to a generic prompt

## Future Ideas

- Add Prophet or SARIMA as an optional forecasting model
- PostgreSQL / SQLite backend for multi-dataset persistence
- Multi-user authentication and saved dashboards
- Real-time streaming data via WebSocket
- Slack / email scheduled report delivery
- Docker deployment with `docker-compose`
