# Revenue Forecasting

Dự báo `Revenue` và `COGS` theo ngày cho **548 ngày** từ 01/01/2023 đến 01/07/2024, dựa trên lịch sử bán hàng 04/07/2012 – 31/12/2022. Đây là Phần 3 của đề thi (20 điểm), và là Phần 4 trong cấu trúc dự án.

**Kết quả chính** (mọi số liệu là kết quả chạy thật, `random_state = 42`):

- Mô hình cuối là **ensemble 3 tầng**: 0.3 × Ridge + 0.7 × LightGBM (4 mô hình chuyên biệt theo quý), nhân hệ số calibration mức.
- Trên năm 2022 (fold A), ensemble + calibration đạt **MAE 544K VND/ngày, R² 0.807** cho Revenue, giảm **37% sai số** so với baseline seasonal naive (MAE 864K, R² 0.445).
- Dự báo Revenue **2023: 1.18 tỷ** (2022 thực tế: 1.17 tỷ); **6 tháng đầu 2024: 0.71 tỷ** (cùng kỳ 2022: 0.69 tỷ).
- SHAP: **mùa vụ năm** (58.7%) và **mức theo giai đoạn** (25.4%) giải thích phần lớn dự báo; ngày cuối tháng là pattern ngắn hạn mạnh nhất.

Báo cáo chi tiết, tự sinh từ code:

- [`reports/markdown/forecasting_eda.md`](../reports/markdown/forecasting_eda.md): mục 1–3, phát biểu bài toán và phân tích chuỗi thời gian.
- [`reports/markdown/forecasting_models.md`](../reports/markdown/forecasting_models.md): mục 4–10, đặc trưng, validation, mô hình, ensemble, kết quả, SHAP và dự báo.
- PDF: [`reports/04_Forecasting_report.pdf`](../reports/04_Forecasting_report.pdf) ghép README này và hai file trên.

## Flow tổng quan

```text
sales.csv ─► 1. Hiểu đề ─► 2. EDA chuỗi ─► 3. Đặc trưng ─► 4. Validation ─► 5. Mô hình ─► 6. Ensemble ─► 7. Calibration ─► 8. SHAP ─► 9. Submission
             & ràng buộc     thời gian      từ lịch         theo thời gian   + baseline     3 tầng         mức                         548 dòng
```

| Bước | Làm gì | Ý nghĩa |
|---|---|---|
| 1. Hiểu đề và ràng buộc | Xác định horizon 548 ngày, chỉ số chấm, ba điều kiện loại bài | Quyết định ngay từ đầu: không dùng lag, không dùng dữ liệu ngoài, phải tái lập được |
| 2. EDA chuỗi thời gian | Tách giai đoạn, kiểm tra mùa vụ, Tết, ngày trong tháng, chẵn/lẻ, margin theo quý | Mỗi pattern tìm được trở thành một nhóm đặc trưng hoặc một quyết định thiết kế |
| 3. Đặc trưng chỉ từ lịch | 81 đặc trưng tính từ ngày tháng và lịch khuyến mãi suy từ `promotions.csv` | Dựng được đặc trưng cho cả 2023–2024 mà không cần doanh thu tương lai, nên không rò rỉ |
| 4. Validation theo thời gian | 3 fold A/B/C, baseline seasonal naive, thêm MAE hình dạng | Đo đúng tình huống thật (dự báo năm sau từ quá khứ) và tách lỗi *hình dạng* khỏi lỗi *mức* |
| 5. Mô hình gốc | Ridge, LightGBM high_era, 4 Q-specialist, Prophet | Ba họ mô hình khác bản chất, mạnh ở những chỗ khác nhau |
| 6. Ensemble 3 tầng | Chọn α và trọng số bằng lưới trên CV | Gộp điểm mạnh, để dữ liệu tự quyết định mô hình nào đáng tin |
| 7. Calibration mức | c = tổng thực tế 2022 ÷ tổng dự báo 2022 | Mô hình học hình dạng từ 2014–2018 nhưng mức doanh thu đã khác, nên cần điều chỉnh mức riêng |
| 8. Giải thích (SHAP) | TreeSHAP theo nhóm đặc trưng và tác động cục bộ | Nói được bằng ngôn ngữ kinh doanh *vì sao* dự báo cao hay thấp |
| 9. Submission | `submission.csv` 548 dòng, kiểm tra định dạng | Đáp ứng đúng yêu cầu nộp bài, chạy lại ra đúng file |

---

## Bước 1. Hiểu đề và ràng buộc

**Bài toán:** với mỗi ngày từ 01/01/2023 đến 01/07/2024, dự báo `Revenue` và `COGS`. Chấm bằng MAE, RMSE, R² trên Kaggle leaderboard.

