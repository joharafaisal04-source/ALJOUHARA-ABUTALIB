"""KPI metric card component."""
from dash import html
import dash_bootstrap_components as dbc
from typing import Optional


def kpi_card(
    title: str,
    value: str,
    change: Optional[str] = None,
    change_positive: Optional[bool] = None,
    icon: str = "bi bi-graph-up",
    subtitle: str = "",
    card_id: str = "",
) -> dbc.Col:
    """
    Render a single KPI card.
    change_positive=True → green, False → red, None → neutral
    """
    if change is not None:
        if change_positive is True:
            badge_cls = "kpi-badge kpi-badge-pos"
            badge_icon = "bi bi-arrow-up-right"
        elif change_positive is False:
            badge_cls = "kpi-badge kpi-badge-neg"
            badge_icon = "bi bi-arrow-down-right"
        else:
            badge_cls = "kpi-badge kpi-badge-neutral"
            badge_icon = "bi bi-dash"
        badge = html.Span(
            [html.I(className=f"{badge_icon} me-1"), change],
            className=badge_cls,
        )
    else:
        badge = html.Span("Not enough history", className="kpi-badge kpi-badge-neutral")

    div_kwargs = {"className": "velora-card kpi-card"}
    if card_id:
        div_kwargs["id"] = card_id

    return dbc.Col(
        html.Div(
            **div_kwargs,
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.P(title, className="kpi-title"),
                                html.H3(value, className="kpi-value"),
                            ]
                        ),
                        html.Div(
                            html.I(className=f"{icon} kpi-icon"),
                            className="kpi-icon-wrap",
                        ),
                    ],
                    className="kpi-top",
                ),
                html.Div(
                    [badge, html.Small(subtitle, className="kpi-subtitle ms-2")],
                    className="kpi-bottom",
                ),
            ],
        ),
        xs=12, sm=6, md=4, xl=2,
    )
