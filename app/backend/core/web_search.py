"""Web search via DuckDuckGo — no API key required.

Uses the `duckduckgo-search` package (pip install duckduckgo-search).
Falls back gracefully if the package is not installed.
"""
from __future__ import annotations

import asyncio
from typing import Optional


async def search_web(query: str, max_results: int = 6) -> list[dict]:
    """Search the web and return a list of results.

    Each result: {"title": str, "url": str, "snippet": str}
    Returns an empty list on error or if package not installed.
    """
    try:
        from duckduckgo_search import DDGS  # type: ignore

        loop = asyncio.get_event_loop()
        raw: list[dict] = await loop.run_in_executor(
            None,
            lambda: list(DDGS().text(query, max_results=max_results)),
        )
        return [
            {
                "title":   r.get("title", ""),
                "url":     r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in raw
            if r.get("title") or r.get("body")
        ]

    except ImportError:
        print(
            "[web_search] duckduckgo-search not installed. "
            "Run: pip install duckduckgo-search --break-system-packages"
        )
        return []

    except Exception as e:
        print(f"[web_search] Search error: {e}")
        return []


def format_search_results(results: list[dict], query: str) -> str:
    """Format search results into a context string for LLM synthesis."""
    if not results:
        return f"Không tìm thấy kết quả nào cho: '{query}'"

    lines = [f"=== KẾT QUẢ TÌM KIẾM WEB: '{query}' ===\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}")
        if r["snippet"]:
            lines.append(f"    {r['snippet'][:300]}")
        if r["url"]:
            lines.append(f"    Nguồn: {r['url']}")
        lines.append("")

    return "\n".join(lines)
