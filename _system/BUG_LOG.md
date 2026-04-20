# 🐛 BUG LOG — HaiVo LeadsMap
**Cập nhật liên tục trong quá trình build**

---

## Format ghi bug mới:
```
### [YYYY-MM-DD] BUG-XXX: Tên bug ngắn gọn
- **Mô tả:** Chuyện gì xảy ra
- **Tái hiện:** Bước nào dẫn đến bug
- **Root cause:** Tại sao xảy ra
- **Fix:** Sửa bằng cách nào
- **File:** path/to/file.py : dòng bao nhiêu
- **Status:** ✅ Fixed | ⏳ Pending | 🔍 Investigating
```

---

## ✅ ĐÃ FIX

### [2026-04-12] BUG-001: UnicodeEncodeError khi print tiếng Việt ra console
- **Mô tả:** Chạy `excel_to_md.py` → crash ngay khi print tên dự án có dấu
- **Tái hiện:** `python excel_to_md.py` trên Windows terminal (cp1252)
- **Root cause:** Python Windows dùng encoding cp1252 mặc định, không hỗ trợ ký tự UTF-8 tiếng Việt
- **Fix:** Wrap stdout: `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`
- **File:** `pipeline/excel_to_md.py` : line 8
- **Status:** ✅ Fixed

---

### [2026-04-12] BUG-002: OSError — Invalid argument — Tên file có ký tự `:` trên Windows
- **Mô tả:** Script tạo contact file → crash với `OSError: [Errno 22] Invalid argument`
- **Tái hiện:** Khi stakeholder có role `"Kỹ Sư Cơ Điện:"` → dấu `:` vào tên file → Windows từ chối
- **Root cause:** Windows không cho phép các ký tự `\ / : * ? " < > |` trong tên file
- **Fix:** `filename = re.sub(r'[\\/:*?"<>|]', '', filename)` trước khi tạo file
- **File:** `pipeline/excel_to_md.py` — hàm `create_contact_file()` : line 154
- **Status:** ✅ Fixed

---

### [2026-04-12] BUG-003: Stakeholder parser bỏ sót người không có công ty
- **Mô tả:** Format `"; Bà Trần Thị Phương Thảo - Project Executive"` (sau dấu `;`, không có tên công ty trước) → bị parse nhầm thành company thay vì person
- **Tái hiện:** Cell Excel có nhiều người trong cùng vai trò, người thứ 2 trở đi không lặp lại tên công ty
- **Root cause:** Regex chỉ xử lý format `"Company, Ông X - Role"`, không có case `"Bà X - Role"` đứng đầu
- **Fix:** Thêm regex `title_start` để catch format bắt đầu bằng `Ông/Bà/Anh/Chị/Mr./Ms.`
- **File:** `pipeline/stakeholder_parser.py` : line 139-151
- **Status:** ✅ Fixed

---

### [2026-04-12] BUG-004: `@radix-ui/react-badge` không tồn tại trên npm
- **Mô tả:** `npm install` fail — package `@radix-ui/react-badge@^1.0.0` không có trên registry
- **Root cause:** Badge không phải là component riêng của Radix UI — dùng inline CSS class thay thế
- **Fix:** Xóa `@radix-ui/react-badge` khỏi package.json, dùng CSS class `.badge` tự viết
- **File:** `app/frontend/package.json`
- **Status:** ✅ Fixed

### [2026-04-12] BUG-005: `next.config.ts` không được Next.js 14.2 hỗ trợ
- **Mô tả:** Build fail — `Configuring Next.js via 'next.config.ts' is not supported`
- **Root cause:** Next.js 14.2 chỉ hỗ trợ `next.config.js` hoặc `next.config.mjs`
- **Fix:** Đổi tên file sang `next.config.mjs` và dùng ES module syntax (`export default`)
- **File:** `app/frontend/next.config.mjs`
- **Status:** ✅ Fixed

## ⏳ ĐANG THEO DÕI

*(Thêm vào đây khi phát hiện bug mới)*

---

## 📊 THỐNG KÊ

| Giai đoạn | Tổng bug | Đã fix | Còn lại |
|-----------|---------|--------|---------|
| Phase 0 — Pipeline | 3 | 3 | 0 |
| Phase 1 — Dashboard | 0 | 0 | 0 |
| Phase 2 — AI/Graph | 0 | 0 | 0 |
| Phase 3 — Upload | 0 | 0 | 0 |
| Phase 4 — Deploy | 0 | 0 | 0 |
| **Tổng** | **3** | **3** | **0** |
