"""Bước 2/6 — Feature engineering: biến đổi phân phối + chuẩn hóa RFM, kèm báo cáo lý do chọn biến.

1. Biến cho K-Means: recency_days, frequency, monetary (định nghĩa ở bước 01).
2. Biến đổi phân phối theo config.FEATURE_TRANSFORMS (none / log1p / sqrt / yeo-johnson);
   báo cáo so sánh độ lệch (skew) của từng lựa chọn để chọn phép biến đổi phù hợp từng biến.
3. StandardScaler đưa các biến về cùng thang (K-Means dùng khoảng cách Euclid).
4. Đánh giá biến hành vi ứng viên (AOV, tenure, tỷ lệ trả/hủy, khuyến mãi, đánh giá): tương quan
   Spearman với RFM để biết biến nào trùng thông tin, biến nào mang thông tin mới.

Đầu vào : data/processed/customer_segmentation/customer_analysis_base.csv, data/raw/*.csv
Đầu ra  : customer_features_transformed.csv, customer_transform_metadata.json,
          feature_engineering/*.csv, plots/fe_*.png, reports/markdown/customer_segmentation_features.md
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.preprocessing import PowerTransformer, StandardScaler

from behavior_features import METRICS, build_behavior_features
from config import (
    CUSTOMER_BASE_PATH,
    FEATURE_TRANSFORMS,
    FEATURES_METADATA_PATH,
    FEATURES_PATH,
    FEATURES_REPORT_PATH,
    OUTPUT_DIR,
    PLOT_DIR,
    PLOT_LINK,
    REVENUE_STATUSES,
    RFM_FEATURES,
    ROOT,
    require_file,
)
from plot_style import DIVERGING, annotate_heatmap, apply_style

FE_DIR = OUTPUT_DIR / "feature_engineering"
TRANSFORM_OPTIONS = ["none", "sqrt", "log1p", "yeo-johnson"]  # thứ tự từ đơn giản → phức tạp
REDUNDANT_THRESHOLD = 0.7
CANDIDATES = ["aov", "items_per_order", "tenure_days", "promo_share", "return_rate", "cancel_rate", "avg_rating"]
DEFINITIONS = {
    "recency_days": "Số ngày từ đơn doanh thu gần nhất đến ngày tham chiếu (ngày đặt cuối cùng trong dữ liệu + 1)",
    "frequency": "Số đơn phát sinh doanh thu (`paid`/`shipped`/`delivered`/`returned`)",
    "monetary": "Σ(`payment_value` − tiền hoàn của đơn), mỗi đơn chặn dưới ở 0",
    "aov": "Monetary / Frequency",
    "items_per_order": "Tổng số sản phẩm / số đơn doanh thu",
    "tenure_days": "Số ngày từ đơn doanh thu đầu tiên đến ngày tham chiếu",
    "promo_share": "Tỷ lệ dòng hàng có mã khuyến mãi",
    "return_rate": "Tỷ lệ đơn bị trả trên số đơn doanh thu",
    "cancel_rate": "Tỷ lệ đơn hủy trên mọi đơn đã đặt",
    "avg_rating": "Điểm đánh giá trung bình (chỉ khách có đánh giá)",
}


def apply_transform(values: pd.Series, method: str) -> np.ndarray:
    data = values.astype(float).to_numpy()
    if method == "none":
        return data
    if method == "log1p":
        return np.log1p(data)
    if method == "sqrt":
        return np.sqrt(data)
    if method == "yeo-johnson":
        return PowerTransformer(method="yeo-johnson", standardize=False).fit_transform(data.reshape(-1, 1)).ravel()
    raise ValueError(f"Unknown transform: {method}")


def compare_transforms(rfm: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in RFM_FEATURES:
        skews = {method: float(pd.Series(apply_transform(rfm[column], method)).skew()) for method in TRANSFORM_OPTIONS}
        # Chọn phép đơn giản nhất mà |skew| không kém lựa chọn tốt nhất quá 0,1.
        best = min(abs(value) for value in skews.values())
        recommended = next(method for method in TRANSFORM_OPTIONS if abs(skews[method]) <= best + 0.1)
        rows.append({"feature": column, **{f"skew_{m}": skews[m] for m in TRANSFORM_OPTIONS},
                     "configured": FEATURE_TRANSFORMS[column], "recommended": recommended})
    return pd.DataFrame(rows)


def assess_candidates(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    correlation = features[[*RFM_FEATURES, *CANDIDATES]].corr(method="spearman").loc[CANDIDATES, RFM_FEATURES]
    rows = []
    for candidate in CANDIDATES:
        values = features[candidate]
        strongest = correlation.loc[candidate].abs().idxmax()
        rho = float(correlation.loc[candidate, strongest])
        if abs(rho) >= REDUNDANT_THRESHOLD:
            decision = f"Trùng thông tin với {strongest} (ρ = {rho:+.2f}) → không đưa vào K-Means; dùng để mô tả cụm"
        else:
            decision = "Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️"
        rows.append({"feature": candidate, "coverage_pct": values.notna().mean() * 100, "median": values.median(),
                     "skew": values.skew(), "strongest_rfm": strongest, "spearman_rho": rho, "decision": decision})
    return pd.DataFrame(rows), correlation


def plot_distributions(rfm: pd.DataFrame, transformed: pd.DataFrame) -> None:
    figure, axes = plt.subplots(len(RFM_FEATURES), 2, figsize=(10, 2.6 * len(RFM_FEATURES)))
    for row, column in enumerate(RFM_FEATURES):
        for col, (data, label) in enumerate([(rfm[column], "gốc"), (transformed[column], FEATURE_TRANSFORMS[column])]):
            axis = axes[row, col]
            axis.hist(data, bins=50, color="#2a78d6" if col == 0 else "#1baf7a", edgecolor="white", linewidth=0.3)
            axis.set_title(f"{METRICS[column]} — {label} (skew {pd.Series(data).skew():+.2f})", loc="left", fontsize=9)
            axis.set_ylabel("Số khách")
    figure.suptitle("Phân phối RFM trước và sau biến đổi", x=0.01, ha="left", fontweight="bold")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "fe_distributions.png", dpi=110)
    plt.close(figure)


def plot_candidate_correlation(correlation: pd.DataFrame) -> None:
    values = correlation.to_numpy()
    figure, axis = plt.subplots(figsize=(6.4, 0.5 * len(correlation) + 1.6))
    image = axis.imshow(values, cmap=DIVERGING, vmin=-1, vmax=1, aspect="auto")
    axis.set_xticks(range(values.shape[1]), [METRICS[c].split(" (")[0] for c in correlation.columns])
    axis.set_yticks(range(len(correlation)), [METRICS[c] for c in correlation.index])
    axis.grid(False)
    annotate_heatmap(axis, values, [[f"{v:+.2f}" for v in row] for row in values], threshold=0.6)
    axis.set_title("Tương quan Spearman: biến ứng viên × RFM", loc="left")
    figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "fe_candidate_correlation.png", dpi=110)
    plt.close(figure)


def write_report(rfm: pd.DataFrame, comparison: pd.DataFrame, scaler: StandardScaler, transformed: pd.DataFrame,
                 candidates: pd.DataFrame, excluded: int) -> None:
    zero_monetary = int(rfm["monetary"].eq(0).sum())
    lines = [
        "# Feature engineering cho phân cụm khách hàng",
        "",
        "Tạo tự động bởi `customer_segmentation/02_transform_features.py`.",
        "",
        "## 1. Biến đưa vào K-Means: RFM",
        "",
        f"Áp dụng cho **{len(rfm):,} khách có đơn phát sinh doanh thu**. {excluded:,} khách không có đơn doanh thu "
        "được gán nhóm rule-based ở bước 01, không đưa vào K-Means.",
        "",
        "| Biến | Định nghĩa | Chiều tốt | Min | Median | Mean | Max | Skew |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    better = {"recency_days": "Thấp", "frequency": "Cao", "monetary": "Cao"}
    for column in RFM_FEATURES:
        values = rfm[column]
        lines.append(
            f"| `{column}` | {DEFINITIONS[column]} | {better[column]} | {values.min():,.0f} | {values.median():,.0f} | "
            f"{values.mean():,.0f} | {values.max():,.0f} | {values.skew():+.2f} |"
        )
    lines += [
        "",
        "**Vì sao chỉ dùng RFM:**",
        "",
        "- RFM đo trực tiếp **hành vi mua tạo doanh thu**: đây là thứ doanh nghiệp tác động được bằng marketing, "
        "và gắn thẳng với mục tiêu tăng doanh thu.",
        "- Nhân khẩu học (tuổi, giới tính, vùng, kênh thu hút) **không** đưa vào. Lý do: cụm cần phản ánh hành vi; "
        "các biến này chỉ dùng để mô tả cụm sau khi phân xong (bước 06).",
        f"- Có {zero_monetary:,} khách có `monetary` = 0, do tiền hoàn bằng hoặc vượt tiền thanh toán (chặn ở 0). "
        "Họ vẫn có frequency và recency nên vẫn được giữ lại.",
        "",
        "## 2. Biến đổi phân phối",
        "",
        "K-Means nhạy với phân phối lệch: vài khách chi tiêu cực lớn sẽ kéo tâm cụm và chiếm khoảng cách. "
        "Mỗi biến được thử 4 phép biến đổi. Gợi ý là **phép đơn giản nhất** có |skew| không kém lựa chọn tốt nhất "
        "quá 0,1 (|skew| gần 0 nghĩa là phân phối gần đối xứng).",
        "",
        "| Biến | Không biến đổi | sqrt | log1p | Yeo-Johnson | Đang dùng | Gợi ý |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for _, row in comparison.iterrows():
        flag = "" if row["configured"] == row["recommended"] else " ⚠️"
        lines.append(
            f"| `{row['feature']}` | {row['skew_none']:+.2f} | {row['skew_sqrt']:+.2f} | {row['skew_log1p']:+.2f} | "
            f"{row['skew_yeo-johnson']:+.2f} | `{row['configured']}`{flag} | `{row['recommended']}` |"
        )
    mismatched = comparison[comparison["configured"] != comparison["recommended"]]
    if not mismatched.empty:
        lines += [
            "",
            "⚠️ **Phép biến đổi đang dùng khác gợi ý** cho: "
            + ", ".join(
                f"`{r['feature']}` (đang `{r['configured']}`, skew {r['skew_' + r['configured']]:+.2f}; "
                f"gợi ý `{r['recommended']}`, skew {r['skew_' + r['recommended']]:+.2f})"
                for _, r in mismatched.iterrows()
            )
            + ". Đổi trong `config.FEATURE_TRANSFORMS` rồi chạy lại từ bước 02.",
        ]
    lines += [
        "",
        f"![Phân phối trước và sau biến đổi]({PLOT_LINK}/fe_distributions.png)",
        "",
        "## 3. Chuẩn hóa (StandardScaler)",
        "",
        "Sau khi biến đổi, mỗi biến được chuẩn hóa về **mean 0, độ lệch chuẩn 1**. K-Means dùng khoảng cách Euclid, "
        "nên nếu không chuẩn hóa thì biến có thang lớn (Monetary) sẽ quyết định gần như toàn bộ khoảng cách.",
        "",
        "| Biến | Phép biến đổi | Mean trước scale | Std trước scale | Mean sau scale | Std sau scale |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for position, column in enumerate(RFM_FEATURES):
        lines.append(
            f"| `{column}` | `{FEATURE_TRANSFORMS[column]}` | {scaler.mean_[position]:,.3f} | {scaler.scale_[position]:,.3f} | "
            f"{transformed[column].mean():+.3f} | {transformed[column].std(ddof=0):.3f} |"
        )
    lines += [
        "",
        "Bước tiếp theo (chương PCA): các biến sau chuẩn hóa vẫn tương quan với nhau (Frequency ↔ Monetary), "
        "nên dùng PCA để khử tương quan trước khi chạy K-Means.",
        "",
        "## 4. Biến hành vi ứng viên",
        "",
        "Các biến dưới đây được tạo từ dữ liệu giao dịch và đánh giá theo câu hỏi: biến này có mang **thông tin mới** "
        f"so với RFM không? Dùng tương quan Spearman (bền với dữ liệu lệch). |ρ| ≥ {REDUNDANT_THRESHOLD} với một biến "
        "RFM nghĩa là trùng thông tin: đưa vào K-Means chỉ làm khía cạnh đó bị tính hai lần.",
        "",
        "| Biến | Định nghĩa | Độ phủ | Median | Skew | Tương quan mạnh nhất với RFM | Quyết định |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for _, row in candidates.iterrows():
        lines.append(
            f"| `{row['feature']}` | {DEFINITIONS[row['feature']]} | {row['coverage_pct']:.0f}% | {row['median']:,.2f} | "
            f"{row['skew']:+.2f} | `{row['strongest_rfm']}` ({row['spearman_rho']:+.2f}) | {row['decision']} |"
        )
    lines += [
        "",
        f"![Tương quan biến ứng viên với RFM]({PLOT_LINK}/fe_candidate_correlation.png)",
        "",
        "**Biến phân loại** (danh mục, thiết bị, phương thức thanh toán, nguồn đơn ưa thích) và **nhân khẩu học** "
        "không đưa vào K-Means vì không đo được bằng khoảng cách Euclid; chúng được dùng để mô tả cụm ở bước 06.",
        "",
        "## 5. Kết quả",
        "",
        f"- Ma trận đặc trưng: **{len(transformed):,} khách × {len(RFM_FEATURES)} biến** "
        f"({', '.join(f'`{c}`' for c in RFM_FEATURES)}), đã biến đổi và chuẩn hóa.",
        "- File: `data/processed/customer_segmentation/customer_features_transformed.csv`. Đây là đầu vào của PCA (bước 03).",
        "- ✍️ Nếu quyết định thêm biến hành vi vào K-Means: thêm vào `config.RFM_FEATURES`, khai báo phép biến đổi "
        "trong `config.FEATURE_TRANSFORMS`, rồi chạy lại từ bước 02.",
    ]
    FEATURES_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    require_file(CUSTOMER_BASE_PATH, "01_build_customer_dataset.py")
    customers = pd.read_csv(CUSTOMER_BASE_PATH)
    purchasers = customers.loc[customers["has_purchase"].astype(bool)].copy()
    if len(purchasers) < 2:
        raise ValueError("At least two purchasing customers are required for K-Means")
    if purchasers[RFM_FEATURES].isna().any().any():
        raise ValueError("RFM values are missing for customers marked as purchasers")
    if (purchasers[RFM_FEATURES] < 0).any().any():
        raise ValueError("RFM values must be non-negative before transformation")
    missing = set(RFM_FEATURES) - set(FEATURE_TRANSFORMS)
    if missing:
        raise ValueError(f"config.FEATURE_TRANSFORMS has no transform for {sorted(missing)}")
    for directory in (OUTPUT_DIR, FE_DIR, PLOT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
    apply_style()

    rfm = purchasers[RFM_FEATURES].reset_index(drop=True)
    shaped = pd.DataFrame({column: apply_transform(rfm[column], FEATURE_TRANSFORMS[column]) for column in RFM_FEATURES})
    scaler = StandardScaler()
    transformed = pd.DataFrame(scaler.fit_transform(shaped), columns=RFM_FEATURES)

    output = transformed.copy()
    output.insert(0, "customer_id", purchasers["customer_id"].to_numpy())
    output.to_csv(FEATURES_PATH, index=False)

    comparison = compare_transforms(rfm)
    behavior = build_behavior_features(purchasers["customer_id"])
    candidates, correlation = assess_candidates(behavior)
    comparison.to_csv(FE_DIR / "transform_comparison.csv", index=False)
    candidates.to_csv(FE_DIR / "candidate_features.csv", index=False)
    plot_distributions(rfm, shaped)
    plot_candidate_correlation(correlation)
    write_report(rfm, comparison, scaler, transformed, candidates, len(customers) - len(purchasers))

    metadata = {
        "input_file": str(CUSTOMER_BASE_PATH.relative_to(ROOT)),
        "output_file": str(FEATURES_PATH.relative_to(ROOT)),
        "customer_count": int(len(purchasers)),
        "excluded_rule_based_customers": int(len(customers) - len(purchasers)),
        "revenue_statuses": sorted(REVENUE_STATUSES),
        "features": RFM_FEATURES,
        "transforms": FEATURE_TRANSFORMS,
        "scaler": {"type": "StandardScaler", "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()},
        "clustering_feature_policy": (
            "Only measurement-based RFM features are used by K-Means. Behavioural candidates, demographic and "
            "acquisition fields are excluded from the feature matrix and used only to describe clusters."
        ),
    }
    FEATURES_METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print(comparison[["feature", *[f"skew_{m}" for m in TRANSFORM_OPTIONS], "configured", "recommended"]]
          .round(2).to_string(index=False))
    print()
    print(candidates[["feature", "coverage_pct", "strongest_rfm", "spearman_rho"]].round(2).to_string(index=False))
    print(f"\nTransformed RFM features: {len(transformed):,} customers × {len(RFM_FEATURES)} → {FEATURES_PATH}")
    print(f"Report: {FEATURES_REPORT_PATH}")


if __name__ == "__main__":
    main()
