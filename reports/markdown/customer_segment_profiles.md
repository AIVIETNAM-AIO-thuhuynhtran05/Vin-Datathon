# Profile các nhóm khách hàng

Tạo tự động bởi `customer_segmentation/06_cluster_profiling.py` từ nhãn cụm trong `customer_segments.csv`. **Tên cụm là gợi ý** theo ma trận Recency × Giá trị (`segment_naming.py`) — chỉnh lại khi diễn giải. Dữ liệu không có biến nghề nghiệp/thu nhập; chân dung dựa trên giới tính, nhóm tuổi, vùng, kênh thu hút và hành vi mua.

## 0. Bức tranh tổng thể toàn bộ khách hàng

Khách **chưa có đơn phát sinh doanh thu** được gán nhóm theo luật (**rule-based**, mã RB) trước khi phân cụm; khách **đã mua** được phân cụm bằng K-Means (mã C). Lift nhân khẩu học ở mục này so với toàn bộ khách đã đăng ký.

| Phương pháp | Nhóm | Tên | Khách | % khách | % doanh thu | Frequency (median) | Monetary (median) |
|---|---|---|---:|---:|---:|---:|---:|
| rule_based | RB1 | Chưa giao dịch | 31,684 | 26.0% | 0.0% | 0 | 0 |
| rule_based | RB2 | Đặt đơn nhưng chưa chuyển đổi | 2,407 | 2.0% | 0.0% | 0 | 0 |
| kmeans | C0 | Đã rời bỏ | 25,216 | 20.7% | 3.5% | 1 | 14,546 |
| kmeans | C1 | Champions | 13,535 | 11.1% | 42.1% | 15 | 367,444 |
| kmeans | C2 | Trung thành | 21,331 | 17.5% | 39.5% | 9 | 216,897 |
| kmeans | C3 | Ngủ đông | 27,757 | 22.8% | 14.9% | 3 | 66,978 |

![Toàn bộ khách hàng](../../data/processed/customer_segmentation/plots/profile_size_vs_revenue.png)

Luật gán nhóm: có ≥ 1 đơn `paid`/`shipped`/`delivered`/`returned` → K-Means; có đơn nhưng tất cả đều `cancelled`/`created` → **RB2**; chưa đặt đơn nào → **RB1**.

### RB1 — Chưa giao dịch

**31,684 khách (26.0%)** · chưa phát sinh doanh thu.

- **Chân dung nổi bật:** Vùng = Central 43% (lift 1.17).
- **Mục tiêu:** Kích hoạt đơn đầu tiên. **Hành động gợi ý:** Voucher đơn đầu có hạn, email/push giới thiệu sản phẩm bán chạy theo kênh thu hút của khách. **KPI:** Tỷ lệ chuyển đổi đơn đầu.

### RB2 — Đặt đơn nhưng chưa chuyển đổi

**2,407 khách (2.0%)** · chưa phát sinh doanh thu.

- **Chân dung nổi bật:** gần giống toàn bộ khách (lift trong khoảng 0,85–1,15).
- **Chi tiết:** số đơn thất bại 1 đơn: 2,255 khách (93.7%), 2 đơn: 140 khách (5.8%), 3 đơn: 12 khách (0.5%) · lý do cancelled: 2,123, abandoned: 258, abandoned+cancelled: 26.
- **Mục tiêu:** Gỡ rào cản để chuyển đổi đơn đầu tiên. **Hành động gợi ý:** Tìm lý do hủy/bỏ dở (thanh toán, giá, giao hàng), retarget bằng đúng sản phẩm khách từng đặt; ưu tiên khách có ≥ 2 đơn thất bại (ý định mua rõ, rào cản lặp lại). **KPI:** Tỷ lệ chuyển đổi đơn đầu tiên.

## 1. Tổng quan cụm K-Means (khách đã mua)

