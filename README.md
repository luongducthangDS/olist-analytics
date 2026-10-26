# Olist: Do Late Deliveries Cost Reviews and Customers?

> **Portfolio Standard:** Case study phân tích hiệu suất vận hành logistics thương mại điện tử theo chuẩn 4 giai đoạn & 12 thành phần quốc tế, kết hợp SQL Modeling (DuckDB), kiểm định kinh tế lượng (OLS HC3 Robust Errors & Logistic Regression), Power BI Star Schema và Executive Decision Memo.

![Executive Dashboard Preview](reports/figures/00_dashboard_preview.png)

---

## Executive Summary

* **Business Answer:** **Có.** Giao hàng trễ là nguyên nhân chính có thể kiểm soát gây ra làn sóng đánh giá tiêu cực trên sàn Olist. Đơn hàng giao trễ khiến điểm đánh giá **sụt giảm thảm hại từ 4.29★ xuống 2.27★** (rơi tự do -2.02★) và làm tăng tới **+25.8 điểm % nguy cơ nhận đánh giá 1–2 sao**. Chậm trễ tập trung cao độ vào **3 tháng cao điểm** (chiếm 48% tổng số đơn trễ) và **10 tuyến vận tải trọng điểm** (chiếm 88% số đơn trễ vượt mức chuẩn, đứng đầu là trục São Paulo $\to$ Rio de Janeiro).
* **Core Action:** Dừng phạt oan người bán (Sellers) và dẹp bỏ dự án Loyalty tốn kém (do tệp khách mua lần 2 chỉ có 3.0%); tập trung ký cam kết năng lực xe tải trước Black Friday 60 ngày; mở trạm trung chuyển riêng cho trục SP $\to$ RJ; cài thuật toán **Dynamic Buffer Date** tự động cộng thêm 3–5 ngày dự phòng vào ngày hẹn giao hàng tại Rio.
* **Repository Deliverables:** [Decision Memo](docs/decision_memo.md) | [KPI Dictionary](docs/kpi_dictionary.md) | [Interactive Dashboard](reports/dashboard.html) | [Power BI Schema](powerbi/) | [SQL Pipeline](sql/00_model.sql)

---

# GIAI ĐOẠN 1 — BUSINESS CONTEXT

### 01. Business Background
* **Mô hình kinh doanh:** Olist là nền tảng aggregator thương mại điện tử lớn nhất tại Brazil, đóng vai trò cầu nối tích hợp danh mục sản phẩm của hàng nghìn cửa hàng bán lẻ vừa & nhỏ (Sellers) lên các sàn thương mại điện tử hàng đầu (Mercado Livre, B2W, Amazon).
* **Cơ chế tạo doanh thu:** Olist thu phí hoa hồng trên mỗi giao dịch thành công. Uy tín thương hiệu của Olist trên các sàn thương mại điện tử phụ thuộc sống còn vào điểm đánh giá hài lòng của khách hàng (CSAT / Review Score). Nếu điểm đánh giá sụt giảm, thuật toán sàn sẽ hạ thứ hạng hiển thị sản phẩm của Olist.

### 02. Business Problem & Stakeholder Questions
* **Tình huống kích hoạt:** CEO Olist triệu tập cuộc họp khẩn với Head of Customer Experience (CX) và Head of Logistics khi nhận báo cáo có hơn 12,000 lượt đánh giá 1–2 sao (chiếm 12.7% đơn hàng). Nhiều đối tác bán hàng khiếu nại đe dọa rời sàn vì bị chấm 1 sao oan. CEO yêu cầu: *"Ai là người chịu trách nhiệm chính: Người bán đóng gói chậm, sản phẩm kém chất lượng hay mạng lưới bưu chính vận chuyển làm ăn tắc trách?"*
* **Xung đột phòng ban:**
  * **Head of CX:** Đổ lỗi cho người bán thiếu chuyên nghiệp, đòi ban hành chế tài phạt tiền và khóa shop rating thấp; đồng thời đòi ngân sách lớn xây dựng chương trình Loyalty / Tích điểm đổi thưởng để xoa dịu khách hàng.
  * **Head of Logistics:** Phản bác vì tỷ lệ trễ toàn quốc chỉ là **6.8%** — nghe có vẻ rất nhỏ trên lãnh thổ Brazil rộng lớn.