**Thang điểm (20 điểm):** hiệu suất mô hình 12 điểm; báo cáo kỹ thuật 8 điểm (pipeline rõ ràng, cross-validation đúng chiều thời gian, kiểm soát leakage, giải thích mô hình, tuân thủ ràng buộc).

**Ba điều kiện loại toàn bộ Phần 3:**

1. Dùng `Revenue`/`COGS` của tập test làm đặc trưng.
2. Dùng dữ liệu ngoài bộ dữ liệu được cung cấp.
3. Không đính kèm mã nguồn, hoặc kết quả không tái lập được.

**Ý nghĩa:** ba ràng buộc này định hình cả pipeline.

- Horizon 18 tháng nên không có doanh thu hôm qua hay tuần trước: **không dùng được đặc trưng lag**.
- Mọi bảng khác (orders, web_traffic, inventory…) dừng ở 31/12/2022: **không dùng làm đặc trưng cho ngày cần dự báo**, chỉ dùng để rút ra quy luật lặp lại (lịch khuyến mãi).
- Mọi mô hình đặt `random_state = 42`, LightGBM chạy `deterministic=True`.

**Lưu ý về dữ liệu:** `sales.csv` có 3.833 ngày liên tục, không thiếu, không trùng. Khi đối soát với dữ liệu giao dịch, `Revenue` = Σ(`quantity` × `unit_price`) của mọi đơn trong ngày, kể cả đơn hủy, chưa trừ giảm giá. Định nghĩa này khác doanh thu trong dashboard và phân nhóm khách hàng, nên phần dự báo chỉ dùng `sales.csv` làm mục tiêu.

## Bước 2. EDA chuỗi thời gian

Script: `01_time_series_eda.py`. Kết quả đầy đủ: [`forecasting_eda.md`](../reports/markdown/forecasting_eda.md).

| Quan sát (từ dữ liệu) | Số liệu | Quyết định thiết kế |
|---|---|---|
| Chuỗi chia 4 giai đoạn khác mức | Trung bình ngày: 4.39 triệu (2012–13), 5.27 (2014–18), 3.12 (2019), 2.98 (2020–22); thấp hơn đỉnh 43.5% | Trọng số mẫu ưu tiên 2014–2018 + tầng calibration mức |
| Mùa vụ năm cùng hình dạng, khác mức | Thấp tháng 1–2, cao nhất tháng 4–6, giảm về cuối năm | Fourier năm k = 1..5 |
| Cuối tháng cao gấp đôi giữa tháng | 3 ngày cuối tháng 7.17 triệu, 3 ngày đầu 5.12, giữa tháng 3.58 | `is_last1..3`, `is_first1..3`, `days_to_eom` |
| Tết dời ngày dương lịch mỗi năm | Trước Tết 2.70 triệu, quanh mùng 1 3.30, sau Tết 3.91 | `tet_days_diff` và các cờ cửa sổ Tết |
| Chu kỳ năm chẵn / lẻ | Tháng 8: năm chẵn 5.50 triệu, năm lẻ 3.25 | `is_odd_year` |
| Margin Q3 dao động theo năm | COGS/Revenue Q3: năm lẻ 1.04 (bán lỗ), năm chẵn 0.86; Q1, Q2, Q4 ổn định 0.82–0.91 | Mô hình riêng cho COGS + 4 mô hình chuyên biệt theo quý |

**Ý nghĩa:** EDA không chỉ để mô tả. Mỗi dòng trong bảng trên được nối thẳng với một nhóm đặc trưng hoặc một quyết định mô hình, nên mọi lựa chọn ở các bước sau đều có lý do từ dữ liệu.

## Bước 3. Đặc trưng chỉ từ lịch

File: `features.py`. Tổng cộng **81 đặc trưng**, chia 8 nhóm: lịch cơ bản, đầu/cuối tháng, xu hướng + giai đoạn, Fourier, lễ dương lịch, Tết, khuyến mãi, năm chẵn/lẻ.

**Lịch khuyến mãi suy từ `promotions.csv`:** mỗi chiến dịch lặp lại cùng ngày bắt đầu và thời lượng mỗi năm. Spring Sale (18/03), Mid-Year Sale (23/06), Fall Launch (30/08), Year-End Sale (18/11) chạy hằng năm; Urban Blowout (30/07) và Rural Special (30/01) **chỉ chạy năm lẻ**. Theo quy luật này, 2023 có cả hai, 2024 thì không.

**Ý nghĩa:**

