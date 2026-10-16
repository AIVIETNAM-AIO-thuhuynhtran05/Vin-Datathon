"""Đọc dữ liệu và tạo đặc trưng chỉ từ lịch.

Horizon 548 ngày nên không có lag (y_{t-1}, y_{t-7}, …): mọi đặc trưng tính được từ ngày tháng, nhờ vậy dựng sẵn
được ma trận đặc trưng cho cả 2023–2024. Lịch khuyến mãi được suy từ quy luật lặp lại trong `promotions.csv`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import RAW_DIR, TET_DATES, VN_FIXED_HOLIDAYS

TAU = 2 * np.pi


def load_sales() -> pd.DataFrame:
    sales = pd.read_csv(RAW_DIR / "sales.csv")
    sales["Date"] = pd.to_datetime(sales["Date"], format="%d/%m/%Y")
    return sales.sort_values("Date").reset_index(drop=True)


def promo_schedule() -> list[dict]:
    """Quy luật lịch khuyến mãi: ngày bắt đầu, thời lượng, mức giảm và năm lặp lại (mọi năm / chỉ năm lẻ)."""
    promos = pd.read_csv(RAW_DIR / "promotions.csv", parse_dates=["start_date", "end_date"])
    promos["base"] = promos["promo_name"].str.replace(r"\s*\d{4}$", "", regex=True)
    schedule = []
    for base, group in promos.groupby("base", sort=False):
        start = group["start_date"]
        years = set(start.dt.year)
        schedule.append({
            "name": base.lower().replace(" ", "_").replace("-", "_"),
            "month": int(start.dt.month.mode()[0]),
            "day": int(start.dt.day.mode()[0]),
            "duration": int((group["end_date"] - start).dt.days.median()),
            "discount": float(group["discount_value"].iloc[0]),
            "odd_only": all(y % 2 == 1 for y in years),
        })
    return schedule


def nearest_tet_diff(day: pd.Timestamp, tet: dict[int, pd.Timestamp]) -> int:
    candidates = [tet.get(day.year), tet.get(day.year - 1), tet.get(day.year + 1)]
    diffs = [(day - c).days for c in candidates if c is not None]
    valid = [d for d in diffs if abs(d) <= 45]
    return min(valid, key=abs) if valid else 999


def build_features(dates: pd.Series | pd.DatetimeIndex, schedule: list[dict] | None = None) -> pd.DataFrame:
    schedule = schedule if schedule is not None else promo_schedule()
    df = pd.DataFrame({"Date": pd.to_datetime(pd.Series(dates)).reset_index(drop=True)})
    d = df["Date"]

    # (a) Lịch cơ bản
    df["year"], df["month"], df["day"] = d.dt.year, d.dt.month, d.dt.day
    df["dow"], df["doy"], df["quarter"] = d.dt.dayofweek, d.dt.dayofyear, d.dt.quarter
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["dim"] = d.dt.days_in_month
    df["days_to_eom"] = df["dim"] - df["day"]
    df["days_from_som"] = df["day"] - 1

    # (b) Đầu / cuối tháng
    for k in (1, 2, 3):
        df[f"is_last{k}"] = (df["days_to_eom"] <= k - 1).astype(int)
        df[f"is_first{k}"] = (df["days_from_som"] <= k - 1).astype(int)

    # (c) Xu hướng + chế độ
    df["t_days"] = (d - pd.Timestamp("2020-01-01")).dt.days
    df["t_years"] = df["t_days"] / 365.25
    df["regime_pre2019"] = (df["year"] <= 2018).astype(int)
    df["regime_2019"] = (df["year"] == 2019).astype(int)
    df["regime_post2019"] = (df["year"] >= 2020).astype(int)

    # (d) Fourier: năm k = 1..5, tuần và tháng k = 1..2
    for k in range(1, 6):
        df[f"sin_y{k}"] = np.sin(TAU * k * df["doy"] / 365.25)
        df[f"cos_y{k}"] = np.cos(TAU * k * df["doy"] / 365.25)
    for k in (1, 2):
        df[f"sin_w{k}"] = np.sin(TAU * k * df["dow"] / 7)
        df[f"cos_w{k}"] = np.cos(TAU * k * df["dow"] / 7)
        df[f"sin_m{k}"] = np.sin(TAU * k * (df["day"] - 1) / df["dim"])
        df[f"cos_m{k}"] = np.cos(TAU * k * (df["day"] - 1) / df["dim"])

    # (e) Lễ dương lịch cố định
    for month, day, name in VN_FIXED_HOLIDAYS:
        df[f"hol_{name}"] = ((df["month"] == month) & (df["day"] == day)).astype(int)

    # (f) Tết Âm lịch
    tet = {y: pd.Timestamp(v) for y, v in TET_DATES.items()}
    diffs = np.array([nearest_tet_diff(day, tet) for day in d])
    df["tet_days_diff"] = diffs
    df["tet_in_7"] = (np.abs(diffs) <= 7).astype(int)
    df["tet_in_14"] = (np.abs(diffs) <= 14).astype(int)
    df["tet_before_7"] = ((diffs >= -7) & (diffs < 0)).astype(int)
    df["tet_after_7"] = ((diffs > 0) & (diffs <= 7)).astype(int)
    df["tet_on"] = (diffs == 0).astype(int)

    # (g) Black Friday: thứ Sáu cuối cùng của tháng 11
    def is_black_friday(day: pd.Timestamp) -> int:
        if day.month != 11:
            return 0
        last = pd.Timestamp(year=day.year, month=11, day=30)
        return int(day == last - pd.Timedelta(days=(last.dayofweek - 4) % 7))

    df["hol_black_friday"] = [is_black_friday(day) for day in d]

    # (h) Cửa sổ khuyến mãi suy từ quy luật trong promotions.csv
    years = range(int(df["year"].min()) - 1, int(df["year"].max()) + 2)
    for promo in schedule:
        in_promo = np.zeros(len(df), dtype=int)
        since = np.full(len(df), -1.0)
        until = np.full(len(df), -1.0)
        discount = np.zeros(len(df))
        for year in years:
            if promo["odd_only"] and year % 2 == 0:
                continue
            start = pd.Timestamp(year=year, month=promo["month"], day=promo["day"])
            end = start + pd.Timedelta(days=promo["duration"])
            mask = ((d >= start) & (d <= end)).to_numpy()
            in_promo[mask] = 1
            since[mask] = (d[mask] - start).dt.days
            until[mask] = (end - d[mask]).dt.days
            discount[mask] = promo["discount"]
        name = promo["name"]
        df[f"promo_{name}"], df[f"promo_{name}_since"] = in_promo, since
        df[f"promo_{name}_until"], df[f"promo_{name}_disc"] = until, discount

    # (i) Năm lẻ (các chiến dịch chỉ chạy năm lẻ)
    df["is_odd_year"] = (df["year"] % 2).astype(int)
    return df


def feature_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame.columns if c not in ("Date", "Revenue", "COGS")]


def feature_group(column: str) -> str:
    """Gom đặc trưng thành nhóm nghiệp vụ để đọc SHAP (Fourier tương quan nên xếp hạng đơn lẻ kém ổn định)."""
    if column == "is_odd_year":
        return "Year-parity"
    if column.startswith("tet_"):
        return "Tết"
    if column.startswith("hol_"):
        return "Lễ VN & BF"
    if column.startswith("promo_"):
        return "Promo campaigns"
    if column.startswith(("is_first", "is_last")) or column in ("days_to_eom", "days_from_som"):
        return "Edge-of-month"
    if column.startswith(("sin_w", "cos_w")) or column in ("dow", "is_weekend"):
        return "Weekly pattern"
    if column.startswith(("sin_y", "cos_y", "sin_m", "cos_m")) or column in ("month", "doy", "quarter", "day", "dim"):
        return "Seasonality"
    if column.startswith("regime_") or column in ("t_days", "t_years", "year"):
        return "Regime & trend"
    return "Khác"
