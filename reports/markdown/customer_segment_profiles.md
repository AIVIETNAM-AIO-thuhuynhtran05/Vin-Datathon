# Profile các nhóm khách hàng

Tạo tự động bởi `customer_segmentation/06_cluster_profiling.py` từ nhãn cụm trong `customer_segments.csv`. Tên cụm đặt theo ma trận Recency × Giá trị (`segment_naming.py`) và đã đối chiếu với profile bên dưới. Dữ liệu không có biến nghề nghiệp/thu nhập; chân dung dựa trên giới tính, nhóm tuổi, vùng, kênh thu hút và hành vi mua.

## 0. Bức tranh tổng thể toàn bộ khách hàng

Khách **chưa có đơn phát sinh doanh thu** được gán nhóm theo luật (**rule-based**, mã RB) trước khi phân cụm; khách **đã mua** được phân cụm bằng K-Means (mã C). Lift nhân khẩu học ở mục này so với toàn bộ khách đã đăng ký.

| Phương pháp | Nhóm | Tên | Khách | % khách | % doanh thu | Frequency (median) | Monetary (median) |
|---|---|---|---:|---:|---:|---:|---:|
| rule_based | RB1 | Chưa giao dịch | 31,684 | 26.0% | 0.0% | 0 | 0 |
| rule_based | RB2 | Đặt đơn nhưng chưa chuyển đổi | 2,407 | 2.0% | 0.0% | 0 | 0 |
| kmeans | C0 | Champions | 12,384 | 10.2% | 43.6% | 17 | 421,487 |
| kmeans | C1 | Đã rời bỏ | 22,412 | 18.4% | 2.6% | 1 | 12,788 |
| kmeans | C2 | Trung thành | 19,103 | 15.7% | 34.9% | 9 | 219,127 |
| kmeans | C3 | Khách mới / tiềm năng | 8,945 | 7.3% | 5.7% | 4 | 80,930 |
| kmeans | C4 | Ngủ đông | 24,995 | 20.5% | 13.1% | 3 | 64,500 |

![Toàn bộ khách hàng](../../data/processed/customer_segmentation/plots/profile_size_vs_revenue.png)

Luật gán nhóm: có ≥ 1 đơn `paid`/`shipped`/`delivered`/`returned` → K-Means; có đơn nhưng tất cả đều `cancelled`/`created` → **RB2**; chưa đặt đơn nào → **RB1**.

### RB1 — Chưa giao dịch

**31,684 khách (26.0%)** · chưa phát sinh doanh thu.

- **Chân dung nổi bật:** Vùng = Central 43% (lift 1.17).
- **Mục tiêu:** Kích hoạt đơn đầu tiên. **Hành động:** Voucher đơn đầu có hạn, email/push giới thiệu sản phẩm bán chạy theo kênh thu hút của khách. **KPI:** Tỷ lệ chuyển đổi đơn đầu.

### RB2 — Đặt đơn nhưng chưa chuyển đổi

**2,407 khách (2.0%)** · chưa phát sinh doanh thu.

- **Chân dung nổi bật:** gần giống toàn bộ khách (lift trong khoảng 0,85–1,15).
- **Chi tiết:** số đơn thất bại 1 đơn: 2,255 khách (93.7%), 2 đơn: 140 khách (5.8%), 3 đơn: 12 khách (0.5%) · lý do cancelled: 2,123, abandoned: 258, abandoned+cancelled: 26.
- **Mục tiêu:** Gỡ rào cản để chuyển đổi đơn đầu tiên. **Hành động:** Tìm lý do hủy/bỏ dở (thanh toán, giá, giao hàng), retarget bằng đúng sản phẩm khách từng đặt; ưu tiên khách có ≥ 2 đơn thất bại (ý định mua rõ, rào cản lặp lại). **KPI:** Tỷ lệ chuyển đổi đơn đầu tiên.

## 1. Tổng quan cụm K-Means (khách đã mua)

| Cụm | Tên nhóm | Khách | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary | AOV | Tỷ lệ trả | Dùng KM |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Champions | 12,384 | 14.1% | 43.6% | 149 | 17 | 421,487 | 23,888 | 6.1% | 38.6% |
| 1 | Đã rời bỏ | 22,412 | 25.5% | 2.6% | 2,391 | 1 | 12,788 | 10,487 | 7.8% | 41.1% |
| 2 | Trung thành | 19,103 | 21.7% | 34.9% | 659 | 9 | 219,127 | 23,764 | 5.9% | 37.8% |
| 3 | Khách mới / tiềm năng | 8,945 | 10.2% | 5.7% | 206 | 4 | 80,930 | 20,775 | 6.2% | 39.5% |
| 4 | Ngủ đông | 24,995 | 28.5% | 13.1% | 1,650 | 3 | 64,500 | 22,627 | 5.2% | 36.0% |
| Tổng | — | 87,839 | 100.0% | 100.0% | 1,033 | 4 | 81,552 | 21,267 | 6.3% | 38.4% |

