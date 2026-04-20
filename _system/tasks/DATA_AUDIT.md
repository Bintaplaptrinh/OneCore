# 📊 DATA AUDIT REPORT — HaiVo LeadsMap
**Thực hiện bởi:** Claude (Kỹ sư)
**Ngày:** 2026-04-12
**Mục đích:** Xác định nguồn dữ liệu tốt nhất cho Phase 0 Demo

---

## 1. KIỂM KÊ TOÀN BỘ

### A. LeadsMap_Input Information (Raw Input)

| File | Loại | Kích thước | Chất lượng |
|------|------|-----------|-----------|
| `Vietnam Market_Leads_Rev01.xlsx` | Excel | 72 KB | ⭐⭐⭐⭐⭐ TỐT NHẤT |
| `TotalParking_updated.xlsx` | Excel | 38 KB | ⭐⭐⭐ KHÁ (context khác) |
| `SKL_MP13_Project Directory.xlsx` | Excel | ? | ⭐⭐ PHỨC TẠP |
| `Contact point_SKL...pdf` | PDF | 689 KB | ⭐⭐ (cần OCR) |
| `Ban ve du an.pdf` | PDF | 25 MB | ❌ BẢN VẼ KỸ THUẬT |
| `NameCard.jpg` | Ảnh | 216 KB | ⭐ (cần OCR) |
| `Hinh anh chup man hinh.png` | Ảnh | 39 KB | ⭐ (cần OCR) |
| `Hinh anh chua ten du an.png` | Ảnh | 330 KB | ⭐ (cần OCR) |

### B. HaiVo LeadsMap Vault (Dữ liệu đã xử lý)

| Folder | Số file MD | Ghi chú |
|--------|-----------|---------|
| `1_project/` | 12 | Trong đó 3 do Claude tạo hôm nay, 9 tạo trước |
| `2_contacts/` | **320** | Nhiều — nguồn gốc chưa rõ |
| `4_company/` | 27 | Công ty |
| `0_dashboard/` | 7 | Dashboard views |
| `CRM/` | 0 | Trống hoàn toàn |

---

## 2. PHÂN TÍCH CHI TIẾT: Vietnam Market_Leads.xlsx ⭐ NGUỒN CHÍNH

### Thống kê tổng quan
- **91 dự án** × 24 cột
- **Xây dựng mới:** 90/91 (99%)
- **1 cột ghost** (cột 20, header = None, 100% null) → bỏ qua

### Chất lượng theo cột

| Nhóm cột | Cột | Null | Đánh giá |
|----------|-----|------|---------|
| Core ID | SỐ_HIỆU, TÊN_DỰ_ÁN, GIÁ_TRỊ, TRẠNG_THÁI | 0% | ✅ Đầy đủ |
| Địa lý | ĐỊA_CHỈ, THỊ_XÃ, TỈNH | 0% | ✅ Đầy đủ |
| Timeline | NGÀY_KHỞI_CÔNG, NGÀY_HOÀN_CÔNG | 0% | ✅ Đầy đủ |
| Quy mô | DIỆN_TÍCH_CÔNG_TRÌNH | 22% | ⚠️ Thiếu 1 phần |
| Quy mô | DIỆN_TÍCH_SÀN, SỐ_TẦNG | 14% | ⚠️ Thiếu 1 phần |
| Stakeholder | Chủ Đầu Tư | 0% | ✅ Đầy đủ nhưng DIRTY |
| Stakeholder | Kiến Trúc Sư | 46% | ⚠️ Thiếu nhiều |
| Stakeholder | Tư Vấn | 53% | ⚠️ Thiếu nhiều |
| Stakeholder | Nhà Thầu Chính | **91%** | ❌ Gần trống |
| Stakeholder | Nhà Thầu Phụ | 78% | ❌ Gần trống |

### Phân bố địa lý (top 8)
```
Hồ Chí Minh  ████████████████ 33
Hà Nội       █████ 11
Bình Dương   █████ 11
Vũng Tàu     ███ 6
Cần Thơ      ██ 5
Đà Nẵng      ██ 5
Đồng Nai     ██ 4
Bình Định    ██ 4
```

### Phân loại công trình
```
Căn hộ       ████████████████████ 53
Khách sạn    ██████ 16
Văn phòng    ████ 11
Trường        █ 3
Trung tâm    █ 3
Khác          █ 3
Bãi đậu xe   1 | Kho 1
```

### Trạng thái dự án
```
Thiết Kế Bản Vẽ Thi Công     20 ← HOT (đang cần vật liệu/nhà thầu)
Phê Duyệt Giấy Phép XD       19 ← HOT
Lập Kế Hoạch Sơ Bộ           18 ← TIỀM NĂNG
Trình Duyệt Hồ Sơ TK         14
```

### ⚠️ Vấn đề chất lượng dữ liệu quan trọng

