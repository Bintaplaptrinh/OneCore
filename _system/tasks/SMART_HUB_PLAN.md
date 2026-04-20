# 🗺️ Master Plan: Smart Hub & Multi-dimensional Linking

## 🏗️ Triết lý Thiết kế (Design Philosophy)
Hệ thống phải mô phỏng lại cấu trúc "Hub & Spoke" của HaiVo LeadsMap Obsidian. Tránh việc liên kết phẳng, ưu tiên các nốt trung tâm (Hubs) và liên kết dựa trên suy luận (Inferred Links).

## 🛠️ Yêu cầu Kỹ thuật cho Claude:
1. **Hub Identification:** 
   - Phân tích file `0_dashboard/Project Matrix.md` để xác định các thực thể "trụ cột".
   - Trong database, đánh dấu trọng số (Weight) cao hơn cho các Hub này để hiển thị to hơn trên Graph.
2. **Contextual Linking (Liên kết theo ngữ cảnh):**
   - Không chỉ nối `[[link]]`. Hãy nối dựa trên **Thuộc tính chung**.
   - Ví dụ: Nối tất cả các dự án có cùng `#segment/luxury` lại với nhau dù chúng không trực tiếp link đến nhau.
3. **Matrix Dashboard:**
   - Xây dựng một View đặc biệt mô phỏng file `Project Matrix.md`.
   - Cho phép người dùng click vào một ô trong ma trận để mở ra danh sách "Liên kết chéo" (vd: Tất cả dự án của Chủ đầu tư X tại Tỉnh Y).
4. **Smart Suggestions:**
   - AI gợi ý: "Tôi thấy 3 dự án này có cùng nhóm tư vấn thiết kế, sếp có muốn nhóm chúng lại thành một cụm không?"

## 🚩 Chỉ thị cho Claude:
Đọc kỹ thư mục `0_dashboard/` để hiểu cách khách hàng tổ chức Ma trận. Nâng cấp logic `get_graph_data` trong `core/db.py` để hỗ trợ "Trọng số nốt" (Node Weighting) và "Liên kết thuộc tính" (Attribute Linking).
