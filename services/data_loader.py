"""Data loading, validation, and caching."""
from __future__ import annotations

import io
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple

from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS, SAMPLE_DATA_PATH


def load_sample_data() -> pd.DataFrame:
    """Load the bundled sample dataset."""
    df = pd.read_csv(SAMPLE_DATA_PATH, parse_dates=["order_date"])
    return df


_COLUMN_ALIASES = {
    "order_id":    ["order_id", "orderid", "id", "order_no", "order_number", "Order_ID"],
    "order_date":  ["order_date", "orderdate", "date", "Order_Date", "sale_date", "transaction_date"],
    "customer_id": ["customer_id", "customerid", "customer", "Customer_ID", "client_id"],
    "product":     ["product", "product_name", "item", "Product", "sku"],
    "category":    ["category", "cat", "Category", "product_category", "dept"],
    "region":      ["region", "Region", "area", "territory", "location", "city"],
    "quantity":    ["quantity", "qty", "Quantity", "units", "count"],
    "unit_price":  ["unit_price", "Unit_Price_SAR", "price", "unit_price_sar", "selling_price"],
    "revenue":     ["revenue", "Net_Sales_SAR", "net_sales_sar", "net_sales", "sales",
                    "total", "amount", "total_sales", "gross_sales_sar", "gross_sales"],
    "unit_cost":   ["unit_cost", "cost", "cogs", "unit_cost_sar"],
    "channel":     ["channel", "Sales_Channel", "sales_channel", "sales_rep_channel"],
}


def auto_map_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, list[str]]:
    """Rename columns to VELORA standard names using known aliases."""
    notes = []
    col_lower = {c.lower(): c for c in df.columns}
    rename_map = {}
    for standard, aliases in _COLUMN_ALIASES.items():
        if standard in df.columns:
            continue
        for alias in aliases:
            if alias in df.columns:
                rename_map[alias] = standard
                notes.append(f"Mapped '{alias}' → '{standard}'")
                break
            if alias.lower() in col_lower:
                orig = col_lower[alias.lower()]
                rename_map[orig] = standard
                notes.append(f"Mapped '{orig}' → '{standard}'")
                break
    if rename_map:
        df = df.rename(columns=rename_map)
    return df, notes


def _smart_fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    If required columns are still missing after alias mapping,
    guess them from data types so almost any sales file is accepted.
    """
    # order_date — pick first parseable date column
    if "order_date" not in df.columns:
        for col in df.columns:
            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > len(df) * 0.5:
                    df = df.rename(columns={col: "order_date"})
                    break
            except Exception:
                continue

    # revenue — pick largest numeric column not already mapped
    if "revenue" not in df.columns:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        taken = {"quantity", "unit_price", "unit_cost"}
        candidates = [c for c in num_cols if c not in taken]
        if candidates:
            best = max(candidates, key=lambda c: df[c].sum())
            df = df.rename(columns={best: "revenue"})

    # quantity — default to 1 if missing
    if "quantity" not in df.columns:
        df["quantity"] = 1

    # unit_price — use revenue if missing
    if "unit_price" not in df.columns and "revenue" in df.columns:
        df["unit_price"] = df["revenue"]

    # synthetic IDs if missing
    if "order_id" not in df.columns:
        df.insert(0, "order_id", [f"ORD-{i+1:05d}" for i in range(len(df))])
    if "customer_id" not in df.columns:
        df["customer_id"] = "CUST-001"
    if "product" not in df.columns:
        # use any text column as product name
        text_cols = df.select_dtypes(include="object").columns.tolist()
        known = {"order_id","customer_id","category","region","channel","order_date"}
        candidates = [c for c in text_cols if c not in known]
        df["product"] = df[candidates[0]] if candidates else "Product"
    if "category" not in df.columns:
        df["category"] = "General"
    if "region" not in df.columns:
        df["region"] = "Unknown"

    return df


def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, list[str]]:
    """
    Check that df has the required columns, correct types, and no fatal issues.
    Returns (is_valid, list_of_error_messages).
    """
    errors: list[str] = []

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return False, errors

    # Parse order_date
    try:
        df["order_date"] = pd.to_datetime(df["order_date"])
    except Exception:
        errors.append("Column 'order_date' could not be parsed as dates.")

    # Numeric checks
    for col in ["quantity", "unit_price", "revenue"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            n_bad = df[col].isna().sum()
            if n_bad > 0:
                errors.append(f"Column '{col}' has {n_bad} non-numeric values (set to NaN).")
            neg = (df[col] < 0).sum()
            if neg > 0:
                errors.append(f"Column '{col}' has {neg} negative values.")

    # Duplicates
    dupes = df["order_id"].duplicated().sum() if "order_id" in df.columns else 0
    if dupes:
        errors.append(f"{dupes} duplicate order_id values found.")

    return len(errors) == 0, errors


def parse_uploaded_csv(contents: str, filename: str) -> Tuple[Optional[pd.DataFrame], list[str]]:
    """Parse a base64-encoded CSV or Excel upload from Dash dcc.Upload."""
    import base64
    errors: list[str] = []
    ext = Path(filename).suffix.lower()

    try:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)

        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(decoded), engine="openpyxl")
        elif ext == ".csv":
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except UnicodeDecodeError:
                df = pd.read_csv(io.StringIO(decoded.decode("latin-1")))
        else:
            return None, [f"Unsupported file type '{ext}'. Please upload a .csv or .xlsx file."]
    except Exception as e:
        return None, [f"Could not read file '{filename}': {e}"]

    # Auto-map non-standard column names to VELORA standard names
    df, mapping_notes = auto_map_columns(df)
    # mapping_notes kept internal — not shown to user

    # If still missing required cols, try to guess from data types
    df = _smart_fill_missing(df)

    is_valid, errs = validate_dataframe(df)
    errors.extend(errs)
    # Don't block on missing optional cols — just warn
    fatal = [e for e in errs if "Missing required" in e]
    if fatal:
        return None, fatal
    return df, errors


def filter_by_date(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Filter dataframe to [start, end] inclusive."""
    return df[(df["order_date"] >= start) & (df["order_date"] <= end)]


def has_column(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].notna().any()