- Vì đặc trưng chỉ phụ thuộc ngày tháng, ma trận đặc trưng cho 2023–2024 dựng được ngay, **không cần bất kỳ giá trị nào của tập test**. Đây là cách kiểm soát leakage từ gốc.
- Ngày Tết Âm lịch và ngày lễ là **kiến thức lịch**, không phải bộ dữ liệu bên ngoài; danh sách nằm trong `config.py` để kiểm tra được.
- Lịch khuyến mãi là quy luật rút ra từ dữ liệu được cung cấp, không phải dữ liệu 2023–2024.

## Bước 4. Validation theo thời gian

| Fold | Train | Validate | Vai trò |
|---|---|---|---|
| A (chính) | ≤ 2021-12 | 2022 | Gần test nhất; dùng để ước lượng hệ số calibration |
| B (ổn định) | ≤ 2020-12 | 2021 | Cải tiến có ổn định qua năm không |
| C (horizon) | ≤ 2021-06 | 2021-07 → 2022-06 | Cửa sổ 12 tháng liên tục, cắt ngang năm |

- **Baseline seasonal naive:** doanh thu cùng thứ trong tuần của năm trước (lag 364 ngày). Mô hình nào không thắng baseline này thì không có giá trị.
- **Hai thước đo:** MAE/RMSE/R² thông thường, và **MAE hình dạng**: đưa dự báo về đúng tổng của tập validate rồi mới tính MAE.

**Ý nghĩa:**

- Không xáo trộn dữ liệu: mỗi fold chỉ học từ quá khứ và dự báo tương lai, giống hệt tình huống thật.
- MAE hình dạng tách hai loại lỗi. Lỗi *hình dạng* (đỉnh, đáy, mùa vụ sai chỗ) do mô hình xử lý; lỗi *mức* (cả năm cao hay thấp hơn) do tầng calibration xử lý. Tách ra thì mỗi tầng được tối ưu cho đúng việc của nó.

## Bước 5. Mô hình gốc

Script: `02_train_forecast.py`. Mọi mô hình train trên log(target), riêng cho Revenue và COGS.

| Mô hình | Cách làm | Vì sao có mặt |
|---|---|---|
| M1 Ridge + Fourier | Tuyến tính trên đặc trưng chuẩn hóa, α = 3 | Ổn định, ít overfit, làm *anchor* |
| M2 LightGBM high_era | Trọng số 1.0 cho 2014–2018, 0.01 cho phần còn lại; early stopping trên 180 ngày cuối rồi train lại toàn bộ | Học tương tác phi tuyến (cuối tháng × mùa vụ) từ vùng dữ liệu có mùa vụ rõ nhất |
| M2q 4 Q-specialist | Như M2, nhân trọng số ×2 cho quý phụ trách; mỗi ngày dùng mô hình đúng quý | Q3 có margin khác hẳn các quý khác, một mô hình chung dễ bị kéo về trung bình |
| M3 Prophet + promos | Học từ 2020 (tối thiểu 2 năm gần nhất), mùa vụ multiplicative, regressor là cửa sổ khuyến mãi | Họ mô hình khác bản chất, bám sát giai đoạn gần nhất |

**Kết quả CV, Revenue, trung bình 3 fold:**

| Mô hình | MAE | R² | MAE hình dạng |
|---|---:|---:|---:|
| Seasonal naive | 840,592 | 0.450 | 841,854 |
| M1 Ridge + Fourier | 644,597 | 0.676 | 614,467 |
| M3 Prophet + promos | 965,129 | 0.344 | 859,008 |
| M2 LightGBM high_era | 558,011 | 0.785 | 557,283 |
| M2q 4 Q-specialists | 554,011 | 0.797 | 548,801 |
| **Ensemble (chưa calibration)** | **545,430** | **0.799** | **529,566** |

**Ý nghĩa:** LightGBM thắng baseline ở mọi fold, Q-specialist nhỉnh hơn bản gốc. Prophet **thua cả baseline**: chỉ có 2–3 năm dữ liệu gần nhất nên mùa vụ năm học được kém ổn định. Kết quả này được giữ nguyên trong báo cáo thay vì bỏ đi, vì nó giải thích tại sao bước ensemble loại Prophet.

## Bước 6. Ensemble 3 tầng

| Tầng | Công thức | Tham số chọn trên CV |
|---|---|---|
| 1. Họ LightGBM | LGB_blend = (1 − α)·M2 + α·M2q | α = 1.0 |
| 2. Ba họ mô hình | raw = w₁·Ridge + w₃·Prophet + w₂·LGB_blend | w₁ = 0.3, w₃ = 0, w₂ = 0.7 |
| 3. Calibration mức | final = c × raw | xem bước 7 |

