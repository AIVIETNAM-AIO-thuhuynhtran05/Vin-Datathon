# Customer Segmentation

Phân nhóm khách hàng theo hành vi mua (RFM) bằng K-Means, mô tả chân dung từng nhóm và đề xuất hành động để tăng doanh thu.

> README này mô tả **flow** của phần phân cụm. Các mục đánh dấu ✍️ là chỗ cần điền khi có kết quả cụ thể.

## Flow tổng quan

```text
                                   ┌─ chưa có đơn doanh thu ► Rule-based (RB1/RB2) ───────────────────────────┐
data/raw ─► 1. Aggregation ─► 2. QC ┤                                                                          ├─► 6. Profile ─► 7. Recommendation
           (đơn → khách)            └─ đã mua ─► 3. Feature engineering ─► 4. K-Means ─► 5. Kết quả cụm ──────┘   (toàn bộ khách)
                                                (RFM, log, scale, PCA)      (chọn k)
```

| Bước | Script | Việc làm | Trạng thái |
|---|---|---|---|
| 1–2 | `01_build_customer_dataset.py` | Aggregation, quality check, tính RFM, gán nhóm rule-based | ✅ |
| 3a | `02_transform_features.py` | Feature engineering: so sánh phép biến đổi, scale, đánh giá biến ứng viên → [`reports/markdown/customer_segmentation_features.md`](../reports/markdown/customer_segmentation_features.md) | ✅ |
| 3b | `03_pca_analysis.py` | PCA + giải thích → [`reports/markdown/customer_segmentation_pca.md`](../reports/markdown/customer_segmentation_pca.md) | ✅ |
| 4 | `04_select_k.py` | Quét k = 2–8, đánh giá thống kê + ổn định + business → [`reports/markdown/customer_segmentation_k_selection.md`](../reports/markdown/customer_segmentation_k_selection.md) | ✅ |
| 5 | `05_kmeans_segmentation.py` | K-Means với k = 5 → `customer_segments.csv` (`customer_id`, `cluster`) | ✅ |
| 6–8 | `06_cluster_profiling.py` | Bức tranh tổng thể, profile, gợi ý hành động → [`reports/markdown/customer_segment_profiles.md`](../reports/markdown/customer_segment_profiles.md) | ✅ (chạy lại sau khi chốt K-Means) |

`config.py` chứa toàn bộ đường dẫn, định nghĩa trạng thái đơn, luật rule-based và phép biến đổi biến. `behavior_features.py` tạo các biến hành vi dùng chung cho bước 02 và 06. `segment_naming.py` chứa luật đặt tên cụm gợi ý và hành động theo nhóm. `plot_style.py` chứa màu và style biểu đồ.

---

## 0. Mục đích

- **Câu hỏi kinh doanh:** khách hàng của doanh nghiệp chia thành những nhóm hành vi nào, mỗi nhóm đóng góp bao nhiêu doanh thu, và nên tác động vào nhóm nào, bằng cách nào để **tăng doanh thu**?
- **Đầu ra mong muốn:**
  1. Mỗi khách hàng có nhãn cụm.
  2. Mỗi cụm có tên dễ hiểu, quy mô, mức đóng góp doanh thu và chân dung (độ tuổi, giới tính, vùng, kênh…).
  3. Mỗi cụm có hành động cụ thể và KPI để đo hiệu quả.
- **Phạm vi:** **toàn bộ 121.930 khách đã đăng ký** (04/07/2012 – 31/12/2022):
  - Khách đã có đơn phát sinh doanh thu (`paid`/`shipped`/`delivered`/`returned`) → phân cụm K-Means.
  - Khách chưa có đơn phát sinh doanh thu → gán nhóm rule-based.

## 1. Dữ liệu đầu vào & aggregation

### Bảng và cột sử dụng

