"""Bước 2/6 — Feature engineering: log1p + StandardScaler cho 3 biến RFM.

Đầu vào : data/processed/customer_segmentation/customer_analysis_base.csv
Đầu ra  : data/processed/customer_segmentation/customer_features_transformed.csv
          data/processed/customer_segmentation/customer_transform_metadata.json
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from config import CUSTOMER_BASE_PATH, FEATURES_METADATA_PATH, FEATURES_PATH, OUTPUT_DIR, ROOT, RFM_FEATURES, require_file


def main() -> None:
    require_file(CUSTOMER_BASE_PATH, "01_build_customer_dataset.py")
    customers = pd.read_csv(CUSTOMER_BASE_PATH)
    purchasers = customers.loc[customers["has_purchase"].astype(bool)].copy()
    if len(purchasers) < 2:
        raise ValueError("At least two purchasing customers are required for K-Means")

    if purchasers[RFM_FEATURES].isna().any().any():
        raise ValueError("RFM values are missing for customers marked as purchasers")
    if (purchasers[RFM_FEATURES] < 0).any().any():
        raise ValueError("RFM values must be non-negative before log1p transformation")

    numeric_values = np.log1p(purchasers[RFM_FEATURES].astype(float))
    scaler = StandardScaler()
    transformed = scaler.fit_transform(numeric_values)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = pd.DataFrame(transformed, columns=RFM_FEATURES)
    output.insert(0, "customer_id", purchasers["customer_id"].to_numpy())
    output.to_csv(FEATURES_PATH, index=False)

    metadata = {
        "input_file": str(CUSTOMER_BASE_PATH.relative_to(ROOT)),
        "output_file": str(FEATURES_PATH.relative_to(ROOT)),
        "customer_count": int(len(purchasers)),
        "excluded_never_purchased_customers": int(len(customers) - len(purchasers)),
        "numeric_features": RFM_FEATURES,
        "numeric_transform": "log1p followed by StandardScaler",
        "clustering_feature_policy": (
            "Only measurement-based RFM features are used by K-Means. "
            "Demographic and acquisition fields are excluded from the feature matrix "
            "and used only to describe clusters after fitting."
        ),
    }
    FEATURES_METADATA_PATH.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Transformed RFM features: {transformed.shape[0]:,} customers "
        f"x {transformed.shape[1]} measurement features"
    )
    print(f"Saved transformed data to {FEATURES_PATH}")


if __name__ == "__main__":
    main()
