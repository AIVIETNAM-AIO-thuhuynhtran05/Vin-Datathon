"""Bước 1/6 — Aggregation, quality check & rule-based segmentation.

Khách có đơn phát sinh doanh thu (REVENUE_STATUSES) → tính RFM để phân cụm K-Means. Khách chưa có → gán nhóm
rule-based (RULE_SEGMENTS trong config.py) để vẫn có mặt trong bức tranh tổng thể.

Đầu vào : data/raw/{customers,orders,payments,returns,geography}.csv
Đầu ra  : data/processed/customer_segmentation/customer_analysis_base.csv
          data/processed/customer_segmentation/refund_reconciliation_issues.csv
"""

from __future__ import annotations

import pandas as pd

from config import (
    CUSTOMER_BASE_PATH,
    DEMOGRAPHIC_COLUMNS,
    PENDING_STATUSES,
    OUTPUT_DIR,
    RAW_DIR,
    REFUND_ISSUES_PATH,
    REVENUE_STATUSES,
    RULE_SEGMENTS,
)


def read_csv(name: str) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Required source data file not found: {path}")
    return pd.read_csv(path)


def require_unique(frame: pd.DataFrame, columns: list[str], table: str) -> None:
    if frame[columns].isna().any().any():
        raise ValueError(f"{table} contains missing values in key columns {columns}")
    if frame.duplicated(columns).any():
        raise ValueError(f"{table} contains duplicate key values for {columns}")


def assign_rule_segment(customer_ids: pd.Series, orders: pd.DataFrame, has_purchase: pd.Series) -> pd.Series:
    """Nhãn rule-based cho khách chưa có đơn phát sinh doanh thu; khách đã mua để trống (sẽ phân cụm K-Means)."""
    statuses = orders.groupby("customer_id")["order_status"].agg(lambda values: set(values.str.lower()))
    customer_statuses = customer_ids.map(statuses)

    def rule(status_set: object) -> str:
        if not isinstance(status_set, set):
            return "RB1"
        if status_set & PENDING_STATUSES:
            return "RB3"
        return "RB2"

    labels = customer_statuses.map(rule)
    return labels.where(~has_purchase, "")


def main() -> None:
    customers = read_csv("customers.csv")
    orders = read_csv("orders.csv")
    payments = read_csv("payments.csv")
    returns = read_csv("returns.csv")
    geography = read_csv("geography.csv")

    require_unique(customers, ["customer_id"], "customers.csv")
    require_unique(orders, ["order_id"], "orders.csv")
    require_unique(payments, ["order_id"], "payments.csv")
    require_unique(geography, ["zip"], "geography.csv")

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    if orders["order_date"].isna().any():
        raise ValueError("orders.csv contains invalid or missing order_date values")
    if orders["customer_id"].isna().any() or not orders["customer_id"].isin(
        customers["customer_id"]
    ).all():
        raise ValueError("orders.csv contains missing or unmatched customer_id values")

    payments["payment_value"] = pd.to_numeric(payments["payment_value"], errors="coerce")
    if payments["payment_value"].isna().any():
        raise ValueError("payments.csv contains invalid or missing payment_value values")
    if set(orders["order_id"]) != set(payments["order_id"]):
        raise ValueError("payments.csv and orders.csv do not have matching order_id keys")

    returns["refund_amount"] = pd.to_numeric(returns["refund_amount"], errors="coerce")
    if returns["refund_amount"].isna().any():
        raise ValueError("returns.csv contains invalid or missing refund_amount values")
    if not returns["order_id"].isin(orders["order_id"]).all():
        raise ValueError("returns.csv contains order_id values absent from orders.csv")

    order_refunds = returns.groupby("order_id", as_index=False)["refund_amount"].sum()
    purchases = (
        orders.loc[orders["order_status"].str.lower().isin(REVENUE_STATUSES)]
        .merge(
            payments[["order_id", "payment_value"]],
            on="order_id",
            how="left",
            validate="one_to_one",
        )
        .merge(order_refunds, on="order_id", how="left", validate="one_to_one")
    )
    purchases["refund_amount"] = purchases["refund_amount"].fillna(0.0)
    purchases["net_order_value_before_floor"] = (
        purchases["payment_value"] - purchases["refund_amount"]
    )
    refund_anomalies = purchases.loc[
        purchases["net_order_value_before_floor"] < 0,
        ["order_id", "payment_value", "refund_amount", "net_order_value_before_floor"],
    ]
    purchases["net_order_value"] = purchases["net_order_value_before_floor"].clip(lower=0)

    if purchases.empty:
        raise ValueError("No revenue orders found for customer analysis")
    reference_date = purchases["order_date"].max() + pd.Timedelta(days=1)
    rfm = (
        purchases.groupby("customer_id")
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("net_order_value", "sum"),
        )
        .reset_index()
    )
    rfm["recency_days"] = (reference_date - rfm["last_order_date"]).dt.days
    rfm = rfm.drop(columns="last_order_date")

    selected_customers = customers[
        ["customer_id", "signup_date", "zip", "gender", "age_group", "acquisition_channel"]
    ].copy()
    selected_customers["signup_date"] = pd.to_datetime(
        selected_customers["signup_date"], errors="coerce"
    )
    customer_region = geography[["zip", "region"]]
    customer_level = (
        selected_customers.merge(
            customer_region, on="zip", how="left", validate="many_to_one"
        )
        .drop(columns="zip")
        .merge(rfm, on="customer_id", how="left", validate="one_to_one")
    )
    customer_level["frequency"] = customer_level["frequency"].fillna(0).astype("int64")
    customer_level["monetary"] = customer_level["monetary"].fillna(0.0)
    customer_level["has_purchase"] = customer_level["frequency"].gt(0)
    customer_level["order_count_all"] = (
        customer_level["customer_id"].map(orders["customer_id"].value_counts()).fillna(0).astype("int64")
    )
    customer_level["rule_segment"] = assign_rule_segment(
        customer_level["customer_id"], orders, customer_level["has_purchase"]
    )
    customer_level["segment_method"] = customer_level["has_purchase"].map({True: "kmeans", False: "rule_based"})
    for column in DEMOGRAPHIC_COLUMNS:
        customer_level[column] = customer_level[column].fillna("Unknown").astype(str)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    refund_anomalies.to_csv(REFUND_ISSUES_PATH, index=False)
    customer_level.to_csv(CUSTOMER_BASE_PATH, index=False, date_format="%Y-%m-%d")
    print(f"Revenue statuses included: {sorted(REVENUE_STATUSES)}")
    print(f"Reference date for recency: {reference_date.date()}")
    print(
        f"Orders where refunds exceed payment: {len(refund_anomalies):,}; "
        "these are listed in refund_reconciliation_issues.csv and net order value is floored at zero."
    )
    print(f"Customers: {len(customer_level):,}")
    print(f"Customers with revenue orders (→ K-Means): {int(customer_level['has_purchase'].sum()):,}")
    for code, count in customer_level.loc[~customer_level["has_purchase"], "rule_segment"].value_counts().sort_index().items():
        print(f"  Rule-based {code} – {RULE_SEGMENTS[code]}: {count:,}")
    print(f"Saved customer-level analysis data to {CUSTOMER_BASE_PATH}")


if __name__ == "__main__":
    main()
