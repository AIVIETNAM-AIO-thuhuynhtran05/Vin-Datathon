"""Bước 2/2 — Huấn luyện, cross-validation, ensemble phân tầng, calibration, giải thích (SHAP) và file nộp.

Mô hình (mỗi mô hình train trên log(target), cho cả Revenue và COGS):
  M1  Ridge + Fourier              — tuyến tính, ổn định, làm "anchor".
  M2  LightGBM high_era            — trọng số 1.0 cho 2014–2018, 0.01 cho phần còn lại; train 2 giai đoạn.
  M2q 4 Q-specialist LightGBM      — như M2, nhân trọng số ×2 cho quý phụ trách; ghép theo quý của từng ngày.
  M3  Prophet + promos             — học từ 2020 (tối thiểu 2 năm gần nhất), regressor là cửa sổ khuyến mãi.
Ensemble:
  Tầng 1  LGB_blend = (1 − α)·M2 + α·M2q
  Tầng 2  raw = w1·M1 + w3·M3 + w2·LGB_blend          (α, w chọn trên CV theo MAE hình dạng)
  Tầng 3  final = c × raw                              (c ước lượng từ fold A: mức thật 2022 / mức dự báo 2022)

Đầu ra : forecasting/submission.csv, data/processed/forecasting/*.csv|json, plots/model_*.png,
         reports/markdown/forecasting_models.md
Chạy    : python forecasting/02_train_forecast.py
"""

from __future__ import annotations

import itertools
import json
import logging

import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import (COLORS, FOLDS, HIGH_ERA, LOW_WEIGHT, MODEL_REPORT_PATH, MUTED, OUTPUT_DIR, PLOT_DIR, PLOT_LINK,
                    QBOOST, SEED, SUBMISSION_PATH, TARGETS, TEST_END, TEST_START, apply_style)
from features import build_features, feature_columns, feature_group, load_sales, promo_schedule

logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)

LGB_PARAMS = dict(objective="regression", metric="mae", learning_rate=0.03, num_leaves=63, min_data_in_leaf=30,
                  feature_fraction=0.85, bagging_fraction=0.85, bagging_freq=5, lambda_l2=1.0, seed=SEED,
                  deterministic=True, force_row_wise=True, num_threads=4, verbosity=-1)
RIDGE_ALPHA = 3.0
COMPONENTS = ["ridge", "prophet", "lgb_base", "lgb_spec"]
COMPONENT_NAMES = {"ridge": "M1 Ridge + Fourier", "prophet": "M3 Prophet + promos", "lgb_base": "M2 LightGBM high_era",
                   "lgb_spec": "M2q 4 Q-specialists", "ensemble_raw": "Ensemble (chưa calibration)",
                   "ensemble_cal": "Ensemble + calibration", "naive": "Seasonal naive (cùng thứ, năm trước)"}


# --------------------------------------------------------------------------------------------- models


def era_weights(frame: pd.DataFrame, quarter: int | None = None) -> np.ndarray:
    weights = np.where(frame["year"].between(*HIGH_ERA), 1.0, LOW_WEIGHT)
    if quarter is not None:
        weights = weights * np.where(frame["quarter"] == quarter, QBOOST, 1.0)
    return weights


def fit_ridge(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], target: str) -> np.ndarray:
    mu, sigma = train[cols].mean(), train[cols].std().replace(0, 1)
    model = Ridge(alpha=RIDGE_ALPHA, random_state=SEED).fit((train[cols] - mu) / sigma, np.log(train[target]))
    return np.exp(model.predict((test[cols] - mu) / sigma))


def fit_lgb(train: pd.DataFrame, cols: list[str], target: str, weights: np.ndarray) -> lgb.Booster:
    """Giai đoạn 1: early stopping trên 180 ngày cuối; giai đoạn 2: train lại toàn bộ với best_iteration."""
    y = np.log(train[target].to_numpy())
    cutoff = train["Date"].max() - pd.Timedelta(days=180)
    fit_idx = (train["Date"] <= cutoff).to_numpy()
    booster_es = lgb.train(
        LGB_PARAMS, lgb.Dataset(train.loc[fit_idx, cols], y[fit_idx], weight=weights[fit_idx]),
        num_boost_round=5000, valid_sets=[lgb.Dataset(train.loc[~fit_idx, cols], y[~fit_idx])],
        callbacks=[lgb.early_stopping(300, verbose=False), lgb.log_evaluation(0)],
    )
    rounds = max(booster_es.best_iteration, 50)
    return lgb.train(LGB_PARAMS, lgb.Dataset(train[cols], y, weight=weights), num_boost_round=rounds)


