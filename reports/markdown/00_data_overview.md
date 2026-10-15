# Mô tả tổng quan dữ liệu

Bộ dữ liệu mô phỏng hoạt động của một doanh nghiệp thương mại điện tử thời trang tại Việt Nam, giai đoạn **04/07/2012 – 31/12/2022**. Gồm 13 tệp CSV trong `data/raw/`, chia thành 4 nhóm: **Master** (danh mục tham chiếu), **Transaction** (giao dịch), **Analytical** (tổng hợp) và **Operational** (vận hành).

> Số dòng/số cột được đếm trực tiếp từ `data/raw/`. Nếu dữ liệu nguồn thay đổi, chạy lại `python eda/data_quality_eda.py` và đối chiếu với `data/processed/eda/table_overview.csv`.

## 1. Tổng quan các bảng

| STT | Tên bảng | Số dòng | Số cột | Ý nghĩa |
|---:|---|---:|---:|---|
| | **Bảng Master (danh mục)** | | | |
| 1 | `customers` | 121.930 | 7 | Mỗi dòng là một khách hàng đã đăng ký tài khoản. Chứa mã bưu chính, thành phố, ngày đăng ký, giới tính, nhóm tuổi và kênh thu hút. Là thuộc tính **tĩnh**, dùng để mô tả và phân nhóm khách hàng. |
| 2 | `geography` | 39.948 | 4 | Mỗi dòng là một mã bưu chính (`zip`) và thành phố, vùng (East/Central/West), quận tương ứng. Dùng để gắn vị trí địa lý cho khách hàng và đơn hàng. |
| 3 | `products` | 2.412 | 8 | Mỗi dòng là một SKU (tên sản phẩm × size × màu). Chứa danh mục, phân khúc, giá niêm yết và giá vốn (COGS) **trên một đơn vị**. |
| 4 | `promotions` | 50 | 10 | Mỗi dòng là một chương trình khuyến mãi: loại (phần trăm/cố định), mức giảm, thời gian hiệu lực, danh mục áp dụng, kênh, khả năng cộng dồn và giá trị đơn tối thiểu. |
| | **Bảng Transaction (giao dịch)** | | | |
| 5 | `orders` | 646.945 | 8 | Mỗi dòng là một đơn hàng: ngày đặt, khách hàng, địa chỉ giao (`zip`), trạng thái, phương thức thanh toán, thiết bị và nguồn truy cập. Là bảng **trung tâm** để nối các bảng giao dịch khác. |
| 6 | `order_items` | 714.669 | 7 | Mỗi dòng là một sản phẩm trong một đơn: số lượng, đơn giá bán thực tế, số tiền giảm giá và tối đa 2 mã khuyến mãi. Đây là chỉ tiêu **phát sinh**, được cộng dồn để ra doanh thu. |
| 7 | `payments` | 646.945 | 4 | Mỗi dòng là khoản thanh toán của một đơn (quan hệ 1–1 với `orders`): phương thức, số tiền thanh toán, số kỳ trả góp. `payment_value` = Σ(số lượng × đơn giá − giảm giá) của đơn, **chưa gồm phí vận chuyển**. |
| 8 | `shipments` | 566.067 | 4 | Mỗi dòng là thông tin vận chuyển của một đơn đã gửi: ngày gửi, ngày giao, phí vận chuyển. Chỉ tồn tại với đơn ở trạng thái `shipped`/`delivered`/`returned`. |
| 9 | `returns` | 39.939 | 7 | Mỗi dòng là một lần trả hàng của một sản phẩm trong đơn: ngày trả, lý do, số lượng trả và số tiền hoàn. |
| 10 | `reviews` | 113.551 | 7 | Mỗi dòng là một đánh giá của khách hàng cho một sản phẩm trong đơn đã giao: ngày đánh giá, điểm (1–5), tiêu đề. |
| | **Bảng Analytical (tổng hợp)** | | | |
| 11 | `sales` | 3.833 | 3 | Mỗi dòng là doanh thu và giá vốn của **một ngày** (04/07/2012 – 31/12/2022, liên tục). Đây là chỉ tiêu **phát sinh**, cộng dồn được theo tháng/năm; là biến mục tiêu của bài toán dự báo. `Revenue` = Σ(số lượng × đơn giá) của mọi đơn trong ngày, **trước giảm giá**. |
| | **Bảng Operational (vận hành)** | | | |
| 12 | `inventory` | 60.247 | 17 | Mỗi dòng là tồn kho của một sản phẩm tại **ngày chốt cuối tháng** (07/2012 – 12/2022). Chứa tồn cuối kỳ, nhập/bán trong tháng, số ngày hết hàng, số ngày cung ứng, tỷ lệ đáp ứng, các cờ hết hàng/tồn dư/đặt lại. `stock_on_hand` là chỉ tiêu **số dư**, không cộng dồn qua các tháng; `units_received`/`units_sold` là **phát sinh** trong tháng. |
| 13 | `web_traffic` | 3.652 | 7 | Mỗi dòng là lưu lượng truy cập website của **một ngày** (01/01/2013 – 31/12/2022): phiên, người dùng duy nhất, lượt xem trang, tỷ lệ thoát, thời lượng phiên trung bình và nguồn truy cập chính. |