α và trọng số được chọn bằng lưới (bước 0.1 cho α, 0.05 cho trọng số) để tối thiểu MAE hình dạng trung bình trên 3 fold × 2 target.

**Ý nghĩa:**

- Dữ liệu tự chọn: α = 1 nghĩa là 4 Q-specialist tốt hơn mô hình chung; Prophet nhận trọng số 0.
- Ridge vẫn giữ 30% dù đơn lẻ kém LightGBM, vì sai số của hai mô hình chỉ tương quan 0.70: Ridge bù được những chỗ mô hình cây đoán sai. Nhờ vậy ensemble giảm MAE hình dạng 3.5% so với mô hình đơn tốt nhất (529,566 so với 548,801).

## Bước 7. Calibration mức

c = tổng Revenue thực tế 2022 ÷ tổng dự báo 2022 của mô hình train đến hết 2021 (fold A). Kết quả: **c<sub>Revenue</sub> = 1.080**, **c<sub>COGS</sub> = 1.097**. Hệ số này nhân vào dự báo 2023–2024 của mô hình train đến hết 2022.

**Đánh giá trung thực:** để kiểm tra cách làm này, lấy hệ số ước lượng từ fold B (năm 2021, c<sub>Revenue</sub> = 1.037) áp lên dự báo 2022:

| Target | Mô hình | MAE | RMSE | R² |
|---|---|---:|---:|---:|
| Revenue | Seasonal naive | 863,664 | 1,247,432 | 0.445 |
| Revenue | Ensemble chưa calibration | 566,967 | 762,150 | 0.793 |
| Revenue | **Ensemble + calibration** | **544,238** | **736,157** | **0.807** |
| COGS | Seasonal naive | 714,915 | 1,035,433 | 0.496 |
| COGS | Ensemble chưa calibration | 513,189 | 685,735 | 0.779 |
| COGS | **Ensemble + calibration** | **478,695** | **635,536** | **0.810** |

**Ý nghĩa:**

- Trên cả 3 fold, ensemble chưa calibration dự báo tổng thấp hơn thực tế 4–7%: mô hình học đúng *hình dạng* nhưng lệch *mức*. Calibration sửa đúng phần này mà không làm thay đổi hình dạng.
- **Khác tài liệu tham chiếu:** tài liệu chỉnh c trực tiếp trên leaderboard. Ở đây c ước lượng hoàn toàn từ dữ liệu train, nên không có thông tin nào từ tập test lọt vào mô hình.

## Bước 8. Giải thích mô hình (SHAP)

TreeSHAP tính qua `predict(pred_contrib=True)` của LightGBM, chính xác cho mô hình cây (sai số cộng tính 4.6e-14). Đặc trưng được gom thành nhóm nghiệp vụ, vì các đặc trưng Fourier tương quan nhau nên xếp hạng từng đặc trưng đơn lẻ không ổn định.

| Nhóm | Revenue | COGS | Đọc theo ngôn ngữ kinh doanh |
|---|---:|---:|---|
| Mùa vụ năm | 58.7% | 58.5% | Tháng nào trong năm quyết định phần lớn doanh thu: cao điểm tháng 4–6 |
| Giai đoạn & xu hướng | 25.4% | 24.4% | Mức doanh thu sau 2019 thấp hơn hẳn trước đó |
| Đầu / cuối tháng | 6.3% | 7.3% | Khách mua dồn vào những ngày cuối tháng |
| Thứ trong tuần | 6.0% | 7.3% | Ngày thường cao hơn cuối tuần |
| Khuyến mãi | 2.6% | 1.6% | Khuyến mãi không phải động lực chính của doanh thu |
| Tết, năm chẵn/lẻ, lễ | < 1% | < 1% | Tác động hẹp, chỉ ở vài ngày trong năm |

**Tác động cục bộ:** ngày cuối cùng của tháng được dự báo cao hơn giữa tháng (ngày 13–17) **72.6%**, trong đó riêng nhóm đặc trưng đầu/cuối tháng đóng góp +29.1%. Với Tết và tháng 8 năm chẵn/lẻ, chênh lệch dự báo lớn (−43.5% và +39.7%) nhưng đến từ các đặc trưng khác; riêng cờ Tết và cờ năm lẻ chỉ đóng góp khoảng 1%.

**Ý nghĩa:** global importance là trung bình trên cả 548 ngày, nên pattern hiếm như Tết có điểm thấp dù tác động tại chỗ rõ. Đọc cả global lẫn cục bộ mới thấy đầy đủ mô hình dựa vào đâu.

## Bước 9. Submission