| Bảng | Cột | Dùng để |
|---|---|---|
| `orders` | `order_id`, `customer_id`, `order_date`, `order_status` | Lọc đơn phát sinh doanh thu, tính Recency/Frequency |
| `payments` | `order_id`, `payment_value` | Tiền khách trả (sau giảm giá) → Monetary |
| `returns` | `order_id`, `refund_amount` | Trừ tiền hoàn khỏi Monetary |
| `customers` | `customer_id`, `gender`, `age_group`, `acquisition_channel`, `zip`, `signup_date` | Biến mô tả (profile), **không** đưa vào K-Means |
| `geography` | `zip`, `region` | Vùng của khách |
| `order_items`, `products`, `reviews` *(dự kiến)* | | Biến hành vi bổ sung cho profile: danh mục ưa thích, tỷ lệ dùng khuyến mãi, điểm đánh giá |

### Các bước gộp (grain: đơn hàng → khách hàng)

1. **Business rule — đơn tính doanh thu:** `order_status ∈ {paid, shipped, delivered, returned}`, tức đơn đã thanh toán trở đi. Loại `created` (chưa thanh toán) và `cancelled` (đã hủy). Đơn `returned` vẫn tính, nhưng trừ tiền hoàn ở bước 3. Định nghĩa nằm ở `config.REVENUE_STATUSES`.
2. Cộng `refund_amount` theo `order_id`, rồi nối 1–1 với `payments`.
3. Giá trị ròng của đơn = `payment_value − tổng tiền hoàn`, **chặn dưới ở 0**.
4. Gộp theo `customer_id`:
   - `recency_days` = ngày tham chiếu (**2023-01-01** = ngày đặt cuối cùng + 1) − ngày đặt gần nhất.
   - `frequency` = số đơn phát sinh doanh thu khác nhau.
   - `monetary` = Σ giá trị ròng của các đơn.
5. Nối thông tin nhân khẩu học và vùng (qua `zip` → `geography.region`). Giá trị thiếu gán `Unknown`.

**Kết quả:** `customer_analysis_base.csv` có 121.930 khách, kèm các cột `segment_method` (`kmeans`/`rule_based`), `rule_segment`, `failed_order_count`, `failed_reason` và `order_count_all`.

### Rule-based segmentation (khách không có đơn phát sinh doanh thu)

Khách không có đơn doanh thu thì không có RFM có ý nghĩa: F = M = 0, còn R không xác định. Nếu đưa vào K-Means, họ sẽ tạo thành một cụm "toàn số 0" và làm lệch các cụm còn lại. Vì vậy họ được gán nhãn bằng luật **trước khi** phân cụm (`config.RULE_SEGMENTS`).

**Tiêu chí:** rule-based dành cho khách **không có hành vi tạo doanh thu để phân cụm**. Tiêu chí này rộng hơn "chưa có giao dịch", để khách đã đặt đơn nhưng không chuyển đổi vẫn có nhóm và có hành động riêng.

| Mã | Nhóm | Điều kiện | Số khách | Mục tiêu |
|---|---|---|---:|---|
| — | → K-Means | Có ≥ 1 đơn `paid`/`shipped`/`delivered`/`returned` | 87.839 | Xem bước 4–6 |
| RB2 | Đặt đơn nhưng chưa chuyển đổi | Có ≥ 1 đơn, tất cả đều `cancelled`/`created` | 2.407 | Gỡ rào cản để chuyển đổi đơn đầu tiên |
| RB1 | Chưa giao dịch | Đăng ký nhưng chưa đặt đơn nào | 31.684 | Kích hoạt đơn đầu tiên |

**Thuộc tính của RB2** (không tách thành nhóm riêng vì phần lẻ quá nhỏ):

