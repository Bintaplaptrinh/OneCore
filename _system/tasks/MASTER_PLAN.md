# 🗺️ Master Plan: HaiVo LeadsMap - Strategic Intelligence System

## 🏗️ Design Philosophy (Triết lý Thiết kế)
Dựa trên `llm-wiki`, hệ thống phải đảm bảo tính **Liên kết (Linked)**, **Trực quan (Visual)** và **Hành động được (Actionable)**.

## 🛠️ Tech Stack & Implementation
1. **Data Ingestion:** Dùng Gemini 1.5 Multimodal để xử lý Excel + PDF + Image (Namecard).
2. **Knowledge Graph:** Tận dụng `wiki-viewer.html` để hiển thị mạng lưới thực thể.
3. **Data Aggregation:** Viết logic Python để quét Metadata từ Markdown (YAML/DataView) và gộp thành bảng động (Dynamic Tables).
4. **Reporting:** Thư viện `python-docx` hoặc `xlsxwriter` để thực hiện tính năng Export.

## 👥 User Personas (Cách vận hành)
- **Manager:** Sử dụng Dashboard để xem biểu đồ và xuất báo cáo.
- **Admin/Sales:** Cập nhật dữ liệu thô vào folder Input.
- **AI Agent:** Tự động hóa việc "nối các điểm" (Connecting the dots) giữa các file.

## 🚩 Câu hỏi cho Kỹ sư Claude (Engineering Review):
1. **Feasibility:** Việc tích hợp `wiki-viewer.html` (HTML/JS) vào giao diện Streamlit (Python) có gặp rào cản nào về bảo mật hay performance không?
2. **Optimization:** Anh có đề xuất cách nào để việc "Gộp bảng" (Aggregation) diễn ra nhanh nhất khi số lượng file Markdown lên đến hàng nghìn không? (Có nên dùng một Database trung gian như SQLite không?)
3. **Consistency:** Làm sao để đảm bảo các links `[[...]]` do AI tạo ra luôn nhất quán với các file đã có sẵn trong `2_contacts`?