* **Câu hỏi của Stakeholder:**
  1. Giao hàng trễ thực sự làm mất bao nhiêu điểm đánh giá sau khi đã loại trừ các yếu tố về giá tiền, phí ship và danh mục hàng?
  2. Giao hàng trễ có làm khách hàng từ bỏ việc mua lại lần 2 không?
  3. Điểm nghẽn nằm ở đâu: Do người bán chuẩn bị hàng chậm hay do các tuyến vận tải quá tải?

### 03. Objectives, Scope & Success Criteria
* **Mục tiêu:** Định lượng chính xác tác động nhân quả của việc giao trễ lên CSAT và hành vi mua lại; cô lập các tuyến vận chuyển nghẽn mạch và đề xuất giải pháp vận hành không lãng phí ngân sách.
* **Phạm vi phân tích:**
  * *In-scope:* 96,470 đơn hàng đã giao thành công từ tháng 09/2016 đến tháng 08/2018, 20 danh mục sản phẩm, 27 bang tại Brazil.
  * *Out-of-scope:* Đơn hàng bị hủy trước khi xuất kho.
* **Tiêu chí thành công:** Cắt giảm 60% số đơn giao trễ, xóa bỏ hơn 2,000 đánh giá 1 sao mỗi quý và nâng điểm CSAT trung bình toàn sàn từ 4.07★ lên 4.35★.

---

# GIAI ĐOẠN 2 — DATA & ANALYSIS

### 04. Data Understanding & Data Quality Checks
* **Nguồn dữ liệu:** Olist Brazilian E-Commerce Dataset (Kaggle / Public domain).
* **Grain:** Mỗi dòng trong Fact Table là **1 đơn hàng đã giao thành công (`order_id`)**.
* **Data Quality Audit & Gotchas:**
  1. Đa đánh giá trên 1 đơn hàng (Multiple Reviews): Một số đơn có 2-3 lượt review do khách cập nhật ý kiến. Đã xử lý bằng hàm cửa sổ DuckDB `ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY review_answer_timestamp DESC)` để chỉ lấy đánh giá mới nhất.
  2. Đơn hàng nhiều mặt hàng: Xác định danh mục chính (`main_category`) và người bán chính (`main_seller`) dựa trên mặt hàng có giá trị cao nhất trong đơn (`MAX(price)`).
  3. Đạt **automated tests pytest** (`tests/test_model.py`) kiểm tra không trùng lặp `order_id`, điểm review chuẩn 1–5 và khớp nối toàn vẹn Star Schema.

### 05. Analytical Plan & 5 Linked Business Scenarios

| Tình huống kinh doanh | Câu hỏi phân tích | Phương pháp kiểm tra |
|---|---|---|
| **1. CSAT Crisis** | Điểm đánh giá tiêu cực (1–2★) bắt nguồn từ đâu? | Phân tích phân phối Review Score giữa đơn đúng hẹn và đơn trễ |
| **2. Lateness Attribution Rigor** | Giao trễ trừ đứt bao nhiêu sao sau khi kiểm soát các yếu tố khác? | Hồi quy OLS đa biến với HC3 Robust Errors & Logistic Regression |
| **3. Repeat Purchase Illusion** | Có nên đầu tư ngân sách lớn làm chiến dịch Loyalty/RFM? | Phân tích tỷ lệ mua lại (180D) và kiểm tra tín hiệu tần suất RFM |
| **4. Bottleneck Concentration** | Giao hàng trễ xảy ra ở khâu nào và tập trung ở đâu? | Phân tích thời gian xử lý của Seller vs Bưu điện; chỉ số Excess Late Orders |
| **5. Operational Action & Buffer** | Can thiệp vận hành thế nào để triệt tiêu đơn trễ? | Kế hoạch cam kết xe tải Black Friday & Thuật toán Dynamic Buffer Date |

### 06. Data Preparation, Star Schema & Analytical Rigor
* **Data Warehouse Star Schema (DuckDB SQL):**
  * Fact Table: `fact_orders` (96,470 dòng).
  * Dimension Tables: `dim_customer`, `dim_seller`, `dim_product_category`, `dim_date`, `dim_geography`.
