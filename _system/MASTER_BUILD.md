# ðŸ—ï¸ MASTER BUILD â€” HaiVo LeadsMap Intelligence System
**PhiÃªn báº£n:** 2.0 | **Cáº­p nháº­t:** 2026-04-12
**Ká»¹ sÆ°:** Claude | **GiÃ¡m Ä‘á»‘c:** Gemini | **KhÃ¡ch hÃ ng:** HoÃ ng VÄƒn

---

## ðŸŽ¯ Táº§m nhÃ¬n Sáº£n pháº©m

> **"Kho tri thá»©c thÃ´ng minh"** cho cÃ´ng ty báº¥t Ä‘á»™ng sáº£n.
> KhÃ´ng Ä‘oÃ¡n mÃ² â€” chá»‰ nÃ³i nhá»¯ng gÃ¬ cÃ³ trong dá»¯ liá»‡u.
> Äáº¹p nhÆ° SaaS, nhanh nhÆ° desktop app, thÃ´ng minh nhÆ° ChatGPT ná»™i bá»™.

**NgÆ°á»i dÃ¹ng:**
- ðŸ‘¨â€ðŸ’¼ **GiÃ¡m Ä‘á»‘c** â†’ NhÃ¬n bao quÃ¡t, xuáº¥t bÃ¡o cÃ¡o, ra quyáº¿t Ä‘á»‹nh
- ðŸ•µï¸ **Sales** â†’ TÃ¬m nhanh dá»± Ã¡n, contacts, lá»‹ch sá»­
- ðŸ—„ï¸ **Admin** â†’ Upload file â†’ há»‡ thá»‘ng tá»± xá»­ lÃ½

---

## ðŸ› ï¸ TECH STACK ÄÃƒ CHá»T

### Frontend
| CÃ´ng nghá»‡ | Vai trÃ² | LÃ½ do chá»n |
|-----------|---------|-----------|
| **Next.js 14** | Web framework | App routing, SSR, modern React |
| **Tailwind CSS** | Styling | Utility-first, responsive nhanh |
| **shadcn/ui** | Component library | Äáº¹p nháº¥t 2024-2025, customizable |
| **react-force-graph-3d** | Graph 3D | "VÅ© trá»¥" node visualization, xoay/zoom Ä‘Æ°á»£c |
| **Recharts** | Biá»ƒu Ä‘á»“ dashboard | Nháº¹, Ä‘áº¹p, React-native |
| **TanStack Table** | Data table | Sort/filter/pagination mÆ°á»£t |

**TÃ´ng mÃ u:** Dark Professional
```css
--bg:        #0A0A0F   /* ná»n chÃ­nh â€” gáº§n Ä‘en hÆ¡i tÃ­m */
--surface:   #111118   /* card, panel */
--border:    #1E1E2E   /* viá»n */
--text:      #E2E8F0   /* chá»¯ chÃ­nh */
--text2:     #64748B   /* chá»¯ phá»¥ */
--accent:    #6366F1   /* indigo â€” accent chÃ­nh */

/* Node colors trong graph */
--node-project:    #6366F1  /* indigo â€” dá»± Ã¡n */
--node-developer:  #F59E0B  /* amber â€” chá»§ Ä‘áº§u tÆ° */
--node-contractor: #10B981  /* emerald â€” nhÃ  tháº§u */
--node-person:     #EC4899  /* pink â€” ngÆ°á»i */
--node-consultant: #8B5CF6  /* violet â€” tÆ° váº¥n */
```

### Backend
| CÃ´ng nghá»‡ | Vai trÃ² | LÃ½ do chá»n |
|-----------|---------|-----------|
| **FastAPI** | API server | Async, tá»± document, type-safe |
| **Python 3.11+** | Logic xá»­ lÃ½ | AI/data ecosystem tá»‘t nháº¥t |
| **SQLite** | Cache layer | Nháº¹, khÃ´ng cáº§n server, query nhanh |
| **LanceDB** | Vector DB | NhÃºng vÃ o Python, khÃ´ng cáº§n server |
| **google-generativeai** | FPT API | Multimodal, context 2M token |
| **python-frontmatter** | Parse MD | Äá»c YAML frontmatter tá»« vault |
| **openpyxl / pandas** | Excel | Xá»­ lÃ½ dá»¯ liá»‡u cáº¥u trÃºc |

