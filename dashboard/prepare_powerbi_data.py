"""Chuẩn bị dữ liệu cho dashboard Power BI.

Đọc 13 CSV gốc trong data/raw/, làm giàu và tổng hợp thành các bảng dim/fact/agg theo mô hình
star schema để load vào Power BI (quan hệ do Power BI quản lý, nên bảng fact chỉ giữ khóa
thay vì nhân bản thuộc tính sản phẩm/địa lý).

Khác với bản Tableau trong tài liệu tham khảo:
  - Thêm dim_date (bảng lịch) — đánh dấu "Mark as date table" trong Power BI; các bảng fact
    không cần cột năm/tháng/thứ riêng.
  - Thêm fact_orders (grain = đơn) chứa payment_value/installments. fact_orders_enriched giữ
    grain dòng sản phẩm và KHÔNG chứa payment_value để tránh cộng trùng khi đơn có nhiều dòng.
  - Doanh thu RFM/cohort chỉ tính đơn có trạng thái phát sinh doanh thu (paid, shipped,
    delivered, returned) — giống customer_segmentation/config.py — thay vì chỉ loại cancelled.
  - Segment "Cant Lose Them" được xét trước "At Risk" (bản gốc không bao giờ tới nhánh này).
  - YoY so với cùng ngày năm trước theo lịch (không dùng shift(365), lệch ở năm nhuận).

Đầu ra: data/processed/powerbi/*.csv

Quan hệ gợi ý trong Power BI (1 → *):
  dim_date[date]            → fact_orders[order_date], fact_orders_enriched[order_date],
                              fact_returns_enriched[return_date], fact_shipments_enriched[ship_date],
                              fact_sales_daily[date], fact_web_traffic[traffic_date],
                              fact_inventory[snapshot_date]
  dim_products[product_id]  → fact_orders_enriched, fact_returns_enriched, fact_inventory
  dim_customers[customer_id]→ fact_orders, fact_orders_enriched, fact_returns_enriched
  dim_geography[zip]        → fact_orders, fact_orders_enriched, dim_customers
  dim_promotions[promo_id]  → fact_orders_enriched[promo_id]
  fact_orders[order_id]     → fact_orders_enriched, fact_returns_enriched, fact_shipments_enriched
Các bảng agg_* đứng riêng (đã tổng hợp sẵn), không cần quan hệ.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "powerbi"
# Nhãn K-Means (tùy chọn) — có khi đã chạy customer_segmentation/06_cluster_profiling.py.
SEGMENTS_PATH = ROOT / "data" / "processed" / "customer_segmentation" / "customer_segments_all.csv"

# Đơn đã thanh toán trở đi được tính doanh thu (đồng bộ với customer_segmentation/config.py).
REVENUE_STATUSES = {"paid", "shipped", "delivered", "returned"}
COHORT_MAX_PERIOD = 24


def load(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    path = RAW_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found. Copy the competition CSVs into data/raw/.")
    df = pd.read_csv(path, dtype={"promo_id": "string", "promo_id_2": "string"})
    # Một số file lưu ngày dạng dd/mm/yyyy, số còn lại dạng ISO yyyy-mm-dd.
    for col in parse_dates or []:
        values = df[col].astype("string")
        fmt = "%d/%m/%Y" if values.str.contains("/", regex=False).any() else "%Y-%m-%d"
        df[col] = pd.to_datetime(values, format=fmt)
    print(f"  Loaded {name}: {df.shape[0]:,} rows x {df.shape[1]} cols")
    return df


def save(df: pd.DataFrame, name: str) -> None:
    path = OUTPUT_DIR / name
    # utf-8-sig (có BOM) để Excel hiển thị đúng tiếng Việt; Power BI đọc bình thường.
    df.to_csv(path, index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    size_mb = path.stat().st_size / 1024 / 1024
    print(f"  Saved {name}: {df.shape[0]:,} rows x {df.shape[1]} cols ({size_mb:.1f} MB)")


def safe_pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """numerator / denominator × 100, trả NaN khi mẫu số ≤ 0."""
    return np.where(denominator > 0, (numerator / denominator * 100).round(2), np.nan)


# ---------------------------------------------------------------------------
# Step 1 — load
# ---------------------------------------------------------------------------
def load_raw() -> dict[str, pd.DataFrame]:
    print("Step 1: load raw data")
    return {
        "orders": load("orders.csv", parse_dates=["order_date"]),
        "order_items": load("order_items.csv"),
        "payments": load("payments.csv"),
        "products": load("products.csv"),
        "customers": load("customers.csv", parse_dates=["signup_date"]),
        "geography": load("geography.csv"),
        "promotions": load("promotions.csv", parse_dates=["start_date", "end_date"]),
        "shipments": load("shipments.csv", parse_dates=["ship_date", "delivery_date"]),
        "returns": load("returns.csv", parse_dates=["return_date"]),
        "reviews": load("reviews.csv", parse_dates=["review_date"]),
        "inventory": load("inventory.csv", parse_dates=["snapshot_date"]),
        "web_traffic": load("web_traffic.csv", parse_dates=["date"]),
        "sales": load("sales.csv", parse_dates=["Date"]),
    }


# ---------------------------------------------------------------------------
# Dimensions
# ---------------------------------------------------------------------------
def build_dim_date(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    start = min(raw["orders"]["order_date"].min(), raw["sales"]["Date"].min(),
                raw["customers"]["signup_date"].min()).to_period("Y").start_time
    end = max(raw["orders"]["order_date"].max(), raw["returns"]["return_date"].max(),
              raw["shipments"]["delivery_date"].max(), raw["inventory"]["snapshot_date"].max(),
              raw["reviews"]["review_date"].max()).to_period("Y").end_time.normalize()
    dates = pd.date_range(start, end, freq="D")
    dim = pd.DataFrame({"date": dates})
    dim["year"] = dates.year
    dim["quarter"] = dates.quarter
    dim["quarter_label"] = "Q" + dim["quarter"].astype(str)
    dim["month"] = dates.month
    dim["month_name"] = dates.strftime("%b")
    dim["year_month"] = dates.strftime("%Y-%m")
    dim["month_start"] = dates.to_period("M").start_time
    dim["week_of_year"] = dates.isocalendar().week.astype(int).values
    dim["day_of_week"] = dates.dayofweek + 1  # 1 = Monday — dùng làm Sort by column
    dim["day_name"] = dates.strftime("%a")
    dim["is_weekend"] = (dates.dayofweek >= 5).astype(int)
    return dim


def build_dim_products(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dim = raw["products"].copy()
    dim["gross_margin_pct"] = ((dim["price"] - dim["cogs"]) / dim["price"] * 100).round(2)
    dim["profit_per_unit"] = (dim["price"] - dim["cogs"]).round(2)

    rating = raw["reviews"].groupby("product_id")["rating"].agg(["mean", "count"]).reset_index()
    rating.columns = ["product_id", "avg_rating", "review_count"]
    rating["avg_rating"] = rating["avg_rating"].round(2)

    ret = raw["returns"].groupby("product_id").agg(
        total_returns=("return_id", "count"),
        total_return_qty=("return_quantity", "sum"),
        total_refund=("refund_amount", "sum"),
    ).reset_index()

    sold = raw["order_items"].groupby("product_id")["quantity"].sum().rename("total_sold_qty").reset_index()

    dim = dim.merge(rating, on="product_id", how="left").merge(ret, on="product_id", how="left") \
        .merge(sold, on="product_id", how="left")
    count_cols = ["review_count", "total_returns", "total_return_qty", "total_sold_qty"]
    dim[count_cols] = dim[count_cols].fillna(0).astype(int)
    dim["total_refund"] = dim["total_refund"].fillna(0).round(2)
    dim["return_rate_pct"] = safe_pct(dim["total_return_qty"], dim["total_sold_qty"])
    return dim


def rfm_segment(r: pd.Series, f: pd.Series, m: pd.Series) -> np.ndarray:
    """Nhãn RFM theo thứ tự ưu tiên (điều kiện đầu tiên khớp được chọn)."""
    rules = [
        ("Champions", (r >= 4) & (f >= 4)),
        ("Loyal Customers", (r >= 3) & (f >= 3)),
        ("New Customers", (r >= 4) & (f <= 2)),
        ("Potential Loyalists", (r >= 3) & (m >= 3)),
        ("Cant Lose Them", (r <= 2) & (f >= 4) & (m >= 4)),
        ("At Risk", (r <= 2) & (f >= 3)),
        ("Lost", (r <= 2) & (f <= 2)),
        ("About To Sleep", (r == 3) & (f <= 2)),
    ]
    return np.select([cond for _, cond in rules], [label for label, _ in rules], default="Need Attention")


def build_dim_customers(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = raw["orders"]
    revenue_orders = orders[orders["order_status"].isin(REVENUE_STATUSES)] \
        .merge(raw["payments"][["order_id", "payment_value"]], on="order_id", how="left")
    ref_date = orders["order_date"].max() + pd.Timedelta(days=1)

    rfm = revenue_orders.groupby("customer_id").agg(
        first_order_date=("order_date", "min"),
        last_order_date=("order_date", "max"),
        frequency=("order_id", "nunique"),
        monetary=("payment_value", "sum"),
        avg_order_value=("payment_value", "mean"),
    ).reset_index()
    rfm["recency_days"] = (ref_date - rfm["last_order_date"]).dt.days
    rfm["tenure_days"] = (ref_date - rfm["first_order_date"]).dt.days
    rfm[["monetary", "avg_order_value"]] = rfm[["monetary", "avg_order_value"]].round(2)

    # rank(method="first") tránh lỗi trùng biên quintile khi nhiều khách cùng giá trị.
    rfm["R_score"] = pd.qcut(rfm["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["RFM_score"] = rfm["R_score"] * 100 + rfm["F_score"] * 10 + rfm["M_score"]
    rfm["rfm_segment"] = rfm_segment(rfm["R_score"], rfm["F_score"], rfm["M_score"])

    total_orders = orders.groupby("customer_id")["order_id"].nunique().rename("total_orders").reset_index()

    dim = raw["customers"].merge(
        raw["geography"][["zip", "region", "district"]], on="zip", how="left"
    ).merge(total_orders, on="customer_id", how="left").merge(rfm, on="customer_id", how="left")
    dim["total_orders"] = dim["total_orders"].fillna(0).astype(int)
    dim["frequency"] = dim["frequency"].fillna(0).astype(int)
    dim["monetary"] = dim["monetary"].fillna(0)
    # Khách chưa có đơn phát sinh doanh thu: tách "chưa đặt" và "đặt nhưng hủy/chưa thanh toán".
    dim["rfm_segment"] = np.where(
        dim["rfm_segment"].notna(), dim["rfm_segment"],
        np.where(dim["total_orders"] > 0, "No Converted Order", "Never Purchased"),
    )
    dim["signup_year"] = dim["signup_date"].dt.year
    dim["cohort_month"] = dim["first_order_date"].dt.strftime("%Y-%m")

    if SEGMENTS_PATH.is_file():
        segments = pd.read_csv(SEGMENTS_PATH).rename(columns={
            "segment_method": "kmeans_method", "segment": "kmeans_segment", "segment_name": "kmeans_segment_name",
        })
        dim = dim.merge(segments, on="customer_id", how="left")
        print("  + merged K-Means segments from customer_segmentation")
    return dim


# ---------------------------------------------------------------------------
# Facts
# ---------------------------------------------------------------------------
def build_fact_orders(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Grain = đơn. Dùng cho đếm đơn, AOV, payment, conversion."""
    items = raw["order_items"].assign(gross=lambda d: d["quantity"] * d["unit_price"])
    items = items.groupby("order_id").agg(
        item_lines=("product_id", "count"),
        total_qty=("quantity", "sum"),
        gross_revenue=("gross", "sum"),
        discount_amount=("discount_amount", "sum"),
        has_promo=("promo_id", lambda s: int(s.notna().any())),
    ).reset_index()
    refunds = raw["returns"].groupby("order_id")["refund_amount"].sum().rename("refund_amount").reset_index()

    fact = raw["orders"].merge(raw["payments"][["order_id", "payment_value", "installments"]],
                               on="order_id", how="left") \
        .merge(items, on="order_id", how="left") \
        .merge(raw["shipments"][["order_id", "shipping_fee"]], on="order_id", how="left") \
        .merge(refunds, on="order_id", how="left")
    fact["refund_amount"] = fact["refund_amount"].fillna(0)
    fact["is_revenue_order"] = fact["order_status"].isin(REVENUE_STATUSES).astype(int)
    fact["net_revenue_after_refund"] = np.where(
        fact["is_revenue_order"] == 1, (fact["payment_value"] - fact["refund_amount"]).round(2), 0)

    # Đơn đầu tiên / mua lại của khách (theo đơn phát sinh doanh thu).
    rev = fact[fact["is_revenue_order"] == 1].sort_values(["customer_id", "order_date", "order_id"])
    seq = rev.groupby("customer_id").cumcount() + 1
    fact["customer_order_seq"] = seq.reindex(fact.index)
    fact["customer_order_type"] = np.select(
        [fact["customer_order_seq"] == 1, fact["customer_order_seq"] > 1], ["New", "Repeat"], default="Non-revenue")
    return fact


