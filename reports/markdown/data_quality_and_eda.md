# Báo cáo chất lượng dữ liệu và EDA

Tạo tự động bởi `eda/data_quality_eda.py` từ `data/raw/`. Mô tả ý nghĩa từng bảng: [`00_data_overview.md`](00_data_overview.md). Script chỉ phát hiện, **không sửa** dữ liệu gốc; dòng vi phạm của từng kiểm tra nằm tại `data/processed/eda/violations/<bảng>__<kiểm tra>.csv`.

Mức độ: **ERROR** — vi phạm ràng buộc cứng, phải xử lý trước khi phân tích; **WARNING** — bất thường/nghi vấn, cần quyết định cách xử lý; **INFO** — đặc điểm dữ liệu cần biết, **không phải lỗi** (hiển thị ℹ️).

## 1. Tổng quan

- 13 bảng, 2,960,188 dòng; 362 kiểm tra, **14** có vi phạm (2 ERROR, 12 WARNING) và **3** đặc điểm dữ liệu cần biết (INFO, không phải lỗi).

| Nhóm | Bảng | Số dòng | Số cột | Ô thiếu (%) | Dòng trùng | ERROR | WARNING | INFO |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Master | `customers` | 121,930 | 7 | 0% | 0 | 0 | 1 | 1 |
| Master | `geography` | 39,948 | 4 | 0% | 0 | 0 | 0 | 0 |
| Master | `products` | 2,412 | 8 | 0% | 0 | 0 | 2 | 1 |
| Master | `promotions` | 50 | 10 | 8% | 0 | 0 | 0 | 0 |
| Transaction | `orders` | 646,945 | 8 | 0% | 0 | 1 | 2 | 0 |
| Transaction | `order_items` | 714,669 | 7 | 23.04% | 0 | 0 | 3 | 0 |
| Transaction | `payments` | 646,945 | 4 | 0% | 0 | 0 | 0 | 0 |
| Transaction | `shipments` | 566,067 | 4 | 0% | 0 | 0 | 0 | 0 |
| Transaction | `returns` | 39,939 | 7 | 0% | 0 | 1 | 2 | 0 |
| Transaction | `reviews` | 113,551 | 7 | 0% | 0 | 0 | 0 | 0 |
| Analytical | `sales` | 3,833 | 3 | 0% | 0 | 0 | 1 | 0 |
| Operational | `inventory` | 60,247 | 17 | 0% | 0 | 0 | 0 | 1 |
| Operational | `web_traffic` | 3,652 | 7 | 0% | 0 | 0 | 1 | 0 |

## 2. Các vấn đề chính cần xử lý

