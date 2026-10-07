# Vin Datathon 2026 — E-commerce Dashboard & Analytics

> **Business Analytics Project | Power BI | SQL | Customer | Sales | Inventory | Logistics**

Phân tích hoạt động kinh doanh của một **fashion e-commerce platform** trong giai đoạn **2012–2022**, tập trung vào việc xác định các vấn đề về **business performance, customer retention, sales, inventory và logistics**, từ đó đưa ra các đề xuất nhằm hỗ trợ ra quyết định dựa trên dữ liệu.

---

## 📌 Project Overview

The dashboard is built in **Power BI** and consists of 5 main analysis pages:

| Dashboard | Business Focus |
|---|---|
| **Overview** | Overall business performance |
| **Customer** | Customer behavior & retention |
| **Sales** | Sales performance & profitability |
| **Inventory** | Inventory efficiency |
| **Logistics** | Delivery & operational performance |

### Business Questions

The project focuses on answering the following questions:

- Is the business growing or declining?
- What are the main drivers behind the decline in revenue and orders?
- Do customers come back to make repeat purchases?
- Which categories and channels generate the most value?
- Is the business facing inventory issues?
- What factors are affecting returns and delivery performance?
- Which areas should the business prioritize improving first?

---

# 🔍 Key Business Insights

## 1. Overview — Business Performance

### 🔎 Key Findings

- Doanh nghiệp đạt đỉnh về các KPI chính vào khoảng **2016**, sau đó doanh thu, số đơn hàng và số khách hàng có xu hướng suy giảm liên tục đến **2022**.
- **Revenue CAGR khoảng -3.8%/năm**, cho thấy doanh nghiệp đang trong xu hướng thu hẹp thay vì tăng trưởng.
- Profit margin giảm từ khoảng **22% xuống 14%**, phản ánh hiệu quả kinh doanh ngày càng suy yếu.
- Traffic tiếp tục tăng nhưng **conversion rate chỉ khoảng 0.13%**, cho thấy vấn đề không chỉ nằm ở khả năng thu hút traffic mà còn ở khả năng chuyển đổi người dùng thành khách hàng.

### 💡 Business Implications

Doanh nghiệp đang gặp vấn đề về **conversion và customer retention**, thay vì chỉ thiếu traffic.

Đặc biệt, cơ cấu acquisition đang phụ thuộc nhiều vào **organic search và paid channels**, trong khi các kênh có khả năng hỗ trợ retention như **email và referral** chưa được khai thác tương xứng.

<img width="1488" height="766" alt="Overview Dashboard" src="https://github.com/user-attachments/assets/1814c8ac-752b-4912-a6d2-f212edd2646e" />

---

# 2. Customer Analytics — Customer Behavior & Retention

### 🔎 Key Findings

- **62.64% registered users chưa phát sinh giao dịch**, cho thấy một lượng lớn người dùng rời khỏi funnel trước khi trở thành khách hàng.
- **Số khách hàng đăng ký tiếp tục tăng nhưng số lượt mua lại giảm**, khiến khoảng cách giữa user đăng ký và khách mua hàng ngày càng lớn. Tỉ lệ chuyển đổi khách hàng thấp là điểm nghẽn chính của funnel.
- Gần **48% customer base thuộc nhóm Never Purchased hoặc Lost**.
- Retention giảm mạnh ngay từ **tháng thứ +1**, cho thấy doanh nghiệp chưa có cơ chế đủ mạnh để kích thích repeat purchase.
- Customer Recency cao ở một bộ phận lớn khách hàng, phản ánh nguy cơ churn.

### 💡 Recommendations

**1. Improve First Purchase Conversion**

- Tặng **15% discount + Free Shipping** cho đơn hàng đầu tiên.
- Thiết kế onboarding flow cho người dùng mới.
- Trigger email/voucher sau **24 giờ** nếu user đăng ký nhưng chưa mua.

**2. Improve Customer Retention**

- Gửi personalized offers sau **30 ngày không mua hàng**.
- Xây dựng customer segmentation dựa trên **RFM**.
- Triển khai **VIP Tier Program** cho nhóm khách hàng có giá trị cao.

