"""Đường dẫn, hằng số lịch và style biểu đồ dùng chung cho phần dự báo doanh thu."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed" / "forecasting"
PLOT_DIR = OUTPUT_DIR / "plots"
PLOT_LINK = "../../data/processed/forecasting/plots"
MARKDOWN_DIR = ROOT / "reports" / "markdown"
EDA_REPORT_PATH = MARKDOWN_DIR / "forecasting_eda.md"
MODEL_REPORT_PATH = MARKDOWN_DIR / "forecasting_models.md"
SUBMISSION_PATH = Path(__file__).resolve().parent / "submission.csv"

SEED = 42
TEST_START, TEST_END = "2023-01-01", "2024-07-01"  # 548 ngày cần dự báo
TARGETS = ["Revenue", "COGS"]

# Vùng dữ liệu "sạch" có mùa vụ rõ nhất; ngoài vùng này mẫu gần như bị bỏ qua khi train cây.
HIGH_ERA = (2014, 2018)
LOW_WEIGHT = 0.01
QBOOST = 2.0

# Mùng 1 Tết Âm lịch: kiến thức lịch (không phải dữ liệu ngoài), cần để mã hóa hiệu ứng Tết cho cả 2023–2024.
TET_DATES = {
    2012: "2012-01-23", 2013: "2013-02-10", 2014: "2014-01-31", 2015: "2015-02-19", 2016: "2016-02-08",
    2017: "2017-01-28", 2018: "2018-02-16", 2019: "2019-02-05", 2020: "2020-01-25", 2021: "2021-02-12",
    2022: "2022-02-01", 2023: "2023-01-22", 2024: "2024-02-10", 2025: "2025-01-29",
}

# Ngày lễ dương lịch cố định ở Việt Nam và các ngày mua sắm (tháng, ngày, tên).
VN_FIXED_HOLIDAYS = [
    (1, 1, "new_year"), (3, 8, "womens_day"), (4, 30, "reunification"), (5, 1, "labor_day"),
    (9, 2, "national_day"), (10, 20, "vn_womens_day"), (11, 11, "dd_1111"), (12, 12, "dd_1212"),
    (12, 24, "christmas_eve"), (12, 25, "christmas"),
]

# Ba fold theo thời gian: (tên, train đến hết, validate từ, validate đến).
FOLDS = [
    ("A", "2021-12-31", "2022-01-01", "2022-12-31"),  # chính: 2022 gần phân phối test nhất
    ("B", "2020-12-31", "2021-01-01", "2021-12-31"),  # ổn định qua năm
    ("C", "2021-06-30", "2021-07-01", "2022-06-30"),  # cửa sổ 12 tháng liên tục
]

# Bảng màu phân loại cố định (không xoay vòng) và màu chữ.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
SURFACE, INK, INK_SECONDARY, MUTED, GRID, BASELINE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
ERA_COLORS = {"Noise (2012–2013)": "#c3c2b7", "Seasonality rõ (2014–2018)": "#1baf7a",
              "Chuyển tiếp (2019)": "#eda100", "Regime mới (2020–2022)": "#e34948"}


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": BASELINE, "axes.labelcolor": INK_SECONDARY, "axes.titlecolor": INK,
        "axes.titlesize": 11, "axes.titleweight": "bold", "axes.labelsize": 9, "axes.grid": True,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "grid.color": GRID, "grid.linewidth": 0.6, "xtick.color": INK_SECONDARY, "ytick.color": INK_SECONDARY,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.frameon": False, "legend.fontsize": 8,
        "font.family": ["Segoe UI", "DejaVu Sans"], "lines.linewidth": 1.6,
    })


def era_of(year: int) -> str:
    if year <= 2013:
        return "Noise (2012–2013)"
    if year <= 2018:
        return "Seasonality rõ (2014–2018)"
    if year == 2019:
        return "Chuyển tiếp (2019)"
    return "Regime mới (2020–2022)"