| Mức | Bảng | Kiểm tra | Vi phạm | % | Đề xuất xử lý |
|---|---|---|---:|---:|---|
| ERROR | `returns` | Tổng tiền hoàn của đơn ≤ `payments.payment_value` | 3,633 | 10.07% | Clip tổng hoàn về tiền thanh toán (giá trị ròng của đơn không âm). |
| ERROR | `orders` | Đơn `shipped`/`delivered`/`returned` phải có bản ghi `shipments` | 564 | 0.10% | Giữ đơn cho doanh thu; loại khỏi phân tích thời gian giao hàng (không impute ngày giao). |
| WARNING | `orders` | Ngày đặt ≥ ngày đăng ký của khách | 477,453 | 73.80% | Giữ đơn (giao dịch là dữ liệu gốc đáng tin hơn); coi `signup_date` là không tin cậy. |
| WARNING | `order_items` | Giá trị đơn (trước giảm) ≥ `min_order_value` của khuyến mãi | 110,717 | 40.07% | Gắn cờ khuyến mãi áp không đủ điều kiện. |
| WARNING | `customers` | Ngày đăng ký ≤ ngày đặt đơn đầu tiên | 80,623 | 89.34% | Không dùng `signup_date` để tính tenure/cohort; thay bằng ngày đơn đầu tiên (hoặc min(signup_date, first_order_date)). |
| WARNING | `order_items` | Đơn giá bán trong khoảng 50%–120% giá niêm yết | 10,531 | 1.47% | Giá lệch mạnh so với niêm yết: xác minh; dùng `unit_price` làm giá thực tế. |
| WARNING | `returns` | Tiền hoàn ≤ giá trị dòng sau giảm (khách thực trả) | 4,415 | 11.05% | Hoàn theo giá trước giảm giá: khi tính doanh thu thuần, clip tiền hoàn về giá trị dòng sau giảm. |
| WARNING | `web_traffic` | `bounce_rate` ≥ 1% (giá trị < 1% nghi lưu sai thang) | 3,652 | 100% | Nhiều khả năng đơn vị là % chia thêm 100 → nhân 100 hoặc chỉ dùng so sánh tương đối. |
| WARNING | `products` | Giá niêm yết < 100 (nhỏ hơn ~50 lần mức thông thường — nghi sai đơn vị) | 654 | 27.11% | Các SKU này không có giao dịch; tách riêng hoặc loại khỏi thống kê giá sản phẩm. |
| WARNING | `products` | Khóa nghiệp vụ (product_name, size, color) không lặp | 426 | 17.66% | Gộp các dòng cùng khóa (cộng số lượng/tiền) trước khi nối bảng để tránh nhân bản. |
| WARNING | `sales` | `COGS` ≤ `Revenue` (ngày không lỗ gộp) | 382 | 9.97% | Có thể hợp lệ (ngày khuyến mãi sâu); giữ lại, gắn cờ khi phân tích biên lợi nhuận. |
| WARNING | `orders` | Đơn `returned` phải có ít nhất một dòng `returns` | 80 | 0.22% | Không có tiền hoàn tương ứng: coi tiền hoàn = 0, gắn cờ khi tính tỷ lệ trả. |
| WARNING | `order_items` | Khóa nghiệp vụ (order_id, product_id) không lặp | 32 | 0.00% | Gộp các dòng cùng khóa (cộng số lượng/tiền) trước khi nối bảng để tránh nhân bản. |
| WARNING | `returns` | Khóa nghiệp vụ (order_id, product_id) không lặp | 4 | 0.01% | Gộp các dòng cùng khóa (cộng số lượng/tiền) trước khi nối bảng để tránh nhân bản. |

### Đặc điểm dữ liệu cần biết (không phải lỗi)

| Bảng | Đặc điểm | Số dòng | % | Ghi chú |
|---|---|---:|---:|---|
| `customers` | Khách đăng ký nhưng chưa đặt đơn nào (hợp lệ) | 31,684 | 25.99% | Không phải lỗi. Giữ trong bảng khách hàng; là nhóm RB1 (Chưa giao dịch) trong phân nhóm khách hàng. |
| `products` | SKU chưa từng xuất hiện trong `order_items` (hợp lệ) | 814 | 33.75% | Không phải lỗi. Giữ trong danh mục; loại khỏi phân tích hiệu quả sản phẩm. |
| `inventory` | `reorder_flag` là hằng số: mọi dòng cùng một giá trị | 60,247 | 100% | Không phải lỗi dữ liệu nhưng cột không mang thông tin: loại khỏi mô hình/phân tích. |

## 3. Chi tiết theo bảng

### 3.1. `customers` (Master)

