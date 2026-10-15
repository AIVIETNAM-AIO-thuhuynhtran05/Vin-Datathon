# PCA cho phân cụm khách hàng

Tạo tự động bởi `customer_segmentation/03_pca_analysis.py`.

## 1. Vì sao dùng PCA trước K-Means

1. **K-Means đo khoảng cách Euclid**, mọi biến có trọng số như nhau. Khi hai biến tương quan mạnh, chúng đo cùng một khía cạnh hành vi và khía cạnh đó bị tính hai lần. Ở đây cặp tương quan mạnh nhất là **Frequency – Monetary (r = 0.83)**: khách mua nhiều lần thì tổng chi tiêu cũng cao. Nếu không xử lý, cụm sẽ bị chi phối bởi "giá trị mua" và Recency bị lép vế.
2. **PCA xoay dữ liệu sang các trục trực giao** (không tương quan). Mỗi trục gom phần thông tin chung của các biến tương quan, nên khoảng cách không còn bị đếm trùng khi ta bỏ bớt trục ít thông tin.
3. **Rút gọn chiều và lọc nhiễu**: giữ các PC giải thích phần lớn phương sai, bỏ PC cuối (chủ yếu là nhiễu).
4. **Trực quan hóa**: PC1–PC2 là mặt phẳng 2D tốt nhất để vẽ và kiểm tra cụm có tách nhau không.
5. **Diễn giải**: loadings cho biết mỗi trục được tạo từ biến nào, giúp đặt tên trục theo ngôn ngữ kinh doanh.

**Tiền xử lý bắt buộc**: `log1p` (vì Frequency/Monetary lệch phải mạnh) rồi `StandardScaler`. PCA tìm hướng có phương sai lớn nhất, nên nếu không chuẩn hóa thì Monetary (đơn vị tiền, hàng chục nghìn) sẽ chiếm gần trọn PC1.

> **Lưu ý quan trọng:** nếu giữ **đủ tất cả** PC thì PCA chỉ là phép xoay, khoảng cách Euclid không đổi, nên K-Means cho kết quả **giống hệt** khi chạy trên dữ liệu đã scale. Lợi ích của PCA với K-Means chỉ đến từ việc **bỏ bớt** PC. Với chỉ 3 biến, mức rút gọn nhỏ; giá trị chính là khử tương quan, trực quan hóa và diễn giải.

## 2. Dữ liệu có phù hợp để PCA không?

- Số khách hàng: **87,839**; số biến: **3** (Recency, Frequency, Monetary).
- **Bartlett's test of sphericity**: χ² = 142,475, p = 0 → bác bỏ H0, các biến có tương quan đáng kể, **PCA có ý nghĩa**.
- **KMO** = 0.65 → chấp nhận được (0,6–0,7).

| | Recency | Frequency | Monetary |
|---|---:|---:|---:|
| **Recency** | 1.00 | -0.60 | -0.52 |
| **Frequency** | -0.60 | 1.00 | 0.83 |
| **Monetary** | -0.52 | 0.83 | 1.00 |

![Tương quan giữa các biến RFM](../../data/processed/customer_segmentation/plots/pca_feature_correlation.png)

## 3. Chọn số thành phần

| PC | Eigenvalue | % phương sai | % tích lũy | Biến chính (trị tuyệt đối loading ≥ 0,5) |
|---|---:|---:|---:|---|
| PC1 | 2.314 | 77.1% | 77.1% | +Frequency (+0.93), +Monetary (+0.91), −Recency (-0.79) |
| PC2 | 0.523 | 17.4% | 94.6% | +Recency (+0.61) |
| PC3 | 0.163 | 5.4% | 100.0% | −Frequency (-0.30) |

- **Tiêu chí phương sai tích lũy** (≥ 80%): cần **2** PC.
- **Tiêu chí Kaiser** (eigenvalue > 1): **1** PC.
- **Scree plot** (`pca_scree.png`): chọn tại "khuỷu", nơi phần phương sai tăng thêm giảm đột ngột.
- **Đã chọn: 2 PC** (phương sai tích lũy ≥ 80%, tối thiểu 2 PC), giữ **94.6%** phương sai. Đổi bằng `--variance-target` hoặc `--n-components`.

![Scree plot](../../data/processed/customer_segmentation/plots/pca_scree.png)

## 4. Diễn giải các thành phần

Loading = tương quan giữa biến gốc và PC (dấu chỉ chiều; Recency cao = lâu rồi chưa mua = **xấu**).

- **PC1**: +Frequency (+0.93), +Monetary (+0.91), −Recency (-0.79).
- **PC2**: +Recency (+0.61).
- **PC3**: −Frequency (-0.30).

Gợi ý đọc trục: thành phần mà Frequency và Monetary cùng dấu, Recency ngược dấu là trục **"giá trị & gắn bó"** (cao = mua nhiều, chi nhiều, mới mua gần đây). Thành phần mà Recency nổi trội là trục **"độ mới"**, tách khách vừa mua gần đây với khách đã lâu không quay lại ở cùng mức giá trị.

![Loadings](../../data/processed/customer_segmentation/plots/pca_loadings.png)

![Biplot PC1–PC2](../../data/processed/customer_segmentation/plots/pca_biplot.png)

## 5. Dùng kết quả cho K-Means

- File đầu vào K-Means: `data/processed/customer_segmentation/customer_pca_scores.csv` (`customer_id`, `PC1`, `PC2`).
- **Không scale lại** điểm PC: phương sai khác nhau giữa các PC chính là mức quan trọng của từng trục. Nếu muốn mọi trục có trọng số bằng nhau thì dùng whitening (`PCA(whiten=True)`), nhưng khi đó nhiễu ở PC nhỏ sẽ bị khuếch đại.
- Kết quả K-Means cần ghi ra `data/processed/customer_segmentation/customer_segments.csv` với 2 cột `customer_id`, `cluster` để bước 5 (`06_cluster_profiling.py`) mô tả cụm.