- `failed_order_count`: 1 đơn có 2.255 khách (93,7%); 2 đơn có 140 khách; 3 đơn có 12 khách. Khách có ≥ 2 đơn thất bại thể hiện ý định mua rõ hơn, gặp rào cản lặp lại, nên được ưu tiên.
- `failed_reason`: `cancelled` 2.123, `abandoned` (đơn `created` bỏ dở) 258, cả hai 26. Đơn `created` trải đều 2012–2022, tức là đơn bỏ dở, không phải đơn đang chờ thanh toán.

Kết quả cuối: `customer_segments_all.csv`, gồm `customer_id`, `segment_method`, `segment` (RB1, RB2 / C0…Ck), `segment_name`. Mọi khách hàng đều có đúng một nhãn.

## 2. Quality check

**Kiểm tra trong `01_build_customer_dataset.py`** — script dừng ngay nếu có lỗi:

- Khóa chính không trùng, không rỗng: `customers.customer_id`, `orders.order_id`, `payments.order_id`, `geography.zip`.
- `order_date` và `payment_value` chuyển kiểu hợp lệ.
- Mọi `orders.customer_id` có trong `customers`; `payments` khớp 1–1 với `orders`; mọi `returns.order_id` có trong `orders`.

**Vấn đề dữ liệu ảnh hưởng đến phân cụm** (từ [báo cáo EDA](../reports/markdown/data_quality_and_eda.md)) và cách xử lý:

| Vấn đề | Quy mô | Xử lý |
|---|---|---|
| Tổng tiền hoàn > tiền thanh toán (hoàn theo giá **trước** giảm giá) | 3.640 đơn | Giữ đơn, giá trị ròng chặn ở 0; danh sách lưu trong `refund_reconciliation_issues.csv` |
| Đơn đặt **trước** ngày đăng ký của khách | 73,8% số đơn | **Không** dùng `signup_date` để tính tenure/cohort |
| Đơn `returned` không có dòng trong `returns` | 80 đơn | Coi tiền hoàn = 0 |
| Monetary / Frequency lệch phải mạnh, nhiều outlier IQR | | Không xóa outlier; giảm ảnh hưởng bằng `log1p` |

## 3. Feature engineering

### 3.1 Biến dùng cho K-Means: RFM

| Biến | Ý nghĩa | Chiều tốt |
|---|---|---|
| `recency_days` | Mới mua gần đây hay đã lâu | Thấp là tốt |
| `frequency` | Mức độ gắn bó | Cao là tốt |
| `monetary` | Giá trị mang lại | Cao là tốt |

Nhân khẩu học (tuổi, giới tính, vùng, kênh) **không** đưa vào K-Means. Lý do: cụm cần phản ánh **hành vi** (thứ có thể tác động bằng marketing); nhân khẩu học chỉ dùng để mô tả cụm sau khi đã phân xong.

### 3.2 Biến đổi — `02_transform_features.py`

Chi tiết và số liệu: [`reports/markdown/customer_segmentation_features.md`](../reports/markdown/customer_segmentation_features.md).

1. **Biến đổi phân phối** (`config.FEATURE_TRANSFORMS`): giảm độ lệch để vài khách cực lớn không kéo tâm cụm. Mỗi biến được thử 4 phép (không biến đổi, `sqrt`, `log1p`, Yeo-Johnson) và so sánh skew:

   | Biến | Skew gốc | `log1p` (đang dùng) | Gợi ý |
   |---|---:|---:|---|
   | Recency | +0,62 | −1,22 (lệch hơn gốc) | `sqrt` (+0,01) |
   | Frequency | +2,61 | +0,53 | Yeo-Johnson (+0,13) |
   | Monetary | +2,55 | −1,07 | Yeo-Johnson (−0,02) |

   ✍️ **Cần quyết định:** giữ `log1p` cho cả 3 biến, hay đổi theo gợi ý. Đổi thì phải chạy lại từ bước 02.
