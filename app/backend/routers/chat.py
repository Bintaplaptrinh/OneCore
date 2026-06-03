"""Chat endpoint with RAG engine."""
from __future__ import annotations

from pydantic import BaseModel

from core.database import (
    delete_chat_session,
    get_chat_session,
    get_chat_sessions,
    get_query_history,
    save_chat_session,
    save_query_log,
)
from core.rag_engine import get_rag_engine
from core.report_agent import generate_agent_report
from fastapi import APIRouter, HTTPException
from unidecode import unidecode

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model."""

    query: str
    history: list[dict] = []
    style: str = "natural"  # "natural" (default) | "precise" (zero-hallucination)


class Citation(BaseModel):
    """Citation model."""

    name: str
    type: str
    slug: str


class GraphFilter(BaseModel):
    """Graph filter model."""

    province: str = ""
    developer: str = ""
    types: list[str] = []


class PendingMutation(BaseModel):
    """Structured data mutation proposal awaiting user confirmation."""

    operation: str = ""   # insert | update | delete
    entity: str = ""      # project | contact
    display_name: str = ""
    slug: str | None = None
    data: dict | None = None
    changes: dict | None = None
    summary: str = ""


class GeneratedReport(BaseModel):
    """Generated report payload for Chat AI."""

    id: str = ""
    title: str = ""
    summary: str = ""
    html: str = ""
    charts: list[dict] = []
    download_url: str = ""


class ChatResponse(BaseModel):
    """Chat response model."""

    answer: str
    citations: list[Citation]
    context_used: int
    graph_filter: GraphFilter | None = None
    pending_mutation: PendingMutation | None = None
    report: GeneratedReport | None = None


class ChatSessionUpsertRequest(BaseModel):
    """Persisted chat session payload."""

    session_id: str | None = None
    title: str | None = None
    messages: list[dict] = []


def _normalize_history(history: list[dict]) -> list[dict]:
    """Normalize chat history."""
    out: list[dict] = []
    for item in history[-16:]:
        role = str(item.get("role", "user")).strip().lower()
        if role in {"assistant", "model", "ai"}:
            role = "assistant"
        else:
            role = "user"
        content = str(item.get("content", "")).strip()
        if content:
            out.append({"role": role, "content": content})
    return out


def _map_citations(raw: list[dict]) -> list[Citation]:
    """Convert raw citations to Citation models."""
    mapped: list[Citation] = []
    for item in raw:
        name = str(item.get("name") or item.get("title") or item.get("id") or "Source").strip()
        ctype = str(item.get("type") or item.get("entity") or "source").strip()
        slug = str(item.get("slug") or item.get("id") or "").strip()
        if name or slug:
            mapped.append(Citation(name=name, type=ctype, slug=slug))
    return mapped


def _is_report_query(query: str) -> bool:
    q = unidecode(str(query or "").lower())
    triggers = [
        "bao cao",
        "report",
        "analyst",
        "analysis",
        "phan tich",
        "dashboard insight",
        "nhan dinh",
    ]
    return any(trigger in q for trigger in triggers)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat endpoint with RAG engine."""
    try:
        if _is_report_query(req.query):
            report = await generate_agent_report(query=req.query, language="vi")
            generated_report = GeneratedReport(
                id=str(report.get("id") or ""),
                title=str(report.get("title") or ""),
                summary=str(report.get("summary") or ""),
                html=str(report.get("html") or ""),
                charts=report.get("charts") or [],
                download_url=str(report.get("download_url") or ""),
            )
            answer = (
                f"Đã tạo **{generated_report.title}** bằng Agent phân tích.\n\n"
                f"{generated_report.summary}\n\n"
                "Bạn có thể xem bản HTML ngay trong Chat AI hoặc tải bản PDF từ thẻ báo cáo bên dưới."
            )
            try:
                await save_query_log(query=req.query, answer=answer, intent="report")
            except Exception:
                pass
            return ChatResponse(
                answer=answer,
                citations=[Citation(name="CoreOne Report Agent", type="report", slug=generated_report.id)],
                context_used=1,
                graph_filter=GraphFilter(),
                report=generated_report,
            )

        engine = get_rag_engine()
        payload = await engine.answer(
            req.query,
            history=_normalize_history(req.history or []),
            style=str(req.style or "natural"),
        )

        answer = str(payload.get("answer") or "Không có phản hồi.")
        citations = _map_citations(payload.get("citations") or [])

        graph_filter_data = payload.get("graph_filter") or {}
        raw_types = graph_filter_data.get("types")
        if isinstance(raw_types, list):
            mapped_types = [str(x) for x in raw_types if str(x).strip()]
        elif isinstance(raw_types, str) and raw_types.strip():
            mapped_types = [raw_types.strip()]
        else:
            mapped_types = []

        graph_filter = GraphFilter(
            province=str(graph_filter_data.get("province") or ""),
            developer=str(graph_filter_data.get("company") or graph_filter_data.get("developer") or ""),
            types=mapped_types,
        )

        # Build pending_mutation if present
        pending_mutation: PendingMutation | None = None
        raw_mutation = payload.get("pending_mutation")
        if isinstance(raw_mutation, dict) and raw_mutation.get("operation"):
            try:
                pending_mutation = PendingMutation(
                    operation=str(raw_mutation.get("operation") or ""),
                    entity=str(raw_mutation.get("entity") or ""),
                    display_name=str(raw_mutation.get("display_name") or ""),
                    slug=raw_mutation.get("slug") or None,
                    data=raw_mutation.get("data") or None,
                    changes=raw_mutation.get("changes") or None,
                    summary=str(raw_mutation.get("summary") or ""),
                )
            except Exception:
                pass

        try:
            await save_query_log(
                query=req.query,
                answer=answer,
                intent=str(payload.get("intent") or "general"),
            )
        except Exception:
            pass

        return ChatResponse(
            answer=answer,
            citations=citations,
            context_used=int(payload.get("context_used") or payload.get("num_sources") or len(citations)),
            graph_filter=graph_filter,
            pending_mutation=pending_mutation,
        )

    except Exception as exc:
        print(f"[chat] Error: {exc}")
        return ChatResponse(
            answer=f"Lỗi xử lý: {str(exc)}",
            citations=[],
            context_used=0,
            graph_filter=GraphFilter(),
        )


@router.get("/chat/history")
async def chat_history(limit: int = 30):
    """Get chat history."""
    history = await get_query_history(limit)
    return {"data": history}


@router.delete("/chat/history/{log_id}")
async def delete_chat_history(log_id: str):
    """Delete a single chat history entry by id."""
    from core.database import delete_query_log
    success = await delete_query_log(log_id)
    return {"success": success}


@router.get("/chat/sessions")
async def chat_sessions(limit: int = 30):
    """Get recent chat sessions with message counts."""
    sessions = await get_chat_sessions(limit)
    return {"data": sessions}


@router.get("/chat/sessions/{session_id}")
async def chat_session_detail(session_id: str):
    """Get a full chat session by id."""
    session = await get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"data": session}


@router.post("/chat/sessions")
async def upsert_chat_session(req: ChatSessionUpsertRequest):
    """Create or update a full chat session."""
    session_id = await save_chat_session(
        messages=req.messages or [],
        title=str(req.title or ""),
        session_id=req.session_id,
    )
    if not session_id:
        raise HTTPException(status_code=400, detail="Session has no valid messages")
    return {"success": True, "id": session_id}


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session by id."""
    success = await delete_chat_session(session_id)
    return {"success": success}
