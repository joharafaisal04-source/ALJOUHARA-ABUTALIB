"""Central configuration for VELORA AI."""
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
SAMPLE_DATA_PATH = DATA_DIR / "sample_sales.csv"

# Color palette — Ivory Premium (light default)
COLORS = {
    "bg": "#FAF7F2",
    "sidebar": "#2D1F14",
    "card": "#FFFFFF",
    "elevated": "#F5EFE6",
    "accent": "#B5882A",
    "accent2": "#6B4C2A",
    "text": "#1C1208",
    "text2": "#6B5040",
    "positive": "#4A7A3A",
    "warning": "#B8691A",
    "negative": "#9A3A2A",
    "border": "#E8DDD0",
}

DARK_COLORS = {
    "bg": "#1A1108",
    "sidebar": "#231609",
    "card": "#2A1C0C",
    "elevated": "#321F0E",
    "accent": "#C8A050",
    "accent2": "#8B6030",
    "text": "#F5EFE6",
    "text2": "#A8886A",
    "positive": "#6A9E5A",
    "warning": "#D4883A",
    "negative": "#C06050",
    "border": "#3D2810",
}

CHART_COLORS = [
    "#B5882A", "#7A9E6E", "#4A6B8A", "#C47B3A",
    "#8B5530", "#9A6B9A", "#4A8A6A", "#D4A050",
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