**Vấn đề 1 — Stakeholder columns là dirty text:**
```
"Chủ Đầu Tư: Công Ty ABC, Ông Nguyễn A - Director (ĐT: 84...) ||
 Phòng Đấu Thầu: ; Bà Trần B - Manager (Email: xxx@yyy.com)"
```
→ Nhiều người trên 1 ô, phân cách bằng `||` và `;`
→ **Cần parser riêng** để tách thành từng contact

**Vấn đề 2 — Tên dự án quá dài:**
```
"BÃI ĐẬU XE - xây mới - 9 tầng (KHU HẠ TẦNG & DỊCH VỤ HỖ TRỢ TRUNG TÂM HÀNH CHÍNH TỈNH - BÌNH DƯƠNG)"
```
→ Cần quy tắc rút gọn thành slug cho tên file Obsidian

**Vấn đề 3 — Giá trị bằng USD (float):**
`9.496` → có thể là 9.496 triệu USD hoặc 9,496 USD → cần xác nhận đơn vị

---

## 3. PHÂN TÍCH: SKL_MP13 Contact Directory.xlsx

| Sheet | Rows | Cấu trúc | Vấn đề |
|-------|------|---------|--------|
| BMW-Basement | 278 | Header null (merged cells) | ❌ Cần xử lý thủ công |
| CENTRAL | 31 | STT, Name, Position, Phone, Email | ✅ Sạch, dùng được |
| REE | 126 | Header null (merged cells) | ❌ Cần xử lý thủ công |

→ Chỉ dùng sheet **CENTRAL** cho demo, bỏ BMW và REE.

---

## 4. PHÂN TÍCH: TotalParking.xlsx

- 125 dòng × 34 cột, context là **công ty TotalParking** (không phải HaiVo)
- Có cột: Prj_Client, PrjName, TTP_Sales, TTP_Tech, Sol_Category
- **Không dùng cho Phase 0 Demo** — context khác, gây nhầm lẫn

---

## 5. PDF & HÌNH ẢNH

| File | Đánh giá Demo |
|------|--------------|
| `Ban ve du an.pdf` (25MB) | ❌ Bản vẽ kỹ thuật, không có text hữu ích |
| `Contact point_SKL.pdf` (689KB) | ⚠️ Có ích nhưng cần OCR — để Phase 1 |
| `NameCard.jpg` | ⚠️ Cần OCR — để Phase 1 |
| `Hinh anh chup man hinh.png` | ⚠️ Cần OCR — để Phase 1 |
| `Hinh anh chua ten du an.png` | ⚠️ Cần OCR — để Phase 1 |

**Kết luận PDF/Ảnh:** Bỏ hoàn toàn khỏi Phase 0. OCR sẽ làm demo bất ổn. Thêm vào Phase 1.

---

## 6. VAULT ANALYSIS: 2_contacts (320 files)

Có **320 file contact** đã tồn tại trong vault — nhiều hơn nhiều so với 3 dự án.
Cần kiểm tra: những file này được tạo từ đâu? Có liên kết với 1_project không?

**Ý nghĩa với Demo:** Đây là tài sản lớn nhất — nếu parse được relationship
giữa 91 projects và 320 contacts → Graph View sẽ rất ấn tượng.

---

## 7. ĐỀ XUẤT CHO PHASE 0 DEMO

### Nguồn dữ liệu sử dụng:
| # | Nguồn | Hành động | Kết quả |
|---|-------|----------|---------|
| 1 | `Vietnam Market_Leads.xlsx` | Parse toàn bộ 91 dòng | 91 project MD files |
| 2 | Cột stakeholder (cùng Excel) | Parse `||` separator | Bổ sung 2_contacts |
| 3 | `SKL_MP13 CENTRAL` sheet | Import 31 contacts | Thêm 2_contacts |
| 4 | Vault 2_contacts (320 files) | Đọc, link vào projects | Graph relationships |

### Không dùng cho Demo:
- ❌ TotalParking.xlsx (context khác)
- ❌ Tất cả PDF và ảnh (cần OCR)
- ❌ SKL BMW và REE sheets (header bị merged)

### Dự kiến dữ liệu sau khi xử lý:
```
1_project/    →  91 dự án (từ Excel) + 9 dự án thủ công = 100 projects
2_contacts/   →  320 (hiện có) + ~150 mới từ parse stakeholders
4_company/    →  27 (hiện có) + ~30 mới từ parse CĐT
```
→ **Đủ để demo Graph View ấn tượng với 250+ nodes**

---

## 8. RỦI RO & LƯU Ý

1. **API Key:** RAG cần LLM API. Chưa xác nhận dùng OpenAI hay Anthropic.
2. **Deduplication:** 320 contacts đã có — cần kiểm tra trùng trước khi thêm.
3. **Stakeholder parser:** Phần phức tạp nhất — cần test kỹ trước khi chạy hàng loạt.
4. **Tên file `[[...]]` trong shell:** Đã biết vấn đề, xử lý bằng chuỗi Python.

---

*Báo cáo này do Claude thực hiện. Gemini review và xác nhận hướng đi tại `project_log.md`.*
