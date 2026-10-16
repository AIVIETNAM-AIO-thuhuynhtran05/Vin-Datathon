"""Bước 1/2 — EDA chuỗi thời gian cho bài toán dự báo Revenue và COGS.

Định lượng các giả định thiết kế: regime drift (cần sample weighting + calibration), mùa vụ năm ổn định về hình dạng
(Fourier), hiệu ứng Tết, đầu/cuối tháng, chu kỳ năm chẵn/lẻ, margin theo quý và quan hệ Revenue–COGS.

Đầu ra : data/processed/forecasting/plots/eda_*.png, data/processed/forecasting/eda_stats.json,
         reports/markdown/forecasting_eda.md
Chạy    : python forecasting/01_time_series_eda.py
"""

from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from config import (COLORS, EDA_REPORT_PATH, ERA_COLORS, MUTED, OUTPUT_DIR, PLOT_DIR, PLOT_LINK, TET_DATES,
                    apply_style, era_of)
from features import load_sales, promo_schedule

MILLION = 1e6
YEAR_RAMP = LinearSegmentedColormap.from_list("years", ["#cde2fb", "#2a78d6", "#0d366b"])


def save(figure: plt.Figure, name: str) -> None:
    figure.tight_layout()
    figure.savefig(PLOT_DIR / f"{name}.png", dpi=130)
    plt.close(figure)


def plot_timeline(s: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 1, figsize=(12, 6.2), sharex=True)
    spans = [("2012-01-01", "2014-01-01"), ("2014-01-01", "2019-01-01"), ("2019-01-01", "2020-01-01"),
             ("2020-01-01", "2023-01-01")]
    for axis, target, color in zip(axes, ["Revenue", "COGS"], [COLORS[0], COLORS[1]]):
        for (start, end), (label, era_color) in zip(spans, ERA_COLORS.items()):
            axis.axvspan(pd.Timestamp(start), pd.Timestamp(end), color=era_color, alpha=0.13, linewidth=0, label=label)
        axis.plot(s["Date"], s[target] / MILLION, color=color, linewidth=0.7)
        axis.set_ylabel(f"{target} (triệu VND)")
        axis.set_title(f"{target} theo ngày, 2012–2022", loc="left")
    axes[0].legend(loc="upper right", ncol=4)
    save(figure, "eda_timeline")


def plot_monthly_by_year(s: pd.DataFrame) -> None:
    monthly = s.groupby([s["Date"].dt.year, s["Date"].dt.month])[["Revenue", "COGS"]].mean() / MILLION
    years = sorted(s["Date"].dt.year.unique())
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for axis, target in zip(axes, ["Revenue", "COGS"]):
        for i, year in enumerate(years):
            data = monthly.loc[year, target]
            axis.plot(data.index, data.values, color=YEAR_RAMP(i / (len(years) - 1)), linewidth=1.4, label=str(year))
        axis.set_xticks(range(1, 13))
        axis.set_xlabel("Tháng")
        axis.set_ylabel(f"{target} trung bình ngày (triệu)")
        axis.set_title(f"Mùa vụ {target} qua các năm", loc="left")
    axes[0].legend(ncol=3, title="Năm (nhạt → đậm)")
    save(figure, "eda_monthly_by_year")