121,930 dòng × 7 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `gender` | 3 | `Female` 59,640 (48.9%), `Male` 57,457 (47.1%), `Non-binary` 4,833 (4.0%) |
| `age_group` | 5 | `25-34` 36,342 (29.8%), `35-44` 31,920 (26.2%), `45-54` 23,172 (19.0%), `18-24` 17,039 (14.0%), `55+` 13,457 (11.0%) |
| `acquisition_channel` | 6 | `organic_search` 36,450 (29.9%), `social_media` 24,448 (20.1%), `paid_search` 24,285 (19.9%), `email_campaign` 14,674 (12.0%), `referral` 12,270 (10.1%), `direct` 9,803 (8.0%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 7 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 121,930 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (customer_id) là duy nhất | ERROR | 121,930 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 13 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `zip` tồn tại trong `geography.zip` | ERROR | 121,930 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `city` khớp với `geography.city` theo `zip` | ERROR | 121,930 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Ngày đăng ký ≤ ngày đặt đơn đầu tiên | WARNING | 90,246 | 80,623 | ❌ 89.34% |
| Đặc điểm dữ liệu | Khách đăng ký nhưng chưa đặt đơn nào (hợp lệ) | INFO | 121,930 | 31,684 | ℹ️ 25.99% |

### 3.2. `geography` (Master)

39,948 dòng × 4 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `region` | 3 | `East` 18,929 (47.4%), `Central` 14,512 (36.3%), `West` 6,507 (16.3%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 4 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 39,948 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (zip) là duy nhất | ERROR | 39,948 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 6 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |

### 3.3. `products` (Master)

2,412 dòng × 8 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `category` | 4 | `Streetwear` 1,320 (54.7%), `Outdoor` 743 (30.8%), `Casual` 201 (8.3%), `GenZ` 148 (6.1%) |
| `segment` | 8 | `Activewear` 598 (24.8%), `Everyday` 405 (16.8%), `Performance` 347 (14.4%), `Balanced` 306 (12.7%), `Standard` 262 (10.9%), `Premium` 177 (7.3%), `All-weather` 169 (7.0%), `Trendy` 148 (6.1%) |
| `size` | 4 | `S` 603 (25%), `M` 603 (25%), `L` 603 (25%), `XL` 603 (25%) |
| `color` | 10 | `black` 242 (10.0%), `orange` 242 (10.0%), `green` 241 (10.0%), `silver` 241 (10.0%), `pink` 241 (10.0%), `yellow` 241 (10.0%), `red` 241 (10.0%), `blue` 241 (10.0%), `white` 241 (10.0%), `purple` 241 (10.0%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 8 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 2,412 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (product_id) là duy nhất | ERROR | 2,412 | 0 | ✅ PASS |
| Trùng lặp | Khóa nghiệp vụ (product_name, size, color) không lặp | WARNING | 2,412 | 426 | ❌ 17.66% |
| Kiểu dữ liệu & miền giá trị | 13 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Giá vốn < giá bán (`cogs` < `price`) | ERROR | 2,412 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Giá niêm yết < 100 (nhỏ hơn ~50 lần mức thông thường — nghi sai đơn vị) | WARNING | 2,412 | 654 | ❌ 27.11% |
| Đặc điểm dữ liệu | SKU chưa từng xuất hiện trong `order_items` (hợp lệ) | INFO | 2,412 | 814 | ℹ️ 33.75% |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `price` | 9.06 | 59.44 | 4,399.60 | 7,720.51 | 40,950 | 1.33 | [-11,432.16; 19,212.12] | 31 (1.29%) | 2 | 0 |
| `cogs` | 5.18 | 35.07 | 3,184.93 | 5,864.92 | 38,902.50 | 1.49 | [-8,709.71; 14,609.69] | 37 (1.53%) | 3 | 0 |

### 3.4. `promotions` (Master)

50 dòng × 10 cột · 40 ô thiếu (8%) · 0 dòng trùng toàn bộ.

**Missing values**

| Cột | Thiếu | % | Loại | Xử lý |
|---|---:|---:|---|---|
| `applicable_category` | 40 | 80% | có ý nghĩa nghiệp vụ | Trống = áp dụng mọi danh mục. Điền 'ALL'. |

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `promo_type` | 2 | `percentage` 45 (90%), `fixed` 5 (10%) |
| `discount_value` | 6 | `12` 10 (20%), `18` 10 (20%), `10` 10 (20%), `20` 10 (20%), `50` 5 (10%), `15` 5 (10%) |
| `applicable_category` | 2 | `(trống)` 40 (80%), `Streetwear` 5 (10%), `Outdoor` 5 (10%) |
| `promo_channel` | 5 | `all_channels` 19 (38%), `online` 13 (26%), `email` 7 (14.0%), `social_media` 6 (12%), `in_store` 5 (10%) |
| `stackable_flag` | 2 | `0` 38 (76%), `1` 12 (24%) |
| `min_order_value` | 5 | `0` 31 (62%), `150000` 8 (16%), `100000` 5 (10%), `50000` 4 (8%), `200000` 2 (4%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 9 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 50 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (promo_id) là duy nhất | ERROR | 50 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 17 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `start_date` ≤ `end_date` | ERROR | 50 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Khuyến mãi % có `discount_value` trong (0, 100] | ERROR | 45 | 0 | ✅ PASS |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `discount_value` | 10 | 12 | 16.50 | 20 | 50 | 2.20 | [0; 32] | 5 (10%) | 5 | 5 |
| `min_order_value` | 0 | 0 | 0 | 100,000 | 200,000 | 1.04 | [-150,000; 250,000] | 0 (0%) | 0 | — |

### 3.5. `orders` (Transaction)

646,945 dòng × 8 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `order_status` | 6 | `delivered` 516,716 (79.9%), `cancelled` 59,462 (9.2%), `returned` 36,142 (5.6%), `shipped` 13,773 (2.1%), `paid` 13,577 (2.1%), `created` 7,275 (1.1%) |
| `payment_method` | 5 | `credit_card` 356,352 (55.1%), `paypal` 97,018 (15.0%), `cod` 96,681 (14.9%), `apple_pay` 64,763 (10.0%), `bank_transfer` 32,131 (5.0%) |
| `device_type` | 3 | `mobile` 291,482 (45.1%), `desktop` 258,855 (40.0%), `tablet` 96,608 (14.9%) |
| `order_source` | 6 | `organic_search` 181,495 (28.1%), `paid_search` 141,652 (21.9%), `social_media` 129,710 (20.0%), `email_campaign` 77,572 (12.0%), `referral` 64,565 (10.0%), `direct` 51,951 (8.0%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 8 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 646,945 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (order_id) là duy nhất | ERROR | 646,945 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 16 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `customer_id` tồn tại trong `customers.customer_id` | ERROR | 646,945 | 0 | ✅ PASS |
| Khóa ngoại | `zip` tồn tại trong `geography.zip` | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Ngày đặt ≥ ngày đăng ký của khách | WARNING | 646,945 | 477,453 | ❌ 73.80% |
| Ràng buộc nghiệp vụ | Mỗi đơn có ít nhất một dòng `order_items` | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Mỗi đơn có một bản ghi `payments` | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Đơn `shipped`/`delivered`/`returned` phải có bản ghi `shipments` | ERROR | 566,631 | 564 | ❌ 0.10% |
| Ràng buộc nghiệp vụ | Đơn `created`/`paid`/`cancelled` không có bản ghi `shipments` | ERROR | 80,314 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Đơn `returned` phải có ít nhất một dòng `returns` | WARNING | 36,142 | 80 | ❌ 0.22% |
| Đặc điểm dữ liệu | Đơn giao tới `zip` khác `zip` của khách | INFO | 646,945 | 0 | ✅ PASS |

### 3.6. `order_items` (Transaction)

714,669 dòng × 7 cột · 1,152,816 ô thiếu (23.04%) · 0 dòng trùng toàn bộ.

**Missing values**

| Cột | Thiếu | % | Loại | Xử lý |
|---|---:|---:|---|---|
| `promo_id` | 438,353 | 61.34% | có ý nghĩa nghiệp vụ | Trống = dòng không dùng khuyến mãi. Giữ nguyên / điền 'NO_PROMO' khi phân tích. |
| `promo_id_2` | 714,463 | 99.97% | có ý nghĩa nghiệp vụ | Trống = không có khuyến mãi cộng dồn. Giữ nguyên / điền 'NO_PROMO'. |

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `quantity` | 8 | `1` 89,623 (12.5%), `5` 89,608 (12.5%), `6` 89,500 (12.5%), `2` 89,394 (12.5%), `7` 89,348 (12.5%), `4` 89,263 (12.5%), `3` 89,252 (12.5%), `8` 88,681 (12.4%) |
| `promo_id_2` | 2 | `(trống)` 714,463 (100.0%), `PROMO-0015` 132 (0.0%), `PROMO-0025` 74 (0.0%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 5 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 714,669 | 0 | ✅ PASS |
| Trùng lặp | Khóa nghiệp vụ (order_id, product_id) không lặp | WARNING | 714,669 | 32 | ❌ 0.00% |
| Kiểu dữ liệu & miền giá trị | 13 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `order_id` tồn tại trong `orders.order_id` | ERROR | 714,669 | 0 | ✅ PASS |
| Khóa ngoại | `product_id` tồn tại trong `products.product_id` | ERROR | 714,669 | 0 | ✅ PASS |
| Khóa ngoại | `promo_id` tồn tại trong `promotions.promo_id` | ERROR | 276,316 | 0 | ✅ PASS |
| Khóa ngoại | `promo_id_2` tồn tại trong `promotions.promo_id` | ERROR | 206 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | 0 ≤ `discount_amount` ≤ `quantity` × `unit_price` | ERROR | 714,669 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Có `promo_id_2` thì phải có `promo_id` | ERROR | 714,669 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Có giảm giá ⇔ có mã khuyến mãi | WARNING | 714,669 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Ngày đặt nằm trong thời gian hiệu lực khuyến mãi | ERROR | 276,316 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Danh mục sản phẩm khớp `applicable_category` của khuyến mãi | ERROR | 29,855 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Giá trị đơn (trước giảm) ≥ `min_order_value` của khuyến mãi | WARNING | 276,316 | 110,717 | ❌ 40.07% |
| Ràng buộc nghiệp vụ | Tiền giảm khớp loại khuyến mãi: % = thành tiền × %, cố định = mức giảm × số lượng | WARNING | 276,110 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Đơn giá bán trong khoảng 50%–120% giá niêm yết | WARNING | 714,669 | 10,531 | ❌ 1.47% |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `quantity` | 1 | 2 | 4 | 6 | 8 | 0.00 | [-4; 12] | 0 (0%) | 0 | 0 |
| `unit_price` | 392.57 | 1,906.89 | 4,257.77 | 7,273.76 | 43,056 | 1.02 | [-6,143.41; 15,324.07] | 8,623 (1.21%) | 177 | 0 |
| `discount_amount` | 0 | 0 | 0 | 967.63 | 35,235.47 | 3.38 | [-1,451.44; 2,419.07] | 105,767 (14.80%) | 66,211 | — |

### 3.7. `payments` (Transaction)

646,945 dòng × 4 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `payment_method` | 5 | `credit_card` 356,352 (55.1%), `paypal` 97,018 (15.0%), `cod` 96,681 (14.9%), `apple_pay` 64,763 (10.0%), `bank_transfer` 32,131 (5.0%) |
| `installments` | 5 | `1` 262,866 (40.6%), `3` 218,949 (33.8%), `6` 109,910 (17.0%), `12` 54,126 (8.4%), `2` 1,094 (0.2%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 4 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 646,945 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (order_id) là duy nhất | ERROR | 646,945 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 9 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `order_id` tồn tại trong `orders.order_id` | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `payment_value` = Σ(`quantity` × `unit_price` − `discount_amount`) của đơn (sai số ≤ 1) | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `payment_method` trùng `orders.payment_method` | ERROR | 646,945 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `installments` trong 1–12; COD chỉ 1 kỳ | ERROR | 646,945 | 0 | ✅ PASS |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `payment_value` | 389.74 | 7,681.06 | 17,229.44 | 33,706.35 | 331,570.40 | 1.68 | [-31,356.87; 72,744.29] | 30,219 (4.67%) | 2,843 | 3,976 |

### 3.8. `shipments` (Transaction)

566,067 dòng × 4 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 4 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 566,067 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (order_id) là duy nhất | ERROR | 566,067 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 8 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `order_id` tồn tại trong `orders.order_id` | ERROR | 566,067 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `ship_date` ≥ `order_date` | ERROR | 566,067 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `delivery_date` ≥ `ship_date` | ERROR | 566,067 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Đơn có vận chuyển phải ở trạng thái shipped/delivered/returned | ERROR | 566,067 | 0 | ✅ PASS |
| Outlier theo ngữ cảnh | `shipping_days` ≤ rào IQR trên (10.5 ngày) | WARNING | 566,067 | 0 | ✅ PASS |
| Outlier theo ngữ cảnh | `processing_days` ≤ rào IQR trên (5.0 ngày) | WARNING | 566,067 | 0 | ✅ PASS |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `shipping_fee` | 0 | 0.87 | 1.73 | 2.60 | 32 | 2.17 | [-1.72; 5.20] | 76,050 (13.43%) | 76,050 | — |

### 3.9. `returns` (Transaction)

39,939 dòng × 7 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `return_reason` | 5 | `wrong_size` 13,967 (35.0%), `defective` 8,020 (20.1%), `not_as_described` 7,035 (17.6%), `changed_mind` 6,931 (17.4%), `late_delivery` 3,986 (10.0%) |
| `return_quantity` | 8 | `1` 13,581 (34.0%), `2` 8,633 (21.6%), `3` 6,050 (15.1%), `4` 4,464 (11.2%), `5` 3,127 (7.8%), `6` 2,126 (5.3%), `7` 1,322 (3.3%), `8` 636 (1.6%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 7 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 39,939 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (return_id) là duy nhất | ERROR | 39,939 | 0 | ✅ PASS |
| Trùng lặp | Khóa nghiệp vụ (order_id, product_id) không lặp | WARNING | 39,939 | 4 | ❌ 0.01% |
| Kiểu dữ liệu & miền giá trị | 14 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `order_id` tồn tại trong `orders.order_id` | ERROR | 39,939 | 0 | ✅ PASS |
| Khóa ngoại | `product_id` tồn tại trong `products.product_id` | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | (`order_id`, `product_id`) trả hàng có trong `order_items` | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Tổng số lượng trả ≤ số lượng mua của dòng | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Tiền hoàn ≤ giá trị dòng trước giảm (`quantity` × `unit_price`) | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Tiền hoàn ≤ giá trị dòng sau giảm (khách thực trả) | WARNING | 39,939 | 4,415 | ❌ 11.05% |
| Ràng buộc nghiệp vụ | Tổng tiền hoàn của đơn ≤ `payments.payment_value` | ERROR | 36,062 | 3,633 | ❌ 10.07% |
| Ràng buộc nghiệp vụ | `return_date` ≥ `order_date` | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `return_date` ≥ `delivery_date` | ERROR | 39,939 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Đơn có trả hàng phải ở trạng thái `returned` | WARNING | 39,939 | 0 | ✅ PASS |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `return_quantity` | 1 | 1 | 2 | 4 | 8 | 0.97 | [-3.50; 8.50] | 0 (0%) | 0 | 0 |
| `refund_amount` | 458.81 | 3,573.39 | 7,888.88 | 16,881.99 | 160,937.94 | 2.32 | [-16,389.50; 36,844.88] | 2,778 (6.96%) | 820 | 0 |

### 3.10. `reviews` (Transaction)

113,551 dòng × 7 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `rating` | 5 | `5` 45,256 (39.9%), `4` 36,412 (32.1%), `3` 17,016 (15.0%), `2` 9,095 (8.0%), `1` 5,772 (5.1%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 6 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 113,551 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (review_id) là duy nhất | ERROR | 113,551 | 0 | ✅ PASS |
| Trùng lặp | Khóa nghiệp vụ (order_id, product_id) không lặp | WARNING | 113,551 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 13 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `order_id` tồn tại trong `orders.order_id` | ERROR | 113,551 | 0 | ✅ PASS |
| Khóa ngoại | `product_id` tồn tại trong `products.product_id` | ERROR | 113,551 | 0 | ✅ PASS |
| Khóa ngoại | `customer_id` tồn tại trong `customers.customer_id` | ERROR | 113,551 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | (`order_id`, `product_id`) đánh giá có trong `order_items` | ERROR | 113,551 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `customer_id` đánh giá trùng người đặt đơn | ERROR | 113,551 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `review_date` ≥ `delivery_date` (và ≥ `order_date`) | ERROR | 113,551 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Chỉ đơn đã giao (`delivered`/`returned`) mới được đánh giá | WARNING | 113,551 | 0 | ✅ PASS |

### 3.11. `sales` (Analytical)

3,833 dòng × 3 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 3 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 3,833 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (Date) là duy nhất | ERROR | 3,833 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 6 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Chuỗi ngày liên tục, không thiếu ngày | ERROR | 3,833 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `COGS` ≤ `Revenue` (ngày không lỗ gộp) | WARNING | 3,833 | 382 | ❌ 9.97% |
| Ràng buộc nghiệp vụ | `Revenue` = Σ(`quantity` × `unit_price`) các đơn trong ngày (sai số ≤ 1) | WARNING | 3,833 | 0 | ✅ PASS |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `Revenue` | 279,813.94 | 2,471,088.82 | 3,647,303.90 | 5,350,877.20 | 20,905,271.35 | 1.67 | [-1,848,593.75; 9,670,559.77] | 169 (4.41%) | 34 | 41 |
| `COGS` | 236,576.31 | 2,150,580.23 | 3,161,112.99 | 4,637,293.92 | 16,535,857.67 | 1.63 | [-1,579,490.31; 8,367,364.46] | 165 (4.30%) | 32 | 31 |

### 3.12. `inventory` (Operational)

60,247 dòng × 17 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `stockout_flag` | 2 | `1` 40,571 (67.3%), `0` 19,676 (32.7%) |
| `overstock_flag` | 2 | `1` 45,942 (76.3%), `0` 14,305 (23.7%) |
| `reorder_flag` | 1 | `0` 60,247 (100%) |
| `category` | 4 | `Streetwear` 31,020 (51.5%), `Outdoor` 21,050 (34.9%), `GenZ` 4,674 (7.8%), `Casual` 3,503 (5.8%) |
| `segment` | 8 | `Activewear` 18,290 (30.4%), `Everyday` 13,598 (22.6%), `Performance` 7,673 (12.7%), `Balanced` 6,622 (11.0%), `Trendy` 4,674 (7.8%), `Premium` 3,182 (5.3%), `Standard` 3,127 (5.2%), `All-weather` 3,081 (5.1%) |
| `year` | 11 | `2018` 6,106 (10.1%), `2017` 6,084 (10.1%), `2016` 5,927 (9.8%), `2015` 5,872 (9.7%), `2019` 5,835 (9.7%), `2014` 5,787 (9.6%), `2020` 5,686 (9.4%), `2021` 5,609 (9.3%), `2013` 5,570 (9.2%), `2022` 5,232 (8.7%), `2012` 2,539 (4.2%) |
| `month` | 12 | `8` 5,541 (9.2%), `7` 5,238 (8.7%), `9` 5,201 (8.6%), `4` 5,181 (8.6%), `12` 5,146 (8.5%), `10` 5,130 (8.5%), `5` 5,117 (8.5%), `6` 5,052 (8.4%), `3` 4,924 (8.2%), `11` 4,814 (8.0%), `2` 4,567 (7.6%), `1` 4,336 (7.2%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 5 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 60,247 | 0 | ✅ PASS |
| Trùng lặp | Khóa nghiệp vụ (product_id, snapshot_date) không lặp | WARNING | 60,247 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 39 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Khóa ngoại | `product_id` tồn tại trong `products.product_id` | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `snapshot_date` là ngày cuối tháng | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `year`/`month` khớp `snapshot_date` | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `stockout_days` ≤ số ngày trong tháng | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `stockout_flag` = 1 ⇔ `stockout_days` > 0 | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `sell_through_rate` = sold / (sold + stock_on_hand) | ERROR | 60,247 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Tên/danh mục/phân khúc khớp bảng `products` | ERROR | 60,247 | 0 | ✅ PASS |
| Đặc điểm dữ liệu | `reorder_flag` là hằng số: mọi dòng cùng một giá trị | INFO | 60,247 | 60,247 | ℹ️ 100% |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `stock_on_hand` | 3 | 15 | 62 | 210 | 2,673 | 3.22 | [-277.50; 502.50] | 6,432 (10.68%) | 3,253 | 0 |
| `units_received` | 1 | 2 | 6 | 19 | 817 | 5.60 | [-23.50; 44.50] | 6,392 (10.61%) | 3,321 | 8 |
| `units_sold` | 1 | 2 | 6 | 16 | 670 | 5.55 | [-19; 37] | 6,388 (10.60%) | 3,410 | 16 |
| `stockout_days` | 0 | 0 | 1 | 2 | 28 | 7.40 | [-3; 5] | 724 (1.20%) | 483 | — |
| `days_of_supply` | 5.20 | 96 | 240 | 683.10 | 68,100 | 8.92 | [-784.65; 1,563.75] | 7,455 (12.37%) | 4,742 | 508 |
| `fill_rate` | 0.07 | 0.93 | 0.97 | 1 | 1 | -7.40 | [0.83; 1.10] | 724 (1.20%) | 483 | 848 |
| `sell_through_rate` | 0.00 | 0.04 | 0.11 | 0.24 | 0.85 | 1.31 | [-0.25; 0.53] | 1,284 (2.13%) | 4 | 845 |

### 3.13. `web_traffic` (Operational)

3,652 dòng × 7 cột · 0 ô thiếu (0%) · 0 dòng trùng toàn bộ.

**Missing values**

Không có giá trị thiếu.

**Giá trị phân loại** (cột có ≤ 15 giá trị)

| Cột | Số giá trị | Giá trị (số dòng, %) |
|---|---:|---|
| `traffic_source` | 6 | `organic_search` 1,090 (29.8%), `paid_search` 784 (21.5%), `social_media` 632 (17.3%), `email_campaign` 505 (13.8%), `referral` 375 (10.3%), `direct` 266 (7.3%) |

**Kiểm tra**

| Nhóm | Kiểm tra | Mức | Đã kiểm | Vi phạm | Kết quả |
|---|---|---|---:|---:|---|
| Missing values | 7 cột bắt buộc đều có giá trị | — | — | 0 | ✅ PASS |
| Trùng lặp | Không có dòng trùng toàn bộ | ERROR | 3,652 | 0 | ✅ PASS |
| Trùng lặp | Khóa chính (date) là duy nhất | ERROR | 3,652 | 0 | ✅ PASS |
| Kiểu dữ liệu & miền giá trị | 17 kiểm tra kiểu / miền / dấu / phạm vi ngày / định dạng text | — | — | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | Chuỗi ngày liên tục, không thiếu ngày | ERROR | 3,652 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `unique_visitors` ≤ `sessions` | ERROR | 3,652 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `page_views` ≥ `sessions` | ERROR | 3,652 | 0 | ✅ PASS |
| Ràng buộc nghiệp vụ | `bounce_rate` ≥ 1% (giá trị < 1% nghi lưu sai thang) | WARNING | 3,652 | 3,652 | ❌ 100% |

**Phân phối & outlier (IQR)**

| Cột | Min | Q1 | Median | Q3 | Max | Skew | Rào IQR 1,5× | Outlier | Cực trị 3× | Outlier thang log |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| `sessions` | 7,973 | 17,099.25 | 23,633.50 | 31,782.75 | 50,947 | 0.47 | [-4,926; 53,808] | 0 (0%) | 0 | 0 |
| `unique_visitors` | 6,136 | 12,915 | 17,924 | 24,191.75 | 40,430 | 0.51 | [-4,000.12; 41,106.88] | 0 (0%) | 0 | 0 |
| `page_views` | 30,451 | 72,982 | 101,010.50 | 138,086 | 275,560 | 0.65 | [-24,674; 235,742] | 18 (0.49%) | 0 | 0 |
| `bounce_rate` | 0.00 | 0.00 | 0.00 | 0.01 | 0.01 | 0.04 | [0.00; 0.01] | 0 (0%) | 0 | 0 |
| `avg_session_duration_sec` | 100.10 | 156.70 | 209.20 | 266.20 | 319.90 | 0.00 | [-7.55; 430.45] | 0 (0%) | 0 | 0 |

## 4. Nguyên tắc xử lý outlier

- Outlier IQR chỉ được **gắn cờ**, không tự động xóa: các biến tiền/số lượng lệch phải mạnh (skew > 1), nên rào IQR trên thang gốc đánh dấu nhiều giá trị lớn hợp lệ. Cột *Outlier thang log* cho số outlier sau log-transform — gần 0 nghĩa là đuôi phải tự nhiên, không phải lỗi.
- Với mô hình nhạy với outlier (K-Means, hồi quy tuyến tính): dùng log1p hoặc winsorize tại P1/P99; với mô hình cây: giữ nguyên.
- Outlier ở bảng tổng hợp ngày (`sales`, `web_traffic`) thường là ngày khuyến mãi/lễ — giữ lại và tạo biến cờ sự kiện.
- Giá trị vi phạm ràng buộc (âm, ngoài miền, sai thứ tự ngày) là **lỗi**, xử lý theo cột *Đề xuất xử lý* ở mục 2.
- Thời gian giao (`delivery_date − ship_date`): 2–7 ngày, trung vị 4 ngày.
- Khuyến mãi cố định giảm `discount_value` × số lượng cho mỗi dòng hàng, tức chỉ 0.41–6.39% thành tiền (trung vị 1.39%), nhỏ hơn nhiều so với khuyến mãi % (10–20%). Khi so sánh hiệu quả khuyến mãi, tách riêng hai loại.