### AI / LLM
| Model | DÃ¹ng cho | Temperature | LÃ½ do |
|-------|---------|-------------|-------|
| `gemma-4-31B-it` | Chatbot RAG, OCR namecard | 0.0 | Nhanh, ráº», Ä‘á»§ chÃ­nh xÃ¡c |
| `gemma-4-31B-it` | PDF scan lá»›n, báº£n váº½ | 0.0 | Context 2M token, multimodal máº¡nh |
| `multilingual-e5-large` | Táº¡o vectors cho LanceDB | â€” | Gemini embedding chuáº©n |

### DevOps / Deploy
| CÃ´ng cá»¥ | DÃ¹ng cho |
|---------|---------|
| **ngrok** | Demo nhanh (share link tá»©c thÃ¬) |
| **Vercel** | Deploy Next.js frontend (free) |
| **Railway / Render** | Deploy FastAPI backend |
| **python-dotenv** | Quáº£n lÃ½ API keys |

---

## ðŸ“ Cáº¤U TRÃšC FILE Äáº¦Y Äá»¦

```
D:/LLM-RAG/
â”‚
â”œâ”€â”€ pipeline/                          â† Scripts xá»­ lÃ½ dá»¯ liá»‡u
â”‚   â”œâ”€â”€ excel_to_md.py                 âœ… DONE
â”‚   â”œâ”€â”€ slug_generator.py              âœ… DONE
â”‚   â”œâ”€â”€ stakeholder_parser.py          âœ… DONE
â”‚   â”œâ”€â”€ link_registry.py               âœ… DONE
â”‚   â”œâ”€â”€ link_registry.json             âœ… DONE (977 entries)
â”‚   â”œâ”€â”€ csv_to_md.py                   âŒ Phase 1
â”‚   â”œâ”€â”€ fpt_ocr.py                  âŒ Phase 2
â”‚   â”œâ”€â”€ fpt_vision.py               âŒ Phase 2
â”‚   â”œâ”€â”€ pdf_parser.py                  âŒ Phase 2
â”‚   â”œâ”€â”€ cache_builder.py               âŒ Phase 1
â”‚   â”œâ”€â”€ lancedb_indexer.py             âŒ Phase 2
â”‚   â”œâ”€â”€ vault_lint.py                  âŒ Phase 3
â”‚   â””â”€â”€ ground_truth_test.py           âŒ Phase 2
â”‚
â”œâ”€â”€ backend/                           â† FastAPI server
â”‚   â”œâ”€â”€ main.py                        âŒ Phase 1
â”‚   â”œâ”€â”€ .env                           â† FPT_API (khÃ´ng commit)
â”‚   â”œâ”€â”€ requirements.txt               âŒ Phase 1
â”‚   â”œâ”€â”€ routers/
â”‚   â”‚   â”œâ”€â”€ projects.py                âŒ GET /projects, /projects/{slug}
â”‚   â”‚   â”œâ”€â”€ contacts.py                âŒ GET /contacts, /search
â”‚   â”‚   â”œâ”€â”€ graph.py                   âŒ GET /graph-data (JSON cho 3D graph)
â”‚   â”‚   â”œâ”€â”€ chat.py                    âŒ POST /chat (RAG + Gemini)
â”‚   â”‚   â”œâ”€â”€ upload.py                  âŒ POST /upload (file â†’ pipeline)
â”‚   â”‚   â””â”€â”€ export.py                  âŒ GET /export/excel, /export/pdf
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ db.py                      âŒ SQLite connection + queries
â”‚   â”‚   â”œâ”€â”€ rag_engine.py              âŒ LanceDB + Gemini RAG
â”‚   â”‚   â”œâ”€â”€ citation.py                âŒ Anti-hallucination validator
â”‚   â”‚   â””â”€â”€ md_parser.py               âŒ Äá»c vault â†’ dict/DataFrame
â”‚   â””â”€â”€ models/
â”‚       â”œâ”€â”€ project.py                 âŒ Pydantic models
â”‚       â””â”€â”€ contact.py                 âŒ Pydantic models
â”‚
â””â”€â”€ frontend/                          â† Next.js app
    â”œâ”€â”€ package.json                   âŒ Phase 1
    â”œâ”€â”€ tailwind.config.ts             âŒ Phase 1
    â”œâ”€â”€ app/
    â”‚   â”œâ”€â”€ layout.tsx                 âŒ Global layout + sidebar
    â”‚   â”œâ”€â”€ page.tsx                   âŒ Redirect â†’ /dashboard
    â”‚   â”œâ”€â”€ dashboard/page.tsx         âŒ Phase 1
    â”‚   â”œâ”€â”€ graph/page.tsx             âŒ Phase 2
    â”‚   â”œâ”€â”€ chat/page.tsx              âŒ Phase 2
    â”‚   â”œâ”€â”€ contacts/page.tsx          âŒ Phase 2
    â”‚   â””â”€â”€ upload/page.tsx            âŒ Phase 3
    â”œâ”€â”€ components/
    â”‚   â”œâ”€â”€ ui/                        â† shadcn/ui components
    â”‚   â”œâ”€â”€ MetricCard.tsx             âŒ
    â”‚   â”œâ”€â”€ ProjectTable.tsx           âŒ
    â”‚   â”œâ”€â”€ GraphViewer.tsx            âŒ react-force-graph-3d
    â”‚   â”œâ”€â”€ ChatWindow.tsx             âŒ
    â”‚   â”œâ”€â”€ UploadZone.tsx             âŒ
    â”‚   â””â”€â”€ Sidebar.tsx                âŒ
    â””â”€â”€ lib/
        â”œâ”€â”€ api.ts                     âŒ fetch helpers â†’ FastAPI
        â””â”€â”€ types.ts                   âŒ TypeScript interfaces
```

