"""Bước 3/6 — Feature engineering (tiếp): PCA trên đặc trưng RFM đã chuẩn hóa — chuẩn bị đầu vào cho K-Means.

Vì sao PCA:
  * K-Means dùng khoảng cách Euclid → các biến tương quan mạnh (frequency ↔ monetary)
    bị tính "hai lần" cho cùng một khía cạnh hành vi (giá trị mua). PCA xoay dữ liệu
    sang các trục trực giao, không tương quan.
  * Giữ số thành phần giải thích ≥ --variance-target phương sai giúp bỏ chiều dư thừa/nhiễu.
  * PC1–PC2 cho phép vẽ cụm trên mặt phẳng 2D để kiểm tra trực quan độ tách cụm.
  * Loadings cho biết mỗi trục là tổ hợp của biến nào → trục có ý nghĩa kinh doanh.

Kiểm tra trước PCA: ma trận tương quan, Bartlett (tương quan có khác 0 không) và KMO
(mức độ chung phương sai). Kết quả và diễn giải ghi vào reports/customer_segmentation_pca.md.

Đầu vào : data/processed/customer_segmentation/customer_features_transformed.csv
Đầu ra  : customer_pca_scores.csv (customer_id + PC đã chọn — dùng cho K-Means),
          pca_explained_variance.csv, pca_loadings.csv, pca_feature_correlation.csv,
          pca_metadata.json, plots/pca_*.png
"""

from __future__ import annotations

import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

from config import FEATURES_PATH, OUTPUT_DIR, PCA_REPORT_PATH, PCA_SCORES_PATH, PLOT_DIR, ROOT, require_file
from plot_style import DIVERGING, INK, INK_SECONDARY, MUTED, SEQUENTIAL, SURFACE, annotate_heatmap, apply_style


LOADING_THRESHOLD = 0.5
FEATURE_LABELS = {"recency_days": "Recency", "frequency": "Frequency", "monetary": "Monetary"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--variance-target", type=float, default=0.80,
                        help="Giữ số PC nhỏ nhất đạt tỷ lệ phương sai tích lũy này (mặc định 0.80)")
    parser.add_argument("--n-components", type=int, help="Cố định số PC giữ lại (bỏ qua --variance-target)")
    return parser.parse_args()


def bartlett_sphericity(correlation: np.ndarray, n: int) -> tuple[float, float]:
    """H0: ma trận tương quan là ma trận đơn vị (các biến không tương quan → PCA vô ích)."""
    p = correlation.shape[0]
    statistic = -(n - 1 - (2 * p + 5) / 6) * np.log(np.linalg.det(correlation))
    degrees = p * (p - 1) / 2
    return float(statistic), float(stats.chi2.sf(statistic, degrees))


def kmo(correlation: np.ndarray) -> float:
    """Kaiser-Meyer-Olkin: > 0.6 là chấp nhận được để rút gọn chiều."""
    inverse = np.linalg.inv(correlation)
    partial = -inverse / np.sqrt(np.outer(np.diag(inverse), np.diag(inverse)))
    off_diagonal = ~np.eye(correlation.shape[0], dtype=bool)
    r2 = (correlation[off_diagonal] ** 2).sum()
    return float(r2 / (r2 + (partial[off_diagonal] ** 2).sum()))


def describe_component(loadings: pd.Series) -> str:
    strong = loadings[loadings.abs() >= LOADING_THRESHOLD].sort_values(key=np.abs, ascending=False)
    if strong.empty:
        strong = loadings.reindex(loadings.abs().sort_values(ascending=False).index[:1])
    return ", ".join(f"{'+' if value > 0 else '−'}{FEATURE_LABELS.get(name, name)} ({value:+.2f})"
                     for name, value in strong.items())


