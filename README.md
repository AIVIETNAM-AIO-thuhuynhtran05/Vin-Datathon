# Vin Datathon 2026 — Dashboard & Customer Analytics

Phân tích hoạt động kinh doanh của một doanh nghiệp thương mại điện tử thời trang tại Việt Nam, giai đoạn 2012–2022. Dự án gồm bốn phần:

- **EDA & chất lượng dữ liệu**
- **Dashboard Power BI** (5 trang, đi từ tổng quan đến chi tiết)
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
│   ├── behavior_features.py             # Biến hành vi dùng chung (FE + profiling)
│   ├── 02_transform_features.py         # Feature engineering: biến đổi, scale, đánh giá biến ứng viên
│   ├── 03_pca_analysis.py               # PCA + giải thích
│   ├── segment_naming.py                # Luật đặt tên cụm gợi ý + hành động
│   ├── 04_select_k.py                   # Quét k, đánh giá thống kê + ổn định + business
│   ├── 05_kmeans_segmentation.py        # K-Means với k đã chọn (tự điều chỉnh)
│   └── 06_cluster_profiling.py          # Bức tranh tổng thể, profile, gợi ý hành động
├── forecasting/                         # Dự báo doanh thu — xem README riêng (chưa có code)
│   └── README.md                        # Flow: yêu cầu đề → dữ liệu → FE → validation → mô hình → submission
├── dashboard/
│   ├── README.md                        # Cấu trúc 5 trang, mô hình dữ liệu, KPI & phân tích
│   └── Ecommerce_Dashboard.pbix         # Chỉ lưu local, không đưa lên Git
├── reports/                             # Báo cáo PDF — mỗi phần một file
│   ├── 01_EDA_report.pdf                # EDA & chất lượng dữ liệu
│   ├── 02_Dashboard_report.pdf          # (chờ dựng lại dashboard)
│   ├── 03_Customer_Segmentation_report.pdf
│   ├── 04_Forecasting_report.pdf        # (chờ triển khai)
│   ├── build_reports.py                 # Dựng PDF từ Markdown
│   └── markdown/                        # Nguồn Markdown của các báo cáo
│       ├── 00_data_overview.md          # Mô tả tổng quan & ý nghĩa từng bảng
│       ├── data_quality_and_eda.md      # (tự sinh) Chất lượng dữ liệu & EDA
│       ├── customer_segmentation_pca.md # (tự sinh) PCA
│       ├── customer_segmentation_k_selection.md  # (tự sinh) Chọn số cụm k
│       ├── customer_segment_profiles.md # (tự sinh) Profile các nhóm khách hàng
│       └── dashboard_analysis_recommendations.md
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
- Báo cáo là **PDF trong `reports/`, mỗi phần một file**. Nguồn Markdown nằm trong `reports/markdown/` (hoặc README của từng folder) và được dựng thành PDF bằng `python reports/build_reports.py`.
- Mỗi folder code là một mảng công việc. Các file đánh số theo thứ tự chạy.

## Tổng quan dữ liệu

Dữ liệu vận hành trải từ **04/07/2012 đến 31/12/2022**, gồm 13 tệp CSV chia thành 4 nhóm:

- **Master:** `products`, `customers`, `promotions`, `geography`.
- **Transaction:** `orders`, `order_items`, `payments`, `shipments`, `returns`, `reviews`.
- **Analytical:** `sales`.
- **Operational:** `inventory`, `web_traffic`.

Tài liệu đề thi mô tả 15 tệp; `sample_submission.csv` và `inventory_enhanced.csv` chưa có trong `data/raw/`.

Mô tả số dòng, số cột, ý nghĩa, khóa và cột của từng bảng: [`reports/markdown/00_data_overview.md`](reports/markdown/00_data_overview.md).

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

# 3. Dựng báo cáo PDF (cần Microsoft Edge hoặc Google Chrome)
python reports/build_reports.py                  # thêm --include-drafts để dựng cả bản nháp
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
- **Báo cáo:** [`reports/01_EDA_report.pdf`](reports/01_EDA_report.pdf) (nguồn: [`reports/markdown/data_quality_and_eda.md`](reports/markdown/data_quality_and_eda.md)).

**Phát hiện chính ảnh hưởng đến phân tích:**

- 3.633 đơn có tổng tiền hoàn vượt tiền thanh toán, do tiền hoàn tính theo giá **trước** giảm giá.
- 564 đơn đã gửi/giao nhưng thiếu bản ghi vận chuyển.
- 73,8% đơn có ngày đặt trước ngày đăng ký, nên `signup_date` không đáng tin.

## 2. Dashboard

> 🔄 **Đang dựng lại:** bản v1 dùng 5 bảng phẳng, chỉ có 2 quan hệ, chưa có bảng ngày dùng chung và chưa áp dụng data cleaning từ bước EDA. Bản mới dựng lại trên star schema theo cấu trúc 5 trang bên dưới.