## 2. Mô tả chi tiết từng bảng

Ký hiệu: **PK** = khóa chính, **FK** = khóa ngoại.

### 2.1. `customers` — khách hàng

- **Grain:** 1 dòng / khách hàng. **PK:** `customer_id`. **FK:** `zip` → `geography.zip`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `customer_id` | int | Mã khách hàng |
| `zip` | int | Mã bưu chính nơi ở |
| `city` | text | Thành phố (phải khớp `geography.city` theo `zip`) |
| `signup_date` | date | Ngày đăng ký tài khoản |
| `gender` | text | Female / Male / Non-binary |
| `age_group` | text | 18-24 / 25-34 / 35-44 / 45-54 / 55+ |
| `acquisition_channel` | text | Kênh thu hút: organic_search, paid_search, social_media, email_campaign, referral, direct |

### 2.2. `geography` — địa lý

- **Grain:** 1 dòng / mã bưu chính. **PK:** `zip`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `zip` | int | Mã bưu chính |
| `city` | text | Thành phố |
| `region` | text | Vùng: East / Central / West |
| `district` | text | Quận/huyện |

### 2.3. `products` — sản phẩm

- **Grain:** 1 dòng / SKU. **PK:** `product_id`. Khóa nghiệp vụ: (`product_name`, `size`, `color`).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `product_id` | int | Mã SKU |
| `product_name` | text | Tên dòng sản phẩm |
| `category` | text | Danh mục: Streetwear, Outdoor, Casual, GenZ |
| `segment` | text | Phân khúc trong danh mục (Everyday, Activewear, Premium, …) |
| `size` | text | S / M / L / XL |
| `color` | text | Màu sắc |
| `price` | float | Giá niêm yết / đơn vị |
| `cogs` | float | Giá vốn / đơn vị (phải < `price`) |

### 2.4. `promotions` — khuyến mãi

- **Grain:** 1 dòng / chương trình. **PK:** `promo_id`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `promo_id` | text | Mã khuyến mãi (PROMO-xxxx) |
| `promo_name` | text | Tên chương trình |
| `promo_type` | text | `percentage` (giảm %) hoặc `fixed` (giảm số tiền cố định) |
| `discount_value` | float | Mức giảm: % nếu `percentage`, số tiền nếu `fixed` |
| `start_date`, `end_date` | date | Thời gian hiệu lực (`start_date` ≤ `end_date`) |
| `applicable_category` | text | Danh mục áp dụng; **trống = áp dụng mọi danh mục** |
| `promo_channel` | text | Kênh triển khai |
| `stackable_flag` | 0/1 | Được cộng dồn với khuyến mãi khác hay không |
| `min_order_value` | float | Giá trị đơn tối thiểu để áp dụng |

