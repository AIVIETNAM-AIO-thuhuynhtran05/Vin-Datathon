# Chọn số cụm k cho K-Means

Tạo tự động bởi `customer_segmentation/04_select_k.py` · đầu vào: `pca` · 87,839 khách đã mua · k = 2–8 · 5 random_state mỗi k. Bước này **không ghi nhãn cụm**; chọn k xong chạy `05_kmeans_segmentation.py --k <k>`.

## 1. Vì sao không chỉ nhìn silhouette

Các chỉ số thống kê thường ưu tiên k nhỏ: ít cụm thì cụm tách nhau rõ hơn. Nhưng số nhóm phải đủ để **mỗi nhóm nhận một chiến lược khác nhau**. Vì vậy k được chọn theo 3 lớp:

1. **Điều kiện business (lọc):**
   - k ≥ 3.
   - Cụm nhỏ nhất ≥ 5% khách (đủ lớn để chạy chiến dịch riêng).
   - Mỗi cụm có tên hành vi khác nhau (`distinct_actions = k`): không có hai cụm cùng một loại, nghĩa là không có hai cụm phải xử lý giống nhau. Tên đặt theo ma trận Recency × Giá trị (`segment_naming.py`).
2. **Độ ổn định:** ARI trung bình giữa các lần chạy ≥ 0.9. Nhãn không đổi khi đổi random_state.
3. **Chất lượng thống kê:** xếp hạng trung bình của Silhouette (↑), Calinski-Harabasz (↑) và Davies-Bouldin (↓); tham khảo thêm điểm elbow của inertia.

## 2. Kết quả

| k | Inertia | Silhouette | Calinski-Harabasz | Davies-Bouldin | ARI | Cụm nhỏ nhất | Nhóm hành động | Hạng TK | Đạt điều kiện |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 2 | 106,747 | 0.494 | 117,209 | 0.749 | 0.995 | 44.2% | 2/2 | 1.0 | — |
| 3 **◄** | 75,474 | 0.401 | 101,084 | 0.882 | 0.988 | 24.9% | 3/3 | 3.3 | ✅ |
| 4 | 61,960 | 0.346 | 88,475 | 0.990 | 0.944 | 15.4% | 4/4 | 5.3 | ✅ |
| 5 | 49,782 | 0.374 | 87,957 | 0.846 | 0.956 | 10.2% | 5/5 | 3.3 | ✅ |
| 6 | 41,627 | 0.372 | 87,592 | 0.867 | 0.969 | 4.2% | 5/6 | 4.3 | — |
| 7 | 36,410 | 0.346 | 85,550 | 0.873 | 0.986 | 3.2% | 6/7 | 6.3 | — |
| 8 | 31,427 | 0.364 | 86,943 | 0.800 | 0.961 | 3.0% | 6/8 | 4.3 | — |

![Chỉ số theo k](../../data/processed/customer_segmentation/plots/k_selection_metrics.png)

- Elbow của inertia: **k = 4**. Silhouette cao nhất: **k = 2**.
- **Gợi ý: k = 3**: silhouette 0.401, ARI 0.988, cụm nhỏ nhất 24.9%, 3 nhóm hành động khác nhau.
- Đây là gợi ý; quyết định cuối nên dựa vào mục 3: nhóm nào cần chiến lược riêng và có đủ nguồn lực để triển khai.

## 3. Mỗi k chia khách hàng thành những nhóm nào

![Thành phần nhóm theo k](../../data/processed/customer_segmentation/plots/k_selection_composition.png)

### k = 3 (gợi ý)

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 0 | Champions | 24.9% | 63.0% | 201 | 14 | 340,703 |
| 2 | Trung thành | 37.0% | 30.7% | 977 | 5 | 108,472 |
| 1 | Ngủ đông | 38.1% | 6.3% | 2,165 | 1 | 20,306 |

### k = 4

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Champions | 15.4% | 42.1% | 125 | 15 | 367,444 |
| 2 | Trung thành | 24.3% | 39.5% | 595 | 9 | 216,897 |
| 3 | Ngủ đông | 31.6% | 14.9% | 1,333 | 3 | 66,978 |
| 0 | Đã rời bỏ | 28.7% | 3.5% | 2,392 | 1 | 14,546 |

### k = 5

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 0 | Champions | 14.1% | 43.6% | 149 | 17 | 421,487 |
| 2 | Trung thành | 21.7% | 34.9% | 659 | 9 | 219,127 |
| 4 | Ngủ đông | 28.5% | 13.1% | 1,650 | 3 | 64,500 |
| 3 | Khách mới / tiềm năng | 10.2% | 5.7% | 206 | 4 | 80,930 |
| 1 | Đã rời bỏ | 25.5% | 2.6% | 2,391 | 1 | 12,788 |

### k = 6

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Trung thành | 17.9% | 49.5% | 247 | 16 | 375,932 |
| 2 | Trung thành (2) | 20.5% | 23.3% | 998 | 7 | 158,576 |
| 5 | Champions | 4.2% | 10.6% | 31 | 14 | 319,249 |
| 0 | Ngủ đông | 26.9% | 9.3% | 1,888 | 2 | 47,456 |
| 4 | Khách mới / tiềm năng | 11.2% | 5.9% | 248 | 3 | 74,252 |
| 3 | Đã rời bỏ | 19.3% | 1.4% | 2,421 | 1 | 9,498 |

### k = 7

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 4 | Trung thành | 13.7% | 41.8% | 195 | 17 | 418,235 |
| 2 | Trung thành (2) | 16.4% | 26.6% | 660 | 10 | 229,406 |
| 3 | Có nguy cơ rời bỏ | 19.7% | 12.4% | 1,400 | 4 | 90,624 |
| 5 | Champions | 3.2% | 7.6% | 19 | 13 | 294,527 |
| 1 | Ngủ đông | 23.8% | 5.5% | 2,100 | 1 | 31,397 |
| 0 | Khách mới / tiềm năng | 10.2% | 5.5% | 225 | 4 | 76,053 |
| 6 | Đã rời bỏ | 13.1% | 0.6% | 2,427 | 1 | 6,567 |

### k = 8

| Cụm | Tên gợi ý | % khách | % doanh thu | Recency (ngày) | Frequency | Monetary |
|---:|---|---:|---:|---:|---:|---:|
| 0 | Trung thành | 10.8% | 37.5% | 204 | 20 | 483,613 |
| 7 | Trung thành (3) | 13.8% | 23.8% | 793 | 10 | 245,312 |
| 6 | Có nguy cơ rời bỏ | 19.8% | 12.6% | 1,367 | 4 | 91,849 |
| 2 | Trung thành (2) | 10.5% | 11.5% | 215 | 7 | 160,290 |
| 4 | Champions | 3.0% | 7.0% | 17 | 13 | 295,445 |
| 5 | Ngủ đông | 22.7% | 5.4% | 2,183 | 1 | 32,116 |
| 1 | Khách mới / tiềm năng | 7.0% | 1.8% | 309 | 2 | 34,478 |
| 3 | Đã rời bỏ | 12.6% | 0.6% | 2,467 | 1 | 6,540 |

## 4. Bước tiếp theo

```bash
python customer_segmentation/05_kmeans_segmentation.py --k 3
python customer_segmentation/06_cluster_profiling.py
```