def fit_prophet(train: pd.DataFrame, test: pd.DataFrame, target: str, promo_cols: list[str]) -> np.ndarray:
    from prophet import Prophet

    # Học từ 2020 (regime mới); nếu train kết thúc sớm thì lùi về để luôn có ≥ 2 năm cho mùa vụ năm.
    start = min(pd.Timestamp("2020-01-01"), train["Date"].max() - pd.DateOffset(years=2) + pd.Timedelta(days=1))
    recent = train[train["Date"] >= start]
    frame = recent[["Date", *promo_cols]].rename(columns={"Date": "ds"}).assign(y=np.log(recent[target].to_numpy()))
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False,
                    seasonality_mode="multiplicative", changepoint_prior_scale=0.05)
    for column in promo_cols:
        model.add_regressor(column)
    model.fit(frame)
    future = test[["Date", *promo_cols]].rename(columns={"Date": "ds"})
    return np.exp(model.predict(future)["yhat"].to_numpy())


def fit_components(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], target: str,
                   promo_cols: list[str]) -> tuple[dict[str, np.ndarray], lgb.Booster]:
    print(f"  train đến {train['Date'].max().date()} · {target}", flush=True)
    base = fit_lgb(train, cols, target, era_weights(train))
    spec = np.zeros(len(test))
    for quarter in (1, 2, 3, 4):
        booster = fit_lgb(train, cols, target, era_weights(train, quarter))
        mask = (test["quarter"] == quarter).to_numpy()
        spec[mask] = np.exp(booster.predict(test.loc[mask, cols]))
    predictions = {
        "ridge": fit_ridge(train, test, cols, target),
        "prophet": fit_prophet(train, test, target, promo_cols),
        "lgb_base": np.exp(base.predict(test[cols])),
        "lgb_spec": spec,
    }
    return predictions, base


def blend(p: dict[str, np.ndarray], alpha: float, weights: tuple[float, float, float]) -> np.ndarray:
    w_ridge, w_prophet, w_lgb = weights
    lgb_blend = (1 - alpha) * p["lgb_base"] + alpha * p["lgb_spec"]
    return w_ridge * p["ridge"] + w_prophet * p["prophet"] + w_lgb * lgb_blend


# -------------------------------------------------------------------------------------------- metrics


