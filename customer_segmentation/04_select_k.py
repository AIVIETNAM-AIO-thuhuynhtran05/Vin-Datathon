"""Bước 4/6 — Chọn số cụm k: quét k và đánh giá theo cả thống kê lẫn business. KHÔNG ghi nhãn cụm.

Mỗi k được đánh giá bằng:
  * Elbow (inertia)            — điểm gãy: thêm cụm không còn giảm nhiều sai số.
  * Silhouette (↑)             — cụm tách nhau rõ; trên mẫu 10.000 khách.
  * Calinski-Harabasz (↑)      — tỷ lệ phân tán giữa cụm / trong cụm.
  * Davies-Bouldin (↓)         — độ chồng lấn giữa các cụm.
  * Độ ổn định (ARI ↑)         — chạy lại với nhiều random_state, nhãn có giữ nguyên không.
  * Cụm nhỏ nhất (% khách)     — cụm quá nhỏ khó triển khai chiến dịch riêng.
  * Số nhóm hành động khác nhau — mỗi cụm có tên gợi ý (theo R/F/M) khác nhau → mỗi cụm một hành động.
Kèm thành phần của từng k: tên cụm gợi ý, % khách, % doanh thu, median R/F/M.

Đầu ra : k_selection/k_selection_metrics.csv, k_selection/k_selection_profiles.csv,
         plots/k_selection_*.png, reports/markdown/customer_segmentation_k_selection.md
Sau khi chọn k: python customer_segmentation/05_kmeans_segmentation.py --k <k>
"""

from __future__ import annotations

import argparse
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score

from config import (
    CUSTOMER_BASE_PATH,
    FEATURES_PATH,
    K_SELECTION_DIR,
    K_SELECTION_REPORT_PATH,
    PCA_SCORES_PATH,
    PLOT_DIR,
    PLOT_LINK,
    RANDOM_STATE,
    require_file,
)
from plot_style import CLUSTER_COLORS, MUTED, apply_style
from segment_naming import NAME_ORDER, RFM_COLUMNS, base_name, name_clusters, rfm_rank_index

