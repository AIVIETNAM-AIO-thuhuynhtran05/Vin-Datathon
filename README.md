# Vin Datathon 2026 — E-commerce Dashboard & Analytics

> **Business Analytics Project | Power BI | SQL | Customer | Sales | Inventory | Logistics**

An analysis of a **fashion e-commerce platform** over **2012–2022**, focused on identifying issues in **business performance, customer retention, sales, inventory, and logistics**, and turning them into recommendations that support data-driven decision-making.

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

- The business peaked on its main KPIs around **2016**; revenue, orders, and customer count then declined steadily through **2022**.
- **Revenue CAGR is about -3.8% per year**, showing the business is contracting rather than growing.
- Profit margin fell from about **22% to 14%**, reflecting weakening business efficiency.
- Traffic keeps growing, but the **conversion rate is only about 0.13%**, so the problem is not just attracting traffic but converting visitors into customers.

### 💡 Business Implications

The business is facing a **conversion and customer retention** problem, not simply a lack of traffic.

In particular, acquisition relies heavily on **organic search and paid channels**, while retention-friendly channels such as **email and referral** remain underused.

<img width="1488" height="766" alt="Overview Dashboard" src="https://github.com/user-attachments/assets/1814c8ac-752b-4912-a6d2-f212edd2646e" />

---

# 2. Customer Analytics — Customer Behavior & Retention

### 🔎 Key Findings

- **62.64% of registered users have never made a purchase**, meaning a large share of users drop out of the funnel before becoming customers.
- **Registrations keep rising while purchases decline**, widening the gap between registered users and paying customers. Low customer conversion is the main bottleneck in the funnel.
- Nearly **48% of the customer base is Never Purchased or Lost**.
- Retention drops sharply from **Month +1**, showing the business lacks strong mechanisms to drive repeat purchases.
- A large share of customers has high Recency, signaling churn risk.

### 💡 Recommendations

**1. Improve First Purchase Conversion**

- Offer **15% discount + Free Shipping** on the first order.
- Design an onboarding flow for new users.
- Trigger an email/voucher **24 hours** after sign-up if the user has not purchased.

**2. Improve Customer Retention**

- Send personalized offers after **30 days without a purchase**.
- Build customer segmentation based on **RFM**.
- Launch a **VIP Tier Program** for high-value customers.

**3. Focus on High-value Customers**

Prioritize customer groups with:

- High Monetary Value
- High Purchase Frequency
- Low Recency

<img width="1343" height="691" alt="Customer Dashboard" src="https://github.com/user-attachments/assets/c615d1ff-c9a5-4518-bb22-6f4bb8f19bfc" />

---

# 3. Sales Performance — Revenue & Profitability

### 🔎 Key Findings

- Revenue reached about **15.7 billion VND** across the dataset.
- Streetwear is the largest category, contributing about **80% of profit**, which creates dependency on a single category.
- **Promotions appear on about 38% of orders**, yet AOV tends to drop in many categories when promotions are used.
- Customers aged **25–44** are one of the most important groups to prioritize.

### 💡 Recommendations

**1. Improve Promotion Efficiency**

Instead of blanket discounts:

- Set a minimum order value.
- Use combo pricing.
- Apply personalized promotions.
- Enforce a discount floor to protect margin.

**2. Increase Customer Value**

Focus on:

- Cross-selling
- Upselling
- Product bundling

for customers with high purchase frequency and AOV.

**3. Reduce Category Concentration Risk**

- Keep growing Streetwear without becoming over-reliant on it.
- Expand **Outdoor** if the category shows growth potential.
- Re-evaluate **Casual** performance and adjust assortment/pricing.

<img width="1318" height="701" alt="Sales Dashboard" src="https://github.com/user-attachments/assets/e6deef96-0416-4d7e-981d-82c9bf4a287c" />

---

# 4. Inventory — Inventory Efficiency

### 🔎 Key Findings

The business is facing a **supply-demand imbalance**:

- **Days of Supply (DOS) reaches ~826 days**.
- Inventory replenishment exceeds actual demand.
- The inventory-to-sales ratio stays around **1.15–1.18**.
- This increases the risk of:
  - Capital being tied up
  - Overstock
  - Inventory aging
  - Markdown pressure

### 💡 Recommendations