def metrics(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    return {"MAE": mean_absolute_error(y, pred), "RMSE": float(np.sqrt(mean_squared_error(y, pred))),
            "R2": r2_score(y, pred)}


def shape_mae(y: np.ndarray, pred: np.ndarray) -> float:
    """MAE sau khi đưa dự báo về đúng mức tổng của tập validate: đo hình dạng, tách khỏi vấn đề mức."""
    return mean_absolute_error(y, pred * y.sum() / pred.sum())


def seasonal_naive(history: pd.DataFrame, dates: pd.Series, target: str) -> np.ndarray:
    lookup = history.set_index("Date")[target]
    values = []
    for day in dates:
        for lag in (364, 728):  # cùng thứ trong tuần, năm trước (hoặc hai năm trước nếu năm trước nằm trong horizon)
            past = day - pd.Timedelta(days=lag)
            if past in lookup.index:
                values.append(lookup[past])
                break
        else:
            values.append(lookup.iloc[-1])
    return np.array(values)


# ------------------------------------------------------------------------------------------------ main


def main() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()
    sales = load_sales()
    schedule = promo_schedule()
    data = build_features(sales["Date"], schedule).merge(sales, on="Date")
    cols = feature_columns(data)
    promo_cols = [c for c in cols if c.startswith("promo_") and not c.endswith(("_since", "_until", "_disc"))]

    # --- Cross-validation theo thời gian
    cv_preds: dict[tuple[str, str], dict[str, np.ndarray]] = {}
    cv_truth: dict[tuple[str, str], np.ndarray] = {}
    for fold, train_end, val_start, val_end in FOLDS:
        train = data[data["Date"] <= train_end].reset_index(drop=True)
        val = data[data["Date"].between(val_start, val_end)].reset_index(drop=True)
        for target in TARGETS:
            preds, _ = fit_components(train, val, cols, target, promo_cols)
            preds["naive"] = seasonal_naive(train, val["Date"], target)
            cv_preds[(fold, target)] = preds
            cv_truth[(fold, target)] = val[target].to_numpy()
            print(f"Fold {fold} · {target}: " + ", ".join(
                f"{k} MAE {mean_absolute_error(val[target], v):,.0f}" for k, v in preds.items()))

    # --- Chọn α và trọng số 3 họ mô hình theo MAE hình dạng (chuẩn hóa theo mức trung bình), trung bình mọi fold & target
    grid = [w for w in itertools.product(np.arange(0, 1.0001, 0.05), repeat=3) if abs(sum(w) - 1) < 1e-9]
    best = None
    for alpha in np.arange(0, 1.0001, 0.1):
        for weights in grid:
            score = np.mean([shape_mae(cv_truth[k], blend(p, alpha, weights)) / cv_truth[k].mean()
                             for k, p in cv_preds.items()])
            if best is None or score < best[0]:
                best = (score, round(float(alpha), 2), tuple(round(float(w), 2) for w in weights))
    _, alpha, weights = best

    # --- Calibration mức: c = tổng thật / tổng dự báo trên fold A (2022). Đánh giá trung thực: áp hệ số của fold B lên fold A.
    calib = {t: float(cv_truth[("A", t)].sum() / blend(cv_preds[("A", t)], alpha, weights).sum()) for t in TARGETS}
    calib_b = {t: float(cv_truth[("B", t)].sum() / blend(cv_preds[("B", t)], alpha, weights).sum()) for t in TARGETS}

    rows = []
    for (fold, target), preds in cv_preds.items():
        y = cv_truth[(fold, target)]
        raw = blend(preds, alpha, weights)
        candidates = {**{k: preds[k] for k in [*COMPONENTS, "naive"]}, "ensemble_raw": raw}
        if fold == "A":
            candidates["ensemble_cal"] = raw * calib_b[target]
        for name, pred in candidates.items():
            rows.append({"fold": fold, "target": target, "model": name, **metrics(y, pred),
                         "shape_MAE": shape_mae(y, pred), "level_ratio": float(pred.sum() / y.sum())})
    cv_table = pd.DataFrame(rows)
    cv_table.to_csv(OUTPUT_DIR / "cv_metrics.csv", index=False)

    # Tương quan sai số giữa các họ mô hình (đo diversity), trên fold A Revenue
    residuals = {k: cv_preds[("A", "Revenue")][k] - cv_truth[("A", "Revenue")] for k in ["ridge", "prophet", "lgb_base"]}
    diversity = {f"{a} vs {b}": float(np.corrcoef(residuals[a], residuals[b])[0, 1])
                 for a, b in itertools.combinations(residuals, 2)}

    # --- Huấn luyện cuối trên toàn bộ 2012–2022 và dự báo 548 ngày
    test = build_features(pd.date_range(TEST_START, TEST_END), schedule)
    final, boosters = {}, {}
    for target in TARGETS:
        preds, boosters[target] = fit_components(data, test, cols, target, promo_cols)
        raw = blend(preds, alpha, weights)
        final[target] = raw * calib[target]
        final[f"{target}_raw"] = raw
    submission = pd.DataFrame({"Date": test["Date"].dt.strftime("%Y-%m-%d"),
                               "Revenue": np.round(final["Revenue"], 2), "COGS": np.round(final["COGS"], 2)})
    assert len(submission) == 548 and submission[["Revenue", "COGS"]].gt(0).all().all()
    submission.to_csv(SUBMISSION_PATH, index=False)

    shap_result = explain(boosters, test, cols)
    plot_forecast(data, test, final)
    plot_cv(cv_table)

    summary = {
        "alpha": alpha, "weights": dict(zip(["ridge", "prophet", "lgb_blend"], weights)),
        "calibration": {t: round(v, 3) for t, v in calib.items()},
        "calibration_from_fold_B": {t: round(v, 3) for t, v in calib_b.items()},
        "diversity_corr": {k: round(v, 3) for k, v in diversity.items()},
        "forecast_total": {t: {"2023": float(final[t][test["year"] == 2023].sum()),
                               "2024H1": float(final[t][((test["year"] == 2024) & (test["Date"] < "2024-07-01")).to_numpy()].sum())}
                           for t in TARGETS},
        "actual_total": {t: {str(y): float(data.loc[data["year"] == y, t].sum()) for y in (2021, 2022)} for t in TARGETS},
        "actual_2022H1": {t: float(data.loc[(data["year"] == 2022) & (data["month"] <= 6), t].sum()) for t in TARGETS},
        "n_features": len(cols),
        **shap_result,
    }
    (OUTPUT_DIR / "forecast_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(cv_table, summary, schedule)
    print(json.dumps({k: summary[k] for k in ["alpha", "weights", "calibration", "calibration_from_fold_B",
                                              "diversity_corr", "forecast_total"]}, indent=2))
    print(f"Submission: {SUBMISSION_PATH} · Report: {MODEL_REPORT_PATH}")


# --------------------------------------------------------------------------------------------- explain


def explain(boosters: dict[str, lgb.Booster], test: pd.DataFrame, cols: list[str]) -> dict:
    """TreeSHAP (pred_contrib) trên base LightGBM — họ cây chiếm phần lớn trọng số ensemble."""
    groups = [feature_group(c) for c in cols]
    group_pct, additivity = {}, {}
    contrib_rev = None
    for target, booster in boosters.items():
        contrib = booster.predict(test[cols], pred_contrib=True)
        sv, base_value = contrib[:, :-1], contrib[0, -1]
        additivity[target] = float(np.max(np.abs(base_value + sv.sum(1) - booster.predict(test[cols]))))
        mean_abs = np.abs(sv).mean(0)
        totals: dict[str, float] = {}
        for group, value in zip(groups, mean_abs):
            totals[group] = totals.get(group, 0.0) + value
        total = sum(totals.values())
        group_pct[target] = {g: round(100 * v / total, 1) for g, v in sorted(totals.items(), key=lambda x: -x[1])}
        if target == "Revenue":
            contrib_rev = sv

    # Hiệu ứng cục bộ trên Revenue: chênh lệch tổng (mọi đặc trưng) và SHAP cô lập của riêng nhóm driver
    def gidx(group: str) -> list[int]:
        return [i for i, g in enumerate(groups) if g == group]

    def eff_total(a: np.ndarray, b: np.ndarray) -> float:
        return 100 * float(np.expm1(contrib_rev[a].sum(1).mean() - contrib_rev[b].sum(1).mean()))

    def eff_iso(group: str, a: np.ndarray, b: np.ndarray) -> float:
        c = contrib_rev[:, gidx(group)].sum(1)
        return 100 * float(np.expm1(c[a].mean() - c[b].mean()))

    t = test.reset_index(drop=True)
    a_eom, b_eom = (t["is_last1"] == 1).to_numpy(), t["day"].between(13, 17).to_numpy()
    a_tet, b_tet = (t["tet_in_7"] == 1).to_numpy(), (t["tet_days_diff"].abs() > 30).to_numpy()
    grid = build_features(pd.date_range("2023-01-01", "2024-12-31"))
    glog = boosters["Revenue"].predict(grid[cols])
    sv_grid = boosters["Revenue"].predict(grid[cols], pred_contrib=True)[:, :-1]
    aug_even = ((grid["month"] == 8) & (grid["is_odd_year"] == 0)).to_numpy()
    aug_odd = ((grid["month"] == 8) & (grid["is_odd_year"] == 1)).to_numpy()
    yp = sv_grid[:, gidx("Year-parity")].sum(1)
    local = [
        {"driver": "Ngày cuối tháng vs giữa tháng (13–17)", "total": eff_total(a_eom, b_eom),
         "isolated": eff_iso("Edge-of-month", a_eom, b_eom)},
        {"driver": "±7 ngày quanh Tết vs cách Tết > 30 ngày", "total": eff_total(a_tet, b_tet),
         "isolated": eff_iso("Tết", a_tet, b_tet)},
        {"driver": "Tháng 8 năm chẵn (2024) vs năm lẻ (2023)",
         "total": 100 * float(np.expm1(glog[aug_even].mean() - glog[aug_odd].mean())),
         "isolated": 100 * float(np.expm1(yp[aug_even].mean() - yp[aug_odd].mean()))},
    ]
    plot_shap(group_pct, contrib_rev, t, cols, grid, glog)
    return {"shap_group_pct": group_pct, "shap_additivity_error": additivity, "local_effects": local}


# ----------------------------------------------------------------------------------------------- plots


def plot_shap(group_pct: dict, sv: np.ndarray, t: pd.DataFrame, cols: list[str], grid: pd.DataFrame,
              glog: np.ndarray) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12.5, 4.2))
    for axis, target in zip(axes, TARGETS):
        names, values = list(group_pct[target]), list(group_pct[target].values())
        axis.barh(names[::-1], values[::-1], color=COLORS[0], height=0.62)
        for y, v in enumerate(values[::-1]):
            axis.text(v + 0.6, y, f"{v:.1f}%", va="center", fontsize=8)
        axis.set_xlim(0, max(values) * 1.18)
        axis.set_title(f"{target}: đóng góp theo nhóm (% tổng mean|SHAP|)", loc="left")
        axis.grid(axis="y", visible=False)
    figure.savefig(PLOT_DIR / "model_shap_groups.png", dpi=130, bbox_inches="tight")
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(14, 4))
    i_eom, i_tet = cols.index("days_to_eom"), cols.index("tet_days_diff")
    axes[0].scatter(t["days_to_eom"], sv[:, i_eom], s=10, color=COLORS[0], alpha=0.7)
    axes[0].set_xlabel("days_to_eom (0 = ngày cuối tháng)")
    axes[0].set_ylabel("SHAP (log)")
    axes[0].set_title("(a) Cuối tháng", loc="left")
    near = (t["tet_days_diff"].abs() <= 45).to_numpy()
    axes[1].scatter(t.loc[near, "tet_days_diff"], sv[near, i_tet], s=10, color=COLORS[1], alpha=0.7)
    axes[1].set_xlabel("tet_days_diff (0 = mùng 1 Tết)")
    axes[1].set_title("(b) Tết Âm lịch (±45 ngày)", loc="left")
    monthly = pd.Series(np.exp(glog) / 1e6).groupby([grid["year"], grid["month"]]).mean()
    axes[2].plot(range(1, 13), monthly.loc[2024].values, color=COLORS[0], marker="o", label="Năm chẵn (2024)")
    axes[2].plot(range(1, 13), monthly.loc[2023].values, color=COLORS[1], marker="s", linestyle="--", label="Năm lẻ (2023)")
    axes[2].set_xticks(range(1, 13))
    axes[2].set_xlabel("Tháng")
    axes[2].set_ylabel("Base LGB dự báo (triệu, chưa calibration)")
    axes[2].set_title("(c) Năm chẵn / lẻ", loc="left")
    axes[2].legend()
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "model_shap_local.png", dpi=130)
    plt.close(figure)


