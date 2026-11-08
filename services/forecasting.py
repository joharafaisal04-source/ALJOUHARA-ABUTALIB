"""Forecasting service — baseline + sklearn model, no data leakage."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from typing import Tuple


MIN_ROWS = 90  # minimum days needed for forecasting


def prepare_daily_series(df: pd.DataFrame) -> pd.Series:
    """Aggregate to daily revenue series."""
    daily = df.set_index("order_date").resample("D")["revenue"].sum()
    daily = daily.asfreq("D", fill_value=0)
    return daily


def _build_features(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Create calendar + lag features from a DatetimeIndex."""
    df = pd.DataFrame(index=dates)
    df["dayofweek"] = dates.dayofweek
    df["month"] = dates.month
    df["quarter"] = dates.quarter
    df["dayofyear"] = dates.dayofyear
    df["week"] = dates.isocalendar().week.values.astype(int)
    # Cyclic encoding
    df["dow_sin"] = np.sin(2 * np.pi * df["dayofweek"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["dayofweek"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df.drop(columns=["dayofweek", "month", "quarter", "dayofyear", "week"])


def _add_lags(series: pd.Series, feature_df: pd.DataFrame, lags: list[int]) -> pd.DataFrame:
    for lag in lags:
        feature_df[f"lag_{lag}"] = series.shift(lag).values
    return feature_df


def seasonal_naive(train: pd.Series, horizon: int, period: int = 7) -> pd.Series:
    """Baseline: repeat the last full seasonal cycle."""
    if len(train) < period:
        base = train.values[-1] if len(train) > 0 else 0.0
        preds = np.full(horizon, base)
    else:
        last_cycle = train.values[-period:]
        reps = int(np.ceil(horizon / period))
        preds = np.tile(last_cycle, reps)[:horizon]

    future_idx = pd.date_range(train.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    return pd.Series(np.maximum(preds, 0), index=future_idx)


def train_ml_model(daily: pd.Series, test_size: int = 30) -> Tuple[dict, pd.Series, pd.Series]:
    """
    Train Ridge regression with calendar + lag features.
    Strict chronological split — no data leakage.
    Returns (metrics_dict, test_preds, forecast_future).
    """
    lags = [1, 2, 3, 7, 14, 28]
    max_lag = max(lags)

    features = _build_features(daily.index)
    features = _add_lags(daily, features, lags)
    features["target"] = daily.values

    valid = features.dropna()
    if len(valid) < test_size + 30:
        raise ValueError(f"Need at least {test_size + 30} non-NaN rows; got {len(valid)}.")

    train_df = valid.iloc[:-test_size]
    test_df = valid.iloc[-test_size:]

    X_train = train_df.drop(columns=["target"]).values
    y_train = train_df["target"].values
    X_test = test_df.drop(columns=["target"]).values
    y_test = test_df["target"].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    model = Ridge(alpha=10.0)
    model.fit(X_train_s, y_train)

    test_preds = np.maximum(model.predict(X_test_s), 0)
    test_series = pd.Series(test_preds, index=test_df.index)

    # Metrics
    mae_ml = float(np.mean(np.abs(y_test - test_preds)))
    rmse_ml = float(np.sqrt(np.mean((y_test - test_preds) ** 2)))
    mape_ml = float(np.mean(np.abs((y_test - test_preds) / (y_test + 1e-8))) * 100)

    # Baseline metrics on same test period
    baseline_preds = seasonal_naive(daily.iloc[:-test_size], test_size)
    mae_b = float(np.mean(np.abs(y_test - baseline_preds.values)))
    rmse_b = float(np.sqrt(np.mean((y_test - baseline_preds.values) ** 2)))
    mape_b = float(np.mean(np.abs((y_test - baseline_preds.values) / (y_test + 1e-8))) * 100)

    metrics = {
        "ml": {"MAE": mae_ml, "RMSE": rmse_ml, "MAPE": mape_ml},
        "baseline": {"MAE": mae_b, "RMSE": rmse_b, "MAPE": mape_b},
        "test_actual": pd.Series(y_test, index=test_df.index),
    }

    # WAPE — weighted absolute percentage error (zero-safe alternative to MAPE)
    sum_actual = float(np.sum(np.abs(y_test)))
    wape_ml = float(np.sum(np.abs(y_test - test_preds)) / (sum_actual + 1e-8) * 100)
    wape_b  = float(np.sum(np.abs(y_test - baseline_preds.values)) / (sum_actual + 1e-8) * 100)

    metrics["ml"]["WAPE"]       = wape_ml
    metrics["baseline"]["WAPE"] = wape_b
    metrics["ml"]["Accuracy"]   = max(0.0, 100.0 - wape_ml)

    # Test date range
    metrics["test_start"] = test_df.index[0]
    metrics["test_end"]   = test_df.index[-1]

    # Residual-based prediction intervals (±1.645 std of residuals = ~90% PI)
    residuals = y_test - test_preds
    residual_std = float(np.std(residuals))

    return metrics, test_series, residual_std


def forecast_future(daily: pd.Series, horizon: int, residual_std: float) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Generate future point forecasts + 90% prediction intervals using
    residual standard deviation from the test period.
    """
    lags = [1, 2, 3, 7, 14, 28]
    max_lag = max(lags)
    extended = daily.copy()

    future_dates = pd.date_range(daily.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    preds = []

    for d in future_dates:
        feat = _build_features(pd.DatetimeIndex([d]))
        lag_vals = [extended.iloc[-l] if len(extended) >= l else extended.mean() for l in lags]
        for i, lag in enumerate(lags):
            feat[f"lag_{lag}"] = lag_vals[i]
        # Simple approximation: use the calendar feature model (re-train inline on all data)
        preds.append(max(0.0, _simple_predict(extended, feat)))
        extended = pd.concat([extended, pd.Series([preds[-1]], index=[d])])

    preds_arr = np.array(preds)
    point = pd.Series(preds_arr, index=future_dates)
    lower = pd.Series(np.maximum(preds_arr - 1.645 * residual_std, 0), index=future_dates)
    upper = pd.Series(preds_arr + 1.645 * residual_std, index=future_dates)
    return point, lower, upper


def _simple_predict(history: pd.Series, feat_df: pd.DataFrame) -> float:
    """Lightweight Ridge on the last window of data for one-step-ahead."""
    window = min(len(history), 180)
    h = history.iloc[-window:]
    lags = [1, 2, 3, 7, 14, 28]
    X_list, y_list = [], []
    for i in range(max(lags), len(h)):
        row = [h.iloc[i - l] for l in lags]
        X_list.append(row)
        y_list.append(h.iloc[i])
    if len(X_list) < 10:
        return float(history.mean())
    X = np.array(X_list)
    y = np.array(y_list)
    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)
    model = Ridge(alpha=10.0)
    model.fit(X_s, y)
    feat_lags = np.array([[feat_df[f"lag_{l}"].values[0] for l in lags]])
    feat_s = scaler.transform(feat_lags)
    return float(model.predict(feat_s)[0])
