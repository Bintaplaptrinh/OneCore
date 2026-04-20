# ðŸš€ Káº¿ hoáº¡ch Xá»­ lÃ½ Dá»¯ liá»‡u ToÃ n diá»‡n (Comprehensive Data Pipeline)

## ðŸŽ¯ Má»¥c tiÃªu Má»›i (Cáº­p nháº­t tá»« KhÃ¡ch hÃ ng)
KHÃ”NG Bá»Ž SÃ“T Dá»® LIá»†U. Xá»­ lÃ½ 100% dá»¯ liá»‡u trong `LeadsMap_Input Information/` bao gá»“m Excel, PDF, Báº£n váº½, vÃ  áº¢nh Namecard.

## ðŸ§  Kiáº¿n trÃºc Ká»¹ thuáº­t (Sá»­ dá»¥ng Gemini Multimodal)
VÃ¬ chÃºng ta Ä‘Ã£ chá»n **FPT API (`gemma-4-31B-it` / `gemma-4-31B-it`)**, chÃºng ta sáº½ táº­n dá»¥ng kháº£ nÄƒng Multimodal (Äa phÆ°Æ¡ng thá»©c) cá»§a nÃ³ Ä‘á»ƒ thay tháº¿ cÃ¡c cÃ´ng cá»¥ OCR truyá»n thá»‘ng phá»©c táº¡p.

### 1. Luá»“ng 1: Dá»¯ liá»‡u Cáº¥u trÃºc (Excel/CSV)
- **Nguá»“n:** `Vietnam Market_Leads.xlsx` (91 dá»± Ã¡n) vÃ  cÃ¡c file CSV tá»« Ä‘iá»‡n thoáº¡i.
- **CÃ´ng cá»¥:** `openpyxl`, `pandas`.
- **Äáº§u ra:** File Markdown chuáº©n Obsidian (`2026 - prj-Name.md` vÃ  `Name_Company.md`).
- **Xá»­ lÃ½:** Entity Mapping (Hybrid), Deduplication (Strategy C).

### 2. Luá»“ng 2: áº¢nh Namecard (Unstructured Images)
- **Nguá»“n:** ThÆ° má»¥c `11_Name Card Scan`.
- **CÃ´ng cá»¥:** DÃ¹ng `google-generativeai` SDK (FPT AI).
- **Prompt:** Gá»­i tháº³ng áº£nh namecard cho FPT API kÃ¨m prompt: *"Extract Name, Company, Phone, Email and return as JSON"*.
- **Äáº§u ra:** File Markdown danh báº¡ (`Name_Company.md`).

### 3. Luá»“ng 3: TÃ i liá»‡u Dá»± Ã¡n (PDF/Báº£n váº½/Brochure)
- **Nguá»“n:** ThÆ° má»¥c `13_Tu file pdf` vÃ  `14_Tu 1 file hinh anh hoac pdf...`.
- **CÃ´ng cá»¥:** `LlamaIndex` + `FPT API`.
- **Ká»¹ thuáº­t:** 
  - **Vá»›i PDF Text:** DÃ¹ng LlamaIndex PDF Reader thÃ´ng thÆ°á»ng Ä‘á»ƒ bÄƒm nhá» (chunking) vÃ  Ä‘Æ°a vÃ o LanceDB.
  - **Vá»›i Báº£n váº½/PDF Scan:** Truyá»n trá»±c tiáº¿p qua FPT AI API Ä‘á»ƒ nháº­n diá»‡n cÃ¡c báº£ng biá»ƒu, sá»‘ liá»‡u quy mÃ´ trong hÃ¬nh áº£nh.
- **Äáº§u ra:** 
  - TrÃ­ch xuáº¥t thÃ´ng tin chÃ­nh (Quy mÃ´, Chá»§ Ä‘áº§u tÆ°, NhÃ  tháº§u) Ä‘á»ƒ táº¡o file Markdown dá»± Ã¡n.
  - Pháº§n cÃ²n láº¡i Ä‘Æ°a vÃ o **Vector Database (LanceDB)** Ä‘á»ƒ phá»¥c vá»¥ tÃ­nh nÄƒng Há»i Ä‘Ã¡p (RAG Chatbot).

## ðŸš© Lá»™ trÃ¬nh Thá»±c thi cho Ká»¹ sÆ° (Claude):
1. **Module 1 (Ngay láº­p tá»©c):** Build script Python xá»­ lÃ½ Luá»“ng 1 (Excel) Ä‘á»ƒ cÃ³ Base Data.
2. **Module 2 (Tiáº¿p theo):** Viáº¿t script dÃ¹ng `google-generativeai` Ä‘á»ƒ xá»­ lÃ½ Luá»“ng 2 (áº¢nh Namecard).
3. **Module 3 (NÃ¢ng cao):** Thiáº¿t láº­p LlamaIndex + LanceDB Ä‘á»ƒ "nuá»‘t" Luá»“ng 3 (PDF/Báº£n váº½).
4. **Module 4 (Giao diá»‡n):** TÃ­ch há»£p táº¥t cáº£ vÃ o Streamlit Dashboard (CÃ³ Báº£ng gá»™p + Chatbot RAG + Export).


