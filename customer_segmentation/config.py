"""Đường dẫn và tham số dùng chung cho các bước customer segmentation.

Mỗi bước đọc đầu vào và ghi đầu ra qua các hằng số ở đây, nên chỉ cần sửa một chỗ
khi đổi vị trí file hoặc định nghĩa RFM.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "customer_segmentation"
PLOT_DIR = OUTPUT_DIR / "plots"
REPORT_DIR = ROOT / "reports"

# Bước 1 — aggregation
CUSTOMER_BASE_PATH = OUTPUT_DIR / "customer_analysis_base.csv"
REFUND_ISSUES_PATH = OUTPUT_DIR / "refund_reconciliation_issues.csv"
# Bước 2 — log + scale
FEATURES_PATH = OUTPUT_DIR / "customer_features_transformed.csv"
FEATURES_METADATA_PATH = OUTPUT_DIR / "customer_transform_metadata.json"
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
PENDING_STATUSES = {"created"}

# Rule-based segmentation cho khách CHƯA có đơn phát sinh doanh thu (không đưa vào K-Means).
# Xét theo thứ tự: có đơn doanh thu → K-Means; còn lại gán nhóm đầu tiên thỏa điều kiện.
RULE_SEGMENTS = {
    "RB3": "Có đơn mới tạo, chưa thanh toán",  # có đơn created
    "RB2": "Chỉ có đơn bị hủy",              # mọi đơn đều cancelled
    "RB1": "Chưa từng đặt đơn",              # đăng ký nhưng không có đơn nào
}
RFM_FEATURES = ["recency_days", "frequency", "monetary"]
DEMOGRAPHIC_COLUMNS = ["gender", "age_group", "region", "acquisition_channel"]
RANDOM_STATE = 42


def require_file(path: Path, producer: str) -> None:
    """Báo lỗi rõ ràng khi bước trước chưa chạy."""
    if not path.is_file():
        raise FileNotFoundError(f"{path} not found. Run customer_segmentation/{producer} first.")