| Cụm | Tên gợi ý | Khách | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary | AOV | Tỷ lệ trả | Dùng KM |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | Đã rời bỏ | 25,216 | 28.7% | 3.5% | 2,392 | 1 | 14,546 | 11,597 | 7.3% | 40.0% |
| 1 | Champions | 13,535 | 15.4% | 42.1% | 125 | 15 | 367,444 | 23,607 | 6.1% | 39.5% |
| 2 | Trung thành | 21,331 | 24.3% | 39.5% | 595 | 9 | 216,897 | 23,786 | 6.0% | 37.7% |
| 3 | Ngủ đông | 27,757 | 31.6% | 14.9% | 1,333 | 3 | 66,978 | 22,261 | 5.6% | 37.1% |
| Tổng | — | 87,839 | 100.0% | 100.0% | 1,033 | 4 | 81,552 | 21,267 | 6.3% | 38.4% |

Giá trị là **median** (tỷ lệ trả và dùng khuyến mãi là trung bình).

![Cụm trên PCA](../../data/processed/customer_segmentation/plots/profile_pca_clusters.png)
![RFM theo cụm](../../data/processed/customer_segmentation/plots/profile_rfm_boxplots.png)
![Rank index](../../data/processed/customer_segmentation/plots/profile_rank_index.png)

## 2. Biến mô tả nào thực sự khác biệt giữa các cụm?

Với hàng chục nghìn khách, p-value của Chi-square gần như luôn rất nhỏ, nên đánh giá bằng **Cramér's V** (độ lớn hiệu ứng): < 0,05 không đáng kể · 0,05–0,1 yếu · 0,1–0,3 trung bình · ≥ 0,3 mạnh. Biến có V không đáng kể **không nên** dùng để nhắm mục tiêu cụm.

| Biến | Cramér's V | Mức độ | p-value |
|---|---:|---|---:|
| Danh mục ưa thích | 0.238 | trung bình | 0 |
| Thanh toán | 0.211 | trung bình | 0 |
| Thiết bị | 0.142 | trung bình | 0 |
| Nguồn đơn | 0.142 | trung bình | 0 |
| Vùng | 0.100 | yếu | 0 |
| Kênh thu hút | 0.008 | không đáng kể | 0.36 |
| Nhóm tuổi | 0.005 | không đáng kể | 0.86 |
| Giới tính | 0.004 | không đáng kể | 0.78 |

## 3. Chân dung từng cụm

### Cụm 0 — Đã rời bỏ

**25,216 khách (28.7%) · 3.5% doanh thu** · median R = 2,392 ngày, F = 1 đơn, M = 14,546, AOV = 11,597.

- **Hành vi nổi bật:** Monetary (doanh thu ròng) thấp hơn mặt bằng (-34 điểm phân vị); Frequency (số đơn) thấp hơn mặt bằng (-33 điểm phân vị); Recency (ngày, cao = lâu chưa mua) cao hơn mặt bằng (+27 điểm phân vị); Tenure (ngày từ đơn đầu) thấp hơn mặt bằng (-19 điểm phân vị).
- **Chân dung nổi bật:** Danh mục ưa thích = GenZ 6% (lift 2.77); Danh mục ưa thích = Outdoor 35% (lift 2.17); Thiết bị = tablet 13% (lift 2.11); Thanh toán = paypal 13% (lift 2.03); Nguồn đơn = referral 9% (lift 1.73); Thanh toán = bank_transfer 6% (lift 1.58).
- **Mục tiêu:** Tối ưu chi phí tiếp cận. **Hành động gợi ý:** Chỉ dùng kênh chi phí gần 0 (email định kỳ); không đầu tư ưu đãi lớn. **KPI:** Chi phí/đơn kéo về.
- ✍️ Ước tính tác động: … (vd +x% tỷ lệ mua lại × AOV × số khách).

### Cụm 1 — Champions

**13,535 khách (15.4%) · 42.1% doanh thu** · median R = 125 ngày, F = 15 đơn, M = 367,444, AOV = 23,607.