2. **`StandardScaler`**: đưa 3 biến về cùng thang (mean 0, std 1). K-Means dùng khoảng cách Euclid, nên nếu không scale thì Monetary sẽ lấn át hai biến còn lại.
3. **PCA** — chi tiết trong [`reports/markdown/customer_segmentation_pca.md`](../reports/markdown/customer_segmentation_pca.md):
   - **Vì sao:** Frequency và Monetary tương quan **r = 0,83**, tức K-Means sẽ tính khía cạnh "giá trị mua" gần như hai lần. PCA xoay sang các trục không tương quan, đồng thời cho phép vẽ cụm trên mặt phẳng 2D.
   - **Có phù hợp không:** Bartlett p ≈ 0 (các biến có tương quan) và KMO = 0,65 (chấp nhận được).
   - **Kết quả:** PC1 giải thích 77,1% phương sai (trục "giá trị & gắn bó": +F, +M, −R); PC2 giải thích 17,4% (trục "độ mới", Recency nổi trội). **Giữ 2 PC = 94,6% phương sai.**
   - **Lưu ý:** nếu giữ đủ 3 PC thì K-Means cho kết quả y hệt dữ liệu đã scale. Lợi ích chỉ đến từ việc bỏ PC3.

### 3.3 Biến hành vi ứng viên

Các biến hành vi được tạo trong `behavior_features.py` (dùng chung với bước profiling) và đánh giá bằng tương quan Spearman với RFM. Nếu |ρ| ≥ 0,7 thì biến đó trùng thông tin với RFM.

| Biến | Định nghĩa | Tương quan mạnh nhất với RFM |
|---|---|---|
| `aov` | Monetary / Frequency | Monetary (ρ = 0,56) |
| `tenure_days` | Số ngày từ đơn doanh thu đầu tiên | Frequency (0,66) |
| `return_rate` | Tỷ lệ đơn bị trả | Frequency (0,40) |
| `cancel_rate` | Tỷ lệ đơn hủy | Frequency (0,39) |
| `items_per_order` | Số sản phẩm / đơn | Monetary (0,20) |
| `promo_share` | Tỷ lệ dòng có khuyến mãi | Frequency (0,12) |
| `avg_rating` | Điểm đánh giá TB (55% khách có) | Frequency (−0,07) |

Không biến nào trùng thông tin với RFM. Hiện tất cả chỉ dùng để **mô tả cụm**. Biến phân loại (danh mục, thiết bị, thanh toán, nguồn đơn) và nhân khẩu học không đưa vào K-Means vì không đo được bằng khoảng cách Euclid.

✍️ Ghi lại ở đây nếu quyết định thêm biến nào vào K-Means.

## 4. Chọn số cụm k — `04_select_k.py`

Bước này **chỉ đánh giá, không ghi nhãn**. Quét k = 2–8 trên `customer_pca_scores.csv`, mỗi k chạy 5 `random_state`. Chi tiết: [`reports/markdown/customer_segmentation_k_selection.md`](../reports/markdown/customer_segmentation_k_selection.md).

**Tiêu chí:** k chọn theo 3 lớp, vì silhouette một mình luôn ưu tiên k nhỏ.

1. **Business:**
   - k ≥ 3 (k = 2 quá thô để có chiến lược khác nhau).
   - Cụm nhỏ nhất ≥ 5% khách.
   - Mỗi cụm là một loại hành vi khác nhau (không có hai cụm phải xử lý giống nhau).
2. **Ổn định:** ARI giữa các lần chạy ≥ 0,9.
3. **Thống kê:** hạng trung bình của Silhouette (↑), Calinski-Harabasz (↑), Davies-Bouldin (↓); tham khảo elbow.

**Kết quả quét** (87.839 khách, đầu vào PCA):