**3. Focus on High-value Customers**

Ưu tiên các nhóm khách hàng có:

- High Monetary Value
- High Purchase Frequency
- Low Recency

<img width="1343" height="691" alt="Customer Dashboard" src="https://github.com/user-attachments/assets/c615d1ff-c9a5-4518-bb22-6f4bb8f19bfc" />

---

# 3. Sales Performance — Revenue & Profitability

### 🔎 Key Findings

- Revenue đạt khoảng **15.7 tỷ VNĐ** trong toàn bộ dataset.
- Streetwear là category đóng góp lớn nhất và chiếm khoảng **80% lợi nhuận**, tạo ra rủi ro phụ thuộc vào một category.
- **Promotion xuất hiện trên khoảng 38% đơn hàng**, tuy nhiên AOV có xu hướng giảm ở nhiều category khi sử dụng promotion.
- Nhóm khách hàng **25–44 tuổi** là một trong những nhóm khách hàng quan trọng cần ưu tiên.

### 💡 Recommendations

**1. Improve Promotion Efficiency**

Thay vì sử dụng discount đại trà:

- Thiết lập minimum order value.
- Sử dụng combo pricing.
- Áp dụng personalized promotions.
- Kiểm soát discount floor để bảo vệ margin.

**2. Increase Customer Value**

Tập trung:

- Cross-selling
- Upselling
- Product bundling

đối với nhóm khách hàng có purchase frequency và AOV cao.

**3. Reduce Category Concentration Risk**

- Tiếp tục khai thác Streetwear nhưng không phụ thuộc quá mức.
- Mở rộng **Outdoor** nếu category này có growth potential.
- Đánh giá lại hiệu suất của **Casual** và điều chỉnh assortment/pricing.

<img width="1318" height="701" alt="Sales Dashboard" src="https://github.com/user-attachments/assets/e6deef96-0416-4d7e-981d-82c9bf4a287c" />

---

# 4. Inventory — Inventory Efficiency

### 🔎 Key Findings

Doanh nghiệp đang gặp tình trạng **supply-demand imbalance**:

- **Days of Supply (DOS) lên tới ~826 ngày**.
- Inventory replenishment cao hơn nhu cầu thực tế.
- Inventory-to-sales ratio duy trì khoảng **1.15–1.18**.
- Điều này làm tăng nguy cơ:
  - Capital being tied up
  - Overstock
  - Inventory aging
  - Markdown pressure

### 💡 Recommendations

#### Short-term — Liquidate Excess Inventory

- Flash Sale
- Markdown
- Clearance Campaign

Mục tiêu: nhanh chóng thu hồi một phần vốn bị tồn đọng.

#### Medium-term — Bundle

Kết hợp:

> Slow-moving products + Best-selling products

để tăng khả năng tiêu thụ hàng tồn mà không cần giảm giá quá sâu.

#### Long-term — B2B / Wholesale

Đối với các sản phẩm có inventory aging cao:

- Wholesale
- B2B liquidation
- Outlet channels

có thể được sử dụng để giải phóng inventory nhanh hơn.

<img width="1309" height="693" alt="Inventory Dashboard" src="https://github.com/user-attachments/assets/b3052d26-983c-4ef8-803c-92696d654000" />

---

# 5. Logistics — Operational Efficiency

### 🔎 Key Findings

- Average delivery time khoảng **6 ngày**, cho thấy còn dư địa để cải thiện delivery experience.
- **Wrong Size** là một trong những nguyên nhân return nổi bật nhất.
- Return do sizing không chỉ ảnh hưởng đến customer experience mà còn làm tăng:
  - Reverse logistics cost
  - Inventory handling cost
  - Delivery workload

### 💡 Recommendations

**1. Improve Size Selection**

- Thiết kế Size Guide trực quan hơn.
- Bổ sung chiều cao/cân nặng của model.
- Cung cấp thông tin fit: Slim / Regular / Oversized.
- Nếu có đủ data, xây dựng size recommendation dựa trên customer profile.

