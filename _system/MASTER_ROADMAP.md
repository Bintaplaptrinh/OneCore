# ðŸ—ºï¸ MASTER ROADMAP â€” HaiVo LeadsMap Intelligence System
**PhiÃªn báº£n:** 1.0 | **NgÃ y:** 2026-04-12
**Soáº¡n:** Claude (Ká»¹ sÆ°) | **Duyá»‡t:** Gemini (GiÃ¡m Ä‘á»‘c) + HoÃ ng VÄƒn

---

## ðŸŽ¯ Má»¤C TIÃŠU Sáº¢N PHáº¨M

XÃ¢y dá»±ng **"ChatGPT ná»™i bá»™"** cho cÃ´ng ty báº¥t Ä‘á»™ng sáº£n â€” khÃ´ng pháº£i RAG Ä‘Æ¡n giáº£n mÃ  lÃ  há»‡ thá»‘ng **há»c, liÃªn káº¿t vÃ  khÃ´ng bá»‹a dá»¯ liá»‡u**.

```
NgÆ°á»i dÃ¹ng há»i tiáº¿ng Viá»‡t
        â†“
Há»‡ thá»‘ng tÃ¬m Ä‘Ãºng nguá»“n (khÃ´ng suy diá»…n bá»«a)
        â†“
Tráº£ lá»i + trÃ­ch dáº«n file gá»‘c
        â†“
Tá»•ng há»£p thÃ nh báº£ng / xuáº¥t bÃ¡o cÃ¡o
```

**3 vai trÃ² sá»­ dá»¥ng:**
- ðŸ‘¨â€ðŸ’¼ **Director** â†’ Dashboard tá»•ng quan, báº£ng lá»c, export bÃ¡o cÃ¡o
- ðŸ•µï¸ **Sales** â†’ Chat há»i nhanh: dá»± Ã¡n, contacts, lá»‹ch sá»­
- ðŸ—„ï¸ **Admin** â†’ Upload file má»›i â†’ há»‡ thá»‘ng tá»± xá»­ lÃ½

---

## ðŸ—ï¸ KIáº¾N TRÃšC Tá»”NG THá»‚

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Táº¦NG 3 â€” GIAO DIá»†N (Streamlit Web App)             â”‚
â”‚  Chat + Báº£ng Ä‘á»™ng + Graph quan há»‡ + Export          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                      â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Táº¦NG 2 â€” TRÃ TUá»† (Knowledge Engine)               â”‚
â”‚  LanceDB (vector) + SQLite (cache) + Lint (kiá»ƒm tra)â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                      â”‚
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  Táº¦NG 1 â€” Dá»® LIá»†U (Obsidian Vault)                 â”‚
â”‚  raw/ (báº¥t biáº¿n) â†’ wiki/ (MD files) â†’ registry.json â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**NguyÃªn táº¯c cá»‘t lÃµi (tá»« llm-wiki):**
- `raw/` = file gá»‘c â†’ **KHÃ”NG BAO GIá»œ Sá»¬A**
- AI chá»‰ viáº¿t vÃ o `wiki/` (Obsidian vault)
- Má»i cÃ¢u tráº£ lá»i pháº£i **truy ngÆ°á»£c Ä‘Æ°á»£c vá» file nguá»“n**
- Lint cháº¡y Ä‘á»‹nh ká»³ â†’ phÃ¡t hiá»‡n broken links, data sai, thiáº¿u sÃ³t

---

## ðŸ“¦ LOáº I FILE Xá»¬ LÃ ÄÆ¯á»¢C

| Loáº¡i file | CÃ´ng cá»¥ | Äá»™ chÃ­nh xÃ¡c | Giai Ä‘oáº¡n |
|-----------|---------|-------------|-----------|
| Excel / CSV | openpyxl / pandas | 99% | GÄ 0 âœ… |
| áº¢nh namecard (JPG/PNG) | FPT Vision API | 85-90% | GÄ 0 |
| Screenshot thÃ´ng tin | FPT Vision API | 80-85% | GÄ 0 |
| PDF cÃ³ text | LlamaIndex PDF Reader | 95%+ | GÄ 0 |
| PDF scan (áº£nh) | FPT Vision page-by-page | 75-80% | GÄ 0 |
| SVG | Parse XML text | 90%+ | GÄ 2 |
| DWG / AutoCAD | ezdxf â†’ PNG â†’ FPT Vision | 60-70% | GÄ 3 |
| Video | FPT AI | 70% | GÄ 3 |
| Word / PowerPoint | python-docx / python-pptx | 95%+ | GÄ 2 |

