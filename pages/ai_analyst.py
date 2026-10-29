"""AI Analyst chat page."""
from dash import html, dcc, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import json

from services.ai_client import ask

EXAMPLE_PROMPTS = [
    "What were our best-performing products?",
    "Which categories contribute the most revenue?",
    "Summarize our latest sales performance.",
    "What actions could improve profitability?",
    "What trends should management watch?",
]


def layout() -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div(id="ai-status-badge", className="mb-3"),
                html.Div([
                    # Chat messages area
                    html.Div(id="chat-messages", className="chat-messages", children=[
                        html.Div(id="ai-welcome-msg"),
                    ]),
                    # Input row
                    html.Div([
                        dcc.Input(
                            id="chat-input",
                            type="text",
                            placeholder="Ask about your data…",
                            debounce=False,
                            className="chat-input",
                            n_submit=0,
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-send me-1"), "Send"],
                            id="chat-send-btn",
                            className="chat-send-btn",
                            n_clicks=0,
                        ),
                    ], className="chat-input-row"),
                ], className="velora-card chat-container"),
            ], md=8),
            dbc.Col([
                html.Div([
                    html.P("Example Questions", className="card-title"),
                    html.Div([
                        dbc.Button(p, id={"type": "example-prompt", "index": i},
                                   color="link", className="d-block text-start p-1 text-accent2 small",
                                   n_clicks=0)
                        for i, p in enumerate(EXAMPLE_PROMPTS)
                    ]),
                ], className="velora-card mb-3"),
                html.Div([
                    html.P("Tips", className="card-title"),
                    html.Ul([
                        html.Li("Questions are answered from the currently loaded dataset."),
                        html.Li("Date range filter applies — ask about the visible period."),
                        html.Li("In Demo mode, no external API is called."),
                        html.Li("Answers show real figures, not invented statistics."),
                    ], className="small text-muted-velora ps-3"),
                ], className="velora-card"),
            ], md=4),
        ], className="g-3"),

        # Hidden stores
        dcc.Store(id="chat-history-store", data=[]),
    ], className="page-content")


def register_callbacks(app, get_df):
    @app.callback(
        Output("ai-status-badge", "children"),
        Output("ai-welcome-msg", "children"),
        Input("theme-store", "data"),
    )
    def show_status(_):
        from services.ai_client import _has_live_key
        if _has_live_key():
            badge = html.Span([
                html.I(className="bi bi-circle-fill text-positive me-1", style={"fontSize": "9px"}),
                "Live AI mode active",
            ], className="velora-badge-teal")
            welcome = html.Div([
                html.Strong("VELORA AI Analyst"),
                html.Br(),
                dcc.Markdown(
                    "Hello! I can answer questions about your sales data using **Live AI** "
                    "(claude-haiku-4-5). Ask me anything about revenue, products, regions, trends, "
                    "or profitability."
                ),
            ], className="chat-msg-ai")
        else:
            badge = html.Span([
                html.I(className="bi bi-circle-fill me-1", style={"fontSize": "9px", "color": "var(--warning)"}),
                "Demo mode — no API key configured",
            ], className="demo-badge")
            welcome = html.Div([
                html.Strong("VELORA AI Analyst"),
                html.Br(),
                dcc.Markdown(
                    "Hello! I can answer questions about your sales data. "
                    "Running in **Demo mode** — answers computed from real data, "
                    "no external AI model called. Add an API key in Settings to enable live AI."
                ),
                html.Span("Demo mode — no AI model was called", className="demo-badge ms-2"),
            ], className="chat-msg-ai demo-mode")
        return badge, welcome

    @app.callback(
        Output("chat-input", "value"),
        Input({"type": "example-prompt", "index": 0}, "n_clicks"),
        Input({"type": "example-prompt", "index": 1}, "n_clicks"),
        Input({"type": "example-prompt", "index": 2}, "n_clicks"),
        Input({"type": "example-prompt", "index": 3}, "n_clicks"),
        Input({"type": "example-prompt", "index": 4}, "n_clicks"),
        prevent_initial_call=True,
    )
    def fill_example(*args):
        ctx = callback_context
        if not ctx.triggered:
            return ""
        prop = ctx.triggered[0]["prop_id"]
        try:
            idx = json.loads(prop.split(".")[0])["index"]
            return EXAMPLE_PROMPTS[idx]
        except Exception:
            return ""

    @app.callback(
        Output("chat-messages", "children"),
        Output("chat-history-store", "data"),
        Output("chat-input", "value", allow_duplicate=True),
        Input("chat-send-btn", "n_clicks"),
        Input("chat-input", "n_submit"),
        State("chat-input", "value"),
        State("chat-history-store", "data"),
        State("date-range-picker", "start_date"),
        State("date-range-picker", "end_date"),
        prevent_initial_call=True,
    )
    def handle_message(n_clicks, n_submit, question, history, start, end):
        if not question or not question.strip():
            from dash import no_update
            return no_update, history, ""

        df = get_df()
        if start and end:
            df = df[(df["order_date"] >= start) & (df["order_date"] <= end)]

        answer, is_demo = ask(question.strip(), df, history or [])

        history = (history or [])
        history.append({"role": "user", "content": question.strip()})
        history.append({"role": "assistant", "content": answer})

        # Build message bubbles
        bubbles = []
        for i, msg in enumerate(history):
            if msg["role"] == "user":
                bubbles.append(html.Div(msg["content"], className="chat-msg-user"))
            else:
                cls = "chat-msg-ai demo-mode" if is_demo else "chat-msg-ai"
                bubbles.append(html.Div([
                    dcc.Markdown(msg["content"]),
                    html.Span("Demo mode — no AI model was called", className="demo-badge ms-1") if is_demo else None,
                ], className=cls))

        # Prepend the initial greeting bubble
        greeting = html.Div([
            html.Strong("VELORA AI Analyst"),
            html.Br(),
            dcc.Markdown("Hello! Ask me anything about your data."),
        ], className="chat-msg-ai")

        return [greeting] + bubbles, history, ""
