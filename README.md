# Vin Datathon 2026 — Dashboard, Customer Analytics & Forecasting

Phân tích hoạt động kinh doanh của một doanh nghiệp thương mại điện tử thời trang tại Việt Nam, giai đoạn 2012–2022. Dự án gồm bốn phần:

- **EDA & chất lượng dữ liệu**
- **Dashboard Power BI** (5 trang, đi từ tổng quan đến chi tiết)
- **Phân nhóm khách hàng** (rule-based + K-Means)
- **Dự báo doanh thu** theo ngày cho giai đoạn 01/01/2023–01/07/2024 (ensemble Ridge + LightGBM, R² 0.807 trên năm 2022)

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
├── forecasting/                         # Dự báo doanh thu — xem README riêng
│   ├── README.md                        # Các bước, ý nghĩa từng bước, kết quả
│   ├── config.py                        # Đường dẫn, seed, fold, ngày Tết & lễ, style biểu đồ
│   ├── features.py                      # 81 đặc trưng chỉ từ lịch + lịch khuyến mãi suy từ promotions.csv
│   ├── 01_time_series_eda.py            # EDA chuỗi thời gian
│   ├── 02_train_forecast.py             # CV, ensemble 3 tầng, calibration, SHAP, file nộp
│   └── submission.csv                   # File nộp, 548 dòng Date,Revenue,COGS
├── dashboard/
│   ├── README.md                        # Cấu trúc 5 trang, mô hình dữ liệu, KPI & phân tích
│   ├── build_powerbi_tables.py          # Gộp CSV gốc thành 10 bảng import vào Power BI (DuckDB)
│   └── Ecommerce_Dashboard.pbix         # Chỉ lưu local, không đưa lên Git
├── reports/                             # Báo cáo PDF — mỗi phần một file
│   ├── 01_EDA_report.pdf                # EDA & chất lượng dữ liệu
│   ├── 02_Dashboard_report.pdf          # (chờ dựng lại dashboard)
│   ├── 03_Customer_Segmentation_report.pdf
│   ├── 04_Forecasting_report.pdf        # Dự báo doanh thu
│   ├── build_reports.py                 # Dựng PDF từ Markdown
│   └── markdown/                        # Nguồn Markdown của các báo cáo
│       ├── 00_data_overview.md          # Mô tả tổng quan & ý nghĩa từng bảng
│       ├── data_quality_and_eda.md      # (tự sinh) Chất lượng dữ liệu & EDA
│       ├── customer_segmentation_pca.md # (tự sinh) PCA
│       ├── customer_segmentation_k_selection.md  # (tự sinh) Chọn số cụm k
│       ├── customer_segment_profiles.md # (tự sinh) Profile các nhóm khách hàng
│       ├── forecasting_eda.md           # (tự sinh) EDA chuỗi thời gian
│       ├── forecasting_models.md        # (tự sinh) Mô hình, CV, SHAP, dự báo
│       └── dashboard_analysis_recommendations.md
├── data/
│   ├── raw/                             # CSV gốc (chỉ đọc)
│   └── processed/                       # Tự sinh, không đưa vào Git
│       ├── eda/
│       ├── customer_segmentation/
│       └── forecasting/
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

# 3. Dự báo doanh thu (khoảng 10 phút)
python forecasting/01_time_series_eda.py
python forecasting/02_train_forecast.py

# 4. Dựng báo cáo PDF (cần Microsoft Edge hoặc Google Chrome)
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

> 🔄 **Đang dựng lại:** bản v1 dùng 5 bảng phẳng, chỉ có 2 quan hệ, chưa có bảng ngày dùng chung và chưa áp dụng data cleaning từ bước EDA. Bản mới gộp lại dữ liệu cho sạch, làm data modeling trong Power BI và theo cấu trúc 5 trang bên dưới.

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

**Biến đổi dữ liệu** — [`dashboard/build_powerbi_tables.py`](dashboard/build_powerbi_tables.py): Python chạy SQL trên DuckDB, đọc `data/raw/`, gộp bảng và ghi ra `data/processed/powerbi/`. Power BI chỉ import rồi làm data modeling.

1. Nạp 13 file CSV gốc vào DuckDB, chỉ đọc.
2. Gộp các bảng cùng grain: dòng hàng + đơn + giá vốn sản phẩm + loại khuyến mãi (`sales_lines`); đơn + thanh toán + vận chuyển (`orders`); lần trả + khách và zip của đơn (`returns`). Bảng khách hàng thêm vùng và phân khúc từ phần 3.
3. Lọc các đơn không tạo ra doanh thu: 7.275 đơn `created` và 59.462 đơn `cancelled` (tổng 66.737 đơn, 10,3%). `sales_lines` chỉ giữ đơn `paid`/`shipped`/`delivered`/`returned`; `orders` vẫn giữ mọi trạng thái để tính tỷ lệ hủy.
4. Áp dụng quy tắc cleaning từ bước EDA: giới hạn tiền hoàn bằng tiền đã trả, loại đơn thiếu bản ghi vận chuyển khỏi KPI thời gian giao, bỏ cột hằng số `reorder_flag`, không dùng `sales.csv`. Web traffic chỉ dùng theo ngày: `traffic_source` mỗi ngày chỉ có 1 nguồn nên không tách được theo kênh, `bounce_rate` (0,3–0,6%) thấp phi thực tế nên không đưa vào KPI.
5. Kiểm tra trước khi xuất (script dừng nếu không đạt): khóa chính không trùng, khóa ngoại đều có trong bảng tra cứu, số dòng khớp nguồn, doanh thu dòng hàng khớp `payments` của cùng các đơn.
6. Data modeling trong Power BI: bảng ngày tạo bằng DAX và đánh dấu Date Table; quan hệ 1-nhiều một chiều từ bảng tra cứu sang bảng dữ liệu (ngày gửi/giao là quan hệ inactive); mọi measure DAX nằm trong bảng `_Measures`.

