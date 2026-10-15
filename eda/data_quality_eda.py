"""EDA và kiểm tra chất lượng dữ liệu theo từng bảng.

Với mỗi bảng trong data/raw/ script kiểm tra:
  1. Missing values  — theo cột, phân biệt thiếu bắt buộc (lỗi) và trống có ý nghĩa.
  2. Trùng lặp       — trùng toàn dòng, trùng khóa chính, trùng khóa nghiệp vụ.
  3. Dữ liệu không hợp lệ — sai kiểu số/ngày, ngoài miền giá trị, âm, ngày ngoài phạm vi.
  4. Ràng buộc nghiệp vụ — khóa ngoại và quan hệ giữa các bảng (vd tiền hoàn ≤ tiền
     thanh toán, ngày giao ≥ ngày gửi ≥ ngày đặt, số lượng trả ≤ số lượng mua…).
  5. Outlier         — rào IQR 1,5× / 3× (thang gốc và thang log) cho mọi biến số.

Script chỉ phát hiện và ghi nhận, không sửa dữ liệu gốc. Mỗi kiểm tra có đề xuất xử lý.
Đầu ra:
  data/processed/eda/data_quality_checks.csv   — toàn bộ kiểm tra + số vi phạm + đề xuất
  data/processed/eda/missing_values.csv        — missing theo cột + chính sách xử lý
  data/processed/eda/outliers.csv              — thống kê outlier theo cột
  data/processed/eda/table_overview.csv        — số dòng/cột/missing/trùng theo bảng
  data/processed/eda/violations/*.csv          — các dòng vi phạm của từng kiểm tra
  data/processed/eda/plots/*.png               — histogram + boxplot biến số
  reports/markdown/data_quality_and_eda.md     — báo cáo tổng hợp theo bảng (nguồn của PDF)
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "eda"
VIOLATION_DIR = OUTPUT_DIR / "violations"
PLOT_DIR = OUTPUT_DIR / "plots"
REPORT_PATH = ROOT / "reports" / "markdown" / "data_quality_and_eda.md"

DATA_START = pd.Timestamp("2012-01-01")
DATA_END = pd.Timestamp("2022-12-31")
MONEY_TOLERANCE = 1.0

ERROR, WARNING, INFO = "ERROR", "WARNING", "INFO"
SEVERITY_ORDER = {ERROR: 0, WARNING: 1, INFO: 2}

CHANNELS = {"direct", "email_campaign", "organic_search", "paid_search", "referral", "social_media"}

# Cấu hình theo bảng. pk: khóa chính; business_keys: khóa nghiệp vụ không được trùng;
# required: cột bắt buộc có giá trị; integers/dates: kiểu mong đợi; domains: miền giá trị;
# non_negative / positive / rates: ràng buộc giá trị số; no_outlier: cột số không rà outlier.
TABLES: dict[str, dict[str, object]] = {
    "customers": {
        "group": "Master",
        "pk": ["customer_id"],
        "required": ["customer_id", "zip", "city", "signup_date", "gender", "age_group", "acquisition_channel"],
        "integers": ["customer_id", "zip"],
        "dates": ["signup_date"],
        "domains": {
            "gender": {"Female", "Male", "Non-binary"},
            "age_group": {"18-24", "25-34", "35-44", "45-54", "55+"},
            "acquisition_channel": CHANNELS,
        },
    },
    "geography": {
        "group": "Master",
        "pk": ["zip"],
        "required": ["zip", "city", "region", "district"],
        "integers": ["zip"],
        "domains": {"region": {"East", "Central", "West"}},
    },
    "products": {
        "group": "Master",
        "pk": ["product_id"],
        "business_keys": [["product_name", "size", "color"]],
        "required": ["product_id", "product_name", "category", "segment", "size", "color", "price", "cogs"],
        "integers": ["product_id"],
        "domains": {
            "category": {"Casual", "GenZ", "Outdoor", "Streetwear"},
            "size": {"S", "M", "L", "XL"},
        },
        "positive": ["price", "cogs"],
    },
    "promotions": {
        "group": "Master",
        "pk": ["promo_id"],
        "required": ["promo_id", "promo_name", "promo_type", "discount_value", "start_date", "end_date",
                     "promo_channel", "stackable_flag", "min_order_value"],
        "dates": ["start_date", "end_date"],
        "domains": {
            "promo_type": {"percentage", "fixed"},
            "applicable_category": {"Casual", "GenZ", "Outdoor", "Streetwear"},
            "promo_channel": {"all_channels", "email", "in_store", "online", "social_media"},
            "stackable_flag": {0, 1},
        },
        "positive": ["discount_value"],
        "non_negative": ["min_order_value"],
        "no_outlier": ["stackable_flag"],
    },
    "orders": {
        "group": "Transaction",
        "pk": ["order_id"],
        "required": ["order_id", "order_date", "customer_id", "zip", "order_status", "payment_method",
                     "device_type", "order_source"],
        "integers": ["order_id", "customer_id", "zip"],
        "dates": ["order_date"],
        "domains": {
            "order_status": {"created", "paid", "shipped", "delivered", "returned", "cancelled"},
            "payment_method": {"apple_pay", "bank_transfer", "cod", "credit_card", "paypal"},
            "device_type": {"desktop", "mobile", "tablet"},
            "order_source": CHANNELS,
        },
    },
    "order_items": {
        "group": "Transaction",
        "business_keys": [["order_id", "product_id"]],
        "required": ["order_id", "product_id", "quantity", "unit_price", "discount_amount"],
        "integers": ["order_id", "product_id", "quantity"],
        "positive": ["quantity", "unit_price"],
        "non_negative": ["discount_amount"],
    },
    "payments": {
        "group": "Transaction",
        "pk": ["order_id"],
        "required": ["order_id", "payment_method", "payment_value", "installments"],
        "integers": ["order_id", "installments"],
        "domains": {"payment_method": {"apple_pay", "bank_transfer", "cod", "credit_card", "paypal"}},
        "positive": ["payment_value", "installments"],
        "no_outlier": ["installments"],
    },
    "shipments": {
        "group": "Transaction",
        "pk": ["order_id"],
        "required": ["order_id", "ship_date", "delivery_date", "shipping_fee"],
        "integers": ["order_id"],
        "dates": ["ship_date", "delivery_date"],
        "non_negative": ["shipping_fee"],
    },
    "returns": {
        "group": "Transaction",
        "pk": ["return_id"],
        "business_keys": [["order_id", "product_id"]],
        "required": ["return_id", "order_id", "product_id", "return_date", "return_reason",
                     "return_quantity", "refund_amount"],
        "integers": ["order_id", "product_id", "return_quantity"],
        "dates": ["return_date"],
        "domains": {"return_reason": {"changed_mind", "defective", "late_delivery", "not_as_described", "wrong_size"}},
        "positive": ["return_quantity", "refund_amount"],
    },
    "reviews": {
        "group": "Transaction",
        "pk": ["review_id"],
        "business_keys": [["order_id", "product_id"]],
        "required": ["review_id", "order_id", "product_id", "customer_id", "review_date", "rating"],
        "integers": ["order_id", "product_id", "customer_id", "rating"],
        "dates": ["review_date"],
        "domains": {"rating": {1, 2, 3, 4, 5}},
        "no_outlier": ["rating"],
    },
    "sales": {
        "group": "Analytical",
        "pk": ["Date"],
        "required": ["Date", "Revenue", "COGS"],
        "dates": ["Date"],
        "positive": ["Revenue", "COGS"],
    },
    "inventory": {
        "group": "Operational",
        "business_keys": [["product_id", "snapshot_date"]],
        "required": ["snapshot_date", "product_id", "stock_on_hand", "units_received", "units_sold"],
        "integers": ["product_id", "stock_on_hand", "units_received", "units_sold", "stockout_days",
                     "stockout_flag", "overstock_flag", "reorder_flag", "year", "month"],
        "dates": ["snapshot_date"],
        "domains": {
            "stockout_flag": {0, 1},
            "overstock_flag": {0, 1},
            "reorder_flag": {0, 1},
            "month": set(range(1, 13)),
        },
        "non_negative": ["stock_on_hand", "units_received", "units_sold", "stockout_days", "days_of_supply"],
        "rates": ["fill_rate", "sell_through_rate"],
        "no_outlier": ["stockout_flag", "overstock_flag", "reorder_flag", "year", "month"],
    },
    "web_traffic": {
        "group": "Operational",
        "pk": ["date"],
        "required": ["date", "sessions", "unique_visitors", "page_views", "bounce_rate",
                     "avg_session_duration_sec", "traffic_source"],
        "integers": ["sessions", "unique_visitors", "page_views"],
        "dates": ["date"],
        "domains": {"traffic_source": CHANNELS},
        "positive": ["sessions", "unique_visitors", "page_views", "avg_session_duration_sec"],
        "rates": ["bounce_rate"],
    },
}

# Cột được phép trống vì giá trị trống mang ý nghĩa nghiệp vụ.
MISSING_POLICY = {
    ("order_items", "promo_id"): "Trống = dòng không dùng khuyến mãi. Giữ nguyên / điền 'NO_PROMO' khi phân tích.",
    ("order_items", "promo_id_2"): "Trống = không có khuyến mãi cộng dồn. Giữ nguyên / điền 'NO_PROMO'.",
    ("promotions", "applicable_category"): "Trống = áp dụng mọi danh mục. Điền 'ALL'.",
}

FOREIGN_KEYS = [
    ("customers", "zip", "geography", "zip"),
    ("orders", "customer_id", "customers", "customer_id"),
    ("orders", "zip", "geography", "zip"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "promo_id", "promotions", "promo_id"),
    ("order_items", "promo_id_2", "promotions", "promo_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("shipments", "order_id", "orders", "order_id"),
    ("returns", "order_id", "orders", "order_id"),
    ("returns", "product_id", "products", "product_id"),
    ("reviews", "order_id", "orders", "order_id"),
    ("reviews", "product_id", "products", "product_id"),
    ("reviews", "customer_id", "customers", "customer_id"),
    ("inventory", "product_id", "products", "product_id"),
]


def is_identifier(column: str) -> bool:
    return column.lower().endswith("_id") or column.lower() == "zip"


class QualityLog:
    """Ghi nhận kết quả kiểm tra và lưu các dòng vi phạm ra CSV."""

    def __init__(self) -> None:
        self.checks: list[dict[str, object]] = []

    def add(
        self,
        table: str,
        category: str,
        check: str,
        description: str,
        mask: pd.Series,
        frame: pd.DataFrame,
        *,
        columns: list[str] | None = None,
        severity: str = ERROR,
        action: str = "",
        checked: int | None = None,
    ) -> int:
        mask = mask.fillna(False).astype(bool)
        invalid = int(mask.sum())
        checked = len(mask) if checked is None else int(checked)
        sample = ""
        if invalid:
            rows = frame.loc[mask, columns or list(frame.columns)]
            rows.to_csv(VIOLATION_DIR / f"{table}__{check}.csv", index=False)
            sample = " | ".join(
                ", ".join(f"{key}={value}" for key, value in record.items())
                for record in rows.head(3).astype(str).to_dict("records")
            )
        self.checks.append(
            {
                "table": table,
                "category": category,
                "check": check,
                "description": description,
                "severity": severity,
                "status": "ISSUE" if invalid else "PASS",
                "checked_rows": checked,
                "invalid_rows": invalid,
                "invalid_pct": invalid / checked * 100 if checked else 0.0,
                "action": action if invalid else "",
                "sample": sample,
            }
        )
        return invalid


# --------------------------------------------------------------------------- load


def load_tables(log: QualityLog) -> dict[str, pd.DataFrame]:
    """Đọc CSV và chuyển kiểu; giá trị không chuyển được bị ghi nhận rồi đặt NaN/NaT."""
    tables: dict[str, pd.DataFrame] = {}
    for name, config in TABLES.items():
        path = RAW_DIR / f"{name}.csv"
        if not path.is_file():
            print(f"Bỏ qua {name}: không tìm thấy {path}")
            continue
        frame = pd.read_csv(path, low_memory=False)
        missing_columns = sorted(set(config.get("required", [])) - set(frame.columns))
        if missing_columns:
            raise ValueError(f"{name}.csv thiếu cột bắt buộc: {missing_columns}")

        numeric_columns = set(config.get("integers", [])) | set(config.get("positive", [])) | set(
            config.get("non_negative", [])
        ) | set(config.get("rates", []))
        for column in sorted(numeric_columns & set(frame.columns)):
            raw = frame[column]
            parsed = pd.to_numeric(raw, errors="coerce")
            log.add(
                name, "invalid", f"{column}__numeric_parse", f"`{column}` phải là số",
                raw.notna() & parsed.isna(), frame, columns=[column],
                action="Kiểm tra định dạng nguồn (dấu phẩy, ký tự lạ); đặt NaN rồi xử lý như missing.",
            )
            frame[column] = parsed
            if column in config.get("integers", []):
                log.add(
                    name, "invalid", f"{column}__integer", f"`{column}` phải là số nguyên",
                    parsed.notna() & parsed.mod(1).ne(0), frame, columns=[column],
                    action="Xác minh nguồn; làm tròn nếu chỉ là sai số lưu trữ.",
                )

        for column in config.get("dates", []):
            raw = frame[column]
            parsed = pd.to_datetime(raw, errors="coerce")
            log.add(
                name, "invalid", f"{column}__date_parse", f"`{column}` phải là ngày hợp lệ",
                raw.notna() & parsed.isna(), frame, columns=[column],
                action="Chuẩn hóa định dạng ngày; giá trị không cứu được đặt NaT.",
            )
            frame[column] = parsed
        tables[name] = frame
    return tables


# ------------------------------------------------------------------ generic checks


def check_missing(name: str, frame: pd.DataFrame, log: QualityLog) -> list[dict[str, object]]:
    config = TABLES[name]
    rows = []
    for column in frame.columns:
        missing = frame[column].isna()
        count = int(missing.sum())
        required = column in config.get("required", [])
        policy = MISSING_POLICY.get((name, column))
        if required:
            log.add(
                name, "missing", f"{column}__required", f"`{column}` là cột bắt buộc, không được trống",
                missing, frame,
                action="Bổ sung từ bảng liên quan nếu suy ra được; nếu không thì loại dòng khỏi phân tích dùng cột này.",
            )
        if count == 0:
            treatment = ""
        elif policy:
            treatment = policy
        elif required:
            treatment = "Lỗi — xem data_quality_checks.csv"
        elif pd.api.types.is_numeric_dtype(frame[column]):
            treatment = "Điền median theo nhóm hoặc giữ NaN + thêm cờ missing."
        else:
            treatment = "Điền 'Unknown'."
        rows.append(
            {
                "table": name,
                "column": column,
                "dtype": str(frame[column].dtype),
                "missing_count": count,
                "missing_pct": count / len(frame) * 100 if len(frame) else 0.0,
                "required": required,
                "missing_type": "" if count == 0 else ("có ý nghĩa nghiệp vụ" if policy else "thiếu thật"),
                "treatment": treatment,
            }
        )
    return rows


def check_duplicates(name: str, frame: pd.DataFrame, log: QualityLog) -> None:
    config = TABLES[name]
    log.add(
        name, "duplicate", "full_row_duplicate", "Không có dòng trùng toàn bộ",
        frame.duplicated(keep=False), frame,
        action="Giữ 1 bản (drop_duplicates).",
    )
    pk = config.get("pk")
    if pk:
        log.add(
            name, "duplicate", "primary_key_unique", f"Khóa chính ({', '.join(pk)}) là duy nhất",
            frame.duplicated(pk, keep=False), frame,
            action="Nếu nội dung giống nhau: giữ 1 bản; nếu khác: giữ bản mới nhất và báo nguồn.",
        )
    for key in config.get("business_keys", []):
        log.add(
            name, "duplicate", f"business_key__{'_'.join(key)}", f"Khóa nghiệp vụ ({', '.join(key)}) không lặp",
            frame.duplicated(key, keep=False), frame, severity=WARNING,
            action="Gộp các dòng cùng khóa (cộng số lượng/tiền) trước khi nối bảng để tránh nhân bản.",
        )


def check_values(name: str, frame: pd.DataFrame, log: QualityLog) -> None:
    config = TABLES[name]
    for column, allowed in config.get("domains", {}).items():
        values = frame[column]
        log.add(
            name, "invalid", f"{column}__allowed_values", f"`{column}` ∈ {{{', '.join(map(str, sorted(allowed)))}}}",
            values.notna() & ~values.isin(allowed), frame, columns=[column],
            action="Chuẩn hóa chính tả/viết hoa; giá trị lạ gán 'Unknown'.",
        )
    for column in config.get("positive", []):
        log.add(
            name, "invalid", f"{column}__positive", f"`{column}` > 0",
            frame[column].le(0), frame,
            action="Giá trị ≤ 0 không hợp lệ: đặt NaN và loại khỏi tính toán liên quan.",
        )
    for column in config.get("non_negative", []):
        log.add(
            name, "invalid", f"{column}__non_negative", f"`{column}` ≥ 0",
            frame[column].lt(0), frame,
            action="Giá trị âm không hợp lệ: đặt NaN hoặc lấy trị tuyệt đối nếu xác nhận sai dấu.",
        )
    for column in config.get("rates", []):
        log.add(
            name, "invalid", f"{column}__rate_0_1", f"`{column}` nằm trong [0, 1]",
            frame[column].notna() & ~frame[column].between(0, 1), frame,
            action="Nếu đang ở thang % thì chia 100; còn lại clip về [0, 1].",
        )
    for column in config.get("dates", []):
        values = frame[column]
        log.add(
            name, "invalid", f"{column}__in_range",
            f"`{column}` trong phạm vi {DATA_START.date()} – {DATA_END.date()}",
            values.notna() & ~values.between(DATA_START, DATA_END), frame, columns=[column],
            action="Ngày ngoài phạm vi nghiên cứu: kiểm tra lỗi nhập; loại khỏi phân tích chuỗi thời gian.",
        )
    for column in frame.columns:
        values = frame[column]
        if not (pd.api.types.is_object_dtype(values) or pd.api.types.is_string_dtype(values)):
            continue
        text = values.dropna().astype(str)
        if text.empty:
            continue
        normalized = text.str.strip().str.lower()
        variants = text.groupby(normalized).nunique()
        inconsistent = text.ne(text.str.strip()) | normalized.isin(variants[variants > 1].index)
        log.add(
            name, "invalid", f"{column}__text_format", f"`{column}` không có khoảng trắng thừa / biến thể hoa-thường",
            inconsistent.reindex(frame.index, fill_value=False), frame, columns=[column], severity=WARNING,
            action="strip() và chuẩn hóa hoa-thường.",
        )


def check_foreign_keys(tables: dict[str, pd.DataFrame], log: QualityLog) -> None:
    for child, column, parent, parent_column in FOREIGN_KEYS:
        if child not in tables or parent not in tables:
            continue
        values = tables[child][column]
        log.add(
            child, "referential", f"{column}__fk_{parent}", f"`{column}` tồn tại trong `{parent}.{parent_column}`",
            values.notna() & ~values.isin(tables[parent][parent_column]), tables[child],
            checked=int(values.notna().sum()),
            action=f"Bản ghi mồ côi: loại khi nối với `{parent}` hoặc bổ sung bản ghi cha.",
        )


def profile_outliers(name: str, frame: pd.DataFrame) -> list[dict[str, object]]:
    config = TABLES[name]
    skip = set(config.get("no_outlier", []))
    rows = []
    for column in frame.columns:
        values = frame[column]
        if column in skip or is_identifier(column) or not pd.api.types.is_numeric_dtype(values):
            continue
        clean = values.dropna()
        if clean.nunique() <= 2:
            continue
        q1, q3 = clean.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier = values.lt(lower) | values.gt(upper)
        extreme = values.lt(q1 - 3 * iqr) | values.gt(q3 + 3 * iqr)
        log_outliers = np.nan
        if clean.gt(0).all():
            logged = np.log(clean)
            lq1, lq3 = logged.quantile([0.25, 0.75])
            liqr = lq3 - lq1
            log_outliers = int((logged.lt(lq1 - 1.5 * liqr) | logged.gt(lq3 + 1.5 * liqr)).sum())
        if outlier.any():
            frame.loc[outlier].assign(
                iqr_lower=lower, iqr_upper=upper
            ).to_csv(VIOLATION_DIR / f"{name}__{column}__iqr_outlier.csv", index=False)
        rows.append(
            {
                "table": name,
                "column": column,
                "count": int(clean.size),
                "mean": clean.mean(),
                "std": clean.std(),
                "min": clean.min(),
                "q1": q1,
                "median": clean.median(),
                "q3": q3,
                "max": clean.max(),
                "skew": clean.skew(),
                "iqr_lower": lower,
                "iqr_upper": upper,
                "iqr_outliers": int(outlier.sum()),
                "iqr_outlier_pct": outlier.sum() / clean.size * 100,
                "extreme_outliers_3iqr": int(extreme.sum()),
                "log_iqr_outliers": log_outliers,
            }
        )
        figure, (hist_axis, box_axis) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [3, 1]})
        hist_axis.hist(clean, bins=50, color="#2a6f97")
        hist_axis.axvline(upper, color="#c1121f", linestyle="--", linewidth=1, label="IQR 1,5×")
        if lower > clean.min():
            hist_axis.axvline(lower, color="#c1121f", linestyle="--", linewidth=1)
        hist_axis.set_title(f"{name}.{column}")
        hist_axis.set_ylabel("Số dòng")
        hist_axis.legend()
        box_axis.boxplot(clean, vert=True, showfliers=True)
        box_axis.set_xticks([])
        figure.tight_layout()
        figure.savefig(PLOT_DIR / f"{name}__{column}.png", dpi=90)
        plt.close(figure)
    return rows


# ------------------------------------------------------------- business rules


def build_context(t: dict[str, pd.DataFrame]) -> SimpleNamespace:
    """Các bảng gốc cộng các bảng tổng hợp dùng chung cho kiểm tra liên bảng."""
    items = t["order_items"].assign(
        gross_amount=t["order_items"]["quantity"] * t["order_items"]["unit_price"],
        net_amount=t["order_items"]["quantity"] * t["order_items"]["unit_price"] - t["order_items"]["discount_amount"],
    )
    return SimpleNamespace(
        customers=t["customers"], geography=t["geography"], products=t["products"], promotions=t["promotions"],
        orders=t["orders"], items=items, payments=t["payments"], shipments=t["shipments"], returns=t["returns"],
        reviews=t["reviews"], sales=t["sales"], inventory=t["inventory"], web=t["web_traffic"],
        order_totals=items.groupby("order_id", as_index=False).agg(
            items_gross=("gross_amount", "sum"), items_net=("net_amount", "sum")
        ),
        line_totals=items.groupby(["order_id", "product_id"], as_index=False).agg(
            purchased_quantity=("quantity", "sum"), line_gross=("gross_amount", "sum"), line_net=("net_amount", "sum")
        ),
        order_info=t["orders"][["order_id", "order_date", "customer_id", "order_status", "payment_method"]],
        ship_info=t["shipments"][["order_id", "ship_date", "delivery_date"]],
    )


def rules_customers(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Khách hàng: city khớp geography, ngày đăng ký so với đơn đầu tiên, khách chưa mua."""
    customers, geography, orders = d.customers, d.geography, d.orders
    merged = customers.merge(geography[["zip", "city"]], on="zip", how="left", suffixes=("", "_geo"))
    log.add(
        "customers", "business_rule", "city_matches_geography", "`city` khớp với `geography.city` theo `zip`",
        merged["city_geo"].notna() & merged["city"].ne(merged["city_geo"]), merged,
        columns=["customer_id", "zip", "city", "city_geo"],
        action="Lấy `city` từ bảng geography làm chuẩn.",
    )
    first_order = orders.groupby("customer_id")["order_date"].min().rename("first_order_date")
    merged = customers.join(first_order, on="customer_id")
    log.add(
        "customers", "business_rule", "signup_not_after_first_order", "Ngày đăng ký ≤ ngày đặt đơn đầu tiên",
        merged["first_order_date"].lt(merged["signup_date"]), merged,
        columns=["customer_id", "signup_date", "first_order_date"], severity=WARNING,
        checked=int(merged["first_order_date"].notna().sum()),
        action="Không dùng `signup_date` để tính tenure/cohort; thay bằng ngày đơn đầu tiên "
        "(hoặc min(signup_date, first_order_date)).",
    )
    log.add(
        "customers", "business_rule", "customer_has_order", "Khách hàng có ít nhất một đơn",
        merged["first_order_date"].isna(), merged, columns=["customer_id", "signup_date"], severity=INFO,
        action="Hợp lệ (khách chưa mua). Giữ trong bảng khách hàng, loại khỏi phân tích RFM.",
    )