| k | Silhouette | Calinski-Harabasz | Davies-Bouldin | ARI | Cụm nhỏ nhất | Nhóm hành động | Đạt điều kiện business |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 2 | 0,494 | 117.209 | 0,749 | 0,995 | 44,2% | 2/2 | — (k < 3) |
| 3 | 0,401 | 101.084 | 0,882 | 0,988 | 24,9% | 3/3 | ✅ |
| 4 | 0,346 | 88.475 | 0,990 | 0,944 | 15,4% | 4/4 | ✅ |
| 5 | 0,374 | 87.957 | 0,846 | 0,956 | 10,2% | 5/5 | ✅ |
| 6 | 0,372 | 87.592 | 0,867 | 0,969 | 4,2% | 5/6 | — |
| 7 | 0,346 | 85.550 | 0,873 | 0,986 | 3,2% | 6/7 | — |
| 8 | 0,364 | 86.943 | 0,800 | 0,961 | 3,0% | 6/8 | — |

- **Elbow:** k = 4. **Xếp hạng thống kê:** k = 3 và k = 5 đồng hạng (3,3) trong các k đạt điều kiện.
- **Ứng viên:**
  - **k = 3**: tách rõ nhất, nhưng gộp chung khách mới mua gần đây với khách đã lâu không quay lại.
  - **k = 5**: thống kê tốt hơn k = 4 (silhouette 0,374 so với 0,346; DB 0,846 so với 0,990), đủ ổn định. Tách thêm 2 nhóm có hành động riêng: **Khách mới / tiềm năng** (10%, mua gần đây nhưng ít đơn) và **Đã rời bỏ** (25%, chỉ 2,6% doanh thu).

**k đã chọn: 5.** Lý do:

1. **Đạt cả 3 lớp điều kiện:** cụm nhỏ nhất 10,2% (≥ 5%), 5/5 cụm là 5 loại hành vi khác nhau, ARI 0,956 (≥ 0,9).
2. **Nhiều nhóm hành động nhất trong các k đạt điều kiện** (k = 3, 4, 5). Mỗi nhóm thêm là một chiến lược riêng triển khai được.
3. **Thống kê không kém k = 3:** đồng hạng 3,3; Davies-Bouldin 0,846 là tốt nhất trong các k đạt điều kiện; silhouette 0,374 cao hơn k = 4 (0,346).
4. **Vì sao không chọn k = 3:** cụm "Trung thành" của k = 3 có recency median 977 ngày, tức gộp chung khách mới mua gần đây nhưng ít đơn với khách đã lâu không quay lại. k = 5 tách được 2 nhóm cần hành động ngược nhau:
   - **Khách mới / tiềm năng** (R = 206 ngày, F = 4): cần nuôi dưỡng để mua lặp lại.
   - **Đã rời bỏ** (R = 2.391 ngày, 2,6% doanh thu) tách khỏi **Ngủ đông** (R = 1.650 ngày, 13,1% doanh thu): không tốn ngân sách win-back cho nhóm gần như đã mất.
5. **Vì sao không chọn k ≥ 6:** cụm nhỏ nhất dưới 5% (4,2%, 3,2%, 3,0%) và có hai cụm cùng loại hành vi (5/6, 6/7, 6/8), tức hai cụm phải xử lý giống nhau.

Báo cáo chọn k ([`customer_segmentation_k_selection.md`](../reports/markdown/customer_segmentation_k_selection.md)) sinh các lý do này trực tiếp từ số liệu.

## 5. K-Means — `05_kmeans_segmentation.py`

- Chạy `python customer_segmentation/05_kmeans_segmentation.py --k 5` trên 2 thành phần PCA (94,6% phương sai).
- **Đầu ra:** `customer_segments.csv` gồm `customer_id`, `cluster`; `customer_segments_all.csv` ghép thêm nhóm rule-based, nên **mọi khách đều có đúng một nhãn**.

## 6. Kết quả phân cụm

**Khách hàng được gom như sau** (121.930 khách đã đăng ký):

