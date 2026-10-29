"""Forecasting page — enterprise-ready, executive-friendly."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

from services.forecasting import (
    prepare_daily_series, train_ml_model, forecast_future,
    seasonal_naive, MIN_ROWS,
)
from services.chart_theme import apply_velora_theme, CHART_COLORS


# ── Governance thresholds ────────────────────────────────────────────────────
_WAPE_VALIDATED      = 20.0   # WAPE ≤ 20 % → Validated
_WAPE_PENDING        = 35.0   # WAPE ≤ 35 % → Validation Pending
                               # WAPE > 35 % → Needs Review


def _governance_badge(wape: float, beats_baseline: bool) -> html.Span:
    if wape <= _WAPE_VALIDATED and beats_baseline:
        label, color, icon = "Validated",          "#10B981", "bi-patch-check-fill"
    elif wape <= _WAPE_PENDING:
        label, color, icon = "Validation Pending", "#F59E0B", "bi-clock-history"
    else:
        label, color, icon = "Needs Review",       "#EF4444", "bi-exclamation-circle"
    return html.Span(
        [html.I(className=f"bi {icon} me-1"), label],
        style={
            "fontSize": "11px", "fontWeight": "700", "letterSpacing": "0.06em",
            "color": color, "padding": "3px 8px",
            "border": f"1px solid {color}", "borderRadius": "20px",
            "background": f"{color}18",
        },
    )


def _kpi_card(title: str, value: str, sub: str = "", accent: bool = False) -> dbc.Col:
    return dbc.Col(html.Div([
        html.P(title, style={"fontSize": "11px", "fontWeight": "600",
                             "letterSpacing": "0.08em", "color": "var(--text2)",
                             "textTransform": "uppercase", "marginBottom": "4px"}),
        html.Div(value, style={"fontSize": "26px", "fontWeight": "800",
                               "color": "var(--accent)" if accent else "var(--text)",
                               "lineHeight": "1.1"}),
        html.Div(sub, style={"fontSize": "11px", "color": "var(--text2)", "marginTop": "4px"}),
    ], className="velora-card", style={"height": "100%"}), md=3, xs=6)


def layout() -> html.Div:
    return html.Div([
        # ── Controls ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col([
                html.Label("Forecast Horizon", className="text-muted-velora small mb-1"),
                dcc.Dropdown(
                    id="forecast-horizon",
                    options=[{"label": f"{d} days", "value": d} for d in [7, 14, 30, 60, 90]],
                    value=30, clearable=False, className="velora-dropdown",
                ),
            ], md=3),
        ], className="g-3 mb-3"),

        html.Div(id="forecast-notice", className="mb-3"),

        # ── Executive KPI cards ─────────────────────────────────────────────
        dbc.Row(id="forecast-kpi-row", className="g-3 mb-4"),

        # ── Main forecast chart ──────────────────────────────────────────────
        html.Div([
            html.Div([
                html.P("Revenue Forecast", className="card-title mb-0"),
                html.Span("90% prediction interval shown as shaded band",
                          style={"fontSize": "11px", "color": "var(--text2)"}),
            ], style={"marginBottom": "12px"}),
            dcc.Graph(id="forecast-main-chart", config={"displayModeBar": False}),
        ], className="velora-card mb-4"),

        # ── Test validation + metrics ────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.P("Backtest: Actual vs Predicted", className="card-title mb-0"),
                    html.Div(id="forecast-test-range",
                             style={"fontSize": "11px", "color": "var(--text2)"}),
                ], style={"marginBottom": "12px"}),
                dcc.Graph(id="forecast-test-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=7),

            dbc.Col(html.Div([
                html.Div([
                    html.P("Model Evaluation", className="card-title mb-0"),
                    html.Div(id="forecast-governance-badge", style={"marginTop": "4px"}),
                ], style={"marginBottom": "12px"}),
                html.Div(id="forecast-metrics-table"),
                html.P(
                    "Metrics computed on held-out test period (last 30 days). "
                    "ML Forecast compared against seasonal-naïve baseline.",
                    style={"fontSize": "11px", "color": "var(--text2)",
                           "marginTop": "12px", "lineHeight": "1.6"},
                ),
            ], className="velora-card"), md=5),
        ], className="g-3 mb-4"),

        # ── Methodology note ─────────────────────────────────────────────────
        html.Div([
            html.I(className="bi bi-info-circle me-2",
                   style={"color": "var(--text2)", "fontSize": "12px"}),
            html.Span(
                "Methodology note · ",
                style={"fontSize": "11px", "color": "var(--text2)", "fontWeight": "600"},
            ),
            html.Span(
                "Forecasts are statistical estimates derived from Ridge regression with "
                "calendar and lag features. They reflect historical patterns and should not "
                "be treated as guaranteed outcomes. Performance may degrade during unusual "
                "events, promotions, or structural market changes. "
                "Prediction intervals represent modelled uncertainty (90% coverage), not certainty.",
                style={"fontSize": "11px", "color": "var(--text2)", "lineHeight": "1.7"},
            ),
            html.Span(
                " · VELORA AI · Aljouhara Abutalib",
                style={"fontSize": "11px", "color": "var(--accent)",
                       "fontWeight": "600", "marginLeft": "4px"},
            ),
        ], style={
            "padding": "10px 16px",
            "borderTop": "1px solid var(--border)",
            "borderRadius": "6px",
            "background": "var(--card)",
            "opacity": "0.85",
        }),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("forecast-notice",          "children"),
        Output("forecast-kpi-row",         "children"),
        Output("forecast-main-chart",      "figure"),
        Output("forecast-test-chart",      "figure"),
        Output("forecast-test-range",      "children"),
        Output("forecast-metrics-table",   "children"),
        Output("forecast-governance-badge","children"),
        Input("date-range-picker",  "start_date"),
        Input("date-range-picker",  "end_date"),
        Input("forecast-horizon",   "value"),
        Input("theme-store",        "data"),
    )
    def update_forecast(start, end, horizon, theme):
        dark   = (theme or "dark") == "dark"
        empty  = go.Figure()
        notice = None

        if not start or not end:
            return notice, [], empty, empty, "", [], ""

        df   = get_df()
        filt = df[(df["order_date"] >= start) & (df["order_date"] <= end)].copy()
        daily = prepare_daily_series(filt)

        if len(daily) < MIN_ROWS:
            notice = dbc.Alert(
                [html.I(className="bi bi-exclamation-triangle me-2"),
                 f"Forecasting requires at least {MIN_ROWS} days of data. "
                 f"Selected range has {len(daily)} days — extend the date range."],
                className="velora-alert-warn",
            )

        try:
            metrics, test_preds, residual_std = train_ml_model(daily)
        except ValueError as e:
            notice = dbc.Alert(str(e), className="velora-alert-warn")
            return notice, [], empty, empty, "", [], ""

        point, lower, upper = forecast_future(daily, horizon, residual_std)
        baseline_future = seasonal_naive(daily, horizon)

        # ── Derived values ───────────────────────────────────────────────────
        wape_ml    = metrics["ml"]["WAPE"]
        wape_b     = metrics["baseline"]["WAPE"]
        mae_ml     = metrics["ml"]["MAE"]
        accuracy   = metrics["ml"]["Accuracy"]
        beats_base = wape_ml <= wape_b
        test_start = metrics["test_start"]
        test_end   = metrics["test_end"]
        refresh_dt = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
        fc_end     = point.index[-1].strftime("%b %d, %Y")

        # ── KPI cards ────────────────────────────────────────────────────────
        kpi_cards = [
            _kpi_card("Forecast Accuracy",  f"{accuracy:.1f}%",
                      "WAPE-based · test period", accent=True),
            _kpi_card("Mean Absolute Error", f"${mae_ml:,.0f}",
                      "Daily revenue · test period"),
            _kpi_card("Forecast Period",    f"{horizon} days",
                      f"Ending {fc_end}"),
            _kpi_card("Last Refresh",       refresh_dt[:10],
                      refresh_dt[11:]),
        ]

        # ── Main chart ───────────────────────────────────────────────────────
        main_fig = go.Figure()
        main_fig.add_trace(go.Scatter(
            x=daily.index, y=daily.values, name="Historical",
            line=dict(color=CHART_COLORS[0], width=1.5),
            hovertemplate="%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))
        main_fig.add_trace(go.Scatter(
            x=list(upper.index) + list(lower.index[::-1]),
            y=list(upper.values) + list(lower.values[::-1]),
            fill="toself", fillcolor="rgba(45,212,191,0.10)",
            line=dict(width=0), name="90% PI", hoverinfo="skip",
        ))
        main_fig.add_trace(go.Scatter(
            x=point.index, y=point.values, name="ML Forecast",
            line=dict(color=CHART_COLORS[0], width=2, dash="dash"),
            hovertemplate="%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))
        main_fig.add_trace(go.Scatter(
            x=baseline_future.index, y=baseline_future.values, name="Baseline Forecast",
            line=dict(color=CHART_COLORS[3], width=2, dash="dot"),
            hovertemplate="%{x|%b %d, %Y}: $%{y:,.0f}<extra></extra>",
        ))
        # Vertical line marking forecast start
        today_str = str(daily.index[-1].date())
        main_fig.add_shape(type="line", x0=today_str, x1=today_str,
                           y0=0, y1=1, xref="x", yref="paper",
                           line=dict(dash="dot", color="rgba(255,255,255,0.25)", width=1))
        main_fig.add_annotation(x=today_str, y=0.98, xref="x", yref="paper",
                                text="Forecast start", showarrow=False,
                                font=dict(size=10, color="#94A3B8"), xanchor="left")
        main_fig.update_layout(yaxis_tickprefix="$", legend_orientation="h",
                               legend=dict(y=1.08, x=0))
        apply_velora_theme(main_fig, dark)

        # ── Backtest chart ───────────────────────────────────────────────────
        actual = metrics["test_actual"]
        test_fig = go.Figure()
        test_fig.add_trace(go.Scatter(
            x=actual.index, y=actual.values, name="Actual",
            line=dict(color=CHART_COLORS[0], width=2),
            hovertemplate="%{x|%b %d}: $%{y:,.0f}<extra></extra>",
        ))
        test_fig.add_trace(go.Scatter(
            x=test_preds.index, y=test_preds.values, name="ML Predicted",
            line=dict(color=CHART_COLORS[1], width=2, dash="dash"),
            hovertemplate="%{x|%b %d}: $%{y:,.0f}<extra></extra>",
        ))
        test_fig.update_layout(yaxis_tickprefix="$")
        apply_velora_theme(test_fig, dark)

        test_range = (f"Evaluation period: "
                      f"{test_start.strftime('%b %d')} – {test_end.strftime('%b %d, %Y')}  "
                      f"({(test_end - test_start).days + 1} days, held out)")

        # ── Metrics table ────────────────────────────────────────────────────
        rows = []
        for metric in ["MAE", "RMSE", "MAPE", "WAPE"]:
            ml_val = metrics["ml"][metric]
            b_val  = metrics["baseline"][metric]
            better = ml_val <= b_val
            ml_cls = "text-positive" if better else "text-negative"
            is_pct = metric in ("MAPE", "WAPE")
            fmt_ml = f"{ml_val:.1f}%" if is_pct else f"${ml_val:,.0f}"
            fmt_b  = f"{b_val:.1f}%"  if is_pct else f"${b_val:,.0f}"
            rows.append(html.Tr([
                html.Td(metric, style={"fontWeight": "600"}),
                html.Td(fmt_ml, className=ml_cls),
                html.Td(fmt_b,  className="text-muted-velora"),
                html.Td(
                    html.I(className="bi bi-arrow-up text-positive"
                           if better else "bi bi-arrow-down text-negative"),
                ),
            ]))

        metrics_tbl = dbc.Table([
            html.Thead(html.Tr([
                html.Th("Metric"), html.Th("ML Model"),
                html.Th("Baseline"), html.Th(""),
            ])),
            html.Tbody(rows),
        ], bordered=False, className="velora-table")

        governance = _governance_badge(wape_ml, beats_base)

        return notice, kpi_cards, main_fig, test_fig, test_range, metrics_tbl, governance