def build_fact_orders_enriched(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Grain = dòng sản phẩm. Thuộc tính sản phẩm/địa lý lấy qua quan hệ dim_products/dim_geography."""
    fact = raw["order_items"].merge(
        raw["orders"][["order_id", "order_date", "customer_id", "zip", "order_status",
                       "payment_method", "device_type", "order_source"]],
        on="order_id", how="left",
    ).merge(raw["products"][["product_id", "cogs"]], on="product_id", how="left")

    fact["line_revenue"] = (fact["quantity"] * fact["unit_price"]).round(2)  # trước giảm giá
    fact["line_net_revenue"] = (fact["line_revenue"] - fact["discount_amount"]).round(2)
    fact["line_cost"] = (fact["quantity"] * fact["cogs"]).round(2)
    fact["line_gross_profit"] = (fact["line_net_revenue"] - fact["line_cost"]).round(2)
    fact["line_margin_pct"] = np.where(
        fact["line_net_revenue"] > 0, (fact["line_gross_profit"] / fact["line_net_revenue"] * 100).round(2), 0)
    fact["has_promo"] = fact["promo_id"].notna().astype(int)
    fact["discount_pct"] = np.where(
        fact["line_revenue"] > 0, (fact["discount_amount"] / fact["line_revenue"] * 100).round(2), 0)
    fact["is_revenue_order"] = fact["order_status"].isin(REVENUE_STATUSES).astype(int)

    returned = raw["returns"].groupby(["order_id", "product_id"]).agg(
        return_qty=("return_quantity", "sum"), refund_amount=("refund_amount", "sum")).reset_index()
    fact = fact.merge(returned, on=["order_id", "product_id"], how="left")
    fact["return_qty"] = fact["return_qty"].fillna(0).astype(int)
    fact["refund_amount"] = fact["refund_amount"].fillna(0)
    return fact.drop(columns=["cogs"])


def build_fact_returns(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = raw["returns"].merge(
        raw["orders"][["order_id", "order_date", "customer_id", "order_source", "device_type"]],
        on="order_id", how="left",
    ).merge(raw["shipments"][["order_id", "delivery_date"]], on="order_id", how="left")
    fact["days_to_return"] = (fact["return_date"] - fact["order_date"]).dt.days
    fact["days_after_delivery"] = (fact["return_date"] - fact["delivery_date"]).dt.days
    return fact


def build_fact_shipments(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = raw["shipments"].merge(
        raw["orders"][["order_id", "order_date", "customer_id", "zip", "order_status"]],
        on="order_id", how="left",
    ).merge(raw["geography"][["zip", "region"]], on="zip", how="left")
    fact["processing_days"] = (fact["ship_date"] - fact["order_date"]).dt.days
    fact["delivery_days"] = (fact["delivery_date"] - fact["ship_date"]).dt.days
    fact["total_lead_time"] = (fact["delivery_date"] - fact["order_date"]).dt.days
    fact["delivery_bucket"] = pd.cut(
        fact["delivery_days"], bins=[-1, 2, 5, 7, 14, np.inf],
        labels=["1-2 days", "3-5 days", "6-7 days", "8-14 days", "15+ days"],
    ).astype(str)
    fact["delivery_bucket_order"] = pd.cut(fact["delivery_days"], bins=[-1, 2, 5, 7, 14, np.inf],
                                           labels=False).astype(int) + 1  # Sort by column
    return fact


def build_fact_sales_daily(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = raw["sales"].rename(columns={"Date": "date", "Revenue": "revenue", "COGS": "cogs"}) \
        .sort_values("date").reset_index(drop=True)
    fact["gross_profit"] = (fact["revenue"] - fact["cogs"]).round(2)
    fact["gross_margin_pct"] = safe_pct(fact["gross_profit"], fact["revenue"])
    fact["revenue_ma7"] = fact["revenue"].rolling(7, min_periods=1).mean().round(2)
    fact["revenue_ma30"] = fact["revenue"].rolling(30, min_periods=1).mean().round(2)

    # Cùng ngày năm trước theo lịch (29/02 → 28/02).
    last_year = fact[["date", "revenue"]].rename(columns={"revenue": "revenue_ly"})
    last_year["date"] = last_year["date"] + pd.DateOffset(years=1)
    last_year = last_year.drop_duplicates("date", keep="last")
    fact = fact.merge(last_year, on="date", how="left")
    fact["yoy_growth_pct"] = safe_pct(fact["revenue"] - fact["revenue_ly"], fact["revenue_ly"])
    return fact


def build_fact_inventory(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    # product_name/category/segment/year/month đã có trong dim_products/dim_date.
    fact = raw["inventory"].drop(columns=["product_name", "category", "segment", "year", "month"],
                                 errors="ignore")
    fact = fact.merge(raw["products"][["product_id", "price", "cogs"]], on="product_id", how="left")
    fact["inventory_value_retail"] = (fact["stock_on_hand"] * fact["price"]).round(2)
    fact["inventory_value_cost"] = (fact["stock_on_hand"] * fact["cogs"]).round(2)
    fact["inventory_health"] = np.select(
        [fact["stockout_flag"] == 1, fact["overstock_flag"] == 1, fact["reorder_flag"] == 1],
        ["Stockout", "Overstock", "Reorder Needed"], default="Healthy",
    )
    return fact.drop(columns=["price", "cogs"])


def build_fact_web_traffic(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fact = raw["web_traffic"].rename(columns={"date": "traffic_date"})
    fact["pages_per_session"] = (fact["page_views"] / fact["sessions"]).round(2)
    revenue_orders = raw["orders"][raw["orders"]["order_status"].isin(REVENUE_STATUSES)]
    orders_per_day = revenue_orders.groupby("order_date")["order_id"].nunique() \
        .rename("orders").rename_axis("traffic_date").reset_index()
    fact = fact.merge(orders_per_day, on="traffic_date", how="left")
    fact["orders"] = fact["orders"].fillna(0).astype(int)
    fact["conversion_rate_pct"] = safe_pct(fact["orders"], fact["sessions"])
    return fact


# ---------------------------------------------------------------------------
# Aggregates
# ---------------------------------------------------------------------------
def build_agg_cohort_retention(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    orders = raw["orders"][raw["orders"]["order_status"].isin(REVENUE_STATUSES)][
        ["order_id", "customer_id", "order_date"]].copy()
    orders["order_month"] = orders["order_date"].dt.to_period("M")
    orders["cohort_month"] = orders.groupby("customer_id")["order_month"].transform("min")
    orders["period_number"] = (orders["order_month"] - orders["cohort_month"]).apply(lambda x: x.n)

    cohort_sizes = orders.groupby("cohort_month")["customer_id"].nunique().rename("cohort_size")
    retention = orders.groupby(["cohort_month", "period_number"])["customer_id"].nunique() \
        .rename("active_customers").reset_index().merge(cohort_sizes, on="cohort_month")
    retention["retention_rate"] = (retention["active_customers"] / retention["cohort_size"] * 100).round(2)
    retention = retention[retention["period_number"] <= COHORT_MAX_PERIOD]
    retention["cohort_year"] = retention["cohort_month"].dt.year
    retention["cohort_month"] = retention["cohort_month"].dt.start_time
    return retention.sort_values(["cohort_month", "period_number"]).reset_index(drop=True)


def build_agg_monthly_summary(fact_sales: pd.DataFrame, fact_orders: pd.DataFrame,
                              fact_web: pd.DataFrame) -> pd.DataFrame:
    sales = fact_sales.assign(month=fact_sales["date"].dt.to_period("M").dt.start_time)
    monthly = sales.groupby("month").agg(
        revenue=("revenue", "sum"),
        cogs=("cogs", "sum"),
        gross_profit=("gross_profit", "sum"),
        avg_daily_rev=("revenue", "mean"),
        days_in_month=("revenue", "count"),
    ).reset_index()

    rev_orders = fact_orders[fact_orders["is_revenue_order"] == 1]
    orders = rev_orders.assign(month=rev_orders["order_date"].dt.to_period("M").dt.start_time) \
        .groupby("month").agg(
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            new_customers=("customer_order_type", lambda s: int((s == "New").sum())),
            net_payment=("payment_value", "sum"),
        ).reset_index()
    web = fact_web.assign(month=fact_web["traffic_date"].dt.to_period("M").dt.start_time) \
        .groupby("month")["sessions"].sum().reset_index()

    monthly = monthly.merge(orders, on="month", how="left").merge(web, on="month", how="left")
    monthly["gross_margin_pct"] = safe_pct(monthly["gross_profit"], monthly["revenue"])
    monthly["aov"] = (monthly["net_payment"] / monthly["orders"]).round(2)
    monthly["revenue_prev"] = monthly["revenue"].shift(1)
    monthly["mom_growth_pct"] = safe_pct(monthly["revenue"] - monthly["revenue_prev"], monthly["revenue_prev"])
    monthly["revenue_ly"] = monthly["revenue"].shift(12)
    monthly["yoy_growth_pct"] = safe_pct(monthly["revenue"] - monthly["revenue_ly"], monthly["revenue_ly"])
    monthly["year_month"] = monthly["month"].dt.strftime("%Y-%m")
    return monthly.round(2)


def build_agg_reviews_summary(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    reviews = raw["reviews"].merge(raw["products"][["product_id", "category", "segment"]],
                                   on="product_id", how="left")
    reviews["review_month"] = reviews["review_date"].dt.to_period("M").dt.start_time
    summary = reviews.groupby(["review_month", "category"]).agg(
        avg_rating=("rating", "mean"),
        review_count=("review_id", "count"),
        pct_5_star=("rating", lambda x: (x == 5).mean() * 100),
        pct_1_star=("rating", lambda x: (x == 1).mean() * 100),
    ).reset_index()
    summary["year_month"] = summary["review_month"].dt.strftime("%Y-%m")
    return summary.round(2)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw()

    print("Dimensions")
    save(build_dim_date(raw), "dim_date.csv")
    save(build_dim_products(raw), "dim_products.csv")
    save(build_dim_customers(raw), "dim_customers_rfm.csv")
    save(raw["geography"], "dim_geography.csv")
    save(raw["promotions"], "dim_promotions.csv")

    print("Facts")
    fact_orders = build_fact_orders(raw)
    save(fact_orders, "fact_orders.csv")
    save(build_fact_orders_enriched(raw), "fact_orders_enriched.csv")
    save(build_fact_returns(raw), "fact_returns_enriched.csv")
    save(build_fact_shipments(raw), "fact_shipments_enriched.csv")
    fact_sales = build_fact_sales_daily(raw)
    save(fact_sales, "fact_sales_daily.csv")
    save(build_fact_inventory(raw), "fact_inventory.csv")
    fact_web = build_fact_web_traffic(raw)
    save(fact_web, "fact_web_traffic.csv")

    print("Aggregates")
    save(build_agg_cohort_retention(raw), "agg_cohort_retention.csv")
    save(build_agg_monthly_summary(fact_sales, fact_orders, fact_web), "agg_monthly_summary.csv")
    save(build_agg_reviews_summary(raw), "agg_reviews_summary.csv")
    print(f"Done -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
