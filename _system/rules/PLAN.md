# Kế hoạch dự án: HaiVo LeadsMap CRM

> **Gemini** = Product Manager (đọc ngữ cảnh, viết brief, đại diện khách hàng)
> **Claude** = Engineer (phân tích kỹ thuật, viết code, phản biện)

---

## Mục tiêu

Xây dựng hệ thống CRM cho công ty bất động sản thay thế cách làm việc rời rạc hiện tại, gồm:
- Quản lý dự án, khách hàng, nhà thầu, tư vấn
- Tìm kiếm bằng ngôn ngữ tự nhiên (tiếng Việt)
- Trực quan hóa mối quan hệ (ai liên kết với ai)
- Giao diện thân thiện, không cần biết công nghệ

---

## Giai đoạn 0: Demo (hiện tại)

**Mục tiêu:** Ra sản phẩm demo để khách hàng xem và phản hồi trước khi đầu tư làm thật.

**Kiến trúc demo:**

```
[Obsidian Graph View]     ← Trực quan hóa quan hệ (đã có sẵn)
        +
[Streamlit Web App]       ← Chat hỏi đáp + Bảng dữ liệu (cần build)
        +
[Python RAG Backend]      ← LanceDB + LLM (cần build)
```

**Dữ liệu demo:** 3 dự án từ Excel đã import (BaiDauXe, TheGioRiverside, WinkHaiPhong)

**Thời gian ước tính:** 1-2 ngày để có demo chạy được

---

## Giai đoạn 1: MVP

> Chờ phản hồi từ khách hàng sau demo

---

## Giai đoạn 2: Sản phẩm hoàn chỉnh

> Chờ xác nhận về deployment (local / cloud) và số lượng người dùng

---

## Quyết định kỹ thuật đã chốt

| # | Quyết định | Lý do |
|---|-----------|-------|
| 1 | Dùng LanceDB cho vector search | Nhẹ, không cần server riêng, có ví dụ trong awesome-ai-apps |
| 2 | Demo dùng Streamlit | Ra nhanh, Python thuần, đủ để test |
| 3 | Graph view dùng wiki-viewer.html làm nền | Đã có sẵn, có graph component |
| 4 | Dữ liệu gốc giữ ở Obsidian vault (Markdown) | Source of truth, dễ edit |

---

## Câu hỏi cần Gemini hỏi khách hàng

- [ ] Họ dùng trên máy tính hay điện thoại nhiều hơn?
- [ ] Cần nhập liệu từ nguồn nào? (Excel, PDF, ảnh name card, gõ tay)
- [ ] Ai là người dùng chính? (sales, director, admin)
- [ ] Có cần xuất báo cáo ra Word/Excel không?