```text
121.930 khách đã đăng ký
├── Rule-based, gán trước khi chạy mô hình (34.091 khách, 28,0%)
│   ├── RB1 Chưa giao dịch .................. 31.684 (26,0%)
│   └── RB2 Đặt đơn nhưng chưa chuyển đổi ...  2.407 ( 2,0%)
└── K-Means k = 5 trên RFM (87.839 khách đã mua, 72,0%)
    ├── C0 Champions ........................ 12.384 · 43,6% doanh thu
    ├── C2 Trung thành ...................... 19.103 · 34,9% doanh thu
    ├── C4 Ngủ đông ......................... 24.995 · 13,1% doanh thu
    ├── C3 Khách mới / tiềm năng ............  8.945 ·  5,7% doanh thu
    └── C1 Đã rời bỏ ........................ 22.412 ·  2,6% doanh thu
```

| Cụm | Tên | Số khách | % khách đã mua | % doanh thu | Recency (median, ngày) | Frequency (median) | Monetary (median) | AOV |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| C0 | Champions | 12.384 | 14,1% | 43,6% | 149 | 17 | 421.487 | 23.888 |
| C2 | Trung thành | 19.103 | 21,7% | 34,9% | 659 | 9 | 219.127 | 23.764 |
| C4 | Ngủ đông | 24.995 | 28,5% | 13,1% | 1.650 | 3 | 64.500 | 22.627 |
| C3 | Khách mới / tiềm năng | 8.945 | 10,2% | 5,7% | 206 | 4 | 80.930 | 20.775 |
| C1 | Đã rời bỏ | 22.412 | 25,5% | 2,6% | 2.391 | 1 | 12.788 | 10.487 |

**Champions và Trung thành chiếm 35,8% khách đã mua nhưng mang về 78,5% doanh thu.**

**Cách đặt tên** (`segment_naming.py`): ma trận Recency × Giá trị (giá trị = trung bình phân vị F và M của cụm so với mặt bằng):

| | Giá trị cao | Giá trị thấp |
|---|---|---|
| **Mua gần đây** | Champions → Trung thành | Khách mới / tiềm năng → Cần nuôi dưỡng |
| **Lâu chưa mua** | Có nguy cơ rời bỏ | Ngủ đông → Đã rời bỏ |

Hai cụm rơi cùng ô thì cụm điểm cao hơn giữ tên, cụm sau lùi sang tên kế tiếp (theo mũi tên). Tên đã được đối chiếu với profile ở mục 7.

Biểu đồ: các cụm trên PC1–PC2, boxplot RFM theo cụm, heatmap z-score của từng chỉ số theo cụm.

## 7. Customer group profile

**Biến mô tả có trong dữ liệu:**

- Nhân khẩu học: giới tính, nhóm tuổi, vùng, kênh thu hút.
- Hành vi: thiết bị, phương thức thanh toán, nguồn đơn, danh mục ưa thích.

Dữ liệu **không có** nghề nghiệp hay thu nhập.

**Phương pháp:**

- Tỷ lệ % của mỗi nhóm giá trị trong từng cụm.
- **Lift** = % trong cụm / % toàn bộ khách: lift > 1,15 là đặc trưng nổi bật của cụm, < 0,85 là ít gặp trong cụm.
- **Chi-square + Cramér's V** để biết biến nào thực sự khác biệt giữa các cụm. Với ~87 nghìn khách thì p-value gần như luôn rất nhỏ, nên đánh giá bằng Cramér's V: < 0,1 nghĩa là biến gần như không phân biệt cụm, không nên dùng để nhắm mục tiêu.

**Biến nào phân biệt cụm (k = 5):**

- **Mức trung bình** (V = 0,11–0,25): danh mục ưa thích (0,245), phương thức thanh toán (0,185), thiết bị (0,143), nguồn đơn (0,128), vùng (0,113).
- **Không đáng kể** (V < 0,01): kênh thu hút, giới tính, nhóm tuổi.

Nghĩa là khi nhắm mục tiêu nên dựa vào **hành vi mua** (danh mục, thanh toán, thiết bị, kênh đặt đơn), không nên dựa vào nhân khẩu học.