Giá trị là **median** (tỷ lệ trả và dùng khuyến mãi là trung bình).

![Cụm trên PCA](../../data/processed/customer_segmentation/plots/profile_pca_clusters.png)
![RFM theo cụm](../../data/processed/customer_segmentation/plots/profile_rfm_boxplots.png)
![Rank index](../../data/processed/customer_segmentation/plots/profile_rank_index.png)

## 2. Biến mô tả nào thực sự khác biệt giữa các cụm?

Với hàng chục nghìn khách, p-value của Chi-square gần như luôn rất nhỏ, nên đánh giá bằng **Cramér's V** (độ lớn hiệu ứng): < 0,05 không đáng kể · 0,05–0,1 yếu · 0,1–0,3 trung bình · ≥ 0,3 mạnh. Biến có V không đáng kể **không nên** dùng để nhắm mục tiêu cụm.

| Biến | Cramér's V | Mức độ | p-value |
|---|---:|---|---:|
| Danh mục ưa thích | 0.245 | trung bình | 0 |
| Thanh toán | 0.185 | trung bình | 0 |
| Thiết bị | 0.143 | trung bình | 0 |
| Nguồn đơn | 0.128 | trung bình | 0 |
| Vùng | 0.113 | trung bình | 0 |
| Kênh thu hút | 0.008 | không đáng kể | 0.25 |
| Giới tính | 0.006 | không đáng kể | 0.65 |
| Nhóm tuổi | 0.005 | không đáng kể | 0.95 |

## 3. Chân dung từng cụm

### Cụm 0 — Champions

**12,384 khách (14.1%) · 43.6% doanh thu** · median R = 149 ngày, F = 17 đơn, M = 421,487, AOV = 23,888.

- **Hành vi nổi bật:** Frequency (số đơn) cao hơn mặt bằng (+39 điểm phân vị); Monetary (doanh thu ròng) cao hơn mặt bằng (+39 điểm phân vị); Recency (ngày, cao = lâu chưa mua) thấp hơn mặt bằng (-39 điểm phân vị); Tenure (ngày từ đơn đầu) cao hơn mặt bằng (+26 điểm phân vị).
- **Chân dung nổi bật:** Vùng = West 28% (lift 1.73); Nguồn đơn = email_campaign 6% (lift 0.49); Thanh toán = credit_card 96% (lift 1.36); Nguồn đơn = organic_search 52% (lift 1.35); Danh mục ưa thích = Streetwear 96% (lift 1.21); Thiết bị = mobile 54% (lift 1.20).
- **Mục tiêu:** Giữ chân và tăng giá trị. **Hành động:** Chương trình VIP/early access, upsell sản phẩm premium, hạn chế giảm giá sâu. **KPI:** Retention, AOV.
- **Kênh tiếp cận và thứ tự ưu tiên:** xem mục 8 *Recommendation* của README phân cụm.

### Cụm 1 — Đã rời bỏ

**22,412 khách (25.5%) · 2.6% doanh thu** · median R = 2,391 ngày, F = 1 đơn, M = 12,788, AOV = 10,487.

- **Hành vi nổi bật:** Monetary (doanh thu ròng) thấp hơn mặt bằng (-36 điểm phân vị); Frequency (số đơn) thấp hơn mặt bằng (-34 điểm phân vị); Recency (ngày, cao = lâu chưa mua) cao hơn mặt bằng (+27 điểm phân vị); Giá trị đơn TB (AOV) thấp hơn mặt bằng (-20 điểm phân vị).
- **Chân dung nổi bật:** Danh mục ưa thích = GenZ 6% (lift 2.93); Danh mục ưa thích = Outdoor 37% (lift 2.31); Thiết bị = tablet 13% (lift 2.17); Thanh toán = paypal 13% (lift 2.08); Nguồn đơn = referral 9% (lift 1.76); Thanh toán = bank_transfer 6% (lift 1.53).
- **Mục tiêu:** Tối ưu chi phí tiếp cận. **Hành động:** Chỉ dùng kênh chi phí gần 0 (email định kỳ); không đầu tư ưu đãi lớn. **KPI:** Chi phí/đơn kéo về.
- **Kênh tiếp cận và thứ tự ưu tiên:** xem mục 8 *Recommendation* của README phân cụm.

### Cụm 2 — Trung thành

**19,103 khách (21.7%) · 34.9% doanh thu** · median R = 659 ngày, F = 9 đơn, M = 219,127, AOV = 23,764.

