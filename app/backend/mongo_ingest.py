"""CLI utility: ingest source files into MongoDB via duantaolao pipeline."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from core.mongo_ingest import ingest_file, ingest_folder


def _default_input_dir() -> Path:
    env = os.getenv("VAULT_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    # app/backend -> app -> akhai ; use repo-level input as fallback
    return (Path(__file__).resolve().parents[3] / "LeadsMap_Input Information").resolve()


async def _run() -> int:
    parser = argparse.ArgumentParser(description="Ingest files into MongoDB.")
    parser.add_argument("--path", type=str, default="", help="File or folder path to ingest")
    args = parser.parse_args()

    target = Path(args.path).expanduser().resolve() if args.path else _default_input_dir()
    if not target.exists():
        print(json.dumps({"ok": False, "error": f"Path not found: {target}"}, ensure_ascii=False))
        return 1

    if target.is_file():
        result = await ingest_file(target)
    else:
        result = await ingest_folder(target)

    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_run()))
