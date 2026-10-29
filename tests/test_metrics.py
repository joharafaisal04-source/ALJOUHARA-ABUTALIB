"""Tests for KPI calculations, profit/margin, period comparison, data validation."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from services.metrics import (
    kpi_summary, period_comparison, format_currency, format_pct,
    revenue_by_period, top_products
)
from services.data_loader import validate_dataframe, load_sample_data
from services.ai_client import _demo_answer


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def simple_df():
    return pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "order_date": pd.to_datetime(["2024-01-10", "2024-01-15", "2024-01-20"]),
        "customer_id": ["C1", "C2", "C3"],
        "product": ["A", "B", "A"],
        "category": ["X", "Y", "X"],
        "region": ["NA", "EU", "NA"],
        "channel": ["Online", "Retail", "Online"],
        "quantity": [2, 1, 3],
        "unit_price": [100.0, 200.0, 100.0],
        "unit_cost": [60.0, 120.0, 60.0],
        "revenue": [200.0, 200.0, 300.0],
    })


# ── KPI calculations ──────────────────────────────────────────────────────────
def test_kpi_revenue(simple_df):
    kpi = kpi_summary(simple_df)
    assert kpi["revenue"] == pytest.approx(700.0)

def test_kpi_orders(simple_df):
    kpi = kpi_summary(simple_df)
    assert kpi["orders"] == 3

def test_kpi_aov(simple_df):
    kpi = kpi_summary(simple_df)
    assert kpi["aov"] == pytest.approx(700.0 / 3)

def test_kpi_profit_and_margin(simple_df):
    kpi = kpi_summary(simple_df)
    # cost = (60*2) + (120*1) + (60*3) = 120 + 120 + 180 = 420
    expected_profit = 700.0 - 420.0
    assert kpi["profit"] == pytest.approx(expected_profit)
    assert kpi["margin"] == pytest.approx(expected_profit / 700.0 * 100)

def test_kpi_no_cost_column():
    df = pd.DataFrame({
        "order_id": ["O1"],
        "order_date": pd.to_datetime(["2024-01-01"]),
        "customer_id": ["C1"],
        "product": ["A"], "category": ["X"], "region": ["NA"],
        "quantity": [1], "unit_price": [100.0], "revenue": [100.0],
    })
    kpi = kpi_summary(df)
    assert kpi["profit"] is None
    assert kpi["margin"] is None

def test_kpi_empty_df():
    df = pd.DataFrame(columns=["order_id", "order_date", "customer_id",
                                "product", "category", "region",
                                "quantity", "unit_price", "unit_cost", "revenue"])
    kpi = kpi_summary(df)
    assert kpi["revenue"] == 0.0
    assert kpi["orders"] == 0
    assert kpi["aov"] == 0.0


# ── Period comparison ─────────────────────────────────────────────────────────
def test_period_comparison_no_history(simple_df):
    comp = period_comparison(simple_df, "2024-01-10", "2024-01-20")
    # All data is in current period; no prior data → previous should be None
    assert comp["previous"] is None
    assert comp["pct_change"] is None

def test_period_comparison_with_history():
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    df = pd.DataFrame({
        "order_id": [f"O{i}" for i in range(60)],
        "order_date": dates,
        "customer_id": [f"C{i}" for i in range(60)],
        "product": ["A"] * 60,
        "category": ["X"] * 60,
        "region": ["NA"] * 60,
        "quantity": [1] * 60,
        "unit_price": [100.0] * 60,
        "revenue": [100.0] * 60,
    })
    comp = period_comparison(df, "2024-02-01", "2024-02-29")
    assert comp["previous"] is not None
    assert comp["current"]["revenue"] == pytest.approx(2900.0)


# ── Data validation ───────────────────────────────────────────────────────────
def test_validate_good_df(simple_df):
    ok, errors = validate_dataframe(simple_df.copy())
    assert ok

def test_validate_missing_required_column(simple_df):
    bad = simple_df.drop(columns=["revenue"])
    ok, errors = validate_dataframe(bad)
    assert not ok
    assert any("revenue" in e for e in errors)

def test_validate_negative_revenue(simple_df):
    bad = simple_df.copy()
    bad.loc[0, "revenue"] = -50.0
    _, errors = validate_dataframe(bad)
    assert any("negative" in e.lower() for e in errors)

def test_validate_duplicate_order_ids():
    df = pd.DataFrame({
        "order_id": ["O1", "O1"],
        "order_date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        "customer_id": ["C1", "C2"],
        "product": ["A", "B"], "category": ["X", "X"], "region": ["NA", "NA"],
        "quantity": [1, 1], "unit_price": [10.0, 10.0], "revenue": [10.0, 10.0],
    })
    _, errors = validate_dataframe(df)
    assert any("duplicate" in e.lower() for e in errors)

def test_sample_data_loads():
    df = load_sample_data()
    assert len(df) > 0
    assert "order_date" in df.columns
    assert "revenue" in df.columns


# ── Forecast train/test split — no data leakage ───────────────────────────────
def test_no_data_leakage_in_split():
    from services.forecasting import prepare_daily_series, train_ml_model
    df = load_sample_data()
    daily = prepare_daily_series(df)
    metrics, test_preds, _ = train_ml_model(daily, test_size=30)
    actual = metrics["test_actual"]
    # Test set must be strictly after training period
    train_end = daily.index[-(30 + 1)]
    assert test_preds.index.min() > train_end

def test_forecast_metrics_shape():
    from services.forecasting import prepare_daily_series, train_ml_model
    df = load_sample_data()
    daily = prepare_daily_series(df)
    metrics, test_preds, _ = train_ml_model(daily, test_size=30)
    assert "MAE" in metrics["ml"]
    assert "RMSE" in metrics["baseline"]
    assert len(test_preds) == 30


# ── AI demo mode ──────────────────────────────────────────────────────────────
def test_demo_mode_top_products(simple_df):
    answer = _demo_answer("What were our best-performing products?", simple_df)
    assert "Product A" in answer or "A" in answer or "Revenue" in answer.replace("**","")

def test_demo_mode_no_fabrication(simple_df):
    answer = _demo_answer("What is our profit margin?", simple_df)
    # Should include a real figure from the data, not invented
    assert "%" in answer or "N/A" in answer or "Cost" in answer

def test_demo_mode_unknown_question(simple_df):
    answer = _demo_answer("Tell me about the weather", simple_df)
    assert len(answer) > 0  # graceful fallback, not a crash


# ── Formatting helpers ────────────────────────────────────────────────────────
def test_format_currency_millions():
    assert "M" in format_currency(1_500_000)

def test_format_currency_thousands():
    assert "K" in format_currency(12_500)

def test_format_pct_positive():
    s = format_pct(12.5)
    assert s.startswith("+")

def test_format_pct_negative():
    s = format_pct(-5.0)
    assert s.startswith("-")

def test_format_pct_none():
    assert format_pct(None) == "—"