#### Short-term — Liquidate Excess Inventory

- Flash Sale
- Markdown
- Clearance Campaign

Goal: quickly recover part of the capital tied up in stock.

#### Medium-term — Bundle

Combine:

> Slow-moving products + Best-selling products

to move excess stock without deep discounting.

#### Long-term — B2B / Wholesale

For products with high inventory aging:

- Wholesale
- B2B liquidation
- Outlet channels

can be used to clear inventory faster.

<img width="1309" height="693" alt="Inventory Dashboard" src="https://github.com/user-attachments/assets/b3052d26-983c-4ef8-803c-92696d654000" />

---

# 5. Logistics — Operational Efficiency

### 🔎 Key Findings

- Average delivery time is about **6 days**, leaving room to improve the delivery experience.
- **Wrong Size** is one of the most common return reasons.
- Size-related returns not only hurt customer experience but also increase:
  - Reverse logistics cost
  - Inventory handling cost
  - Delivery workload

### 💡 Recommendations

**1. Improve Size Selection**

- Design a clearer, more visual Size Guide.
- Add model height/weight.
- Provide fit information: Slim / Regular / Oversized.
- With enough data, build size recommendations based on customer profiles.

**2. Improve Delivery Performance**

- Adopt a **Multi-carrier Strategy**.
- Compare carriers by:
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

Priorities are ranked by **impact on revenue/profit** and **speed of implementation**. Each priority covers the problem (based on the findings), specific actions, owner, timeline, and KPIs to track.

> **Note:** Targets are **proposals** based on baselines in the dataset and should be validated through A/B tests or monthly tracking before being formally adopted. KPIs marked *"Measure from dashboard"* do not yet have a specific baseline and need one established before rollout.

### 🗺️ Roadmap Summary

| Priority | Core Problem | Key Actions | North-star KPI | Proposed Target |
|---|---|---|---|---|
| 1️⃣ Conversion & Retention | Registrations up but purchases down · 62.64% of users never purchased · ~48% Never Purchased/Lost | Funnel fix + welcome flow + RFM-based win-back | % Never Purchased/Lost customers | **48% → 40%** in 12 months |
| 2️⃣ Inventory Efficiency | DOS ~826 days · Inventory/Sales 1.15–1.18 | Stop replenishing aged SKUs + liquidate by inventory age | Days of Supply | **826 → < 365 days** in 12 months |
| 3️⃣ Promotion & Margin | Promotions on ~38% of orders · Margin 22% → 14% | Targeted promotions + discount floor | Gross Margin | **14% → 18%** in 12 months |
| 4️⃣ Revenue Diversification | Streetwear ~80% of profit | Expand Outdoor + grow the Email channel | % of profit from Streetwear | **80% → ≤ 70%** in 12 months |
| 5️⃣ Logistics & Returns | Delivery ~6 days · Wrong Size is a top return reason | Standardized size guide + carrier scorecard | Average Delivery Time | **6 → 4 days** in 6 months |

---

### 1️⃣ Improve Customer Conversion & Retention

**Why priority #1:** **Registrations are rising while purchases are falling**, meaning the business still attracts new users but fails to turn them into buyers. Traffic is growing, yet conversion is only **~0.13%**, **62.64%** of registered users have never purchased, and retention drops sharply from **Month +1**. The business is losing customers at both ends of the funnel: it cannot convert new users or keep existing buyers.

| # | Action | Implementation Details | Owner | Timeline |
|---|---|---|---|---|
| 1.1 | **Find funnel drop-off points** | Analyze the **Sign-up → Product View → Add to Cart → Checkout → Payment** funnel by monthly sign-up cohort to find the step losing the most users, and fix that step first. | Data / E-commerce | Month 1 |
| 1.2 | **Abandoned cart reminders** | Send email/push at **1h** and **24h** to users who added items to cart but did not pay, with product images and free-shipping info. | CRM | Month 1 |
| 1.3 | **Welcome flow for new users** | Email/push **24h** after sign-up if no purchase: **15% + Free Shipping** voucher, valid for 7 days. Second reminder after 72h. | CRM / Marketing | Month 1 |
| 1.4 | **Post-purchase journey** | Emails on day **+7** (styling tips, related products) and day **+21** (second-order voucher) to carry customers past the Month +1 drop. | CRM | Months 1–2 |
| 1.5 | **Recency-based win-back** | Automated triggers at **30 / 60 / 90 days** without a purchase, with escalating offers. After 90 days with no response, move to Lost and reduce send frequency. | CRM | Months 2–3 |
| 1.6 | **Monthly RFM segmentation** | Refresh RFM monthly in Power BI and map each segment to its own campaign (Champions → early access, At Risk → win-back, Hibernating → reactivation). | Data / CRM | Month 2 |
| 1.7 | **VIP Tier Program** | For the **top 10% of customers by Monetary value**: unlimited free shipping, early sale access, birthday gifts. | Marketing | Months 4–6 |

