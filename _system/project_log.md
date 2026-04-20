# ðŸ“ AI Communication Log: HaiVo LeadsMap (LLM-RAG)

## ðŸ—ï¸ Kiáº¿n trÃºc Tá»•ng quÃ¡t (Thá»‘ng nháº¥t bá»Ÿi GiÃ¡m Ä‘á»‘c & Ká»¹ sÆ°)
- **MÃ´ hÃ¬nh:** Hybrid (Káº¿t há»£p Obsidian + Python).
- **Giao diá»‡n/LÆ°u trá»¯:** Obsidian Vault (Graph View, DataView).
- **Xá»­ lÃ½/RAG:** Python (LlamaIndex/LangChain) - Cháº¡y cÃ¡c script tá»± Ä‘á»™ng hÃ³a.
- **Trá»±c quan hÃ³a:** Giai Ä‘oáº¡n 1 dÃ¹ng Obsidian Graph; Giai Ä‘oáº¡n 2 phÃ¡t triá»ƒn Web Dashboard (Streamlit).

## ðŸ“… Nháº­t kÃ½ PhiÃªn lÃ m viá»‡c (Session Logs)

### [2026-04-12] - Thiáº¿t láº­p Há»‡ thá»‘ng & PhÃ¢n vai
- **GiÃ¡m Ä‘á»‘c (Gemini):** ÄÃ£ quy hoáº¡ch láº¡i folder há»‡ thá»‘ng vÃ o `_system/`. ÄÃ£ thiáº¿t láº­p `GEMINI.md` vá»›i cÃ¡c quy táº¯c nÃ¢ng cao (Entity Mapping, Deduplication).
- **Ká»¹ sÆ° (Claude):** ÄÃ£ pháº£n biá»‡n vá» ká»¹ thuáº­t (chá»n `openpyxl`, cáº£nh bÃ¡o vá» dáº¥u ngoáº·c trong tÃªn file, yÃªu cáº§u lÃ m rÃµ Stack).
- **KhÃ¡ch hÃ ng (HoÃ ng VÄƒn):** ÄÃ£ chá»‘t hÆ°á»›ng Ä‘i Hybrid vÃ  yÃªu cáº§u má»™t quy trÃ¬nh ghi chÃ©p minh báº¡ch giá»¯a cÃ¡c AI.

## ðŸš© Chá»‰ thá»‹ Tiáº¿p theo (Next Action)
- Viáº¿t script Python máº«u Ä‘á»ƒ xá»­ lÃ½ 3 dá»± Ã¡n Ä‘áº§u tiÃªn tá»« file Excel.
- Táº¡o "leadsmap-expert" skill Ä‘á»ƒ Gemini vÃ  Claude luÃ´n Ä‘á»“ng bá»™ logic.

---

### [2026-04-12] - Claude thá»±c thi & pháº£n há»“i ká»¹ thuáº­t
- **Ká»¹ sÆ° (Claude):**
  - ÄÃ£ Ä‘á»c Excel `Vietnam Market_Leads data_Rev 01_210721.xlsx` báº±ng `openpyxl` âœ…
  - ÄÃ£ táº¡o 3 file Markdown cho 3 dá»± Ã¡n Ä‘áº§u tiÃªn trong `1_project/`:
    - `2026 - [[prj-KhuHaTangBinhDuong]].md`
    - `2026 - [[prj-TheGioRiverside]].md`
    - `2026 - [[prj-WinkHaiPhong]].md`
  - ÄÃ£ tráº£ lá»i 3 cÃ¢u há»i ká»¹ thuáº­t táº¡i `_system/tasks/ENGINEER_RESPONSE.md`
  - PhÃ¡t hiá»‡n: Ä‘Ã£ táº¡o `_COLLAB/` trÃ¹ng vá»›i `_system/` â€” chá» Gemini quyáº¿t Ä‘á»‹nh merge
- **Quyáº¿t Ä‘á»‹nh ká»¹ thuáº­t ÄÃƒ CHá»T (Executive Approval):**
  - **TÃªn file:** GIá»® NGUYÃŠN `[[...]]` (vd: `2026 - [[prj-Name]].md`). Claude Ä‘Ã£ xÃ¡c nháº­n xá»­ lÃ½ Ä‘Æ°á»£c.
  - **Performance:** DÃ¹ng SQLite Cache Ä‘á»ƒ há»— trá»£ gá»™p báº£ng cho Manager.
  - **Consistency:** XÃ¢y dá»±ng Link Registry tá»« 320+ contacts cÃ³ sáºµn.
  - **Visualization:** Inject JSON trá»±c tiáº¿p vÃ o `wiki-viewer.html`.

### [2026-04-12] - PHÃT Lá»†NH BUILD MODULE 1
- **Tráº¡ng thÃ¡i:** ÄANG THá»°C THI (BUILDING)
- **Nhiá»‡m vá»¥ cho Claude:** XÃ¢y dá»±ng Pipeline Excelâ†’Obsidian hoÃ n chá»‰nh (91 dá»± Ã¡n) kÃ¨m theo Link Registry vÃ  Slug Generator.

### [2026-04-12] - NÃ‚NG Cáº¤P KIáº¾N TRÃšC: NEXT.JS + FASTAPI + 3D GRAPH
- **Quyáº¿t Ä‘á»‹nh:** Chuyá»ƒn tá»« Streamlit sang **Next.js 14 + FastAPI** Ä‘á»ƒ Ä‘áº¡t Ä‘á»™ tháº©m má»¹ 95% (Showroom Quality).
- **Trá»±c quan:** Sá»­ dá»¥ng **3D Force Graph** (Hiá»‡u á»©ng vÅ© trá»¥/hÃ nh tinh) cho Manager.
- **HÃ nh Ä‘á»™ng:** Ban hÃ nh `_system/tasks/MASTER_BUILD_PLAN.md`.
- **Lá»‡nh cho Claude:** Thiáº¿t láº­p thÆ° má»¥c `backend/` vÃ  `frontend/`. Báº¯t Ä‘áº§u Phase 1: SQLite Cache & Dashboard Table.