File [`submission.csv`](submission.csv): 548 dòng `Date,Revenue,COGS`, theo thứ tự ngày từ 2023-01-01 đến 2024-07-01.

**Checklist:**

- [x] Đúng 3 cột `Date,Revenue,COGS`.
- [x] 548 dòng, không có giá trị âm hoặc NaN (script tự `assert`).
- [x] Không dùng `Revenue`/`COGS` của tập test làm đặc trưng: mọi đặc trưng tính từ ngày tháng.
- [x] Không dùng dữ liệu ngoài: lịch khuyến mãi suy từ `promotions.csv`; Tết và ngày lễ là kiến thức lịch.
- [x] Tái lập được: `random_state = 42`, LightGBM `deterministic=True`.
- [ ] Đối chiếu thứ tự dòng với `sample_submission.csv` trước khi nộp: file này chưa có trong `data/raw/`, nên hiện tại các dòng được xếp theo thứ tự ngày.

## Dự báo và ý nghĩa kinh doanh

| | Thực tế 2022 | Dự báo 2023 | Thực tế 6 tháng đầu 2022 | Dự báo 6 tháng đầu 2024 |
|---|---:|---:|---:|---:|
| Revenue | 1.17 tỷ | 1.18 tỷ | 0.69 tỷ | 0.71 tỷ |
| COGS | 1.02 tỷ | 1.08 tỷ | 0.59 tỷ | 0.61 tỷ |

- **Doanh thu đi ngang, chưa hồi phục:** 2023 gần bằng 2022 (+1.2%), nửa đầu 2024 nhỉnh hơn cùng kỳ 2022 (+2.9%). Không có dấu hiệu quay lại mức 2014–2018.
- **Tháng 4–6 chiếm 37.9% doanh thu 2023:** tồn kho, nhân sự và vận chuyển cần sẵn sàng từ tháng 3.
- **Q3 2023 dự báo bán lỗ:** COGS/Revenue 1.05 (Q3 2022 là 0.89), trùng thời điểm Urban Blowout giảm 50% chỉ chạy năm lẻ. Nên xem lại mức giảm của chiến dịch này trước khi chạy năm 2023.
- **Cuối tháng là cao điểm ngắn hạn:** dự báo 3 ngày cuối tháng trung bình 5.55 triệu/ngày, gần gấp đôi giữa tháng (2.92 triệu). Đây là thời điểm hợp lý để đẩy chiến dịch và bảo đảm hàng.
- **Độ tin cậy:** sai số trên năm 2022 khoảng 0.54 triệu/ngày, tương đương 17% doanh thu trung bình ngày năm 2022. Dự báo dùng tốt cho kế hoạch theo tháng/quý; theo từng ngày chỉ nên coi là định hướng.

## Hạn chế

- Calibration giả định độ lệch mức của 2023–2024 giống năm 2022. Nếu thị trường thay đổi mạnh, hệ số này cần cập nhật.
- Prophet chưa đóng góp vào ensemble; có thể thử lại với cửa sổ dài hơn hoặc mùa vụ cộng tính.
- Chưa có điểm leaderboard và chưa đối chiếu `sample_submission.csv`.

## Cấu trúc và cách chạy

```text
forecasting/
├── README.md                # File này: các bước, ý nghĩa, kết quả
├── config.py                # Đường dẫn, seed, fold, ngày Tết và lễ, style biểu đồ
├── features.py              # Đọc sales.csv, suy lịch khuyến mãi, tạo 81 đặc trưng
├── 01_time_series_eda.py    # EDA → plots/eda_*.png, eda_stats.json, forecasting_eda.md
├── 02_train_forecast.py     # CV, ensemble, calibration, SHAP → submission.csv, forecasting_models.md
└── submission.csv           # File nộp, 548 dòng
```

```bash
python forecasting/01_time_series_eda.py
python forecasting/02_train_forecast.py      # khoảng 10 phút (3 fold × 2 target + train cuối)
python reports/build_reports.py              # dựng reports/04_Forecasting_report.pdf
```

Kết quả trung gian nằm ở `data/processed/forecasting/` (không commit): `cv_metrics.csv`, `forecast_summary.json`, `eda_stats.json`, `plots/`.

## Nhật ký cập nhật

| Ngày | Thay đổi |
|---|---|
| 2026-10-15 | Tạo folder và README mô tả flow, yêu cầu đề, lưu ý leakage và quy luật lịch khuyến mãi |
| 2026-10-16 | Triển khai pipeline: EDA chuỗi thời gian, 81 đặc trưng lịch, 3 fold, Ridge / LightGBM / Q-specialist / Prophet, ensemble 3 tầng, calibration, SHAP, `submission.csv` |
