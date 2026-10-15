# Vin Datathon 2026 — Dashboard & Customer Analytics

Phân tích hoạt động kinh doanh của một doanh nghiệp thương mại điện tử thời trang tại Việt Nam, giai đoạn 2012–2022. Dự án gồm bốn phần:

- **EDA & chất lượng dữ liệu**
- **Dashboard Power BI**
- **Phân nhóm khách hàng** (rule-based + K-Means)
- **Dự báo doanh thu** theo ngày cho giai đoạn 01/01/2023–01/07/2024

## Cấu trúc dự án

```text
.
├── eda/
│   └── data_quality_eda.py              # EDA & kiểm tra chất lượng dữ liệu theo từng bảng
├── customer_segmentation/               # Phân nhóm khách hàng — xem README riêng
│   ├── README.md                        # Flow: mục đích → dữ liệu → FE → K-Means → profile → recommendation
│   ├── config.py                        # Đường dẫn & tham số dùng chung
│   ├── plot_style.py                    # Màu/style biểu đồ
│   ├── 01_build_customer_dataset.py     # Aggregation, quality check, rule-based segmentation
│   ├── 02_transform_features.py         # log1p + StandardScaler
│   ├── 03_pca_analysis.py               # PCA + giải thích
│   ├── segment_naming.py                # Luật đặt tên cụm gợi ý + hành động
│   ├── 04_select_k.py                   # Quét k, đánh giá thống kê + ổn định + business
│   ├── 05_kmeans_segmentation.py        # K-Means với k đã chọn (tự điều chỉnh)
│   └── 06_cluster_profiling.py          # Bức tranh tổng thể, profile, gợi ý hành động
├── dashboard/
│   ├── README.md                        # Phân tích dashboard (đang rà soát)
│   └── Ecommerce_Dashboard.pbix         # Chỉ lưu local, không đưa lên Git
├── reports/
│   ├── 00_data_overview.md              # Mô tả tổng quan & ý nghĩa từng bảng
│   ├── data_quality_and_eda.md          # (tự sinh) Chất lượng dữ liệu & EDA
│   ├── customer_segmentation_pca.md     # (tự sinh) PCA
│   ├── customer_segmentation_k_selection.md  # (tự sinh) Chọn số cụm k
│   ├── customer_segment_profiles.md     # (tự sinh) Profile các nhóm khách hàng
│   └── dashboard_analysis_recommendations.md
├── data/
│   ├── raw/                             # CSV gốc (chỉ đọc)
│   └── processed/                       # Tự sinh, không đưa vào Git
│       ├── eda/
│       └── customer_segmentation/
├── notebooks/                           # Notebook thử nghiệm
├── docs/                                # Đề thi, tài liệu tham khảo
└── requirements.txt
```

**Nguyên tắc chung:**

- Code chỉ đọc `data/raw/`, ghi kết quả vào `data/processed/` (không commit).
- Báo cáo Markdown đặt trong `reports/`.
- Mỗi folder code là một mảng công việc. Các file đánh số theo thứ tự chạy.

## Tổng quan dữ liệu

Dữ liệu vận hành trải từ **04/07/2012 đến 31/12/2022**, gồm 13 tệp CSV chia thành 4 nhóm:

- **Master:** `products`, `customers`, `promotions`, `geography`.
- **Transaction:** `orders`, `order_items`, `payments`, `shipments`, `returns`, `reviews`.
- **Analytical:** `sales`.
- **Operational:** `inventory`, `web_traffic`.

Tài liệu đề thi mô tả 15 tệp; `sample_submission.csv` và `inventory_enhanced.csv` chưa có trong `data/raw/`.

Mô tả số dòng, số cột, ý nghĩa, khóa và cột của từng bảng: [`reports/00_data_overview.md`](reports/00_data_overview.md).

Các bảng liên kết qua `customer_id`, `product_id`, `order_id`, `promo_id` và `zip`. Grain khác nhau giữa các bảng:

- `orders`: cấp đơn.
- `order_items`: cấp dòng sản phẩm.
- `inventory`: cấp sản phẩm-tháng.
- `web_traffic`: cấp ngày.

Vì vậy cần tổng hợp về cùng grain trước khi nối bảng.

Bài toán dự báo doanh thu:

- Huấn luyện: **04/07/2012–31/12/2022**.
- Kiểm tra: **01/01/2023–01/07/2024**.

## Cài đặt và chạy

```bash
python -m pip install -r requirements.txt

# 1. EDA & chất lượng dữ liệu
python eda/data_quality_eda.py

# 2. Phân nhóm khách hàng
python customer_segmentation/01_build_customer_dataset.py
python customer_segmentation/02_transform_features.py
python customer_segmentation/03_pca_analysis.py
python customer_segmentation/04_select_k.py                    # chọn k
python customer_segmentation/05_kmeans_segmentation.py --k <k> # tự điều chỉnh
python customer_segmentation/06_cluster_profiling.py
```

## 1. EDA & chất lượng dữ liệu