---

## ðŸš¦ 4 GIAI ÄOáº N & TIáº¾N Äá»˜

---

### GIAI ÄOáº N 0 â€” Ná»€N Táº¢NG Dá»® LIá»†U `â–“â–“â–“â–“â–“â–“â–“â–‘â–‘â–‘ 75%`

> **Má»¥c tiÃªu:** Vault Ä‘áº§y Ä‘á»§, sáº¡ch, cÃ³ link registry trÆ°á»›c khi lÃ m AI

| # | Viá»‡c cáº§n lÃ m | Tráº¡ng thÃ¡i | Cáº§n gÃ¬ |
|---|-------------|-----------|--------|
| 0.1 | Cáº¥u trÃºc Obsidian Vault | âœ… 100% | â€” |
| 0.2 | Excel â†’ 101 project MD files | âœ… 100% | â€” |
| 0.3 | Stakeholder â†’ 741 contact MD files | âœ… 100% | â€” |
| 0.4 | Link Registry (977 entity slugs) | âœ… 100% | â€” |
| 0.5 | áº¢nh namecard â†’ contact MD | âŒ 0% | FPT_API |
| 0.6 | PDF â†’ project + contact MD | âŒ 0% | FPT_API |
| 0.7 | Company profiles (4_company/) | âŒ 0% | Script tá»« registry |
| 0.8 | DWG / SVG â†’ metadata | âŒ 0% | Giai Ä‘oáº¡n 3 |

**Files Ä‘Ã£ cÃ³:**
```
pipeline/
â”œâ”€â”€ excel_to_md.py        âœ… cháº¡y Ä‘Æ°á»£c
â”œâ”€â”€ slug_generator.py     âœ…
â”œâ”€â”€ stakeholder_parser.py âœ…
â”œâ”€â”€ link_registry.py      âœ…
â””â”€â”€ link_registry.json    âœ… 977 entries
```

---

### GIAI ÄOáº N 1 â€” DEMO Cá»T LÃ•I `â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘ 0%`

> **Má»¥c tiÃªu:** Web app cháº¡y Ä‘Æ°á»£c trÃªn PC, cho khÃ¡ch hÃ ng xem
> **KhÃ´ng cáº§n API key** â€” dÃ¹ng keyword search táº¡m thay AI

| # | Viá»‡c cáº§n lÃ m | Tráº¡ng thÃ¡i | DÃ¹ng tá»« Ä‘Ã¢u |
|---|-------------|-----------|------------|
| 1.1 | SQLite cache builder | âŒ 0% | Tá»± viáº¿t |
| 1.2 | MD parser â†’ DataFrame | âŒ 0% | Tá»± viáº¿t |
| 1.3 | Báº£ng dá»± Ã¡n + filter (tá»‰nh/loáº¡i/CÄT/thá»i gian) | âŒ 0% | Streamlit |
| 1.4 | Báº£ng contacts + search | âŒ 0% | Streamlit |
| 1.5 | Export Excel | âŒ 0% | openpyxl |
| 1.6 | Export PDF bÃ¡o cÃ¡o | âŒ 0% | python-docx |
| 1.7 | Graph quan há»‡ (project â†” company â†” person) | âŒ 0% | wiki-viewer.html |
| 1.8 | Chat UI (khung nhÃ¬n) | âŒ 0% | pdf_rag_analyser |
| 1.9 | Keyword search fallback (chÆ°a cáº§n AI) | âŒ 0% | Tá»± viáº¿t |

