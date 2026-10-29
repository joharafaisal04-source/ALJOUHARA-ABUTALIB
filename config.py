"""Central configuration for VELORA AI."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SAMPLE_DATA_PATH = DATA_DIR / "sample_sales.csv"

# Color palette
COLORS = {
    "bg": "#0B1020",
    "sidebar": "#0F172A",
    "card": "#121A2B",
    "elevated": "#182338",
    "accent": "#2DD4BF",
    "accent2": "#818CF8",
    "text": "#F8FAFC",
    "text2": "#94A3B8",
    "positive": "#34D399",
    "warning": "#FBBF24",
    "negative": "#FB7185",
    "border": "#263449",
}

LIGHT_COLORS = {
    "bg": "#F1F5F9",
    "sidebar": "#E2E8F0",
    "card": "#FFFFFF",
    "elevated": "#F8FAFC",
    "accent": "#0D9488",
    "accent2": "#4F46E5",
    "text": "#0F172A",
    "text2": "#475569",
    "positive": "#059669",
    "warning": "#D97706",
    "negative": "#E11D48",
    "border": "#CBD5E1",
}

CHART_COLORS = [
    "#2DD4BF", "#818CF8", "#34D399", "#FBBF24",
    "#FB7185", "#60A5FA", "#F472B6", "#A78BFA",
]

REQUIRED_COLUMNS = [
    "order_id", "order_date", "customer_id", "product",
    "category", "region", "quantity", "unit_price", "revenue",
]
OPTIONAL_COLUMNS = ["channel", "unit_cost"]

PAGES = [
    {"id": "overview",   "label": "Overview",          "icon": "bi bi-grid-1x2"},
    {"id": "sales",      "label": "Sales Analytics",   "icon": "bi bi-bar-chart"},
    {"id": "revenue",    "label": "Revenue & Profit",  "icon": "bi bi-currency-dollar"},
    {"id": "forecast",   "label": "Forecasting",       "icon": "bi bi-graph-up-arrow"},
    {"id": "ai",         "label": "AI Analyst",        "icon": "bi bi-robot"},
    {"id": "reports",    "label": "Reports",           "icon": "bi bi-file-earmark-text"},
    {"id": "datasources","label": "Data Sources",      "icon": "bi bi-database"},
    {"id": "settings",   "label": "Settings",          "icon": "bi bi-gear"},
]
