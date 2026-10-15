# Revenue Forecasting

Dự báo doanh thu theo ngày (`Revenue`) cho giai đoạn **01/01/2023 – 01/07/2024**. Đây là Phần 3 của đề thi, chiếm 20 điểm.

> README này mô tả **flow** của phần dự báo. Các mục đánh dấu ✍️ là chỗ cần điền khi có kết quả cụ thể. Folder hiện chưa có code.

## Flow tổng quan

```text
sales.csv ─► 1. Chuẩn bị ─► 2. EDA chuỗi ─► 3. Feature ─► 4. Validation ─► 5. Mô hình ─► 6. Giải thích ─► 7. Submission
            (ngày, QC)     thời gian        engineering   theo thời gian   (so baseline)   (SHAP)          (Kaggle + GitHub)
```

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 1 | Chuẩn bị dữ liệu ngày, kiểm tra chất lượng | ⏳ |
| 2 | EDA chuỗi thời gian: xu hướng, mùa vụ, điểm gãy | ⏳ |
| 3 | Feature engineering: lịch, khuyến mãi, lịch sử | ⏳ |
| 4 | Thiết kế validation theo chiều thời gian + baseline | ⏳ |
| 5 | Huấn luyện và so sánh mô hình | ✍️ |
| 6 | Giải thích mô hình (SHAP / feature importance) | ⏳ |
| 7 | Tạo `submission.csv`, kiểm tra định dạng, nộp Kaggle | ⏳ |

---

## 0. Yêu cầu của đề

**Bài toán:** dự báo cột `Revenue` cho từng ngày trong `sales_test.csv`, tổng cộng **548 ngày**.

**Chỉ số đánh giá:** chấm trên Kaggle leaderboard.

| Chỉ số | Ý nghĩa | Tốt khi |
|---|---|---|
| MAE | Sai số tuyệt đối trung bình | Thấp |
| RMSE | Phạt nặng các sai số lớn | Thấp |
| R² | Tỷ lệ phương sai giải thích được | Gần 1 |

**Thang điểm (20 điểm):**

- **Hiệu suất mô hình (12 điểm):** xếp hạng theo MAE, RMSE, R² trên leaderboard.
- **Báo cáo kỹ thuật (8 điểm):** pipeline rõ ràng, cross-validation đúng chiều thời gian, kiểm soát leakage, giải thích mô hình bằng SHAP hoặc tương đương, tuân thủ đủ ràng buộc.

**Điều kiện loại toàn bộ Phần 3:** vi phạm một trong ba điều sau là mất cả 20 điểm.

1. Dùng `Revenue`/`COGS` của tập test làm đặc trưng.
2. Dùng dữ liệu ngoài bộ dữ liệu được cung cấp.
3. Không đính kèm mã nguồn, hoặc kết quả không tái lập được (phải đặt random seed).

**Định dạng nộp:**

- File `submission.csv` gồm 3 cột `Date,Revenue,COGS`.
- Số dòng và **thứ tự dòng** phải giống hệt `sample_submission.csv`, không sắp xếp lại.
- File này phải nằm trong repo GitHub.

## 1. Dữ liệu

| File | Có trong `data/raw/`? | Dùng để |
|---|:---:|---|
| `sales.csv` | ✅ | Biến mục tiêu `Revenue` (và `COGS`), 04/07/2012 – 31/12/2022 |
| `sample_submission.csv` | ❌ cần tải từ Kaggle | Danh sách ngày và thứ tự dòng của file nộp |
| `promotions.csv` | ✅ | Lịch khuyến mãi (có thể suy ra cho giai đoạn dự báo, xem mục 3) |
| `orders`, `order_items`, `web_traffic`, `inventory` | ✅ | Chỉ dùng được cho giai đoạn train (xem lưu ý bên dưới) |

**Đặc điểm của `sales.csv`:**

- 3.833 ngày liên tục, không thiếu ngày, không trùng ngày.
- **Định nghĩa doanh thu:** đề gọi `Revenue` là "tổng doanh thu thuần". Khi đối soát với dữ liệu giao dịch, `Revenue` = Σ(`quantity` × `unit_price`) của **mọi đơn trong ngày, kể cả đơn hủy**, chưa trừ `discount_amount`. Vì vậy nó khác `payments.payment_value` và khác doanh thu trong phần phân nhóm khách hàng.
- Có 382 ngày `COGS` > `Revenue`.

**Lưu ý quan trọng về leakage:** mọi bảng khác chỉ có dữ liệu đến **31/12/2022**. Trong giai đoạn dự báo không có đơn hàng, web traffic hay tồn kho. Vì vậy:

- Không dùng trực tiếp các bảng đó làm feature cho ngày cần dự báo.
- Chỉ dùng được: thông tin lịch, lịch khuyến mãi suy ra từ quy luật, và lịch sử doanh thu với độ trễ phù hợp (mục 3).

## 2. EDA chuỗi thời gian ⏳

Các điểm đã thấy từ bước EDA chung:

- **Xu hướng và điểm gãy:** doanh thu theo năm tăng đến đỉnh năm 2016 (khoảng 2,11 tỷ), giảm dần đến 2018 (khoảng 1,85 tỷ), rồi **giảm mạnh năm 2019** (khoảng 1,14 tỷ) và đi ngang đến 2022 (khoảng 1,17 tỷ). Mô hình cần xử lý điểm gãy này: chọn cửa sổ train phù hợp hoặc thêm biến xu hướng/chế độ.
- **Mùa vụ năm:** 169 ngày doanh thu cao vượt rào IQR tập trung vào **tháng 4–6**.
- **Khuyến mãi không phải nguyên nhân của các đỉnh:** chỉ 31% ngày doanh thu cao rơi vào đợt khuyến mãi, so với 45% trên toàn bộ các ngày. Doanh thu trung vị của ngày có khuyến mãi còn thấp hơn ngày không có.

