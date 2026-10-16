# Dự báo doanh thu — Mô hình, đánh giá và giải thích

Tạo tự động bởi `forecasting/02_train_forecast.py`. Phân tích dữ liệu nằm ở báo cáo trước ([`forecasting_eda.md`](forecasting_eda.md)); mọi con số dưới đây là kết quả chạy thật, `random_state = 42`.

## 4. Feature engineering

Mọi đặc trưng tính được từ ngày tháng (`forecasting/features.py`), tổng cộng **81 đặc trưng**, nên ma trận đặc trưng cho 2023–2024 dựng sẵn được mà không cần doanh thu của test:

| Nhóm | Đặc trưng | Từ quan sát nào |
|---|---|---|
| Lịch cơ bản | năm, tháng, ngày, thứ, ngày trong năm, quý, cuối tuần | Mùa vụ năm, thứ trong tuần (mục 3.2, 3.3) |
| Đầu / cuối tháng | `is_first1..3`, `is_last1..3`, `days_to_eom`, `days_from_som` | Cuối tháng cao gấp đôi giữa tháng (3.3b) |
| Xu hướng + chế độ | `t_days`, `regime_pre2019`, `regime_2019`, `regime_post2019` | Regime drift (3.1) |
| Fourier | sin/cos năm k = 1..5, tuần và tháng k = 1..2 | Hình dạng mùa vụ bền vững (3.2) |
| Lễ | 10 ngày lễ dương lịch cố định ở Việt Nam, Black Friday | Ngày mua sắm |
| Tết Âm lịch | `tet_days_diff`, `tet_in_7`, `tet_in_14`, `tet_before_7`, `tet_after_7`, `tet_on` | Hiệu ứng Tết (3.3a) |
| Khuyến mãi | trạng thái, số ngày đã/còn lại và mức giảm của 6 chiến dịch | Lịch khuyến mãi |
| Năm lẻ | `is_odd_year` | Chu kỳ chẵn/lẻ, margin Q3 (3.3c, 3.4) |

**Lịch khuyến mãi suy từ `promotions.csv`** (không dùng dữ liệu ngoài): mỗi chiến dịch lặp lại cùng ngày bắt đầu và thời lượng mỗi năm.

| Chiến dịch | Bắt đầu | Thời lượng | Mức giảm | Lặp lại |
|---|---|---:|---:|---|
| `spring_sale` | 18/03 | 30 ngày | 12 | hằng năm |
| `mid_year_sale` | 23/06 | 29 ngày | 18 | hằng năm |
| `fall_launch` | 30/08 | 32 ngày | 10 | hằng năm |
| `year_end_sale` | 18/11 | 45 ngày | 20 | hằng năm |
| `urban_blowout` | 30/07 | 34 ngày | 50 | chỉ năm lẻ |
| `rural_special` | 30/01 | 30 ngày | 15 | chỉ năm lẻ |

Ngày Tết Âm lịch và ngày lễ là **kiến thức lịch**, không phải bộ dữ liệu bên ngoài.

## 5. Chiến lược validation

Ba fold theo thời gian, không xáo trộn dữ liệu:

| Fold | Train | Validate | Vai trò |
|---|---|---|---|
| A (chính) | ≤ 2021-12 | 2022 | 2022 gần phân phối test nhất; dùng để ước lượng hệ số calibration |
| B (ổn định) | ≤ 2020-12 | 2021 | Kiểm tra cải tiến có ổn định qua năm không |
| C (horizon) | ≤ 2021-06 | 2021-07 → 2022-06 | Cửa sổ 12 tháng liên tục, gần horizon thật |

Hai thước đo: **MAE/RMSE/R² thông thường** và **MAE hình dạng** (đưa dự báo về đúng tổng của tập validate trước khi tính MAE). MAE hình dạng tách được chất lượng *hình dạng* khỏi vấn đề *mức*, vốn do tầng calibration xử lý.

## 6. Lựa chọn và huấn luyện mô hình

Ba họ mô hình khác bản chất để ensemble có diversity:

- **M1 Ridge + Fourier:** tuyến tính trên đặc trưng chuẩn hóa z-score, train trên log(target), α = 3. Ổn định, làm *anchor*.
- **M2 LightGBM high_era:** trọng số 1.0 cho 2014–2018, 0.01 cho phần còn lại; learning rate 0.03, 63 lá. Train 2 giai đoạn: early stopping trên 180 ngày cuối để chọn số vòng, rồi train lại trên toàn bộ dữ liệu.
- **M2q 4 Q-specialist:** cùng cấu hình M2, nhân trọng số ×2 cho quý phụ trách. Khi dự báo, mỗi ngày lấy dự báo của specialist đúng quý của ngày đó (không lấy trung bình). Tổng cộng 4 quý × 2 target = 8 mô hình.
- **M3 Prophet + promos:** học từ 2020 trở đi (trend không bị bước nhảy 2019 bóp méo); fold nào train kết thúc sớm thì lùi về đủ 2 năm gần nhất để mùa vụ năm không bị thiếu dữ liệu. Mùa vụ năm và tuần dạng multiplicative, regressor là cửa sổ của các chiến dịch khuyến mãi.

**Diversity** (tương quan sai số trên fold A, Revenue): Ridge vs Prophet = 0.71, Ridge vs LGB = 0.70, Prophet vs LGB = 0.56.

## 7. Ensemble phân tầng và calibration

| Tầng | Công thức | Tham số |
|---|---|---|
| 1. Hợp nhất họ LightGBM | LGB_blend = (1 − α)·M2 + α·M2q | α = 1.00 |
| 2. Hợp nhất 3 họ | raw = w₁·M1 + w₃·M3 + w₂·LGB_blend | w₁ = 0.30, w₃ = 0.00, w₂ = 0.70 |
| 3. Calibration mức | final = c × raw | c<sub>Revenue</sub> = 1.080, c<sub>COGS</sub> = 1.097 |

- **α và trọng số** chọn bằng lưới (bước 0.1 cho α, 0.05 cho trọng số) để tối thiểu **MAE hình dạng** trung bình trên 3 fold và cả 2 target.
- **Calibration:** c = tổng thực tế 2022 ÷ tổng dự báo 2022 của mô hình train đến 2021 (fold A), rồi áp cho mô hình train đến 2022 dự báo 2023–2024. Hệ số tách khỏi tầng blend vì vấn đề *mức* khác vấn đề *hình dạng*.
- **Khác tài liệu tham chiếu:** tài liệu chỉnh c trực tiếp trên Leaderboard. Ở đây không dùng Leaderboard; c ước lượng hoàn toàn từ dữ liệu train, nên không có rò rỉ từ test.

## 8. Kết quả cross-validation

![CV](../../data/processed/forecasting/plots/model_cv.png)

**Revenue: trung bình 3 fold**

| Mô hình | MAE | RMSE | R² | MAE hình dạng | Mức dự báo / thực tế |
|---|---:|---:|---:|---:|---:|
| Seasonal naive (cùng thứ, năm trước) | 840,592 | 1,232,949 | 0.450 | 841,854 | 0.96 |
| M1 Ridge + Fourier | 644,597 | 944,853 | 0.676 | 614,467 | 0.89 |
| M3 Prophet + promos | 965,129 | 1,344,605 | 0.344 | 859,008 | 1.07 |
| M2 LightGBM high_era | 558,011 | 770,167 | 0.785 | 557,283 | 0.96 |
| M2q 4 Q-specialists | 554,011 | 748,401 | 0.797 | 548,801 | 0.96 |
| Ensemble (chưa calibration) | 545,430 | 744,724 | 0.799 | 529,566 | 0.94 |

**COGS: trung bình 3 fold**

| Mô hình | MAE | RMSE | R² | MAE hình dạng | Mức dự báo / thực tế |
|---|---:|---:|---:|---:|---:|
| Seasonal naive (cùng thứ, năm trước) | 686,869 | 1,012,621 | 0.518 | 684,908 | 0.92 |
| M1 Ridge + Fourier | 588,239 | 861,485 | 0.650 | 543,010 | 0.88 |
| M3 Prophet + promos | 860,172 | 1,195,796 | 0.327 | 762,693 | 1.08 |
| M2 LightGBM high_era | 506,871 | 697,915 | 0.771 | 495,771 | 0.94 |
| M2q 4 Q-specialists | 498,365 | 682,245 | 0.781 | 486,066 | 0.93 |
| Ensemble (chưa calibration) | 497,684 | 690,590 | 0.776 | 473,413 | 0.92 |

