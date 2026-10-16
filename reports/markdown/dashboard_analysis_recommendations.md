# Phân tích Dashboard và Khuyến nghị

Dashboard Power BI hiện tại: [Ecommerce_Dashboard.pbix](../Phần%202/Ecommerce_Dashboard.pbix).

> 🔄 Dashboard đang được dựng lại trên star schema với 5 trang: Executive Overview, Customer, Sales & Promotion, Inventory, Logistics & Returns. Cấu trúc, mô hình dữ liệu và công thức KPI: [`dashboard/README.md`](../../dashboard/README.md). Insight và hình bên dưới lấy từ bản v1, sẽ được rà soát lại khi bản mới hoàn thành.

## 1. Executive Overview (Tổng quan)

* **Thực trạng**: Doanh nghiệp đạt đỉnh năm 2016 nhưng suy giảm liên tục đến năm 2022 ở các chỉ số KPI chính (doanh thu, đơn hàng, khách hàng).
* **Vấn đề**: Lưu lượng truy cập tăng 63% (2013–2022) nhưng tỷ lệ chuyển đổi (đơn có doanh thu ÷ sessions) giảm từ **1,01% xuống 0,29%**. Chiến lược khách hàng chưa bền vững khi phụ thuộc vào kênh thu hút mới (organic, paid), thiếu các kênh giữ chân (email, referral).

<img width="1488" height="766" alt="Overview dashboard" src="https://github.com/user-attachments/assets/1814c8ac-752b-4912-a6d2-f212edd2646e" />

## 2. Customer (Khách hàng)

* **Điểm nghẽn**: 28% khách đã đăng ký (34.091 người) chưa hoàn tất đơn nào. Khách hàng cũ ít quay lại (Recency cao).
* **Định hướng cải thiện hiện tại**:
  * Tặng ưu đãi 15% + Freeship cho đơn đầu tiên.
  * Gửi Email/Voucher cá nhân hóa sau 24h đăng ký hoặc 30 ngày không mua.
  * Xây dựng hệ thống VIP Tier cho khách chi tiêu trên 2 triệu VNĐ/năm.

<img width="1343" height="691" alt="Customer dashboard" src="https://github.com/user-attachments/assets/c615d1ff-c9a5-4518-bb22-6f4bb8f19bfc" />

## 3. Sales & Promotion (Kinh doanh & khuyến mãi)

* **Thực trạng**: Chi phí cao (15.7 tỷ VNĐ) nhưng lợi nhuận gộp rất thấp (5.1 triệu VNĐ). Streetwear chiếm tới 80% lợi nhuận, gây rủi ro phụ thuộc.
* **Giải pháp**:
  * Thúc đẩy thanh toán trước để giảm rủi ro từ COD.
  * Áp dụng Combo Pricing và Upsell cho nhóm khách hàng chủ lực (25-44 tuổi).
  * Mở rộng danh mục Outdoor và tái định vị dòng Casual hiệu suất thấp.

<img width="1318" height="701" alt="Sales dashboard" src="https://github.com/user-attachments/assets/e6deef96-0416-4d7e-981d-82c9bf4a287c" />

## 4. Inventory (Tồn kho)

* **Vấn đề**: Mất cân bằng cung cầu nghiêm trọng. Chỉ số Days of Supply (DOS) lên tới **826 ngày**. Hàng nhập liên tục vượt nhu cầu thực tế (Ratio 1.15-1.18).
* **Xử lý hàng tồn**:
  * **Ngắn hạn**: Flash sale/Markdown để thu hồi 40-60% vốn.
  * **Trung hạn**: Gói combo (Bundling) hàng tồn với hàng bán chạy.
  * **Dài hạn**: Bán sỉ B2B để giải phóng kho nhanh chóng.

<img width="1309" height="693" alt="Inventory dashboard" src="https://github.com/user-attachments/assets/b3052d26-983c-4ef8-803c-92696d654000" />

## 5. Logistics & Returns (Giao hàng & trả hàng)

* **Thực trạng**: Thời gian giao hàng chậm (khoảng 6 ngày) do khâu vận chuyển. Lý do hoàn trả hàng đầu là **Sai kích thước (Wrong size)**.
* **Cải thiện**:
  * Hợp tác đa đơn vị vận chuyển (Multi-carrier).
  * Cải thiện Size Guide, thêm thông tin chiều cao/cân nặng người mẫu để khách dễ ước lượng.

<img width="1370" height="747" alt="Logistics dashboard" src="https://github.com/user-attachments/assets/0ce22572-ecab-4f8d-9b54-e3e0dfa6bb45" />

## Sau khi hoàn thiện dashboard: Customer Segmentation

Pipeline K-Means được tách riêng trong [`customer_segmentation/`](../customer_segmentation/README.md) để chạy sau khi hoàn thiện dashboard. K-Means chỉ dùng các biến đo lường RFM; nhóm tuổi, giới tính, khu vực và kênh thu hút chỉ dùng để mô tả profile sau phân cụm. Các khuyến nghị theo từng cụm sẽ được xây dựng sau khi xem xét hồ sơ và độ ổn định của cụm; báo cáo này chưa đưa ra khuyến nghị dựa trên cụm.