✍️ Cần làm thêm:

- Mùa vụ theo ngày trong tuần và ngày trong tháng.
- Phân rã chuỗi (trend / seasonal / residual).
- Kiểm tra phương sai có tăng theo mức doanh thu không, để quyết định có log-transform hay không.

## 3. Feature engineering ⏳

| Nhóm feature | Ví dụ | Dùng được cho giai đoạn dự báo? |
|---|---|:---:|
| Lịch | Ngày trong tuần, tháng, quý, ngày trong năm, cuối tuần, đầu/cuối tháng, biến Fourier mùa vụ | ✅ |
| Xu hướng / chế độ | Chỉ số thời gian, cờ giai đoạn sau 2019 | ✅ |
| Lịch khuyến mãi suy ra | Cờ "đang trong đợt khuyến mãi", loại khuyến mãi | ✅ suy từ quy luật trong `promotions.csv` |
| Lịch sử doanh thu | Doanh thu cùng ngày năm trước, trung bình cùng kỳ | ⚠️ chỉ khi độ trễ ≥ 548 ngày, hoặc dự báo đệ quy |
| Giao dịch / web / tồn kho | Số đơn, sessions, tồn kho | ❌ không có cho 2023–2024 |

**Quy luật lịch khuyến mãi** (suy từ `promotions.csv`, nên không vi phạm quy định dữ liệu ngoài):

- **Hằng năm, cùng tháng bắt đầu:** Spring Sale (tháng 3), Mid-Year Sale (tháng 6), Fall Launch (tháng 8), Year-End Sale (tháng 11).
- **Chỉ năm lẻ:** Rural Special (tháng 1), Urban Blowout (tháng 7). Theo quy luật này, năm 2023 sẽ có, 2024 thì không.

✍️ **Cần quyết định:**

- **Ngày lễ / Tết âm lịch:** có tạo cờ không? Lịch âm là kiến thức lịch chứ không phải dataset, nhưng nên ghi rõ trong báo cáo để tránh bị coi là dữ liệu ngoài.
- **Dự báo `COGS`:** file nộp có cột `COGS` dù đề chỉ chấm `Revenue`. Có thể dùng tỷ lệ COGS/Revenue lịch sử, hoặc một mô hình riêng.

## 4. Validation theo chiều thời gian ⏳

- **Không xáo trộn dữ liệu.** Dùng **rolling-origin / expanding window**: mỗi fold train trên quá khứ, rồi dự báo một khoảng **548 ngày liền sau** (đúng độ dài horizon thật).

  | Fold | Train đến hết | Dự báo |
  |---|---|---|
  | 1 | 30/06/2019 | 01/07/2019 – 31/12/2020 |
  | 2 | 30/06/2020 | 01/07/2020 – 31/12/2021 |
  | 3 | 30/06/2021 | 01/07/2021 – 31/12/2022 |

- **Baseline để so sánh:**
  - Seasonal naive: doanh thu cùng ngày năm trước.
  - Trung bình theo (tháng × ngày trong tuần) của năm gần nhất.
- **Báo cáo** MAE, RMSE, R² theo từng fold và trung bình các fold.

## 5. Mô hình ✍️

- **Ứng viên:**
  - Mô hình cộng tính trend + mùa vụ.
  - Gradient boosting trên feature lịch (LightGBM / XGBoost / sklearn).
  - Ensemble các mô hình trên.
- **Ghi lại cho mỗi mô hình:** feature dùng, tham số, điểm CV, và so sánh với baseline.
- **Đặt `random_state` cố định** cho mọi mô hình có yếu tố ngẫu nhiên.

| Mô hình | MAE (CV) | RMSE (CV) | R² (CV) | Ghi chú |
|---|---:|---:|---:|---|
| Seasonal naive | | | | Baseline |
| … | | | | |

✍️ **Mô hình chọn:** … · **Lý do:** … · **Điểm Kaggle:** …

## 6. Giải thích mô hình ⏳

Yêu cầu của đề: giải thích các yếu tố dẫn động doanh thu bằng **ngôn ngữ kinh doanh**.

- Dùng SHAP values, feature importance hoặc partial dependence plots.
- ✍️ Các yếu tố chính: … (ví dụ: mùa vụ tháng 4–6, ngày trong tuần, xu hướng sau 2019, đợt khuyến mãi).

## 7. Submission ⏳

**Checklist trước khi nộp:**

- [ ] Đúng 3 cột `Date,Revenue,COGS`.
- [ ] Số dòng và thứ tự giống hệt `sample_submission.csv`.
- [ ] Không có giá trị âm hoặc NaN.
- [ ] Không dùng `Revenue`/`COGS` của tập test làm đặc trưng.
- [ ] Chạy lại từ đầu ra đúng file nộp (đã đặt seed).
- [ ] File `submission.csv` được commit trong folder này.

## 8. Kết quả và ý nghĩa kinh doanh ✍️

- **Dự báo tổng doanh thu** 2023 và nửa đầu 2024; so sánh với 2022.
- **Gợi ý cho kế hoạch kinh doanh:**
  - Tồn kho và logistics cho cao điểm tháng 4–6.
  - Lịch khuyến mãi.
  - Mức độ tin cậy của dự báo (khoảng sai số theo CV).

## Nhật ký cập nhật ✍️

| Ngày | Thay đổi |
|---|---|
| 2026-10-15 | Tạo folder và README mô tả flow, yêu cầu đề, lưu ý leakage và quy luật lịch khuyến mãi |