| KPI | Baseline | Proposed Target |
|---|---|---|
| Registered users who never purchased | 62.64% | **≤ 55%** after 6 months |
| First purchase within 30 days of sign-up | Measure from dashboard | Steady increase across monthly cohorts |
| Purchase growth vs. registration growth | Registrations up, purchases down | Purchases grow in line with registrations |
| Never Purchased + Lost | ~48% | **≤ 40%** after 12 months |
| Conversion Rate | ~0.13% | **≥ 0.18%** after 6 months |
| Month +1 Retention | Measure from dashboard | **+5 percentage points** vs. baseline |
| Repeat Purchase Rate / CLV | Measure from dashboard | Quarter-over-quarter growth |

---

### 2️⃣ Improve Inventory Efficiency

**Why priority #2:** A DOS of **~826 days** means current stock would last more than 2 years, while the inventory-to-sales ratio stays at **1.15–1.18**. Capital is locked in inventory and markdown pressure will keep growing.

| # | Action | Implementation Details | Owner | Timeline |
|---|---|---|---|---|
| 2.1 | **Classify SKUs by inventory age** | Split SKUs into 4 groups: **< 90 days / 90–180 / 180–365 / > 365 days**, combined with ABC analysis by revenue. This feeds every action below. | Data / Merchandising | Month 1 |
| 2.2 | **Stop replenishing aged SKUs** | Pause replenishment for SKUs with **DOS > 365 days**. Set reorder points from a **90-day** demand forecast instead of habitual ordering. | Supply Chain | Months 1–2 |
| 2.3 | **Liquidate by inventory age** | 180–365 days: **flash sale / 20–30% markdown**. Over 365 days: **clearance campaign**. | Merchandising / Marketing | Months 2–4 |
| 2.4 | **Bundle slow movers with best-sellers** | Pair 1 slow-moving SKU with 1 best-seller in the same category, discounting the bundle total rather than each item to protect best-seller pricing. | Merchandising | Months 3–6 |
| 2.5 | **B2B / Outlet channels** | Stock still over 365 days after clearance: move to wholesale, B2B liquidation, or outlet. | Sales / Ops | Months 6–12 |

| KPI | Baseline | Proposed Target |
|---|---|---|
| Days of Supply | ~826 days | **< 500 days** after 6 months · **< 365 days** after 12 months |
| Inventory-to-Sales Ratio | 1.15–1.18 | **≤ 1.0** |
| % SKUs aged > 365 days | Measure from dashboard | **50%** reduction after 12 months |
| Stockout Rate (best-sellers) | Measure from dashboard | No increase while cutting replenishment |

---

### 3️⃣ Improve Promotion & Margin

**Why priority #3:** Promotions appear on **~38% of orders**, yet AOV drops in many categories when promotions are used, while margin has already fallen from **~22% to ~14%**. Blanket discounting is eroding profit without increasing order value.

| # | Action | Implementation Details | Owner | Timeline |
|---|---|---|---|---|
| 3.1 | **Minimum order value** | Apply vouchers only to orders **≥ current AOV + 15–20%**, so promotions push AOV up instead of down. | Marketing | Month 1 |
| 3.2 | **Discount floor by category** | Cap discounts so post-discount margin stays **≥ 10%**; promotions above the cap require separate approval. | Finance / Merchandising | Months 1–2 |
| 3.3 | **Targeted instead of mass discounts** | Reserve deep offers for segments that need activation (At Risk, New), not for Champions who already buy regularly. | CRM | Months 2–3 |
| 3.4 | **Combo pricing & cross-sell** | Outfit combos (top + bottom + accessory) for high-frequency, high-AOV customers, especially those aged **25–44**. | Merchandising | Months 3–6 |
| 3.5 | **Measure Promotion ROI with a holdout** | Keep **10% of customers out of promotions** as a control group to measure the true incremental revenue of each campaign. | Data | Ongoing |

