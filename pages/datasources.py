"""Data Sources page — upload, validate, and manage datasets."""
import base64, pathlib
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd

from services.data_loader import parse_uploaded_csv, load_sample_data, validate_dataframe
from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS

_TEMPLATE_PATH = pathlib.Path(__file__).parent.parent / "data" / "velora_sample_template.xlsx"


def layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.P("Active Dataset", className="card-title"),
                html.Div(id="ds-active-info"),
            ], className="velora-card"), md=5),
            dbc.Col(html.Div([
                html.P("Upload Your Data File", className="card-title"),
                dcc.Upload(
                    id="ds-upload",
                    children=html.Div([
                        html.I(className="bi bi-cloud-arrow-up-fill", style={"fontSize": "32px", "color": "var(--accent)"}),
                        html.Br(),
                        html.Span("Drag & drop or "),
                        html.A("click to select", className="text-accent"),
                        html.Br(),
                        html.Small("CSV or Excel (.xlsx) — any column names accepted", className="text-muted-velora"),
                    ]),
                    style={
                        "width": "100%", "height": "120px", "lineHeight": "1.4",
                        "borderWidth": "2px", "borderStyle": "dashed",
                        "borderColor": "var(--accent)", "borderRadius": "10px",
                        "textAlign": "center", "padding": "20px",
                        "cursor": "pointer", "color": "var(--text2)",
                    },
                    multiple=False,
                ),
                html.Div(id="ds-upload-feedback", className="mt-2"),
                html.Hr(style={"borderColor": "var(--border)", "opacity": "0.3", "margin": "12px 0"}),
                html.Div([
                    html.Span("Don't have a file? ", style={"fontSize": "12px", "color": "var(--text2)"}),
                    html.A(
                        [html.I(className="bi bi-file-earmark-excel me-1"), "Download sample template (.xlsx)"],
                        id="ds-template-download",
                        download="velora_sample_template.xlsx",
                        href="",
                        style={"fontSize": "12px", "color": "var(--accent)", "fontWeight": "600"},
                    ),
                ]),
            ], className="velora-card"), md=7),
        ], className="g-3 mb-4"),

        html.Div([
            html.P("Data Quality Summary", className="card-title"),
            html.Div(id="ds-quality"),
        ], className="velora-card mb-3"),

        html.Div([
            html.P("What file formats are accepted?", className="card-title"),
            html.Div([
                html.Div([
                    html.I(className="bi bi-check-circle-fill text-positive me-2"),
                    html.Strong("Any CSV or Excel file "),
                    html.Span("— column names are detected automatically", style={"color": "var(--text2)", "fontSize": "13px"}),
                ], className="mb-2"),
                html.Div([
                    html.I(className="bi bi-check-circle-fill text-positive me-2"),
                    html.Strong("Minimum: 1 date column + 1 numeric column "),
                    html.Span("(revenue / sales / amount / total…)", style={"color": "var(--text2)", "fontSize": "13px"}),
                ], className="mb-2"),
                html.Div([
                    html.I(className="bi bi-check-circle-fill text-positive me-2"),
                    html.Strong("Optional: "),
                    html.Span("Product, Category, Region, Channel, Cost — all optional, app works without them", style={"color": "var(--text2)", "fontSize": "13px"}),
                ], className="mb-2"),
                html.Div([
                    html.I(className="bi bi-info-circle text-accent me-2"),
                    html.Span("Forecasting requires at least 90 days of data", style={"color": "var(--text2)", "fontSize": "13px"}),
                ]),
            ]),
        ], className="velora-card mb-3"),

        dbc.Button(
            [html.I(className="bi bi-arrow-counterclockwise me-2"), "Reset to Sample Dataset"],
            id="ds-reset-btn", color="link", className="text-negative",
            n_clicks=0,
        ),
        dcc.Store(id="ds-reset-trigger"),
    ], className="page-content")


def register_callbacks(app, get_df, set_df):
    @app.callback(
        Output("ds-template-download", "href"),
        Input("ds-template-download", "id"),
    )
    def set_template_href(_):
        xlsx_bytes = _TEMPLATE_PATH.read_bytes()
        b64 = base64.b64encode(xlsx_bytes).decode()
        return (
            "data:application/vnd.openxmlformats-officedocument"
            f".spreadsheetml.sheet;base64,{b64}"
        )

    @app.callback(
        Output("ds-active-info", "children"),
        Output("ds-quality", "children"),
        Input("date-range-picker", "start_date"),
        Input("ds-reset-trigger", "data"),
    )
    def refresh_info(_, __):
        df = get_df()
        has_cost = "unit_cost" in df.columns and df["unit_cost"].notna().any()
        has_channel = "channel" in df.columns and df["channel"].notna().any()

        info = dbc.Table([
            html.Tbody([
                html.Tr([html.Td("Rows"), html.Td(f"{len(df):,}")]),
                html.Tr([html.Td("Columns"), html.Td(", ".join(df.columns.tolist()))]),
                html.Tr([html.Td("Date range"),
                         html.Td(f"{df['order_date'].min().date()} → {df['order_date'].max().date()}")]),
                html.Tr([html.Td("Cost data"), html.Td("✓ Available" if has_cost else "✗ Not available")]),
                html.Tr([html.Td("Channel data"), html.Td("✓ Available" if has_channel else "✗ Not available")]),
            ])
        ], bordered=False, className="velora-table")

        # Quality checks
        nulls = df[REQUIRED_COLUMNS].isnull().sum()
        negs = {c: int((df[c] < 0).sum()) for c in ["quantity", "unit_price", "revenue"] if c in df.columns}
        dupes = int(df["order_id"].duplicated().sum()) if "order_id" in df.columns else 0

        issues = []
        for col, n in nulls.items():
            if n > 0:
                issues.append(f"⚠ {col}: {n} null values")
        for col, n in negs.items():
            if n > 0:
                issues.append(f"⚠ {col}: {n} negative values")
        if dupes:
            issues.append(f"⚠ {dupes} duplicate order IDs")

        if issues:
            quality = dbc.Alert("\n".join(issues), className="velora-alert-warn")
        else:
            quality = dbc.Alert(
                [html.I(className="bi bi-check-circle-fill me-2 text-positive"),
                 "No data quality issues detected."],
                className="velora-alert-info",
            )

        return info, quality

    @app.callback(
        Output("ds-upload-feedback", "children"),
        Output("ds-reset-trigger", "data"),
        Input("ds-upload", "contents"),
        State("ds-upload", "filename"),
        prevent_initial_call=True,
    )
    def handle_upload(contents, filename):
        if not contents:
            return None, None
        df, errors = parse_uploaded_csv(contents, filename)
        if df is None:
            msgs = [dbc.Alert(e, className="velora-alert-error") for e in errors]
            return msgs, None

        set_df(df)
        # Only show real warnings (not mapping info notes)
        real_warnings = [dbc.Alert(e, className="velora-alert-warn small")
                         for e in errors if not e.startswith("ℹ")]
        success = dbc.Alert(
            [html.I(className="bi bi-check-circle-fill me-2 text-positive"),
             f"✓ '{filename}' loaded successfully — {len(df):,} rows ready. ",
             html.A("Go to Overview →", href="/overview",
                    style={"color": "var(--accent)", "fontWeight": "600"})],
            className="velora-alert-info",
        )
        return [success] + real_warnings, {"loaded": filename}

    @app.callback(
        Output("ds-reset-trigger", "data", allow_duplicate=True),
        Input("ds-reset-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def reset_to_sample(n):
        if n:
            set_df(load_sample_data())
            return {"reset": True}
        return None