INPUTS = {"pca": (PCA_SCORES_PATH, "03_pca_analysis.py"), "scaled": (FEATURES_PATH, "02_transform_features.py")}
SILHOUETTE_SAMPLE_SIZE = 10_000
STABILITY_THRESHOLD = 0.9
NAME_COLORS = dict(zip(NAME_ORDER, CLUSTER_COLORS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", choices=INPUTS, default="pca", help="Đặc trưng đưa vào K-Means")
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--seeds", type=int, default=5, help="Số random_state để đo độ ổn định")
    parser.add_argument("--min-cluster-pct", type=float, default=5.0, help="Cụm nhỏ nhất tối thiểu (%% khách)")
    parser.add_argument("--min-business-k", type=int, default=3,
                        help="Số nhóm tối thiểu để có chiến lược khác biệt (k=2 thường quá thô)")
    return parser.parse_args()


def evaluate_k(features: np.ndarray, rfm: pd.DataFrame, k: int, seeds: list[int]) -> tuple[dict, pd.DataFrame]:
    models = [KMeans(n_clusters=k, random_state=seed, n_init=10).fit(features) for seed in seeds]
    labels = models[0].labels_
    stability = [adjusted_rand_score(a.labels_, b.labels_) for a, b in combinations(models, 2)]
    sizes = np.bincount(labels, minlength=k)

    labels_series = pd.Series(labels, index=rfm.index)
    names = name_clusters(rfm_rank_index(rfm, labels_series))
    grouped = rfm.groupby(labels)
    profile = pd.DataFrame({
        "k": k,
        "cluster": range(k),
        "suggested_name": [names[c] for c in range(k)],
        "customers": sizes,
        "customer_pct": sizes / sizes.sum() * 100,
        "revenue_pct": grouped["monetary"].sum().reindex(range(k)).to_numpy() / rfm["monetary"].sum() * 100,
        **{f"{column}_median": grouped[column].median().reindex(range(k)).to_numpy() for column in RFM_COLUMNS},
    }).sort_values("revenue_pct", ascending=False)

    metrics = {
        "k": k,
        "inertia": models[0].inertia_,
        "silhouette": silhouette_score(features, labels, sample_size=min(SILHOUETTE_SAMPLE_SIZE, len(features) - 1),
                                       random_state=RANDOM_STATE),
        "calinski_harabasz": calinski_harabasz_score(features, labels),
        "davies_bouldin": davies_bouldin_score(features, labels),
        "stability_ari": float(np.mean(stability)) if stability else 1.0,
        "min_cluster_pct": sizes.min() / sizes.sum() * 100,
        "distinct_actions": len({base_name(n) for n in names.values()}),
        "top_cluster_revenue_pct": profile["revenue_pct"].max(),
    }
    return metrics, profile


def elbow_k(metrics: pd.DataFrame) -> int:
    """Kneedle: điểm xa nhất so với đường nối inertia đầu và cuối (sau khi chuẩn hóa)."""
    x = (metrics["k"] - metrics["k"].min()) / (metrics["k"].max() - metrics["k"].min())
    y = (metrics["inertia"] - metrics["inertia"].min()) / (metrics["inertia"].max() - metrics["inertia"].min())
    distance = (1 - x) - y
    return int(metrics.loc[distance.idxmax(), "k"])


def recommend(metrics: pd.DataFrame, args: argparse.Namespace) -> tuple[int, pd.DataFrame]:
    scored = metrics.copy()
    scored["stat_rank"] = (
        scored["silhouette"].rank(ascending=False) + scored["calinski_harabasz"].rank(ascending=False)
        + scored["davies_bouldin"].rank(ascending=True)
    ) / 3
    scored["eligible"] = (
        (scored["k"] >= args.min_business_k)
        & (scored["stability_ari"] >= STABILITY_THRESHOLD)
        & (scored["min_cluster_pct"] >= args.min_cluster_pct)
        & (scored["distinct_actions"] == scored["k"])
    )
    pool = scored[scored["eligible"]] if scored["eligible"].any() else scored[scored["k"] >= args.min_business_k]
    best = pool.sort_values(["stat_rank", "k"]).iloc[0]
    return int(best["k"]), scored


def plot_metrics(scored: pd.DataFrame, chosen: int, elbow: int, args: argparse.Namespace) -> None:
    panels = [
        ("inertia", "Inertia — elbow", None, f"elbow k = {elbow}"),
        ("silhouette", "Silhouette (↑)", None, None),
        ("calinski_harabasz", "Calinski-Harabasz (↑)", None, None),
        ("davies_bouldin", "Davies-Bouldin (↓)", None, None),
        ("stability_ari", "Độ ổn định ARI (↑)", STABILITY_THRESHOLD, f"ngưỡng {STABILITY_THRESHOLD}"),
        ("min_cluster_pct", "Cụm nhỏ nhất (% khách)", args.min_cluster_pct, f"ngưỡng {args.min_cluster_pct:.0f}%"),
    ]
    figure, axes = plt.subplots(2, 3, figsize=(12, 6.4))
    for axis, (column, title, threshold, note) in zip(axes.flat, panels):
        axis.axvspan(chosen - 0.4, chosen + 0.4, color="#eb6834", alpha=0.12, linewidth=0)
        axis.plot(scored["k"], scored[column], color="#2a78d6", linewidth=2, marker="o", markersize=7)
        point = scored.loc[scored["k"] == chosen, column].iloc[0]
        axis.plot([chosen], [point], marker="o", markersize=10, color="#eb6834", markeredgecolor="white",
                  markeredgewidth=2, zorder=3)
        if threshold is not None:
            axis.axhline(threshold, color=MUTED, linestyle="--", linewidth=1)
        if column == "inertia":
            axis.axvline(elbow, color=MUTED, linestyle=":", linewidth=1)
        if note:
            axis.text(0.98, 0.95, note, transform=axis.transAxes, ha="right", va="top", fontsize=8, color=MUTED)
        axis.set_title(title, loc="left", fontsize=10)
        axis.set_xticks(scored["k"])
        axis.set_xlabel("k")
    figure.suptitle(f"Chọn số cụm — vùng cam là k gợi ý ({chosen})", x=0.01, ha="left", fontweight="bold")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "k_selection_metrics.png", dpi=110)
    plt.close(figure)


def plot_composition(profiles: pd.DataFrame, chosen: int) -> None:
    """Mỗi k chia khách & doanh thu thành những nhóm gì (màu theo tên gợi ý)."""
    ks = sorted(profiles["k"].unique())
    figure, axes = plt.subplots(1, 2, figsize=(12, 0.55 * len(ks) + 2.2), sharey=True)
    for axis, column, title in [(axes[0], "customer_pct", "% khách hàng"), (axes[1], "revenue_pct", "% doanh thu")]:
        for row, k in enumerate(ks):
            left = 0.0
            part = profiles[profiles["k"] == k].assign(order=lambda d: d["suggested_name"].map(base_name).map(
                {n: i for i, n in enumerate(NAME_ORDER)}))
            for _, cluster in part.sort_values("order").iterrows():
                width = cluster[column]
                axis.barh(row, width, left=left, height=0.62, color=NAME_COLORS[base_name(cluster["suggested_name"])],
                          edgecolor="white", linewidth=2)
                if width >= 7:
                    axis.text(left + width / 2, row, f"{width:.0f}%", ha="center", va="center", fontsize=7.5,
                              color="white")
                left += width
        axis.set_yticks(range(len(ks)), [f"k = {k}" + ("  ◄" if k == chosen else "") for k in ks])
        axis.set_xlim(0, 100)
        axis.invert_yaxis()
        axis.grid(axis="y", visible=False)
        axis.set_title(title, loc="left", fontsize=10)
    handles = [plt.Rectangle((0, 0), 1, 1, color=NAME_COLORS[n]) for n in NAME_ORDER
               if n in set(profiles["suggested_name"].map(base_name))]
    labels = [n for n in NAME_ORDER if n in set(profiles["suggested_name"].map(base_name))]
    figure.legend(handles, labels, loc="lower center", ncol=len(labels), frameon=False, fontsize=8)
    figure.suptitle("Thành phần nhóm theo từng k (tên gợi ý theo R/F/M)", x=0.01, ha="left", fontweight="bold")
    figure.tight_layout(rect=(0, 0.07, 1, 1))
    figure.savefig(PLOT_DIR / "k_selection_composition.png", dpi=110)
    plt.close(figure)


def write_report(scored: pd.DataFrame, profiles: pd.DataFrame, chosen: int, elbow: int,
                 args: argparse.Namespace, customer_count: int) -> None:
    plots = PLOT_LINK
    best_silhouette = int(scored.loc[scored["silhouette"].idxmax(), "k"])
    lines = [
        "# Chọn số cụm k cho K-Means",
        "",
        f"Tạo tự động bởi `customer_segmentation/04_select_k.py` · đầu vào: `{args.input}` · {customer_count:,} khách "
        f"đã mua · k = {args.min_k}–{args.max_k} · {args.seeds} random_state mỗi k. Bước này **không ghi nhãn cụm**; "
        "chọn k xong chạy `05_kmeans_segmentation.py --k <k>`.",
        "",
        "## 1. Vì sao không chỉ nhìn silhouette",
        "",
        "Các chỉ số thống kê thường ưu tiên k nhỏ: ít cụm thì cụm tách nhau rõ hơn. Nhưng số nhóm phải đủ để "
        "**mỗi nhóm nhận một chiến lược khác nhau**. Vì vậy k được chọn theo 3 lớp:",
        "",
        "1. **Điều kiện business (lọc):**",
        f"   - k ≥ {args.min_business_k}.",
        f"   - Cụm nhỏ nhất ≥ {args.min_cluster_pct:.0f}% khách (đủ lớn để chạy chiến dịch riêng).",
        "   - Mỗi cụm có tên hành vi khác nhau (`distinct_actions = k`): không có hai cụm cùng một loại, "
        "nghĩa là không có hai cụm phải xử lý giống nhau. Tên đặt theo ma trận Recency × Giá trị (`segment_naming.py`).",
        f"2. **Độ ổn định:** ARI trung bình giữa các lần chạy ≥ {STABILITY_THRESHOLD}. Nhãn không đổi khi đổi random_state.",
        "3. **Chất lượng thống kê:** xếp hạng trung bình của Silhouette (↑), Calinski-Harabasz (↑) và Davies-Bouldin (↓); "
        "tham khảo thêm điểm elbow của inertia.",
        "",
        "## 2. Kết quả",
        "",
        "| k | Inertia | Silhouette | Calinski-Harabasz | Davies-Bouldin | ARI | Cụm nhỏ nhất | Nhóm hành động | Hạng TK | Đạt điều kiện |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for _, row in scored.iterrows():
        mark = " **◄**" if row["k"] == chosen else ""
        lines.append(
            f"| {int(row['k'])}{mark} | {row['inertia']:,.0f} | {row['silhouette']:.3f} | {row['calinski_harabasz']:,.0f} | "
            f"{row['davies_bouldin']:.3f} | {row['stability_ari']:.3f} | {row['min_cluster_pct']:.1f}% | "
            f"{int(row['distinct_actions'])}/{int(row['k'])} | {row['stat_rank']:.1f} | {'✅' if row['eligible'] else '—'} |"
        )
    pick = scored[scored["k"] == chosen].iloc[0]
    lines += [
        "",
        f"![Chỉ số theo k]({plots}/k_selection_metrics.png)",
        "",
        f"- Elbow của inertia: **k = {elbow}**. Silhouette cao nhất: **k = {best_silhouette}**.",
        f"- **Gợi ý: k = {chosen}**: silhouette {pick['silhouette']:.3f}, ARI {pick['stability_ari']:.3f}, "
        f"cụm nhỏ nhất {pick['min_cluster_pct']:.1f}%, {int(pick['distinct_actions'])} nhóm hành động khác nhau.",
        "- Đây là gợi ý; quyết định cuối nên dựa vào mục 3: nhóm nào cần chiến lược riêng và có đủ nguồn lực để triển khai.",
        "",
        "## 3. Mỗi k chia khách hàng thành những nhóm nào",
        "",
        f"![Thành phần nhóm theo k]({plots}/k_selection_composition.png)",
    ]
    for k in sorted(profiles["k"].unique()):
        if k < args.min_business_k:
            continue
        part = profiles[profiles["k"] == k]
        lines += [
            "",
            f"### k = {k}" + (" (gợi ý)" if k == chosen else ""),
            "",
            "| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
        for _, row in part.iterrows():
            lines.append(
                f"| {int(row['cluster'])} | {row['suggested_name']} | {row['customer_pct']:.1f}% | {row['revenue_pct']:.1f}% | "
                f"{row['recency_days_median']:,.0f} | {row['frequency_median']:.0f} | {row['monetary_median']:,.0f} |"
            )
    lines += [
        "",
        "## 4. Bước tiếp theo",
        "",
        "```bash",
        f"python customer_segmentation/05_kmeans_segmentation.py --k {chosen}",
        "python customer_segmentation/06_cluster_profiling.py",
        "```",
    ]
    K_SELECTION_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path, producer = INPUTS[args.input]
    require_file(input_path, producer)
    require_file(CUSTOMER_BASE_PATH, "01_build_customer_dataset.py")
    if not 2 <= args.min_k <= args.max_k:
        raise ValueError("Expected 2 <= min-k <= max-k")
    K_SELECTION_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()

    features_frame = pd.read_csv(input_path)
    feature_columns = [column for column in features_frame.columns if column != "customer_id"]
    rfm = features_frame[["customer_id"]].merge(
        pd.read_csv(CUSTOMER_BASE_PATH, usecols=["customer_id", *RFM_COLUMNS]), on="customer_id", how="left",
        validate="one_to_one",
    )
    features = features_frame[feature_columns].to_numpy()
    seeds = [RANDOM_STATE + i for i in range(args.seeds)]

    metric_rows, profile_frames = [], []
    for k in range(args.min_k, args.max_k + 1):
        metrics, profile = evaluate_k(features, rfm, k, seeds)
        metric_rows.append(metrics)
        profile_frames.append(profile)
        print(f"k={k}: silhouette={metrics['silhouette']:.3f}, CH={metrics['calinski_harabasz']:,.0f}, "
              f"DB={metrics['davies_bouldin']:.3f}, ARI={metrics['stability_ari']:.3f}, "
              f"min cluster={metrics['min_cluster_pct']:.1f}%, actions={metrics['distinct_actions']}/{k}")

    metrics = pd.DataFrame(metric_rows)
    profiles = pd.concat(profile_frames, ignore_index=True)
    elbow = elbow_k(metrics)
    chosen, scored = recommend(metrics, args)
    scored.to_csv(K_SELECTION_DIR / "k_selection_metrics.csv", index=False)
    profiles.to_csv(K_SELECTION_DIR / "k_selection_profiles.csv", index=False)
    plot_metrics(scored, chosen, elbow, args)
    plot_composition(profiles, chosen)
    write_report(scored, profiles, chosen, elbow, args, len(features))
    print(f"\nElbow k={elbow}; suggested k={chosen}. Report: {K_SELECTION_REPORT_PATH}")


if __name__ == "__main__":
    main()