**Cáº¥u trÃºc code sáº½ táº¡o:**
```
demo/
â”œâ”€â”€ app.py                â† Entry point: streamlit run app.py
â”œâ”€â”€ pages/
â”‚   â”œâ”€â”€ 1_dashboard.py    â† Báº£ng + filter + export
â”‚   â”œâ”€â”€ 2_chat.py         â† Chat UI
â”‚   â””â”€â”€ 3_graph.py        â† Graph view
â”œâ”€â”€ core/
â”‚   â”œâ”€â”€ cache.py          â† SQLite builder
â”‚   â”œâ”€â”€ md_parser.py      â† Äá»c vault â†’ DataFrame
â”‚   â””â”€â”€ search.py         â† Keyword search
â””â”€â”€ assets/
    â””â”€â”€ graph.html        â† Adapted wiki-viewer.html
```

**Test Giai Ä‘oáº¡n 1:**
```
âœ… PASS náº¿u:
- App load < 3 giÃ¢y
- Filter "Tá»‰nh = HÃ  Ná»™i" â†’ Ä‘Ãºng sá»‘ dá»± Ã¡n
- Export Excel â†’ file táº£i Ä‘Æ°á»£c, dá»¯ liá»‡u khá»›p
- Graph hiá»ƒn thá»‹ > 50 nodes cÃ³ liÃªn káº¿t
```

---

### GIAI ÄOáº N 2 â€” AI INTELLIGENCE `â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘ 0%`

> **Má»¥c tiÃªu:** Chat thÃ´ng minh tháº­t sá»± + há»‡ thá»‘ng khÃ´ng bá»‹a
> **Cáº§n:** FPT_API

| # | Viá»‡c cáº§n lÃ m | Tráº¡ng thÃ¡i | DÃ¹ng tá»« Ä‘Ã¢u |
|---|-------------|-----------|------------|
| 2.1 | LanceDB vector index (embedding tiáº¿ng Viá»‡t) | âŒ 0% | LlamaIndex |
| 2.2 | RAG Engine â€” FPT AI | âŒ 0% | pdf_rag_analyser |
| 2.3 | CÃ¢u tráº£ lá»i kÃ¨m trÃ­ch dáº«n nguá»“n | âŒ 0% | Tá»± viáº¿t |
| 2.4 | Entity resolver (merge "Cotec" = "Coteccons") | âŒ 0% | Tá»± viáº¿t |
| 2.5 | Relationship builder tá»± Ä‘á»™ng | âŒ 0% | Tá»± viáº¿t |
| 2.6 | Báº£ng tá»•ng há»£p thÃ´ng minh (SQLite aggregate) | âŒ 0% | Tá»± viáº¿t |
| 2.7 | **Lint â€” chá»‘ng bá»‹a** | âŒ 0% | llm-wiki Lint spec |
| 2.8 | Ground truth test suite (4 cÃ¢u chuáº©n) | âŒ 0% | test_vector_search pattern |
| 2.9 | Xá»­ lÃ½ áº£nh namecard (Module 2) | âŒ 0% | google-generativeai |
| 2.10 | Xá»­ lÃ½ PDF (Module 3) | âŒ 0% | LlamaIndex + Gemini |

**Bá»™ test "khÃ´ng bá»‹a" (Ground Truth):**
```python
# CÃ¢u há»i chuáº©n â€” Ä‘Ãºng háº¿t má»›i PASS
Q1: "Dá»± Ã¡n Wink Hotel á»Ÿ Ä‘Ã¢u?"          â†’ "Háº£i PhÃ²ng"
Q2: "Chá»§ Ä‘áº§u tÆ° The GiÃ³ Riverside?"    â†’ "An Gia"
Q3: "Dá»± Ã¡n nÃ o á»Ÿ HÃ  Ná»™i?"             â†’ danh sÃ¡ch Ä‘Ãºng tá»« Excel
Q4: "SÄT anh Quang bÃªn Kajima?"        â†’ "090 3411 661"

TiÃªu chÃ­: 4/4 Ä‘Ãºng + cÃ³ trÃ­ch dáº«n file nguá»“n = âœ… khÃ´ng bá»‹a
```

---

### GIAI ÄOáº N 3 â€” PRODUCTION READY `â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘ 0%`

