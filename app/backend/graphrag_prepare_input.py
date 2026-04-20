"""Prepare Microsoft GraphRAG input/*.txt files from LeadsMap vault markdown."""
from __future__ import annotations

import io
import os
import re
from pathlib import Path

from dotenv import load_dotenv

import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

load_dotenv(Path(__file__).parent / ".env")


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "doc"


def _read_docs(vault_base: Path) -> list[tuple[str, Path, str]]:
    docs: list[tuple[str, Path, str]] = []
    sources = [
        ("project", vault_base / "1_project"),
        ("contact", vault_base / "2_contacts"),
    ]

    for doc_type, folder in sources:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                docs.append((doc_type, path, text))
    return docs


def main() -> None:
    backend_dir = Path(__file__).resolve().parent
    graphrag_root = Path(os.getenv("GRAPHRAG_ROOT", str(backend_dir / "graphrag")))
    input_dir = graphrag_root / "input"

    vault_base = Path(os.getenv("VAULT_PATH", "D:/LLM-RAG/HaiVo LeadsMap/HaiVo LeadsMap"))

    docs = _read_docs(vault_base)
    if not docs:
        print(f"No markdown docs found in vault: {vault_base}")
        return

    input_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    for doc_type, src, text in docs:
        slug = _slugify(src.stem)
        out_name = f"{doc_type}-{slug}.txt"
        out_path = input_dir / out_name

        payload = (
            f"DocumentType: {doc_type}\n"
            f"SourceFile: {src.name}\n"
            f"SourcePath: {src}\n\n"
            f"{text}\n"
        )
        out_path.write_text(payload, encoding="utf-8")
        written += 1

    print("=== GraphRAG Input Prepared ===")
    print(f"Vault      : {vault_base}")
    print(f"Output dir : {input_dir}")
    print(f"Files      : {written}")
    print("Next: run GraphRAG index in workspace root.")


if __name__ == "__main__":
    main()