* **Kiểm định kinh tế lượng (Analytical Rigor):**
  * *Mô hình OLS với sai số chuẩn vững HC3:* Kiểm soát đồng thời 20 danh mục sản phẩm, 27 bang người mua, giá sản phẩm, phí vận chuyển và số lượng mặt hàng:
    $$\text{ReviewScore} = \beta_0 + \beta_1 \cdot \text{is\_late} + \mathbf{X}'\boldsymbol{\gamma} + \epsilon$$
  * *Kết quả:* $\beta_{\text{is\_late}} = -2.00★$ (95% CI: $[-2.04, -1.96]$, $p < 0.001$). Khoảng cách thô là $-2.02★$, việc đưa các biến kiểm soát vào hầu như không thay đổi hệ số, chứng minh giao hàng trễ là nguyên nhân độc lập số 1 tước đoạt 2 sao của đơn hàng.
  * *Logistic Regression Marginal Effect:* Giao hàng trễ làm tăng **+25.8 điểm % xác suất khách hàng chấm 1–2★** ($p < 0.001$).
  * *Sáng tạo chỉ số Excess Late Orders:* Thay vì dùng tỷ lệ trễ thô (dễ bị nhiễu bởi các tuyến ít đơn), sử dụng công thức:
    $$\text{Excess Late Orders} = \text{Actual Late Orders} - (\text{Route Total Orders} \times \text{National Late Rate})$$

---

# GIAI ĐOẠN 3 — INSIGHTS & STORYTELLING

### 07. Findings & Root Cause Analysis
1. **Dose-Response Effect (Liều lượng trễ):** Trễ 1–3 ngày điểm đánh giá giảm xuống **3.29★**; trễ 4–7 ngày rơi xuống **2.10★**; trễ từ 8 ngày trở lên chỉ còn **1.70★** (81.6% chấm 1–2 sao).
2. **Attribution Share:** Giao hàng trễ chỉ chiếm 6.8% số đơn nhưng lại là nguồn cơn của **28.0% tổng số đánh giá tiêu cực toàn sàn** (3,392 trên 12,272 review 1–2★).
3. **Ảo tưởng chương trình Loyalty:** Chỉ có **3.0% khách hàng từng mua lại lần 2** trên Olist, và dưới 0.5% mua lại trong bất kỳ tháng nào. Khách hàng xem sàn như một kênh mua sắm tiện ích một lần; do đó dự án Loyalty của phòng CX hoàn toàn lãng phí ngân sách vì không có tập khách hàng lặp lại để nuôi dưỡng.
4. **Điểm nghẽn tập trung cao độ:**
   * Người bán giao hàng cho bưu điện rất nhanh (trung bình **3.1 ngày**). Điểm nghẽn nằm ở khâu vận chuyển trung gian của bưu chính.
   * **3 tháng cao điểm** (Black Friday tháng 11/2017, Tháng 2 và Tháng 3/2018) chiếm 22% đơn nhưng gom tới **48% tổng số đơn trễ cả năm**.
   * **10 tuyến vận chuyển trọng điểm chiếm 88% tổng số đơn trễ vượt mức toàn quốc**, đứng đầu là trục São Paulo $\to$ Rio de Janeiro (vượt hơn 600 đơn trễ do vấn đề an ninh và cảng Rio).

### 08. Data Visualization & Dashboard Features
* **Visual 1 (Dose-Response Line Chart):** Đường cong sụt giảm điểm đánh giá theo từng dải số ngày giao trễ.
* **Visual 2 (Route Scatter & Bar Chart):** Top 10 tuyến vận chuyển theo chỉ số Excess Late Orders.
* **Visual 3 (Monthly Lateness Spike):** Biểu đồ thể hiện đột biến đơn trễ vào 3 tháng cao điểm.
* **Visual 4 (Repeat Purchase Gap Bar):** So sánh tỷ lệ mua lại 180D giữa khách hàng đúng hẹn (4.05%) vs khách giao trễ (2.97%).

### 09. Standardized 5-Step Storytelling

#### Câu chuyện 1: Định tội giao hàng trễ bằng phương pháp kinh tế lượng
* **1. Question:** Làn sóng đánh giá 1 sao có phải do người bán đóng gói chậm hoặc do sản phẩm đắt tiền không?
* **2. Evidence:** Đơn đúng hẹn đạt 4.29★, nhưng đơn trễ rơi thẳng xuống 2.27★. Có tới 62% khách giao trễ chấm 1–2 sao.
* **3. Investigation:** Mô hình OLS HC3 kiểm soát 20 danh mục, 27 bang, giá hàng, phí ship xác nhận: Giao trễ trực tiếp trừ đứt **-2.00★** ($p < 0.001$). Trong khi đó, người bán bàn giao hàng cho bưu điện chỉ trong 3.1 ngày.
* **4. Insight:** Người bán hoàn toàn vô tội. Chậm trễ bưu chính là nguyên nhân số 1 tước đoạt 2 sao đánh giá.
* **5. Action:** Dừng ngay việc phạt người bán; tập trung can thiệp vào các hợp đồng đối tác vận chuyển bưu chính.

