# ðŸ—ºï¸ MASTER BUILD PLAN: HaiVo LeadsMap Strategic OS

## ðŸŽ¯ Má»¥c tiÃªu: 100% ChÃ­nh xÃ¡c - Giao diá»‡n 3D VÅ© trá»¥ - Tráº£i nghiá»‡m Manager

---

## ðŸ› ï¸ PHáº¦N 1: Cáº¥u trÃºc Dá»± Ã¡n (Project Structure)
```text
D:/LLM-RAG/
â”œâ”€â”€ backend/ (FastAPI)
â”‚   â”œâ”€â”€ main.py
â”‚   â”œâ”€â”€ core/ (RAG logic, FPT API)
â”‚   â”œâ”€â”€ database/ (SQLite, LanceDB)
â”‚   â””â”€â”€ pipeline/ (Excel, PDF, Namecard Parsers)
â”œâ”€â”€ frontend/ (Next.js)
â”‚   â”œâ”€â”€ app/ (Pages: Dashboard, Graph, Chat)
â”‚   â”œâ”€â”€ components/ (shadcn/ui, 3D Graph)
â”‚   â””â”€â”€ styles/ (Tailwind, Dark Modern Theme)
â””â”€â”€ _system/ (Management)
    â”œâ”€â”€ logs/ (Fix-bug & Change logs)
    â””â”€â”€ rules/ (Sáº¯c lá»‡nh & Blueprint)
```

## ðŸ“… Giai Ä‘oáº¡n 1: Ná»n táº£ng & Dashboard (NgÃ y 1-4)
- **CÃ´ng viá»‡c:** 
  - Build Backend FastAPI láº¥y dá»¯ liá»‡u tá»« 104 dá»± Ã¡n (SQLite).
  - Build Frontend Next.js: Giao diá»‡n Dashboard vá»›i cÃ¡c báº£ng AgGrid (Sort/Filter/Export).
  - UI: TÃ´ng mÃ u Dark Professional (#0A0A0F), Indigo Accent.
- **Testing:** Unit test script quÃ©t 104 file MD Ä‘áº£m báº£o khÃ´ng máº¥t dá»¯ liá»‡u khi vÃ o SQLite.
- **Logging:** Ghi láº¡i má»i lá»—i parse YAML vÃ o `_system/logs/module1_fix.md`.

## ðŸ“… Giai Ä‘oáº¡n 2: VÅ© trá»¥ 3D & Smart Chat (NgÃ y 5-8)
- **CÃ´ng viá»‡c:** 
  - TÃ­ch há»£p `react-force-graph-3d`. Chia cá»¥m "HÃ nh tinh": Dá»± Ã¡n (Blue), Contacts (Green), Companies (Orange).
  - Build RAG Engine vá»›i LanceDB + FPT AI.
  - UI: Khung Chatbot giá»‘ng ChatGPT, tráº£ lá»i kÃ¨m link trÃ­ch dáº«n nguá»“n.
- **Testing:** "Ground Truth Test" - Soáº¡n 20 cÃ¢u há»i vá» dá»± Ã¡n, AI pháº£i tráº£ lá»i Ä‘Ãºng 20/20 kÃ¨m nguá»“n.
- **Logging:** Ghi láº¡i cÃ¡c case AI bá»‹ "hallucinate" (náº¿u cÃ³) Ä‘á»ƒ Ä‘iá»u chá»‰nh Prompt.

## ðŸ“… Giai Ä‘oáº¡n 3: Multimodal & Deployment (NgÃ y 9-12)
- **CÃ´ng viá»‡c:** 
  - Module 2: Xá»­ lÃ½ Namecard Vision.
  - Module 3: Xá»­ lÃ½ PDF Báº£n váº½ 25MB (DÃ¹ng FPT AI).
  - Module 4: TÃ­nh nÄƒng Export bÃ¡o cÃ¡o sang Excel/Word Ä‘áº¹p máº¯t.
  - Deploy: Setup Ngrok/Streamlit Cloud (hoáº·c Vercel cho Frontend) Ä‘á»ƒ Manager dÃ¹ng thá»­.
- **Testing:** Test kháº£ nÄƒng Ä‘á»c báº£n váº½ thá»±c táº¿ (SÆ¡n Háº£i ÄÃ  Náºµng).
- **Logging:** Tá»•ng káº¿t dá»± Ã¡n vÃ  hÆ°á»›ng dáº«n váº­n hÃ nh.

---

## ðŸ¤ Quy trÃ¬nh Phá»‘i há»£p (Agile AI Workflow)
1. **Gemini (Director):** Soáº¡n Briefing cho tá»«ng module con.
2. **Claude (Engineer):** Code module Ä‘Ã³. Sau khi xong, cháº¡y test script.
3. **Claude:** Cáº­p nháº­t file `_system/logs/CHANGELOG.md` (ÄÃ£ lÃ m gÃ¬, Fix lá»—i gÃ¬, Cáº§n lÆ°u Ã½ gÃ¬).
4. **Gemini & User:** Review káº¿t quáº£ vÃ  chuyá»ƒn sang module tiáº¿p theo.


