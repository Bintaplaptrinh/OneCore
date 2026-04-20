import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parents[2] / "app/backend/.env")


def normalize_base_url(raw_url: str) -> str:
    url = raw_url.strip().rstrip("/")
    if not url:
        return "https://mkp-api.fptcloud.com"
    if url.endswith("/chat/completions"):
        return url[: -len("/chat/completions")]
    return url


def test_full_capability() -> None:
    api_key = (os.getenv("FPT_API", "") or os.getenv("FPT_API_KEY", "")).strip()
    if not api_key:
        print("Loi: khong tim thay FPT_API hoac FPT_API_KEY trong app/backend/.env")
        return

    base_url = normalize_base_url(os.getenv("FPT_BASE_URL", "") or os.getenv("FPT_API_URL", ""))
    chat_model = os.getenv("FPT_MODEL", "gemma-4-31B-it")
    embed_model = os.getenv("FPT_EMBEDDING_MODEL", "multilingual-e5-large")
    rerank_model = os.getenv("FPT_RERANKER_MODEL", "bge-reranker-v2-m3")

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        print("Dang test chat model...")
        chat_resp = client.chat.completions.create(
            model=chat_model,
            messages=[{"role": "user", "content": "Tra loi 1 cau ngan bang tieng Viet."}],
            temperature=0.2,
            max_tokens=64,
        )
        chat_text = chat_resp.choices[0].message.content if chat_resp.choices else ""
        print(f"Chat OK: {chat_text}")

        print("Dang test embedding model...")
        try:
            emb_resp = client.embeddings.create(
                model=embed_model,
                input=["input 1", "input 2"],
                dimensions=1024,
                encoding_format="float",
                input_text_truncate="none",
                input_type="passage",
            )
        except TypeError:
            emb_resp = client.embeddings.create(model=embed_model, input=["input 1", "input 2"])

        print(f"Embedding OK: {len(emb_resp.data)} vectors")

        print("Dang test reranker...")
        rerank_resp = client._client.post(
            f"{str(client.base_url).rstrip('/')}/v1/rerank",
            json={
                "model": rerank_model,
                "query": "What is the capital of the United States?",
                "documents": [
                    "Carson City is the capital city of the American state of Nevada.",
                    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
                    "Washington, D.C. is the capital of the United States.",
                    "Capital punishment has existed in the United States since before it was a country.",
                ],
                "top_n": 2,
            },
            headers={
                "Authorization": f"Bearer {client.api_key}",
                "Content-Type": "application/json",
            },
        )
        rerank_resp.raise_for_status()
        print(f"Rerank OK: {rerank_resp.json()}")

        print("\nKET QUA: Tat ca FPT API tests da thanh cong.")
    except Exception as e:
        print(f"Loi ket noi hoac cau hinh API: {e}")


if __name__ == "__main__":
    test_full_capability()
