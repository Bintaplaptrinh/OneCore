---
name: leadsmap-expert
description: Chuyên gia quản lý Obsidian Vault cho LeadsMap (BĐS). Dùng để xử lý dữ liệu dự án/danh bạ, tạo script Python RAG, và đảm bảo sự đồng bộ giữa Giám đốc (Gemini) và Kỹ sư (Claude).
---

# LeadsMap Expert Skill

Kỹ năng này cung cấp các quy tắc và quy trình chuẩn để quản lý dự án HaiVo LeadsMap.

## 🏗️ Kiến trúc Hệ thống (Hybrid)
- **Cấu trúc:** Obsidian Vault + Python Automation.
- **Dữ liệu:** File Markdown trong `1_project/` và `2_contacts/`.
- **Logic:** Script Python dùng `openpyxl` để xử lý Excel và `LlamaIndex` cho RAG.

## 🛠️ Quy tắc Kỹ thuật (Từ Kỹ sư Claude)
1. **Xử lý Excel:** Luôn dùng `openpyxl` cho các file quy mô vừa.
2. **Entity Mapping:**
   - Dùng bảng ánh xạ cho thực thể đã biết (ví dụ: `Coteccons` -> `[[mc-CTD]]`).
   - Chuẩn hóa tên mới: Xóa dấu, PascalCase (ví dụ: `Gamuda Land` -> `[[client-GamudaLand]]`).
3. **Chống trùng lặp:** Kiểm tra file tồn tại trước khi tạo. Nếu trùng, tạo file `.tmp` hoặc ghi vào `_system/tasks/conflict.log`.

## 📂 Quy tắc File Obsidian
- **Project:** `2026 - [[prj-Name]].md`, tags `[project]`, có CRM block.
- **Contact:** `Name_Company.md`, tags `[contacts]`, DataView fields (`Company::`, `Role::`).

## 🤝 Quy trình Giao tiếp (Communication Protocol)
1. **Ghi Nhật ký:** Mọi quyết định quan trọng PHẢI được ghi vào `_system/project_log.md`.
2. **Phân vai:** Gemini (Briefing/Context) -> Claude (Coding/Technical Review).
3. **Phản biện:** Trước khi thực thi task phức tạp, Gemini phải gửi "Bản tham vấn" cho Claude và đọc phản hồi từ `ENGINEER_RESPONSE.md`.

## 🚀 Workflow Thực thi Task
1. Đọc `_system/rules/GEMINI.md` và `_system/project_log.md`.
2. Phân loại input từ `LeadsMap_Input Information/`.
3. Soạn "Briefing" cho Claude thực hiện nếu cần code phức tạp.