[`eda/data_quality_eda.py`](eda/data_quality_eda.py) kiểm tra từng bảng theo 5 nhóm:

1. **Missing values:** phân biệt thiếu bắt buộc với trống có ý nghĩa (như `promo_id` trống = không dùng khuyến mãi).
2. **Trùng lặp:** toàn dòng, khóa chính, khóa nghiệp vụ.
3. **Dữ liệu không hợp lệ:** sai kiểu số/ngày, ngoài miền giá trị, giá trị âm, ngày ngoài phạm vi.
4. **Ràng buộc nghiệp vụ:**
   - Khóa ngoại tồn tại.
   - Tiền hoàn ≤ tiền thanh toán; số lượng trả ≤ số lượng mua.
   - Ngày đặt ≤ ngày gửi ≤ ngày giao ≤ ngày trả/đánh giá.
   - `payment_value` = Σ dòng hàng.
   - Khuyến mãi đúng thời gian và đúng danh mục.
5. **Outlier:** rào IQR 1,5×/3× trên thang gốc và thang log.

Mỗi kiểm tra có mức ERROR/WARNING/INFO kèm đề xuất xử lý. Script chỉ gắn cờ, không sửa dữ liệu gốc.

- **Kết quả** (trong `data/processed/eda/`):
  - `data_quality_checks.csv`, `missing_values.csv`, `outliers.csv`, `table_overview.csv`
  - `violations/<bảng>__<kiểm tra>.csv`: các dòng vi phạm
  - `plots/`: biểu đồ
- **Báo cáo:** [`reports/data_quality_and_eda.md`](reports/data_quality_and_eda.md).

**Phát hiện chính ảnh hưởng đến phân tích:**

- 3.633 đơn có tổng tiền hoàn vượt tiền thanh toán, do tiền hoàn tính theo giá **trước** giảm giá.
- 564 đơn đã gửi/giao nhưng thiếu bản ghi vận chuyển.
- 73,8% đơn có ngày đặt trước ngày đăng ký, nên `signup_date` không đáng tin.

## 2. Dashboard

> ⏳ **Đang rà soát:** dashboard chưa được kiểm tra lại và chưa áp dụng data cleaning từ bước EDA. Nội dung phân tích dashboard tạm để ở [`dashboard/README.md`](dashboard/README.md).

- **Power BI:** `dashboard/Ecommerce_Dashboard.pbix` — file nặng (~110 MB) nên chỉ lưu local, không đưa lên GitHub.
- **Phân tích & khuyến nghị:** [`reports/dashboard_analysis_recommendations.md`](reports/dashboard_analysis_recommendations.md)

## 3. Phân nhóm khách hàng

Hai lớp phân nhóm cho **toàn bộ** 121.930 khách hàng:

- **Rule-based** cho khách chưa có đơn phát sinh doanh thu:
  - RB1 — chưa giao dịch (chưa đặt đơn nào).
  - RB2 — đặt đơn nhưng chưa chuyển đổi (mọi đơn đều bị hủy hoặc bỏ dở).
- **K-Means trên RFM** (log1p → scale → PCA) cho khách có đơn `paid`/`shipped`/`delivered`/`returned` (business rule: đơn đã thanh toán là có doanh thu).

Nhân khẩu học không tham gia phân cụm; chỉ dùng để mô tả chân dung từng nhóm.

Flow chi tiết, định nghĩa biến và quyết định xử lý: [`customer_segmentation/README.md`](customer_segmentation/README.md).

## 4. Dự báo doanh thu ✍️

> ⏳ Chưa triển khai.

- **Mục tiêu:** dự báo `Revenue` theo ngày.
- **Dữ liệu huấn luyện:** `sales.csv`, từ 04/07/2012 đến 31/12/2022 (3.833 ngày, chuỗi liên tục, không thiếu ngày).
- **Giai đoạn dự báo:** 01/01/2023–01/07/2024.
- **Lưu ý từ EDA:**
  - `sales.Revenue` = Σ(số lượng × đơn giá) của **mọi đơn trong ngày**: tính trước giảm giá, gồm cả đơn hủy. Định nghĩa này khác với `payments.payment_value` và với doanh thu dùng trong phần phân nhóm khách hàng.
  - Có 382 ngày `COGS` > `Revenue`.
  - 169 ngày doanh thu cao vượt rào IQR, tập trung vào **tháng 4–6** (mùa vụ), **không** trùng đợt khuyến mãi: chỉ 31% các ngày này có khuyến mãi, so với 45% trên toàn bộ các ngày. Median doanh thu ngày có khuyến mãi còn thấp hơn ngày không có. Nên giữ các ngày này và mô hình hóa mùa vụ, không xóa như outlier.
- **Biến hỗ trợ có thể dùng:**
  - Lịch khuyến mãi (`promotions`).
  - Lưu lượng truy cập (`web_traffic`, có từ 01/01/2013).
  - Mùa vụ: ngày trong tuần, tháng, lễ Tết.
- `sample_submission.csv` (định dạng nộp bài) chưa có trong `data/raw/`.