### 2.5. `orders` — đơn hàng

- **Grain:** 1 dòng / đơn. **PK:** `order_id`. **FK:** `customer_id` → `customers`, `zip` → `geography`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `order_id` | int | Mã đơn |
| `order_date` | date | Ngày đặt |
| `customer_id` | int | Khách đặt |
| `zip` | int | Mã bưu chính giao hàng |
| `order_status` | text | created → paid → shipped → delivered / returned; hoặc cancelled |
| `payment_method` | text | credit_card, paypal, cod, apple_pay, bank_transfer |
| `device_type` | text | mobile / desktop / tablet |
| `order_source` | text | Nguồn truy cập dẫn đến đơn |

### 2.6. `order_items` — chi tiết đơn

- **Grain:** 1 dòng / sản phẩm trong đơn. Khóa logic: (`order_id`, `product_id`). **FK:** `order_id` → `orders`, `product_id` → `products`, `promo_id`/`promo_id_2` → `promotions`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `order_id`, `product_id` | int | Đơn và sản phẩm |
| `quantity` | int | Số lượng mua (> 0) |
| `unit_price` | float | Đơn giá bán thực tế (có thể khác giá niêm yết) |
| `discount_amount` | float | Tổng tiền giảm cho dòng (0 ≤ giảm ≤ số lượng × đơn giá) |
| `promo_id` | text | Mã khuyến mãi thứ nhất; **trống = dòng không có khuyến mãi** |
| `promo_id_2` | text | Mã khuyến mãi cộng dồn thứ hai; chỉ có khi đã có `promo_id` |

### 2.7. `payments` — thanh toán

- **Grain:** 1 dòng / đơn. **PK + FK:** `order_id` → `orders`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `order_id` | int | Mã đơn |
| `payment_method` | text | Phải trùng `orders.payment_method` |
| `payment_value` | float | Số tiền thanh toán = Σ(`quantity` × `unit_price` − `discount_amount`) |
| `installments` | int | Số kỳ trả góp 1–12 (COD luôn = 1) |

### 2.8. `shipments` — vận chuyển

- **Grain:** 1 dòng / đơn đã gửi. **PK + FK:** `order_id` → `orders`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `order_id` | int | Mã đơn |
| `ship_date` | date | Ngày gửi (≥ `order_date`) |
| `delivery_date` | date | Ngày giao (≥ `ship_date`) |
| `shipping_fee` | float | Phí vận chuyển (≥ 0) |

### 2.9. `returns` — trả hàng

- **Grain:** 1 dòng / lần trả một sản phẩm. **PK:** `return_id`. **FK:** (`order_id`, `product_id`) → `order_items`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `return_id` | text | Mã phiếu trả (RET-xxxxxx) |
| `order_id`, `product_id` | int | Dòng sản phẩm bị trả |
| `return_date` | date | Ngày trả (≥ ngày giao) |
| `return_reason` | text | wrong_size, defective, not_as_described, changed_mind, late_delivery |
| `return_quantity` | int | Số lượng trả (0 < trả ≤ số lượng mua) |
| `refund_amount` | float | Số tiền hoàn (tổng hoàn theo đơn ≤ tiền thanh toán của đơn) |

### 2.10. `reviews` — đánh giá

- **Grain:** 1 dòng / đánh giá. **PK:** `review_id`. **FK:** (`order_id`, `product_id`) → `order_items`, `customer_id` → `customers`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `review_id` | text | Mã đánh giá |
| `order_id`, `product_id`, `customer_id` | int | Đơn, sản phẩm, khách đánh giá (khách phải là người đặt đơn) |
| `review_date` | date | Ngày đánh giá (≥ ngày giao) |
| `rating` | int | Điểm 1–5 |
| `review_title` | text | Tiêu đề đánh giá |

### 2.11. `sales` — doanh thu theo ngày

