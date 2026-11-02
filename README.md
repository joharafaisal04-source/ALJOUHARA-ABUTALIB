# VELORA AI — Intelligence Beyond Data

**VELORA AI** is an enterprise-grade, AI-powered business analytics platform combining interactive dashboards, sales intelligence, profitability analysis, machine learning forecasting, and AI-powered business insights — built entirely with Python.

> Built by **Aljouhara Abutalib** as a professional data science portfolio project.

---

## Live Demo

Deploy your own instance on Render in minutes — see [Deployment](#deployment) below.

---

## Features

| Module | Capability |
|---|---|
| **Overview** | Executive KPI cards (revenue, profit, margin, orders, AOV, growth), period-over-period comparison, AI-generated executive summary |
| **Sales Analytics** | Daily / weekly / monthly trend charts, category & regional breakdown, channel analysis, searchable product table, CSV export |
| **Revenue & Profit** | Revenue vs profit trends, cost analysis, anomaly detection (rolling z-score), regional profitability heatmap |
| **Forecasting** | Ridge regression ML model vs seasonal naive baseline, WAPE governance badge, 90% prediction intervals, strict chronological train/test split |
| **AI Analyst** | Conversational chat — Demo mode (real data, no API) and Live mode (AI-powered responses via external API) |
| **Reports** | KPI summary, executive summary, CSV export, styled HTML report download |
| **Data Sources** | Upload any CSV or Excel file — automatic column detection, data quality checks, downloadable sample template |
| **Settings** | Dark / light theme, currency selector, live AI status indicator |

- Responsive, dark-by-default UI
- Fully keyboard-accessible
- Light and dark theme with smooth toggle

---

## Screenshots

> Run the app locally and add screenshots here.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Dash 2.17 + Plotly 5.22 |
| UI components | Dash Bootstrap Components 1.6 |
| Data processing | pandas 2.2, NumPy 1.26 |
| Machine learning | scikit-learn 1.5 (Ridge regression) |
| AI integration | External AI API (configurable via environment variables) |
| Environment | python-dotenv |
| Production server | Gunicorn 22 |
| Testing | pytest 8.2 (23 tests) |
| Runtime | Python 3.11+ |

---

## Local Setup

**Requirements:** Python 3.11+

```bash
# 1. Clone the repository
git clone https://github.com/joharafaisal04-source/ALJOUHARA-ABUTALIB.git
cd ALJOUHARA-ABUTALIB

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Add your AI API key — see section below

# 5. Run the app
python app.py
```

Open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.

---

## AI Analyst — API Key Setup

The app works fully in **Demo mode** with no API key. To enable live AI responses:

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add one key:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# or
OPENAI_API_KEY=your_openai_api_key_here
```

Restart the app. The **Settings** page will confirm **Live AI mode active**.

> The key is loaded server-side only via environment variables. It is never displayed, logged, or sent to the browser.

---

## Demo Mode

Without an API key the app runs in **Demo mode**:
- All dashboards, charts, forecasting, and reports work fully
- The AI Analyst answers questions computed directly from the loaded dataset — no external API is called
- Demo mode is clearly labeled in the UI

---

## Upload Your Own Data

Go to **Data Sources** and upload any CSV or Excel file.  
The app detects your column names automatically — no specific format required.

Minimum requirements:
- One date column
- One numeric revenue / sales / amount column

Download the **sample template** from the Data Sources page for reference.

---

## Running Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

23 tests covering KPI calculations, profit/margin formulas, period comparisons, data validation, forecast train/test split integrity, and demo-mode AI responses.

---

## Deployment

### Render.com (Recommended — Free Tier)

1. Fork or clone this repository to your GitHub account
2. Go to [render.com](https://render.com) → **New +** → **Web Service**
3. Connect your GitHub repository
4. Use these settings:

| Setting | Value |
|---|---|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:server --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| **Instance Type** | Free |

5. Add Environment Variable (optional — for live AI):

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your key |

6. Click **Create Web Service** — deploy takes ~3–5 minutes.

> The app runs in Demo mode on Render without an API key.

---

## Project Structure

```
ALJOUHARA-ABUTALIB/
├── app.py                      # Entry point — routing, layout, server
├── config.py                   # Colors, page list, column definitions
├── requirements.txt
├── Procfile                    # Gunicorn start command for Render
├── .env.example                # Placeholder env vars (no real keys)
├── .gitignore
├── data/
│   ├── sample_sales.csv        # Built-in demo dataset (18,000 rows, 2 years)
│   └── velora_sample_template.xlsx  # Downloadable upload template
├── assets/
│   └── velora.css              # Full visual theme (dark + light)
├── components/
│   ├── sidebar.py              # Collapsible navigation
│   ├── topbar.py               # Date range picker, theme toggle
│   └── kpi_card.py             # Reusable KPI card component
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
│   ├── data_loader.py          # CSV/XLSX upload, validation, column mapping
│   ├── metrics.py              # KPI engine, period comparison, formatting
│   ├── chart_theme.py          # Shared Plotly theme (dark + light)
│   ├── forecasting.py          # ML model, baseline, WAPE governance
│   ├── ai_client.py            # AI Analyst — demo + live mode, key handling
│   └── generate_data.py        # Sample data generator
└── tests/
    └── test_metrics.py         # 23 pytest tests
```

---

## Security

- API keys are loaded exclusively via environment variables (`os.getenv`)
- `.env` is in `.gitignore` and never committed
- `.env.example` contains placeholder values only — no real keys
- API keys are never logged, printed, displayed, or sent to the browser
- The app degrades gracefully to Demo mode when no key is present

---

## Known Limitations

- Forecasting uses Ridge regression — deep seasonality may need SARIMA or Prophet
- No persistent user settings across browser sessions (session-only state)
- PDF export not implemented — HTML report is the formatted deliverable
- Multi-user / authentication not included

---

## Author

**Aljouhara Abutalib**  
Data Science & AI — Intelligence Beyond Data