---

## ðŸš¦ 4 GIAI ÄOáº N BUILD

---

### GIAI ÄOáº N 1 â€” Ná»€N Táº¢NG (KhÃ´ng cáº§n API key)
**Má»¥c tiÃªu:** Dashboard báº£ng dá»¯ liá»‡u cháº¡y Ä‘Æ°á»£c, filter Ä‘Æ°á»£c, export Ä‘Æ°á»£c
**Thá»i gian:** 2-3 ngÃ y

#### Viá»‡c cáº§n lÃ m:

**Backend:**
- [ ] `pipeline/csv_to_md.py` â€” Ä‘á»c contacts.csv â†’ contact.md
- [ ] `pipeline/cache_builder.py` â€” Ä‘á»c 104 project.md â†’ SQLite
- [ ] `backend/main.py` â€” FastAPI entry point + CORS
- [ ] `backend/routers/projects.py` â€” GET /projects (filter: tá»‰nh, CÄT, loáº¡i, nÄƒm)
- [ ] `backend/routers/export.py` â€” GET /export/excel
- [ ] `backend/core/db.py` â€” SQLite schema + queries
- [ ] `backend/core/md_parser.py` â€” parse YAML frontmatter

**Frontend:**
- [ ] Next.js init + Tailwind + shadcn/ui setup
- [ ] `app/layout.tsx` â€” sidebar + navigation
- [ ] `app/dashboard/page.tsx` â€” metric cards + table + filters
- [ ] `components/ProjectTable.tsx` â€” TanStack Table
- [ ] Export Excel button

**Test Giai Ä‘oáº¡n 1:**
```
âœ… PASS náº¿u:
â–¡ App load < 2 giÃ¢y
â–¡ Filter "Tá»‰nh = HÃ  Ná»™i" â†’ Ä‘Ãºng sá»‘ dá»± Ã¡n khá»›p Excel gá»‘c
â–¡ Filter káº¿t há»£p (Tá»‰nh + CÄT) â†’ káº¿t quáº£ Ä‘Ãºng
â–¡ Export Excel â†’ file táº£i Ä‘Æ°á»£c, dá»¯ liá»‡u khá»›p 100%
â–¡ Metric cards hiá»ƒn thá»‹ Ä‘Ãºng tá»•ng (104 dá»± Ã¡n, 749 contacts)
```

---

### GIAI ÄOáº N 2 â€” AI + GRAPH (Cáº§n FPT_API âœ…)
**Má»¥c tiÃªu:** Graph 3D Ä‘áº¹p + Chatbot thÃ´ng minh khÃ´ng bá»‹a
**Thá»i gian:** 3-4 ngÃ y

#### Viá»‡c cáº§n lÃ m:

**Pipeline AI:**
- [ ] `pipeline/fpt_ocr.py` â€” NameCard.jpg â†’ JSON â†’ contact.md
- [ ] `pipeline/fpt_vision.py` â€” PDF scan/PNG â†’ project metadata
- [ ] `pipeline/pdf_parser.py` â€” PDF text â†’ chunks â†’ LanceDB
- [ ] `pipeline/lancedb_indexer.py` â€” táº¥t cáº£ MD â†’ vectors

**Backend RAG:**
- [ ] `backend/routers/chat.py` â€” POST /chat
- [ ] `backend/core/rag_engine.py` â€” metadata filter + vector search + Gemini call
- [ ] `backend/core/citation.py` â€” validate source citations
- [ ] `backend/routers/graph.py` â€” GET /graph-data (nodes + edges JSON)