**Đánh giá trung thực của tầng calibration (fold A, 2022):** áp hệ số ước lượng từ fold B (năm 2021) lên dự báo 2022, mô phỏng đúng cách hệ số được dùng cho 2023–2024.

| Target | Mô hình | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| Revenue | Seasonal naive (cùng thứ, năm trước) | 863,664 | 1,247,432 | 0.445 |
| Revenue | Ensemble (chưa calibration) | 566,967 | 762,150 | 0.793 |
| Revenue | Ensemble + calibration | 544,238 | 736,157 | 0.807 |
| COGS | Seasonal naive (cùng thứ, năm trước) | 714,915 | 1,035,433 | 0.496 |
| COGS | Ensemble (chưa calibration) | 513,189 | 685,735 | 0.779 |
| COGS | Ensemble + calibration | 478,695 | 635,536 | 0.810 |

Hệ số ước lượng từ fold B: c<sub>Revenue</sub> = 1.037, c<sub>COGS</sub> = 1.075.

## 9. Khả năng giải thích mô hình (SHAP)

Giải thích **base LightGBM** cuối (train trên toàn bộ 2012–2022), đại diện cho họ cây trong ensemble. TreeSHAP tính trực tiếp qua `predict(pred_contrib=True)`, chính xác cho mô hình cây. Kiểm tra tính cộng tính (base value + Σ SHAP = dự báo log): sai số lớn nhất 4.6e-14. Vì mô hình học trên log, đóng góp Δ quy ra phần trăm doanh thu theo e<sup>Δ</sup> − 1.

### 9.1. Global importance

![SHAP nhóm](../../data/processed/forecasting/plots/model_shap_groups.png)

| Nhóm pattern | Revenue (%) | COGS (%) |
|---|---:|---:|
| Seasonality | 58.7 | 58.5 |
| Regime & trend | 25.4 | 24.4 |
| Edge-of-month | 6.3 | 7.3 |
| Weekly pattern | 6.0 | 7.3 |
| Promo campaigns | 2.6 | 1.6 |
| Tết | 0.6 | 0.6 |
| Year-parity | 0.3 | 0.3 |
| Lễ VN & BF | 0.0 | 0.0 |

### 9.2. Local effect

![SHAP cục bộ](../../data/processed/forecasting/plots/model_shap_local.png)

Global importance đo trung bình trên cả 548 ngày, nên pattern hiếm như Tết có global thấp dù tác động cục bộ rõ. Bảng dưới đo tác động ngay tại những ngày pattern xuất hiện: *chênh lệch tổng* cộng SHAP của mọi đặc trưng, *SHAP cô lập* chỉ cộng nhóm đặc trưng của driver.

| Driver | Chênh lệch dự báo tổng | SHAP cô lập của nhóm driver |
|---|---:|---:|
| Ngày cuối tháng vs giữa tháng (13–17) | +72.6% | +29.1% |
| ±7 ngày quanh Tết vs cách Tết > 30 ngày | -43.5% | -1.0% |
| Tháng 8 năm chẵn (2024) vs năm lẻ (2023) | +39.7% | +0.8% |

## 10. Dự báo và ý nghĩa kinh doanh

![Dự báo](../../data/processed/forecasting/plots/model_forecast.png)

| Target | Thực tế 2021 | Thực tế 2022 | Dự báo 2023 | Thực tế 6 tháng đầu 2022 | Dự báo 6 tháng đầu 2024 |
|---|---:|---:|---:|---:|---:|
| Revenue | 1.04 tỷ | 1.17 tỷ | 1.18 tỷ | 0.69 tỷ | 0.71 tỷ |
| COGS | 0.94 tỷ | 1.02 tỷ | 1.08 tỷ | 0.59 tỷ | 0.61 tỷ |

File nộp: [`forecasting/submission.csv`](../../forecasting/submission.csv), 548 dòng `Date, Revenue, COGS`, theo thứ tự ngày từ 2023-01-01 đến 2024-07-01.

