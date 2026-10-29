"""Settings page."""
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from services.ai_client import _has_live_key


def layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Appearance", className="card-title"),
                dbc.Row([
                    dbc.Col(html.Label("Theme", className="text-muted-velora small"), width=4),
                    dbc.Col(dcc.RadioItems(
                        id="settings-theme",
                        options=[
                            {"label": " Dark", "value": "dark"},
                            {"label": " Light", "value": "light"},
                        ],
                        value="dark",
                        inline=True,
                        inputClassName="me-1",
                        labelClassName="me-3 small",
                    ), width=8),
                ], className="mb-3 align-items-center"),
            ], className="velora-card"), md=6),

            dbc.Col(html.Div([
                html.P("Currency & Format", className="card-title"),
                dbc.Row([
                    dbc.Col(html.Label("Currency symbol", className="text-muted-velora small"), width=5),
                    dbc.Col(dcc.Dropdown(
                        id="settings-currency",
                        options=[
                            {"label": "$ USD", "value": "$"},
                            {"label": "€ EUR", "value": "€"},
                            {"label": "£ GBP", "value": "£"},
                            {"label": "﷼ SAR", "value": "﷼"},
                        ],
                        value="$", clearable=False, className="velora-dropdown",
                    ), width=7),
                ], className="align-items-center"),
                html.Small("Affects number formatting across the app.", className="text-muted-velora mt-2 d-block"),
            ], className="velora-card"), md=6),
        ], className="g-3 mb-4"),

        html.Div([
            html.P("AI Analyst Status", className="card-title"),
            html.Div(id="settings-ai-status"),
            html.Div(id="settings-ai-hint"),
        ], className="velora-card mb-4"),

        html.Div([
            html.P("About VELORA AI", className="card-title"),
            html.P("Version 1.0.0 — Built with Dash, Plotly, and scikit-learn.",
                   className="text-muted-velora small"),
            html.P("Intelligence Beyond Data.", className="text-accent small"),
        ], className="velora-card"),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("settings-ai-status", "children"),
        Output("settings-ai-hint", "children"),
        Input("theme-store", "data"),
    )
    def ai_status(_):
        if _has_live_key():
            return (
                dbc.Alert(
                    [html.I(className="bi bi-check-circle-fill me-2"),
                     "Live AI mode is active. API key detected."],
                    className="velora-alert-info",
                ),
                [],
            )
        return (
            dbc.Alert(
                [html.I(className="bi bi-info-circle me-2"),
                 "Demo mode is active. No API key configured. "
                 "Answers are computed from real data without calling an external model."],
                className="velora-alert-warn",
            ),
            html.Small([
                "To enable live AI mode: add ",
                html.Code("OPENAI_API_KEY=sk-..."),
                " or ",
                html.Code("ANTHROPIC_API_KEY=sk-ant-..."),
                " to your ",
                html.Code(".env"),
                " file, then restart the app. The key is never displayed or logged.",
            ], className="text-muted-velora d-block mt-2"),
        )

    @app.callback(
        Output("theme-store", "data", allow_duplicate=True),
        Input("settings-theme", "value"),
        prevent_initial_call=True,
    )
    def sync_theme_from_settings(val):
        return val