## ðŸš© Chá»‰ thá»‹ Tiáº¿p theo
- [ ] **Claude:** Äá»c ngay `COMPREHENSIVE_DATA_PLAN.md`. Chuáº©n bá»‹ mÃ´i trÆ°á»ng Python cÃ i Ä‘áº·t `google-generativeai`, `llama-index`, `lancedb`, `openpyxl`. Báº¯t Ä‘áº§u code tá»«ng module má»™t!


### [2026-04-12] - Module 1 HOÃ€N THÃ€NH âœ…
- **Ká»¹ sÆ° (Claude):** Pipeline Excel â†’ Obsidian cháº¡y thÃ nh cÃ´ng
- **Káº¿t quáº£:**
  - 78 project files má»›i trong 1_project/ (13 Ä‘Ã£ cÃ³ â†’ skip)
  - ~391 contact files trong 2_contacts/
  - link_registry.json: 977 entries
  - Vault: ~500+ nodes sáºµn sÃ ng cho Graph View
- **Code:** D:/LLM-RAG/pipeline/ (slug_generator, stakeholder_parser, link_registry, excel_to_md)
- **Lá»—i Ä‘Ã£ fix:** Windows filename sanitize (xÃ³a kÃ½ tá»± :/*? trong tÃªn file)

## ðŸš© Chá»‰ thá»‹ Tiáº¿p theo
- [ ] **Gemini:** Viáº¿t VISION_SPEC.md cho Module 2 (áº£nh namecard vá»›i FPT Vision)
- [ ] **Cáº§n:** FPT_API Ä‘á»ƒ cháº¡y Module 2 & 3
- [ ] **Claude sáºµn sÃ ng:** Build Module 4 (Streamlit Dashboard) song song náº¿u cÃ³ chá»‰ thá»‹

### [2026-04-12] - Phase 1 Web App HOÃ€N THÃ€NH âœ…
- **Ká»¹ sÆ° (Claude):** ÄÃ£ build toÃ n bá»™ web app Next.js + FastAPI
- **Frontend hoÃ n thÃ nh:**
  - /dashboard â€” Báº£ng dá»± Ã¡n vá»›i filter, sort, pagination, export Excel
  - /graph â€” 3D Knowledge Graph (react-force-graph-3d)
  - /contacts â€” Grid liÃªn há»‡ vá»›i search/filter
  - /chat â€” AI Chatbot (Gemini RAG, anti-hallucination, citations)
  - /upload â€” Drag & drop upload (UI hoÃ n chá»‰nh, endpoint sáº½ build sau)
  - /settings â€” Cáº¥u hÃ¬nh API key Gemini
- **Backend hoÃ n thÃ nh:**
  - GET /api/stats, /api/projects, /api/contacts, /api/graph, /api/export/excel
  - POST /api/chat â€” RAG vá»›i SQLite search + FPT AI
- **UI:** Dark theme, Tailwind CSS, glassmorphism sidebar, hover effects, badges
- **Refactor:** Gemini audit â€” xÃ³a inline styles, dÃ¹ng Tailwind classes, backdrop-blur sidebar
- **Bugs Ä‘Ã£ fix:** BUG-001 Ä‘áº¿n BUG-006 (Unicode, Windows filename, npm packages, Next.js config, bat files)
- **Cháº¡y:** setup.bat â†’ start.bat â†’ http://localhost:3000

### [2026-04-12] - Phase 2 HOÃ€N THÃ€NH âœ…
- **Sprint 1 â€” Graph + Chat Power:**
  - /graph: filter panel (tá»‰nh, CÄT, loáº¡i node) + node highlight/dim + localStorage Chatâ†’Graph sync
  - /chat: markdown table rendering â†’ HTML table Ä‘áº¹p + Download CSV + Download Excel
  - /chat: graph filter notification khi AI detect filter intent
  - backend: detect_filter_intent() â†’ GraphFilter response
- **Sprint 2 â€” LanceDB RAG:**
  - pipeline/lancedb_indexer.py: embed toÃ n bá»™ Vault â†’ LanceDB multilingual-e5-large
  - backend/core/rag.py: LanceDB vector search â†’ fallback SQLite LIKE
  - /api/chat: nÃ¢ng cáº¥p dÃ¹ng rag.py (semantic search > keyword search)
  - pipeline/ground_truth_test.py: 20 cÃ¢u Q&A test suite
  - pipeline/fpt_ocr.py: namecard JPG/PNG â†’ contact.md (FPT Vision)
- **Sprint 3 â€” Export + PDF:**
  - pipeline/pdf_parser.py: PDF text (LlamaIndex) + scan (FPT Vision) â†’ LanceDB
  - POST /api/export/table: chat table â†’ Excel download
  - build_index.bat + test_rag.bat

## ðŸš© CÃ²n láº¡i (Phase 3 - Production)
- [ ] POST /api/upload endpoint tháº­t sá»± (ná»‘i frontend Upload page)
- [ ] Company profiles auto-generation (tá»« link_registry.json)
- [ ] Entity resolver ("Cotec" = "Coteccons")
- [ ] Export Word/PDF bÃ¡o cÃ¡o Ä‘áº¹p (python-docx)
- [ ] Deploy ngrok cho sáº¿p xem remote
- [ ] PhÃ¢n quyá»n Director / Sales / Admin
- [ ] Mobile responsive