def plot_forecast(data: pd.DataFrame, test: pd.DataFrame, final: dict) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(12, 6.4), sharex=True)
    history = data[data["Date"] >= "2020-01-01"]
    for axis, target, color in zip(axes, TARGETS, [COLORS[0], COLORS[1]]):
        axis.plot(history["Date"], history[target] / 1e6, color=MUTED, linewidth=0.7, label="Thực tế 2020–2022")
        axis.plot(test["Date"], final[target] / 1e6, color=color, linewidth=1, label="Dự báo 2023–2024")
        axis.axvline(pd.Timestamp(TEST_START), color=MUTED, linestyle="--", linewidth=1)
        axis.set_ylabel(f"{target} (triệu)")
        axis.set_title(f"{target}: thực tế và dự báo", loc="left")
        axis.legend(loc="upper left")
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "model_forecast.png", dpi=130)
    plt.close(figure)


def plot_cv(cv: pd.DataFrame) -> None:
    order = ["naive", "ridge", "prophet", "lgb_base", "lgb_spec", "ensemble_raw"]
    data = cv[(cv["target"] == "Revenue") & cv["model"].isin(order)].pivot(index="model", columns="fold", values="shape_MAE")
    data = data.reindex(order) / 1e6
    figure, axis = plt.subplots(figsize=(10, 4))
    x = np.arange(len(order))
    for i, (fold, color) in enumerate(zip(["A", "B", "C"], COLORS)):
        axis.bar(x + (i - 1) * 0.26, data[fold], width=0.24, color=color, label=f"Fold {fold}", edgecolor="white")
    axis.set_xticks(x, [COMPONENT_NAMES[m].split(" (")[0] for m in order], rotation=12, fontsize=8)
    axis.set_ylabel("MAE hình dạng (triệu)")
    axis.set_title("Revenue: MAE hình dạng theo fold (thấp = tốt)", loc="left")
    axis.legend(ncol=3)
    figure.tight_layout()
    figure.savefig(PLOT_DIR / "model_cv.png", dpi=130)
    plt.close(figure)