| KPI | Baseline | Proposed Target |
|---|---|---|
| % of orders with promotion | ~38% | **≤ 25%** after 6 months |
| Gross Margin | ~14% | **≥ 18%** after 12 months |
| AOV with vs. without promotion | Measure from dashboard | Narrow the gap |
| Promotion ROI | Not yet measured | Every campaign shows positive ROI vs. holdout |

---

### 4️⃣ Diversify Revenue Sources

**Why priority #4:** Streetwear generates **~80% of profit**, so any slowdown in this category hits total profit directly. On the channel side, Organic Search & Social Media bring high volume but low AOV, while **Email has high AOV but low volume**.

| # | Action | Implementation Details | Owner | Timeline |
|---|---|---|---|---|
| 4.1 | **Expand Outdoor** | Increase Outdoor assortment and ad budget if quarterly growth is positive; pilot with 10–20 new SKUs first. | Merchandising | Months 2–6 |
| 4.2 | **Restructure Casual** | Review the lowest-margin Casual SKUs, cut underperformers, and adjust pricing. | Merchandising | Months 3–4 |
| 4.3 | **Cross-sell from Streetwear** | Use Streetwear's large customer base to introduce Outdoor/Casual through "complete the look" suggestions on product pages and in emails. | Marketing / E-commerce | Months 2–4 |
| 4.4 | **Scale the Email channel** | Capture emails at checkout and on site (offer pop-ups), and shift part of the paid budget to CRM/Email and Referral. | Marketing | Months 1–6 |
| 4.5 | **Track CAC & AOV by channel** | Monthly report on CAC, AOV, and repeat rate per channel to reallocate budget by efficiency. | Data / Marketing | Month 1 |

| KPI | Baseline | Proposed Target |
|---|---|---|
| % of profit from Streetwear | ~80% | **≤ 70%** after 12 months |
| Outdoor revenue growth | Measure from dashboard | Positive quarter-over-quarter growth |
| % of revenue from Email | Measure from dashboard | **Double** after 12 months |
| CAC by channel | Measure from dashboard | Lower blended CAC |

---

### 5️⃣ Improve Logistics & Return Experience

**Why priority #5:** Average delivery time is **~6 days** and **Wrong Size** is a leading return reason. Every size-related return adds reverse logistics and inventory handling cost, and lowers the chance the customer comes back.

| # | Action | Implementation Details | Owner | Timeline |
|---|---|---|---|---|
| 5.1 | **Prioritize SKUs with high Wrong Size returns** | List the **top 20 SKUs** by Wrong Size returns and re-measure their actual size charts first. | Data / Product | Month 1 |
| 5.2 | **Detailed size guide** | Measurements in **cm**, model height/weight, and **Slim / Regular / Oversized** fit labels on every product page. | E-commerce / Product | Months 1–3 |
| 5.3 | **Size recommendation** | Suggest sizes from each customer's purchase and return history (once enough data is available). | Data | Months 6–12 |
| 5.4 | **Carrier scorecard** | Compare carriers monthly on **delivery time, on-time rate, return rate, cost per order**; shift volume to the best carrier in each region. | Ops / Logistics | Months 2–3 |
| 5.5 | **Regional multi-carrier setup** | Contract at least 2 carriers per major region for backup capacity and competitive pressure on SLAs. | Ops | Months 3–6 |

| KPI | Baseline | Proposed Target |
|---|---|---|
| Average Delivery Time | ~6 days | **≤ 4 days** after 6 months |
| Wrong Size returns | Measure from dashboard | **20–30%** reduction after 6 months |
| On-time Delivery Rate | Measure from dashboard | **≥ 95%** |
| Cost per Shipment | Measure from dashboard | No increase while cutting delivery time |

---

# 🛠️ Tools & Technologies

- **Power BI** — Dashboard & Data Visualization
- **Python** — Data Querying & Transformation
- **Excel** — Data Exploration & Validation
- **DAX** — KPI Calculation & Business Metrics

---