def plot_correlation(correlation: pd.DataFrame) -> None:
    labels = [FEATURE_LABELS.get(name, name) for name in correlation.columns]
    figure, axis = plt.subplots(figsize=(4.6, 3.8))
    image = axis.imshow(correlation.to_numpy(), cmap=DIVERGING, vmin=-1, vmax=1)
    axis.set_xticks(range(len(labels)), labels)
    axis.set_yticks(range(len(labels)), labels)
    axis.grid(False)
    annotate_heatmap(axis, correlation.to_numpy(), [[f"{v:.2f}" for v in row] for row in correlation.to_numpy()],
                     threshold=0.6)
    axis.set_title("Tương quan giữa các biến RFM (sau log1p + scale)", loc="left")
    figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "pca_feature_correlation.png", dpi=110)
    plt.close(figure)


def plot_scree(variance: pd.DataFrame, n_selected: int, target: float) -> None:
    figure, axis = plt.subplots(figsize=(6.4, 3.6))
    x = np.arange(1, len(variance) + 1)
    colors = ["#2a78d6" if index < n_selected else "#b7d3f6" for index in range(len(variance))]
    axis.bar(x, variance["explained_variance_pct"], color=colors, width=0.55, label="Phương sai từng PC")
    axis.plot(x, variance["cumulative_pct"], color=INK_SECONDARY, linewidth=2, marker="o", markersize=6,
              label="Tích lũy")
    axis.axhline(target * 100, color=MUTED, linestyle="--", linewidth=1)
    axis.text(0.55, target * 100 + 1.5, f"mục tiêu {target:.0%}", va="bottom", fontsize=8, color=MUTED)
    for xi, value in zip(x, variance["cumulative_pct"]):
        axis.annotate(f"{value:.1f}%", (xi, value), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    axis.set_xticks(x, [f"PC{i}" for i in x])
    axis.set_ylim(0, 110)
    axis.set_ylabel("% phương sai")
    axis.set_title(f"Scree plot — giữ {n_selected} thành phần (màu đậm)", loc="left")
    axis.legend(loc="center right")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "pca_scree.png", dpi=110)
    plt.close(figure)


def plot_loadings(loadings: pd.DataFrame) -> None:
    labels = [FEATURE_LABELS.get(name, name) for name in loadings.index]
    figure, axis = plt.subplots(figsize=(4.8, 3.4))
    image = axis.imshow(loadings.to_numpy(), cmap=DIVERGING, vmin=-1, vmax=1, aspect="auto")
    axis.set_xticks(range(loadings.shape[1]), loadings.columns)
    axis.set_yticks(range(len(labels)), labels)
    axis.grid(False)
    annotate_heatmap(axis, loadings.to_numpy(), [[f"{v:+.2f}" for v in row] for row in loadings.to_numpy()],
                     threshold=0.6)
    axis.set_title("Loadings (tương quan biến – thành phần)", loc="left")
    figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "pca_loadings.png", dpi=110)
    plt.close(figure)


def plot_projection(scores: np.ndarray, loadings: pd.DataFrame, variance: pd.DataFrame) -> None:
    """Mật độ khách hàng trên PC1–PC2 kèm mũi tên loadings (biplot)."""
    figure, axis = plt.subplots(figsize=(6.6, 5.2))
    axis.hexbin(scores[:, 0], scores[:, 1], gridsize=60, cmap=SEQUENTIAL, mincnt=1, bins="log")
    scale = np.percentile(np.abs(scores[:, :2]), 99, axis=0).min()
    tips = loadings.iloc[:, :2].to_numpy() * scale
    angles = np.degrees(np.arctan2(tips[:, 1], tips[:, 0]))
    for index, (name, tip) in enumerate(zip(loadings.index, tips)):
        axis.annotate("", xy=tip, xytext=(0, 0),
                      arrowprops={"arrowstyle": "-|>", "color": INK, "linewidth": 1.6})
        # Mũi tên gần cùng hướng: đẩy nhãn lên/xuống để không đè nhau.
        close = [other for other in range(len(tips)) if other != index and abs(angles[other] - angles[index]) < 20]
        lift = 0 if not close else (10 if angles[index] > max(angles[c] for c in close) else -10)
        axis.annotate(FEATURE_LABELS.get(name, name), xy=tip, xytext=(6 * np.sign(tip[0]), lift),
                      textcoords="offset points", fontsize=9, color=INK, fontweight="bold",
                      ha="left" if tip[0] >= 0 else "right", va="center",
                      bbox={"boxstyle": "round,pad=0.2", "facecolor": SURFACE, "edgecolor": "none", "alpha": 0.85})
    pct = variance["explained_variance_pct"].to_numpy()
    axis.set_xlabel(f"PC1 ({pct[0]:.1f}% phương sai)")
    axis.set_ylabel(f"PC2 ({pct[1]:.1f}% phương sai)")
    axis.set_title("Khách hàng trên mặt phẳng PC1–PC2", loc="left", pad=16)
    axis.text(0, 1.01, "Màu đậm = nhiều khách; mũi tên = hướng tăng của từng biến", transform=axis.transAxes,
              fontsize=8, color=MUTED, va="bottom")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "pca_biplot.png", dpi=110)
    plt.close(figure)