# ---------------------------------------------------------------------------------------------- report


def fmt(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


def write_report(cv: pd.DataFrame, s: dict, schedule: list[dict]) -> None:
    p = PLOT_LINK
    w = s["weights"]
    mean_cv = cv[cv["model"] != "ensemble_cal"].groupby(["target", "model"])[["MAE", "RMSE", "R2", "shape_MAE",
                                                                              "level_ratio"]].mean()
    fold_a = cv[cv["fold"] == "A"].set_index(["target", "model"])
    lines = [
        "# Dự báo doanh thu — Mô hình, đánh giá và giải thích",
        "",
        "Tạo tự động bởi `forecasting/02_train_forecast.py`. Phân tích dữ liệu nằm ở báo cáo trước "
        "([`forecasting_eda.md`](forecasting_eda.md)); mọi con số dưới đây là kết quả chạy thật, `random_state = 42`.",
        "",
        "## 4. Feature engineering",
        "",
        f"Mọi đặc trưng tính được từ ngày tháng (`forecasting/features.py`), tổng cộng **{s['n_features']} đặc trưng**, "
        "nên ma trận đặc trưng cho 2023–2024 dựng sẵn được mà không cần doanh thu của test:",
        "",
        "| Nhóm | Đặc trưng | Từ quan sát nào |",
        "|---|---|---|",
        "| Lịch cơ bản | năm, tháng, ngày, thứ, ngày trong năm, quý, cuối tuần | Mùa vụ năm, thứ trong tuần (mục 3.2, 3.3) |",
        "| Đầu / cuối tháng | `is_first1..3`, `is_last1..3`, `days_to_eom`, `days_from_som` | Cuối tháng cao gấp đôi giữa tháng (3.3b) |",
        "| Xu hướng + chế độ | `t_days`, `regime_pre2019`, `regime_2019`, `regime_post2019` | Regime drift (3.1) |",
        "| Fourier | sin/cos năm k = 1..5, tuần và tháng k = 1..2 | Hình dạng mùa vụ bền vững (3.2) |",
        "| Lễ | 10 ngày lễ dương lịch cố định ở Việt Nam, Black Friday | Ngày mua sắm |",
        "| Tết Âm lịch | `tet_days_diff`, `tet_in_7`, `tet_in_14`, `tet_before_7`, `tet_after_7`, `tet_on` | Hiệu ứng Tết (3.3a) |",
        f"| Khuyến mãi | trạng thái, số ngày đã/còn lại và mức giảm của {len(schedule)} chiến dịch | Lịch khuyến mãi |",
        "| Năm lẻ | `is_odd_year` | Chu kỳ chẵn/lẻ, margin Q3 (3.3c, 3.4) |",
        "",
        "**Lịch khuyến mãi suy từ `promotions.csv`** (không dùng dữ liệu ngoài): mỗi chiến dịch lặp lại cùng ngày bắt đầu và "
        "thời lượng mỗi năm.",
        "",
        "| Chiến dịch | Bắt đầu | Thời lượng | Mức giảm | Lặp lại |",
        "|---|---|---:|---:|---|",
        *[f"| `{x['name']}` | {x['day']:02d}/{x['month']:02d} | {x['duration']} ngày | {x['discount']:g} | "
          f"{'chỉ năm lẻ' if x['odd_only'] else 'hằng năm'} |" for x in schedule],
        "",
        "Ngày Tết Âm lịch và ngày lễ là **kiến thức lịch**, không phải bộ dữ liệu bên ngoài.",
        "",
        "## 5. Chiến lược validation",
        "",
        "Ba fold theo thời gian, không xáo trộn dữ liệu:",
        "",
        "| Fold | Train | Validate | Vai trò |",
        "|---|---|---|---|",
        "| A (chính) | ≤ 2021-12 | 2022 | 2022 gần phân phối test nhất; dùng để ước lượng hệ số calibration |",
        "| B (ổn định) | ≤ 2020-12 | 2021 | Kiểm tra cải tiến có ổn định qua năm không |",
        "| C (horizon) | ≤ 2021-06 | 2021-07 → 2022-06 | Cửa sổ 12 tháng liên tục, gần horizon thật |",
        "",
        "Hai thước đo: **MAE/RMSE/R² thông thường** và **MAE hình dạng** (đưa dự báo về đúng tổng của tập validate "
        "trước khi tính MAE). MAE hình dạng tách được chất lượng *hình dạng* khỏi vấn đề *mức*, vốn do tầng calibration xử lý.",
        "",
        "## 6. Lựa chọn và huấn luyện mô hình",
        "",
        "Ba họ mô hình khác bản chất để ensemble có diversity:",
        "",
        "- **M1 Ridge + Fourier:** tuyến tính trên đặc trưng chuẩn hóa z-score, train trên log(target), α = 3. Ổn định, làm *anchor*.",
        f"- **M2 LightGBM high_era:** trọng số 1.0 cho {HIGH_ERA[0]}–{HIGH_ERA[1]}, {LOW_WEIGHT} cho phần còn lại; learning "
        "rate 0.03, 63 lá. Train 2 giai đoạn: early stopping trên 180 ngày cuối để chọn số vòng, rồi train lại trên toàn bộ dữ liệu.",
        f"- **M2q 4 Q-specialist:** cùng cấu hình M2, nhân trọng số ×{QBOOST:g} cho quý phụ trách. Khi dự báo, mỗi ngày lấy "
        "dự báo của specialist đúng quý của ngày đó (không lấy trung bình). Tổng cộng 4 quý × 2 target = 8 mô hình.",
        "- **M3 Prophet + promos:** học từ 2020 trở đi (trend không bị bước nhảy 2019 bóp méo); fold nào train kết thúc sớm "
        "thì lùi về đủ 2 năm gần nhất để mùa vụ năm không bị thiếu dữ liệu. Mùa vụ năm và tuần "
        "dạng multiplicative, regressor là cửa sổ của các chiến dịch khuyến mãi.",
        "",
        "**Diversity** (tương quan sai số trên fold A, Revenue): " + ", ".join(
            f"{k.replace('lgb_base', 'LGB').replace('ridge', 'Ridge').replace('prophet', 'Prophet')} = {v:.2f}"
            for k, v in s["diversity_corr"].items()) + ".",
        "",
        "## 7. Ensemble phân tầng và calibration",
        "",
        "| Tầng | Công thức | Tham số |",
        "|---|---|---|",
        f"| 1. Hợp nhất họ LightGBM | LGB_blend = (1 − α)·M2 + α·M2q | α = {s['alpha']:.2f} |",
        f"| 2. Hợp nhất 3 họ | raw = w₁·M1 + w₃·M3 + w₂·LGB_blend | w₁ = {w['ridge']:.2f}, w₃ = {w['prophet']:.2f}, w₂ = {w['lgb_blend']:.2f} |",
        f"| 3. Calibration mức | final = c × raw | c<sub>Revenue</sub> = {s['calibration']['Revenue']:.3f}, c<sub>COGS</sub> = {s['calibration']['COGS']:.3f} |",
        "",
        "- **α và trọng số** chọn bằng lưới (bước 0.1 cho α, 0.05 cho trọng số) để tối thiểu **MAE hình dạng** trung bình "
        "trên 3 fold và cả 2 target.",
        "- **Calibration:** c = tổng thực tế 2022 ÷ tổng dự báo 2022 của mô hình train đến 2021 (fold A), rồi áp cho mô hình "
        "train đến 2022 dự báo 2023–2024. Hệ số tách khỏi tầng blend vì vấn đề *mức* khác vấn đề *hình dạng*.",
        "- **Khác tài liệu tham chiếu:** tài liệu chỉnh c trực tiếp trên Leaderboard. Ở đây không dùng Leaderboard; c ước "
        "lượng hoàn toàn từ dữ liệu train, nên không có rò rỉ từ test.",
        "",
        "## 8. Kết quả cross-validation",
        "",
        f"![CV]({p}/model_cv.png)",
        "",
    ]
    for target in TARGETS:
        lines += [
            f"**{target}: trung bình 3 fold**",
            "",
            "| Mô hình | MAE | RMSE | R² | MAE hình dạng | Mức dự báo / thực tế |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for model in ["naive", *COMPONENTS, "ensemble_raw"]:
            r = mean_cv.loc[(target, model)]
            lines.append(f"| {COMPONENT_NAMES[model]} | {fmt(r['MAE'])} | {fmt(r['RMSE'])} | {r['R2']:.3f} | "
                         f"{fmt(r['shape_MAE'])} | {r['level_ratio']:.2f} |")
        lines.append("")
    lines += [
        "**Đánh giá trung thực của tầng calibration (fold A, 2022):** áp hệ số ước lượng từ fold B (năm 2021) lên dự báo "
        "2022, mô phỏng đúng cách hệ số được dùng cho 2023–2024.",
        "",
        "| Target | Mô hình | MAE | RMSE | R² |",
        "|---|---|---:|---:|---:|",
    ]
    for target in TARGETS:
        for model in ["naive", "ensemble_raw", "ensemble_cal"]:
            r = fold_a.loc[(target, model)]
            lines.append(f"| {target} | {COMPONENT_NAMES[model]} | {fmt(r['MAE'])} | {fmt(r['RMSE'])} | {r['R2']:.3f} |")
    lines += [
        "",
        f"Hệ số ước lượng từ fold B: c<sub>Revenue</sub> = {s['calibration_from_fold_B']['Revenue']:.3f}, "
        f"c<sub>COGS</sub> = {s['calibration_from_fold_B']['COGS']:.3f}.",
        "",
        "## 9. Khả năng giải thích mô hình (SHAP)",
        "",
        "Giải thích **base LightGBM** cuối (train trên toàn bộ 2012–2022), đại diện cho họ cây trong ensemble. TreeSHAP "
        "tính trực tiếp qua `predict(pred_contrib=True)`, chính xác cho mô hình cây. Kiểm tra tính cộng tính "
        f"(base value + Σ SHAP = dự báo log): sai số lớn nhất {max(s['shap_additivity_error'].values()):.1e}. Vì mô hình "
        "học trên log, đóng góp Δ quy ra phần trăm doanh thu theo e<sup>Δ</sup> − 1.",
        "",
        "### 9.1. Global importance",
        "",
        f"![SHAP nhóm]({p}/model_shap_groups.png)",
        "",
        "| Nhóm pattern | Revenue (%) | COGS (%) |",
        "|---|---:|---:|",
        *[f"| {g} | {v:.1f} | {s['shap_group_pct']['COGS'].get(g, 0.0):.1f} |" for g, v in s["shap_group_pct"]["Revenue"].items()],
        "",
        "### 9.2. Local effect",
        "",
        f"![SHAP cục bộ]({p}/model_shap_local.png)",
        "",
        "Global importance đo trung bình trên cả 548 ngày, nên pattern hiếm như Tết có global thấp dù tác động cục bộ rõ. "
        "Bảng dưới đo tác động ngay tại những ngày pattern xuất hiện: *chênh lệch tổng* cộng SHAP của mọi đặc trưng, "
        "*SHAP cô lập* chỉ cộng nhóm đặc trưng của driver.",
        "",
        "| Driver | Chênh lệch dự báo tổng | SHAP cô lập của nhóm driver |",
        "|---|---:|---:|",
        *[f"| {x['driver']} | {x['total']:+.1f}% | {x['isolated']:+.1f}% |" for x in s["local_effects"]],
        "",
        "## 10. Dự báo và ý nghĩa kinh doanh",
        "",
        f"![Dự báo]({p}/model_forecast.png)",
        "",
        "| Target | Thực tế 2021 | Thực tế 2022 | Dự báo 2023 | Thực tế 6 tháng đầu 2022 | Dự báo 6 tháng đầu 2024 |",
        "|---|---:|---:|---:|---:|---:|",
        *[f"| {t} | {s['actual_total'][t]['2021'] / 1e9:.2f} tỷ | {s['actual_total'][t]['2022'] / 1e9:.2f} tỷ | "
          f"{s['forecast_total'][t]['2023'] / 1e9:.2f} tỷ | {s['actual_2022H1'][t] / 1e9:.2f} tỷ | "
          f"{s['forecast_total'][t]['2024H1'] / 1e9:.2f} tỷ |" for t in TARGETS],
        "",
        "File nộp: [`forecasting/submission.csv`](../../forecasting/submission.csv), 548 dòng `Date, Revenue, COGS`, "
        "theo thứ tự ngày từ 2023-01-01 đến 2024-07-01.",
        "",
    ]
    MODEL_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
