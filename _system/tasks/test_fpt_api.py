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


api_key = (os.getenv("FPT_API", "") or os.getenv("FPT_API_KEY", "")).strip()
base_url = normalize_base_url(os.getenv("FPT_BASE_URL", "") or os.getenv("FPT_API_URL", ""))
model = os.getenv("FPT_MODEL", "gemma-4-31B-it")

if not api_key:
    print("Loi: khong tim thay FPT_API hoac FPT_API_KEY trong app/backend/.env")
else:
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Chao ban, vui long tra loi ngan gon bang tieng Viet."}
            ],
            temperature=0.2,
            max_tokens=64,
        )
        text = response.choices[0].message.content if response.choices else ""
        print("Ket noi FPT thanh cong")
        print(f"AI tra loi: {text}")
    except Exception as e:
        print(f"Loi ket noi: {e}")
