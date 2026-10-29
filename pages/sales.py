"""Sales Analytics page."""
from dash import html, dcc, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd

from services.metrics import format_currency, revenue_by_period
from services.chart_theme import apply_velora_theme, CHART_COLORS


def layout() -> html.Div:
    return html.Div([
        # Filters
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Category", className="text-muted-velora small mb-1"),
                    dcc.Dropdown(id="sales-cat-filter", multi=True, placeholder="All categories",
                                 className="velora-dropdown"),
                ], md=3),
                dbc.Col([
                    html.Label("Region", className="text-muted-velora small mb-1"),
                    dcc.Dropdown(id="sales-region-filter", multi=True, placeholder="All regions",
                                 className="velora-dropdown"),
                ], md=3),
                dbc.Col([
                    html.Label("Channel", className="text-muted-velora small mb-1"),
                    dcc.Dropdown(id="sales-channel-filter", multi=True, placeholder="All channels",
                                 className="velora-dropdown"),
                ], md=3),
                dbc.Col([
                    html.Label("Granularity", className="text-muted-velora small mb-1"),
                    dcc.Dropdown(id="sales-freq", options=[
                        {"label": "Daily", "value": "D"},
                        {"label": "Weekly", "value": "W"},
                        {"label": "Monthly", "value": "ME"},
                    ], value="W", clearable=False, className="velora-dropdown"),
                ], md=3),
            ], className="g-3"),
        ], className="velora-card mb-4"),

        # KPI row
        dbc.Row(id="sales-kpi-row", className="g-3 mb-4"),

        # Trend chart
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Sales Trend", className="card-title"),
                dcc.Graph(id="sales-trend-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=8),
            dbc.Col(html.Div([
                html.P("Revenue by Channel", className="card-title"),
                html.Div(id="sales-channel-note"),
                dcc.Graph(id="sales-channel-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=4),
        ], className="g-3 mb-3"),

        # Category + Region
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Category Performance", className="card-title"),
                dcc.Graph(id="sales-category-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=6),
            dbc.Col(html.Div([
                html.P("Regional Comparison", className="card-title"),
                dcc.Graph(id="sales-region-chart", config={"displayModeBar": False}),
            ], className="velora-card"), md=6),
        ], className="g-3 mb-3"),

        # Product table
        html.Div([
            dbc.Row([
                dbc.Col(html.P("Product Performance", className="card-title mb-0"), md=8),
                dbc.Col(dbc.Button(
                    [html.I(className="bi bi-download me-2"), "Export CSV"],
                    id="sales-export-btn", color="link", size="sm",
                    className="float-end text-accent",
                ), md=4),
            ], align="center", className="mb-3"),
            dcc.Download(id="sales-download"),
            html.Div(id="sales-product-table"),
        ], className="velora-card"),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("sales-cat-filter", "options"),
        Output("sales-region-filter", "options"),
        Output("sales-channel-filter", "options"),
        Input("date-range-picker", "start_date"),
    )
    def populate_filters(_):
        df = get_df()
        cats = [{"label": c, "value": c} for c in sorted(df["category"].unique())]
        regs = [{"label": r, "value": r} for r in sorted(df["region"].unique())]
        chans = []
        if "channel" in df.columns:
            chans = [{"label": c, "value": c} for c in sorted(df["channel"].dropna().unique())]
        return cats, regs, chans

    @app.callback(
        Output("sales-kpi-row", "children"),
        Output("sales-trend-chart", "figure"),
        Output("sales-channel-chart", "figure"),
        Output("sales-channel-note", "children"),
        Output("sales-category-chart", "figure"),
        Output("sales-region-chart", "figure"),
        Output("sales-product-table", "children"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("sales-cat-filter", "value"),
        Input("sales-region-filter", "value"),
        Input("sales-channel-filter", "value"),
        Input("sales-freq", "value"),
        Input("theme-store", "data"),
    )
    def update_sales(start, end, cats, regions, channels, freq, theme):
        df = get_df()
        dark = (theme or "dark") == "dark"
        if not start or not end:
            return [], *[go.Figure()] * 4, None, []

        filt = df[(df["order_date"] >= start) & (df["order_date"] <= end)].copy()
        if cats:
            filt = filt[filt["category"].isin(cats)]
        if regions:
            filt = filt[filt["region"].isin(regions)]
        if channels and "channel" in filt.columns:
            filt = filt[filt["channel"].isin(channels)]

        if filt.empty:
            note = dbc.Alert("No data for selected filters.", color="warning", className="velora-alert-warn")
            return [], *[go.Figure()] * 4, note, []

        # KPI cards (mini)
        from components.kpi_card import kpi_card
        from services.metrics import period_comparison, format_pct
        comp = period_comparison(df, start, end)
        pct = comp.get("pct_change") or {}

        def dp(k):
            v = pct.get(k)
            return (format_pct(v), v >= 0) if v is not None else (None, None)

        rev_d, rev_p = dp("revenue")
        ord_d, ord_p = dp("orders")
        rev = filt["revenue"].sum()
        orders = len(filt)
        aov = rev / orders if orders else 0
        cards = [
            kpi_card("Revenue", format_currency(rev), rev_d, rev_p, "bi bi-currency-dollar"),
            kpi_card("Orders", f"{orders:,}", ord_d, ord_p, "bi bi-bag"),
            kpi_card("Avg Order Value", format_currency(aov), None, None, "bi bi-receipt"),
            kpi_card("Unique Products", str(filt["product"].nunique()), None, None, "bi bi-box-seam"),
        ]

        # Trend
        ts = revenue_by_period(filt, freq)
        trend_fig = go.Figure(go.Scatter(
            x=ts["date"], y=ts["revenue"], mode="lines",
            fill="tozeroy", fillcolor="rgba(45,212,191,0.08)",
            line=dict(color=CHART_COLORS[0], width=2),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>$%{y:,.0f}<extra></extra>",
        ))
        trend_fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        apply_velora_theme(trend_fig, dark)

        # Channel
        channel_note = None
        if "channel" in filt.columns and filt["channel"].notna().any():
            ch = filt.groupby("channel")["revenue"].sum().reset_index()
            ch_fig = go.Figure(go.Pie(
                labels=ch["channel"], values=ch["revenue"], hole=0.5,
                marker_colors=CHART_COLORS,
                hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
            ))
            apply_velora_theme(ch_fig, dark)
        else:
            ch_fig = go.Figure()
            apply_velora_theme(ch_fig, dark)
            channel_note = html.Small("No channel data available.", className="text-muted-velora")

        # Category
        cat_df = filt.groupby("category")["revenue"].sum().reset_index().sort_values("revenue", ascending=False)
        cat_fig = go.Figure(go.Bar(
            x=cat_df["category"], y=cat_df["revenue"],
            marker_color=CHART_COLORS, marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
        ))
        cat_fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        apply_velora_theme(cat_fig, dark)

        # Region
        reg_df = filt.groupby("region")["revenue"].sum().reset_index().sort_values("revenue")
        reg_fig = go.Figure(go.Bar(
            x=reg_df["revenue"], y=reg_df["region"], orientation="h",
            marker_color=CHART_COLORS[1], marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
        ))
        reg_fig.update_layout(showlegend=False, xaxis_tickprefix="$")
        apply_velora_theme(reg_fig, dark)

        # Product table
        prod_df = filt.groupby("product").agg(
            Revenue=("revenue", "sum"),
            Orders=("order_id", "count"),
            Quantity=("quantity", "sum"),
        ).reset_index().sort_values("Revenue", ascending=False)
        prod_df["Revenue"] = prod_df["Revenue"].map(lambda x: f"${x:,.2f}")

        tbl = dash_table.DataTable(
            data=prod_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in prod_df.columns],
            sort_action="native", filter_action="native", page_size=15,
            style_table={"overflowX": "auto"},
            style_cell={"backgroundColor": "transparent", "color": "var(--text)",
                        "border": "1px solid var(--border)", "fontSize": "13px", "padding": "8px 12px"},
            style_header={"backgroundColor": "var(--elevated)", "fontWeight": "600",
                          "color": "var(--text2)", "border": "1px solid var(--border)",
                          "textTransform": "uppercase", "fontSize": "11px"},
            style_data_conditional=[{"if": {"state": "active"}, "backgroundColor": "var(--elevated)"}],
        )
        return cards, trend_fig, ch_fig, channel_note, cat_fig, reg_fig, tbl

    @app.callback(
        Output("sales-download", "data"),
        Input("sales-export-btn", "n_clicks"),
        State("date-range-picker", "start_date"),
        State("date-range-picker", "end_date"),
        State("sales-cat-filter", "value"),
        State("sales-region-filter", "value"),
        prevent_initial_call=True,
    )
    def export_csv(n, start, end, cats, regions):
        df = get_df()
        filt = df[(df["order_date"] >= start) & (df["order_date"] <= end)]
        if cats:
            filt = filt[filt["category"].isin(cats)]
        if regions:
            filt = filt[filt["region"].isin(regions)]
        return dcc.send_data_frame(filt.to_csv, "velora_sales_export.csv", index=False)
