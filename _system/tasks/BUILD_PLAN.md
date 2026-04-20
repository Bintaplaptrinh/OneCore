# ðŸ—ï¸ BUILD PLAN â€” HaiVo LeadsMap (Ká»¹ sÆ° Claude)
**Cáº­p nháº­t:** 2026-04-12 | **Tráº¡ng thÃ¡i:** CONFIRMED â€” CÃ³ FPT_API âœ…

---

## ðŸ—‚ï¸ Cáº¥u trÃºc Code Sáº½ Táº¡o

```
D:/LLM-RAG/
â”œâ”€â”€ pipeline/                     â† Scripts xá»­ lÃ½ dá»¯ liá»‡u
â”‚   â”œâ”€â”€ excel_to_md.py            âœ… DONE
â”‚   â”œâ”€â”€ slug_generator.py         âœ… DONE
â”‚   â”œâ”€â”€ stakeholder_parser.py     âœ… DONE
â”‚   â”œâ”€â”€ link_registry.py          âœ… DONE
â”‚   â”œâ”€â”€ link_registry.json        âœ… DONE (977 entries)
â”‚   â”œâ”€â”€ csv_to_md.py              âŒ Cáº¦N BUILD
â”‚   â”œâ”€â”€ fpt_ocr.py             âŒ Cáº¦N BUILD (namecard)
â”‚   â”œâ”€â”€ fpt_vision.py          âŒ Cáº¦N BUILD (PDF scan/áº£nh)
â”‚   â”œâ”€â”€ pdf_parser.py             âŒ Cáº¦N BUILD (PDF text)
â”‚   â”œâ”€â”€ cache_builder.py          âŒ Cáº¦N BUILD (SQLite)
â”‚   â”œâ”€â”€ lancedb_indexer.py        âŒ Cáº¦N BUILD (vectors)
â”‚   â””â”€â”€ ground_truth_test.py      âŒ Cáº¦N BUILD (test suite)
â”‚
â””â”€â”€ demo/                         â† Web App (Streamlit)
    â”œâ”€â”€ app.py                    âŒ Entry point
    â”œâ”€â”€ .env                      â† FPT_API (khÃ´ng commit)
    â”œâ”€â”€ requirements.txt          âŒ
    â”œâ”€â”€ pages/
    â”‚   â”œâ”€â”€ 1_Dashboard.py        âŒ Báº£ng + filter + export
    â”‚   â”œâ”€â”€ 2_Graph.py            âŒ Graph quan há»‡
    â”‚   â””â”€â”€ 3_Chat.py             âŒ RAG Chatbot
    â”œâ”€â”€ core/
    â”‚   â”œâ”€â”€ md_parser.py          âŒ Äá»c vault â†’ DataFrame
    â”‚   â”œâ”€â”€ db.py                 âŒ SQLite queries
    â”‚   â”œâ”€â”€ rag_engine.py         âŒ LanceDB + Gemini RAG
    â”‚   â”œâ”€â”€ citation.py           âŒ Anti-hallucination layer
    â”‚   â””â”€â”€ search.py             âŒ Keyword fallback search
    â””â”€â”€ assets/
        â”œâ”€â”€ graph.html            âŒ Adapted wiki-viewer.html
        â””â”€â”€ style.css             âŒ Custom CSS Streamlit
```

---

## ðŸ“¦ Nguá»“n TÃ¡i Sá»­ Dá»¥ng Tá»« Repo

| Láº¥y tá»« Ä‘Ã¢u | File gá»‘c | DÃ¹ng cho | Sá»­a gÃ¬ |
|-----------|----------|---------|--------|
| `llm-wiki/wiki-viewer.html` | ToÃ n bá»™ | `demo/assets/graph.html` | Äá»•i mÃ u node (dá»± Ã¡n/CÄT/nhÃ  tháº§u), thÃªm filter loáº¡i BÄS |
| `pdf_rag_analyser/app.py` | Chat UI + Gemini call pattern | `demo/pages/3_Chat.py` | Bá» FAISS â†’ LanceDB, thÃªm citation, tiáº¿ng Viá»‡t |
| `agentic_rag/main.py` | LanceDB setup pattern | `pipeline/lancedb_indexer.py` | Äá»•i source tá»« URL â†’ MD files |
| `talk_to_db/app.py` | Textâ†’SQL pattern | `demo/core/db.py` | Äá»•i MySQL â†’ SQLite, viáº¿t láº¡i schema |

---

## ðŸ”„ 5 Pháº§n Cáº§n Build (Chi tiáº¿t)

---

### PHáº¦N 1 â€” DATA PIPELINE

**Má»¥c tiÃªu:** Má»i file input â†’ MD files trong vault

#### Script cáº§n táº¡o:

**`csv_to_md.py`** â€” KhÃ´ng cáº§n API
```
contacts.csv (Ä‘iá»‡n thoáº¡i) â†’ parse columns â†’ contact.md
Cáº§n: Ä‘á»c format CSV trÆ°á»›c, map cá»™t
```

