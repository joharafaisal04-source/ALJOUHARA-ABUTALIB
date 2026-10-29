"""VELORA AI — Main application entry point."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from config import PAGES
from services.data_loader import load_sample_data
from components.sidebar import build_sidebar
from components.topbar import build_topbar

import pages.overview as overview_page
import pages.sales as sales_page
import pages.revenue as revenue_page
import pages.forecast as forecast_page
import pages.ai_analyst as ai_page
import pages.reports as reports_page
import pages.datasources as datasources_page
import pages.settings as settings_page

# ── Shared mutable dataset store ────────────────────────────────────────────
_df: pd.DataFrame = load_sample_data()

def get_df() -> pd.DataFrame:
    return _df

def set_df(new_df: pd.DataFrame):
    global _df
    _df = new_df

# ── App init ─────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    ],
    title="VELORA AI",
    update_title=None,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ── Layout ────────────────────────────────────────────────────────────────────
df0 = get_df()
min_date = str(df0["order_date"].min().date())
max_date = str(df0["order_date"].max().date())

app.layout = html.Div(
    id="app-root",
    **{"data-theme": "dark"},
    children=[
        dcc.Store(id="theme-store", data="dark"),
        dcc.Store(id="sidebar-collapsed", data=False),
        dcc.Location(id="url"),

        html.Div(
            id="app-shell",
            children=[
                build_sidebar(),
                html.Div(
                    id="main-content",
                    children=[
                        build_topbar(min_date, max_date),
                        html.Div(id="page-container"),
                    ],
                ),
            ],
        ),
    ],
)

# ── Page routing ──────────────────────────────────────────────────────────────
PAGE_MAP = {
    "/":            ("Overview",         overview_page.layout),
    "/overview":    ("Overview",         overview_page.layout),
    "/sales":       ("Sales Analytics",  sales_page.layout),
    "/revenue":     ("Revenue & Profit", revenue_page.layout),
    "/forecast":    ("Forecasting",      forecast_page.layout),
    "/ai":          ("AI Analyst",       ai_page.layout),
    "/reports":     ("Reports",          reports_page.layout),
    "/datasources": ("Data Sources",     datasources_page.layout),
    "/settings":    ("Settings",         settings_page.layout),
}

@app.callback(
    Output("page-container", "children"),
    Output("page-title", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    title, layout_fn = PAGE_MAP.get(pathname, ("Overview", overview_page.layout))
    return layout_fn(), title


# ── Theme toggle ──────────────────────────────────────────────────────────────
@app.callback(
    Output("theme-store", "data"),
    Output("app-root", "data-theme"),
    Output("theme-icon", "className"),
    Input("theme-toggle", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def toggle_theme(n, current):
    new = "light" if current == "dark" else "dark"
    icon = "bi bi-sun-fill" if new == "light" else "bi bi-moon-stars-fill"
    return new, new, icon


# ── Sidebar toggle ────────────────────────────────────────────────────────────
@app.callback(
    Output("sidebar", "className"),
    Output("main-content", "className"),
    Output("sidebar-collapsed", "data"),
    Input("sidebar-toggle", "n_clicks"),
    State("sidebar-collapsed", "data"),
)
def toggle_sidebar(n, collapsed):
    if n and collapsed is False:
        return "velora-sidebar collapsed", "sidebar-collapsed", True
    return "velora-sidebar", "", False


# ── Register all page callbacks ───────────────────────────────────────────────
overview_page.register_callbacks(app, get_df)
sales_page.register_callbacks(app, get_df)
revenue_page.register_callbacks(app, get_df)
forecast_page.register_callbacks(app, get_df)
ai_page.register_callbacks(app, get_df)
reports_page.register_callbacks(app, get_df)
datasources_page.register_callbacks(app, get_df, set_df)
settings_page.register_callbacks(app, get_df)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=port, host="0.0.0.0")