def write_report(meta: dict[str, object], variance: pd.DataFrame, loadings: pd.DataFrame,
                 correlation: pd.DataFrame) -> None:
    labels = {name: FEATURE_LABELS.get(name, name) for name in correlation.columns}
    pairs = [
        (labels[a], labels[b], correlation.loc[a, b])
        for i, a in enumerate(correlation.columns) for b in correlation.columns[i + 1:]
    ]
    strongest = max(pairs, key=lambda pair: abs(pair[2]))
    n = meta["n_components_selected"]
    lines = [
        "# PCA cho phân cụm khách hàng",
        "",
        "Tạo tự động bởi `customer_segmentation/03_pca_analysis.py`. Biểu đồ: "
        "`data/processed/customer_segmentation/plots/pca_*.png`.",
        "",
        "## 1. Vì sao dùng PCA trước K-Means",
        "",
        "1. **K-Means đo khoảng cách Euclid**, mọi biến có trọng số như nhau. Khi hai biến tương quan mạnh, "
        f"chúng đo cùng một khía cạnh hành vi và khía cạnh đó bị tính hai lần. Ở đây cặp tương quan mạnh nhất là "
        f"**{strongest[0]} – {strongest[1]} (r = {strongest[2]:.2f})**: khách mua nhiều lần thì tổng chi tiêu cũng cao. "
        "Nếu không xử lý, cụm sẽ bị chi phối bởi \"giá trị mua\" và Recency bị lép vế.",
        "2. **PCA xoay dữ liệu sang các trục trực giao** (không tương quan). Mỗi trục gom phần thông tin chung "
        "của các biến tương quan, nên khoảng cách không còn bị đếm trùng khi ta bỏ bớt trục ít thông tin.",
        "3. **Rút gọn chiều và lọc nhiễu**: giữ các PC giải thích phần lớn phương sai, bỏ PC cuối (chủ yếu là nhiễu).",
        "4. **Trực quan hóa**: PC1–PC2 là mặt phẳng 2D tốt nhất để vẽ và kiểm tra cụm có tách nhau không.",
        "5. **Diễn giải**: loadings cho biết mỗi trục được tạo từ biến nào, giúp đặt tên trục theo ngôn ngữ kinh doanh.",
        "",
        "**Tiền xử lý bắt buộc**: `log1p` (vì Frequency/Monetary lệch phải mạnh) rồi `StandardScaler`. PCA tìm hướng có "
        "phương sai lớn nhất, nên nếu không chuẩn hóa thì Monetary (đơn vị tiền, hàng chục nghìn) sẽ chiếm gần trọn PC1.",
        "",
        "> **Lưu ý quan trọng:** nếu giữ **đủ tất cả** PC thì PCA chỉ là phép xoay, khoảng cách Euclid không đổi, nên "
        "K-Means cho kết quả **giống hệt** khi chạy trên dữ liệu đã scale. Lợi ích của PCA với K-Means chỉ đến từ việc "
        "**bỏ bớt** PC. Với chỉ 3 biến, mức rút gọn nhỏ; giá trị chính là khử tương quan, trực quan hóa và diễn giải.",
        "",
        "## 2. Dữ liệu có phù hợp để PCA không?",
        "",
        f"- Số khách hàng: **{meta['customer_count']:,}**; số biến: **{len(correlation)}** "
        f"({', '.join(labels.values())}).",
        f"- **Bartlett's test of sphericity**: χ² = {meta['bartlett_chi2']:,.0f}, p = {meta['bartlett_p']:.2g} → "
        + ("bác bỏ H0, các biến có tương quan đáng kể, **PCA có ý nghĩa**."
           if meta["bartlett_p"] < 0.05 else "không bác bỏ H0, các biến gần như độc lập, PCA ít giá trị."),
        f"- **KMO** = {meta['kmo']:.2f} → "
        + ("tốt (≥ 0,7)." if meta["kmo"] >= 0.7 else "chấp nhận được (0,6–0,7)." if meta["kmo"] >= 0.6
           else "thấp (< 0,6): tương quan chủ yếu đến từ một cặp biến, không phải từ toàn bộ biến. Với 3 biến, KMO thấp "
                "là thường gặp; dùng PCA chủ yếu để khử tương quan và trực quan hóa."),
        "",
        "| | " + " | ".join(labels.values()) + " |",
        "|---|" + "---:|" * len(labels),
    ]
    for name in correlation.index:
        lines.append(f"| **{labels[name]}** | " + " | ".join(f"{v:.2f}" for v in correlation.loc[name]) + " |")

    lines += [
        "",
        "## 3. Chọn số thành phần",
        "",
        "| PC | Eigenvalue | % phương sai | % tích lũy | Thành phần chính (|loading| ≥ 0,5) |",
        "|---|---:|---:|---:|---|",
    ]
    for _, row in variance.iterrows():
        lines.append(
            f"| {row['component']} | {row['eigenvalue']:.3f} | {row['explained_variance_pct']:.1f}% | "
            f"{row['cumulative_pct']:.1f}% | {describe_component(loadings[row['component']])} |"
        )
    lines += [
        "",
        f"- **Tiêu chí phương sai tích lũy** (≥ {meta['variance_target']:.0%}): cần **{meta['n_by_variance']}** PC.",
        f"- **Tiêu chí Kaiser** (eigenvalue > 1): **{meta['n_by_kaiser']}** PC.",
        "- **Scree plot** (`pca_scree.png`): chọn tại \"khuỷu\", nơi phần phương sai tăng thêm giảm đột ngột.",
        f"- **Đã chọn: {n} PC** ({meta['selection_rule']}), giữ **{meta['cumulative_variance_selected_pct']:.1f}%** "
        "phương sai. Đổi bằng `--variance-target` hoặc `--n-components`.",
        "",
        "## 4. Diễn giải các thành phần",
        "",
        "Loading = tương quan giữa biến gốc và PC (dấu chỉ chiều; Recency cao = lâu rồi chưa mua = **xấu**).",
        "",
    ]
    for component in loadings.columns:
        lines.append(f"- **{component}**: {describe_component(loadings[component])}.")
    lines += [
        "",
        "Gợi ý đọc trục: thành phần mà Frequency và Monetary cùng dấu, Recency ngược dấu là trục **\"giá trị & gắn bó\"** "
        "(cao = mua nhiều, chi nhiều, mới mua gần đây). Thành phần mà Recency nổi trội là trục **\"độ mới\"**, tách khách "
        "vừa mua gần đây với khách đã lâu không quay lại ở cùng mức giá trị.",
        "",
        "## 5. Dùng kết quả cho K-Means",
        "",
        "- File đầu vào K-Means: `data/processed/customer_segmentation/customer_pca_scores.csv` "
        f"(`customer_id`, {', '.join(f'`PC{i}`' for i in range(1, n + 1))}).",
        "- **Không scale lại** điểm PC: phương sai khác nhau giữa các PC chính là mức quan trọng của từng trục. "
        "Nếu muốn mọi trục có trọng số bằng nhau thì dùng whitening (`PCA(whiten=True)`), nhưng khi đó nhiễu ở PC nhỏ "
        "sẽ bị khuếch đại.",
        "- Kết quả K-Means cần ghi ra `data/processed/customer_segmentation/customer_segments.csv` với 2 cột "
        "`customer_id`, `cluster` để bước 5 (`06_cluster_profiling.py`) mô tả cụm.",
    ]
    PCA_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    require_file(FEATURES_PATH, "02_transform_features.py")
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()

    features = pd.read_csv(FEATURES_PATH)
    feature_columns = [column for column in features.columns if column != "customer_id"]
    matrix = features[feature_columns].to_numpy()
    if np.isnan(matrix).any():
        raise ValueError("Feature matrix contains missing values")

    correlation = features[feature_columns].corr()
    bartlett_chi2, bartlett_p = bartlett_sphericity(correlation.to_numpy(), len(features))
    kmo_value = kmo(correlation.to_numpy())

    pca = PCA().fit(matrix)
    components = [f"PC{i}" for i in range(1, len(feature_columns) + 1)]
    variance = pd.DataFrame(
        {
            "component": components,
            "eigenvalue": pca.explained_variance_,
            "explained_variance_pct": pca.explained_variance_ratio_ * 100,
            "cumulative_pct": np.cumsum(pca.explained_variance_ratio_) * 100,
        }
    )
    loadings = pd.DataFrame(
        pca.components_.T * np.sqrt(pca.explained_variance_), index=feature_columns, columns=components
    )
    # Cố định dấu: PC có Monetary dương để diễn giải nhất quán giữa các lần chạy.
    anchor = "monetary" if "monetary" in feature_columns else feature_columns[0]
    signs = np.where(loadings.loc[anchor] < 0, -1, 1)
    loadings *= signs
    scores = pca.transform(matrix) * signs

    n_by_variance = int(np.searchsorted(variance["cumulative_pct"].to_numpy(), args.variance_target * 100) + 1)
    n_by_kaiser = int((pca.explained_variance_ > 1).sum())
    if args.n_components:
        n_selected, rule = args.n_components, "cố định bằng --n-components"
    else:
        n_selected, rule = max(n_by_variance, 2), f"phương sai tích lũy ≥ {args.variance_target:.0%}, tối thiểu 2 PC"
    n_selected = min(n_selected, len(components))

    output = pd.DataFrame(scores[:, :n_selected], columns=components[:n_selected])
    output.insert(0, "customer_id", features["customer_id"].to_numpy())
    output.to_csv(PCA_SCORES_PATH, index=False)
    variance.to_csv(OUTPUT_DIR / "pca_explained_variance.csv", index=False)
    loadings.rename_axis("feature").to_csv(OUTPUT_DIR / "pca_loadings.csv")
    correlation.rename_axis("feature").to_csv(OUTPUT_DIR / "pca_feature_correlation.csv")

    meta = {
        "input_file": str(FEATURES_PATH.relative_to(ROOT)),
        "customer_count": len(features),
        "features": feature_columns,
        "bartlett_chi2": bartlett_chi2,
        "bartlett_p": bartlett_p,
        "kmo": kmo_value,
        "variance_target": args.variance_target,
        "n_by_variance": n_by_variance,
        "n_by_kaiser": n_by_kaiser,
        "n_components_selected": n_selected,
        "selection_rule": rule,
        "cumulative_variance_selected_pct": float(variance["cumulative_pct"].iloc[n_selected - 1]),
        "sign_convention": f"loading of {anchor} is positive on every PC",
        "whiten": False,
    }
    (OUTPUT_DIR / "pca_metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    plot_correlation(correlation)
    plot_scree(variance, n_selected, args.variance_target)
    plot_loadings(loadings)
    plot_projection(scores, loadings, variance)
    write_report(meta, variance, loadings, correlation)

    print(variance.round(3).to_string(index=False))
    print(f"\nBartlett p={bartlett_p:.2g}, KMO={kmo_value:.2f}")
    print(f"Selected {n_selected} PCs ({rule}) → {PCA_SCORES_PATH}")
    print(f"Report: {PCA_REPORT_PATH}")


if __name__ == "__main__":
    main()
