# Vin Datathon 2026 — Dashboard, Customer Analytics & Forecasting

Phân tích hoạt động kinh doanh của một doanh nghiệp thương mại điện tử thời trang tại Việt Nam, giai đoạn 2012–2022. Dự án gồm bốn phần:

- **EDA & chất lượng dữ liệu**
- **Dashboard Power BI** (5 trang, đi từ tổng quan đến chi tiết)
- **Phân nhóm khách hàng** (rule-based + K-Means)
- **Dự báo doanh thu** theo ngày cho giai đoạn 01/01/2023–01/07/2024 (ensemble Ridge + LightGBM, R² 0.807 trên năm 2022)

## Bài toán kinh doanh

Doanh nghiệp tăng trưởng đến khoảng năm 2016 rồi suy giảm suốt sáu năm, dù lượng truy cập website vẫn tăng. Ban lãnh đạo cần biết vì sao, nên tập trung vào ai, sắp tới sẽ ra sao và nên sửa gì trước. Đề thi chấm theo bốn cấp độ, từ "điều gì đã xảy ra" đến "nên làm gì", từ đó dự án đặt ra năm câu hỏi kinh doanh:

| # | Câu hỏi kinh doanh | Cụ thể | Phần trả lời |
|---:|---|---|---|
| 1 | **Điều gì đã xảy ra?** | Doanh thu, số đơn, biên lợi nhuận, khách hàng và lượng truy cập biến động thế nào từ 2012, và suy giảm bắt đầu từ đâu? | [1. EDA](#1-eda--chất-lượng-dữ-liệu), [2. Dashboard](#2-dashboard) (trang Executive Overview) |
| 2 | **Vì sao xảy ra?** | Suy giảm do thiếu traffic, chuyển đổi kém, khách không quay lại, khuyến mãi, tồn kho, hay giao hàng và trả hàng? | [2. Dashboard](#2-dashboard) (trang Customer, Sales & Promotion, Inventory, Logistics & Returns) |
| 3 | **Nên tập trung vào ai?** | Nhóm khách nào mang về doanh thu, nhóm nào đã im lặng, nhóm nào chưa từng mua? | [3. Phân nhóm khách hàng](#3-phân-nhóm-khách-hàng) |
| 4 | **Sắp tới sẽ ra sao?** | Doanh thu từng ngày từ 01/2023 đến 07/2024 là bao nhiêu, để lên kế hoạch tồn kho, khuyến mãi và giao hàng? | [4. Dự báo doanh thu](#4-dự-báo-doanh-thu) |
| 5 | **Nên làm gì?** | Hành động nào làm trước, cho nhóm khách nào, và KPI nào cho biết hành động đó có hiệu quả? | Recommendation ở [mục 3](#recommendation) và [mục 4](#recommendation-1), [`dashboard_analysis_recommendations.md`](reports/markdown/dashboard_analysis_recommendations.md) |

**Câu trả lời ngắn (từ dữ liệu):**

1. **Điều gì đã xảy ra:** doanh thu thuần giảm trung bình 3,86% mỗi năm (CAGR 2013–2022); cùng giai đoạn, sessions tăng 63% nhưng tỷ lệ chuyển đổi (đơn có doanh thu ÷ sessions) giảm từ 1,01% xuống 0,29%.
2. **Vì sao:** suy giảm đến từ chuyển đổi và giữ chân khách, không phải từ traffic; 28% khách đăng ký (34.091) chưa từng hoàn tất đơn nào.
3. **Tập trung vào ai:** Champions và Trung thành là 35,8% khách đã mua nhưng mang về 78,5% doanh thu; nhóm Trung thành đã gần 2 năm chưa quay lại.
4. **Sắp tới:** doanh thu dự báo đi ngang: 1,18 tỷ năm 2023 so với 1,17 tỷ năm 2022; tháng 4–6 chiếm 37,9%; Q3 2023 có nguy cơ bán lỗ.
5. **Nên làm gì:** ưu tiên giữ Champions và kéo lại nhóm Trung thành, kích hoạt đơn đầu cho khách chưa mua, chuẩn bị hàng cho mùa cao điểm và xem lại chiến dịch giảm 50% năm lẻ; mỗi hành động có KPI và nhóm đối chứng.

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
│   ├── prepare_powerbi_data.py          # Dựng star schema 15 bảng (dim/fact/agg) cho Power BI
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
│       ├── forecasting/
│       └── powerbi/                     # 15 CSV import vào Power BI
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

# 4. Dữ liệu cho dashboard Power BI (chạy sau phần 2 để có nhãn phân khúc)
python dashboard/prepare_powerbi_data.py

# 5. Dựng báo cáo PDF (cần Microsoft Edge hoặc Google Chrome)
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

**Biến đổi dữ liệu** — [`dashboard/prepare_powerbi_data.py`](dashboard/prepare_powerbi_data.py): Python + pandas đọc `data/raw/`, dựng **star schema** (5 dim, 7 fact, 3 bảng tổng hợp) và ghi ra `data/processed/powerbi/`. Power BI chỉ import rồi tạo quan hệ và measure DAX.

1. Nạp 13 file CSV gốc, chỉ đọc. Một số file lưu ngày dạng `dd/mm/yyyy`, số còn lại `yyyy-mm-dd`; script tự nhận định dạng theo từng cột.
2. Dựng bảng dim: bảng lịch `dim_date`; sản phẩm kèm margin, điểm đánh giá trung bình, tỷ lệ trả; khách hàng kèm vùng, điểm và nhãn RFM, tháng cohort, phân khúc K-Means từ phần 3 (nếu đã chạy).
3. Dựng bảng fact, mỗi bảng đúng một grain: đơn (`fact_orders`: thanh toán, phí ship, tiền hoàn, đơn mới/mua lại), dòng hàng (`fact_orders_enriched`: doanh thu, giảm giá, giá vốn, lãi gộp), trả hàng, vận chuyển (số ngày xử lý, số ngày giao, nhóm thời gian giao), doanh thu ngày (MA7/MA30, YoY), tồn kho tháng (giá trị tồn, nhãn tình trạng), web traffic ngày (trang/phiên, tỷ lệ chuyển đổi).
4. RFM, cohort, khách mới/mua lại và tỷ lệ chuyển đổi chỉ tính đơn `paid`/`shipped`/`delivered`/`returned`, giống phần 3. Bảng fact vẫn giữ mọi trạng thái (kèm cờ `is_revenue_order`) để tính tỷ lệ hủy.
5. Tổng hợp sẵn các góc nhìn khó làm bằng DAX: KPI theo tháng kèm MoM/YoY, ma trận cohort retention (tháng 0–24), điểm đánh giá theo tháng × danh mục.
6. Data modeling trong Power BI: đánh dấu `dim_date` là Date Table; quan hệ 1-nhiều một chiều từ dim sang fact; mọi measure DAX nằm trong bảng `_Measures`.

**Đầu ra (15 file CSV):**

| Loại | File | 1 dòng = | Số dòng |
|---|---|---|---:|
| Dim | `dim_date.csv` | 1 ngày | 4.018 |
| Dim | `dim_products.csv` | 1 SKU | 2.412 |
| Dim | `dim_customers_rfm.csv` | 1 khách (kèm vùng, RFM, phân khúc) | 121.930 |
| Dim | `dim_geography.csv` | 1 mã bưu chính | 39.948 |
| Dim | `dim_promotions.csv` | 1 chương trình | 50 |
| Fact | `fact_orders.csv` | 1 đơn (mọi trạng thái) | 646.945 |
| Fact | `fact_orders_enriched.csv` | 1 dòng hàng (mọi trạng thái) | 714.669 |
| Fact | `fact_returns_enriched.csv` | 1 lần trả 1 sản phẩm | 39.939 |
| Fact | `fact_shipments_enriched.csv` | 1 lần giao | 566.067 |
| Fact | `fact_sales_daily.csv` | 1 ngày | 3.833 |
| Fact | `fact_inventory.csv` | 1 sản phẩm / 1 tháng | 60.247 |
| Fact | `fact_web_traffic.csv` | 1 ngày | 3.652 |
| Agg | `agg_monthly_summary.csv` | 1 tháng | 126 |
| Agg | `agg_cohort_retention.csv` | 1 cohort × tháng thứ N | 2.423 |
| Agg | `agg_reviews_summary.csv` | 1 tháng × danh mục | 504 |

- `payment_value` chỉ nằm ở `fact_orders` (cấp đơn), để không bị cộng trùng khi đơn có nhiều dòng hàng.
- Hai định nghĩa doanh thu tách riêng: `line_revenue` khớp đúng `sales.Revenue` (trước giảm giá, mọi trạng thái đơn); `line_net_revenue`/`payment_value` là sau giảm giá.

Sơ đồ quan hệ (star schema), các quyết định mô hình, định nghĩa từng KPI và công thức: [`dashboard/README.md`](dashboard/README.md).

- **Power BI:** `dashboard/Ecommerce_Dashboard.pbix` — file nặng (~110 MB) nên chỉ lưu local, không đưa lên GitHub.
- **Phân tích & khuyến nghị:** [`reports/markdown/dashboard_analysis_recommendations.md`](reports/markdown/dashboard_analysis_recommendations.md)

## 3. Phân nhóm khách hàng

**Câu hỏi:** khách nào mang về doanh thu, khách nào đã rời đi, khách nào chưa từng mua, và nên làm gì với từng nhóm? Chi tiết: [`customer_segmentation/README.md`](customer_segmentation/README.md). Báo cáo: `reports/03_Customer_Segmentation_report.pdf`.

**Phương pháp:** hai lớp phân nhóm cho **toàn bộ** 121.930 khách đã đăng ký.

- **Rule-based** cho khách chưa có đơn phát sinh doanh thu: RB1 chưa đặt đơn nào; RB2 đặt đơn nhưng mọi đơn đều bị hủy hoặc bỏ dở.
- **K-Means trên RFM** (log1p → scale → PCA) cho khách có đơn `paid`/`shipped`/`delivered`/`returned`. Chọn **k = 5**: đạt điều kiện business (cụm nhỏ nhất 10,2%, 5 cụm là 5 loại hành vi khác nhau), ổn định (ARI 0,956), thống kê đồng hạng với k = 3 nhưng tách được khách mới khỏi khách đã rời bỏ.
- Nhân khẩu học không tham gia phân cụm; chỉ dùng để mô tả chân dung từng nhóm.

### Output: mọi khách có đúng một nhãn

```text
121.930 khách đã đăng ký
├── Rule-based (34.091 khách, 28,0%): chưa tạo ra doanh thu
│   ├── RB1 Chưa giao dịch .................. 31.684 (26,0%)
│   └── RB2 Đặt đơn nhưng chưa chuyển đổi ...  2.407 ( 2,0%)
└── K-Means k = 5 (87.839 khách đã mua, 72,0%)
    ├── C0 Champions ........................ 12.384 · 43,6% doanh thu
    ├── C2 Trung thành ...................... 19.103 · 34,9% doanh thu
    ├── C4 Ngủ đông ......................... 24.995 · 13,1% doanh thu
    ├── C3 Khách mới / tiềm năng ............  8.945 ·  5,7% doanh thu
    └── C1 Đã rời bỏ ........................ 22.412 ·  2,6% doanh thu
```

| Nhóm | Chân dung (Recency, Frequency là median) |
|---|---|
| C0 Champions | Mua gần nhất (~5 tháng), 17 đơn, chi cao nhất. Gần như chỉ mua Streetwear (96%), trả bằng thẻ tín dụng; rất ít đến từ email (lift 0,49) |
| C2 Trung thành | 9 đơn, chi khá, nhưng gần 2 năm chưa quay lại. Chân dung giống Champions: đang trôi dần thành Ngủ đông |
| C4 Ngủ đông | 3 đơn, AOV trên mặt bằng, ~4,5 năm chưa mua. Đặt trực tiếp và qua email (lift 1,53 và 1,35) |
| C3 Khách mới / tiềm năng | Mua gần đây (~7 tháng) nhưng mới 4 đơn. Liên lạc được qua email và kênh trực tiếp |
| C1 Đã rời bỏ | 1 đơn giá trị thấp, ~6,5 năm trước, tỷ lệ trả hàng cao nhất (7,8%). Mua GenZ và Outdoor nhiều bất thường (lift 2,93 và 2,31) |
| RB1 Chưa giao dịch | Đăng ký nhưng chưa đặt đơn nào: 1/4 số khách đăng ký |
| RB2 Đặt đơn nhưng chưa chuyển đổi | Mọi đơn bị hủy hoặc bỏ dở; 152 khách thất bại từ 2 đơn trở lên |

**Insight chính:**

1. **Doanh thu phụ thuộc vào một nhóm nhỏ:** Champions và Trung thành là 35,8% khách đã mua nhưng mang về **78,5% doanh thu**.
2. **Rủi ro lớn nhất:** nhóm Trung thành (34,9% doanh thu) đã gần 2 năm chưa mua.
3. **Cơ hội lớn nhất ở đầu phễu:** **28% khách đăng ký** (34.091) chưa từng tạo ra doanh thu.
4. **Nhắm mục tiêu theo hành vi, không theo nhân khẩu học:** danh mục, thanh toán, thiết bị phân biệt cụm (Cramér's V 0,14–0,25); tuổi, giới tính, kênh thu hút thì không (V < 0,01).

### Recommendation

| Ưu tiên | Nhóm | Hành động | Kênh | KPI theo dõi |
|---:|---|---|---|---|
| 1 | C0 Champions | Hạng VIP, quyền mua sớm Streetwear mới, upsell premium; **không** giảm giá sâu | App/mobile, ưu đãi gắn thẻ tín dụng; chủ động thu email | Giữ chân 90 ngày, AOV |
| 1 | C2 Trung thành | Nhắc mua theo mốc 6/12 tháng, điểm thưởng có hạn dùng, cross-sell | SEO/landing page Streetwear, email | % mua lại trong 12 tháng |
| 2 | RB1 Chưa giao dịch | Voucher đơn đầu có hạn, giới thiệu sản phẩm bán chạy | Email/push | Tỷ lệ chuyển đổi đơn đầu |
| 2 | RB2 Chưa chuyển đổi | Tìm lý do hủy (thanh toán, giá, giao hàng), retarget đúng sản phẩm đã đặt | Email/retargeting | Tỷ lệ chuyển đổi đơn đầu |
| 3 | C3 Khách mới | Voucher đơn kế tiếp trong 30 ngày, email onboarding | Email, kênh trực tiếp | Mua lần tiếp trong 90 ngày |
| 4 | C4 Ngủ đông | Email theo mùa, ưu đãi nhỏ, chạy thử với nhóm đối chứng trước | Email | Reactivation rate |
| 5 | C1 Đã rời bỏ | Chỉ email chi phí gần 0; rà soát trải nghiệm sản phẩm GenZ/Outdoor | Email | Chi phí/đơn kéo về |

Mọi hành động đo bằng nhóm đối chứng (giữ 10% khách mỗi nhóm không nhận ưu đãi) để biết doanh thu tăng thêm thật sự.

## 4. Dự báo doanh thu

**Câu hỏi:** doanh thu và giá vốn từng ngày từ 01/01/2023 đến 01/07/2024 sẽ ra sao, để lên kế hoạch tồn kho, khuyến mãi và giao hàng? Chi tiết từng bước và ý nghĩa: [`forecasting/README.md`](forecasting/README.md). Báo cáo: `reports/04_Forecasting_report.pdf`.

**Phương pháp:** 9 bước, từ `sales.csv` (3.833 ngày) đến file nộp 548 dòng.

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

### Output

| | Thực tế 2022 | Dự báo 2023 | Thực tế 6 tháng đầu 2022 | Dự báo 6 tháng đầu 2024 |
|---|---:|---:|---:|---:|
| Revenue | 1,17 tỷ | 1,18 tỷ | 0,69 tỷ | 0,71 tỷ |
| COGS | 1,02 tỷ | 1,08 tỷ | 0,59 tỷ | 0,61 tỷ |

- **File nộp:** `forecasting/submission.csv`, 548 dòng `Date,Revenue,COGS`.
- **Độ chính xác:** trên năm 2022, ensemble + calibration đạt **MAE 544K VND/ngày, R² 0,807** cho Revenue, giảm **37%** sai số so với seasonal naive (MAE 864K, R² 0,445). Sai số tương đương 17% doanh thu trung bình ngày năm 2022: tin cậy cho kế hoạch theo tháng/quý, theo ngày chỉ nên coi là định hướng.

**Insight chính:**

1. **Doanh thu đi ngang, chưa hồi phục:** 2023 +1,2% so với 2022, 6 tháng đầu 2024 +2,9% so với cùng kỳ 2022; không quay lại mức 2014–2018.
2. **Tháng 4–6 chiếm 37,9% doanh thu 2023.**
3. **Q3 2023 dự báo bán lỗ:** COGS/Revenue 1,05 (Q3 2022: 0,89), trùng thời điểm chiến dịch Urban Blowout giảm 50% chỉ chạy năm lẻ.
4. **Cuối tháng là cao điểm ngắn hạn:** 3 ngày cuối tháng dự báo 5,55 triệu/ngày, gần gấp đôi giữa tháng (2,92 triệu).
5. **Khuyến mãi không phải động lực tăng trưởng:** chỉ giải thích 2,6% dự báo (SHAP), so với 58,7% của mùa vụ năm.

### Recommendation

| Ưu tiên | Hành động | Dựa trên | KPI theo dõi |
|---:|---|---|---|
| 1 | Chuẩn bị tồn kho, nhân sự, năng lực giao hàng cho tháng 4–6 từ tháng 3 | Tháng 4–6 chiếm 37,9% doanh thu 2023 | Tỷ lệ hết hàng, thời gian giao hàng mùa cao điểm |
| 1 | Xem lại mức giảm 50% của Urban Blowout trước tháng 7/2023 | Q3 2023 dự báo COGS vượt Revenue | Gross margin Q3 |
| 2 | Đặt chiến dịch và lịch nhập hàng theo mốc cuối tháng | Cuối tháng doanh thu gần gấp đôi giữa tháng | Doanh thu 3 ngày cuối tháng, tồn kho đầu tháng |
| 2 | Không dựa vào khuyến mãi để tăng doanh thu; tập trung chuyển đổi và giữ chân (mục 3) | Khuyến mãi chỉ 2,6% SHAP; doanh thu đi ngang | Conversion rate, tỷ lệ mua lại |
| 3 | So dự báo với thực tế mỗi tháng, cập nhật hệ số calibration khi lệch kéo dài | Calibration giả định mức lệch giống năm 2022 | Sai số tháng (MAE, % lệch tổng) |

**Còn lại trước khi nộp:** chưa có `sample_submission.csv` để đối chiếu thứ tự dòng; file nộp đang xếp theo thứ tự ngày.
