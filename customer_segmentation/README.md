# Customer Segmentation

Phân nhóm khách hàng theo hành vi mua (RFM) bằng K-Means, mô tả chân dung từng nhóm và đề xuất hành động để tăng doanh thu.

> README này mô tả **flow** của phần phân cụm. Các mục đánh dấu ✍️ là chỗ cần điền khi có kết quả cụ thể.

## Flow tổng quan

```text
                                   ┌─ chưa có đơn doanh thu ► Rule-based (RB1/RB2/RB3) ───────────────────────┐
data/raw ─► 1. Aggregation ─► 2. QC ┤                                                                          ├─► 6. Profile ─► 7. Recommendation
           (đơn → khách)            └─ đã mua ─► 3. Feature engineering ─► 4. K-Means ─► 5. Kết quả cụm ──────┘   (toàn bộ khách)
                                                (RFM, log, scale, PCA)      (chọn k)
```

| Bước | Script | Việc làm | Trạng thái |
|---|---|---|---|
| 1–2 | `01_build_customer_dataset.py` | Aggregation, quality check, tính RFM, gán nhóm rule-based | ✅ |
| 3a | `02_transform_features.py` | log1p + StandardScaler | ✅ |
| 3b | `03_pca_analysis.py` | PCA + giải thích → [`reports/customer_segmentation_pca.md`](../reports/customer_segmentation_pca.md) | ✅ |
| 4 | `04_select_k.py` | Quét k = 2–8, đánh giá thống kê + ổn định + business → [`reports/customer_segmentation_k_selection.md`](../reports/customer_segmentation_k_selection.md) | ✅ |
| 5 | `05_kmeans_segmentation.py` | K-Means với k đã chọn → `customer_segments.csv` (`customer_id`, `cluster`) | ✍️ tự điều chỉnh |
| 6–8 | `06_cluster_profiling.py` | Bức tranh tổng thể, profile, gợi ý hành động → [`reports/customer_segment_profiles.md`](../reports/customer_segment_profiles.md) | ✅ (chạy lại sau khi chốt K-Means) |

`config.py` chứa toàn bộ đường dẫn, định nghĩa trạng thái đơn và luật rule-based. `segment_naming.py` chứa luật đặt tên cụm gợi ý và hành động theo nhóm. `plot_style.py` chứa màu và style biểu đồ.

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

**Kết quả:** `customer_analysis_base.csv` có 121.930 khách, kèm các cột `segment_method` (`kmeans`/`rule_based`), `rule_segment` và `order_count_all`.

### Rule-based segmentation (khách chưa có đơn phát sinh doanh thu)

Khách chưa mua không có RFM có ý nghĩa: R không xác định, còn F = M = 0. Nếu đưa vào K-Means, họ sẽ tạo thành một cụm "toàn số 0" và làm lệch các cụm còn lại. Vì vậy họ được gán nhãn bằng luật **trước khi** phân cụm. Luật xét theo thứ tự, định nghĩa trong `config.RULE_SEGMENTS`:

| Mã | Nhóm | Điều kiện | Số khách | Mục tiêu |
|---|---|---|---:|---|
| — | → K-Means | Có ≥ 1 đơn `paid`/`shipped`/`delivered`/`returned` | 87.839 | Xem bước 4–6 |
| RB3 | Có đơn mới tạo, chưa thanh toán | Có đơn `created` | 284 | Chuyển thành đơn thanh toán |
| RB2 | Chỉ có đơn bị hủy | Mọi đơn đều `cancelled` | 2.123 | Tìm và gỡ lý do hủy |
| RB1 | Chưa từng đặt đơn | Không có đơn nào | 31.684 | Kích hoạt đơn đầu tiên |

Kết quả cuối: `customer_segments_all.csv`, gồm `customer_id`, `segment_method`, `segment` (RB1–3 / C0…Ck), `segment_name`. Mọi khách hàng đều có đúng một nhãn.

## 2. Quality check

**Kiểm tra trong `01_build_customer_dataset.py`** — script dừng ngay nếu có lỗi:

- Khóa chính không trùng, không rỗng: `customers.customer_id`, `orders.order_id`, `payments.order_id`, `geography.zip`.
- `order_date` và `payment_value` chuyển kiểu hợp lệ.
- Mọi `orders.customer_id` có trong `customers`; `payments` khớp 1–1 với `orders`; mọi `returns.order_id` có trong `orders`.

**Vấn đề dữ liệu ảnh hưởng đến phân cụm** (từ [báo cáo EDA](../reports/data_quality_and_eda.md)) và cách xử lý:

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

