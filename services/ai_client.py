"""
AI Analyst service.
All AI calls are isolated here. Demo mode runs with no API calls.
Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env to enable live mode.
"""
from __future__ import annotations

import os
import pandas as pd
from dotenv import load_dotenv
from services.metrics import (
    kpi_summary, revenue_by_category, revenue_by_region,
    top_products, format_currency
)

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _has_live_key() -> bool:
    return bool(OPENAI_KEY and not OPENAI_KEY.startswith("your_")) or \
           bool(ANTHROPIC_KEY and not ANTHROPIC_KEY.startswith("your_"))


def _build_context_summary(df: pd.DataFrame) -> str:
    """Compute key figures to ground the AI answer in real data."""
    kpi = kpi_summary(df)
    cats = revenue_by_category(df).head(3)
    top = top_products(df, 5)
    regs = revenue_by_region(df).head(3)

    lines = [
        f"Period: {df['order_date'].min().date()} to {df['order_date'].max().date()}",
        f"Total revenue: {format_currency(kpi['revenue'])}",
        f"Total orders: {kpi['orders']:,}",
        f"Average order value: {format_currency(kpi['aov'])}",
    ]
    if kpi["profit"] is not None:
        lines.append(f"Gross profit: {format_currency(kpi['profit'])} ({kpi['margin']:.1f}% margin)")

    lines.append("Top categories by revenue: " +
                 ", ".join(f"{r['category']} ({format_currency(r['revenue'])})"
                           for _, r in cats.iterrows()))
    lines.append("Top 5 products: " +
                 ", ".join(f"{r['product']} ({format_currency(r['revenue'])})"
                           for _, r in top.iterrows()))
    lines.append("Top regions: " +
                 ", ".join(f"{r['region']} ({format_currency(r['revenue'])})"
                           for _, r in regs.iterrows()))
    return "\n".join(lines)


def _demo_answer(question: str, df: pd.DataFrame) -> str:
    """
    Answer common questions from real data, with no API call.
    Clearly labeled as demo mode.
    """
    q = question.lower()
    kpi = kpi_summary(df)

    if any(w in q for w in ["best", "top", "highest", "performing product"]):
        top = top_products(df, 5)
        rows = "\n".join(f"- **{r['product']}**: {format_currency(r['revenue'])}"
                         for _, r in top.iterrows())
        return f"**Top 5 products by revenue:**\n\n{rows}"

    if any(w in q for w in ["category", "categories"]):
        cats = revenue_by_category(df)
        rows = "\n".join(f"- **{r['category']}**: {format_currency(r['revenue'])} "
                         f"({r['revenue']/kpi['revenue']*100:.1f}%)"
                         for _, r in cats.iterrows())
        return f"**Revenue by category:**\n\n{rows}"

    if any(w in q for w in ["region", "regions", "geographic"]):
        regs = revenue_by_region(df)
        rows = "\n".join(f"- **{r['region']}**: {format_currency(r['revenue'])}"
                         for _, r in regs.iterrows())
        return f"**Revenue by region:**\n\n{rows}"

    if any(w in q for w in ["revenue", "sales", "summary", "performance"]):
        ctx = _build_context_summary(df)
        return f"**Sales Summary**\n\n{ctx}"

    if any(w in q for w in ["profit", "margin", "cost"]):
        if kpi["profit"] is not None:
            return (f"**Profitability Overview**\n\n"
                    f"- Gross profit: **{format_currency(kpi['profit'])}**\n"
                    f"- Profit margin: **{kpi['margin']:.1f}%**")
        return ("Cost data (`unit_cost`) is available in the dataset. "
                "Profit = Revenue − Cost. Currently: "
                f"Revenue = {format_currency(kpi['revenue'])}.")

    if any(w in q for w in ["improve", "action", "recommend", "suggest"]):
        cats = revenue_by_category(df)
        best_cat = cats.iloc[0]["category"]
        worst_cat = cats.iloc[-1]["category"]
        return (f"**Data-Driven Suggestions** *(based on current data only)*\n\n"
                f"1. **Double down on {best_cat}** — it is your highest-revenue category.\n"
                f"2. **Review {worst_cat}** — lowest revenue; consider whether pricing or "
                f"   product mix can be improved.\n"
                f"3. **Monitor average order value** (currently {format_currency(kpi['aov'])}) "
                f"   — bundling or upsells may increase it.\n"
                f"4. **Expand in top regions** — see Regional analysis for details.")

    if any(w in q for w in ["trend", "watch", "management"]):
        return (
            "**Trends to Watch** *(derived from data)*\n\n"
            "- Compare revenue week-over-week on the Sales page for momentum shifts.\n"
            "- Monitor the anomaly chart on the Revenue page for unusual days.\n"
            "- Use the Forecasting page to see the model's 30/90-day outlook.\n"
            "- Review channel mix if channel data is available."
        )

    # Fallback
    return (
        "I can answer questions about your revenue, top products, categories, regions, "
        "profitability, and actionable suggestions — all grounded in the loaded dataset.\n\n"
        "Try asking: *What were our top products?* or *Which categories drive the most revenue?*"
    )


def ask(question: str, df: pd.DataFrame, history: list[dict]) -> tuple[str, bool]:
    """
    Ask a question. Returns (answer_text, is_demo_mode).
    Never makes API calls unless a valid key is configured.
    """
    if not _has_live_key():
        answer = _demo_answer(question, df)
        return answer, True

    # Live mode — only reached with a valid key
    ctx = _build_context_summary(df)
    system_prompt = (
        "You are VELORA AI Analyst, an expert business intelligence assistant. "
        "Answer questions strictly based on the data context provided. "
        "Never fabricate statistics or causes not supported by the data. "
        "If the data cannot answer the question, say so clearly."
    )
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-6:]:  # last 3 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user",
                     "content": f"Data context:\n{ctx}\n\nQuestion: {question}"})

    try:
        if OPENAI_KEY and not OPENAI_KEY.startswith("your_"):
            import openai
            client = openai.OpenAI(api_key=OPENAI_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages, max_tokens=600, timeout=20
            )
            return resp.choices[0].message.content, False

        if ANTHROPIC_KEY and not ANTHROPIC_KEY.startswith("your_"):
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                system=system_prompt,
                messages=[m for m in messages if m["role"] != "system"],
            )
            return resp.content[0].text, False

    except Exception as e:
        err_type = type(e).__name__
        if "rate" in str(e).lower():
            return "Rate limit reached — please wait a moment and try again.", False
        if "auth" in str(e).lower() or "key" in str(e).lower():
            return "API key error. Please check your key in Settings.", False
        return f"AI service unavailable ({err_type}). Try again shortly.", False

    return _demo_answer(question, df), True
