"""Shared Plotly chart theme for VELORA AI."""
import plotly.graph_objects as go
import plotly.io as pio
from config import COLORS, CHART_COLORS


def apply_velora_theme(fig: go.Figure, dark: bool = True) -> go.Figure:
    """Apply the VELORA dark/light theme to any Plotly figure."""
    bg = COLORS["bg"] if dark else "#F1F5F9"
    card = COLORS["card"] if dark else "#FFFFFF"
    text = COLORS["text"] if dark else "#0F172A"
    text2 = COLORS["text2"] if dark else "#475569"
    border = COLORS["border"] if dark else "#CBD5E1"
    grid = "#1E2D42" if dark else "#E2E8F0"

    fig.update_layout(
        paper_bgcolor=card,
        plot_bgcolor=card,
        font=dict(family="Inter, system-ui, sans-serif", color=text, size=13),
        title_font=dict(size=15, color=text),
        margin=dict(l=16, r=16, t=40, b=16),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=text2),
            bordercolor=border,
            borderwidth=1,
        ),
        colorway=CHART_COLORS,
        hoverlabel=dict(
            bgcolor=card,
            bordercolor=border,
            font_color=text,
        ),
    )
    fig.update_xaxes(
        gridcolor=grid,
        zerolinecolor=grid,
        tickfont=dict(color=text2),
        linecolor=border,
    )
    fig.update_yaxes(
        gridcolor=grid,
        zerolinecolor=grid,
        tickfont=dict(color=text2),
        linecolor=border,
    )
    return fig


def line_chart(x, y, name: str = "", color: str = None, dark: bool = True) -> go.Figure:
    c = color or CHART_COLORS[0]
    fig = go.Figure(go.Scatter(
        x=x, y=y, name=name, mode="lines",
        line=dict(color=c, width=2),
        fill="tozeroy",
        fillcolor=f"rgba({_hex_to_rgb(c)},0.10)",
    ))
    return apply_velora_theme(fig, dark)


def bar_chart(x, y, name: str = "", color: str = None, dark: bool = True) -> go.Figure:
    c = color or CHART_COLORS[0]
    fig = go.Figure(go.Bar(x=x, y=y, name=name, marker_color=c, marker_line_width=0))
    return apply_velora_theme(fig, dark)


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"