- **Hành vi nổi bật:** Recency (ngày, cao = lâu chưa mua) thấp hơn mặt bằng (-41 điểm phân vị); Frequency (số đơn) cao hơn mặt bằng (+34 điểm phân vị); Monetary (doanh thu ròng) cao hơn mặt bằng (+34 điểm phân vị); Tenure (ngày từ đơn đầu) cao hơn mặt bằng (+22 điểm phân vị).
- **Chân dung nổi bật:** Vùng = West 26% (lift 1.57); Nguồn đơn = email_campaign 8% (lift 0.58); Thanh toán = credit_card 92% (lift 1.31); Nguồn đơn = organic_search 50% (lift 1.30); Danh mục ưa thích = Streetwear 95% (lift 1.19); Thiết bị = mobile 53% (lift 1.17).
- **Mục tiêu:** Giữ chân và tăng giá trị. **Hành động gợi ý:** Chương trình VIP/early access, upsell sản phẩm premium, hạn chế giảm giá sâu. **KPI:** Retention, AOV.
- ✍️ Ước tính tác động: … (vd +x% tỷ lệ mua lại × AOV × số khách).

### Cụm 2 — Trung thành

**21,331 khách (24.3%) · 39.5% doanh thu** · median R = 595 ngày, F = 9 đơn, M = 216,897, AOV = 23,786.

- **Hành vi nổi bật:** Frequency (số đơn) cao hơn mặt bằng (+26 điểm phân vị); Monetary (doanh thu ròng) cao hơn mặt bằng (+26 điểm phân vị); Tenure (ngày từ đơn đầu) cao hơn mặt bằng (+17 điểm phân vị); Recency (ngày, cao = lâu chưa mua) thấp hơn mặt bằng (-13 điểm phân vị).
- **Chân dung nổi bật:** Thanh toán = cod 5% (lift 0.51); Nguồn đơn = direct 6% (lift 0.64); Thanh toán = credit_card 88% (lift 1.25); Nguồn đơn = email_campaign 10% (lift 0.77); Danh mục ưa thích = Streetwear 95% (lift 1.19); Nguồn đơn = organic_search 46% (lift 1.19).
- **Mục tiêu:** Tăng tần suất mua. **Hành động gợi ý:** Tích điểm theo bậc, cross-sell theo danh mục ưa thích, nhắc mua định kỳ. **KPI:** Frequency, doanh thu/khách.
- ✍️ Ước tính tác động: … (vd +x% tỷ lệ mua lại × AOV × số khách).

### Cụm 3 — Ngủ đông

**27,757 khách (31.6%) · 14.9% doanh thu** · median R = 1,333 ngày, F = 3 đơn, M = 66,978, AOV = 22,261.

- **Hành vi nổi bật:** Tenure (ngày từ đơn đầu) thấp hơn mặt bằng (-7 điểm phân vị); Frequency (số đơn) thấp hơn mặt bằng (-7 điểm phân vị); Monetary (doanh thu ròng) thấp hơn mặt bằng (-6 điểm phân vị).
- **Chân dung nổi bật:** Thanh toán = apple_pay 14% (lift 1.58); Nguồn đơn = direct 14% (lift 1.54); Thanh toán = bank_transfer 6% (lift 1.51); Nguồn đơn = email_campaign 18% (lift 1.34); Thanh toán = cod 14% (lift 1.34); Nguồn đơn = social_media 10% (lift 0.74).
- **Mục tiêu:** Đánh thức với chi phí thấp. **Hành động gợi ý:** Remarketing/email theo mùa, ưu đãi nhỏ; đo phản hồi trước khi đầu tư thêm. **KPI:** Reactivation rate.
- ✍️ Ước tính tác động: … (vd +x% tỷ lệ mua lại × AOV × số khách).

## 4. Chân dung chi tiết theo biến

Ô hiển thị % khách trong cụm; màu đỏ = lift > 1 (nhiều hơn mặt bằng), xanh = lift < 1.

![Danh mục ưa thích](../../data/processed/customer_segmentation/plots/profile_preferred_category.png)
![Thanh toán](../../data/processed/customer_segmentation/plots/profile_preferred_payment.png)
![Thiết bị](../../data/processed/customer_segmentation/plots/profile_preferred_device.png)
![Nguồn đơn](../../data/processed/customer_segmentation/plots/profile_preferred_source.png)
![Vùng](../../data/processed/customer_segmentation/plots/profile_region.png)
![Kênh thu hút](../../data/processed/customer_segmentation/plots/profile_acquisition_channel.png)
![Nhóm tuổi](../../data/processed/customer_segmentation/plots/profile_age_group.png)
![Giới tính](../../data/processed/customer_segmentation/plots/profile_gender.png)
