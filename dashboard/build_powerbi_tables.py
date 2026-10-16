"""Gộp các file CSV gốc thành các bảng import vào Power BI.

Mỗi file đầu ra giữ đúng một grain (1 dòng là gì), không gộp tất cả thành một bảng phẳng: gộp đơn với
dòng hàng sẽ nhân phí ship / tiền thanh toán theo số dòng. Quan hệ, bảng ngày và measure DAX làm trong Power BI.

Đầu vào : data/raw/*.csv, data/processed/customer_segmentation/customer_segments_all.csv (phân khúc, nếu có)
Đầu ra  : data/processed/powerbi/*.csv
Chạy    : python dashboard/build_powerbi_tables.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "powerbi"
SEGMENTS_PATH = ROOT / "data" / "processed" / "customer_segmentation" / "customer_segments_all.csv"

# Đơn tạo ra doanh thu: đã thanh toán trở đi. `created` (bỏ dở) và `cancelled` (đã hủy) không có doanh thu.
REVENUE_STATUSES = ("paid", "shipped", "delivered", "returned")
RAW_TABLES = ["customers", "geography", "products", "promotions", "orders", "order_items", "payments",
              "shipments", "returns", "reviews", "inventory", "web_traffic"]

STATUS_LIST = ", ".join(f"'{s}'" for s in REVENUE_STATUSES)

# Mỗi bảng: tên file đầu ra → câu SQL. Thứ tự giữ nguyên khi xuất.
TABLES = {
    # --- Bảng tra cứu (dimension) ---
    "customers": """
        SELECT c.customer_id, c.gender, c.age_group, c.acquisition_channel, c.signup_date,
               c.zip, c.city, g.district, g.region,
               COALESCE(s.segment, 'Unknown') AS segment, COALESCE(s.segment_name, 'Unknown') AS segment_name
        FROM customers c
        LEFT JOIN geography g USING (zip)
        LEFT JOIN segments s USING (customer_id)
    """,
    "products": "SELECT product_id, product_name, category, segment, size, color, price, cogs FROM products",
    "promotions": """
        SELECT promo_id, promo_name, promo_type, discount_value, start_date, end_date,
               COALESCE(applicable_category, 'ALL') AS applicable_category, promo_channel, stackable_flag,
               min_order_value
        FROM promotions
    """,
    "geography": "SELECT zip, city, district, region FROM geography",

    # --- Bảng dữ liệu (fact) ---
    # 1 dòng = 1 sản phẩm trong 1 đơn có doanh thu.
    "sales_lines": f"""
        SELECT i.order_id, i.product_id, o.order_date, o.customer_id, o.zip, o.order_status,
               o.payment_method, o.device_type, o.order_source,
               i.promo_id, i.promo_id_2, p.promo_type, i.promo_id IS NOT NULL AS has_promotion,
               i.quantity, i.unit_price,
               ROUND(i.quantity * i.unit_price, 2) AS gross_amount,
               i.discount_amount,
               ROUND(i.quantity * i.unit_price - i.discount_amount, 2) AS net_revenue,
               ROUND(i.quantity * pr.cogs, 2) AS cost,
               ROUND(i.quantity * i.unit_price - i.discount_amount - i.quantity * pr.cogs, 2) AS gross_profit
        FROM order_items i
        JOIN orders o USING (order_id)
        JOIN products pr USING (product_id)
        LEFT JOIN promotions p ON p.promo_id = i.promo_id
        WHERE o.order_status IN ({STATUS_LIST})
    """,
    # 1 dòng = 1 đơn, mọi trạng thái (để tính tỷ lệ hủy), kèm thanh toán và vận chuyển.
    "orders": f"""
        WITH items AS (
            SELECT order_id, COUNT(*) AS line_count, SUM(quantity) AS units,
                   ROUND(SUM(quantity * unit_price), 2) AS gross_amount, ROUND(SUM(discount_amount), 2) AS discount_amount
            FROM order_items GROUP BY order_id
        ), refunds AS (
            SELECT order_id, SUM(refund_amount) AS refund_raw FROM returns GROUP BY order_id
        )
        SELECT o.order_id, o.order_date, o.customer_id, o.zip, o.order_status, o.payment_method,
               o.device_type, o.order_source,
               o.order_status IN ({STATUS_LIST}) AS is_revenue_order,
               o.order_status = 'cancelled' AS is_cancelled,
               it.line_count, it.units, it.gross_amount, it.discount_amount,
               pay.payment_value, pay.installments,
               s.ship_date, s.delivery_date, s.shipping_fee,
               s.order_id IS NOT NULL AS has_shipment,
               DATE_DIFF('day', o.order_date, s.ship_date) AS days_to_ship,
               DATE_DIFF('day', o.order_date, s.delivery_date) AS days_to_deliver,
               r.order_id IS NOT NULL AS has_return,
               ROUND(LEAST(COALESCE(r.refund_raw, 0), pay.payment_value), 2) AS refund_amount
        FROM orders o
        LEFT JOIN items it USING (order_id)
        LEFT JOIN payments pay USING (order_id)
        LEFT JOIN shipments s USING (order_id)
        LEFT JOIN refunds r USING (order_id)
    """,
    # 1 dòng = 1 lần trả 1 sản phẩm; tiền hoàn chia tỷ lệ để tổng mỗi đơn không vượt tiền đã trả.
    "returns": """
        WITH order_refund AS (
            SELECT order_id, SUM(refund_amount) AS refund_raw FROM returns GROUP BY order_id
        )
        SELECT r.return_id, r.order_id, r.product_id, o.customer_id, o.zip, o.order_date, r.return_date,
               DATE_DIFF('day', o.order_date, r.return_date) AS days_to_return,
               r.return_reason, r.return_quantity, r.refund_amount AS refund_amount_raw,
               ROUND(r.refund_amount * LEAST(1, pay.payment_value / NULLIF(t.refund_raw, 0)), 2) AS refund_amount
        FROM returns r
        JOIN orders o USING (order_id)
        JOIN payments pay USING (order_id)
        JOIN order_refund t USING (order_id)
    """,
    "reviews": "SELECT review_id, order_id, product_id, customer_id, review_date, rating, review_title FROM reviews",
    # Bỏ tên/danh mục/phân khúc (đã có trong products) và reorder_flag (hằng số 0).
    "inventory": """
        SELECT snapshot_date, product_id, stock_on_hand, units_received, units_sold, stockout_days,
               days_of_supply, fill_rate, stockout_flag, overstock_flag, sell_through_rate
        FROM inventory
    """,
    "web_traffic": """
        SELECT date, sessions, unique_visitors, page_views, bounce_rate, avg_session_duration_sec, traffic_source
        FROM web_traffic
    """,
}

# Khóa chính của từng bảng (kiểm tra không trùng) và khóa ngoại tới bảng tra cứu (kiểm tra đều tìm thấy).
PRIMARY_KEYS = {
    "customers": ["customer_id"], "products": ["product_id"], "promotions": ["promo_id"], "geography": ["zip"],
    "orders": ["order_id"], "returns": ["return_id"], "reviews": ["review_id"],
    "inventory": ["product_id", "snapshot_date"], "web_traffic": ["date"],
}
FOREIGN_KEYS = [
    ("sales_lines", "customer_id", "customers"), ("sales_lines", "product_id", "products"),
    ("sales_lines", "promo_id", "promotions"), ("sales_lines", "zip", "geography"),
    ("orders", "customer_id", "customers"), ("orders", "zip", "geography"),
    ("returns", "customer_id", "customers"), ("returns", "product_id", "products"), ("returns", "zip", "geography"),
    ("reviews", "customer_id", "customers"), ("reviews", "product_id", "products"),
    ("inventory", "product_id", "products"), ("customers", "zip", "geography"),
]
KEY_COLUMNS = {"customers": "customer_id", "products": "product_id", "promotions": "promo_id", "geography": "zip"}


def load_raw(con: duckdb.DuckDBPyConnection) -> None:
    for name in RAW_TABLES:
        path = RAW_DIR / f"{name}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Thiếu {path}")
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_csv_auto('{path.as_posix()}', header=true)")
    if SEGMENTS_PATH.is_file():
        con.execute(f"CREATE VIEW segments AS SELECT customer_id, segment, segment_name "
                    f"FROM read_csv_auto('{SEGMENTS_PATH.as_posix()}', header=true)")
    else:
        print(f"Chưa có {SEGMENTS_PATH.name}: cột segment để 'Unknown' (chạy customer_segmentation trước).")
        con.execute("CREATE VIEW segments AS SELECT NULL::BIGINT AS customer_id, NULL AS segment, NULL AS segment_name "
                    "WHERE false")


def check(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Kiểm tra trước khi xuất; trả về danh sách lỗi (rỗng = đạt)."""
    problems = []
    for table, keys in PRIMARY_KEYS.items():
        key = ", ".join(keys)
        duplicates = con.execute(f"SELECT COUNT(*) FROM (SELECT {key} FROM out_{table} GROUP BY {key} "
                                 f"HAVING COUNT(*) > 1)").fetchone()[0]
        if duplicates:
            problems.append(f"{table}: {duplicates:,} khóa ({key}) bị trùng")
    for table, column, target in FOREIGN_KEYS:
        missing = con.execute(
            f"SELECT COUNT(*) FROM out_{table} t WHERE t.{column} IS NOT NULL AND NOT EXISTS "
            f"(SELECT 1 FROM out_{target} d WHERE d.{KEY_COLUMNS[target]} = t.{column})"
        ).fetchone()[0]
        if missing:
            problems.append(f"{table}.{column}: {missing:,} giá trị không có trong {target}")
    for table, source in [("orders", "orders"), ("returns", "returns"), ("reviews", "reviews"),
                          ("inventory", "inventory"), ("web_traffic", "web_traffic"), ("customers", "customers")]:
        out_rows, src_rows = (con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                              for name in (f"out_{table}", source))
        if out_rows != src_rows:
            problems.append(f"{table}: {out_rows:,} dòng, nguồn có {src_rows:,}")
    # Doanh thu dòng hàng (sau giảm giá) phải khớp tiền thanh toán của cùng các đơn.
    lines, paid = con.execute(f"""
        SELECT (SELECT SUM(net_revenue) FROM out_sales_lines),
               (SELECT SUM(payment_value) FROM out_orders WHERE is_revenue_order)
    """).fetchone()
    if abs(lines - paid) > max(1.0, paid * 1e-6):
        problems.append(f"Doanh thu dòng hàng {lines:,.0f} lệch tiền thanh toán {paid:,.0f}")
    return problems


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    load_raw(con)
    for name, sql in TABLES.items():
        con.execute(f"CREATE TABLE out_{name} AS {sql}")

    problems = check(con)
    if problems:
        raise SystemExit("Kiểm tra không đạt:\n  - " + "\n  - ".join(problems))

    for name in TABLES:
        path = OUTPUT_DIR / f"{name}.csv"
        con.execute(f"COPY out_{name} TO '{path.as_posix()}' (HEADER, DELIMITER ',')")
        rows, columns = con.execute(f"SELECT COUNT(*), (SELECT COUNT(*) FROM (DESCRIBE out_{name})) "
                                    f"FROM out_{name}").fetchone()
        print(f"{name + '.csv':<18} {rows:>9,} dòng × {columns:>2} cột")

    revenue_orders, cancelled = con.execute(
        "SELECT COUNT(*) FILTER (WHERE is_revenue_order), COUNT(*) FILTER (WHERE NOT is_revenue_order) FROM out_orders"
    ).fetchone()
    print(f"\nĐơn có doanh thu: {revenue_orders:,} · đơn created/cancelled (chỉ dùng cho tỷ lệ hủy): {cancelled:,}")
    print(f"Kiểm tra: đạt. Kết quả: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
