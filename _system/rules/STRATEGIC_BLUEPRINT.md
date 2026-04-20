# ðŸ—ºï¸ STRATEGIC BLUEPRINT: HaiVo LeadsMap (Knowledge OS)

## 1. Táº§m nhÃ¬n & Má»¥c tiÃªu (Vision & Objectives)
- **Má»¥c tiÃªu:** XÃ¢y dá»±ng má»™t "Há»‡ Ä‘iá»u hÃ nh Tri thá»©c" (Knowledge OS) dÃ nh cho Managers & Sales. 
- **Triáº¿t lÃ½:** Dá»±a trÃªn `llm-wiki`. KhÃ´ng chá»‰ lÃ  RAG há»i Ä‘Ã¡p mÃ  lÃ  má»™t há»‡ thá»‘ng há»c táº­p tá»« dá»¯ liá»‡u, trá»±c quan hÃ³a má»‘i quan há»‡.
- **Äá»™ chÃ­nh xÃ¡c:** **Báº®T BUá»˜C 100% (Zero Hallucination)**. Chá»‰ nÃ³i dá»±a trÃªn báº±ng chá»©ng, khÃ´ng Ä‘oÃ¡n mÃ².

## 2. Äá»‘i tÆ°á»£ng & CÃ¡ch váº­n hÃ nh (User Journey)
- **Manager/Director:** DÃ¹ng Dashboard Ä‘á»ƒ xem bá»©c tranh tá»•ng quÃ¡t (Graph), gá»™p báº£ng dá»¯ liá»‡u (Aggregation) vÃ  Xuáº¥t bÃ¡o cÃ¡o (Export).
- **Sales:** Tra cá»©u nhanh thÃ´ng tin dá»± Ã¡n/danh báº¡ qua Chatbot, chá»¥p áº£nh namecard Ä‘á»ƒ AI tá»± Ä‘á»™ng nháº­p liá»‡u.
- **Admin:** NÃ©m má»i loáº¡i file (Excel, PDF, áº¢nh, Báº£n váº½) vÃ o folder Input Ä‘á»ƒ há»‡ thá»‘ng tá»± xá»­ lÃ½.

## 3. Báº£n Ä‘á»“ Ká»¹ thuáº­t (Technical Roadmap)
- **Bá»™ nÃ£o (Brain):** **FPT API (Sá»­ dá»¥ng cÃ¡c model 2.5/3.1 Ä‘Ã£ test thÃ nh cÃ´ng)**.
- **Giao diá»‡n (Frontend):** **Streamlit** (PC first, tá»‘i Æ°u cho Dashboard ná»™i bá»™).
- **LÆ°u trá»¯ (Storage):**
  - **Obsidian (Markdown):** Source of Truth.
  - **SQLite:** Cache layer Ä‘á»ƒ xá»­ lÃ½ báº£ng biá»ƒu tá»‘c Ä‘á»™ cao.
  - **LanceDB:** Vector DB cho RAG Chatbot.
- **TÃ­nh nÄƒng Äá»‰nh cao:**
  - **Dynamic Tables:** Tá»± Ä‘á»™ng gá»™p dá»¯ liá»‡u tá»« nhiá»u note Markdown dá»±a trÃªn `[[link]]`.
  - **Smart Export:** NÃºt xuáº¥t file Excel/Word/PDF chuyÃªn nghiá»‡p.
  - **Multimodal Processing:** Äá»c hiá»ƒu cáº£ báº£n váº½ ká»¹ thuáº­t (PDF 25MB) vÃ  áº¢nh Namecard.

## 4. CÃ¡c Giai Ä‘oáº¡n Thá»±c thi (Implementation Phases)
- **Phase 0 (Demo):** Build Module 1 (Excel) + Khung Dashboard Streamlit + Chatbot RAG cÆ¡ báº£n.
- **Phase 1 (Full Input):** Build Module 2 (Namecard Vision) + Module 3 (PDF/Drawings RAG).
- **Phase 2 (Optimization):** HoÃ n thiá»‡n tÃ­nh nÄƒng Export, SQLite Caching vÃ  Graph Visualization (wiki-viewer.html).

## 5. Danh sÃ¡ch cÃ¡c file Quy táº¯c bá»• trá»£ (Reference Docs)
- `_system/rules/GEMINI.md`: Quy táº¯c Obsidian & Naming.
- `_system/rules/ZERO_HALLUCINATION.md`: Quy táº¯c chá»‘ng áº£o giÃ¡c.
- `_system/tasks/FINAL_EXECUTIVE_ORDER.md`: Lá»‡nh thá»±c thi chi tiáº¿t.
- `_system/tasks/POST_DEMO_STRATEGY.md`: CÃ¡c gÃ³i chi phÃ­ (Lite, Pro, Enterprise).

---
**Chá»‰ thá»‹ cho Claude:** LuÃ´n Ä‘á»c Blueprint nÃ y trÆ°á»›c khi báº¯t Ä‘áº§u báº¥t ká»³ Module nÃ o. Äáº£m báº£o má»i dÃ²ng code Ä‘á»u phá»¥c vá»¥ má»¥c tiÃªu "ChÃ­nh xÃ¡c 100%" vÃ  "Trá»±c quan hÃ³a chiáº¿n lÆ°á»£c" cho Manager.

