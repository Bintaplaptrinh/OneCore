# GraphRAG Workspace

This folder is the Microsoft GraphRAG workspace used by backend query flow.

## 1) Initialize

From this folder, run:

```bash
graphrag init
```

This creates `.env`, `settings.yml` and keeps `input/` for source documents.

## 2) Configure models for FPT + Gemma4

Update `.env`:

```env
GRAPHRAG_API_KEY=<your_fpt_api_key>
GRAPHRAG_API_BASE=https://mkp-api.fptcloud.com
```

Update `settings.yml` model blocks to use LiteLLM OpenAI provider:

```yml
completion_models:
  default_completion_model:
    type: litellm
    model_provider: openai
    model: gemma-4-31B-it
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
    api_base: ${GRAPHRAG_API_BASE}

embedding_models:
  default_embedding_model:
    type: litellm
    model_provider: openai
    model: multilingual-e5-large
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
    api_base: ${GRAPHRAG_API_BASE}
```

## 3) Prepare input and index

From project root:

```bash
python app/backend/graphrag_prepare_input.py
app\build_index.bat
```

## 4) Query check

```bash
cd app/backend/graphrag
graphrag query "Top themes in this dataset" --method global
graphrag query "Who is ... and related entities?" --method local
```