def rules_products(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Sản phẩm: giá vốn < giá bán, giá nghi sai đơn vị, SKU chưa bán."""
    products, items = d.products, d.items
    log.add(
        "products", "business_rule", "cogs_less_than_price", "Giá vốn < giá bán (`cogs` < `price`)",
        products["cogs"].ge(products["price"]), products,
        action="Sản phẩm lỗ vốn: xác minh giá; nếu sai thì đặt NaN cho margin.",
    )
    sold = products["product_id"].isin(items["product_id"])
    low_price = products["price"].lt(100)
    log.add(
        "products", "business_rule", "price_scale_suspicious",
        "Giá niêm yết < 100 (nhỏ hơn ~50 lần mức thông thường — nghi sai đơn vị)",
        low_price, products.assign(ever_sold=sold), severity=WARNING,
        action="Các SKU này không có giao dịch; tách riêng hoặc loại khỏi thống kê giá sản phẩm.",
    )
    log.add(
        "products", "business_rule", "product_ever_sold", "SKU xuất hiện ít nhất một lần trong `order_items`",
        ~sold, products, severity=INFO,
        action="SKU chưa bán: giữ trong danh mục, loại khỏi phân tích hiệu quả sản phẩm.",
    )


def rules_promotions(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Khuyến mãi: thứ tự ngày hiệu lực, mức giảm %."""
    promotions = d.promotions
    log.add(
        "promotions", "business_rule", "start_not_after_end", "`start_date` ≤ `end_date`",
        promotions["start_date"].gt(promotions["end_date"]), promotions,
        action="Hoán đổi nếu nhập ngược; nếu không xác định được thì loại chương trình.",
    )
    percentage = promotions["promo_type"].eq("percentage")
    log.add(
        "promotions", "business_rule", "percentage_between_0_100", "Khuyến mãi % có `discount_value` trong (0, 100]",
        percentage & ~promotions["discount_value"].between(0, 100, inclusive="right"), promotions,
        checked=int(percentage.sum()), action="Xác minh mức giảm; giá trị > 100 có thể là số tiền cố định.",
    )


def rules_orders(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Đơn hàng: zip/ngày đăng ký của khách, đơn có items/payment, trạng thái khớp shipments/returns."""
    customers, orders, items, payments, shipments, returns = d.customers, d.orders, d.items, d.payments, d.shipments, d.returns
    merged = orders.merge(customers[["customer_id", "zip"]], on="customer_id", how="left", suffixes=("", "_customer"))
    log.add(
        "orders", "business_rule", "zip_matches_customer", "`zip` của đơn trùng `zip` của khách",
        merged["zip_customer"].notna() & merged["zip"].ne(merged["zip_customer"]), merged,
        columns=["order_id", "customer_id", "zip", "zip_customer"], severity=INFO,
        action="Có thể hợp lệ (giao địa chỉ khác); dùng `orders.zip` cho phân tích địa lý đơn hàng.",
    )
    merged = orders.merge(customers[["customer_id", "signup_date"]], on="customer_id", how="left")
    log.add(
        "orders", "business_rule", "order_not_before_signup", "Ngày đặt ≥ ngày đăng ký của khách",
        merged["order_date"].lt(merged["signup_date"]), merged,
        columns=["order_id", "customer_id", "order_date", "signup_date"], severity=WARNING,
        action="Giữ đơn (giao dịch là dữ liệu gốc đáng tin hơn); coi `signup_date` là không tin cậy.",
    )
    log.add(
        "orders", "business_rule", "order_has_items", "Mỗi đơn có ít nhất một dòng `order_items`",
        ~orders["order_id"].isin(items["order_id"]), orders,
        action="Đơn rỗng: loại khỏi phân tích doanh thu.",
    )
    log.add(
        "orders", "business_rule", "order_has_payment", "Mỗi đơn có một bản ghi `payments`",
        ~orders["order_id"].isin(payments["order_id"]), orders,
        action="Thiếu thanh toán: suy ra từ Σ order_items hoặc loại khỏi phân tích tiền.",
    )
    shipped_status = orders["order_status"].isin(["shipped", "delivered", "returned"])
    has_shipment = orders["order_id"].isin(shipments["order_id"])
    log.add(
        "orders", "business_rule", "shipped_order_has_shipment",
        "Đơn `shipped`/`delivered`/`returned` phải có bản ghi `shipments`",
        shipped_status & ~has_shipment, orders, checked=int(shipped_status.sum()),
        action="Giữ đơn cho doanh thu; loại khỏi phân tích thời gian giao hàng (không impute ngày giao).",
    )
    log.add(
        "orders", "business_rule", "unshipped_order_has_no_shipment",
        "Đơn `created`/`paid`/`cancelled` không có bản ghi `shipments`",
        ~shipped_status & has_shipment, orders, checked=int((~shipped_status).sum()),
        action="Trạng thái lỗi thời: cập nhật trạng thái theo shipments hoặc loại bản ghi vận chuyển.",
    )
    returned = orders["order_status"].eq("returned")
    log.add(
        "orders", "business_rule", "returned_order_has_return", "Đơn `returned` phải có ít nhất một dòng `returns`",
        returned & ~orders["order_id"].isin(returns["order_id"]), orders, checked=int(returned.sum()),
        severity=WARNING, action="Không có tiền hoàn tương ứng: coi tiền hoàn = 0, gắn cờ khi tính tỷ lệ trả.",
    )


def rules_order_items(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Chi tiết đơn: giảm giá ≤ thành tiền, mã khuyến mãi hợp lệ (thời gian, danh mục, giá trị tối thiểu), đơn giá so với niêm yết."""
    products, promotions, items, order_totals, order_info = d.products, d.promotions, d.items, d.order_totals, d.order_info
    log.add(
        "order_items", "business_rule", "discount_not_exceed_gross", "0 ≤ `discount_amount` ≤ `quantity` × `unit_price`",
        items["discount_amount"].gt(items["gross_amount"] + MONEY_TOLERANCE), items,
        action="Clip giảm giá về `quantity × unit_price`.",
    )
    log.add(
        "order_items", "business_rule", "promo2_requires_promo1", "Có `promo_id_2` thì phải có `promo_id`",
        items["promo_id_2"].notna() & items["promo_id"].isna(), items,
        action="Dời `promo_id_2` sang `promo_id`.",
    )
    log.add(
        "order_items", "business_rule", "discount_matches_promo", "Có giảm giá ⇔ có mã khuyến mãi",
        items["discount_amount"].gt(0).ne(items["promo_id"].notna()), items, severity=WARNING,
        action="Giảm giá không rõ nguồn: gán promo 'UNKNOWN'; có mã nhưng không giảm: kiểm tra điều kiện áp dụng.",
    )
    merged = items.merge(order_info[["order_id", "order_date"]], on="order_id", how="left").merge(
        promotions[["promo_id", "start_date", "end_date", "applicable_category", "min_order_value"]],
        on="promo_id", how="left",
    ).merge(products[["product_id", "category", "price"]], on="product_id", how="left").merge(
        order_totals[["order_id", "items_gross"]], on="order_id", how="left"
    )
    with_promo = merged["start_date"].notna()
    log.add(
        "order_items", "business_rule", "promo_active_on_order_date", "Ngày đặt nằm trong thời gian hiệu lực khuyến mãi",
        with_promo & ~merged["order_date"].between(merged["start_date"], merged["end_date"]), merged,
        columns=["order_id", "product_id", "promo_id", "order_date", "start_date", "end_date"],
        checked=int(with_promo.sum()), action="Khuyến mãi áp sai thời gian: gắn cờ, không tính vào hiệu quả khuyến mãi.",
    )
    log.add(
        "order_items", "business_rule", "promo_category_matches", "Danh mục sản phẩm khớp `applicable_category` của khuyến mãi",
        merged["applicable_category"].notna() & merged["applicable_category"].ne(merged["category"]), merged,
        columns=["order_id", "product_id", "promo_id", "category", "applicable_category"],
        checked=int(merged["applicable_category"].notna().sum()), action="Gắn cờ khuyến mãi áp sai danh mục.",
    )
    log.add(
        "order_items", "business_rule", "promo_min_order_value", "Giá trị đơn (trước giảm) ≥ `min_order_value` của khuyến mãi",
        with_promo & merged["items_gross"].lt(merged["min_order_value"]), merged,
        columns=["order_id", "product_id", "promo_id", "items_gross", "min_order_value"], severity=WARNING,
        checked=int(with_promo.sum()), action="Gắn cờ khuyến mãi áp không đủ điều kiện.",
    )
    price_ratio = merged["unit_price"] / merged["price"]
    log.add(
        "order_items", "business_rule", "unit_price_near_list_price", "Đơn giá bán trong khoảng 50%–120% giá niêm yết",
        merged["price"].notna() & ~price_ratio.between(0.5, 1.2), merged.assign(price_ratio=price_ratio),
        columns=["order_id", "product_id", "unit_price", "price", "price_ratio"], severity=WARNING,
        action="Giá lệch mạnh so với niêm yết: xác minh; dùng `unit_price` làm giá thực tế.",
    )
    extras["price_ratio"] = price_ratio.describe().to_dict()


def rules_payments(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Thanh toán: tiền = Σ dòng hàng sau giảm, phương thức khớp đơn, số kỳ trả góp."""
    payments, order_totals, order_info = d.payments, d.order_totals, d.order_info
    merged = payments.merge(order_totals, on="order_id", how="left").merge(
        order_info[["order_id", "payment_method", "order_status"]], on="order_id", how="left", suffixes=("", "_order")
    )
    merged["payment_gap"] = merged["payment_value"] - merged["items_net"]
    log.add(
        "payments", "business_rule", "payment_equals_items_net",
        "`payment_value` = Σ(`quantity` × `unit_price` − `discount_amount`) của đơn (sai số ≤ 1)",
        merged["items_net"].notna() & merged["payment_gap"].abs().gt(MONEY_TOLERANCE), merged,
        columns=["order_id", "payment_value", "items_net", "payment_gap"],
        action="Lệch tiền: dùng Σ order_items làm chuẩn doanh thu thuần.",
    )
    log.add(
        "payments", "business_rule", "payment_method_matches_order", "`payment_method` trùng `orders.payment_method`",
        merged["payment_method_order"].notna() & merged["payment_method"].ne(merged["payment_method_order"]), merged,
        columns=["order_id", "payment_method", "payment_method_order"],
        action="Lấy phương thức trong payments làm chuẩn.",
    )
    log.add(
        "payments", "business_rule", "installments_range", "`installments` trong 1–12; COD chỉ 1 kỳ",
        ~merged["installments"].between(1, 12) | (merged["payment_method"].eq("cod") & merged["installments"].ne(1)),
        merged, columns=["order_id", "payment_method", "installments"],
        action="Đặt về 1 kỳ với COD; ngoài 1–12 đặt NaN.",
    )


def rules_shipments(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Vận chuyển: ngày đặt ≤ ngày gửi ≤ ngày giao, trạng thái đơn, outlier thời gian giao/xử lý."""
    shipments, order_info = d.shipments, d.order_info
    merged = shipments.merge(order_info[["order_id", "order_date", "order_status"]], on="order_id", how="left")
    merged["shipping_days"] = (merged["delivery_date"] - merged["ship_date"]).dt.days
    merged["processing_days"] = (merged["ship_date"] - merged["order_date"]).dt.days
    log.add(
        "shipments", "business_rule", "ship_not_before_order", "`ship_date` ≥ `order_date`",
        merged["ship_date"].lt(merged["order_date"]), merged,
        columns=["order_id", "order_date", "ship_date"], action="Ngày gửi sai: đặt NaT, loại khỏi phân tích thời gian xử lý.",
    )
    log.add(
        "shipments", "business_rule", "delivery_not_before_ship", "`delivery_date` ≥ `ship_date`",
        merged["delivery_date"].lt(merged["ship_date"]), merged,
        columns=["order_id", "ship_date", "delivery_date"], action="Ngày giao sai: đặt NaT, loại khỏi phân tích thời gian giao.",
    )
    log.add(
        "shipments", "business_rule", "shipment_status_consistent", "Đơn có vận chuyển phải ở trạng thái shipped/delivered/returned",
        merged["order_status"].notna() & ~merged["order_status"].isin(["shipped", "delivered", "returned"]), merged,
        columns=["order_id", "order_status", "ship_date"], action="Xem `orders.unshipped_order_has_no_shipment`.",
    )
    for column in ["shipping_days", "processing_days"]:
        values = merged[column].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        upper = q3 + 1.5 * (q3 - q1)
        log.add(
            "shipments", "outlier", f"{column}__iqr_outlier", f"`{column}` ≤ rào IQR trên ({upper:.1f} ngày)",
            merged[column].gt(upper), merged, columns=["order_id", "order_date", "ship_date", "delivery_date", column],
            severity=WARNING, action="Gắn cờ giao chậm; không xóa.",
        )
        extras[column] = values.describe().to_dict()


def rules_returns(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Trả hàng: sản phẩm đã mua, số lượng trả ≤ mua, tiền hoàn ≤ giá trị dòng / tiền thanh toán, ngày trả."""
    payments, returns, line_totals, order_info, ship_info = d.payments, d.returns, d.line_totals, d.order_info, d.ship_info
    merged = returns.merge(line_totals, on=["order_id", "product_id"], how="left").merge(
        order_info[["order_id", "order_date", "order_status"]], on="order_id", how="left"
    ).merge(ship_info, on="order_id", how="left")
    log.add(
        "returns", "business_rule", "return_item_was_purchased", "(`order_id`, `product_id`) trả hàng có trong `order_items`",
        merged["purchased_quantity"].isna(), merged, columns=["return_id", "order_id", "product_id"],
        action="Trả sản phẩm không mua: loại khỏi phân tích trả hàng.",
    )
    returned_qty = merged.groupby(["order_id", "product_id"])["return_quantity"].transform("sum")
    log.add(
        "returns", "business_rule", "return_qty_not_exceed_purchased", "Tổng số lượng trả ≤ số lượng mua của dòng",
        returned_qty.gt(merged["purchased_quantity"]), merged.assign(total_returned=returned_qty),
        columns=["return_id", "order_id", "product_id", "return_quantity", "total_returned", "purchased_quantity"],
        action="Clip số lượng trả về số lượng mua.",
    )
    log.add(
        "returns", "business_rule", "refund_not_exceed_line_gross", "Tiền hoàn ≤ giá trị dòng trước giảm (`quantity` × `unit_price`)",
        merged["refund_amount"].gt(merged["line_gross"] + MONEY_TOLERANCE), merged,
        columns=["return_id", "order_id", "product_id", "refund_amount", "line_gross"],
        action="Clip tiền hoàn về giá trị dòng.",
    )
    log.add(
        "returns", "business_rule", "refund_not_exceed_line_net", "Tiền hoàn ≤ giá trị dòng sau giảm (khách thực trả)",
        merged["refund_amount"].gt(merged["line_net"] + MONEY_TOLERANCE), merged.assign(excess=merged["refund_amount"] - merged["line_net"]),
        columns=["return_id", "order_id", "product_id", "refund_amount", "line_net", "line_gross", "excess"], severity=WARNING,
        action="Hoàn theo giá trước giảm giá: khi tính doanh thu thuần, clip tiền hoàn về giá trị dòng sau giảm.",
    )
    refund_by_order = returns.groupby("order_id", as_index=False)["refund_amount"].sum().merge(
        payments[["order_id", "payment_value"]], on="order_id", how="left"
    )
    refund_by_order["excess_refund"] = refund_by_order["refund_amount"] - refund_by_order["payment_value"]
    log.add(
        "returns", "business_rule", "refund_not_exceed_payment", "Tổng tiền hoàn của đơn ≤ `payments.payment_value`",
        refund_by_order["excess_refund"].gt(MONEY_TOLERANCE), refund_by_order,
        action="Clip tổng hoàn về tiền thanh toán (giá trị ròng của đơn không âm).",
    )
    log.add(
        "returns", "business_rule", "return_after_order", "`return_date` ≥ `order_date`",
        merged["return_date"].lt(merged["order_date"]), merged,
        columns=["return_id", "order_id", "order_date", "return_date"], action="Ngày trả sai: đặt NaT.",
    )
    log.add(
        "returns", "business_rule", "return_after_delivery", "`return_date` ≥ `delivery_date`",
        merged["return_date"].lt(merged["delivery_date"]), merged,
        columns=["return_id", "order_id", "delivery_date", "return_date"], action="Ngày trả sai: đặt NaT.",
    )
    log.add(
        "returns", "business_rule", "return_order_status", "Đơn có trả hàng phải ở trạng thái `returned`",
        merged["order_status"].notna() & merged["order_status"].ne("returned"), merged,
        columns=["return_id", "order_id", "order_status"], severity=WARNING,
        action="Cập nhật trạng thái đơn thành `returned`.",
    )


def rules_reviews(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Đánh giá: sản phẩm đã mua, người đánh giá là người mua, ngày đánh giá sau ngày giao."""
    items, reviews, order_info, ship_info = d.items, d.reviews, d.order_info, d.ship_info
    merged = reviews.merge(order_info[["order_id", "order_date", "customer_id", "order_status"]], on="order_id",
                           how="left", suffixes=("", "_order")).merge(ship_info, on="order_id", how="left")
    review_keys = pd.MultiIndex.from_frame(reviews[["order_id", "product_id"]])
    item_keys = pd.MultiIndex.from_frame(items[["order_id", "product_id"]])
    log.add(
        "reviews", "business_rule", "review_item_was_purchased", "(`order_id`, `product_id`) đánh giá có trong `order_items`",
        pd.Series(~review_keys.isin(item_keys), index=reviews.index), reviews,
        action="Đánh giá sản phẩm không mua: loại.",
    )
    log.add(
        "reviews", "business_rule", "reviewer_is_buyer", "`customer_id` đánh giá trùng người đặt đơn",
        merged["customer_id_order"].notna() & merged["customer_id"].ne(merged["customer_id_order"]), merged,
        columns=["review_id", "order_id", "customer_id", "customer_id_order"], action="Lấy khách hàng của đơn làm chuẩn.",
    )
    log.add(
        "reviews", "business_rule", "review_after_delivery", "`review_date` ≥ `delivery_date` (và ≥ `order_date`)",
        merged["review_date"].lt(merged["delivery_date"]) | merged["review_date"].lt(merged["order_date"]), merged,
        columns=["review_id", "order_id", "order_date", "delivery_date", "review_date"], action="Ngày đánh giá sai: đặt NaT.",
    )
    log.add(
        "reviews", "business_rule", "review_order_status", "Chỉ đơn đã giao (`delivered`/`returned`) mới được đánh giá",
        merged["order_status"].notna() & ~merged["order_status"].isin(["delivered", "returned"]), merged,
        columns=["review_id", "order_id", "order_status"], severity=WARNING, action="Gắn cờ; loại khỏi phân tích hài lòng.",
    )


def rules_sales(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Doanh thu ngày: chuỗi liên tục, COGS ≤ Revenue, đối soát với order_items."""
    products, items, sales, order_info = d.products, d.items, d.sales, d.order_info
    full_range = pd.date_range(sales["Date"].min(), sales["Date"].max(), freq="D")
    missing_days = full_range.difference(sales["Date"])
    log.add(
        "sales", "business_rule", "daily_continuity", "Chuỗi ngày liên tục, không thiếu ngày",
        pd.Series(True, index=range(len(missing_days))), pd.DataFrame({"missing_date": missing_days}),
        checked=len(full_range), action="Thêm ngày thiếu với Revenue nội suy/0 tùy nguyên nhân trước khi dự báo.",
    )
    log.add(
        "sales", "business_rule", "cogs_not_exceed_revenue", "`COGS` ≤ `Revenue` (ngày không lỗ gộp)",
        sales["COGS"].gt(sales["Revenue"]), sales.assign(margin=sales["Revenue"] - sales["COGS"]), severity=WARNING,
        action="Có thể hợp lệ (ngày khuyến mãi sâu); giữ lại, gắn cờ khi phân tích biên lợi nhuận.",
    )
    daily = items.merge(order_info[["order_id", "order_date"]], on="order_id").merge(
        products[["product_id", "cogs"]].rename(columns={"cogs": "unit_cogs"}), on="product_id", how="left"
    )
    daily = daily.assign(line_cogs=daily["quantity"] * daily["unit_cogs"]).groupby("order_date").agg(
        items_gross=("gross_amount", "sum"), items_cogs=("line_cogs", "sum")
    )
    merged = sales.join(daily, on="Date")
    merged["revenue_gap"] = merged["Revenue"] - merged["items_gross"]
    log.add(
        "sales", "business_rule", "revenue_matches_order_items",
        "`Revenue` = Σ(`quantity` × `unit_price`) các đơn trong ngày (sai số ≤ 1)",
        merged["revenue_gap"].abs().gt(MONEY_TOLERANCE) | merged["items_gross"].isna(), merged,
        columns=["Date", "Revenue", "items_gross", "revenue_gap"], severity=WARNING,
        action="Dùng Σ order_items để đối soát; không trộn định nghĩa doanh thu trước/sau giảm giá.",
    )
    extras["cogs_gap"] = (merged["COGS"] - merged["items_cogs"]).describe().to_dict()


def rules_inventory(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Tồn kho: ngày chốt cuối tháng, year/month, công thức cờ và tỷ lệ, thuộc tính khớp products."""
    products, inventory = d.products, d.inventory
    log.add(
        "inventory", "business_rule", "snapshot_is_month_end", "`snapshot_date` là ngày cuối tháng",
        inventory["snapshot_date"].notna() & ~inventory["snapshot_date"].dt.is_month_end, inventory,
        action="Chuẩn hóa về ngày cuối tháng.",
    )
    log.add(
        "inventory", "business_rule", "year_month_match_snapshot", "`year`/`month` khớp `snapshot_date`",
        inventory["year"].ne(inventory["snapshot_date"].dt.year) | inventory["month"].ne(inventory["snapshot_date"].dt.month),
        inventory, action="Tính lại year/month từ snapshot_date.",
    )
    log.add(
        "inventory", "business_rule", "stockout_days_within_month", "`stockout_days` ≤ số ngày trong tháng",
        inventory["stockout_days"].gt(inventory["snapshot_date"].dt.days_in_month), inventory,
        action="Clip về số ngày của tháng.",
    )
    log.add(
        "inventory", "business_rule", "stockout_flag_consistent", "`stockout_flag` = 1 ⇔ `stockout_days` > 0",
        inventory["stockout_flag"].eq(1).ne(inventory["stockout_days"].gt(0)), inventory,
        action="Tính lại cờ từ stockout_days.",
    )
    expected_sell_through = inventory["units_sold"] / (inventory["units_sold"] + inventory["stock_on_hand"])
    log.add(
        "inventory", "business_rule", "sell_through_formula", "`sell_through_rate` = sold / (sold + stock_on_hand)",
        (inventory["sell_through_rate"] - expected_sell_through).abs().gt(0.001), inventory,
        action="Tính lại theo công thức.",
    )
    merged = inventory.merge(products[["product_id", "product_name", "category", "segment"]], on="product_id",
                             how="left", suffixes=("", "_product"))
    log.add(
        "inventory", "business_rule", "product_attributes_match", "Tên/danh mục/phân khúc khớp bảng `products`",
        merged["product_name_product"].notna() & (
            merged["product_name"].ne(merged["product_name_product"])
            | merged["category"].ne(merged["category_product"])
            | merged["segment"].ne(merged["segment_product"])
        ),
        merged, action="Lấy thuộc tính từ products làm chuẩn.",
    )
    log.add(
        "inventory", "business_rule", "reorder_flag_informative", "`reorder_flag` có biến thiên (không hằng số)",
        pd.Series(inventory["reorder_flag"].nunique() <= 1, index=[0]),
        pd.DataFrame({"reorder_flag_values": [inventory["reorder_flag"].unique().tolist()]}),
        severity=INFO, checked=1, action="Cột hằng số: loại khỏi mô hình/phân tích.",
    )


def rules_web_traffic(d: SimpleNamespace, log: QualityLog, extras: dict[str, object]) -> None:
    """Web traffic: chuỗi liên tục, visitors ≤ sessions ≤ page_views, bounce_rate hợp lý."""
    web = d.web
    full_range = pd.date_range(web["date"].min(), web["date"].max(), freq="D")
    missing_days = full_range.difference(web["date"])
    log.add(
        "web_traffic", "business_rule", "daily_continuity", "Chuỗi ngày liên tục, không thiếu ngày",
        pd.Series(True, index=range(len(missing_days))), pd.DataFrame({"missing_date": missing_days}),
        checked=len(full_range), action="Nội suy các ngày thiếu.",
    )
    log.add(
        "web_traffic", "business_rule", "visitors_not_exceed_sessions", "`unique_visitors` ≤ `sessions`",
        web["unique_visitors"].gt(web["sessions"]), web, action="Clip unique_visitors về sessions.",
    )
    log.add(
        "web_traffic", "business_rule", "page_views_not_below_sessions", "`page_views` ≥ `sessions`",
        web["page_views"].lt(web["sessions"]), web, action="Xác minh nguồn; gắn cờ.",
    )
    log.add(
        "web_traffic", "business_rule", "bounce_rate_plausible", "`bounce_rate` ≥ 1% (giá trị < 1% nghi lưu sai thang)",
        web["bounce_rate"].lt(0.01), web, severity=WARNING,
        action="Nhiều khả năng đơn vị là % chia thêm 100 → nhân 100 hoặc chỉ dùng so sánh tương đối.",
    )


BUSINESS_RULES = [
    rules_customers,
    rules_products,
    rules_promotions,
    rules_orders,
    rules_order_items,
    rules_payments,
    rules_shipments,
    rules_returns,
    rules_reviews,
    rules_sales,
    rules_inventory,
    rules_web_traffic,
]


def business_rules(t: dict[str, pd.DataFrame], log: QualityLog) -> dict[str, object]:
    """Chạy ràng buộc nghiệp vụ của mọi bảng. Trả về số liệu phụ cho báo cáo."""
    context = build_context(t)
    extras: dict[str, object] = {}
    for rule in BUSINESS_RULES:
        rule(context, log, extras)
    return extras


# ------------------------------------------------------------------- report


def fmt(value: object, digits: int = 2) -> str:
    if value is None or value is pd.NA or (isinstance(value, float) and np.isnan(value)):
        return "—"
    number = float(value)
    if number.is_integer():
        return f"{number:,.0f}"
    return f"{number:,.{digits}f}"


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_report(
    overview: pd.DataFrame,
    missing: pd.DataFrame,
    outliers: pd.DataFrame,
    checks: pd.DataFrame,
    extras: dict[str, object],
) -> None:
    issues = checks[checks["status"].eq("ISSUE")]
    lines = [
        "# Báo cáo chất lượng dữ liệu và EDA",
        "",
        "Tạo tự động bởi `eda/data_quality_eda.py` từ `data/raw/`. Mô tả ý nghĩa từng bảng: "
        "[`00_data_overview.md`](00_data_overview.md). Script chỉ phát hiện, **không sửa** dữ liệu gốc; "
        "dòng vi phạm của từng kiểm tra nằm tại `data/processed/eda/violations/<bảng>__<kiểm tra>.csv`.",
        "",
        "Mức độ: **ERROR** — vi phạm ràng buộc cứng, phải xử lý trước khi phân tích; "
        "**WARNING** — bất thường/nghi vấn, cần quyết định cách xử lý; **INFO** — đặc điểm dữ liệu cần biết.",
        "",
        "## 1. Tổng quan",
        "",
        f"- {len(overview)} bảng, {int(overview['rows'].sum()):,} dòng; {len(checks)} kiểm tra, "
        f"**{len(issues)}** có vi phạm "
        f"({int(issues['severity'].eq(ERROR).sum())} ERROR, {int(issues['severity'].eq(WARNING).sum())} WARNING, "
        f"{int(issues['severity'].eq(INFO).sum())} INFO).",
        "",
        "| Nhóm | Bảng | Số dòng | Số cột | Ô thiếu (%) | Dòng trùng | ERROR | WARNING | INFO |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in overview.iterrows():
        lines.append(
            f"| {row['group']} | `{row['table']}` | {row['rows']:,} | {row['columns']} | "
            f"{fmt(row['missing_pct'])}% | {row['duplicate_rows']:,} | {row['errors']} | {row['warnings']} | {row['infos']} |"
        )

    lines += [
        "",
        "## 2. Các vấn đề chính cần xử lý",
        "",
        "| Mức | Bảng | Kiểm tra | Vi phạm | % | Đề xuất xử lý |",
        "|---|---|---|---:|---:|---|",
    ]
    ranked = issues.assign(rank=issues["severity"].map(SEVERITY_ORDER)).sort_values(
        ["rank", "invalid_rows"], ascending=[True, False]
    )
    for _, row in ranked.iterrows():
        if row["category"] == "outlier":
            continue
        lines.append(
            f"| {row['severity']} | `{row['table']}` | {cell(row['description'])} | {row['invalid_rows']:,} | "
            f"{fmt(row['invalid_pct'])}% | {cell(row['action'])} |"
        )

    lines += ["", "## 3. Chi tiết theo bảng"]
    category_titles = {
        "missing": "Missing values",
        "duplicate": "Trùng lặp",
        "invalid": "Kiểu dữ liệu & miền giá trị",
        "referential": "Khóa ngoại",
        "business_rule": "Ràng buộc nghiệp vụ",
        "outlier": "Outlier theo ngữ cảnh",
    }
    for position, summary in enumerate(overview.to_dict("records"), start=1):
        name = summary["table"]
        lines += [
            "",
            f"### 3.{position}. `{name}` ({summary['group']})",
            "",
            f"{summary['rows']:,} dòng × {summary['columns']} cột · {summary['missing_cells']:,} ô thiếu "
            f"({fmt(summary['missing_pct'])}%) · {summary['duplicate_rows']:,} dòng trùng toàn bộ.",
        ]

        table_missing = missing[(missing["table"] == name) & (missing["missing_count"] > 0)]
        lines += ["", "**Missing values**", ""]
        if table_missing.empty:
            lines.append("Không có giá trị thiếu.")
        else:
            lines += ["| Cột | Thiếu | % | Loại | Xử lý |", "|---|---:|---:|---|---|"]
            for _, row in table_missing.iterrows():
                lines.append(
                    f"| `{row['column']}` | {row['missing_count']:,} | {fmt(row['missing_pct'])}% | "
                    f"{row['missing_type']} | {cell(row['treatment'])} |"
                )

        table_checks = checks[checks["table"] == name]
        lines += [
            "",
            "**Kiểm tra**",
            "",
            "| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |",
            "|---|---|---|---:|---:|---|",
        ]
        for category, title in category_titles.items():
            subset = table_checks[table_checks["category"] == category]
            if category in {"missing", "invalid"}:
                passed = subset[subset["status"] == "PASS"]
                subset = subset[subset["status"] == "ISSUE"]
                if not passed.empty:
                    scope = (
                        "cột bắt buộc đều có giá trị"
                        if category == "missing"
                        else "kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text"
                    )
                    lines.append(f"| {title} | {len(passed)} {scope} | — | — | 0 | ✅ PASS |")
            for _, row in subset.iterrows():
                status = "✅ PASS" if row["status"] == "PASS" else f"❌ {fmt(row['invalid_pct'])}%"
                lines.append(
                    f"| {title} | {cell(row['description'])} | {row['severity']} | {row['checked_rows']:,} | "
                    f"{row['invalid_rows']:,} | {status} |"
                )

        table_outliers = outliers[outliers["table"] == name]
        if not table_outliers.empty:
            lines += [
                "",
                "**Phân phối & outlier (IQR)**",
                "",
                "| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |",
                "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
            ]
            for _, row in table_outliers.iterrows():
                lines.append(
                    f"| `{row['column']}` | {fmt(row['min'])} | {fmt(row['q1'])} | {fmt(row['median'])} | {fmt(row['q3'])} | "
                    f"{fmt(row['max'])} | {fmt(row['skew'])} | [{fmt(row['iqr_lower'])}; {fmt(row['iqr_upper'])}] | "
                    f"{row['iqr_outliers']:,} ({fmt(row['iqr_outlier_pct'])}%) | {row['extreme_outliers_3iqr']:,} | "
                    f"{fmt(row['log_iqr_outliers'])} |"
                )

    lines += [
        "",
        "## 4. Nguyên tắc xử lý outlier",
        "",
        "- Outlier IQR chỉ được **gắn cờ**, không tự động xóa: các biến tiền/số lượng lệch phải mạnh (skew > 1), "
        "nên rào IQR trên thang gốc đánh dấu nhiều giá trị lớn hợp lệ. Cột *Outlier thang log* cho số outlier "
        "sau log-transform — gần 0 nghĩa là đuôi phải tự nhiên, không phải lỗi.",
        "- Với mô hình nhạy với outlier (K-Means, hồi quy tuyến tính): dùng log1p hoặc winsorize tại P1/P99; "
        "với mô hình cây: giữ nguyên.",
        "- Outlier ở bảng tổng hợp ngày (`sales`, `web_traffic`) thường là ngày khuyến mãi/lễ — giữ lại và tạo biến cờ sự kiện.",
        "- Giá trị vi phạm ràng buộc (âm, ngoài miền, sai thứ tự ngày) là **lỗi**, xử lý theo cột *Đề xuất xử lý* ở mục 2.",
    ]
    if "shipping_days" in extras:
        ship = extras["shipping_days"]
        lines.append(
            f"- Thời gian giao (`delivery_date − ship_date`): {fmt(ship['min'])}–{fmt(ship['max'])} ngày, "
            f"trung vị {fmt(ship['50%'])} ngày."
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------- main


def main() -> None:
    for directory in (OUTPUT_DIR, VIOLATION_DIR, PLOT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    for stale in [*VIOLATION_DIR.glob("*.csv"), *PLOT_DIR.glob("*.png")]:
        stale.unlink()

    log = QualityLog()
    tables = load_tables(log)
    missing_rows: list[dict[str, object]] = []
    outlier_rows: list[dict[str, object]] = []
    for name, frame in tables.items():
        print(f"Kiểm tra {name}: {len(frame):,} dòng × {len(frame.columns)} cột")
        missing_rows += check_missing(name, frame, log)
        check_duplicates(name, frame, log)
        check_values(name, frame, log)
        outlier_rows += profile_outliers(name, frame)
    check_foreign_keys(tables, log)
    extras = business_rules(tables, log) if set(TABLES) <= set(tables) else {}

    checks = pd.DataFrame(log.checks)
    missing = pd.DataFrame(missing_rows)
    outliers = pd.DataFrame(outlier_rows)
    issues = checks[checks["status"].eq("ISSUE")]
    overview = pd.DataFrame(
        [
            {
                "group": TABLES[name]["group"],
                "table": name,
                "rows": len(frame),
                "columns": len(frame.columns),
                "missing_cells": int(frame.isna().sum().sum()),
                "missing_pct": frame.isna().sum().sum() / frame.size * 100 if frame.size else 0.0,
                "duplicate_rows": int(frame.duplicated().sum()),
                "errors": int((issues["table"].eq(name) & issues["severity"].eq(ERROR)).sum()),
                "warnings": int((issues["table"].eq(name) & issues["severity"].eq(WARNING)).sum()),
                "infos": int((issues["table"].eq(name) & issues["severity"].eq(INFO)).sum()),
            }
            for name, frame in tables.items()
        ]
    )

    checks.to_csv(OUTPUT_DIR / "data_quality_checks.csv", index=False)
    missing.to_csv(OUTPUT_DIR / "missing_values.csv", index=False)
    outliers.to_csv(OUTPUT_DIR / "outliers.csv", index=False)
    overview.to_csv(OUTPUT_DIR / "table_overview.csv", index=False)
    write_report(overview, missing, outliers, checks, extras)

    print(
        f"\n{len(checks)} kiểm tra, {len(issues)} có vi phạm "
        f"({int(issues['severity'].eq(ERROR).sum())} ERROR, {int(issues['severity'].eq(WARNING).sum())} WARNING)."
    )
    for _, row in issues.sort_values("severity").iterrows():
        if row["category"] != "outlier":
            print(f"  [{row['severity']}] {row['table']}.{row['check']}: {row['invalid_rows']:,}")
    print(f"Kết quả: {OUTPUT_DIR}\nBáo cáo: {REPORT_PATH}")


if __name__ == "__main__":
    main()