**Frontend:**
- [ ] `app/graph/page.tsx` â€” react-force-graph-3d
- [ ] `components/GraphViewer.tsx` â€” toggle clusters, zoom, click node
- [ ] `app/chat/page.tsx` â€” chat UI vá»›i citation display
- [ ] `app/contacts/page.tsx` â€” danh báº¡ + search

**Test Giai Ä‘oáº¡n 2:**
```
âœ… PASS náº¿u:
â–¡ Graph hiá»ƒn thá»‹ > 100 nodes cÃ³ liÃªn káº¿t
â–¡ Click node â†’ hiá»‡n Ä‘Ãºng thÃ´ng tin
â–¡ Toggle "Dá»± Ã¡n only" â†’ chá»‰ hiá»‡n project nodes
â–¡ Ground truth test 20/20 cÃ¢u Ä‘Ãºng (xem bÃªn dÆ°á»›i)
â–¡ CÃ¢u khÃ´ng cÃ³ dá»¯ liá»‡u â†’ tráº£ lá»i "KhÃ´ng cÃ³ thÃ´ng tin"
â–¡ Má»i cÃ¢u tráº£ lá»i cÃ³ [Source: file.md]
â–¡ NameCard.jpg â†’ Ä‘Ãºng tÃªn/SÄT/email
```

**Ground Truth Test (20 cÃ¢u â€” pháº£i pass 20/20):**
```python
TEST_CASES = [
    # Tá»« Excel data â€” biáº¿t cháº¯c Ä‘Ã¡p Ã¡n
    {"q": "Wink Hotel á»Ÿ tá»‰nh nÃ o?",              "must_contain": "Háº£i PhÃ²ng"},
    {"q": "Chá»§ Ä‘áº§u tÆ° The GiÃ³ Riverside lÃ  ai?", "must_contain": "An Gia"},
    {"q": "SÄT cá»§a Nguyá»…n ChÃ­ Äá»©c?",            "must_contain": "3855263"},
    {"q": "Dá»± Ã¡n nÃ o á»Ÿ HÃ  Ná»™i?",                "must_contain": ["project list"]},
    {"q": "Coteccons lÃ  nhÃ  tháº§u dá»± Ã¡n nÃ o?",    "must_contain": ["project list"]},
    # ... 15 cÃ¢u ná»¯a tá»« Excel
    
    # Test khÃ´ng bá»‹a
    {"q": "GiÃ¡ cá»• phiáº¿u An Gia hÃ´m nay?",       "must_say": "khÃ´ng cÃ³ thÃ´ng tin"},
    {"q": "Sá»‘ Ä‘iá»‡n thoáº¡i cá»§a Obama?",            "must_say": "khÃ´ng cÃ³ thÃ´ng tin"},
]
```

---

### GIAI ÄOáº N 3 â€” UPLOAD + LINT
**Má»¥c tiÃªu:** Admin tá»± upload file, há»‡ thá»‘ng tá»± xá»­ lÃ½
**Thá»i gian:** 2 ngÃ y

#### Viá»‡c cáº§n lÃ m:

- [ ] `backend/routers/upload.py` â€” nháº­n file â†’ detect type â†’ cháº¡y Ä‘Ãºng pipeline
- [ ] `frontend/app/upload/page.tsx` â€” drag & drop zone, progress bar
- [ ] `pipeline/vault_lint.py` â€” kiá»ƒm tra broken links, orphan files, conflicts
- [ ] Auto-rebuild SQLite + LanceDB sau má»—i upload

**Test Giai Ä‘oáº¡n 3:**
```
âœ… PASS náº¿u:
â–¡ Upload Excel â†’ contacts xuáº¥t hiá»‡n trong dashboard trong < 30s
â–¡ Upload JPG namecard â†’ contact má»›i trong < 20s, thÃ´ng tin Ä‘Ãºng
â–¡ Upload PDF â†’ chunks vÃ o LanceDB, chat Ä‘Æ°á»£c há»i vá» nÃ³
â–¡ Upload file trÃ¹ng â†’ khÃ´ng táº¡o duplicate
â–¡ Lint phÃ¡t hiá»‡n broken link â†’ hiá»‡n cáº£nh bÃ¡o
```

---

