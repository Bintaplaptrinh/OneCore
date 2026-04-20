# 📄 Technical Brief: HaiVo LeadsMap Demo (Giai đoạn 0)

## 🎯 Mục tiêu
Xây dựng một bản Demo chạy trên PC (Streamlit) thể hiện sức mạnh của hệ thống RAG + CRM đa chức năng.

## 👥 Đối tượng & Giao diện (UX/UI)
1. **Thiết bị:** Ưu tiên hiển thị trên PC (Bảng biểu rộng), nhưng code phải linh hoạt để sau này chuyển sang Mobile (Responsive).
2. **Vai trò (Roles):**
   - **Director/Manager:** Xem bảng tổng hợp, biểu đồ liên kết, xuất báo cáo.
   - **Sales:** Tìm kiếm dự án, danh bạ, tra cứu lịch sử qua chatbot.
   - **Client (View only):** Xem thông tin dự án công khai.

## 📂 Dữ liệu & Xử lý (Data Pipeline)
- **Nguồn:** Hỗ trợ song song **Excel** (Dữ liệu bảng) và **PDF/Ảnh** (Tài liệu dự án, Namecard).
- **Kỹ thuật:** 
  - OCR/LlamaIndex để "đọc" nội dung từ PDF/Ảnh.
  - Entity Mapping để tự động tạo links `[[...]]` trong Obsidian.

## 📊 Tính năng Bảng biểu & Xuất dữ liệu (Dynamic Tables & Export)
- **Yêu cầu:** Hệ thống phải có khả năng tự gộp (Aggregate) dữ liệu từ nhiều file Markdown dựa trên các liên kết `[[link]]`.
- **Ví dụ:** Liệt kê tất cả dự án có chung nhà thầu `[[mc-CTD]]` vào một bảng.
- **Export:** Cho phép người dùng nhấn nút "Export to Excel/Word" để tải bảng dữ liệu đó về máy.

## 🚩 Yêu cầu cho Kỹ sư (Claude):
1. **Phân tích kỹ thuật:** Làm sao để thực hiện việc "gộp bảng" (Data Aggregation) từ các file Markdown một cách hiệu quả nhất?
2. **Lộ trình Demo:** Trong 24h tới, anh có thể build một trang Streamlit đơn giản có Chatbot hỏi đáp + 1 Bảng tổng hợp dự án từ 3 file Excel đã import không?
3. **Phản hồi:** Viết phản hồi vào `_system/tasks/ENGINEER_RESPONSE.md`.