> **Má»¥c tiÃªu:** BÃ n giao tháº­t sá»± cho cÃ´ng ty dÃ¹ng hÃ ng ngÃ y

| # | Viá»‡c cáº§n lÃ m | Tráº¡ng thÃ¡i | Ghi chÃº |
|---|-------------|-----------|---------|
| 3.1 | Chuyá»ƒn Gemini â†’ Claude API | âŒ 0% | Sau demo ok |
| 3.2 | Xá»­ lÃ½ DWG/AutoCAD | âŒ 0% | ezdxf + FPT Vision |
| 3.3 | Xá»­ lÃ½ Video | âŒ 0% | FPT AI (Ä‘áº¯t) |
| 3.4 | Xá»­ lÃ½ Word / PowerPoint | âŒ 0% | python-docx |
| 3.5 | PhÃ¢n quyá»n Director / Sales / Admin | âŒ 0% | Streamlit auth |
| 3.6 | Auto-sync (file má»›i â†’ tá»± xá»­ lÃ½) | âŒ 0% | File watcher |
| 3.7 | Deploy lÃªn server / cloud | âŒ 0% | Chá» xÃ¡c nháº­n |
| 3.8 | Mobile responsive | âŒ 0% | CSS responsive |

---

## ðŸ“Š Tá»”NG TIáº¾N Äá»˜

```
GÄ 0 â€” Ná»n táº£ng dá»¯ liá»‡u    â–“â–“â–“â–“â–“â–“â–“â–‘â–‘â–‘  75%
GÄ 1 â€” Demo cá»‘t lÃµi        â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%
GÄ 2 â€” AI Intelligence     â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%
GÄ 3 â€” Production          â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%

Tá»”NG Dá»° ÃN                 â–“â–“â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘  18%
```

---

## ðŸ”„ THá»¨ Tá»° LÃ€M TIáº¾P THEO

```
KHÃ”NG cáº§n API key â†’ lÃ m ngay:
â”œâ”€â”€ GÄ1.1 â†’ SQLite cache + MD parser     (ná»­a ngÃ y)
â”œâ”€â”€ GÄ1.2 â†’ Báº£ng filter + Export Excel   (1 ngÃ y)
â”œâ”€â”€ GÄ1.3 â†’ Graph view                   (ná»­a ngÃ y)
â””â”€â”€ GÄ1.4 â†’ Chat UI + keyword search     (1 ngÃ y)
â†’ Káº¾T QUáº¢: Demo cháº¡y Ä‘Æ°á»£c sau ~3 ngÃ y

CÃ“ FPT_API â†’ lÃ m song song:
â”œâ”€â”€ GÄ0.5 â†’ áº¢nh namecard
â”œâ”€â”€ GÄ0.6 â†’ PDF processing
â””â”€â”€ GÄ2.1 â†’ RAG Engine tháº­t sá»±
```

---

## ðŸ“ CÃC FILE THAM KHáº¢O TÃI Sá»¬ Dá»¤NG

| File cÃ³ sáºµn | DÃ¹ng cho |
|-------------|---------|
| `awesome-ai-apps/rag_apps/pdf_rag_analyser/app.py` | Chat UI + RAG Gemini |
| `llm-wiki/wiki-viewer.html` | Graph visualization |
| `llm-wiki/CLAUDE.md` (Lint section) | Chá»‘ng bá»‹a |
| `awesome-ai-apps/.../test_vector_search.py` | Pattern viáº¿t test |

---

## â“ CÃ’N THIáº¾U Äá»‚ TIáº¾P Tá»¤C

- [ ] `FPT_API` â†’ má»Ÿ khÃ³a GÄ0 (100%) + GÄ2
- [ ] XÃ¡c nháº­n: Demo trÆ°á»›c (GÄ1) hay chá» API key lÃ m Ä‘á»“ng thá»i?

---
*Cáº­p nháº­t láº§n cuá»‘i: 2026-04-12 | Claude (Ká»¹ sÆ°)*
*Gemini review â†’ ghi quyáº¿t Ä‘á»‹nh vÃ o `project_log.md`*