Dashboard đi từ tổng quan đến chi tiết, xoay quanh một cây KPI:

- **Revenue** = Sessions × Conversion Rate × AOV
- **Gross Profit** = Revenue × Gross Margin %

Trang Overview trả lời doanh thu giảm là do yếu tố nào: traffic, CR hay AOV. Mỗi trang sau đi sâu vào đúng một yếu tố:

| Trang | Câu hỏi | Nội dung chính |
|---|---|---|
| Executive Overview | Doanh nghiệp đang lên hay xuống, vì sao? | KPI so với năm trước, cây KPI, xu hướng 2012–2022 |
| Customer | Khách có mua và có quay lại không? | Funnel khách đăng ký → khách đã mua, cohort retention theo tháng đơn đầu tiên, phân khúc RFM từ phần 3 |
| Sales & Promotion | Tiền và lãi đến từ đâu, khuyến mãi có hiệu quả không? | Category và margin, AOV và margin khi có hoặc không có khuyến mãi |
| Inventory | Tồn kho có cân với nhu cầu không? | DOS đã sửa công thức, stockout/overstock, hàng chậm bán (DOS > 365 ngày) |
| Logistics & Returns | Hàng có đến nơi, có bị trả lại không? | Thời gian giao theo vùng, lý do trả hàng, Wrong Size theo sản phẩm |

**Biến đổi dữ liệu:** dùng SQL (DuckDB, chạy từ Python) đọc `data/raw/`, ghi ra `data/processed/powerbi/`; Power BI chỉ import.

1. Nạp 13 file CSV gốc vào DuckDB, chỉ đọc.
2. Dựng các bảng dimension, trong đó `dim_date` gồm mọi ngày từ 04/07/2012 đến 31/12/2022.
3. Dựng từng bảng fact theo một grain rõ ràng. Doanh thu dòng hàng = số lượng × đơn giá − giảm giá.
4. Lọc các đơn không tạo ra doanh thu: 7.275 đơn `created` và 59.462 đơn `cancelled` (tổng 66.737 đơn, 10,3%). Bảng dòng hàng chỉ giữ đơn `paid`/`shipped`/`delivered`/`returned`; bảng đơn hàng vẫn giữ mọi trạng thái để tính tỷ lệ hủy.
5. Áp dụng quy tắc cleaning từ bước EDA: giới hạn tiền hoàn bằng tiền đã trả, loại đơn thiếu bản ghi vận chuyển khỏi KPI thời gian giao, không dùng `sales.csv` trong model.
6. Kiểm tra trước khi xuất: khóa chính không trùng, khóa ngoại đều có trong dimension, số dòng khớp nguồn, doanh thu dòng hàng khớp `payments`.
7. Nạp vào Power BI: quan hệ 1-nhiều một chiều, đánh dấu `dim_date` là bảng ngày, ngày gửi/giao là quan hệ inactive, mọi measure DAX nằm trong bảng `_Measures`.

**Mô hình dữ liệu (star schema):**

- **Fact:** `fact_order_items` (dòng hàng), `fact_orders` (đơn, gộp `payments` và `shipments` vì cả hai 1 dòng/đơn), `fact_returns` (lần trả), `fact_inventory` (sản phẩm-tháng), `fact_web_traffic` (ngày).
- **Dimension:** `dim_date` (dùng chung cho mọi fact), `dim_customer`, `dim_product`, `dim_geography`, `dim_promotion`.

Định nghĩa từng KPI, công thức và trang chứa KPI: [`dashboard/README.md`](dashboard/README.md).

- **Power BI:** `dashboard/Ecommerce_Dashboard.pbix` — file nặng (~110 MB) nên chỉ lưu local, không đưa lên GitHub.
- **Phân tích & khuyến nghị:** [`reports/markdown/dashboard_analysis_recommendations.md`](reports/markdown/dashboard_analysis_recommendations.md)

## 3. Phân nhóm khách hàng

Hai lớp phân nhóm cho **toàn bộ** 121.930 khách hàng:

- **Rule-based** cho khách chưa có đơn phát sinh doanh thu:
  - RB1 — chưa giao dịch (chưa đặt đơn nào).
  - RB2 — đặt đơn nhưng chưa chuyển đổi (mọi đơn đều bị hủy hoặc bỏ dở).
- **K-Means trên RFM** (log1p → scale → PCA) cho khách có đơn `paid`/`shipped`/`delivered`/`returned` (business rule: đơn đã thanh toán là có doanh thu).

Nhân khẩu học không tham gia phân cụm; chỉ dùng để mô tả chân dung từng nhóm.

Flow chi tiết, định nghĩa biến và quyết định xử lý: [`customer_segmentation/README.md`](customer_segmentation/README.md).

## 4. Dự báo doanh thu ✍️

> ⏳ Chưa triển khai. Flow, yêu cầu đề, lưu ý leakage và kế hoạch validation: [`forecasting/README.md`](forecasting/README.md).

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
