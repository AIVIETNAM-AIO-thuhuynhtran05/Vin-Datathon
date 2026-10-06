# Vin Datathon 2026 — E-commerce Dashboard & Analytics

> **Business Analytics Project | Power BI | SQL | Customer | Sales | Inventory | Logistics**

Phân tích hoạt động kinh doanh của một **fashion e-commerce platform** trong giai đoạn **2012–2022**, tập trung vào việc xác định các vấn đề về **business performance, customer retention, sales, inventory và logistics**, từ đó đưa ra các đề xuất nhằm hỗ trợ ra quyết định dựa trên dữ liệu.

---

## 📌 Project Overview

Dashboard được xây dựng trên **Power BI**, gồm 5 trang phân tích chính:

| Dashboard | Business Focus |
|---|---|
| **Overview** | Tổng quan tình hình kinh doanh |
| **Customer** | Customer behavior & retention |
| **Sales** | Sales performance & profitability |
| **Inventory** | Inventory efficiency |
| **Logistics** | Delivery & operational performance |

### Business Questions

Dự án tập trung trả lời các câu hỏi:

- Doanh nghiệp đang tăng trưởng hay suy giảm?
- Đâu là nguyên nhân chính khiến doanh thu và số đơn hàng giảm?
- Khách hàng có quay lại mua hàng không?
- Category và channel nào đang tạo ra giá trị cao nhất?
- Doanh nghiệp có đang gặp vấn đề về tồn kho?
- Những yếu tố nào đang ảnh hưởng đến return và delivery performance?
- Doanh nghiệp nên ưu tiên cải thiện khu vực nào trước?

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

---

# 🎯 Recommended Business Priorities

Dựa trên các findings, doanh nghiệp nên ưu tiên theo thứ tự:

### 1️⃣ Improve Customer Retention

Tăng repeat purchase và giảm customer churn.

**Key KPIs:**

- Repeat Purchase Rate
- Retention Rate
- Churn Rate
- Customer Lifetime Value
- Customer AOV

### 2️⃣ Improve Inventory Efficiency

Giảm lượng vốn bị khóa trong slow-moving inventory.

**Key KPIs:**

- Days of Supply
- Inventory Turnover
- Stockout Rate
- Overstock Rate
- Inventory Aging

### 3️⃣ Improve Promotion & Margin

Chuyển từ mass discount sang **targeted promotion**.

**Key KPIs:**

- AOV
- Gross Margin
- Discount Rate
- Revenue per Order
- Promotion ROI

### 4️⃣ Diversify Revenue Sources

Giảm sự phụ thuộc vào một category và tối ưu channel mix.

**Key KPIs:**

- Revenue by Category
- Profit by Category
- Revenue by Channel
- AOV by Channel
- Customer Acquisition Cost

### 5️⃣ Improve Logistics & Return Experience

Giảm delivery time và return do sizing.

**Key KPIs:**

- Average Delivery Time
- On-time Delivery Rate
- Return Rate
- Return Reason
- Cost per Shipment

---

# 🛠️ Tools & Technologies

- **Power BI** — Dashboard & Data Visualization
- **Python** — Data Querying & Transformation
- **Excel** — Data Exploration & Validation
- **DAX** — KPI Calculation & Business Metrics

---