**2. Improve Delivery Performance**

- Áp dụng **Multi-carrier Strategy**.
- So sánh carrier theo:
  - Delivery Time
  - On-time Delivery Rate
  - Return Rate
  - Cost per Order

<img width="1370" height="747" alt="Logistics Dashboard" src="https://github.com/user-attachments/assets/0ce22572-ecab-4f8d-9b54-e3e0dfa6bb45" />

---

# 📊 Key Business Findings

| # | Finding | Business Implication |
|---|---|---|
| 01 | Revenue CAGR ≈ **-3.8%** | Business has entered a declining growth phase |
| 02 | Margin declined from **~22% → ~14%** | Profitability is deteriorating |
| 03 | **~48% customers** are Never Purchased or Lost | Customer retention is a major issue |
| 04 | Retention drops significantly from **Month +1** | Weak post-purchase engagement |
| 05 | Promotion applied to **~38% orders** | Discount strategy may be hurting AOV |
| 06 | Streetwear contributes **~80% of profit** | High category concentration risk |
| 07 | DOS reaches **~826 days** | Severe overstock / capital inefficiency |
| 08 | Wrong Size is a major return reason | Opportunity to improve product information |
| 09 | Organic Search & Social Media have high volume but lower AOV | Acquisition efficiency should be optimized |
| 10 | Email has higher AOV but lower volume | Potential opportunity for targeted CRM investment |
| 11 | Registrations keep rising while purchases decline | Low customer conversion: new users are not turning into buyers |

---

# 🎯 Recommended Business Priorities

Các priority được sắp xếp theo **mức độ ảnh hưởng đến doanh thu/lợi nhuận** và **tốc độ có thể triển khai**. Mỗi priority gồm: vấn đề (dựa trên findings), hành động cụ thể, bộ phận phụ trách, timeline và KPI đo lường.

> **Lưu ý:** Target là **đề xuất** dựa trên baseline trong dataset, cần được kiểm chứng bằng A/B test hoặc theo dõi theo tháng trước khi áp dụng chính thức. KPI ghi *"Đo từ dashboard"* là chỉ số chưa có baseline cụ thể, cần thiết lập trước khi triển khai.

### 🗺️ Roadmap Summary

| Priority | Vấn đề chính | Hành động trọng tâm | North-star KPI | Target đề xuất |
|---|---|---|---|---|
| 1️⃣ Conversion & Retention | Đăng ký tăng nhưng lượt mua giảm · 62.64% user chưa mua · ~48% Never Purchased/Lost | Funnel fix + welcome flow + win-back theo RFM | % khách Never Purchased/Lost | **48% → 40%** trong 12 tháng |
| 2️⃣ Inventory Efficiency | DOS ~826 ngày · Inventory/Sales 1.15–1.18 | Dừng nhập SKU tồn lâu + thanh lý theo độ tuổi tồn kho | Days of Supply | **826 → < 365 ngày** trong 12 tháng |
| 3️⃣ Promotion & Margin | Promotion trên ~38% đơn · Margin 22% → 14% | Targeted promotion + discount floor | Gross Margin | **14% → 18%** trong 12 tháng |
| 4️⃣ Revenue Diversification | Streetwear ~80% lợi nhuận | Mở rộng Outdoor + tăng kênh Email | % lợi nhuận từ Streetwear | **80% → ≤ 70%** trong 12 tháng |
| 5️⃣ Logistics & Returns | Delivery ~6 ngày · Wrong Size là lý do return nổi bật | Chuẩn hóa size guide + carrier scorecard | Average Delivery Time | **6 → 4 ngày** trong 6 tháng |

---

### 1️⃣ Improve Customer Conversion & Retention

**Vì sao ưu tiên số 1:** Số khách hàng **đăng ký tăng nhưng lượt mua giảm**, tức là doanh nghiệp vẫn thu hút được người dùng mới nhưng không biến họ thành người mua. Traffic tăng nhưng conversion chỉ **~0.13%**, **62.64%** registered users chưa từng mua và retention rơi mạnh từ **tháng +1**. Doanh nghiệp đang mất khách ở cả hai đầu funnel: không chuyển đổi được user mới và không giữ được khách đã mua.