### GIAI ÄOáº N 4 â€” POLISH + DEPLOY
**Má»¥c tiÃªu:** Äáº¹p hoÃ n chá»‰nh, deploy Ä‘Æ°á»£c, share link cho khÃ¡ch
**Thá»i gian:** 1-2 ngÃ y

- [ ] Animation transitions giá»¯a cÃ¡c tab
- [ ] Mobile responsive (giÃ¡m Ä‘á»‘c xem trÃªn Ä‘iá»‡n thoáº¡i Ä‘Æ°á»£c)
- [ ] Loading skeletons (khÃ´ng hiá»‡n trang tráº¯ng khi load)
- [ ] Error states (khi API fail)
- [ ] Deploy frontend â†’ Vercel
- [ ] Deploy backend â†’ Railway/Render
- [ ] Setup environment variables production
- [ ] Test end-to-end trÃªn mÃ´i trÆ°á»ng production

---

## ðŸ§ª CHIáº¾N LÆ¯á»¢C TEST & ÄÃNH GIÃ

### Má»—i ngÃ y build xong â†’ cháº¡y test nÃ y:

```
Checklist cuá»‘i ngÃ y:
â–¡ API endpoint má»›i â†’ test báº±ng curl/Postman
â–¡ UI má»›i â†’ check trÃªn Chrome + Edge
â–¡ Data má»›i â†’ verify khá»›p vá»›i Excel gá»‘c
â–¡ Performance â†’ load time < 2s
â–¡ Console errors â†’ pháº£i = 0
```

### Test tá»± Ä‘á»™ng (cháº¡y trÆ°á»›c khi deploy):

```python
# ground_truth_test.py â€” cháº¡y: python pipeline/ground_truth_test.py
# Káº¿t quáº£: PASS (x/20) hoáº·c FAIL + cÃ¢u nÃ o sai

# ThÃªm: API endpoint tests
# pytest backend/tests/
```

### ÄÃ¡nh giÃ¡ cháº¥t lÆ°á»£ng RAG:

| TiÃªu chÃ­ | Má»¥c tiÃªu | Äo báº±ng cÃ¡ch |
|---------|---------|-------------|
| CÃ¢u tráº£ lá»i Ä‘Ãºng | 20/20 ground truth | ground_truth_test.py |
| CÃ³ citation | 100% cÃ¢u tráº£ lá»i | citation.py validator |
| KhÃ´ng bá»‹a | 0 hallucination | Test cÃ¢u khÃ´ng cÃ³ data |
| Tá»‘c Ä‘á»™ chat | < 3 giÃ¢y/cÃ¢u | Log API response time |
| Tá»‘c Ä‘á»™ load | < 2 giÃ¢y | Browser DevTools |

---

## ðŸ› BUG LOG & FIX HISTORY

### Format ghi bug:
```
[DATE] BUG: <mÃ´ táº£>
      ROOT CAUSE: <nguyÃªn nhÃ¢n>
      FIX: <Ä‘Ã£ sá»­a báº±ng cÃ¡ch>
      FILE: <file Ä‘Ã£ thay Ä‘á»•i>
      STATUS: âœ… Fixed / â³ Pending
```

---

### Bugs Ä‘Ã£ fix (tá»« Module 1):

**[2026-04-12] BUG: UnicodeEncodeError khi print tiáº¿ng Viá»‡t**
- Root cause: Python console Windows dÃ¹ng cp1252, khÃ´ng há»— trá»£ UTF-8
- Fix: `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`
- File: `pipeline/excel_to_md.py` line 8
- Status: âœ… Fixed

**[2026-04-12] BUG: OSError â€” Invalid filename vá»›i kÃ½ tá»± `:` trong tÃªn file**
- Root cause: TÃªn role `"Ká»¹ SÆ° CÆ¡ Äiá»‡n:"` cÃ³ dáº¥u `:` â†’ Windows khÃ´ng cho phÃ©p trong filename
- Fix: `filename = re.sub(r'[\\/:*?"<>|]', '', filename)`
- File: `pipeline/excel_to_md.py` â€” hÃ m `create_contact_file()`
- Status: âœ… Fixed

**[2026-04-12] BUG: Stakeholder parser bá» sÃ³t ngÆ°á»i khÃ´ng cÃ³ cÃ´ng ty**
- Root cause: Parser chá»‰ nháº­n format `"CÃ´ng ty, Ã”ng X - Chá»©c vá»¥"`, bá» qua `"; BÃ  X - Chá»©c vá»¥"`
- Fix: ThÃªm regex `title_start` cho format khÃ´ng cÃ³ cÃ´ng ty
- File: `pipeline/stakeholder_parser.py` line 139-151
- Status: âœ… Fixed

