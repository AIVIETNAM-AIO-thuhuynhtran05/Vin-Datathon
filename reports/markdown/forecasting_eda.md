# Dự báo doanh thu — Phân tích chuỗi thời gian

Tạo tự động bởi `forecasting/01_time_series_eda.py` từ `data/raw/sales.csv`. Mọi con số dưới đây tính trực tiếp từ dữ liệu.

## 1. Giới thiệu

Phần 3 của VinDatathon 2026 Round 1: từ doanh thu hằng ngày đến hết 2022, dự báo **Revenue** và **COGS** cho **548 ngày** kế tiếp (01/01/2023 – 01/07/2024). Phần 2 trả lời *điều gì đã xảy ra*; phần này dự báo *điều gì sẽ xảy ra* và dùng lại các insight của Phần 2 (doanh thu giảm sau 2016, mùa vụ, chiến dịch khuyến mãi) làm giả định thiết kế.

Pipeline: phân tích dữ liệu → đặc trưng chỉ từ lịch → ba mô hình gốc (Ridge, LightGBM, Prophet) và bốn mô hình chuyên biệt theo quý → ensemble phân tầng → calibration mức → giải thích bằng SHAP.

## 2. Phát biểu bài toán

- **Input:** `sales.csv` gồm `Date`, `Revenue`, `COGS`, 3,833 ngày liên tục từ 2012-07-04 đến 2022-12-31. Các bảng phụ (orders, web_traffic, inventory…) đều dừng ở 2022 nên chỉ dùng để rút ra **quy luật lặp lại** (lịch khuyến mãi), không dùng làm đặc trưng cho giai đoạn test.
- **Output:** `submission.csv` gồm 548 dòng `Date, Revenue, COGS`.
- **Chấm điểm:** MAE, RMSE và R² trên cả Revenue lẫn COGS.

**Vì sao bài toán khó:**

1. **Horizon dài 18 tháng:** không có giá trị của hôm qua hay tuần trước, nên không dùng được đặc trưng lag (y<sub>t−1</sub>, y<sub>t−7</sub>). Phương án ổn định là **đặc trưng chỉ từ lịch**.
2. **Regime drift:** mức doanh thu sau 2019 khác hẳn giai đoạn trước (mục 3.1).
3. **Không có phản hồi từ test:** không biết sai ở ngày nào, nên mọi lựa chọn phải dựa trên cross-validation theo thời gian.

## 3. Phân tích dữ liệu

### 3.1. Bức tranh tổng thể: dữ liệu không đồng nhất theo thời gian

![Timeline](../../data/processed/forecasting/plots/eda_timeline.png)

| Giai đoạn | Doanh thu trung bình ngày (triệu VND) |
|---|---:|
| Noise (2012–2013) | 4.39 |
| Seasonality rõ (2014–2018) | 5.27 |
| Chuyển tiếp (2019) | 3.12 |
| Regime mới (2020–2022) | 2.98 |

Chuỗi chia thành bốn vùng có tính chất khác nhau. 2014–2018 là vùng có biên độ lớn và mùa vụ rõ nhất; năm 2019 giảm đột ngột; giai đoạn 2020–2022 là một regime mới với mức doanh thu thấp hơn **43.5%** so với 2014–2018. Từ đây có hai quyết định thiết kế:

- **Sample weighting:** ưu tiên vùng 2014–2018 khi train để mô hình học *hình dạng* mùa vụ từ vùng sạch.
- **Calibration tách rời:** vì vùng học có mức khác vùng test, cần một tầng điều chỉnh mức riêng (mục 7).

### 3.2. Mùa vụ có bền vững không?

![Mùa vụ theo năm](../../data/processed/forecasting/plots/eda_monthly_by_year.png)

Các đường cong theo năm có cùng **hình dạng**: thấp ở tháng 1–2, tăng mạnh tháng 3–4, cao nhất tháng 4–6 rồi giảm dần về cuối năm. Khác biệt giữa các năm chủ yếu nằm ở **mức** (level). Kết luận *mùa vụ bền vững, mức thay đổi* là cơ sở để dùng đặc trưng Fourier cho mùa vụ năm.

### 3.3. Các pattern lịch chi tiết

**(a) Hiệu ứng Tết Âm lịch**

![Tết](../../data/processed/forecasting/plots/eda_tet.png)

Doanh thu trung bình từ 30 đến 8 ngày trước Tết khoảng **2.70 triệu**, quanh mùng 1 (±3 ngày) khoảng **3.30 triệu**, và 20–30 ngày sau Tết lên **3.91 triệu**. Tết rơi vào ngày dương lịch khác nhau mỗi năm, nên đặc trưng theo tháng không bắt được; dùng `tet_days_diff` (khoảng cách tới mùng 1 Tết gần nhất), áp dụng được cho cả 2023 (22/01) và 2024 (10/02).

**(b) Thứ trong tuần và ngày trong tháng**

![Lịch](../../data/processed/forecasting/plots/eda_calendar.png)

- Ngày thường trung bình **4.41 triệu**, cuối tuần **3.99 triệu**.
- Pattern ngày trong tháng mạnh hơn nhiều: 3 ngày cuối tháng trung bình **7.17 triệu**, 3 ngày đầu tháng **5.12 triệu**, so với **3.58 triệu** ở giữa tháng (ngày 4–20). Từ đây có nhóm đặc trưng `is_last1..3`, `is_first1..3` và `days_to_eom`.

**(c) Chu kỳ năm chẵn / năm lẻ**

![Chẵn lẻ](../../data/processed/forecasting/plots/eda_parity.png)

`promotions.csv` có hai chiến dịch chỉ chạy năm lẻ: `urban_blowout`, `rural_special`. Khác biệt rõ nhất ở **tháng 8**: năm chẵn trung bình **5.50 triệu**, năm lẻ **3.25 triệu**. Test gồm 2023 (lẻ) và 2024 (chẵn), nên đặc trưng `is_odd_year` cho mô hình chuyển giữa hai pattern.

### 3.4. Phân phối và margin theo quý

![Phân phối](../../data/processed/forecasting/plots/eda_distribution.png)

Ba era có phân phối gần như không chồng lấp. Nếu mọi mẫu có cùng trọng số, mô hình sẽ thỏa hiệp ở một mức trung bình không thuộc era nào, và dự báo 2023 bị lệch mức. Đây là lý do pipeline cần tầng calibration.

![Margin theo quý](../../data/processed/forecasting/plots/eda_margin_quarter.png)

Q1, Q2, Q4 có tỷ lệ COGS/Revenue ổn định trong khoảng 0.82–0.91. Riêng **Q3 dao động theo năm chẵn/lẻ**: năm lẻ trung bình **1.04** (bán lỗ, COGS vượt Revenue), năm chẵn **0.86**. Pattern này trùng với `urban_blowout` (chỉ năm lẻ, cuối tháng 7) và dẫn tới hai ý tưởng: đặc trưng `is_odd_year` và **mô hình chuyên biệt theo quý**.

### 3.5. Quan hệ Revenue – COGS

![Scatter](../../data/processed/forecasting/plots/eda_scatter.png)

COGS gần tuyến tính theo Revenue với hệ số khoảng **0.85**. Có 382 ngày COGS vượt Revenue, tập trung ở Q3 năm lẻ. Vì margin Q3 vi phạm giả định *tỷ lệ ổn định*, pipeline dự báo **COGS bằng mô hình riêng** (train trên log COGS) thay vì nhân Revenue với một tỷ lệ cố định.