def tet_profile(s: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, value in TET_DATES.items():
        tet = pd.Timestamp(value)
        window = s[(s["Date"] >= tet - pd.Timedelta(days=30)) & (s["Date"] <= tet + pd.Timedelta(days=30))]
        if len(window) == 61:
            rows.append(window.assign(offset=(window["Date"] - tet).dt.days))
    return pd.concat(rows).groupby("offset")[["Revenue", "COGS"]].mean() / MILLION


def plot_tet(profile: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(11, 4.2))
    axis.axvspan(-7, 0, color=COLORS[3], alpha=0.15, linewidth=0, label="Tuần trước Tết")
    axis.axvspan(0, 7, color=COLORS[0], alpha=0.12, linewidth=0, label="Tuần sau Tết")
    axis.axvline(0, color=MUTED, linestyle="--", linewidth=1)
    axis.plot(profile.index, profile["Revenue"], color=COLORS[0], marker="o", markersize=3, label="Revenue")
    axis.plot(profile.index, profile["COGS"], color=COLORS[1], marker="s", markersize=3, label="COGS")
    axis.set_xlabel("Số ngày cách mùng 1 Tết")
    axis.set_ylabel("Trung bình (triệu VND)")
    axis.set_title("Hiệu ứng Tết Âm lịch, trung bình các năm có đủ ±30 ngày", loc="left")
    axis.legend(ncol=4)
    save(figure, "eda_tet")


def plot_calendar(s: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    dow = s.groupby(s["Date"].dt.dayofweek)["Revenue"].mean() / MILLION
    dom = s.groupby(s["Date"].dt.day)["Revenue"].mean() / MILLION
    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    axes[0].bar(names, dow.values, color=[COLORS[0]] * 5 + [COLORS[1]] * 2, edgecolor="white", linewidth=2)
    axes[0].set_title("Doanh thu trung bình theo thứ", loc="left")
    axes[0].set_ylabel("Revenue (triệu)")
    axes[1].bar(dom.index, dom.values, color=COLORS[2], edgecolor="white", linewidth=1)
    axes[1].set_title("Doanh thu trung bình theo ngày trong tháng", loc="left")
    axes[1].set_xlabel("Ngày trong tháng")
    save(figure, "eda_calendar")
    return dow, dom


def plot_parity(s: pd.DataFrame) -> pd.DataFrame:
    frame = s.assign(month=s["Date"].dt.month, odd=s["Date"].dt.year % 2 == 1)
    parity = frame[frame["Date"].dt.year.between(2013, 2022)].groupby(["odd", "month"])["Revenue"].mean().unstack(0) / MILLION
    parity.columns = ["Năm chẵn", "Năm lẻ"]
    figure, axis = plt.subplots(figsize=(10, 4.2))
    axis.plot(parity.index, parity["Năm chẵn"], color=COLORS[0], marker="s", label="Năm chẵn (2014–2022)")
    axis.plot(parity.index, parity["Năm lẻ"], color=COLORS[1], marker="o", label="Năm lẻ (2013–2021)")
    axis.set_xticks(range(1, 13))
    axis.set_xlabel("Tháng")
    axis.set_ylabel("Revenue trung bình ngày (triệu)")
    axis.set_title("Doanh thu theo tháng, tách năm chẵn / năm lẻ", loc="left")
    axis.legend()
    save(figure, "eda_parity")
    return parity


def plot_distribution(s: pd.DataFrame) -> None:
    groups = {"trước 2019": s["Date"].dt.year < 2019, "2019": s["Date"].dt.year == 2019,
              "sau 2019": s["Date"].dt.year > 2019}
    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    for axis, target in zip(axes, ["Revenue", "COGS"]):
        bins = np.linspace(0, s[target].quantile(0.995) / MILLION, 50)
        for (label, mask), color in zip(groups.items(), [COLORS[0], COLORS[3], COLORS[2]]):
            axis.hist(s.loc[mask, target] / MILLION, bins=bins, color=color, alpha=0.6, label=label)
        axis.set_xlabel(f"{target} (triệu VND)")
        axis.set_ylabel("Số ngày")
        axis.set_title(f"Phân phối {target} theo era", loc="left")
        axis.legend()
    save(figure, "eda_distribution")


def plot_margin(s: pd.DataFrame) -> pd.DataFrame:
    quarterly = s.groupby([s["Date"].dt.year, s["Date"].dt.quarter])[["Revenue", "COGS"]].sum()
    ratio = (quarterly["COGS"] / quarterly["Revenue"]).unstack()
    figure, axis = plt.subplots(figsize=(10, 4.2))
    for q, color in zip([1, 2, 3, 4], COLORS):
        axis.plot(ratio.index, ratio[q], color=color, marker="o", label=f"Q{q}")
    axis.axhline(1.0, color=MUTED, linestyle="--", linewidth=1)
    axis.set_ylabel("COGS / Revenue")
    axis.set_title("Tỷ lệ COGS / Revenue theo quý", loc="left")
    axis.legend(ncol=4)
    save(figure, "eda_margin_quarter")
    return ratio


def plot_scatter(s: pd.DataFrame) -> float:
    figure, axis = plt.subplots(figsize=(7.2, 6))
    for label, mask, color in [("trước 2019", s["Date"].dt.year < 2019, COLORS[0]),
                               ("2019", s["Date"].dt.year == 2019, COLORS[3]),
                               ("sau 2019", s["Date"].dt.year > 2019, COLORS[2])]:
        axis.scatter(s.loc[mask, "Revenue"] / MILLION, s.loc[mask, "COGS"] / MILLION, s=6, alpha=0.5, color=color,
                     label=label, linewidths=0)
    slope = float((s["COGS"] * s["Revenue"]).sum() / (s["Revenue"] ** 2).sum())
    top = s["Revenue"].max() / MILLION
    axis.plot([0, top], [0, top], color=MUTED, linestyle="--", linewidth=1, label="COGS = Revenue (hòa vốn)")
    axis.plot([0, top], [0, slope * top], color=MUTED, linestyle=":", linewidth=1.2, label=f"COGS = {slope:.2f} × Revenue")
    axis.set_xlabel("Revenue (triệu VND)")
    axis.set_ylabel("COGS (triệu VND)")
    axis.set_title("Quan hệ Revenue – COGS theo ngày", loc="left")
    axis.legend()
    save(figure, "eda_scatter")
    return slope


def main() -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()
    s = load_sales()
    s["era"] = s["Date"].dt.year.map(era_of)

    plot_timeline(s)
    plot_monthly_by_year(s)
    tet = tet_profile(s)
    plot_tet(tet)
    dow, dom = plot_calendar(s)
    parity = plot_parity(s)
    plot_distribution(s)
    ratio = plot_margin(s)
    slope = plot_scatter(s)

    era_mean = (s.groupby("era")["Revenue"].mean() / MILLION).reindex(list(ERA_COLORS))
    peak = era_mean["Seasonality rõ (2014–2018)"]
    post = era_mean["Regime mới (2020–2022)"]
    q3 = ratio[3]
    stats = {
        "days": len(s), "start": s["Date"].min().date().isoformat(), "end": s["Date"].max().date().isoformat(),
        "era_mean_million": era_mean.round(3).to_dict(),
        "post_vs_peak_pct": round((post / peak - 1) * 100, 1),
        "weekday_mean": round(float(dow.iloc[:5].mean()), 2), "weekend_mean": round(float(dow.iloc[5:].mean()), 2),
        "dom_mid_mean": round(float(dom.loc[4:20].mean()), 2), "dom_last3_mean": round(float(dom.loc[29:31].mean()), 2),
        "dom_first3_mean": round(float(dom.loc[1:3].mean()), 2),
        "tet_before_mean": round(float(tet.loc[-30:-8, "Revenue"].mean()), 2),
        "tet_window_mean": round(float(tet.loc[-3:3, "Revenue"].mean()), 2),
        "tet_after_mean": round(float(tet.loc[20:30, "Revenue"].mean()), 2),
        "aug_even": round(float(parity.loc[8, "Năm chẵn"]), 2), "aug_odd": round(float(parity.loc[8, "Năm lẻ"]), 2),
        "q3_ratio_odd": round(float(q3[[y for y in q3.index if y % 2 == 1 and y >= 2013]].mean()), 3),
        "q3_ratio_even": round(float(q3[[y for y in q3.index if y % 2 == 0 and y >= 2014]].mean()), 3),
        "q124_ratio_range": [round(float(ratio[[1, 2, 4]].loc[2013:].min().min()), 3),
                             round(float(ratio[[1, 2, 4]].loc[2013:].max().max()), 3)],
        "cogs_slope": round(slope, 3),
        "days_cogs_above_revenue": int((s["COGS"] > s["Revenue"]).sum()),
        "odd_only_promos": [p["name"] for p in promo_schedule() if p["odd_only"]],
    }
    (OUTPUT_DIR / "eda_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def write_report(st: dict) -> None:
    p = PLOT_LINK
    eras = st["era_mean_million"]
    lines = [
        "# Dự báo doanh thu — Phân tích chuỗi thời gian",
        "",
        "Tạo tự động bởi `forecasting/01_time_series_eda.py` từ `data/raw/sales.csv`. Mọi con số dưới đây tính trực tiếp từ dữ liệu.",
        "",
        "## 1. Giới thiệu",
        "",
        "Phần 3 của VinDatathon 2026 Round 1: từ doanh thu hằng ngày đến hết 2022, dự báo **Revenue** và **COGS** cho "
        "**548 ngày** kế tiếp (01/01/2023 – 01/07/2024). Phần 2 trả lời *điều gì đã xảy ra*; phần này dự báo *điều gì sẽ "
        "xảy ra* và dùng lại các insight của Phần 2 (doanh thu giảm sau 2016, mùa vụ, chiến dịch khuyến mãi) làm giả định "
        "thiết kế.",
        "",
        "Pipeline: phân tích dữ liệu → đặc trưng chỉ từ lịch → ba mô hình gốc (Ridge, LightGBM, Prophet) và bốn mô hình "
        "chuyên biệt theo quý → ensemble phân tầng → calibration mức → giải thích bằng SHAP.",
        "",
        "## 2. Phát biểu bài toán",
        "",
        f"- **Input:** `sales.csv` gồm `Date`, `Revenue`, `COGS`, {st['days']:,} ngày liên tục từ {st['start']} đến {st['end']}. "
        "Các bảng phụ (orders, web_traffic, inventory…) đều dừng ở 2022 nên chỉ dùng để rút ra **quy luật lặp lại** "
        "(lịch khuyến mãi), không dùng làm đặc trưng cho giai đoạn test.",
        "- **Output:** `submission.csv` gồm 548 dòng `Date, Revenue, COGS`.",
        "- **Chấm điểm:** MAE, RMSE và R² trên cả Revenue lẫn COGS.",
        "",
        "**Vì sao bài toán khó:**",
        "",
        "1. **Horizon dài 18 tháng:** không có giá trị của hôm qua hay tuần trước, nên không dùng được đặc trưng lag "
        "(y<sub>t−1</sub>, y<sub>t−7</sub>). Phương án ổn định là **đặc trưng chỉ từ lịch**.",
        "2. **Regime drift:** mức doanh thu sau 2019 khác hẳn giai đoạn trước (mục 3.1).",
        "3. **Không có phản hồi từ test:** không biết sai ở ngày nào, nên mọi lựa chọn phải dựa trên cross-validation theo thời gian.",
        "",
        "## 3. Phân tích dữ liệu",
        "",
        "### 3.1. Bức tranh tổng thể: dữ liệu không đồng nhất theo thời gian",
        "",
        f"![Timeline]({p}/eda_timeline.png)",
        "",
        "| Giai đoạn | Doanh thu trung bình ngày (triệu VND) |",
        "|---|---:|",
        *[f"| {era} | {value:.2f} |" for era, value in eras.items()],
        "",
        f"Chuỗi chia thành bốn vùng có tính chất khác nhau. 2014–2018 là vùng có biên độ lớn và mùa vụ rõ nhất; năm 2019 "
        f"giảm đột ngột; giai đoạn 2020–2022 là một regime mới với mức doanh thu thấp hơn **{abs(st['post_vs_peak_pct']):.1f}%** "
        "so với 2014–2018. Từ đây có hai quyết định thiết kế:",
        "",
        "- **Sample weighting:** ưu tiên vùng 2014–2018 khi train để mô hình học *hình dạng* mùa vụ từ vùng sạch.",
        "- **Calibration tách rời:** vì vùng học có mức khác vùng test, cần một tầng điều chỉnh mức riêng (mục 7).",
        "",
        "### 3.2. Mùa vụ có bền vững không?",
        "",
        f"![Mùa vụ theo năm]({p}/eda_monthly_by_year.png)",
        "",
        "Các đường cong theo năm có cùng **hình dạng**: thấp ở tháng 1–2, tăng mạnh tháng 3–4, cao nhất tháng 4–6 rồi "
        "giảm dần về cuối năm. Khác biệt giữa các năm chủ yếu nằm ở **mức** (level). Kết luận *mùa vụ bền vững, mức thay "
        "đổi* là cơ sở để dùng đặc trưng Fourier cho mùa vụ năm.",
        "",
        "### 3.3. Các pattern lịch chi tiết",
        "",
        "**(a) Hiệu ứng Tết Âm lịch**",
        "",
        f"![Tết]({p}/eda_tet.png)",
        "",
        f"Doanh thu trung bình từ 30 đến 8 ngày trước Tết khoảng **{st['tet_before_mean']:.2f} triệu**, quanh mùng 1 "
        f"(±3 ngày) khoảng **{st['tet_window_mean']:.2f} triệu**, và 20–30 ngày sau Tết lên **{st['tet_after_mean']:.2f} "
        "triệu**. Tết rơi vào ngày dương lịch khác nhau mỗi năm, nên đặc trưng theo tháng không bắt được; dùng "
        "`tet_days_diff` (khoảng cách tới mùng 1 Tết gần nhất), áp dụng được cho cả 2023 (22/01) và 2024 (10/02).",
        "",
        "**(b) Thứ trong tuần và ngày trong tháng**",
        "",
        f"![Lịch]({p}/eda_calendar.png)",
        "",
        f"- Ngày thường trung bình **{st['weekday_mean']:.2f} triệu**, cuối tuần **{st['weekend_mean']:.2f} triệu**.",
        f"- Pattern ngày trong tháng mạnh hơn nhiều: 3 ngày cuối tháng trung bình **{st['dom_last3_mean']:.2f} triệu**, 3 ngày "
        f"đầu tháng **{st['dom_first3_mean']:.2f} triệu**, so với **{st['dom_mid_mean']:.2f} triệu** ở giữa tháng (ngày 4–20). "
        "Từ đây có nhóm đặc trưng `is_last1..3`, `is_first1..3` và `days_to_eom`.",
        "",
        "**(c) Chu kỳ năm chẵn / năm lẻ**",
        "",
        f"![Chẵn lẻ]({p}/eda_parity.png)",
        "",
        f"`promotions.csv` có hai chiến dịch chỉ chạy năm lẻ: {', '.join(f'`{n}`' for n in st['odd_only_promos'])}. Khác biệt "
        f"rõ nhất ở **tháng 8**: năm chẵn trung bình **{st['aug_even']:.2f} triệu**, năm lẻ **{st['aug_odd']:.2f} triệu**. "
        "Test gồm 2023 (lẻ) và 2024 (chẵn), nên đặc trưng `is_odd_year` cho mô hình chuyển giữa hai pattern.",
        "",
        "### 3.4. Phân phối và margin theo quý",
        "",
        f"![Phân phối]({p}/eda_distribution.png)",
        "",
        "Ba era có phân phối gần như không chồng lấp. Nếu mọi mẫu có cùng trọng số, mô hình sẽ thỏa hiệp ở một mức "
        "trung bình không thuộc era nào, và dự báo 2023 bị lệch mức. Đây là lý do pipeline cần tầng calibration.",
        "",
        f"![Margin theo quý]({p}/eda_margin_quarter.png)",
        "",
        f"Q1, Q2, Q4 có tỷ lệ COGS/Revenue ổn định trong khoảng {st['q124_ratio_range'][0]:.2f}–{st['q124_ratio_range'][1]:.2f}. "
        f"Riêng **Q3 dao động theo năm chẵn/lẻ**: năm lẻ trung bình **{st['q3_ratio_odd']:.2f}** (bán lỗ, COGS vượt Revenue), "
        f"năm chẵn **{st['q3_ratio_even']:.2f}**. Pattern này trùng với `urban_blowout` (chỉ năm lẻ, cuối tháng 7) và dẫn "
        "tới hai ý tưởng: đặc trưng `is_odd_year` và **mô hình chuyên biệt theo quý**.",
        "",
        "### 3.5. Quan hệ Revenue – COGS",
        "",
        f"![Scatter]({p}/eda_scatter.png)",
        "",
        f"COGS gần tuyến tính theo Revenue với hệ số khoảng **{st['cogs_slope']:.2f}**. Có {st['days_cogs_above_revenue']:,} "
        "ngày COGS vượt Revenue, tập trung ở Q3 năm lẻ. Vì margin Q3 vi phạm giả định *tỷ lệ ổn định*, pipeline dự báo "
        "**COGS bằng mô hình riêng** (train trên log COGS) thay vì nhân Revenue với một tỷ lệ cố định.",
        "",
    ]
    EDA_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