- **Grain:** 1 dòng / ngày. **PK:** `Date`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `Date` | date | Ngày |
| `Revenue` | float | Doanh thu ngày (Σ số lượng × đơn giá, trước giảm giá, mọi trạng thái đơn) |
| `COGS` | float | Giá vốn hàng bán trong ngày |

### 2.12. `inventory` — tồn kho cuối tháng

- **Grain:** 1 dòng / sản phẩm / tháng. Khóa: (`product_id`, `snapshot_date`). **FK:** `product_id` → `products`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `snapshot_date` | date | Ngày chốt (ngày cuối tháng) |
| `product_id` | int | Mã SKU |
| `stock_on_hand` | int | Tồn cuối kỳ (**số dư**) |
| `units_received`, `units_sold` | int | Nhập / bán trong tháng (**phát sinh**) |
| `stockout_days` | int | Số ngày hết hàng trong tháng (≤ số ngày của tháng) |
| `days_of_supply` | float | Số ngày đủ hàng ≈ `stock_on_hand` / `units_sold` × 30 |
| `fill_rate` | float | Tỷ lệ đáp ứng đơn (0–1) |
| `stockout_flag`, `overstock_flag`, `reorder_flag` | 0/1 | Cờ hết hàng (= `stockout_days` > 0), tồn dư, cần đặt lại |
| `sell_through_rate` | float | `units_sold` / (`units_sold` + `stock_on_hand`) |
| `product_name`, `category`, `segment` | text | Thuộc tính sản phẩm (sao chép từ `products`) |
| `year`, `month` | int | Năm, tháng của `snapshot_date` |

### 2.13. `web_traffic` — lưu lượng website

- **Grain:** 1 dòng / ngày. **PK:** `date`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `date` | date | Ngày |
| `sessions` | int | Số phiên truy cập |
| `unique_visitors` | int | Số người dùng duy nhất (≤ `sessions`) |
| `page_views` | int | Lượt xem trang (≥ `sessions`) |
| `bounce_rate` | float | Tỷ lệ thoát (0–1) |
| `avg_session_duration_sec` | float | Thời lượng phiên trung bình (giây) |
| `traffic_source` | text | Nguồn truy cập chính của ngày |

## 3. Quan hệ giữa các bảng

```text
geography (zip) ──< customers (customer_id) ──< orders (order_id) ──┬── payments   (1–1)
        └───────────────────────────────────────< orders.zip        ├── shipments  (1–0..1)
                                                                    └──< order_items (order_id, product_id) >── products (product_id)
                                                                              ├──< returns                         ├──< inventory
                                                                              ├──< reviews                         
                                                                              └── promo_id / promo_id_2 >── promotions
sales (Date)  ≈ Σ order_items theo orders.order_date
web_traffic (date) — chỉ nối theo ngày
```

## 4. Lưu ý khi sử dụng

- **Số dư vs phát sinh:** `inventory.stock_on_hand` là số dư tại ngày chốt — lấy giá trị cuối kỳ, **không cộng** qua các tháng. `sales`, `order_items`, `payments`, `inventory.units_sold/units_received` là phát sinh — cộng dồn được theo kỳ.
- **Grain khác nhau:** nối `orders` với `order_items` làm nhân bản dòng đơn; cần tổng hợp `order_items`/`returns` về cấp đơn trước khi nối với `payments`, `shipments`.
- **Doanh thu:** `sales.Revenue` là doanh thu **trước giảm giá, gồm cả đơn hủy**; `payments.payment_value` là số tiền **sau giảm giá**. Không dùng lẫn hai định nghĩa.
- **Giá trị trống có ý nghĩa:** `order_items.promo_id`/`promo_id_2` trống = không khuyến mãi; `promotions.applicable_category` trống = mọi danh mục. Đây không phải dữ liệu thiếu.
- Chi tiết chất lượng dữ liệu (missing, trùng lặp, vi phạm ràng buộc, outlier) xem tại [`data_quality_and_eda.md`](data_quality_and_eda.md).