**`fpt_ocr.py`** â€” Cáº§n FPT_API
```
Input: JPG/PNG namecard
Gemini prompt: "Extract Name, Company, Role, Phone, Email as JSON. Return ONLY JSON."
Output: JSON â†’ kiá»ƒm tra link_registry â†’ táº¡o/cáº­p nháº­t contact.md
```

**`fpt_vision.py`** â€” Cáº§n FPT_API
```
Input: PDF scan / PNG cÃ³ thÃ´ng tin dá»± Ã¡n
FPT AI (context lá»›n): gá»­i tá»«ng trang áº£nh
Prompt: "Extract project info: name, location, developer, scale, timeline as JSON"
Output: JSON â†’ táº¡o/cáº­p nháº­t project.md
```

**`pdf_parser.py`** â€” Cáº§n FPT_API
```
Input: PDF cÃ³ text (khÃ´ng pháº£i scan)
LlamaIndex PDF Reader â†’ chunks (1000 token, overlap 200)
â†’ LanceDB (cho chat search)
â†’ Äá»“ng thá»i extract metadata â†’ project.md
```

---

### PHáº¦N 2 â€” KNOWLEDGE STORE

**`cache_builder.py`** â€” KhÃ´ng cáº§n API
```python
# Schema SQLite
CREATE TABLE projects (
  slug TEXT PRIMARY KEY,        -- prj-WinkHaiPhong
  name TEXT,                    -- Wink Hotel Háº£i PhÃ²ng
  province TEXT,                -- Háº£i PhÃ²ng
  district TEXT,
  developer TEXT,               -- An Gia
  value_usd REAL,
  status TEXT,
  phase TEXT,
  address TEXT,
  floors INTEGER,
  source_file TEXT,             -- /1_project/2026 - [[prj-WinkHaiPhong]].md
  updated_at TEXT
);

CREATE TABLE contacts (
  slug TEXT PRIMARY KEY,
  name TEXT,
  company TEXT,
  role TEXT,
  phone TEXT,
  email TEXT,
  source_file TEXT
);

CREATE TABLE relationships (
  project_slug TEXT,
  entity_slug TEXT,
  relationship TEXT,  -- developer/mc/consultant
  FOREIGN KEY ...
);
```

**`lancedb_indexer.py`** â€” Cáº§n embedding API
```
Äá»c táº¥t cáº£ MD files â†’ split chunks
â†’ FPT Embeddings API (multilingual-e5-large)
â†’ LÆ°u vÃ o LanceDB vá»›i metadata (slug, file, loáº¡i)
```

---

### PHáº¦N 3 â€” FRONTEND (Streamlit)

**`demo/app.py`** â€” Entry point
```python
st.set_page_config(
  page_title="HaiVo LeadsMap",
  page_icon="ðŸ¢",
  layout="wide",
  initial_sidebar_state="expanded"
)
# Load custom CSS
# Sidebar navigation
```

**`demo/pages/1_Dashboard.py`**
```
Sidebar filters:
  - Tá»‰nh (multiselect)
  - Loáº¡i cÃ´ng trÃ¬nh (multiselect)
  - Chá»§ Ä‘áº§u tÆ° (multiselect)
  - NÄƒm (slider)
  - GiÃ¡ trá»‹ (range slider)

Main:
  - 4 metric cards: Tá»•ng dá»± Ã¡n / Tá»•ng CÄT / Tá»•ng giÃ¡ trá»‹ / Äang xÃ¢y
  - AgGrid table (sortable, resizable)
  - [Export Excel] [Export PDF bÃ¡o cÃ¡o]
```

**`demo/pages/2_Graph.py`**
```
- st.components.v1.html(open("assets/graph.html").read(), height=700)
- Filter panel phÃ­a trÃªn: lá»c theo loáº¡i node
- HÆ°á»›ng dáº«n: click node â†’ xem chi tiáº¿t
```

**`demo/pages/3_Chat.py`**
```
- Chat input + history (session state)
- Má»—i cÃ¢u tráº£ lá»i: text + [Source: file.md] clickable
- Náº¿u khÃ´ng cÃ³ dá»¯ liá»‡u: "TÃ´i khÃ´ng cÃ³ thÃ´ng tin nÃ y trong CSDL"
- Sidebar: suggested questions
```

**`demo/assets/style.css`** â€” Custom CSS
```css
/* Dark/light theme tÃ¹y chá»n */
/* Sidebar styling */
/* Metric cards */
/* Chat bubbles */
/* Table styling */
/* Export buttons */
```

---

### PHáº¦N 4 â€” RAG ENGINE

