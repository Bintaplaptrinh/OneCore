# Project: HaiVo LeadsMap (LLM-RAG)

Đây là hệ thống quản lý dữ liệu dự án và danh bạ khách hàng dựa trên Obsidian.

## Quy tắc chung
- **Nền tảng:** Sử dụng Obsidian với các tính năng như internal links `[[link]]`, DataView fields (`Key:: Value`), và YAML frontmatter.
- **Ngôn ngữ:** Hỗ trợ song ngữ Tiếng Việt và Tiếng Anh (ưu tiên Tiếng Việt cho ghi chú).

## Quy tắc Dữ liệu Nâng cao (Refined by Claude & Gemini)

### 1. Xử lý Thực thể & Liên kết (Entity Linking)
- **Phương pháp Hybrid:** Ưu tiên bảng ánh xạ (Mapping Table) cho các thực thể đã biết (ví dụ: `Coteccons` -> `mc-CTD`). 
- **Chuẩn hóa (Normalization):** Với thực thể mới, script sẽ loại bỏ dấu tiếng Việt, ký tự đặc biệt và dùng PascalCase (ví dụ: `Gamuda Land` -> `client-GamudaLand`).
- **Phân loại:** Prefix (`client-`, `mc-`, `consultant-`) phải dựa trên cột "Role/Category" trong dữ liệu nguồn.

### 2. Chiến lược Chống trùng lặp (Deduplication)
- Trước khi tạo file mới, script phải kiểm tra sự tồn tại của file trong folder đích.
- **Quy tắc:** Nếu file đã tồn tại, script sẽ KHÔNG ghi đè (để bảo vệ các chỉnh sửa thủ công của người dùng), mà sẽ ghi nội dung mới vào một file `.log` hoặc `.tmp` để người dùng đối soát.

### 3. Quy tắc Đặt tên file & Cấu trúc (Finalized)
- **Định dạng:** BẮT BUỘC dùng dấu ngoặc Obsidian trong tên file (vd: `2026 - [[prj-TênDựÁn]].md`). 
- **Lý do:** Đảm bảo tính native của Obsidian và sự nhất quán với 320+ file hiện có.
- **Xử lý kỹ thuật:** Script Python phải dùng string quoting để xử lý các ký tự đặc biệt trong tên file.

### 4. Hệ thống Cache & Nhất quán
- **Performance:** Dùng **SQLite** làm lớp Cache layer để gộp bảng (Aggregation) tốc độ cao. Markdown vẫn là Source of Truth.
- **Link Registry:** Duy trì một file JSON mapping để quản lý Slugs và Wiki-links, được khởi tạo từ thư mục `2_contacts`.

## Cấu trúc Dữ liệu
... (giữ nguyên phần cũ) ...
### 1. Projects (Dự án)
- **Vị trí:** `HaiVo LeadsMap/1_project/`
- **Định dạng tên file:** `2026 - [[prj-TênDựÁn]].md`
- **Cấu trúc mẫu:**
  - Tag: `tags: [project]`
  - Các trường quan trọng: `type`, `location`, `developer`, `segment`, `site`, `scale`, `timeline`, `stakeholders`, `contractors`.
  - Sử dụng block code ```crm``` cho các tính năng quản lý CRM.

### 2. Contacts (Danh bạ)
- **Vị trí:** `HaiVo LeadsMap/2_contacts/`
- **Định dạng tên file:** `Tên Người_Công Ty.md`
- **Cấu trúc mẫu:**
  - Tag: `tags: [contacts]`
  - Fields: `Company::`, `Role::`, `Email::`, `Phone::` (định dạng DataView).
  - Có phần `## Project` và `## Contact Notes`.

## Ưu tiên hỗ trợ
- Khi xử lý dữ liệu từ thư mục `LeadsMap_Input Information`, cần phân loại và chuyển đổi thành file Markdown đúng định dạng vào thư mục `1_project` hoặc `2_contacts`.
- Luôn giữ tính nhất quán trong việc sử dụng link `[[...]]` để duy trì đồ thị liên kết (Graph View) trong Obsidian.

---
*File này được tạo tự động bởi Gemini CLI để lưu trữ ngữ cảnh dự án.*
