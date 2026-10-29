"""Top navigation bar with date range selector, theme toggle, and title."""
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd


def build_topbar(min_date: str, max_date: str) -> html.Div:
    return html.Div(
        className="velora-topbar",
        children=[
            html.Div(
                id="topbar-left",
                className="topbar-left",
                children=[
                    dbc.Button(
                        html.I(className="bi bi-list"),
                        id="sidebar-toggle",
                        color="link",
                        className="sidebar-toggle-btn",
                        n_clicks=0,
                    ),
                    html.H5(id="page-title", className="topbar-title mb-0"),
                ],
            ),
            html.Div(
                className="topbar-right",
                children=[
                    html.Div(
                        [
                            html.I(className="bi bi-calendar3 me-2"),
                            dcc.DatePickerRange(
                                id="date-range-picker",
                                min_date_allowed=min_date,
                                max_date_allowed=max_date,
                                start_date=str(pd.Timestamp(max_date) - pd.DateOffset(months=12))[:10],
                                end_date=max_date,
                                display_format="MMM D, YYYY",
                                className="velora-date-picker",
                            ),
                        ],
                        className="topbar-date-wrap d-flex align-items-center",
                    ),
                    dbc.Button(
                        [html.I(className="bi bi-moon-stars-fill", id="theme-icon")],
                        id="theme-toggle",
                        color="link",
                        className="theme-toggle-btn",
                        n_clicks=0,
                        title="Toggle light/dark mode",
                    ),
                ],
            ),
        ],
    )