### 3.2 Biến đổi

1. **`log1p`**: giảm độ lệch phải của F và M, để vài khách chi tiêu cực lớn không kéo tâm cụm.
2. **`StandardScaler`**: đưa 3 biến về cùng thang. K-Means dùng khoảng cách Euclid, nên nếu không scale thì Monetary (đơn vị tiền) sẽ lấn át hai biến còn lại.
3. **PCA** — chi tiết trong [`reports/customer_segmentation_pca.md`](../reports/customer_segmentation_pca.md):
   - **Vì sao:** Frequency và Monetary tương quan **r = 0,83**, tức K-Means sẽ tính khía cạnh "giá trị mua" gần như hai lần. PCA xoay sang các trục không tương quan, đồng thời cho phép vẽ cụm trên mặt phẳng 2D.
   - **Có phù hợp không:** Bartlett p ≈ 0 (các biến có tương quan) và KMO = 0,65 (chấp nhận được).
   - **Kết quả:** PC1 giải thích 77,1% phương sai (trục "giá trị & gắn bó": +F, +M, −R); PC2 giải thích 17,4% (trục "độ mới", Recency nổi trội). **Giữ 2 PC = 94,6% phương sai.**
   - **Lưu ý:** nếu giữ đủ 3 PC thì K-Means cho kết quả y hệt dữ liệu đã scale. Lợi ích chỉ đến từ việc bỏ PC3.

### 3.3 Biến hành vi bổ sung cho profile *(dự kiến — không đưa vào K-Means trừ khi quyết định khác)*

- Giá trị đơn trung bình (AOV = M / F).
- Tỷ lệ đơn bị trả, tỷ lệ đơn hủy.
- Tỷ lệ dòng hàng có khuyến mãi.
- Số ngày từ đơn đầu tiên (tenure, thay cho `signup_date`).
- Danh mục / thiết bị / phương thức thanh toán / nguồn đơn ưa thích.
- Điểm đánh giá trung bình.

✍️ Ghi lại ở đây nếu quyết định thêm biến nào vào K-Means.

## 4. Chọn số cụm k — `04_select_k.py`

Bước này **chỉ đánh giá, không ghi nhãn**. Quét k = 2–8 trên `customer_pca_scores.csv`, mỗi k chạy 5 `random_state`. Chi tiết: [`reports/customer_segmentation_k_selection.md`](../reports/customer_segmentation_k_selection.md).

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

- **Elbow:** k = 4. **Xếp hạng thống kê:** k = 3 tốt nhất trong các k đạt điều kiện.
- **Ứng viên:**
  - **k = 3**: tách rõ nhất, nhưng gộp chung khách mới mua gần đây với khách đã lâu không quay lại.
  - **k = 5**: thống kê tốt hơn k = 4 (silhouette 0,374 so với 0,346; DB 0,846 so với 0,990), đủ ổn định. Tách thêm 2 nhóm có hành động riêng: **Khách mới / tiềm năng** (10%, mua gần đây nhưng ít đơn) và **Đã rời bỏ** (25%, chỉ 2,6% doanh thu).

✍️ **k đã chọn:** … · **Lý do:** …

## 5. K-Means — `05_kmeans_segmentation.py` ✍️

- **Chạy với k đã chọn:** `--k <k>`. Đầu vào mặc định là PCA; `--input scaled` để chạy trên dữ liệu đã scale.
- **Đầu ra bắt buộc:** `customer_segments.csv` gồm 2 cột `customer_id`, `cluster`.

## 6. Kết quả phân cụm ✍️

| Cụm | Tên gợi ý | Số khách | % khách | % doanh thu | Recency (median, ngày) | Frequency (median) | Monetary (median) | AOV |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | … | | | | | | | |
| 1 | … | | | | | | | |

**Cách đặt tên gợi ý** (`segment_naming.py`): ma trận Recency × Giá trị (giá trị = trung bình phân vị F và M của cụm so với mặt bằng):

| | Giá trị cao | Giá trị thấp |
|---|---|---|
| **Mua gần đây** | Champions → Trung thành | Khách mới / tiềm năng → Cần nuôi dưỡng |
| **Lâu chưa mua** | Có nguy cơ rời bỏ | Ngủ đông → Đã rời bỏ |

Hai cụm rơi cùng ô thì cụm điểm cao hơn giữ tên, cụm sau lùi sang tên kế tiếp (theo mũi tên). Tên chỉ là gợi ý; tên chính thức đặt sau khi xem profile.