**`demo/core/rag_engine.py`**
```
Luá»“ng xá»­ lÃ½:
1. Nháº­n cÃ¢u há»i (tiáº¿ng Viá»‡t)
2. Metadata filter: SQLite WHERE province/developer/type
3. Vector search: LanceDB top-5 chunks tá»« subset
4. Build context: ghÃ©p 5 chunks + source info
5. Gemini call (temperature=0.0):
   System: "Chá»‰ dÃ¹ng context. KhÃ´ng biáº¿t â†’ nÃ³i khÃ´ng biáº¿t."
   User: cÃ¢u há»i + context
6. Parse response â†’ tÃ¡ch citation
7. Return: {answer, sources: [file1.md, file2.md]}
```

**`demo/core/citation.py`**
```
Validate má»—i cÃ¢u tráº£ lá»i:
- Má»i claim pháº£i cÃ³ file nguá»“n
- File nguá»“n pháº£i thá»±c sá»± tá»“n táº¡i trong vault
- Náº¿u khÃ´ng validate Ä‘Æ°á»£c â†’ thÃªm warning
```

---

### PHáº¦N 5 â€” LLM-WIKI / ANTI-HALLUCINATION

**`pipeline/ground_truth_test.py`**
```python
# 20 cÃ¢u tá»« data Excel (biáº¿t Ä‘Ã¡p Ã¡n chÃ­nh xÃ¡c)
TEST_CASES = [
  {"q": "Wink Hotel á»Ÿ Ä‘Ã¢u?", "expected": "Háº£i PhÃ²ng"},
  {"q": "Chá»§ Ä‘áº§u tÆ° The GiÃ³ Riverside?", "expected": "An Gia"},
  {"q": "SÄT Nguyá»…n ChÃ­ Äá»©c?", "expected": "84 274 3855263"},
  # ... 17 cÃ¢u ná»¯a
]
# Cháº¡y tá»«ng cÃ¢u â†’ so sÃ¡nh â†’ bÃ¡o cÃ¡o pass/fail
# Pháº£i 20/20 má»›i deploy chatbot
```

**Lint vault (cháº¡y Ä‘á»‹nh ká»³):**
```
- Broken [[links]] â†’ cáº£nh bÃ¡o
- Contact trÃ¹ng tÃªn nhÆ°ng SÄT khÃ¡c â†’ flag conflict  
- Project khÃ´ng cÃ³ CÄT â†’ cáº£nh bÃ¡o thiáº¿u
```

---

## âš¡ Thá»© Tá»± Build Thá»±c Táº¿

```
NgÃ y 1:
  âœ¦ csv_to_md.py           (30 phÃºt, khÃ´ng cáº§n API)
  âœ¦ cache_builder.py       (2 giá», khÃ´ng cáº§n API)
  âœ¦ demo/app.py + CSS      (1 giá» setup)
  âœ¦ 1_Dashboard.py         (3 giá»)
  â†’ Cuá»‘i ngÃ y: Báº£ng dá»± Ã¡n cháº¡y Ä‘Æ°á»£c, filter Ä‘Æ°á»£c

NgÃ y 2:
  âœ¦ 2_Graph.py             (2 giá», nhÃºng + adapt wiki-viewer.html)
  âœ¦ fpt_ocr.py          (2 giá», xá»­ lÃ½ NameCard.jpg)
  âœ¦ fpt_vision.py       (3 giá», PDF + áº£nh dá»± Ã¡n)
  â†’ Cuá»‘i ngÃ y: Graph view + namecard/PDF Ä‘Ã£ xá»­ lÃ½

NgÃ y 3:
  âœ¦ lancedb_indexer.py     (2 giá»)
  âœ¦ rag_engine.py          (3 giá»)
  âœ¦ 3_Chat.py              (2 giá»)
  âœ¦ ground_truth_test.py   (1 giá»)
  â†’ Cuá»‘i ngÃ y: Chatbot tháº­t, test pass â†’ Demo ready

Deploy:
  âœ¦ ngrok http 8501 â†’ link cho giÃ¡m Ä‘á»‘c xem
```

---

## ðŸ”‘ Environment Setup

```
FPT_API=...   â† ÄÃƒ CÃ“ âœ…
FPT_MODEL=gemma-4-31B-it     â† Ä‘á»c PDF lá»›n
FPT_MODEL=gemma-4-31B-it        â† chatbot (nhanh, ráº»)
VAULT_PATH=D:/LLM-RAG/HaiVo LeadsMap/HaiVo LeadsMap
PIPELINE_PATH=D:/LLM-RAG/pipeline
DEMO_PATH=D:/LLM-RAG/demo
```

---

## ðŸ“¦ Packages Cáº§n CÃ i

```
# Data
openpyxl, pandas, python-frontmatter

# AI
google-generativeai>=0.8.0
llama-index-core
llama-index-readers-file
lancedb>=0.5.0

# Web
streamlit>=1.40.0
streamlit-aggrid

# Export
openpyxl, xlsxwriter, python-docx

# Utils
python-dotenv, pathlib
```

---
*BUILD_PLAN.md â€” Claude (Ká»¹ sÆ°) | 2026-04-12*
*ÄÃ£ confirm: FPT_API cÃ³ sáºµn â†’ unlock toÃ n bá»™ pipeline*


