"""Đường dẫn và tham số dùng chung cho các bước customer segmentation.

Mỗi bước đọc đầu vào và ghi đầu ra qua các hằng số ở đây, nên chỉ cần sửa một chỗ
khi đổi vị trí file hoặc định nghĩa RFM.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "customer_segmentation"
PLOT_DIR = OUTPUT_DIR / "plots"
REPORT_DIR = ROOT / "reports" / "markdown"
# Đường dẫn ảnh tương đối từ file Markdown báo cáo tới thư mục biểu đồ.
PLOT_LINK = Path(os.path.relpath(PLOT_DIR, REPORT_DIR)).as_posix()

# Bước 1 — aggregation
CUSTOMER_BASE_PATH = OUTPUT_DIR / "customer_analysis_base.csv"
REFUND_ISSUES_PATH = OUTPUT_DIR / "refund_reconciliation_issues.csv"
# Bước 2 — log + scale
FEATURES_PATH = OUTPUT_DIR / "customer_features_transformed.csv"
FEATURES_METADATA_PATH = OUTPUT_DIR / "customer_transform_metadata.json"
FEATURES_REPORT_PATH = REPORT_DIR / "customer_segmentation_features.md"
# Bước 3 — PCA
PCA_SCORES_PATH = OUTPUT_DIR / "customer_pca_scores.csv"
PCA_REPORT_PATH = REPORT_DIR / "customer_segmentation_pca.md"
# Bước 4 — chọn k (chỉ đánh giá, không ghi nhãn)
K_SELECTION_DIR = OUTPUT_DIR / "k_selection"
K_SELECTION_REPORT_PATH = REPORT_DIR / "customer_segmentation_k_selection.md"
# Bước 5 — K-Means (đầu ra bắt buộc: customer_id, cluster)
SEGMENTS_PATH = OUTPUT_DIR / "customer_segments.csv"
CLUSTER_EVALUATION_PATH = OUTPUT_DIR / "customer_cluster_evaluation.csv"
# Bước 6 — profiling
PROFILE_DIR = OUTPUT_DIR / "profiles"
PROFILE_REPORT_PATH = REPORT_DIR / "customer_segment_profiles.md"
ALL_SEGMENTS_PATH = OUTPUT_DIR / "customer_segments_all.csv"  # rule-based + K-Means cho toàn bộ khách

# Định nghĩa RFM
# Business rule: đơn đã thanh toán trở đi (paid → shipped → delivered/returned) được tính doanh thu.
# Không tính: created (chưa thanh toán) và cancelled (đã hủy). Đơn returned tính doanh thu trừ tiền hoàn.
REVENUE_STATUSES = {"paid", "shipped", "delivered", "returned"}
FAILED_STATUSES = {"cancelled": "cancelled", "created": "abandoned"}  # trạng thái → lý do không chuyển đổi

# Rule-based segmentation cho khách KHÔNG có đơn phát sinh doanh thu (không đưa vào K-Means vì F = M = 0).
#   có ≥ 1 đơn doanh thu                  → K-Means
#   có ≥ 1 đơn, tất cả cancelled/created  → RB2 (kèm failed_order_count, failed_reason)
#   chưa đặt đơn nào                      → RB1
RULE_SEGMENTS = {
    "RB2": "Đặt đơn nhưng chưa chuyển đổi",
    "RB1": "Chưa giao dịch",
}
RFM_FEATURES = ["recency_days", "frequency", "monetary"]
# Phép biến đổi phân phối cho từng biến trước khi scale: "none" | "log1p" | "sqrt" | "yeo-johnson".
# Báo cáo feature engineering (bước 02) so sánh độ lệch (skew) của từng lựa chọn để chọn.
FEATURE_TRANSFORMS = {"recency_days": "log1p", "frequency": "log1p", "monetary": "log1p"}
DEMOGRAPHIC_COLUMNS = ["gender", "age_group", "region", "acquisition_channel"]
RANDOM_STATE = 42


def require_file(path: Path, producer: str) -> None:
    """Báo lỗi rõ ràng khi bước trước chưa chạy."""
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found. Run customer_segmentation/{producer} first.")