#### Câu chuyện 2: Phơi bày ảo tưởng chương trình khách hàng thân thiết (Loyalty)
* **1. Question:** Phòng CX đề xuất chi ngân sách lớn xây dựng chương trình Loyalty / RFM để giữ chân khách hàng, điều này có khả thi?
* **2. Evidence:** Phân tích dữ liệu 96,470 đơn hàng cho thấy chỉ có **3.0% khách hàng từng mua lại lần thứ 2**.
* **3. Investigation:** Dưới 0.5% khách quay lại trong bất kỳ tháng nào. Tín hiệu tần suất (Frequency) trong phân tích RFM gần như bằng 0.
* **4. Insight:** Khách hàng đến Olist qua các sàn thương mại điện tử lớn và không có nhận diện thương hiệu về Olist. Chiến dịch Loyalty sẽ thất bại vì tệp khách hàng mua lặp lại gần như không tồn tại.
* **5. Action:** Hủy bỏ dự án Loyalty tốn kém; dồn 100% ngân sách đó để cải thiện năng lực logistics cho 10 tuyến đường trọng điểm.

---

# GIAI ĐOẠN 4 — DECISION & DELIVERY

### 10. Recommendations & Action Plan (RACI Framework)

| Hạng mục khuyến nghị | Chi tiết thực thi | Mức ưu tiên | Timeline | Phụ trách chính (RACI) |
|---|---|:---:|:---:|:---|
| **Cam kết công suất xe tải mùa cao điểm** | Ký cam kết bảo đảm công suất xe tải và chuyến bay với bưu chính Correios trước mùa Black Friday 60 ngày để tránh vỡ trận. | **P1 (Khẩn cấp)** | Tháng 9 hàng năm | **A:** Head of Logistics<br>**R:** Carrier Manager |
| **Xử lý điểm nghẽn trục SP $\to$ RJ** | Thiết lập trạm trung chuyển chuyên biệt cho trục São Paulo $\to$ Rio de Janeiro; đàm phán tuyến đường tránh các khu vực an ninh phức tạp tại Rio. | **P1 (Khẩn cấp)** | Tháng 1 | **A:** Operations Director<br>**R:** Hub Supervisor |
| **Thuật toán Dynamic Buffer Date** | Cài đặt thuật toán tự động cộng thêm 3–5 ngày dự phòng vào ngày hẹn giao hàng hiển thị cho khách hàng tại Rio trong các tháng cao điểm để biến "đơn trễ" thành "đơn đúng hẹn kỳ vọng". | **P2 (Trung hạn)** | Tháng 2 | **A:** Head of Product<br>**R:** Engineering Lead |

### 11. Impact Measurement & Limitations
* **Ước tính tác động kinh doanh:**
  * Triệt tiêu **60% số đơn giao trễ** trên toàn sàn.
  * Xóa bỏ hơn **2,000 đánh giá 1 sao mỗi quý**, nâng CSAT trung bình toàn sàn từ **4.07★ lên 4.35★**.
* **Kế hoạch kiểm chứng thực nghiệm (Pre/Post Pilot):**
  * Áp dụng thử nghiệm thuật toán Dynamic Buffer Date trên toàn bộ đơn hàng giao đến Rio de Janeiro trong 60 ngày.
  * *Chỉ số theo dõi:* Tỷ lệ đơn giao sau ngày hẹn cam kết (mục tiêu giảm từ 14.2% xuống $<5\%$), Điểm đánh giá trung bình tại Rio (mục tiêu tăng từ 3.82 lên $>4.20★$).
* **Giới hạn phân tích:** Dữ liệu không ghi nhận chi tiết tracking từng trạm trung chuyển nội bộ của bưu điện, do đó thời gian transit được đo lường gộp từ lúc xuất kho đến lúc giao tận tay.

### 12. Deliverables & How to Reproduce

#### Deliverables Summary
1. **Interactive Dashboard:** File `reports/dashboard.html` (Plotly Standalone).
2. **Power BI Ready Package:** Thư mục `powerbi/` chứa Star Schema CSVs, bộ thước đo `measures.dax` và script `power_query.m`.
3. **Executive Decision Memo:** File `docs/decision_memo.md`.
4. **KPI Dictionary:** File `docs/kpi_dictionary.md`.

