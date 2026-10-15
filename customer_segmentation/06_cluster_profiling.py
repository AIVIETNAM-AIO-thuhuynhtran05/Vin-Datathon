"""Bước 6/6 — Kết quả & profile: bức tranh tổng thể (rule-based + K-Means), chân dung và hành động cho từng nhóm.

Đọc nhãn cụm từ bước 4 (customer_segments.csv: customer_id, cluster) — không phụ thuộc
cách bạn chạy K-Means. Gồm:
  1. Đặc tính hành vi theo cụm: quy mô, % doanh thu, RFM, AOV, tỷ lệ trả/hủy, dùng khuyến mãi…
  2. Chỉ số thứ hạng (rank index): khách trung bình của cụm đứng trên/dưới mặt bằng bao nhiêu
     điểm phần trăm ở từng chỉ số — bền với dữ liệu lệch, dễ so sánh giữa các chỉ số.
  3. Tên cụm gợi ý theo R/F/M + hành động tăng doanh thu tương ứng.
  4. Chân dung theo biến mô tả (giới tính, nhóm tuổi, vùng, kênh, thiết bị, thanh toán, danh mục):
     % trong cụm, lift so với toàn bộ, Chi-square + Cramér's V để biết biến nào thực sự phân biệt cụm.

Đầu ra : data/processed/customer_segmentation/profiles/*.csv, plots/profile_*.png,
         reports/markdown/customer_segment_profiles.md
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from config import (
    ALL_SEGMENTS_PATH,
    CUSTOMER_BASE_PATH,
    DEMOGRAPHIC_COLUMNS,
    PCA_SCORES_PATH,
    PLOT_DIR,
    PLOT_LINK,
    PROFILE_DIR,
    PROFILE_REPORT_PATH,
    RANDOM_STATE,
    RULE_SEGMENTS,
    SEGMENTS_PATH,
    require_file,
)
from behavior_features import BEHAVIOR_CATEGORICALS, LABELS, METRICS, build_behavior_features
from segment_naming import SEGMENT_PLAYBOOK, base_name, name_clusters
from plot_style import DIVERGING, INK, MUTED, annotate_heatmap, apply_style, cluster_color

RULE_PLAYBOOK = {
    "RB1": ("Kích hoạt đơn đầu tiên",
            "Voucher đơn đầu có hạn, email/push giới thiệu sản phẩm bán chạy theo kênh thu hút của khách.",
            "Tỷ lệ chuyển đổi đơn đầu"),
    "RB2": ("Gỡ rào cản để chuyển đổi đơn đầu tiên",
            "Tìm lý do hủy/bỏ dở (thanh toán, giá, giao hàng), retarget bằng đúng sản phẩm khách từng đặt; "
            "ưu tiên khách có ≥ 2 đơn thất bại (ý định mua rõ, rào cản lặp lại).", "Tỷ lệ chuyển đổi đơn đầu tiên"),
}


# ------------------------------------------------------------------ features


def build_customer_features(segments: pd.DataFrame) -> pd.DataFrame:
    """Biến hành vi + nhân khẩu học cho khách đã có nhãn cụm (chỉ để mô tả, không dùng phân cụm)."""
    features = segments.merge(build_behavior_features(segments["customer_id"]), on="customer_id", how="left",
                              validate="one_to_one")
    return features[["customer_id", "cluster", *METRICS, *DEMOGRAPHIC_COLUMNS, *BEHAVIOR_CATEGORICALS]]


# ------------------------------------------------------------------ profiles


def numeric_profile(features: pd.DataFrame) -> pd.DataFrame:
    grouped = features.groupby("cluster")
    profile = grouped.agg(customers=("customer_id", "size"), revenue=("monetary", "sum"))
    profile["customer_pct"] = profile["customers"] / profile["customers"].sum() * 100
    profile["revenue_pct"] = profile["revenue"] / profile["revenue"].sum() * 100
    for metric in METRICS:
        profile[f"{metric}_median"] = grouped[metric].median()
        profile[f"{metric}_mean"] = grouped[metric].mean()
    overall = {f"{metric}_median": features[metric].median() for metric in METRICS}
    overall |= {f"{metric}_mean": features[metric].mean() for metric in METRICS}
    overall |= {"customers": len(features), "revenue": features["monetary"].sum(), "customer_pct": 100.0,
                "revenue_pct": 100.0}
    return pd.concat([profile, pd.DataFrame([overall], index=pd.Index(["Tổng"], name="cluster"))])


def rank_index(features: pd.DataFrame) -> pd.DataFrame:
    """Trung bình phân vị (0–100) của khách trong cụm − 50."""
    ranks = features[list(METRICS)].rank(pct=True) * 100
    return ranks.groupby(features["cluster"]).mean() - 50


def categorical_profile(features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, tests = [], []
    for column in [*DEMOGRAPHIC_COLUMNS, *BEHAVIOR_CATEGORICALS]:
        table = pd.crosstab(features["cluster"], features[column])
        chi2, p_value, _, _ = chi2_contingency(table)
        cramers_v = float(np.sqrt(chi2 / (table.to_numpy().sum() * (min(table.shape) - 1)))) if min(table.shape) > 1 else 0.0
        tests.append({"variable": column, "chi2": chi2, "p_value": p_value, "cramers_v": cramers_v,
                      "strength": "mạnh" if cramers_v >= 0.3 else "trung bình" if cramers_v >= 0.1
                      else "yếu" if cramers_v >= 0.05 else "không đáng kể"})
        share = table.div(table.sum(axis=1), axis=0) * 100
        overall = table.sum() / table.to_numpy().sum() * 100
        for cluster in table.index:
            for value in table.columns:
                rows.append({"variable": column, "value": value, "cluster": cluster,
                             "customers": int(table.loc[cluster, value]), "pct_in_cluster": share.loc[cluster, value],
                             "pct_overall": overall[value], "lift": share.loc[cluster, value] / overall[value]})
    return pd.DataFrame(rows), pd.DataFrame(tests).sort_values("cramers_v", ascending=False)


def overall_segments(names: dict[int, str]) -> pd.DataFrame:
    """Gộp nhãn rule-based (khách chưa mua) và cụm K-Means (khách đã mua) cho toàn bộ khách hàng."""
    base = pd.read_csv(CUSTOMER_BASE_PATH)
    clusters = pd.read_csv(SEGMENTS_PATH)[["customer_id", "cluster"]]
    frame = base.merge(clusters, on="customer_id", how="left", validate="one_to_one")
    unlabeled = frame["has_purchase"].astype(bool) & frame["cluster"].isna()
    if unlabeled.any():
        print(f"Cảnh báo: {int(unlabeled.sum()):,} khách đã mua nhưng không có nhãn cụm — xếp vào 'Chưa gán cụm'.")
    is_rule = ~frame["has_purchase"].astype(bool)
    frame["segment_method"] = np.where(is_rule, "rule_based", "kmeans")
    frame["segment"] = np.where(
        is_rule, frame["rule_segment"],
        frame["cluster"].map(lambda c: f"C{int(c)}" if pd.notna(c) else "UNASSIGNED"),
    )
    frame["segment_name"] = frame["segment"].map(
        {**RULE_SEGMENTS, **{f"C{c}": n for c, n in names.items()}, "UNASSIGNED": "Chưa gán cụm"}
    )
    return frame


def rule_details(frame: pd.DataFrame) -> dict[str, str]:
    """Phân bố số đơn thất bại và lý do trong RB2."""
    rb2 = frame[frame["segment"] == "RB2"]
    if rb2.empty:
        return {}
    counts = rb2["failed_order_count"].value_counts().sort_index()
    reasons = rb2["failed_reason"].value_counts()
    return {"RB2": "số đơn thất bại " + ", ".join(f"{int(n)} đơn: {c:,} khách ({c / len(rb2):.1%})" for n, c in counts.items())
            + " · lý do " + ", ".join(f"{r}: {c:,}" for r, c in reasons.items())}


def overall_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary = frame.groupby(["segment_method", "segment", "segment_name"], as_index=False).agg(
        customers=("customer_id", "size"), revenue=("monetary", "sum"),
        frequency_median=("frequency", "median"), monetary_median=("monetary", "median"),
    )
    summary["customer_pct"] = summary["customers"] / summary["customers"].sum() * 100
    summary["revenue_pct"] = summary["revenue"] / summary["revenue"].sum() * 100
    order = {"rule_based": 0, "kmeans": 1}
    return summary.sort_values(["segment_method", "segment"], key=lambda s: s.map(order) if s.name == "segment_method" else s)


def overall_demographics(frame: pd.DataFrame) -> pd.DataFrame:
    """% và lift nhân khẩu học của mọi nhóm so với toàn bộ khách đã đăng ký."""
    rows = []
    for column in DEMOGRAPHIC_COLUMNS:
        table = pd.crosstab(frame["segment"], frame[column].fillna("Unknown"))
        share = table.div(table.sum(axis=1), axis=0) * 100
        overall = table.sum() / table.to_numpy().sum() * 100
        for segment in table.index:
            for value in table.columns:
                rows.append({"variable": column, "value": value, "segment": segment,
                             "pct_in_segment": share.loc[segment, value], "lift": share.loc[segment, value] / overall[value]})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ plots


def plot_size_vs_revenue(summary: pd.DataFrame) -> None:
    """Bức tranh tổng thể: % khách và % doanh thu của mọi nhóm (rule-based + K-Means)."""
    labels = [f"{row.segment} · {row.segment_name}" for row in summary.itertuples()]
    y = np.arange(len(summary))
    figure, axis = plt.subplots(figsize=(8, 0.62 * len(summary) + 1.6))
    axis.barh(y - 0.19, summary["customer_pct"], height=0.36, color="#86b6ef", label="% khách hàng")
    axis.barh(y + 0.19, summary["revenue_pct"], height=0.36, color="#1c5cab", label="% doanh thu")
    for yi, (_, row) in zip(y, summary.iterrows()):
        for offset, column in [(-0.19, "customer_pct"), (0.19, "revenue_pct")]:
            axis.text(row[column] + 0.5, yi + offset, f"{row[column]:.1f}%", va="center", fontsize=8, color=INK)
    axis.set_yticks(y, labels)
    axis.invert_yaxis()
    rule_count = int(summary["segment_method"].eq("rule_based").sum())
    if 0 < rule_count < len(summary):
        axis.axhline(rule_count - 0.5, color=MUTED, linewidth=0.8, linestyle="--")
    axis.set_xlabel("%")
    axis.grid(axis="y", visible=False)
    axis.set_title("Toàn bộ khách hàng: nhóm rule-based (trên) và cụm K-Means (dưới)", loc="left")
    axis.legend(loc="lower right")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "profile_size_vs_revenue.png", dpi=110)
    plt.close(figure)


def plot_pca_clusters(features: pd.DataFrame) -> None:
    if not PCA_SCORES_PATH.is_file():
        return
    scores = pd.read_csv(PCA_SCORES_PATH).merge(features[["customer_id", "cluster"]], on="customer_id")
    if not {"PC1", "PC2"} <= set(scores.columns):
        return
    sample = scores.sample(min(len(scores), 15_000), random_state=RANDOM_STATE)
    figure, axis = plt.subplots(figsize=(6.6, 5.2))
    for position, cluster in enumerate(sorted(scores["cluster"].unique())):
        part = sample[sample["cluster"] == cluster]
        axis.scatter(part["PC1"], part["PC2"], s=8, alpha=0.45, color=cluster_color(position), label=f"Cụm {cluster}",
                     linewidths=0)
        center = scores.loc[scores["cluster"] == cluster, ["PC1", "PC2"]].mean()
        axis.scatter(*center, s=90, color=cluster_color(position), edgecolors="white", linewidths=2, zorder=3)
        axis.annotate(f"Cụm {cluster}", center, xytext=(8, 8), textcoords="offset points", fontsize=9,
                      fontweight="bold", color=INK)
    axis.set_xlabel("PC1 — giá trị & gắn bó")
    axis.set_ylabel("PC2 — độ mới")
    axis.set_title("Các cụm trên mặt phẳng PCA (mẫu 15.000 khách)", loc="left")
    axis.legend(markerscale=2, loc="best")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "profile_pca_clusters.png", dpi=110)
    plt.close(figure)


def plot_rfm_boxplots(features: pd.DataFrame) -> None:
    clusters = sorted(features["cluster"].unique())
    figure, axes = plt.subplots(1, 3, figsize=(11, 3.8))
    for axis, metric in zip(axes, ["recency_days", "frequency", "monetary"]):
        data = [features.loc[features["cluster"] == c, metric].dropna() for c in clusters]
        boxes = axis.boxplot(data, patch_artist=True, showfliers=False, widths=0.55,
                             medianprops={"color": INK, "linewidth": 1.5})
        for position, patch in enumerate(boxes["boxes"]):
            patch.set_facecolor(cluster_color(position))
            patch.set_alpha(0.8)
            patch.set_edgecolor("white")
        axis.set_xticks(range(1, len(clusters) + 1), [f"Cụm {c}" for c in clusters])
        if metric != "recency_days":
            axis.set_yscale("log")
        axis.set_title(METRICS[metric], loc="left", fontsize=10)
    figure.suptitle("Phân phối RFM theo cụm (không vẽ outlier; F, M thang log)", x=0.01, ha="left",
                    fontweight="bold")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "profile_rfm_boxplots.png", dpi=110)
    plt.close(figure)


def plot_rank_heatmap(index: pd.DataFrame, names: dict[int, str]) -> None:
    values = index.to_numpy()
    figure, axis = plt.subplots(figsize=(10, 0.6 * len(index) + 2.2))
    image = axis.imshow(values, cmap=DIVERGING, vmin=-40, vmax=40, aspect="auto")
    axis.set_xticks(range(values.shape[1]), [METRICS[m] for m in index.columns], rotation=30, ha="right")
    axis.set_yticks(range(len(index)), [f"Cụm {c} · {names[c]}" for c in index.index])
    axis.grid(False)
    annotate_heatmap(axis, values, [[f"{v:+.0f}" for v in row] for row in values], threshold=25)
    axis.set_title("Rank index: cụm đứng trên (+) / dưới (−) mặt bằng bao nhiêu điểm phân vị", loc="left")
    figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "profile_rank_index.png", dpi=110)
    plt.close(figure)


def plot_categorical_lift(categorical: pd.DataFrame, tests: pd.DataFrame) -> None:
    for column in categorical["variable"].unique():
        part = categorical[categorical["variable"] == column]
        lift = part.pivot(index="cluster", columns="value", values="lift")
        pct = part.pivot(index="cluster", columns="value", values="pct_in_cluster")
        cramers_v = float(tests.loc[tests["variable"] == column, "cramers_v"].iloc[0])
        figure, axis = plt.subplots(figsize=(max(6, 1.1 * lift.shape[1] + 2), 0.55 * len(lift) + 2))
        image = axis.imshow(lift.to_numpy(), cmap=DIVERGING, vmin=0.5, vmax=1.5, aspect="auto")
        axis.set_xticks(range(lift.shape[1]), lift.columns, rotation=30, ha="right")
        axis.set_yticks(range(len(lift)), [f"Cụm {c}" for c in lift.index])
        axis.grid(False)
        annotate_heatmap(axis, lift.to_numpy() - 1, [[f"{p:.0f}%" for p in row] for row in pct.to_numpy()],
                         threshold=0.35)
        axis.set_title(f"{LABELS[column]} — % trong cụm (màu = lift so với toàn bộ)", loc="left")
        axis.text(0, 1.02, f"Cramér's V = {cramers_v:.3f}", transform=axis.transAxes, fontsize=8, color=MUTED)
        figure.colorbar(image, ax=axis, shrink=0.8, label="lift")
        figure.tight_layout()
        figure.savefig(PLOT_DIR / f"profile_{column}.png", dpi=110)
        plt.close(figure)


# ------------------------------------------------------------------ report


def rule_segment_cards(summary: pd.DataFrame, demographics: pd.DataFrame, details: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for row in summary[summary["segment_method"] == "rule_based"].itertuples():
        goal, action, kpi = RULE_PLAYBOOK[row.segment]
        traits = demographics[
            (demographics["segment"] == row.segment) & (demographics["pct_in_segment"] >= 5)
            & ((demographics["lift"] >= 1.15) | (demographics["lift"] <= 0.85))
        ].sort_values("lift", key=lambda s: (s - 1).abs(), ascending=False)
        portrait = "; ".join(
            f"{LABELS[t.variable]} = {t.value} {t.pct_in_segment:.0f}% (lift {t.lift:.2f})" for t in traits.head(5).itertuples()
        ) or "gần giống toàn bộ khách (lift trong khoảng 0,85–1,15)"
        lines += [
            "",
            f"### {row.segment} — {row.segment_name}",
            "",
            f"**{row.customers:,} khách ({row.customer_pct:.1f}%)** · chưa phát sinh doanh thu.",
            "",
            f"- **Chân dung nổi bật:** {portrait}.",
            *([f"- **Chi tiết:** {details[row.segment]}."] if row.segment in details else []),
            f"- **Mục tiêu:** {goal}. **Hành động gợi ý:** {action} **KPI:** {kpi}.",
        ]
    return lines


def write_report(profile: pd.DataFrame, index: pd.DataFrame, names: dict[int, str], categorical: pd.DataFrame,
                 tests: pd.DataFrame, summary: pd.DataFrame, demographics: pd.DataFrame, details: dict[str, str]) -> None:
    clusters = list(index.index)
    plots = PLOT_LINK
    rule_cards = rule_segment_cards(summary, demographics, details)
    lines = [
        "# Profile các nhóm khách hàng",
        "",
        "Tạo tự động bởi `customer_segmentation/06_cluster_profiling.py` từ nhãn cụm trong `customer_segments.csv`. "
        "**Tên cụm là gợi ý** theo ma trận Recency × Giá trị (`segment_naming.py`) — chỉnh lại khi diễn giải. Dữ liệu không có biến nghề nghiệp/thu nhập; "
        "chân dung dựa trên giới tính, nhóm tuổi, vùng, kênh thu hút và hành vi mua.",
        "",
        "## 0. Bức tranh tổng thể toàn bộ khách hàng",
        "",
        "Khách **chưa có đơn phát sinh doanh thu** được gán nhóm theo luật (**rule-based**, mã RB) trước khi phân cụm; "
        "khách **đã mua** được phân cụm bằng K-Means (mã C). Lift nhân khẩu học ở mục này so với toàn bộ khách đã đăng ký.",
        "",
        "| Phương pháp | Nhóm | Tên | Khách | % khách | % doanh thu | Frequency (median) | Monetary (median) |",
        "|---|---|---|---:|---:|---:|---:|---:|",
        *[
            f"| {row.segment_method} | {row.segment} | {row.segment_name} | {row.customers:,} | {row.customer_pct:.1f}% | "
            f"{row.revenue_pct:.1f}% | {row.frequency_median:.0f} | {row.monetary_median:,.0f} |"
            for row in summary.itertuples()
        ],
        "",
        f"![Toàn bộ khách hàng]({plots}/profile_size_vs_revenue.png)",
        "",
        "Luật gán nhóm: có ≥ 1 đơn `paid`/`shipped`/`delivered`/`returned` → K-Means; có đơn nhưng tất cả đều "
        "`cancelled`/`created` → **RB2**; chưa đặt đơn nào → **RB1**.",
        *rule_cards,
        "",
        "## 1. Tổng quan cụm K-Means (khách đã mua)",
        "",
        "| Cụm | Tên gợi ý | Khách | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary | AOV | Tỷ lệ trả | Dùng KM |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for cluster in [*clusters, "Tổng"]:
        row = profile.loc[cluster]
        lines.append(
            f"| {cluster} | {names.get(cluster, '—')} | {row['customers']:,.0f} | {row['customer_pct']:.1f}% | "
            f"{row['revenue_pct']:.1f}% | {row['recency_days_median']:,.0f} | {row['frequency_median']:.0f} | "
            f"{row['monetary_median']:,.0f} | {row['aov_median']:,.0f} | {row['return_rate_mean'] * 100:.1f}% | "
            f"{row['promo_share_mean'] * 100:.1f}% |"
        )
    lines += [
        "",
        "Giá trị là **median** (tỷ lệ trả và dùng khuyến mãi là trung bình).",
        "",
        f"![Cụm trên PCA]({plots}/profile_pca_clusters.png)",
        f"![RFM theo cụm]({plots}/profile_rfm_boxplots.png)",
        f"![Rank index]({plots}/profile_rank_index.png)",
        "",
        "## 2. Biến mô tả nào thực sự khác biệt giữa các cụm?",
        "",
        "Với hàng chục nghìn khách, p-value của Chi-square gần như luôn rất nhỏ, nên đánh giá bằng **Cramér's V** "
        "(độ lớn hiệu ứng): < 0,05 không đáng kể · 0,05–0,1 yếu · 0,1–0,3 trung bình · ≥ 0,3 mạnh. "
        "Biến có V không đáng kể **không nên** dùng để nhắm mục tiêu cụm.",
        "",
        "| Biến | Cramér's V | Mức độ | p-value |",
        "|---|---:|---|---:|",
    ]
    for _, row in tests.iterrows():
        lines.append(f"| {LABELS[row['variable']]} | {row['cramers_v']:.3f} | {row['strength']} | {row['p_value']:.2g} |")

    useful = set(tests.loc[tests["cramers_v"] >= 0.05, "variable"])
    lines += ["", "## 3. Chân dung từng cụm"]
    for cluster in clusters:
        row = profile.loc[cluster]
        name = names[cluster]
        goal, action, kpi = SEGMENT_PLAYBOOK[base_name(name)]
        ranks = index.loc[cluster].sort_values(key=np.abs, ascending=False)
        behaviour = [
            f"{METRICS[metric]} {'cao hơn' if value > 0 else 'thấp hơn'} mặt bằng ({value:+.0f} điểm phân vị)"
            for metric, value in ranks.head(4).items() if abs(value) >= 5
        ]
        traits = categorical[
            (categorical["cluster"] == cluster) & categorical["variable"].isin(useful)
            & (categorical["pct_in_cluster"] >= 5) & ((categorical["lift"] >= 1.15) | (categorical["lift"] <= 0.85))
        ].sort_values("lift", key=lambda s: (s - 1).abs(), ascending=False)
        lines += [
            "",
            f"### Cụm {cluster} — {name}",
            "",
            f"**{row['customers']:,.0f} khách ({row['customer_pct']:.1f}%) · {row['revenue_pct']:.1f}% doanh thu** · "
            f"median R = {row['recency_days_median']:,.0f} ngày, F = {row['frequency_median']:.0f} đơn, "
            f"M = {row['monetary_median']:,.0f}, AOV = {row['aov_median']:,.0f}.",
            "",
            "- **Hành vi nổi bật:** " + ("; ".join(behaviour) if behaviour else "gần mặt bằng chung") + ".",
        ]
        if traits.empty:
            lines.append("- **Chân dung:** phân bố nhân khẩu học/kênh gần giống toàn bộ khách — không có nhóm nổi trội "
                         "(lift trong khoảng 0,85–1,15).")
        else:
            lines.append("- **Chân dung nổi bật:** " + "; ".join(
                f"{LABELS[t['variable']]} = {t['value']} {t['pct_in_cluster']:.0f}% (lift {t['lift']:.2f})"
                for _, t in traits.head(6).iterrows()) + ".")
        lines += [
            f"- **Mục tiêu:** {goal}. **Hành động gợi ý:** {action} **KPI:** {kpi}.",
            "- ✍️ Ước tính tác động: … (vd +x% tỷ lệ mua lại × AOV × số khách).",
        ]
    lines += [
        "",
        "## 4. Chân dung chi tiết theo biến",
        "",
        "Ô hiển thị % khách trong cụm; màu đỏ = lift > 1 (nhiều hơn mặt bằng), xanh = lift < 1.",
        "",
    ]
    for _, row in tests.iterrows():
        lines.append(f"![{LABELS[row['variable']]}]({plots}/profile_{row['variable']}.png)")
    PROFILE_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ main


def main() -> None:
    require_file(SEGMENTS_PATH, "05_kmeans_segmentation.py")
    require_file(CUSTOMER_BASE_PATH, "01_build_customer_dataset.py")
    segments = pd.read_csv(SEGMENTS_PATH)
    if not {"customer_id", "cluster"} <= set(segments.columns):
        raise ValueError("customer_segments.csv must contain columns customer_id, cluster")
    if segments["customer_id"].duplicated().any():
        raise ValueError("customer_segments.csv has duplicate customer_id")
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()

    features = build_customer_features(segments[["customer_id", "cluster"]])
    profile = numeric_profile(features)
    index = rank_index(features)
    names = name_clusters(index)
    profile.insert(0, "suggested_name", pd.Series(names))
    categorical, tests = categorical_profile(features)

    features.to_csv(PROFILE_DIR / "customer_profile_features.csv", index=False)
    profile.to_csv(PROFILE_DIR / "cluster_numeric_profile.csv")
    index.to_csv(PROFILE_DIR / "cluster_rank_index.csv")
    categorical.to_csv(PROFILE_DIR / "cluster_categorical_profile.csv", index=False)
    tests.to_csv(PROFILE_DIR / "cluster_association_tests.csv", index=False)

    overall = overall_segments(names)
    summary = overall_summary(overall)
    demographics = overall_demographics(overall)
    overall[["customer_id", "segment_method", "segment", "segment_name"]].to_csv(ALL_SEGMENTS_PATH, index=False)
    summary.to_csv(PROFILE_DIR / "all_segments_summary.csv", index=False)
    demographics.to_csv(PROFILE_DIR / "all_segments_demographics.csv", index=False)

    plot_size_vs_revenue(summary)
    plot_pca_clusters(features)
    plot_rfm_boxplots(features)
    plot_rank_heatmap(index, names)
    plot_categorical_lift(categorical, tests)
    write_report(profile, index, names, categorical, tests, summary, demographics, rule_details(overall))

    print(summary[["segment", "segment_name", "customers", "customer_pct", "revenue_pct"]].round(1).to_string(index=False))
    print(f"\nProfiles: {PROFILE_DIR}\nReport: {PROFILE_REPORT_PATH}")


if __name__ == "__main__":
    main()