**Chân dung từng cụm** (chi tiết và biểu đồ: [`customer_segment_profiles.md`](../reports/markdown/customer_segment_profiles.md)):

| Cụm | Hành vi | Chân dung nổi bật (lift) |
|---|---|---|
| C0 Champions | Mua gần nhất (149 ngày), nhiều đơn nhất (17), chi nhiều nhất | Streetwear 96% (1,21), thẻ tín dụng 96% (1,36), organic search 52% (1,35), vùng West (1,73), mobile (1,20); rất ít đến từ email (0,49) |
| C2 Trung thành | 9 đơn, chi cao, nhưng đã gần 2 năm chưa mua (659 ngày) | Streetwear 95% (1,19), thẻ tín dụng 88% (1,25), organic search (1,19); ít dùng COD (0,52) |
| C4 Ngủ đông | 3 đơn, AOV cao hơn mặt bằng, ~4,5 năm chưa mua | Đặt đơn trực tiếp (1,53) và qua email (1,35); Apple Pay (1,60), chuyển khoản (1,58), COD (1,35) |
| C3 Khách mới / tiềm năng | Mua gần đây (206 ngày), mới 4 đơn | Đặt trực tiếp (1,33) và qua email (1,17); Apple Pay (1,29), COD (1,17) |
| C1 Đã rời bỏ | 1 đơn, giá trị thấp nhất, ~6,5 năm chưa mua | GenZ (2,93) và Outdoor (2,31) cao bất thường; tablet (2,17), PayPal (2,08), referral (1,76) |

## 8. Recommendation để tăng doanh thu

Hành động cho từng nhóm dựa trên profile ở mục 7. **Thứ tự ưu tiên** theo doanh thu đang có hoặc có thể kéo về so với chi phí:

| Ưu tiên | Nhóm | Mục tiêu | Hành động | Kênh tiếp cận (theo profile) | KPI |
|---:|---|---|---|---|---|
| 1 | C0 Champions (43,6% doanh thu) | Giữ chân, tăng giá trị | Hạng VIP, quyền mua sớm bộ sưu tập Streetwear mới, upsell sản phẩm premium; **không** giảm giá sâu | App/mobile và ưu đãi gắn thẻ tín dụng; chủ động thu email vì nhóm này hiện ít đến từ email (lift 0,49) | Tỷ lệ giữ chân 90 ngày, AOV |
| 1 | C2 Trung thành (34,9% doanh thu) | Kéo quay lại trước khi trôi thành Ngủ đông | Nhắc mua theo mốc 6/12 tháng từ đơn cuối, điểm thưởng có hạn dùng, cross-sell Streetwear | Organic search (SEO/landing page Streetwear), email nhắc mua | % khách mua lại trong 12 tháng, Frequency |
| 2 | RB1 Chưa giao dịch (26,0% khách) | Kích hoạt đơn đầu tiên | Voucher đơn đầu có hạn, email giới thiệu sản phẩm bán chạy | Email/push theo kênh thu hút của khách | Tỷ lệ chuyển đổi đơn đầu |
| 2 | RB2 Đặt đơn nhưng chưa chuyển đổi (2,0% khách) | Gỡ rào cản chuyển đổi | Tìm lý do hủy/bỏ dở (thanh toán, giá, giao hàng), retarget đúng sản phẩm từng đặt; ưu tiên 152 khách có ≥ 2 đơn thất bại | Email/retargeting theo sản phẩm đã đặt | Tỷ lệ chuyển đổi đơn đầu |
| 3 | C3 Khách mới / tiềm năng (5,7% doanh thu) | Tạo thói quen mua lặp lại | Voucher đơn kế tiếp trong 30 ngày, email onboarding, gợi ý sản phẩm bán chạy | Email và kênh trực tiếp (lift 1,17 và 1,33) | Tỷ lệ mua lần tiếp theo trong 90 ngày |
| 4 | C4 Ngủ đông (13,1% doanh thu) | Đánh thức với chi phí thấp | Email theo mùa, ưu đãi nhỏ; chạy thử với nhóm đối chứng trước khi tăng ngân sách | Email (lift 1,35), kênh trực tiếp | Reactivation rate |
| 5 | C1 Đã rời bỏ (2,6% doanh thu) | Tối ưu chi phí | Chỉ email định kỳ, không ưu đãi lớn; rà soát trải nghiệm sản phẩm GenZ/Outdoor vì nhóm này mua hai danh mục đó nhiều bất thường | Email chi phí gần 0 | Chi phí/đơn kéo về |