- **Hành vi nổi bật:** Frequency (số đơn) cao hơn mặt bằng (+26 điểm phân vị); Monetary (doanh thu ròng) cao hơn mặt bằng (+26 điểm phân vị); Tenure (ngày từ đơn đầu) cao hơn mặt bằng (+18 điểm phân vị); Recency (ngày, cao = lâu chưa mua) thấp hơn mặt bằng (-9 điểm phân vị).
- **Chân dung nổi bật:** Thanh toán = cod 5% (lift 0.52); Nguồn đơn = direct 6% (lift 0.63); Thanh toán = credit_card 88% (lift 1.25); Nguồn đơn = email_campaign 10% (lift 0.75); Danh mục ưa thích = Streetwear 95% (lift 1.19); Nguồn đơn = organic_search 46% (lift 1.19).
- **Mục tiêu:** Tăng tần suất mua. **Hành động:** Tích điểm theo bậc, cross-sell theo danh mục ưa thích, nhắc mua định kỳ. **KPI:** Frequency, doanh thu/khách.
- **Kênh tiếp cận và thứ tự ưu tiên:** xem mục 8 *Recommendation* của README phân cụm.

### Cụm 3 — Khách mới / tiềm năng

**8,945 khách (10.2%) · 5.7% doanh thu** · median R = 206 ngày, F = 4 đơn, M = 80,930, AOV = 20,775.

- **Hành vi nổi bật:** Recency (ngày, cao = lâu chưa mua) thấp hơn mặt bằng (-35 điểm phân vị); Tenure (ngày từ đơn đầu) thấp hơn mặt bằng (-10 điểm phân vị).
- **Chân dung nổi bật:** Nguồn đơn = direct 12% (lift 1.33); Vùng = West 12% (lift 0.70); Thanh toán = apple_pay 12% (lift 1.29); Danh mục ưa thích = Outdoor 13% (lift 0.82); Nguồn đơn = email_campaign 15% (lift 1.17); Thanh toán = cod 12% (lift 1.17).
- **Mục tiêu:** Tạo thói quen mua lặp lại. **Hành động:** Voucher đơn kế tiếp trong 30 ngày, email onboarding, gợi ý sản phẩm bán chạy. **KPI:** Tỷ lệ mua lần tiếp theo.
- **Kênh tiếp cận và thứ tự ưu tiên:** xem mục 8 *Recommendation* của README phân cụm.

### Cụm 4 — Ngủ đông

**24,995 khách (28.5%) · 13.1% doanh thu** · median R = 1,650 ngày, F = 3 đơn, M = 64,500, AOV = 22,627.

- **Hành vi nổi bật:** Recency (ngày, cao = lâu chưa mua) cao hơn mặt bằng (+14 điểm phân vị); Frequency (số đơn) thấp hơn mặt bằng (-8 điểm phân vị); Giá trị đơn TB (AOV) cao hơn mặt bằng (+6 điểm phân vị); Monetary (doanh thu ròng) thấp hơn mặt bằng (-6 điểm phân vị).
- **Chân dung nổi bật:** Thanh toán = apple_pay 14% (lift 1.60); Thanh toán = bank_transfer 6% (lift 1.58); Nguồn đơn = direct 14% (lift 1.53); Nguồn đơn = email_campaign 18% (lift 1.35); Thanh toán = cod 14% (lift 1.35); Nguồn đơn = social_media 10% (lift 0.74).
- **Mục tiêu:** Đánh thức với chi phí thấp. **Hành động:** Remarketing/email theo mùa, ưu đãi nhỏ; đo phản hồi trước khi đầu tư thêm. **KPI:** Reactivation rate.
- **Kênh tiếp cận và thứ tự ưu tiên:** xem mục 8 *Recommendation* của README phân cụm.

## 4. Chân dung chi tiết theo biến

Ô hiển thị % khách trong cụm; màu đỏ = lift > 1 (nhiều hơn mặt bằng), xanh = lift < 1.

![Danh mục ưa thích](../../data/processed/customer_segmentation/plots/profile_preferred_category.png)
![Thanh toán](../../data/processed/customer_segmentation/plots/profile_preferred_payment.png)
![Thiết bị](../../data/processed/customer_segmentation/plots/profile_preferred_device.png)
![Nguồn đơn](../../data/processed/customer_segmentation/plots/profile_preferred_source.png)
![Vùng](../../data/processed/customer_segmentation/plots/profile_region.png)
![Kênh thu hút](../../data/processed/customer_segmentation/plots/profile_acquisition_channel.png)
![Giới tính](../../data/processed/customer_segmentation/plots/profile_gender.png)
![Nhóm tuổi](../../data/processed/customer_segmentation/plots/profile_age_group.png)