---

### Bugs Ä‘ang theo dÃµi:

*(Cáº­p nháº­t khi phÃ¡t hiá»‡n bug má»›i)*

---

## ðŸ“Š TIáº¾N Äá»˜ THá»°C Táº¾

```
GIAI ÄOáº N 0 â€” Dá»¯ liá»‡u ná»n      â–“â–“â–“â–“â–“â–“â–“â–‘â–‘â–‘  75%
  âœ… Excel â†’ 104 project.md
  âœ… Stakeholder â†’ 749 contact.md
  âœ… Link Registry 977 entries
  âŒ CSV/Excel phá»¥ â†’ contacts
  âŒ Namecard OCR â†’ contacts
  âŒ PDF/áº£nh â†’ project metadata

GIAI ÄOáº N 1 â€” Dashboard         â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%
  âŒ FastAPI backend
  âŒ SQLite cache
  âŒ Next.js + báº£ng dá»± Ã¡n
  âŒ Export Excel

GIAI ÄOáº N 2 â€” AI + Graph        â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%
  âŒ LanceDB vector index
  âŒ RAG chatbot
  âŒ Graph 3D viewer
  âŒ Ground truth 20/20 pass

GIAI ÄOáº N 3 â€” Upload + Lint     â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%
GIAI ÄOáº N 4 â€” Deploy            â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘   0%

Tá»”NG Dá»° ÃN                      â–“â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘â–‘  15%
```

---

## âš¡ Lá»†NH CHáº Y NHANH

```bash
# Cháº¡y pipeline xá»­ lÃ½ data
cd D:/LLM-RAG/pipeline
python cache_builder.py          # Build SQLite tá»« vault
python ground_truth_test.py      # Test RAG accuracy

# Cháº¡y backend
cd D:/LLM-RAG/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Cháº¡y frontend
cd D:/LLM-RAG/frontend
npm install
npm run dev                      # http://localhost:3000

# Demo share
ngrok http 3000                  # â†’ link public cho khÃ¡ch xem

# Xem API docs
open http://localhost:8000/docs  # FastAPI auto-docs
```

---

## ðŸ”‘ ENVIRONMENT VARIABLES

```env
# backend/.env â€” KHÃ”NG commit file nÃ y lÃªn git
FPT_API=...           âœ… ÄÃ£ cÃ³
FPT_MODEL=gemma-4-31B-it
FPT_MODEL=gemma-4-31B-it
FPT_EMBEDDING_MODEL=multilingual-e5-large

VAULT_PATH=D:/LLM-RAG/HaiVo LeadsMap/HaiVo LeadsMap
PIPELINE_PATH=D:/LLM-RAG/pipeline
SQLITE_PATH=D:/LLM-RAG/backend/leadsmap.db
LANCEDB_PATH=D:/LLM-RAG/backend/lancedb

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ðŸ“¦ PACKAGES Cáº¦N CÃ€I

```bash
# Backend Python
pip install fastapi uvicorn python-dotenv
pip install google-generativeai>=0.8.0
pip install llama-index-core llama-index-readers-file
pip install lancedb>=0.5.0
pip install openpyxl pandas python-frontmatter
pip install python-docx xlsxwriter
pip install python-multipart  # for file upload

# Frontend Node
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npx shadcn@latest init
npm install react-force-graph-3d three
npm install @tanstack/react-table
npm install recharts
npm install lucide-react  # icons
```

---

## ðŸ“‹ CÃC FILE THAM KHáº¢O TÃI Sá»¬ Dá»¤NG

| File gá»‘c | DÃ¹ng cho | Láº¥y gÃ¬ |
|----------|---------|--------|
| `llm-wiki/wiki-viewer.html` | Ã tÆ°á»Ÿng graph + CSS dark theme | Color palette, node physics |
| `pdf_rag_analyser/app.py` | Chat UI pattern + Gemini call | Session state, chat bubbles, Gemini setup |
| `agentic_rag/main.py` | LanceDB setup pattern | Index creation, query pattern |
| `talk_to_db/app.py` | Textâ†’SQL pattern | SQLite query generation |
| `temporal_agent/app.py` | Dashboard CSS | Metric card CSS, badge styling |

---

*MASTER_BUILD.md â€” Claude (Ká»¹ sÆ°) | 2026-04-12*
*Review: Gemini (GiÃ¡m Ä‘á»‘c) | Approved: HoÃ ng VÄƒn*