Biểu đồ: các cụm trên PC1–PC2, boxplot RFM theo cụm, heatmap z-score của từng chỉ số theo cụm.

## 7. Customer group profile ✍️

**Biến mô tả có trong dữ liệu:**

- Nhân khẩu học: giới tính, nhóm tuổi, vùng, kênh thu hút.
- Hành vi: thiết bị, phương thức thanh toán, nguồn đơn, danh mục ưa thích.

Dữ liệu **không có** nghề nghiệp hay thu nhập.

**Phương pháp:**

- Tỷ lệ % của mỗi nhóm giá trị trong từng cụm.
- **Lift** = % trong cụm / % toàn bộ khách: lift > 1,15 là đặc trưng nổi bật của cụm, < 0,85 là ít gặp trong cụm.
- **Chi-square + Cramér's V** để biết biến nào thực sự khác biệt giữa các cụm. Với ~87 nghìn khách thì p-value gần như luôn rất nhỏ, nên đánh giá bằng Cramér's V: < 0,1 nghĩa là biến gần như không phân biệt cụm, không nên dùng để nhắm mục tiêu.

**Lưu ý từ bản chạy thử (k = 4):**

- **Không phân biệt được cụm** (Cramér's V < 0,01): giới tính, nhóm tuổi, kênh thu hút.
- **Phân biệt ở mức trung bình** (V ≈ 0,14–0,24): danh mục ưa thích, phương thức thanh toán, thiết bị, nguồn đơn.

Nghĩa là khi nhắm mục tiêu nên dựa vào hành vi mua, không nên dựa vào nhân khẩu học.

**Mẫu ghi cho mỗi cụm:**

> **Cụm X – <tên>** (n khách, x% khách, y% doanh thu)
> - Hành vi: …
> - Chân dung nổi bật: nhóm tuổi … (lift …), vùng …, kênh …
> - Khác biệt so với trung bình: …

## 8. Recommendation để tăng doanh thu ✍️

**Khung hành động theo loại cụm** (điều chỉnh theo kết quả thực tế):

| Loại cụm | Mục tiêu | Hành động gợi ý | KPI đo |
|---|---|---|---|
| RB1 Chưa từng đặt đơn | Kích hoạt đơn đầu | Voucher đơn đầu có hạn, email giới thiệu sản phẩm bán chạy | Tỷ lệ chuyển đổi đơn đầu |
| RB2 Chỉ có đơn hủy | Gỡ lý do hủy | Khảo sát lý do hủy, nhắc giỏ hàng, hỗ trợ thanh toán | Tỷ lệ đặt lại thành công |
| RB3 Đơn mới tạo, chưa thanh toán | Chuyển thành đơn thanh toán | Nhắc thanh toán/giỏ hàng bỏ dở trong 24–48h, hỗ trợ COD/trả góp | Tỷ lệ created → paid |
| Champions / giá trị cao | Giữ chân, tăng giá trị | Chương trình VIP, early access, upsell sản phẩm premium; hạn chế giảm giá sâu | Retention rate, AOV |
| Trung thành | Tăng tần suất | Tích điểm, gợi ý cross-sell theo danh mục ưa thích | Frequency, doanh thu/khách |
| Khách mới / tiềm năng | Tạo thói quen mua lặp lại | Voucher đơn kế tiếp trong 30 ngày, onboarding email | Tỷ lệ mua lần tiếp theo |
| Cần nuôi dưỡng | Nâng giá trị đơn | Bundle/khuyến mãi theo ngưỡng giá trị đơn | AOV, Frequency |
| Có nguy cơ rời bỏ | Kéo quay lại | Win-back cá nhân hóa, ưu đãi có hạn theo danh mục từng mua nhiều | Reactivation rate |
| Ngủ đông | Đánh thức với chi phí thấp | Remarketing/email theo mùa, ưu đãi nhỏ; đo phản hồi trước khi đầu tư | Reactivation rate |
| Đã rời bỏ | Tối ưu chi phí | Chỉ dùng kênh chi phí gần 0 (email định kỳ); không đầu tư ưu đãi lớn | Chi phí/đơn kéo về |

✍️ Với mỗi cụm thực tế, ghi lại:

- Hành động cụ thể.
- Kênh tiếp cận (dựa trên profile).
- Ước tính tác động doanh thu, ví dụ: tăng 5% tỷ lệ mua lại ở cụm X × AOV × số khách = +… doanh thu.
- Ưu tiên triển khai.

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
| `customer_features_transformed.csv` | RFM sau log1p + scale (khách đã mua) |
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
