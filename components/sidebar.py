"""Collapsible sidebar navigation."""
from dash import html, dcc
import dash_bootstrap_components as dbc
from config import PAGES


def build_sidebar() -> html.Div:
    nav_items = []
    for page in PAGES:
        nav_items.append(
            dbc.NavLink(
                [html.I(className=f"{page['icon']} me-2"), page["label"]],
                href=f"/{page['id']}",
                id=f"nav-{page['id']}",
                active="exact",
                className="velora-nav-link",
            )
        )

    return html.Div(
        id="sidebar",
        className="velora-sidebar",
        children=[
            html.Div(
                className="velora-logo",
                children=[
                    html.Div("V", className="velora-logo-icon"),
                    html.Div([
                        html.Span("VELORA", className="velora-logo-name"),
                        html.Span("AI", className="velora-logo-ai"),
                    ], className="velora-logo-text", id="sidebar-logo-text"),
                ],
            ),
            html.Hr(className="velora-divider"),
            dbc.Nav(nav_items, vertical=True, pills=True, className="velora-nav"),
            html.Div(
                [
                    html.Div("ALJOUHARA ABUTALIB",
                             style={
                                 "fontSize": "13px",
                                 "fontWeight": "800",
                                 "letterSpacing": "0.08em",
                                 "color": "var(--accent)",
                                 "textTransform": "uppercase",
                                 "lineHeight": "1.3",
                             }),
                    html.Small("Intelligence Beyond Data", className="velora-tagline",
                               style={"opacity": "0.6", "fontSize": "10px"}),
                ],
                id="sidebar-tagline",
                className="mt-auto px-3 pb-3",
            ),
        ],
    )