**Đầu ra (10 file CSV):**

| Loại | File | 1 dòng = | Số dòng |
|---|---|---|---:|
| Dữ liệu | `sales_lines.csv` | 1 dòng hàng của đơn có doanh thu | 641.002 |
| Dữ liệu | `orders.csv` | 1 đơn (mọi trạng thái) | 646.945 |
| Dữ liệu | `returns.csv` | 1 lần trả 1 sản phẩm | 39.939 |
| Dữ liệu | `reviews.csv` | 1 đánh giá | 113.551 |
| Dữ liệu | `inventory.csv` | 1 sản phẩm / 1 tháng | 60.247 |
| Dữ liệu | `web_traffic.csv` | 1 ngày | 3.652 |
| Tra cứu | `customers.csv` | 1 khách (kèm vùng, phân khúc) | 121.930 |
| Tra cứu | `products.csv` | 1 SKU | 2.412 |
| Tra cứu | `promotions.csv` | 1 chương trình | 50 |
| Tra cứu | `geography.csv` | 1 mã bưu chính | 39.948 |

Các bảng dữ liệu **không nối trực tiếp với nhau**; mọi so sánh giữa chúng đi qua bảng ngày và bảng tra cứu dùng chung.

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

## 4. Dự báo doanh thu

Dự báo `Revenue` và `COGS` theo ngày cho 548 ngày (01/01/2023 – 01/07/2024) từ `sales.csv`. Chi tiết từng bước và ý nghĩa: [`forecasting/README.md`](forecasting/README.md). Báo cáo: `reports/04_Forecasting_report.pdf`.

| Bước | Làm gì | Ý nghĩa |
|---|---|---|
| 1. Hiểu ràng buộc | Horizon 18 tháng, cấm dùng giá trị test và dữ liệu ngoài, phải tái lập được | Không dùng được lag; mọi đặc trưng phải tính được cho 2023–2024 |
| 2. EDA chuỗi thời gian | 4 giai đoạn (mức sau 2019 thấp hơn đỉnh 43.5%), mùa vụ tháng 4–6, cuối tháng cao gấp đôi giữa tháng, Tết, năm chẵn/lẻ, margin Q3 | Mỗi pattern thành một nhóm đặc trưng hoặc một quyết định mô hình |
| 3. Đặc trưng chỉ từ lịch | 81 đặc trưng: lịch, đầu/cuối tháng, Fourier, Tết, lễ, lịch khuyến mãi suy từ `promotions.csv`, năm lẻ | Kiểm soát leakage từ gốc: không cần giá trị nào của tập test |
| 4. Validation theo thời gian | 3 fold (validate 2022, 2021, 07/2021–06/2022), baseline seasonal naive, MAE hình dạng | Đo đúng tình huống dự báo năm sau; tách lỗi hình dạng khỏi lỗi mức |
| 5. Mô hình gốc | Ridge + Fourier, LightGBM ưu tiên 2014–2018, 4 LightGBM chuyên biệt theo quý, Prophet | Ba họ mô hình khác bản chất để ensemble có giá trị |
| 6. Ensemble | 0.3 × Ridge + 0.7 × LightGBM theo quý (Prophet nhận trọng số 0) | Trọng số chọn trên CV; giảm MAE hình dạng 3.5% so với mô hình đơn tốt nhất |
| 7. Calibration mức | Hệ số c = thực tế 2022 ÷ dự báo 2022 (1.080 cho Revenue) | Sửa độ lệch mức 4–7% mà không dùng leaderboard |
| 8. SHAP | Mùa vụ năm 58.7%, giai đoạn & xu hướng 25.4%, đầu/cuối tháng 6.3%, khuyến mãi 2.6% | Giải thích dự báo bằng ngôn ngữ kinh doanh |
| 9. Submission | `forecasting/submission.csv`, 548 dòng | Đúng định dạng, chạy lại ra đúng file (`random_state = 42`) |

**Kết quả:**

- Trên năm 2022, ensemble + calibration đạt **MAE 544K VND/ngày, R² 0.807** cho Revenue, giảm **37%** sai số so với seasonal naive (MAE 864K, R² 0.445).
- Dự báo Revenue **2023: 1.18 tỷ** (2022: 1.17 tỷ), **6 tháng đầu 2024: 0.71 tỷ** (cùng kỳ 2022: 0.69 tỷ): doanh thu đi ngang, chưa hồi phục.
- Tháng 4–6 chiếm 37.9% doanh thu dự báo 2023; Q3 2023 dự báo bán lỗ (COGS/Revenue 1.05), trùng thời điểm chiến dịch giảm 50% chỉ chạy năm lẻ.
- Chưa có `sample_submission.csv` để đối chiếu thứ tự dòng; file nộp đang xếp theo thứ tự ngày.

