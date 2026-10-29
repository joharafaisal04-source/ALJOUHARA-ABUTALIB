"""Generate realistic 2+ year sample sales dataset."""
import numpy as np
import pandas as pd
from pathlib import Path

def generate_sample_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2023-01-01")
    end = pd.Timestamp("2025-01-15")
    dates = pd.date_range(start, end, freq="D")

    products = {
        "Laptop Pro": ("Electronics", 1299.0, 780.0),
        "Laptop Air": ("Electronics", 899.0, 540.0),
        "Wireless Mouse": ("Electronics", 49.99, 18.0),
        "Mechanical Keyboard": ("Electronics", 129.99, 55.0),
        "Monitor 27\"": ("Electronics", 379.0, 210.0),
        "USB-C Hub": ("Electronics", 59.99, 22.0),
        "Running Shoes": ("Apparel", 119.0, 48.0),
        "Sport Jacket": ("Apparel", 89.99, 32.0),
        "Denim Jeans": ("Apparel", 69.99, 25.0),
        "Backpack": ("Accessories", 79.99, 28.0),
        "Sunglasses": ("Accessories", 49.99, 14.0),
        "Watch Classic": ("Accessories", 199.0, 80.0),
        "Coffee Maker": ("Home & Kitchen", 89.99, 38.0),
        "Air Purifier": ("Home & Kitchen", 149.0, 65.0),
        "Blender Pro": ("Home & Kitchen", 69.99, 28.0),
        "Desk Lamp": ("Home & Kitchen", 39.99, 14.0),
        "Protein Powder": ("Health", 54.99, 22.0),
        "Yoga Mat": ("Health", 34.99, 12.0),
        "Smart Scale": ("Health", 49.99, 18.0),
        "Python Bootcamp": ("Education", 149.0, 20.0),
        "Data Science Course": ("Education", 199.0, 25.0),
        "Excel Mastery": ("Education", 79.99, 10.0),
    }

    regions = ["North America", "Europe", "Asia Pacific", "Middle East", "Latin America"]
    channels = ["Online", "Retail", "Wholesale", "Direct Sales"]
    product_names = list(products.keys())

    n_orders = 18000
    order_dates = rng.choice(dates, size=n_orders)

    # Seasonal & weekly trend multipliers
    months = pd.DatetimeIndex(order_dates).month
    # Q4 boost, summer dip
    season_mult = np.where(months.isin([11, 12]), 1.4,
                  np.where(months.isin([1, 2]), 0.85,
                  np.where(months.isin([6, 7, 8]), 0.9, 1.0)))

    # Year-over-year growth ~15%
    years = pd.DatetimeIndex(order_dates).year
    growth = np.where(years == 2023, 1.0, np.where(years == 2024, 1.15, 1.30))

    probs = season_mult * growth
    probs = probs / probs.sum()

    chosen_product_idx = rng.choice(len(product_names), size=n_orders, p=None)
    chosen_products = [product_names[i] for i in chosen_product_idx]
    chosen_regions = rng.choice(regions, size=n_orders, p=[0.35, 0.25, 0.20, 0.12, 0.08])
    chosen_channels = rng.choice(channels, size=n_orders, p=[0.45, 0.30, 0.15, 0.10])

    quantities = rng.integers(1, 6, size=n_orders)
    # Add bulk orders occasionally
    bulk_mask = rng.random(n_orders) < 0.05
    quantities[bulk_mask] = rng.integers(10, 30, size=bulk_mask.sum())

    unit_prices = np.array([products[p][1] for p in chosen_products])
    unit_costs = np.array([products[p][2] for p in chosen_products])
    categories = [products[p][0] for p in chosen_products]

    # Small price variation ±5%
    price_var = 1 + rng.uniform(-0.05, 0.05, size=n_orders)
    unit_prices = unit_prices * price_var

    revenues = unit_prices * quantities
    customer_ids = rng.integers(1001, 5001, size=n_orders)

    df = pd.DataFrame({
        "order_id": [f"ORD-{i+10001}" for i in range(n_orders)],
        "order_date": order_dates,
        "customer_id": [f"CUST-{c}" for c in customer_ids],
        "product": chosen_products,
        "category": categories,
        "region": chosen_regions,
        "channel": chosen_channels,
        "quantity": quantities,
        "unit_price": np.round(unit_prices, 2),
        "unit_cost": np.round(unit_costs, 2),
        "revenue": np.round(revenues, 2),
    })

    df = df.sort_values("order_date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "data" / "sample_sales.csv"
    out.parent.mkdir(exist_ok=True)
    df = generate_sample_data()
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} rows → {out}")
    print(df.describe())
