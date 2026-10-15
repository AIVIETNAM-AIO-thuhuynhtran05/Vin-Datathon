"""Đặt tên gợi ý và hành động cho cụm theo R/F/M — dùng chung cho bước chọn k và bước profiling.

Đầu vào là "rank index": phân vị trung bình (0–100) của khách trong cụm − 50, cho từng biến RFM.
Tên đặt theo ma trận Recency × Giá trị (giá trị = trung bình phân vị F và M):

                    Giá trị cao                Giá trị thấp
    Mua gần đây     Champions → Trung thành    Khách mới / tiềm năng → Cần nuôi dưỡng
    Lâu chưa mua    Có nguy cơ rời bỏ          Ngủ đông → Đã rời bỏ

Hai cụm rơi cùng ô: cụm điểm cao hơn giữ tên, cụm sau lùi sang tên kế tiếp (mũi tên).
Tên chỉ là gợi ý để đọc kết quả nhanh; tên chính thức do người phân tích đặt sau khi xem profile.
"""

from __future__ import annotations

import pandas as pd

RFM_COLUMNS = ["recency_days", "frequency", "monetary"]

# Thứ tự hiển thị (từ giá trị cao → thấp); mỗi tên gắn một màu cố định trong biểu đồ.
NAME_ORDER = [
    "Champions",
    "Trung thành",
    "Khách mới / tiềm năng",
    "Cần nuôi dưỡng",
    "Có nguy cơ rời bỏ",
    "Ngủ đông",
    "Đã rời bỏ",
]
NAME_FALLBACK = {
    "Champions": "Trung thành",
    "Khách mới / tiềm năng": "Cần nuôi dưỡng",
    "Có nguy cơ rời bỏ": "Ngủ đông",
    "Ngủ đông": "Đã rời bỏ",
}
# Tên → (mục tiêu, hành động gợi ý, KPI)
SEGMENT_PLAYBOOK = {
    "Champions": ("Giữ chân và tăng giá trị",
                  "Chương trình VIP/early access, upsell sản phẩm premium, hạn chế giảm giá sâu.", "Retention, AOV"),
    "Trung thành": ("Tăng tần suất mua",
                    "Tích điểm theo bậc, cross-sell theo danh mục ưa thích, nhắc mua định kỳ.", "Frequency, doanh thu/khách"),
    "Khách mới / tiềm năng": ("Tạo thói quen mua lặp lại",
                              "Voucher đơn kế tiếp trong 30 ngày, email onboarding, gợi ý sản phẩm bán chạy.",
                              "Tỷ lệ mua lần tiếp theo"),
    "Cần nuôi dưỡng": ("Nâng giá trị đơn",
                       "Bundle/khuyến mãi theo ngưỡng giá trị đơn để tăng AOV và tần suất.", "AOV, Frequency"),
    "Có nguy cơ rời bỏ": ("Kéo quay lại trước khi mất",
                          "Win-back cá nhân hóa, ưu đãi có hạn theo danh mục từng mua nhiều.", "Reactivation rate"),
    "Ngủ đông": ("Đánh thức với chi phí thấp",
                 "Remarketing/email theo mùa, ưu đãi nhỏ; đo phản hồi trước khi đầu tư thêm.", "Reactivation rate"),
    "Đã rời bỏ": ("Tối ưu chi phí tiếp cận",
                  "Chỉ dùng kênh chi phí gần 0 (email định kỳ); không đầu tư ưu đãi lớn.", "Chi phí/đơn kéo về"),
}


def rfm_rank_index(rfm: pd.DataFrame, labels: pd.Series) -> pd.DataFrame:
    """Phân vị trung bình của mỗi cụm trừ 50 (dương = cao hơn mặt bằng)."""
    ranks = rfm[RFM_COLUMNS].rank(pct=True) * 100
    return ranks.groupby(labels.to_numpy()).mean() - 50


def base_name(name: str) -> str:
    """Bỏ hậu tố '(2)', '(3)' của tên trùng."""
    return name.split(" (")[0]


def suggest_name(r_good: float, value: float) -> str:
    """r_good, value: chỉ số (−50…+50); r_good > 0 = mua gần đây hơn mặt bằng, value > 0 = F/M cao hơn."""
    if r_good >= 0:
        return "Champions" if value >= 0 else "Khách mới / tiềm năng"
    return "Có nguy cơ rời bỏ" if value >= 0 else "Ngủ đông"


def name_clusters(index: pd.DataFrame) -> dict[int, str]:
    """Tên gợi ý không trùng cho từng cụm, từ rank index của recency_days, frequency, monetary."""
    r_good = -index["recency_days"]
    value = (index["frequency"] + index["monetary"]) / 2
    names: dict[int, str] = {}
    for cluster in (r_good + value).sort_values(ascending=False).index:
        name = suggest_name(r_good[cluster], value[cluster])
        while name in names.values() and name in NAME_FALLBACK:
            name = NAME_FALLBACK[name]
        base, copy = name, 2
        while name in names.values():
            name, copy = f"{base} ({copy})", copy + 1
        names[cluster] = name
    return dict(sorted(names.items()))
