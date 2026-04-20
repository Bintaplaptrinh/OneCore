"use client";

import { useState, useRef, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Network,
  Table2,
  FileSpreadsheet,
} from "lucide-react";
import { motion } from "framer-motion";
import { api, invalidateGraphCache, GraphFilter, Citation } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TableData {
  headers: string[];
  rows: string[][];
}

interface Message {
  role: "user" | "ai";
  content: string;
  loading?: boolean;
  graphFilter?: GraphFilter | null;
  tableData?: TableData | null;
  citations?: Citation[];
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseMarkdownTable(text: string): TableData | null {
  const lines = text.trim().split("\n").filter((l) => l.trim().startsWith("|"));
  if (lines.length < 3) return null;
  const parseRow = (line: string) =>
    line.split("|").slice(1, -1).map((c) => c.trim());
  const headers = parseRow(lines[0]);
  const rows = lines.slice(2).map(parseRow).filter((r) => r.some((c) => c));
  if (headers.length === 0) return null;
  return { headers, rows };
}

function hasGraphFilter(gf: GraphFilter | null | undefined): boolean {
  if (!gf) return false;
  return Boolean(gf.province || gf.developer);
}

// Strip markdown table block from display text so the bubble stays compact
function stripTableFromContent(content: string): string {
  const lines = content.split("\n");
  const result: string[] = [];
  let inTable = false;
  for (const line of lines) {
    if (line.trim().startsWith("|")) {
      inTable = true;
      continue;
    }
    if (inTable && line.trim() === "") {
      inTable = false;
      continue;
    }
    inTable = false;
    result.push(line);
  }
  return result.join("\n").trim();
}

// ---------------------------------------------------------------------------
// Quick-starter prompts
// ---------------------------------------------------------------------------

const QUICK_STARTERS = [
  "SĐT chủ thầu ở Đà Nẵng",
  "Dự án Vingroup đang xây",
  "Tạo bảng liên hệ theo tỉnh",
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 px-1 py-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-[#6366F1] opacity-80"
          style={{
            animation: "floatingChatBounce 1.2s infinite",
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

interface MessageBubbleProps {
  msg: Message;
  onExcelExport: (tableData: TableData, title: string) => void;
  onOpenTable: (tableData: TableData) => void;
  onOpenGraph: (gf: GraphFilter, citations?: Citation[]) => void;
  onOpenGraphNode: (citation: Citation) => void;
}

function MessageBubble({
  msg,
  onExcelExport,
  onOpenTable,
  onOpenGraph,
  onOpenGraphNode,
}: MessageBubbleProps) {
  const isUser = msg.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div
          className="max-w-[78%] rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm text-white leading-relaxed"
          style={{ background: "#6366F1" }}
        >
          {msg.content}
        </div>
      </div>
    );
  }

  // AI bubble
  const displayText = msg.tableData
    ? stripTableFromContent(msg.content)
    : msg.content;

  return (
    <div className="flex items-start gap-2">
      {/* Avatar */}
      <div
        className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5"
        style={{
          background: "linear-gradient(135deg, #6366F1 0%, #7c3aed 100%)",
        }}
      >
        <Sparkles size={13} className="text-white" />
      </div>

      <div className="flex-1 min-w-0">
        {/* Bubble */}
        <div className="inline-block max-w-full rounded-2xl rounded-tl-sm px-3.5 py-2.5 bg-[var(--surface-container-high)] text-sm text-[var(--text)] leading-relaxed">
          {msg.loading ? (
            <LoadingDots />
          ) : (
            <>
              {/* Display text (table stripped out) */}
              {displayText && (
                <p className="whitespace-pre-wrap">{displayText}</p>
              )}

              {/* Table summary badge */}
              {msg.tableData && (
                <div className="mt-2 flex items-center gap-1.5 text-xs text-[var(--text2)]">
                  <Table2 size={13} className="flex-shrink-0" />
                  <span>
                    [Bảng {msg.tableData.rows.length} dòng,{" "}
                    {msg.tableData.headers.length} cột]
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Citation chips → click to open node in graph */}
        {!msg.loading && msg.citations && msg.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {msg.citations
              .filter((c) => (c.type === "project" || c.type === "company" || c.type === "contact") && !!c.slug)
              .slice(0, 6)
              .map((c, i) => (
                <button
                  key={`${c.slug}-${i}`}
                  onClick={() => onOpenGraphNode(c)}
                  title={`Xem ${c.name} trong graph`}
                  className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md border transition-colors"
                  style={{
                    background: "var(--surface-container)",
                    borderColor: "var(--border)",
                    color: "var(--text)",
                  }}
                >
                  <Network size={10} className="opacity-70" />
                  <span className="truncate max-w-[160px]">{c.name}</span>
                </button>
              ))}
          </div>
        )}

        {/* Action buttons (only when not loading) */}
        {!msg.loading && (msg.tableData || hasGraphFilter(msg.graphFilter)) && (
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {/* Table actions */}
            {msg.tableData && (
              <>
                <button
                  onClick={() =>
                    onExcelExport(
                      msg.tableData!,
                      `LeadsMap_${msg.tableData!.headers[0] ?? "Table"}`
                    )
                  }
                  className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-[var(--border)] text-[var(--text2)] hover:text-[var(--text)] hover:border-[#6366F1] transition-colors"
                >
                  <FileSpreadsheet size={12} />
                  Excel
                </button>
                <button
                  onClick={() => onOpenTable(msg.tableData!)}
                  className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-[var(--border)] text-[var(--text2)] hover:text-[var(--text)] hover:border-[#6366F1] transition-colors"
                >
                  <Table2 size={12} />
                  Mở Table Builder
                </button>
              </>
            )}

            {/* Graph filter action */}
            {hasGraphFilter(msg.graphFilter) && (
              <button
                onClick={() => onOpenGraph(msg.graphFilter!, msg.citations)}
                className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-[#6366F1]/50 text-[#6366F1] hover:bg-[#6366F1]/10 transition-colors"
              >
                <Network size={12} />
                Xem Graph →
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function FloatingChat() {
  const pathname = usePathname();
  const router = useRouter();

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom whenever messages change or panel opens
  useEffect(() => {
    if (open) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open]);

  // Focus input when panel opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Hide on /chat page — hooks must all be called before this return
  if (pathname === "/chat") return null;

  // -------------------------------------------------------------------------
  // Send message
  // -------------------------------------------------------------------------

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setInput("");
    setSending(true);

    // Append user message
    const userMsg: Message = { role: "user", content: trimmed };
    // Append placeholder AI loading message
    const loadingMsg: Message = { role: "ai", content: "", loading: true };

    setMessages((prev) => [...prev, userMsg, loadingMsg]);

    // Build history (exclude the loading placeholder)
    const history = [...messages, userMsg].map((m) => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.content,
    }));

    let contextStr = `\n\n[System Info: User đang xem trang ${pathname}.`;
    if (pathname === "/tables") {
      contextStr += " (Hỗ trợ tạo bảng/chọn cột)]";
    } else if (pathname === "/graph") {
      contextStr += " (Hỗ trợ truy vấn liên kết, filter đồ thị)]";
    } else if (pathname === "/dashboard") {
      contextStr += " (Hỗ trợ phân tích tổng quan, tạo bảng dự án)]";
    } else {
      contextStr += "]";
    }

    try {
      const response = await api.chat(trimmed + contextStr, history);
      const tableData = parseMarkdownTable(response.answer);

      // If the backend confirmed that data has changed, invalidate caches
      // so other views (graph, tables, stats) show fresh numbers next time.
      const answerLower = (response.answer || "").toLowerCase();
      const mentionsChange = /(đã\s*(xong|cập nhật|thêm|xóa|xoá|sửa|đổi|thực hiện)|hoàn tất|hoan tat|success|thành công)/i.test(
        answerLower
      );
      if (mentionsChange) {
        invalidateGraphCache();
        window.dispatchEvent(new CustomEvent("leadsmap_data_changed"));
      }

      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1
            ? {
                role: "ai",
                content: response.answer,
                loading: false,
                graphFilter: response.graph_filter ?? null,
                tableData: tableData,
                citations: response.citations,
              }
            : m
        )
      );
    } catch {
      setMessages((prev) =>
        prev.map((m, i) =>
          i === prev.length - 1
            ? {
                role: "ai",
                content: "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                loading: false,
              }
            : m
        )
      );
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  // -------------------------------------------------------------------------
  // Action handlers
  // -------------------------------------------------------------------------

  function handleExcelExport(tableData: TableData, title: string) {
    api.exportTable(tableData.headers, tableData.rows, title);
  }

  function handleOpenTable(tableData: TableData) {
    localStorage.setItem("leadsmap_pending_table", JSON.stringify(tableData));
    setOpen(false);
    router.push("/tables");
  }

  function handleOpenGraph(gf: GraphFilter, citations?: Citation[]) {
    localStorage.setItem("leadsmap_graph_filter", JSON.stringify(gf));
    window.dispatchEvent(
      new CustomEvent("leadsmap_filter_update", { detail: gf })
    );
    setOpen(false);

    // If the message cited concrete entities, carry them as a ?nodes=... deep
    // link so the graph can highlight + fit-to-zoom on that exact group
    // (single slug -> open card; multiple slugs -> fit bounding box).
    const slugs = (citations ?? [])
      .filter((c) => (c.type === "project" || c.type === "company" || c.type === "contact") && !!c.slug)
      .map((c) => c.slug);
    const unique = Array.from(new Set(slugs));

    if (unique.length === 1) {
      router.push(`/graph?node=${encodeURIComponent(unique[0])}&from=chat`);
    } else if (unique.length > 1) {
      router.push(
        `/graph?nodes=${unique.map(encodeURIComponent).join(",")}&from=chat`
      );
    } else {
      router.push("/graph?from=chat");
    }
  }

  function handleOpenGraphNode(c: Citation) {
    setOpen(false);
    if (!c.slug) {
      router.push("/graph?from=chat");
      return;
    }
    const slug = encodeURIComponent(c.slug);
    // Focus camera on the specific node via deep link query param.
    router.push(`/graph?node=${slug}&from=chat`);
  }

  const hasMessages = messages.length > 0;

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <>
      {/* Bounce keyframe injected via style tag */}
      <style>{`
        @keyframes floatingChatBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.5; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>

      {/* ------------------------------------------------------------------ */}
      {/* Floating Container (Draggable)                                      */}
      {/* ------------------------------------------------------------------ */}
      <motion.div
        drag
        dragMomentum={false}
        className="fixed z-[200]"
        style={{ bottom: 20, right: 20, width: 56, height: 56 }}
      >
        {/* Chat Panel */}
        {open && (
          <div
            onPointerDown={(e) => e.stopPropagation()} // Prevent dragging when interacting with chat
            className="absolute bottom-[70px] right-0 flex flex-col rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl overflow-hidden"
            style={{ width: 400, height: 560, cursor: "auto" }}
          >
            {/* Header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border)] flex-shrink-0">
              <div
                className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{
                  background:
                    "linear-gradient(135deg, #6366F1 0%, #7c3aed 100%)",
                }}
              >
                <Sparkles size={15} className="text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-[var(--text)] leading-none">
                  Chat AI
                </p>
                <p className="text-xs text-[var(--text2)] mt-0.5 leading-none">
                  LeadsMap Intelligence
                </p>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="btn btn-ghost p-1.5 rounded-lg text-[var(--text2)] hover:text-[var(--text)]"
              >
                <X size={16} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
              {!hasMessages ? (
                /* Empty state */
                <div className="h-full flex flex-col items-center justify-center gap-4">
                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center"
                    style={{
                      background:
                        "linear-gradient(135deg, #6366F1 0%, #7c3aed 100%)",
                    }}
                  >
                    <MessageSquare size={26} className="text-white" />
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium text-[var(--text)]">
                      Hỏi về dự án BĐS
                    </p>
                    <p className="text-xs text-[var(--text2)] mt-1">
                      Tôi có thể tìm liên hệ, dự án, xuất bảng Excel...
                    </p>
                  </div>
                  <div className="flex flex-col gap-2 w-full">
                    {QUICK_STARTERS.map((starter) => (
                      <button
                        key={starter}
                        onClick={() => sendMessage(starter)}
                        className="text-left text-xs px-3.5 py-2.5 rounded-xl border border-[var(--border)] text-[var(--text2)] hover:border-[#6366F1] hover:text-[var(--text)] transition-colors bg-[var(--bg)]"
                      >
                        {starter}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <MessageBubble
                    key={idx}
                    msg={msg}
                    onExcelExport={handleExcelExport}
                    onOpenTable={handleOpenTable}
                    onOpenGraph={handleOpenGraph}
                    onOpenGraphNode={handleOpenGraphNode}
                  />
                ))
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div className="flex-shrink-0 px-3 py-3 border-t border-[var(--border)]">
              <div className="flex items-end gap-2 rounded-xl border border-[var(--border)] bg-[var(--bg)] px-3 py-2 focus-within:border-[#6366F1] transition-colors">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Nhập câu hỏi... (Enter để gửi)"
                  rows={1}
                  disabled={sending}
                  className="flex-1 resize-none bg-transparent text-sm text-[var(--text)] placeholder:text-[var(--text2)] outline-none leading-relaxed max-h-28 overflow-y-auto disabled:opacity-50"
                  style={{ minHeight: "1.5rem" }}
                />
                <button
                  onClick={() => sendMessage(input)}
                  disabled={!input.trim() || sending}
                  className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  style={{ background: "#6366F1" }}
                >
                  <Send size={14} className="text-white" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Bubble Button */}
        <button
          onClick={() => setOpen((v) => !v)}
          className="w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 active:scale-95 cursor-move"
          style={{
            background: "linear-gradient(135deg, #6366F1 0%, #7c3aed 100%)",
          }}
          aria-label="Mở chat AI"
        >
          <MessageSquare size={22} className="text-white pointer-events-none" />

          {/* Unread badge */}
          {hasMessages && (
            <span className="absolute top-1 right-1 w-3 h-3 rounded-full bg-amber-400 border-2 border-[var(--bg)] pointer-events-none" />
          )}
        </button>
      </motion.div>
    </>
  );
}