| # | Hành động | Chi tiết triển khai | Owner | Timeline |
|---|---|---|---|---|
| 1.1 | **Tìm điểm rơi trong funnel** | Phân tích funnel **Đăng ký → Xem sản phẩm → Thêm giỏ → Checkout → Thanh toán** theo cohort tháng đăng ký để xác định bước mất nhiều user nhất, và ưu tiên sửa bước đó trước. | Data / E-commerce | Tháng 1 |
| 1.2 | **Nhắc giỏ hàng bỏ dở** | Gửi email/push sau **1h** và **24h** cho user đã thêm giỏ nhưng chưa thanh toán, kèm ảnh sản phẩm và thông tin freeship. | CRM | Tháng 1 |
| 1.3 | **Welcome flow cho user mới** | Email/push sau **24h** nếu đăng ký nhưng chưa mua: voucher **15% + Free Shipping**, hết hạn sau 7 ngày. Nhắc lại lần 2 sau 72h. | CRM / Marketing | Tháng 1 |
| 1.4 | **Post-purchase journey** | Email ngày **+7** (gợi ý phối đồ, sản phẩm liên quan) và ngày **+21** (voucher cho đơn thứ 2) để kéo khách qua mốc tháng +1. | CRM | Tháng 1–2 |
| 1.5 | **Win-back theo mốc recency** | Kích hoạt tự động ở **30 / 60 / 90 ngày** không mua, ưu đãi tăng dần theo mốc. Sau 90 ngày không phản hồi thì chuyển sang nhóm Lost và giảm tần suất gửi. | CRM | Tháng 2–3 |
| 1.6 | **RFM segmentation hàng tháng** | Cập nhật RFM mỗi tháng trên Power BI, gắn mỗi segment với một campaign riêng (Champions → early access, At Risk → win-back, Hibernating → reactivation). | Data / CRM | Tháng 2 |
| 1.7 | **VIP Tier Program** | Áp dụng cho **top 10% khách theo Monetary**: free shipping không giới hạn, early access sale, quà sinh nhật. | Marketing | Tháng 4–6 |

| KPI | Baseline | Target đề xuất |
|---|---|---|
| Registered users chưa mua | 62.64% | **≤ 55%** sau 6 tháng |
| Tỉ lệ user mua đơn đầu tiên trong 30 ngày sau đăng ký | Đo từ dashboard | Tăng đều qua từng cohort tháng |
| Tăng trưởng lượt mua so với tăng trưởng đăng ký | Đăng ký tăng, lượt mua giảm | Lượt mua tăng cùng chiều với đăng ký |
| Never Purchased + Lost | ~48% | **≤ 40%** sau 12 tháng |
| Conversion Rate | ~0.13% | **≥ 0.18%** sau 6 tháng |
| Month +1 Retention | Đo từ dashboard | **+5 điểm %** so với baseline |
| Repeat Purchase Rate / CLV | Đo từ dashboard | Tăng theo quý |

---

### 2️⃣ Improve Inventory Efficiency

**Vì sao ưu tiên số 2:** DOS **~826 ngày** nghĩa là lượng hàng tồn đủ bán hơn 2 năm, trong khi inventory-to-sales duy trì **1.15–1.18**. Vốn đang bị khóa trong hàng tồn và áp lực markdown sẽ ngày càng lớn.

