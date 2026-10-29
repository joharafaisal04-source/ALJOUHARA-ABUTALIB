"""Revenue & Profit page."""
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from services.metrics import (
    format_currency, revenue_by_period, anomaly_zscore
)
from services.chart_theme import apply_velora_theme, CHART_COLORS


def layout() -> html.Div:
    return html.Div([
        html.Div(id="revenue-cost-notice", className="mb-3"),
        dbc.Row(id="revenue-kpi-row", className="g-3 mb-4"),
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Revenue vs Profit Over Time", className="card-title"),
                dcc.Graph(id="rev-profit-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=8),
            dbc.Col(html.Div([
                html.P("Profitability by Category", className="card-title"),
                dcc.Graph(id="rev-cat-profit-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=4),
        ], className="g-3 mb-3"),
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Revenue Anomaly Detection", className="card-title"),
                html.Small(
                    "Rolling z-score (30-day window, threshold ±2.5): days where revenue "
                    "deviates more than 2.5 standard deviations from its rolling mean are flagged. "
                    "This is an exploratory signal — not a forecast.",
                    className="text-muted-velora d-block mb-2",
                ),
                dcc.Graph(id="rev-anomaly-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=7),
            dbc.Col(html.Div([
                html.P("Regional Profitability", className="card-title"),
                dcc.Graph(id="rev-region-profit-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=5),
        ], className="g-3"),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("revenue-cost-notice", "children"),
        Output("revenue-kpi-row", "children"),
        Output("rev-profit-chart", "figure"),
        Output("rev-cat-profit-chart", "figure"),
        Output("rev-anomaly-chart", "figure"),
        Output("rev-region-profit-chart", "figure"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("theme-store", "data"),
    )
    def update_revenue(start, end, theme):
        df = get_df()
        dark = (theme or "dark") == "dark"
        from components.kpi_card import kpi_card

        if not start or not end:
            return None, [], *[go.Figure()] * 4

        filt = df[(df["order_date"] >= start) & (df["order_date"] <= end)].copy()
        has_cost = "unit_cost" in filt.columns and filt["unit_cost"].notna().any()

        notice = None
        if not has_cost:
            notice = dbc.Alert(
                [html.I(className="bi bi-info-circle me-2"),
                 "Cost data (unit_cost) not available. Profit and margin features are hidden. "
                 "Upload a dataset with a unit_cost column to enable them."],
                className="velora-alert-info",
            )

        rev = filt["revenue"].sum()
        orders = len(filt)
        if has_cost:
            filt["cost"] = filt["unit_cost"] * filt["quantity"]
            filt["profit"] = filt["revenue"] - filt["cost"]
            total_profit = filt["profit"].sum()
            total_cost = filt["cost"].sum()
            margin = (total_profit / rev * 100) if rev else 0
        else:
            total_profit = None
            total_cost = None
            margin = None

        cards = [
            kpi_card("Total Revenue", format_currency(rev), None, None, "bi bi-currency-dollar"),
            kpi_card("Total Cost", format_currency(total_cost) if has_cost else "N/A",
                     None, None, "bi bi-box-arrow-down"),
            kpi_card("Gross Profit", format_currency(total_profit) if has_cost else "N/A",
                     None, None, "bi bi-graph-up"),
            kpi_card("Profit Margin", f"{margin:.1f}%" if has_cost else "N/A",
                     None, None, "bi bi-pie-chart"),
        ]

        # Revenue vs Profit
        ts = revenue_by_period(filt, "ME")
        rv_fig = go.Figure()
        rv_fig.add_trace(go.Scatter(
            x=ts["date"], y=ts["revenue"], name="Revenue",
            line=dict(color=CHART_COLORS[0], width=2), fill="tozeroy",
            fillcolor="rgba(45,212,191,0.06)",
            hovertemplate="%{x|%b %Y}<br>Revenue: $%{y:,.0f}<extra></extra>",
        ))
        if has_cost:
            prof_ts = filt.set_index("order_date").resample("ME")["profit"].sum().reset_index()
            rv_fig.add_trace(go.Scatter(
                x=prof_ts["order_date"], y=prof_ts["profit"], name="Profit",
                line=dict(color=CHART_COLORS[1], width=2),
                hovertemplate="%{x|%b %Y}<br>Profit: $%{y:,.0f}<extra></extra>",
            ))
        rv_fig.update_layout(yaxis_tickprefix="$")
        apply_velora_theme(rv_fig, dark)

        # Category profit
        if has_cost:
            cat_p = filt.groupby("category").agg(
                Revenue=("revenue", "sum"), Profit=("profit", "sum")
            ).reset_index()
            cat_p["Margin %"] = (cat_p["Profit"] / cat_p["Revenue"] * 100).round(1)
            cat_p = cat_p.sort_values("Profit", ascending=True)
            cat_fig = go.Figure(go.Bar(
                x=cat_p["Profit"], y=cat_p["category"], orientation="h",
                marker_color=[CHART_COLORS[2] if v >= 0 else CHART_COLORS[4] for v in cat_p["Profit"]],
                marker_line_width=0,
                customdata=cat_p[["Margin %"]].values,
                hovertemplate="<b>%{y}</b><br>Profit: $%{x:,.0f}<br>Margin: %{customdata[0]:.1f}%<extra></extra>",
            ))
            cat_fig.update_layout(xaxis_tickprefix="$", showlegend=False)
        else:
            cat_fig = go.Figure()
        apply_velora_theme(cat_fig, dark)

        # Anomaly detection on daily revenue
        daily = filt.set_index("order_date").resample("D")["revenue"].sum()
        is_anomaly = anomaly_zscore(daily, window=30, threshold=2.5)
        anom_fig = go.Figure()
        anom_fig.add_trace(go.Scatter(
            x=daily.index, y=daily.values, name="Daily Revenue",
            line=dict(color=CHART_COLORS[0], width=1.5),
            hovertemplate="%{x|%Y-%m-%d}<br>$%{y:,.0f}<extra></extra>",
        ))
        anomaly_days = daily[is_anomaly]
        if not anomaly_days.empty:
            anom_fig.add_trace(go.Scatter(
                x=anomaly_days.index, y=anomaly_days.values,
                mode="markers", name="Anomaly",
                marker=dict(color=CHART_COLORS[4], size=8, symbol="circle"),
                hovertemplate="%{x|%Y-%m-%d}<br>$%{y:,.0f} ⚠ Anomaly<extra></extra>",
            ))
        anom_fig.update_layout(yaxis_tickprefix="$")
        apply_velora_theme(anom_fig, dark)

        # Regional profit
        if has_cost:
            reg_p = filt.groupby("region").agg(
                Revenue=("revenue", "sum"), Profit=("profit", "sum")
            ).reset_index().sort_values("Revenue", ascending=False)
            reg_fig = go.Figure()
            reg_fig.add_trace(go.Bar(
                x=reg_p["region"], y=reg_p["Revenue"], name="Revenue",
                marker_color=CHART_COLORS[0], marker_line_width=0,
            ))
            reg_fig.add_trace(go.Bar(
                x=reg_p["region"], y=reg_p["Profit"], name="Profit",
                marker_color=CHART_COLORS[2], marker_line_width=0,
            ))
            reg_fig.update_layout(barmode="group", yaxis_tickprefix="$")
        else:
            reg_p = filt.groupby("region")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
            reg_fig = go.Figure(go.Bar(
                x=reg_p["region"], y=reg_p["revenue"],
                marker_color=CHART_COLORS[0], marker_line_width=0,
            ))
            reg_fig.update_layout(yaxis_tickprefix="$", showlegend=False)
        apply_velora_theme(reg_fig, dark)

        return notice, cards, rv_fig, cat_fig, anom_fig, reg_fig