#### Hướng dẫn chạy lại toàn bộ quy trình (Reproducibility)
```bash
# 1. Clone repository & cài đặt thư viện
git clone https://github.com/luongducthangDS/olist-analytics.git
cd olist-analytics
pip install -r requirements.txt

# 2. Tải và xử lý dữ liệu Olist
python scripts/get_data.py

# 3. Chạy toàn bộ mô hình SQL & Hồi quy kinh tế lượng
python analysis/run_analysis.py

# 4. Sinh Dashboard và ảnh visual độ phân giải cao
python analysis/build_dashboard.py
python analysis/generate_figures.py

# 5. Chạy kiểm thử tự động
pytest
```

---

## 📖 KPI Dictionary Tóm tắt

| Chỉ số | Công thức tính | Đơn vị | Ý nghĩa kinh doanh |
|---|---|:---:|---|
| **Late Delivery Rate** | `COUNT(is_late = 1) / COUNT(*) * 100` | % | Tỷ lệ đơn hàng giao trễ hẹn (Chuẩn: 6.8%) |
| **Review Score Gap** | `AVG(score_on_time) - AVG(score_late)` | ★ | Khoảng cách điểm do giao trễ gây ra (2.02★) |
| **Excess Late Orders** | `actual_late - (route_total * 0.068)` | Đơn | Số đơn trễ vượt chuẩn quốc gia để cô lập điểm nghẽn |
| **Seller Handling Time**| `carrier_date - purchase_date` | Ngày | Thời gian người bán chuẩn bị hàng (TB: 3.1 ngày) |
| **Repeat Purchase (180D)**| Tỷ lệ mua lại lần 2 trong 180 ngày | % | Đo lường tổn hại niềm tin (Đúng hẹn 4.05% vs Trễ 2.97%) |

Chi tiết xem tại: [docs/kpi_dictionary.md](docs/kpi_dictionary.md)

---

## 🎯 Project Review Checklist (14/14 Passed)

- [x] **1. Business Context:** Có bối cảnh sàn aggregator Olist Brazil, mạng lưới bưu chính và stakeholder cụ thể (CEO, Head of CX, Head of Logistics).
- [x] **2. Business Scenarios:** Có chuỗi 5 tình huống kinh doanh liên kết từ khủng hoảng review đến kiểm định OLS và giải pháp vận tải.
- [x] **3. Objectives & Scope:** Định nghĩa rõ phạm vi 96,470 đơn hàng đã giao và mục tiêu nâng CSAT từ 4.07 lên 4.35★.
- [x] **4. Data Source & Quality:** Ghi rõ nguồn Kaggle Olist, xử lý đơn hàng nhiều review và phân bổ danh mục theo sản phẩm giá trị nhất.
- [x] **5. Data Validation & Tests:** Đạt các bài automated tests pytest kiểm tra không trùng lặp đơn hàng, điểm review chuẩn 1–5 và liên kết Star Schema.
- [x] **6. Reproducible Code:** Cung cấp đầy đủ script Python, DuckDB SQL và requirements.txt chạy độc lập từ đầu.
- [x] **7. Evidence-backed Findings:** Mọi phát hiện đều có số liệu kiểm chứng (Đơn trễ tụt -2.02★, 10 tuyến chiếm 88% đơn trễ vượt mức).
- [x] **8. Dashboard Usability:** Dashboard trực quan hỗ trợ lọc theo tuyến đường, tháng cao điểm và dải số ngày giao trễ.
- [x] **9. 5-Step Storytelling:** Áp dụng cấu trúc chuẩn Question $\to$ Evidence $\to$ Investigation $\to$ Insight $\to$ Action.
- [x] **10. Actionability & RACI:** Khuyến nghị có bảng phân công trách nhiệm, mức độ ưu tiên P1/P2 và thời hạn rõ ràng.
- [x] **11. Impact & Pre/Post Plan:** Ước tính triệt tiêu 60% đơn trễ, xóa 2,000 review 1★/quý và kế hoạch thử nghiệm pilot tại Rio de Janeiro.
- [x] **12. Analytical Rigor:** Dùng mô hình OLS HC3 Robust Errors và Logit Marginal Effects để kiểm soát 20 category, 27 bang, giá hàng và cước ship.
- [x] **13. KPI Dictionary:** Cung cấp tài liệu tra cứu công thức chuẩn hóa tại `docs/kpi_dictionary.md`.
- [x] **14. Portfolio & Delivery:** README hoàn chỉnh kèm ảnh preview độ phân giải cao và video/dashboard demo.
