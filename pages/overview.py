"""Overview dashboard page."""
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from components.kpi_card import kpi_card
from services.metrics import (
    kpi_summary, period_comparison, revenue_by_period,
    top_products, revenue_by_category, revenue_by_region,
    format_currency, format_pct, executive_summary
)
from services.chart_theme import apply_velora_theme, CHART_COLORS


def layout() -> html.Div:
    return html.Div([
        # KPI row
        dbc.Row(id="overview-kpi-row", className="g-3 mb-4"),
        # Executive summary
        html.Div(id="overview-exec-summary", className="mb-4"),
        # Charts row 1
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Revenue Over Time", className="card-title"),
                dcc.Graph(id="overview-revenue-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=8),
            dbc.Col(html.Div([
                html.P("Revenue by Category", className="card-title"),
                dcc.Graph(id="overview-category-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=4),
        ], className="g-3 mb-3"),
        # Charts row 2
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Sales by Region", className="card-title"),
                dcc.Graph(id="overview-region-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=6),
            dbc.Col(html.Div([
                html.P("Top Products", className="card-title"),
                dcc.Graph(id="overview-top-products", config={"displayModeBar": False}),
            ], className="velora-card"), md=6),
        ], className="g-3 mb-3"),
        # Recent transactions
        html.Div([
            html.P("Recent Transactions", className="card-title"),
            html.Div(id="overview-transactions-table"),
        ], className="velora-card"),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("overview-kpi-row", "children"),
        Output("overview-exec-summary", "children"),
        Output("overview-revenue-chart", "figure"),
        Output("overview-category-chart", "figure"),
        Output("overview-region-chart", "figure"),
        Output("overview-top-products", "figure"),
        Output("overview-transactions-table", "children"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("theme-store", "data"),
    )
    def update_overview(start, end, theme):
        df = get_df()
        dark = (theme or "dark") == "dark"

        if not start or not end:
            return [], _empty_msg("Select a date range"), *[go.Figure()] * 4, []

        filtered = df[(df["order_date"] >= start) & (df["order_date"] <= end)]
        if filtered.empty:
            return [], _empty_msg("No data for selected range"), *[go.Figure()] * 4, []

        comp = period_comparison(df, start, end)
        cur = comp["current"]
        pct = comp["pct_change"]

        has_cost = cur["profit"] is not None

        def delta(key, higher_is_better=True):
            if pct is None or pct.get(key) is None:
                return None, None
            v = pct[key]
            pos = v >= 0 if higher_is_better else v <= 0
            return format_pct(v), pos

        rev_d, rev_pos = delta("revenue")
        ord_d, ord_pos = delta("orders")
        aov_d, aov_pos = delta("aov")
        prof_d, prof_pos = delta("profit")

        cards = [
            kpi_card("Total Revenue", format_currency(cur["revenue"]), rev_d, rev_pos, "bi bi-currency-dollar"),
            kpi_card("Total Orders", f"{cur['orders']:,}", ord_d, ord_pos, "bi bi-bag"),
            kpi_card("Avg Order Value", format_currency(cur["aov"]), aov_d, aov_pos, "bi bi-receipt"),
            kpi_card(
                "Gross Profit", format_currency(cur["profit"]) if has_cost else "N/A — no cost data",
                prof_d if has_cost else None, prof_pos if has_cost else None, "bi bi-graph-up",
                subtitle="Cost data required" if not has_cost else "vs prior period",
            ),
            kpi_card(
                "Profit Margin",
                f"{cur['margin']:.1f}%" if has_cost else "N/A",
                None, None, "bi bi-pie-chart",
                subtitle="Gross margin" if has_cost else "Cost data required",
            ),
            kpi_card(
                "Revenue Growth",
                format_pct(pct["revenue"]) if pct and pct.get("revenue") is not None else "—",
                None, None, "bi bi-arrow-up-right-circle",
                subtitle="vs prior period" if pct else "Not enough history",
            ),
        ]

        # Executive summary
        summary_md = executive_summary(filtered, comp)
        summary_el = html.Div([
            html.P("Executive Summary", className="card-title"),
            dcc.Markdown(summary_md, className="executive-summary"),
        ], className="velora-card")

        # Revenue over time
        rev_ts = revenue_by_period(filtered, "W")
        rev_fig = go.Figure(go.Scatter(
            x=rev_ts["date"], y=rev_ts["revenue"], mode="lines",
            fill="tozeroy", fillcolor="rgba(45,212,191,0.08)",
            line=dict(color=CHART_COLORS[0], width=2.5),
            hovertemplate="<b>%{x|%b %d}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
        ))
        rev_fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        apply_velora_theme(rev_fig, dark)

        # Category donut
        cat_df = revenue_by_category(filtered)
        cat_fig = go.Figure(go.Pie(
            labels=cat_df["category"], values=cat_df["revenue"],
            hole=0.55, marker_colors=CHART_COLORS,
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>",
        ))
        cat_fig.update_layout(showlegend=True, legend=dict(orientation="v"))
        apply_velora_theme(cat_fig, dark)

        # Region bar
        reg_df = revenue_by_region(filtered)
        reg_fig = go.Figure(go.Bar(
            x=reg_df["revenue"], y=reg_df["region"], orientation="h",
            marker_color=CHART_COLORS[1], marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
        ))
        reg_fig.update_layout(showlegend=False, xaxis_tickprefix="$")
        apply_velora_theme(reg_fig, dark)

        # Top products
        top_df = top_products(filtered, 8)
        prod_fig = go.Figure(go.Bar(
            x=top_df["revenue"], y=top_df["product"], orientation="h",
            marker_color=CHART_COLORS[2], marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
        ))
        prod_fig.update_layout(showlegend=False, xaxis_tickprefix="$")
        apply_velora_theme(prod_fig, dark)

        # Recent transactions table
        recent = filtered.sort_values("order_date", ascending=False).head(10)
        tbl = dbc.Table.from_dataframe(
            recent[["order_date", "order_id", "product", "category", "region", "quantity", "revenue"]].assign(
                order_date=recent["order_date"].dt.strftime("%Y-%m-%d"),
                revenue=recent["revenue"].map(lambda x: f"${x:,.2f}"),
            ),
            striped=False, bordered=False, hover=True,
            className="velora-table",
        )

        return cards, summary_el, rev_fig, cat_fig, reg_fig, prod_fig, tbl


def _empty_msg(msg: str) -> html.Div:
    return html.Div([
        html.I(className="bi bi-info-circle"),
        html.P(msg),
    ], className="empty-state")
