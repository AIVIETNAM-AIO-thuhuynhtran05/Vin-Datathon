# Feature engineering cho phân cụm khách hàng

Tạo tự động bởi `customer_segmentation/02_transform_features.py`.

## 1. Biến đưa vào K-Means: RFM

Áp dụng cho **87,839 khách có đơn phát sinh doanh thu**. 34,091 khách không có đơn doanh thu được gán nhóm rule-based ở bước 01, không đưa vào K-Means.

| Biến | Định nghĩa | Chiều tốt | Min | Median | Mean | Max | Skew |
|---|---|---|---:|---:|---:|---:|---:|
| `recency_days` | Số ngày từ đơn doanh thu gần nhất đến ngày tham chiếu (ngày đặt cuối cùng trong dữ liệu + 1) | Thấp | 1 | 1,033 | 1,289 | 3,833 | +0.62 |
| `frequency` | Số đơn phát sinh doanh thu (`paid`/`shipped`/`delivered`/`returned`) | Cao | 1 | 4 | 7 | 100 | +2.61 |
| `monetary` | Σ(`payment_value` − tiền hoàn của đơn), mỗi đơn chặn dưới ở 0 | Cao | 0 | 81,552 | 154,211 | 3,115,457 | +2.55 |

**Vì sao chỉ dùng RFM:**

- RFM đo trực tiếp **hành vi mua tạo doanh thu**: đây là thứ doanh nghiệp tác động được bằng marketing, và gắn thẳng với mục tiêu tăng doanh thu.
- Nhân khẩu học (tuổi, giới tính, vùng, kênh thu hút) **không** đưa vào. Lý do: cụm cần phản ánh hành vi; các biến này chỉ dùng để mô tả cụm sau khi phân xong (bước 06).
- Có 119 khách có `monetary` = 0, do tiền hoàn bằng hoặc vượt tiền thanh toán (chặn ở 0). Họ vẫn có frequency và recency nên vẫn được giữ lại.

## 2. Biến đổi phân phối

K-Means nhạy với phân phối lệch: vài khách chi tiêu cực lớn sẽ kéo tâm cụm và chiếm khoảng cách. Mỗi biến được thử 4 phép biến đổi. Gợi ý là **phép đơn giản nhất** có |skew| không kém lựa chọn tốt nhất quá 0,1 (|skew| gần 0 nghĩa là phân phối gần đối xứng).

| Biến | Không biến đổi | sqrt | log1p | Yeo-Johnson | Đang dùng | Gợi ý |
|---|---:|---:|---:|---:|---|---|
| `recency_days` | +0.62 | +0.01 | -1.22 | -0.17 | `log1p` ⚠️ | `sqrt` |
| `frequency` | +2.61 | +1.19 | +0.53 | +0.13 | `log1p` ⚠️ | `yeo-johnson` |
| `monetary` | +2.55 | +0.96 | -1.07 | -0.02 | `log1p` ⚠️ | `yeo-johnson` |

⚠️ **Phép biến đổi đang dùng khác gợi ý** cho: `recency_days` (đang `log1p`, skew -1.22; gợi ý `sqrt`, skew +0.01), `frequency` (đang `log1p`, skew +0.53; gợi ý `yeo-johnson`, skew +0.13), `monetary` (đang `log1p`, skew -1.07; gợi ý `yeo-johnson`, skew -0.02). Đổi trong `config.FEATURE_TRANSFORMS` rồi chạy lại từ bước 02.

![Phân phối trước và sau biến đổi](../../data/processed/customer_segmentation/plots/fe_distributions.png)

## 3. Chuẩn hóa (StandardScaler)

Sau khi biến đổi, mỗi biến được chuẩn hóa về **mean 0, độ lệch chuẩn 1**. K-Means dùng khoảng cách Euclid, nên nếu không chuẩn hóa thì biến có thang lớn (Monetary) sẽ quyết định gần như toàn bộ khoảng cách.

| Biến | Phép biến đổi | Mean trước scale | Std trước scale | Mean sau scale | Std sau scale |
|---|---|---:|---:|---:|---:|
| `recency_days` | `log1p` | 6.643 | 1.261 | +0.000 | 1.000 |
| `frequency` | `log1p` | 1.651 | 0.832 | -0.000 | 1.000 |
| `monetary` | `log1p` | 11.146 | 1.494 | +0.000 | 1.000 |

Bước tiếp theo (chương PCA): các biến sau chuẩn hóa vẫn tương quan với nhau (Frequency ↔ Monetary), nên dùng PCA để khử tương quan trước khi chạy K-Means.

## 4. Biến hành vi ứng viên

Các biến dưới đây được tạo từ dữ liệu giao dịch và đánh giá theo câu hỏi: biến này có mang **thông tin mới** so với RFM không? Dùng tương quan Spearman (bền với dữ liệu lệch). |ρ| ≥ 0.7 với một biến RFM nghĩa là trùng thông tin: đưa vào K-Means chỉ làm khía cạnh đó bị tính hai lần.

| Biến | Định nghĩa | Độ phủ | Median | Skew | Tương quan mạnh nhất với RFM | Quyết định |
|---|---|---:|---:|---:|---|---|
| `aov` | Monetary / Frequency | 100% | 21,266.97 | +1.87 | `monetary` (+0.56) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `items_per_order` | Tổng số sản phẩm / số đơn doanh thu | 100% | 5.00 | +0.72 | `monetary` (+0.20) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `tenure_days` | Số ngày từ đơn doanh thu đầu tiên đến ngày tham chiếu | 100% | 3,299.00 | -1.40 | `frequency` (+0.66) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `promo_share` | Tỷ lệ dòng hàng có mã khuyến mãi | 100% | 0.35 | +0.53 | `frequency` (+0.12) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `return_rate` | Tỷ lệ đơn bị trả trên số đơn doanh thu | 100% | 0.00 | +4.10 | `frequency` (+0.40) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `cancel_rate` | Tỷ lệ đơn hủy trên mọi đơn đã đặt | 100% | 0.00 | +2.11 | `frequency` (+0.39) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |
| `avg_rating` | Điểm đánh giá trung bình (chỉ khách có đánh giá) | 55% | 4.00 | -1.03 | `frequency` (-0.07) | Mang thông tin mới so với RFM → dùng để mô tả cụm; có thể cân nhắc đưa vào K-Means ✍️ |

![Tương quan biến ứng viên với RFM](../../data/processed/customer_segmentation/plots/fe_candidate_correlation.png)

**Biến phân loại** (danh mục, thiết bị, phương thức thanh toán, nguồn đơn ưa thích) và **nhân khẩu học** không đưa vào K-Means vì không đo được bằng khoảng cách Euclid; chúng được dùng để mô tả cụm ở bước 06.

## 5. Kết quả

- Ma trận đặc trưng: **87,839 khách × 3 biến** (`recency_days`, `frequency`, `monetary`), đã biến đổi và chuẩn hóa.
- File: `data/processed/customer_segmentation/customer_features_transformed.csv`. Đây là đầu vào của PCA (bước 03).
- ✍️ Nếu quyết định thêm biến hành vi vào K-Means: thêm vào `config.RFM_FEATURES`, khai báo phép biến đổi trong `config.FEATURE_TRANSFORMS`, rồi chạy lại từ bước 02.
