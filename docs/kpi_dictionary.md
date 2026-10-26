# KPI Dictionary: Olist Operations & Delivery Performance

Tài liệu định nghĩa chuẩn hóa các chỉ số đo lường hiệu suất vận hành logistics, mức độ hài lòng khách hàng (CSAT) và tác động hành vi mua sắm trên sàn thương mại điện tử Olist Brazil.

---

## 1. Bảng tra cứu KPI cốt lõi

| Mã KPI | Tên chỉ số | Công thức tính toán | Đơn vị | Grain / Phạm vi tính | Ý nghĩa kinh doanh & Ngưỡng chuẩn |
|:---|:---|:---|:---:|:---|:---|
| **KPI-01** | **Delivered Orders Volume** | `COUNT(order_id)` với `order_status = 'delivered'` | Đơn hàng | Toàn sàn (09/2016 – 08/2018) | Tổng số đơn hàng được giao thành công tới tay khách. Tổng thể: **96,470 đơn**. |
| **KPI-02** | **Late Delivery Rate %** | `COUNT(orders WHERE is_late = 1) / COUNT(delivered_orders) * 100` | % | Toàn sàn / Tuyến đường / Tháng | Tỷ lệ đơn hàng giao sau ngày cam kết (`delivered_date > estimated_date`). Mức trung bình sàn: **6.8%**. |
| **KPI-03** | **Average Review Score** | `AVG(review_score)` | Điểm ★ (1–5) | Toàn sàn / Phân khúc giao hàng | Điểm đánh giá trung bình từ khách hàng. Benchmark chuẩn: **4.07★**. Đơn đúng hẹn: **4.29★**. Đơn trễ: **2.27★**. |
| **KPI-04** | **Negative Review Share (1–2★)** | `COUNT(reviews <= 2) / COUNT(total_reviews) * 100` | % | Toàn sàn / Phân khúc giao hàng | Tỷ lệ khách hàng cực kỳ thất vọng. Đơn đúng hẹn: **9.0%**. Đơn trễ: **62.0%** (Tăng gấp gần 7 lần!). |
| **KPI-05** | **Lateness Attribution Share** | `(Late Negative Reviews - Expected Negative Reviews) / Total Negative Reviews` | % | Toàn sàn | Tỷ trọng các đánh giá 1–2 sao trực tiếp bắt nguồn từ việc giao hàng trễ. Đạt: **≈ 28.0%**. |
| **KPI-06** | **Excess Late Orders** | `actual_late_orders - (route_total_orders * national_late_rate)` | Đơn hàng | Từng tuyến đường (`origin_state` $\to$ `dest_state`) | Số lượng đơn trễ vượt quá mức chuẩn quốc gia (6.8%). Cho phép cô lập điểm nghẽn thực sự mà không bị nhiễu bởi volume. |
| **KPI-07** | **Seller Handling Time** | `order_delivered_carrier_date - order_purchase_timestamp` | Ngày | Từng đơn hàng / Người bán | Thời gian từ lúc khách chốt đơn đến khi người bán bàn giao hàng cho bưu điện. Trung bình: **3.1 ngày** (Rất tốt). |
| **KPI-08** | **Carrier Transit Time** | `order_delivered_customer_date - order_delivered_carrier_date` | Ngày | Từng đơn hàng / Tuyến đường | Thời gian bưu điện vận chuyển trên đường. Trung bình: **9.4 ngày**. Mùa cao điểm: vọt lên **18–25 ngày**. |
| **KPI-09** | **Repeat Purchase Rate (180D)** | Tỷ lệ khách hàng mua lại lần 2 trong vòng 180 ngày sau đơn hàng đầu tiên | % | Khách hàng giao đúng hẹn vs Khách hàng bị giao trễ | Đo lường tổn hại niềm tin dài hạn. Đơn đúng hẹn: **4.05%** vs Đơn trễ: **2.97%** (Sụt giảm **-27%**, $p = 0.001$). |
| **KPI-10** | **Total Repeat Customers Share** | `COUNT(customers with orders >= 2) / COUNT(total_customers) * 100` | % | Toàn sàn | Tỷ lệ khách hàng từng mua từ 2 lần trở lên trên Olist. Đạt: **3.0%** (RFM segmentation không có tín hiệu tần suất). |

---

## 2. Thống kê liều lượng tác động (Dose-Response of Lateness)

| Số ngày giao trễ | Điểm đánh giá bình quân (★) | Tỷ lệ đánh giá 1–2 sao (%) | Nhận định vận hành |
|---|:---:|:---:|:---|
| **Đúng hẹn hoặc sớm hơn** | **4.29★** | 9.1% | Khách hàng hài lòng, trải nghiệm đạt chuẩn. |
| **Trễ 1 – 3 ngày** | **3.29★** | 35.4% | Bắt đầu mất kiên nhẫn, mức hài lòng giảm 1★. |
| **Trễ 4 – 7 ngày** | **2.10★** | 68.2% | Bức xúc cao độ, đa phần đánh giá 1 sao. |
| **Trễ 8+ ngày** | **1.70★** | 81.6% | Khủng hoảng niềm tin, khiếu nại và đòi hoàn tiền. |

---

## 3. Top Tuyến Vận Tải Có Số Đơn Trễ Vượt Mức (Excess Late Orders)

- **São Paulo (SP) $\to$ Rio de Janeiro (RJ):** 600 đơn trễ vượt mức (Tuyến huyết mạch số 1 bị nghẽn do an ninh và cảng Rio).
- **São Paulo (SP) $\to$ Bahia (BA):** 184 đơn trễ vượt mức (Khoảng cách địa lý lớn, hạ tầng đường bộ miền Đông Bắc).
- **Minas Gerais (MG) $\to$ Rio de Janeiro (RJ):** 122 đơn trễ vượt mức.
- **Top 10 tuyến trọng điểm:** Chiếm **88% tổng số đơn trễ vượt mức toàn quốc**.
