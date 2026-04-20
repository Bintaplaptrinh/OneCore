# ðŸ Sáº®C Lá»†NH THá»°C THI Tá»I CAO (FINAL EXECUTIVE ORDER)

## 1. Táº§m nhÃ¬n & Äá»‘i tÆ°á»£ng (Product Vision)
- **TÃªn dá»± Ã¡n:** HaiVo LeadsMap - Strategic Knowledge OS.
- **Má»¥c tiÃªu:** Biáº¿n kho dá»¯ liá»‡u thÃ´ thÃ nh "Kho lÆ°u trá»¯ thÃ´ng minh" (Smart Vault).
- **Äá»‘i tÆ°á»£ng:** GiÃ¡m Ä‘á»‘c (Director) vÃ  Sales (Cáº§n tra cá»©u nhanh, gá»™p báº£ng, xuáº¥t bÃ¡o cÃ¡o).
- **NguyÃªn táº¯c vÃ ng:** **CHÃNH XÃC 100% (Zero Hallucination)**. KhÃ´ng Ä‘oÃ¡n, khÃ´ng bá»‹a, chá»‰ nÃ³i dá»±a trÃªn báº±ng chá»©ng (Citation).

## 2. Kiáº¿n trÃºc Ká»¹ thuáº­t (Technical Stack)
- **NgÃ´n ngá»¯:** Python (Dá»… báº£o trÃ¬, máº¡nh vá» AI/Data).
- **Giao diá»‡n:** **Streamlit** (Phá»¥c vá»¥ ná»™i bá»™, Dashboard trá»±c quan, ra sáº£n pháº©m nhanh).
- **Bá»™ nÃ£o AI:** **FPT API (Flash/Pro)**. Táº­n dá»¥ng kháº£ nÄƒng Multimodal Ä‘á»ƒ Ä‘á»c PDF/áº¢nh vÃ  Context Window khá»•ng lá»“.
- **LÆ°u trá»¯:**
  - Obsidian (Markdown) - Source of Truth.
  - SQLite - Cache Ä‘á»ƒ gá»™p báº£ng (Aggregation) tá»‘c Ä‘á»™ cao.
  - LanceDB - Vector DB cho RAG Chatbot.

## 3. Lá»™ trÃ¬nh Thá»±c thi (The Pipeline)
- **Module 1 (ÄÃƒ XONG):** Pipeline Excel -> Obsidian (91 dá»± Ã¡n, 391 contacts).
- **Module 2 (TIáº¾P THEO):** DÃ¹ng FPT Vision xá»­ lÃ½ áº¢nh Namecard -> Obsidian.
- **Module 3 (NÃ‚NG CAO):** DÃ¹ng LlamaIndex + Gemini Ä‘á»c PDF Báº£n váº½/TÃ i liá»‡u -> Vector DB.
- **Module 4 (GIAO DIá»†N):** Build Streamlit Dashboard gá»“m:
  - Báº£ng dá»¯ liá»‡u Ä‘á»™ng (Dynamic Tables) lá»c theo Linket.
  - NÃºt **Export** ra Excel/Word.
  - Äá»“ thá»‹ quan há»‡ (Graph View) nhÃºng `wiki-viewer.html`.
  - Chatbot RAG há»— trá»£ tiáº¿ng Viá»‡t, tráº£ lá»i kÃ¨m nguá»“n trÃ­ch dáº«n.

## 4. Quy táº¯c "BÃ n tay sáº¯t" (Guardrails)
- **TÃªn file:** Giá»¯ chuáº©n Obsidian `2026 - [[prj-Name]].md`.
- **Nháº¥t quÃ¡n:** DÃ¹ng `link_registry.json` Ä‘á»ƒ quáº£n lÃ½ cÃ¡c liÃªn káº¿t.
- **Äá»™ tin cáº­y:** Temperature = 0.0. Thá»±c hiá»‡n Unit Test 50 cÃ¢u há»i thá»±c táº¿ trÆ°á»›c khi bÃ n giao.

---
**Gá»­i Ká»¹ sÆ° Claude:** ÄÃ¢y lÃ  tÃ i liá»‡u duy nháº¥t anh cáº§n tuÃ¢n thá»§ tá»« nay vá» sau. HÃ£y Ä‘á»c thÃªm `GEMINI.md`, `project_log.md` vÃ  `ZERO_HALLUCINATION.md` trong thÆ° má»¥c `_system/` Ä‘á»ƒ náº¯m chi tiáº¿t. Báº¯t Ä‘áº§u build Module 4 (Giao diá»‡n Dashboard) vÃ  Module 2 (Xá»­ lÃ½ Namecard) ngay!


