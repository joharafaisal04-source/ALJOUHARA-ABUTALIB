"""KPI calculations and metric helpers."""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def kpi_summary(df: pd.DataFrame) -> dict:
    """Compute core KPIs from a filtered dataframe."""
    revenue = df["revenue"].sum()
    orders = len(df)
    aov = revenue / orders if orders else 0.0

    has_cost = "unit_cost" in df.columns and df["unit_cost"].notna().any()
    if has_cost:
        cost = (df["unit_cost"] * df["quantity"]).sum()
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue else 0.0
    else:
        cost = None
        profit = None
        margin = None

    return {
        "revenue": revenue,
        "orders": orders,
        "aov": aov,
        "cost": cost,
        "profit": profit,
        "margin": margin,
    }


def period_comparison(
    df: pd.DataFrame, current_start: str, current_end: str
) -> dict:
    """
    Compare current period KPIs vs the equal-length preceding period.
    Returns a dict with 'current', 'previous', and 'pct_change' (or None if no prior data).
    """
    cs = pd.Timestamp(current_start)
    ce = pd.Timestamp(current_end)
    delta = ce - cs

    prev_end = cs - pd.Timedelta(days=1)
    prev_start = prev_end - delta

    cur_df = df[(df["order_date"] >= cs) & (df["order_date"] <= ce)]
    prev_df = df[(df["order_date"] >= prev_start) & (df["order_date"] <= prev_end)]

    cur = kpi_summary(cur_df)
    prev = kpi_summary(prev_df)

    if len(prev_df) == 0:
        return {"current": cur, "previous": None, "pct_change": None}

    pct = {}
    for k in ["revenue", "orders", "aov", "profit"]:
        c_val = cur.get(k)
        p_val = prev.get(k)
        if c_val is not None and p_val is not None and p_val != 0:
            pct[k] = (c_val - p_val) / abs(p_val) * 100
        else:
            pct[k] = None

    return {"current": cur, "previous": prev, "pct_change": pct}


def revenue_by_period(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Aggregate revenue by time period. freq: D/W/M"""
    g = df.set_index("order_date").resample(freq)["revenue"].sum().reset_index()
    g.columns = ["date", "revenue"]
    return g


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    g = df.groupby("product")["revenue"].sum().nlargest(n).reset_index()
    g.columns = ["product", "revenue"]
    return g


def revenue_by_category(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("category")["revenue"].sum().reset_index()
    g.columns = ["category", "revenue"]
    return g.sort_values("revenue", ascending=False)


def revenue_by_region(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("region")["revenue"].sum().reset_index()
    g.columns = ["region", "revenue"]
    return g.sort_values("revenue", ascending=False)


def format_currency(val: Optional[float], symbol: str = "$") -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1_000_000:
        return f"{symbol}{val/1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"{symbol}{val/1_000:.1f}K"
    return f"{symbol}{val:,.2f}"


def format_pct(val: Optional[float]) -> str:
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


def anomaly_zscore(series: pd.Series, window: int = 30, threshold: float = 2.5) -> pd.Series:
    """Rolling z-score anomaly detection. Returns boolean mask of anomalies."""
    rolling_mean = series.rolling(window=window, min_periods=5).mean()
    rolling_std = series.rolling(window=window, min_periods=5).std()
    z = (series - rolling_mean) / (rolling_std + 1e-9)
    return z.abs() > threshold


def executive_summary(df: pd.DataFrame, comp: dict) -> str:
    """Generate a plain-English executive summary from real data."""
    cur = comp["current"]
    pct = comp.get("pct_change")
    rev_str = format_currency(cur["revenue"])
    orders_str = f"{cur['orders']:,}"

    rev_change = ""
    if pct and pct.get("revenue") is not None:
        rev_change = f", a {format_pct(pct['revenue'])} change vs the prior period"

    top = df.groupby("category")["revenue"].sum().idxmax() if len(df) else "N/A"
    top_prod = df.groupby("product")["revenue"].sum().idxmax() if len(df) else "N/A"

    profit_line = ""
    if cur["profit"] is not None:
        profit_line = (
            f" Gross profit was {format_currency(cur['profit'])} "
            f"({cur['margin']:.1f}% margin)."
        )

    return (
        f"Total revenue for the selected period was **{rev_str}**{rev_change}. "
        f"The business processed **{orders_str}** orders with an average order value of "
        f"**{format_currency(cur['aov'])}**."
        f"{profit_line} "
        f"The top-performing category was **{top}**, led by the product **{top_prod}**."
    )