| # | Hành động | Chi tiết triển khai | Owner | Timeline |
|---|---|---|---|---|
| 2.1 | **Phân loại SKU theo độ tuổi tồn kho** | Chia SKU thành 4 nhóm: **< 90 ngày / 90–180 / 180–365 / > 365 ngày**, kết hợp ABC theo doanh thu. Đây là đầu vào cho mọi hành động phía sau. | Data / Merchandising | Tháng 1 |
| 2.2 | **Dừng nhập hàng SKU tồn lâu** | Tạm dừng replenishment cho SKU có **DOS > 365 ngày**. Đặt reorder point dựa trên forecast nhu cầu **90 ngày** thay vì nhập theo thói quen. | Supply Chain | Tháng 1–2 |
| 2.3 | **Thanh lý theo từng nhóm tuổi tồn** | Tồn 180–365 ngày: **flash sale / markdown 20–30%**. Tồn > 365 ngày: **clearance campaign**. | Merchandising / Marketing | Tháng 2–4 |
| 2.4 | **Bundle hàng chậm bán + best-seller** | Ghép 1 slow-moving SKU với 1 best-seller cùng category, giảm giá trên tổng bundle thay vì từng món để bảo vệ giá best-seller. | Merchandising | Tháng 3–6 |
| 2.5 | **Kênh B2B / Outlet** | Phần tồn > 365 ngày còn lại sau clearance: chuyển cho wholesale, B2B liquidation hoặc outlet. | Sales / Ops | Tháng 6–12 |

| KPI | Baseline | Target đề xuất |
|---|---|---|
| Days of Supply | ~826 ngày | **< 500 ngày** sau 6 tháng · **< 365 ngày** sau 12 tháng |
| Inventory-to-Sales Ratio | 1.15–1.18 | **≤ 1.0** |
| % SKU tồn > 365 ngày | Đo từ dashboard | Giảm **50%** sau 12 tháng |
| Stockout Rate (best-sellers) | Đo từ dashboard | Không tăng khi cắt giảm nhập hàng |

---

### 3️⃣ Improve Promotion & Margin

**Vì sao ưu tiên số 3:** Promotion xuất hiện trên **~38% đơn hàng** nhưng AOV giảm ở nhiều category khi có promotion, trong khi margin đã giảm từ **~22% xuống ~14%**. Discount đại trà đang làm giảm lợi nhuận mà không tăng giá trị đơn.

| # | Hành động | Chi tiết triển khai | Owner | Timeline |
|---|---|---|---|---|
| 3.1 | **Minimum order value** | Chỉ áp dụng voucher cho đơn **≥ AOV hiện tại + 15–20%** để promotion kéo AOV lên thay vì kéo xuống. | Marketing | Tháng 1 |
| 3.2 | **Discount floor theo category** | Đặt mức giảm tối đa sao cho margin sau giảm vẫn **≥ 10%**; promotion vượt ngưỡng phải được duyệt riêng. | Finance / Merchandising | Tháng 1–2 |
| 3.3 | **Targeted thay vì mass discount** | Chỉ gửi ưu đãi sâu cho segment cần kích hoạt (At Risk, New), không áp dụng cho Champions vốn đã mua đều. | CRM | Tháng 2–3 |
| 3.4 | **Combo pricing & cross-sell** | Combo theo outfit (áo + quần + phụ kiện) cho nhóm có frequency và AOV cao, đặc biệt nhóm **25–44 tuổi**. | Merchandising | Tháng 3–6 |
| 3.5 | **Đo Promotion ROI bằng holdout** | Giữ **10% khách không nhận promotion** làm control group để đo doanh thu tăng thêm thực sự của từng campaign. | Data | Liên tục |

| KPI | Baseline | Target đề xuất |
|---|---|---|
| % đơn hàng có promotion | ~38% | **≤ 25%** sau 6 tháng |
| Gross Margin | ~14% | **≥ 18%** sau 12 tháng |
| AOV đơn có promotion vs không có | Đo từ dashboard | Thu hẹp chênh lệch |
| Promotion ROI | Chưa đo | Mọi campaign có ROI dương so với holdout |

---

### 4️⃣ Diversify Revenue Sources

**Vì sao ưu tiên số 4:** Streetwear tạo ra **~80% lợi nhuận**, nên chỉ cần category này chững lại là toàn bộ lợi nhuận bị ảnh hưởng. Ở góc độ channel, Organic Search & Social Media mang volume lớn nhưng AOV thấp, còn **Email có AOV cao nhưng volume thấp**.

