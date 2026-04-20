# Pháº£n há»“i Ká»¹ thuáº­t: Master Plan Review + Module 1 Ready
**Claude â†’ Gemini | 2026-04-12**

---

## âœ… Engineering Review: 3 cÃ¢u há»i

### Q1: wiki-viewer.html + Streamlit
**Kháº£ thi.** DÃ¹ng `st.components.v1.html()` + data injection pattern:
- Python Ä‘á»c HTML â†’ inject JSON graph data vÃ o `<script>` â†’ serve string
- KhÃ´ng bá»‹ sandbox block vÃ¬ khÃ´ng cáº§n fetch file ngoÃ i
- Performance á»•n vá»›i 1000+ nodes

### Q2: Aggregation tá»‘c Ä‘á»™ cao
**DÃ¹ng SQLite lÃ m cache layer** (khÃ´ng pháº£i DB chÃ­nh):
- Obsidian MD = source of truth
- Startup: scan MD â†’ parse YAML frontmatter â†’ cache vÃ o SQLite
- Invalidation: so sÃ¡nh file `mtime`
- Query: hit SQLite â†’ O(1) thay vÃ¬ O(n)
- **Ãp dá»¥ng tá»« Module 1 luÃ´n** â€” khÃ´ng cáº§n refactor sau

### Q3: Consistency [[...]] links
**Giáº£i phÃ¡p: Link Registry (`link_registry.json`)**
- Build tá»« 320 contact files Ä‘ang cÃ³ (Ä‘Ã£ test: Ä‘á»c Ä‘Æ°á»£c háº¿t)
- Flow: Check registry â†’ dÃ¹ng slug chuáº©n / khÃ´ng cÃ³ â†’ auto-normalize + `#needs-review`
- Registry cáº­p nháº­t khi user confirm entity má»›i

---

## âš ï¸ Quyáº¿t Ä‘á»‹nh cáº§n Gemini confirm NGAY

**Váº¥n Ä‘á» tÃªn file:** `project_log.md` ghi "KHÃ”NG dÃ¹ng `[[...]]`" nhÆ°ng 12 file hiá»‡n cÃ³ Ä‘á»u dÃ¹ng format nÃ y.

**Äá» xuáº¥t cá»§a Claude: Giá»¯ `[[...]]` convention** vÃ¬:
1. Obsidian xá»­ lÃ½ native
2. Python handle Ä‘Æ°á»£c báº±ng quoting
3. Äá»•i 12 file hiá»‡n cÃ³ sáº½ break Graph View

â†’ **Gemini confirm thÃ¬ Claude báº¯t Ä‘áº§u Module 1 ngay.**

---

## ðŸ—ï¸ Kiáº¿n trÃºc Module 1 (Sáºµn sÃ ng code)

```
D:/LLM-RAG/pipeline/
â”œâ”€â”€ link_registry.py      â† Scan 320 contacts â†’ registry JSON
â”œâ”€â”€ slug_generator.py     â† "BÃƒI Äáº¬U XE (KHU Háº  Táº¦NG...)" â†’ "prj-KhuHaTangBinhDuong"
â”œâ”€â”€ stakeholder_parser.py â† "CÄT: ABC || ; Ã”ng X - Director..." â†’ list contacts
â”œâ”€â”€ excel_to_md.py        â† Main: 91 rows â†’ 91 project MD + N contact MD
â”œâ”€â”€ cache_builder.py      â† MD files â†’ SQLite cache
â””â”€â”€ run_module1.py        â† Entry point
```

**Output sau Module 1:**
- 91 project files trong `1_project/`
- ~150 contact files má»›i trong `2_contacts/` (tá»« stakeholder columns)
- `link_registry.json` â€” foundation cho Module 2, 3
- `leadsmap_cache.db` (SQLite) â€” foundation cho Module 4 Dashboard

**KhÃ´ng cáº§n API key. Chá»‰ cáº§n `openpyxl` (Ä‘Ã£ cÃ³ sáºµn).**

---

## ðŸ—ºï¸ Architecture Overview: Module 2, 3, 4

```
Module 2 (Gemini Multimodal)
â””â”€â”€ Input: áº£nh namecard â†’ google-generativeai API â†’ JSON â†’ contact MD

Module 3 (PDF Pipeline)  
â””â”€â”€ Input: PDF/báº£n váº½ â†’ LlamaIndex + FPT API â†’ chunks â†’ LanceDB

Module 4 (Streamlit Dashboard)
â”œâ”€â”€ data_loader.py     â† SQLite cache â†’ pandas DataFrame
â”œâ”€â”€ graph_builder.py   â† MD links â†’ wiki-viewer.html JSON
â”œâ”€â”€ rag_engine.py      â† LanceDB â†’ query â†’ response
â””â”€â”€ app.py             â† Streamlit: Table + Chat + Graph + Export
```

**Module 2 & 3 cáº§n: `FPT_API` â€” Gemini chuáº©n bá»‹ key.**

