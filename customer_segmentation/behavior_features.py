"""Biến hành vi theo khách hàng — dùng chung cho bước feature engineering (02) và profiling (06).

RFM lấy từ customer_analysis_base.csv (bước 01); các biến còn lại tính từ đơn phát sinh doanh thu
(REVENUE_STATUSES), trừ tỷ lệ hủy tính trên mọi đơn.
"""

from __future__ import annotations

import pandas as pd

from config import CUSTOMER_BASE_PATH, DEMOGRAPHIC_COLUMNS, RAW_DIR, REVENUE_STATUSES

BEHAVIOR_CATEGORICALS = ["preferred_category", "preferred_device", "preferred_payment", "preferred_source"]
METRICS = {
    "recency_days": "Recency (ngày, cao = lâu chưa mua)",
    "frequency": "Frequency (số đơn)",
    "monetary": "Monetary (doanh thu ròng)",
    "aov": "Giá trị đơn TB (AOV)",
    "items_per_order": "Số SP / đơn",
    "tenure_days": "Tenure (ngày từ đơn đầu)",
    "promo_share": "Tỷ lệ dòng có khuyến mãi",
    "return_rate": "Tỷ lệ đơn bị trả",
    "cancel_rate": "Tỷ lệ đơn hủy",
    "avg_rating": "Điểm đánh giá TB",
}
LABELS = {
    "gender": "Giới tính", "age_group": "Nhóm tuổi", "region": "Vùng", "acquisition_channel": "Kênh thu hút",
    "preferred_category": "Danh mục ưa thích", "preferred_device": "Thiết bị", "preferred_payment": "Thanh toán",
    "preferred_source": "Nguồn đơn",
}


def build_behavior_features(customer_ids: pd.Series) -> pd.DataFrame:
    """RFM, biến hành vi và nhân khẩu học cho danh sách khách hàng (một dòng / khách)."""
    base = pd.read_csv(CUSTOMER_BASE_PATH)
    orders = pd.read_csv(RAW_DIR / "orders.csv", parse_dates=["order_date"])
    items = pd.read_csv(RAW_DIR / "order_items.csv", usecols=["order_id", "product_id", "quantity", "unit_price", "promo_id"])
    products = pd.read_csv(RAW_DIR / "products.csv", usecols=["product_id", "category"])
    reviews = pd.read_csv(RAW_DIR / "reviews.csv", usecols=["customer_id", "rating"])

    completed = orders[orders["order_status"].isin(REVENUE_STATUSES)]
    reference_date = completed["order_date"].max() + pd.Timedelta(days=1)
    per_order = orders.groupby("customer_id").agg(
        total_orders=("order_id", "size"), cancelled_orders=("order_status", lambda s: s.eq("cancelled").sum())
    )
    per_completed = completed.groupby("customer_id").agg(
        first_order=("order_date", "min"),
        returned_orders=("order_status", lambda s: s.eq("returned").sum()),
        completed_orders=("order_id", "size"),
        preferred_device=("device_type", lambda s: s.mode().iloc[0]),
        preferred_payment=("payment_method", lambda s: s.mode().iloc[0]),
        preferred_source=("order_source", lambda s: s.mode().iloc[0]),
    )
    lines = items.merge(completed[["order_id", "customer_id"]], on="order_id").merge(products, on="product_id", how="left")
    lines["gross"] = lines["quantity"] * lines["unit_price"]
    per_lines = lines.groupby("customer_id").agg(
        units=("quantity", "sum"), promo_share=("promo_id", lambda s: s.notna().mean())
    )
    category_value = lines.groupby(["customer_id", "category"])["gross"].sum().reset_index()
    preferred_category = category_value.loc[category_value.groupby("customer_id")["gross"].idxmax()].set_index(
        "customer_id")["category"].rename("preferred_category")

    features = (
        pd.DataFrame({"customer_id": customer_ids.to_numpy()})
        .merge(base, on="customer_id", how="left", validate="one_to_one")
        .join(per_order, on="customer_id").join(per_completed, on="customer_id")
        .join(per_lines, on="customer_id").join(preferred_category, on="customer_id")
        .join(reviews.groupby("customer_id")["rating"].mean().rename("avg_rating"), on="customer_id")
    )
    features["aov"] = features["monetary"] / features["frequency"]
    features["items_per_order"] = features["units"] / features["completed_orders"]
    features["tenure_days"] = (reference_date - features["first_order"]).dt.days
    features["return_rate"] = features["returned_orders"] / features["completed_orders"]
    features["cancel_rate"] = features["cancelled_orders"] / features["total_orders"]
    for column in [*DEMOGRAPHIC_COLUMNS, *BEHAVIOR_CATEGORICALS]:
        features[column] = features[column].fillna("Unknown").astype(str)
    return features[["customer_id", *METRICS, *DEMOGRAPHIC_COLUMNS, *BEHAVIOR_CATEGORICALS]]