| # | Hành động | Chi tiết triển khai | Owner | Timeline |
|---|---|---|---|---|
| 4.1 | **Mở rộng Outdoor** | Tăng assortment và ngân sách quảng cáo cho Outdoor nếu growth rate theo quý dương; test trước với 10–20 SKU mới. | Merchandising | Tháng 2–6 |
| 4.2 | **Tái cấu trúc Casual** | Rà soát SKU Casual có margin thấp nhất, cắt giảm SKU kém hiệu quả và điều chỉnh giá. | Merchandising | Tháng 3–4 |
| 4.3 | **Cross-sell từ Streetwear** | Dùng lượng khách lớn của Streetwear để giới thiệu Outdoor/Casual qua gợi ý "complete the look" trên trang sản phẩm và email. | Marketing / E-commerce | Tháng 2–4 |
| 4.4 | **Tăng quy mô kênh Email** | Thu thập email tại checkout và trên website (popup ưu đãi), chuyển một phần ngân sách paid sang CRM/Email và Referral. | Marketing | Tháng 1–6 |
| 4.5 | **Theo dõi CAC & AOV theo channel** | Báo cáo tháng về CAC, AOV và repeat rate của từng kênh để phân bổ lại ngân sách theo hiệu quả. | Data / Marketing | Tháng 1 |

| KPI | Baseline | Target đề xuất |
|---|---|---|
| % lợi nhuận từ Streetwear | ~80% | **≤ 70%** sau 12 tháng |
| Revenue growth của Outdoor | Đo từ dashboard | Tăng trưởng dương theo quý |
| % revenue từ Email | Đo từ dashboard | **Gấp đôi** sau 12 tháng |
| CAC theo channel | Đo từ dashboard | Giảm CAC blended |

---

### 5️⃣ Improve Logistics & Return Experience

**Vì sao ưu tiên số 5:** Delivery time trung bình **~6 ngày** và **Wrong Size** là lý do return nổi bật. Mỗi đơn return vì size làm tăng chi phí reverse logistics, chi phí xử lý tồn kho và giảm khả năng khách quay lại.

| # | Hành động | Chi tiết triển khai | Owner | Timeline |
|---|---|---|---|---|
| 5.1 | **Ưu tiên SKU có tỉ lệ Wrong Size cao** | Lấy danh sách **top 20 SKU** có return do Wrong Size cao nhất, đo lại size chart thực tế của các SKU này trước. | Data / Product | Tháng 1 |
| 5.2 | **Size guide chi tiết** | Bảng số đo theo **cm**, chiều cao/cân nặng của model, nhãn fit **Slim / Regular / Oversized** trên mọi trang sản phẩm. | E-commerce / Product | Tháng 1–3 |
| 5.3 | **Size recommendation** | Gợi ý size dựa trên lịch sử mua và return của khách (khi đủ dữ liệu). | Data | Tháng 6–12 |
| 5.4 | **Carrier scorecard** | So sánh carrier hàng tháng theo **delivery time, on-time rate, return rate, cost per order**; chuyển volume sang carrier tốt nhất theo từng khu vực. | Ops / Logistics | Tháng 2–3 |
| 5.5 | **Multi-carrier theo khu vực** | Ký với ít nhất 2 carrier cho mỗi khu vực lớn để có phương án dự phòng và tạo áp lực cạnh tranh về SLA. | Ops | Tháng 3–6 |

| KPI | Baseline | Target đề xuất |
|---|---|---|
| Average Delivery Time | ~6 ngày | **≤ 4 ngày** sau 6 tháng |
| Return do Wrong Size | Đo từ dashboard | Giảm **20–30%** sau 6 tháng |
| On-time Delivery Rate | Đo từ dashboard | **≥ 95%** |
| Cost per Shipment | Đo từ dashboard | Không tăng khi giảm delivery time |

---

# 🛠️ Tools & Technologies

- **Power BI** — Dashboard & Data Visualization
- **Python** — Data Querying & Transformation
- **Excel** — Data Exploration & Validation
- **DAX** — KPI Calculation & Business Metrics

---