**Nguyên tắc chung:** đo mọi hành động bằng nhóm đối chứng (giữ 10% khách mỗi nhóm không nhận ưu đãi) để biết doanh thu tăng thêm thật sự. Ước tính tác động doanh thu cần tỷ lệ phản hồi thực tế từ lần chạy thử, nên chưa đưa con số ở đây.

---

## Cách chạy

```bash
python customer_segmentation/01_build_customer_dataset.py
python customer_segmentation/02_transform_features.py
python customer_segmentation/03_pca_analysis.py                    # --variance-target 0.9 / --n-components 2
python customer_segmentation/04_select_k.py                        # quét k, không ghi nhãn
python customer_segmentation/05_kmeans_segmentation.py --k <k>     # --input pca|scaled
python customer_segmentation/06_cluster_profiling.py
```

**Đầu ra** (trong `data/processed/customer_segmentation/`):

| File | Nội dung |
|---|---|
| `customer_analysis_base.csv` | RFM + nhân khẩu học + nhóm rule-based cho toàn bộ khách |
| `customer_features_transformed.csv` | RFM sau biến đổi + scale (khách đã mua) |
| `feature_engineering/*.csv` | So sánh phép biến đổi, đánh giá biến ứng viên |
| `customer_pca_scores.csv`, `pca_*.csv` | Điểm PC và kết quả PCA |
| `k_selection/*.csv` | Chỉ số và thành phần cụm theo từng k |
| `customer_segments.csv` | Nhãn K-Means (khách đã mua) |
| `customer_segments_all.csv` | Nhãn cuối cùng cho **toàn bộ** khách (rule-based + K-Means) |
| `profiles/*.csv` | Profile số, rank index, profile phân loại, kiểm định Cramér's V |
| `plots/` | Biểu đồ PCA và profile |

## Nhật ký cập nhật ✍️

| Ngày | Thay đổi |
|---|---|
| 2026-10-15 | Tạo flow; hoàn thành aggregation, quality check, log + scale, PCA |
| 2026-10-15 | Thêm rule-based segmentation cho khách chưa mua; thêm bước profiling (bức tranh tổng thể) |
| 2026-10-15 | Đổi business rule doanh thu: tính cả đơn `paid`/`shipped`, chỉ loại `created` và `cancelled`; RB3 = có đơn `created` |
| 2026-10-15 | Thêm bước 4 chọn k (quét k = 2–8, đánh giá thống kê + ổn định + business); đổi luật đặt tên cụm sang ma trận Recency × Giá trị |
| 2026-10-15 | Rule-based còn 2 nhóm: RB1 Chưa giao dịch, RB2 Đặt đơn nhưng chưa chuyển đổi (gộp đơn hủy + đơn bỏ dở, thêm `failed_order_count`, `failed_reason`) |
| 2026-10-15 | Thêm báo cáo feature engineering: so sánh phép biến đổi theo skew, tham số scale, đánh giá biến hành vi ứng viên |
| 2026-10-16 | Chốt k = 5 kèm lý do; điền kết quả cụm, profile và hành động theo từng nhóm; bước chọn k ưu tiên k đạt điều kiện có nhiều nhóm hành động nhất |
