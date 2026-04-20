# ðŸ›ï¸ FINAL ARCHITECTURE REVIEW & EXECUTION PLAN

## 1. Má»¥c tiÃªu Cá»‘t lÃµi (The "Smart Vault" Concept)
Há»‡ thá»‘ng KHÃ”NG PHáº¢I lÃ  má»™t cÃ´ng cá»¥ dá»± Ä‘oÃ¡n. NÃ³ lÃ  má»™t **Kho lÆ°u trá»¯ thÃ´ng minh (Smart Vault)**. 
YÃªu cáº§u: Äá»™ chÃ­nh xÃ¡c tuyá»‡t Ä‘á»‘i (100% Grounding), khÃ´ng áº£o giÃ¡c. Phá»¥c vá»¥ nhÃ³m nhá» Manager & Sales.

## 2. Tech Stack Quyáº¿t Ä‘á»‹nh (Python-Centric)
- **Frontend:** Streamlit (Tá»‘c Ä‘á»™ phÃ¡t triá»ƒn nhanh, phÃ¹ há»£p quy mÃ´ ná»™i bá»™, há»— trá»£ hiá»ƒn thá»‹ báº£ng/biá»ƒu Ä‘á»“ xuáº¥t sáº¯c).
- **Backend & Logic:** Python thuáº§n.
- **Storage:** 
  1. Obsidian (Markdown) - Nguá»“n chÃ¢n lÃ½ (Source of Truth).
  2. SQLite - Cache layer Ä‘á»ƒ gá»™p báº£ng siÃªu tá»‘c.
  3. LanceDB - Vector DB nhÃºng siÃªu nháº¹ cho RAG.
- **LLM/API:** **FPT AI/Pro API**. LÃ½ do: Xá»­ lÃ½ Multimodal (PDF, áº¢nh) báº£n Ä‘á»‹a cá»±c máº¡nh, context window khá»•ng lá»“ (khÃ´ng cáº§n chunking quÃ¡ Ä‘Ã  lÃ m máº¥t ngá»¯ cáº£nh), chi phÃ­ tá»‘i Æ°u.

## 3. Kiáº¿n trÃºc Luá»“ng Dá»¯ liá»‡u (Data Flow)
1. **Input:** File rÆ¡i vÃ o `LeadsMap_Input Information`.
2. **Parser Pipeline (Python):** 
   - Excel â†’ `openpyxl` â†’ Markdown.
   - Namecard/PDF â†’ Gemini Multimodal API â†’ TrÃ­ch xuáº¥t JSON â†’ Markdown.
3. **Linker:** Äá»‘i chiáº¿u `Link Registry` â†’ Cáº­p nháº­t SQLite.
4. **Indexer:** BÄƒm vÄƒn báº£n â†’ Vectorize â†’ LÆ°u vÃ o LanceDB.

## 4. Tráº£i nghiá»‡m NgÆ°á»i dÃ¹ng trÃªn Streamlit (User Views)
- **View 1 (Dynamic Tables):** Giao diá»‡n báº£ng biá»ƒu tá»•ng há»£p (vd: Dá»± Ã¡n theo Chá»§ Ä‘áº§u tÆ°). CÃ³ nÃºt **Export to Excel**.
- **View 2 (Graph Visualizer):** NhÃºng `wiki-viewer.html` Ä‘á»ƒ sáº¿p xem máº¡ng lÆ°á»›i quan há»‡.
- **View 3 (RAG Chatbot):** Giao diá»‡n há»i Ä‘Ã¡p. Pháº£i luÃ´n kÃ¨m nguá»“n trÃ­ch dáº«n (Source Citation).

## 5. Chiáº¿n lÆ°á»£c Testing (Äáº£m báº£o 100% ChÃ­nh xÃ¡c)
- **Strict Prompting:** Temperature = 0.0. "TrÃ­ch dáº«n file hoáº·c tráº£ lá»i KhÃ´ng biáº¿t".
- **Unit Testing:** Claude pháº£i viáº¿t script test 20 cÃ¢u há»i truy váº¥n dá»¯ liá»‡u Excel Ä‘á»ƒ Ä‘áº£m báº£o Chatbot khÃ´ng tráº£ lá»i sai lá»‡ch trÆ°á»›c khi duyá»‡t Phase 0.

---
**Gá»­i Ká»¹ sÆ° Claude:** Äá»c ká»¹ báº£n thiáº¿t káº¿ nÃ y. Náº¿u khÃ´ng cÃ³ pháº£n Ä‘á»‘i ká»¹ thuáº­t nghiÃªm trá»ng nÃ o, hÃ£y Báº®T Äáº¦U CODE MODULE 1 (Excel Pipeline) VÃ€ SETUP STREAMLIT APP CÆ  Báº¢N.

