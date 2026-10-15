"""Bước 5/6 — K-Means. PHẦN TỰ ĐIỀU CHỈNH: chạy với k đã chọn ở bước 4 (04_select_k.py).

Đầu vào : customer_pca_scores.csv (mặc định, từ bước 3) hoặc customer_features_transformed.csv (--input scaled)
Đầu ra bắt buộc : customer_segments.csv với 2 cột `customer_id`, `cluster` — bước 6 đọc file này.
Đầu ra phụ      : customer_cluster_evaluation.csv (inertia/silhouette theo k)
"""

from __future__ import annotations

import argparse

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from config import (
    CLUSTER_EVALUATION_PATH,
    FEATURES_PATH,
    PCA_SCORES_PATH,
    RANDOM_STATE,
    SEGMENTS_PATH,
    require_file,
)

INPUTS = {"pca": (PCA_SCORES_PATH, "03_pca_analysis.py"), "scaled": (FEATURES_PATH, "02_transform_features.py")}
SILHOUETTE_SAMPLE_SIZE = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, help="Use a fixed cluster count instead of silhouette selection")
    parser.add_argument("--min-k", type=int, default=2)
    parser.add_argument("--max-k", type=int, default=8)
    parser.add_argument("--input", choices=INPUTS, default="pca", help="Đặc trưng đưa vào K-Means")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path, producer = INPUTS[args.input]
    require_file(input_path, producer)
    transformed = pd.read_csv(input_path)
    if "customer_id" not in transformed:
        raise ValueError(f"{input_path.name} must contain customer_id")
    feature_columns = [column for column in transformed.columns if column != "customer_id"]
    if not feature_columns or transformed[feature_columns].isna().any().any():
        raise ValueError("Transformed feature matrix is empty or contains missing values")
    if transformed["customer_id"].duplicated().any():
        raise ValueError("Transformed features contain duplicate customer_id values")

    features = transformed[feature_columns].to_numpy()
    customer_count = len(transformed)
    if customer_count < 3:
        raise ValueError("At least three purchasing customers are required to evaluate clusters")

    selected_k = args.k
    evaluation_rows: list[dict[str, float | int]] = []
    if selected_k is None:
        if args.min_k < 2 or args.max_k < args.min_k:
            raise ValueError("Expected 2 <= min-k <= max-k")
        max_k = min(args.max_k, customer_count - 1)
        if max_k < args.min_k:
            raise ValueError("Not enough customers for the requested cluster-count range")
        for k in range(args.min_k, max_k + 1):
            model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
            labels = model.fit_predict(features)
            score = silhouette_score(
                features,
                labels,
                sample_size=min(SILHOUETTE_SAMPLE_SIZE, customer_count - 1),
                random_state=RANDOM_STATE,
            )
            evaluation_rows.append(
                {"k": k, "inertia": float(model.inertia_), "silhouette": float(score)}
            )
            print(f"k={k}: inertia={model.inertia_:,.2f}, sampled silhouette={score:.4f}")
        selected_k = max(evaluation_rows, key=lambda row: row["silhouette"])["k"]
    elif selected_k < 2 or selected_k >= customer_count:
        raise ValueError(f"k must be between 2 and {customer_count - 1}")

    final_model = KMeans(n_clusters=selected_k, random_state=RANDOM_STATE, n_init=10)
    labels = final_model.fit_predict(features)
    assignments = transformed[["customer_id"]].copy()
    assignments["cluster"] = labels
    assignments.to_csv(SEGMENTS_PATH, index=False)

    if evaluation_rows:
        pd.DataFrame(evaluation_rows).to_csv(CLUSTER_EVALUATION_PATH, index=False)

    print(f"Selected k={selected_k} on {args.input} features; labels saved to {SEGMENTS_PATH}")
    print("Next: python customer_segmentation/06_cluster_profiling.py")


if __name__ == "__main__":
    main()
