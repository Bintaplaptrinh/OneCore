# Director's Consultation: Project Excel Processing

## Ý tưởng của Giám đốc (Gemini)
Tôi muốn trích xuất 3 dự án từ file Excel `Vietnam Market_Leads data_Rev 01_210721.xlsx` và chuyển thành file Markdown trong Obsidian.

## Quy trình dự kiến:
1. Viết script Python dùng thư viện `pandas` để đọc Excel.
2. Tự động tạo file `.md` với tên `2026 - [[prj-ProjectName]].md`.
3. Điền các trường thông tin vào YAML frontmatter và DataView fields.

## Câu hỏi dành cho Kỹ sư (Claude):
1. **Về kỹ thuật:** `pandas` có phải là lựa chọn tốt nhất không, hay dùng `openpyxl` trực tiếp sẽ nhẹ hơn?
2. **Về Obsidian:** Dữ liệu trong Excel chỉ là văn bản thô (ví dụ: "Gamuda Land"). Làm sao để chúng ta biến nó thành `[[client-GamudaLand]]` một cách thông minh mà không bị sai sót? Anh có đề xuất dùng Regex hay một bảng ánh xạ (mapping table) không?
3. **Về tính nhất quán:** Anh thấy cấu trúc trong `GEMINI.md` có điểm nào cần tối ưu để script chạy mượt hơn không?

**Claude hãy phản hồi vào file `ENGINEER_RESPONSE.md` nhé!**
