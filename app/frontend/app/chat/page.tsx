"use client";
import { useState, useRef, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  api,
  AgentReport,
  invalidateGraphCache,
  ChatResponse,
  ChatSessionMessage,
  ChatSessionSummary,
  Citation,
  GraphFilter,
  PendingMutation,
} from "@/lib/api";
import ReportHtmlViewer from "@/components/ReportHtmlViewer";
import { FileSpreadsheet } from "lucide-react";
import {
  MessageSquare, Send, Sparkles, Database, Network, Download,
  X, History, ChevronLeft, BarChart2, Copy, Check,
  Plus, Pencil, Trash2, AlertCircle, Loader2, CheckCircle2, FileText,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

interface Message {
  role: "user" | "ai";
  content: string;
  citations?: Citation[];
  contextUsed?: number;
  graphFilter?: GraphFilter | null;
  loading?: boolean;
  pendingMutation?: PendingMutation | null;
  report?: AgentReport | null;
}

function looksLikeMutationQuery(query: string): boolean {
  const q = query.trim().toLowerCase();
  const hasVerb = /(thêm|tạo|cập nhật|sửa|chỉnh sửa|xóa|xoá|đổi|insert|update|delete|remove)/i.test(q);
  const hasTarget = /(dự án|du an|project|liên hệ|lien he|contact|hệ thống|he thong|database|db|chủ đầu tư|cdt|developer)/i.test(q);
  const hasFromTo = /(từ|tu).*(sang|thành|thanh)/i.test(q);
  return (hasVerb && hasTarget) || hasFromTo;
}

function claimsMutationCompleted(answer: string): boolean {
  const a = (answer || "").toLowerCase();
  return /(đã\s*(xong|cập nhật|thêm|xóa|xoá|sửa|đổi|thực hiện)|hoàn tất|hoan tat|success|thành công)/i.test(a);
}

const STARTERS = [
  "Xin chào! Bạn có thể làm được những gì?",
  "Liệt kê các dự án ở Đà Nẵng vào bảng",
  "Thêm dự án mới: Vinhomes Ocean Park 3 tại Hưng Yên, CĐT Vinhomes, 8.500 tỷ VND",
  "Cập nhật dự án Gamuda Gardens: đổi trạng thái thành Hoàn thành",
  "Danh sách liên hệ đầu mối của Vingroup",
  "Xóa dự án ABC khỏi hệ thống",
];

// ── Colour palette for bar charts ─────────────────────────────────────────────
const CHART_COLORS = [
  "#6366F1", "#F59E0B", "#10B981", "#EC4899", "#8B5CF6",
  "#3B82F6", "#EF4444", "#14B8A6", "#F97316", "#84CC16",
];

// ── Markdown helpers ───────────────────────────────────────────────────────────
function parseMarkdownTable(text: string): { headers: string[]; rows: string[][] } | null {
  const lines = text.trim().split("\n").filter(l => l.trim().startsWith("|"));
  if (lines.length < 3) return null;
  const parseRow = (line: string) => line.split("|").slice(1, -1).map(c => c.trim());
  const headers = parseRow(lines[0]);
  const rows = lines.slice(2).map(parseRow).filter(r => r.some(c => c));
  if (headers.length === 0) return null;
  return { headers, rows };
}

function isNumericColumn(col: string[]): boolean {
  const nums = col.filter(v => v && !isNaN(parseFloat(v.replace(/[,.]/g, ""))));
  return nums.length > 0 && nums.length >= col.length * 0.6;
}

function stripInlineMarkdown(raw: string): string {
  return stripLatex(raw || "")
    .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeLookupText(raw: string): string {
  return stripInlineMarkdown(raw)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

function detectPrimaryEntityColumn(headers: string[]): number {
  const normalized = headers.map((h) => normalizeLookupText(h));
  const patterns = [
    /(ten du an|du an|project)/,
    /(ten lien he|lien he|contact|person)/,
    /(ten cong ty|cong ty|company|developer|chu dau tu|cdt)/,
    /(^ten$|^name$)/,
  ];

  for (const pattern of patterns) {
    const idx = normalized.findIndex((h) => pattern.test(h));
    if (idx >= 0) return idx;
  }
  return 0;
}

function inferPreferredNodeType(header: string): "project" | "company" | "person" | null {
  const h = normalizeLookupText(header);
  if (/(du an|project)/.test(h)) return "project";
  if (/(lien he|contact|person)/.test(h)) return "person";
  if (/(cong ty|company|developer|chu dau tu|cdt)/.test(h)) return "company";
  return null;
}

function candidateNames(raw: string): string[] {
  const base = stripInlineMarkdown(raw);
  if (!base) return [];
  const extra = base.split(/[,;|]/g).map((s) => s.trim()).filter(Boolean);
  return Array.from(new Set([base, ...extra]));
}

function downloadCSV(data: { headers: string[]; rows: string[][] }) {
  const csv = [
    data.headers.join(","),
    ...data.rows.map(row => row.map(c => `"${c.replace(/"/g, '""')}"`).join(",")),
  ].join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "coreone_data.csv"; a.click();
  URL.revokeObjectURL(url);
}

// ── Mermaid diagram renderer ──────────────────────────────────────────────────
function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    const isDark = document.documentElement.classList.contains("dark");
    async function render() {
      try {
        if (typeof window !== "undefined" && !(window as any).mermaid) {
          await new Promise<void>((resolve) => {
            const s = document.createElement("script");
            s.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
            s.onload = () => resolve();
            document.head.appendChild(s);
          });
        }
        if (cancelled || !ref.current) return;
        const mermaid = (window as any).mermaid;
        mermaid.initialize({
          startOnLoad: false,
          theme: isDark ? "dark" : "default",
          securityLevel: "loose",
        });
        const id = `mmd-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, code);
        if (!cancelled && ref.current) ref.current.innerHTML = svg;
      } catch {
        if (!cancelled && ref.current)
          ref.current.innerHTML = `<pre class="md-para text-xs">${code}</pre>`;
      }
    }
    render();
    return () => { cancelled = true; };
  }, [code]);

  return <div ref={ref} className="md-mermaid" />;
}

// ── Copyable code block ───────────────────────────────────────────────────────
function CodeBlock({ code, lang }: { code: string; lang?: string }) {
  const [copied, setCopied] = useState(false);
  function copy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }
  if (lang === "mermaid") return <MermaidBlock code={code} />;
  return (
    <div className="md-code-block">
      {lang && (
        <div className="md-code-header">
          <span className="text-[10px] md-muted uppercase tracking-widest">{lang}</span>
          <button
            onClick={copy}
            className="flex items-center gap-1 text-[10px] md-muted hover:text-[var(--text)] transition-colors"
          >
            {copied
              ? <Check size={11} style={{ color: "var(--secondary)" }} />
              : <Copy size={11} />}
            {copied ? "Đã copy" : "Copy"}
          </button>
        </div>
      )}
      <pre><code>{code}</code></pre>
    </div>
  );
}

// ── Interactive table with optional chart ─────────────────────────────────────
function MarkdownTable({
  parsed,
  citations,
}: {
  parsed: { headers: string[]; rows: string[][] };
  citations?: Citation[];
}) {
  const [showChart, setShowChart] = useState(false);
  const [graphNodeIds, setGraphNodeIds] = useState<Set<string>>(new Set());
  const [graphNameIndex, setGraphNameIndex] = useState<Map<string, Array<{ id: string; type: string }>>>(new Map());
  const [graphReady, setGraphReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api.graph()
      .then((g) => {
        if (cancelled) return;

        const ids = new Set<string>();
        const byName = new Map<string, Array<{ id: string; type: string }>>();

        for (const n of g.nodes || []) {
          const id = String(n.id || "").trim();
          if (!id) continue;
          ids.add(id);

          const key = normalizeLookupText(n.name || "");
          if (!key) continue;

          const list = byName.get(key) ?? [];
          list.push({ id, type: String(n.type || "") });
          byName.set(key, list);
        }

        setGraphNodeIds(ids);
        setGraphNameIndex(byName);
        setGraphReady(true);
      })
      .catch(() => {
        if (cancelled) return;
        setGraphReady(true);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const primaryColIdx = useMemo(() => detectPrimaryEntityColumn(parsed.headers), [parsed.headers]);
  const preferredType = useMemo(() => {
    if (primaryColIdx < 0 || primaryColIdx >= parsed.headers.length) return null;
    return inferPreferredNodeType(parsed.headers[primaryColIdx] || "");
  }, [parsed.headers, primaryColIdx]);

  const citationSlugByName = useMemo(() => {
    const map = new Map<string, string>();
    for (const c of citations ?? []) {
      const slug = String(c?.slug || "").trim();
      if (!slug) continue;
      const key = normalizeLookupText(c.name || "");
      if (!key) continue;
      map.set(key, slug);
    }
    return map;
  }, [citations]);

  const rowNodeSlug = useMemo(() => {
    if (!graphReady) return parsed.rows.map(() => "");

    return parsed.rows.map((row) => {
      const baseCell = (row[primaryColIdx] || row[0] || "").trim();
      const names = candidateNames(baseCell);

      for (const name of names) {
        const key = normalizeLookupText(name);
        if (!key) continue;

        const citationSlug = citationSlugByName.get(key);
        if (citationSlug && graphNodeIds.has(citationSlug)) {
          return citationSlug;
        }

        const refs = graphNameIndex.get(key) ?? [];
        if (refs.length === 1) return refs[0].id;

        if (preferredType) {
          const typed = refs.filter((r) => r.type === preferredType);
          if (typed.length === 1) return typed[0].id;
        }
      }

      return "";
    });
  }, [parsed.rows, primaryColIdx, citationSlugByName, graphNodeIds, graphNameIndex, graphReady, preferredType]);

  const chartData = useMemo(() => {
    if (parsed.rows.length < 2 || parsed.headers.length < 2) return null;
    const numColIdx = parsed.headers.findIndex((_, i) =>
      i > 0 && isNumericColumn(parsed.rows.map(r => r[i] || ""))
    );
    if (numColIdx === -1) return null;
    return parsed.rows
      .map(row => ({
        name: (row[0] || "").slice(0, 20),
        value: parseFloat((row[numColIdx] || "0").replace(/[,.]/g, m => m === "," ? "" : ".")),
        rawLabel: parsed.headers[numColIdx],
      }))
      .filter(d => !isNaN(d.value));
  }, [parsed]);

  return (
    <div className="mt-2 mb-1">
      <div className="overflow-x-auto rounded-xl border" style={{ borderColor: "var(--border)" }}>
        <table className="data-table">
          <thead>
            <tr>{parsed.headers.map((h, j) => <th key={j}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {parsed.rows.map((row, j) => (
              <tr key={j}>
                {row.map((cell, k) => {
                  const slug = rowNodeSlug[j] || "";
                  const canOpenGraph = k === primaryColIdx && !!slug;

                  return (
                    <td key={k}>
                      {canOpenGraph ? (
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <InlineMarkdown text={cell} />
                          <Link
                            href={`/graph?node=${encodeURIComponent(slug)}&from=chat`}
                            title={`Mở ${stripInlineMarkdown(cell)} trong graph`}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-medium border transition-colors hover:underline"
                            style={{
                              color: "var(--primary)",
                              borderColor: "var(--primary)55",
                              background: "var(--primary)18",
                            }}
                          >
                            <Network size={10} className="opacity-80" /> Graph
                          </Link>
                        </div>
                      ) : (
                        <InlineMarkdown text={cell} />
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
        <button className="btn btn-ghost text-xs py-1 px-2" onClick={() => downloadCSV(parsed)}>
          <Download size={11} /> CSV
        </button>
        <button className="btn btn-primary text-xs py-1 px-2"
          onClick={() => api.exportTable(parsed.headers, parsed.rows)}>
          <FileSpreadsheet size={11} /> Excel
        </button>
        {chartData && chartData.length >= 2 && (
          <button
            className={`text-xs py-1 px-2 btn ${showChart ? "btn-primary" : "btn-ghost"}`}
            onClick={() => setShowChart(v => !v)}
          >
            <BarChart2 size={11} /> {showChart ? "Ẩn Chart" : "Xem Chart"}
          </button>
        )}
      </div>

      {showChart && chartData && (
        <div className="mt-2 rounded-xl p-4 md-card">
          <p className="text-[10px] md-muted uppercase tracking-widest mb-3">
            {chartData[0]?.rawLabel || "Biểu đồ"}
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 4, right: 8, left: 4, bottom: 40 }}>
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 10 }} width={48} />
              <Tooltip
                contentStyle={{
                  background: "var(--surface-container-high)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  fontSize: 11,
                  color: "var(--text)",
                }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((_, index) => (
                  <Cell key={index} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ── Full Markdown renderer ─────────────────────────────────────────────────────
type Token =
  | { type: "heading"; level: 1 | 2 | 3; text: string }
  | { type: "table"; content: string }
  | { type: "code"; lang: string; code: string }
  | { type: "paragraph"; text: string }
  | { type: "blank" };

function tokenizeMarkdown(raw: string): Token[] {
  const lines = raw.split("\n");
  const tokens: Token[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    const fenceMatch = line.match(/^```(\w*)$/);
    if (fenceMatch) {
      const lang = fenceMatch[1] || "";
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      tokens.push({ type: "code", lang, code: codeLines.join("\n") });
      i++;
      continue;
    }

    // Heading
    const hMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (hMatch) {
      tokens.push({ type: "heading", level: hMatch[1].length as 1 | 2 | 3, text: hMatch[2] });
      i++;
      continue;
    }

    // Table block (collect consecutive | lines)
    if (line.trim().startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      tokens.push({ type: "table", content: tableLines.join("\n") });
      continue;
    }

    // Blank line
    if (!line.trim()) {
      tokens.push({ type: "blank" });
      i++;
      continue;
    }

    // Paragraph (accumulate consecutive non-special lines)
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith("|") &&
      !lines[i].match(/^#{1,3}\s/) &&
      !lines[i].startsWith("```")
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      tokens.push({ type: "paragraph", text: paraLines.join("\n") });
    }
  }
  return tokens;
}

/** Convert LaTeX math tokens to plain Unicode — safety net for model output */
function stripLatex(raw: string): string {
  return raw
    // Named commands inside $...$
    .replace(/\$\\rightarrow\$/g, "→")
    .replace(/\$\\leftarrow\$/g, "←")
    .replace(/\$\\Rightarrow\$/g, "⇒")
    .replace(/\$\\Leftarrow\$/g, "⇐")
    .replace(/\$\\leftrightarrow\$/g, "↔")
    .replace(/\$\\times\$/g, "×")
    .replace(/\$\\cdot\$/g, "·")
    .replace(/\$\\div\$/g, "÷")
    .replace(/\$\\pm\$/g, "±")
    .replace(/\$\\leq\$/g, "≤")
    .replace(/\$\\geq\$/g, "≥")
    .replace(/\$\\neq\$/g, "≠")
    .replace(/\$\\approx\$/g, "≈")
    .replace(/\$\\infty\$/g, "∞")
    .replace(/\$\\sum\$/g, "∑")
    .replace(/\$\\%\$/g, "%")
    // Bare commands (no $ delimiters)
    .replace(/\\rightarrow/g, "→")
    .replace(/\\leftarrow/g, "←")
    .replace(/\\Rightarrow/g, "⇒")
    .replace(/\\times/g, "×")
    .replace(/\\leq/g, "≤")
    .replace(/\\geq/g, "≥")
    .replace(/\\neq/g, "≠")
    .replace(/\\approx/g, "≈")
    .replace(/\\pm/g, "±")
    .replace(/\\infty/g, "∞")
    // \text{...} → just the text inside
    .replace(/\$?\\text\{([^}]*)\}\$?/g, "$1")
    // Generic $...$ single-token — strip delimiters only
    .replace(/\$([^$\n]{1,40})\$/g, "$1")
    // Remaining stray backslash before word
    .replace(/\\([a-zA-Z]+)/g, "$1");
}

/** Render inline markdown: bold, italic, code */
function InlineMarkdown({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  const safeText = stripLatex(text);
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let m: RegExpExecArray | null;

  while ((m = regex.exec(safeText)) !== null) {
    if (m.index > last) parts.push(safeText.slice(last, m.index));
    if (m[2])
      parts.push(
        <strong key={m.index} className="font-semibold" style={{ color: "var(--text)" }}>
          {m[2]}
        </strong>
      );
    else if (m[3])
      parts.push(
        <em key={m.index} className="italic md-muted">{m[3]}</em>
      );
    else if (m[4])
      parts.push(
        <code key={m.index} className="md-code-inline">{m[4]}</code>
      );
    last = m.index + m[0].length;
  }
  if (last < safeText.length) parts.push(safeText.slice(last));
  return <>{parts}</>;
}

/** Render a paragraph that may contain list items */
function ParagraphBlock({ text }: { text: string }) {
  const lines = text.split("\n");
  const isBullet   = (l: string) => /^[-•*]\s+/.test(l.trim());
  const isNumbered = (l: string) => /^\d+[.)]\s+/.test(l.trim());
  const isListBlock = lines.every(l => !l.trim() || isBullet(l) || isNumbered(l));

  if (isListBlock) {
    const numbered = lines.some(l => isNumbered(l.trim()));
    const items = lines.filter(l => l.trim());
    const Tag = numbered ? "ol" : "ul";
    return (
      <Tag className={`my-1 pl-4 space-y-0.5 ${numbered ? "list-decimal" : "list-disc"} list-inside`}>
        {items.map((item, i) => {
          const clean = item.trim().replace(/^[-•*\d.)]+\s*/, "");
          return (
            <li key={i} className="md-list-item">
              <InlineMarkdown text={clean} />
            </li>
          );
        })}
      </Tag>
    );
  }

  return (
    <p className="md-para my-0.5">
      <InlineMarkdown text={text} />
    </p>
  );
}

function AnswerContent({ text, citations }: { text: string; citations?: Citation[] }) {
  const tokens = useMemo(() => tokenizeMarkdown(text), [text]);

  return (
    <div className="space-y-1">
      {tokens.map((token, i) => {
        switch (token.type) {
          case "heading": {
            const cls = {
              1: "md-h1 mt-2 mb-0.5",
              2: "md-h2 mt-1.5 mb-0.5",
              3: "md-h3 mt-1 mb-0.5",
            };
            return <p key={i} className={cls[token.level]}>{token.text}</p>;
          }
          case "code":
            return <CodeBlock key={i} lang={token.lang} code={token.code} />;
          case "table": {
            const parsed = parseMarkdownTable(token.content);
            if (!parsed) return <pre key={i} className="md-para text-xs whitespace-pre-wrap">{token.content}</pre>;
            return <MarkdownTable key={i} parsed={parsed} citations={citations} />;
          }
          case "paragraph":
            return <ParagraphBlock key={i} text={token.text} />;
          case "blank":
            return <div key={i} className="h-1" />;
          default:
            return null;
        }
      })}
    </div>
  );
}

// ── Mutation confirmation card ────────────────────────────────────────────────
const OP_META = {
  insert: { label: "Thêm mới",  Icon: Plus,   accentVar: "--secondary",  warnDelete: false },
  update: { label: "Cập nhật",  Icon: Pencil,  accentVar: "--primary",    warnDelete: false },
  delete: { label: "Xóa",       Icon: Trash2,  accentVar: "--error",      warnDelete: true  },
} as const;

const ENTITY_LABEL: Record<string, string> = { project: "Dự án", contact: "Liên hệ" };

const FIELD_LABEL: Record<string, string> = {
  name: "Tên", province: "Tỉnh/TP", district: "Quận/Huyện", address: "Địa chỉ",
  developer: "Chủ đầu tư", value_billion_vnd: "Giá trị (tỷ VND)", status: "Trạng thái",
  phase: "Giai đoạn", type_tags: "Loại", site_area: "Diện tích đất", floors: "Số tầng",
  groundbreaking: "Khởi công", handover: "Bàn giao", notes: "Ghi chú",
  company: "Công ty", role: "Chức vụ", phone: "Điện thoại", email: "Email",
};

function fmt(v: any): string {
  if (Array.isArray(v)) return v.join(", ");
  if (v === null || v === undefined || v === "") return "—";
  return String(v);
}

function MutationCard({ mutation }: { mutation: PendingMutation }) {
  const [status, setStatus] = useState<"pending" | "loading" | "success" | "cancelled" | "error">("pending");
  const [resultMsg, setResultMsg] = useState("");

  const op = (mutation.operation ?? "insert") as keyof typeof OP_META;
  const meta = OP_META[op] ?? OP_META.insert;
  const accentColor = `var(${meta.accentVar})`;
  const entityLabel = ENTITY_LABEL[mutation.entity] ?? mutation.entity;

  const dataEntries = Object.entries(mutation.data ?? {}).filter(
    ([, v]) => v !== null && v !== undefined && v !== ""
  );
  const changesEntries = Object.entries(mutation.changes ?? {});

  async function handleConfirm() {
    setStatus("loading");
    try {
      const res = await api.mutateExecute({
        operation: mutation.operation,
        entity: mutation.entity,
        slug: mutation.slug ?? undefined,
        display_name: mutation.display_name,
        data: mutation.data ?? undefined,
        confirmed: true,
      });
      setStatus(res.success ? "success" : "error");
      setResultMsg(res.message);
      if (res.success) {
        // Force other views (graph, tables, stats) to refetch fresh data.
        invalidateGraphCache();
        try {
          window.dispatchEvent(new CustomEvent("leadsmap_data_changed"));
        } catch {}
      }
    } catch {
      setStatus("error");
      setResultMsg("Lỗi kết nối tới backend.");
    }
  }

  // ── Result states ────────────────────────────────────────────────────────
  if (status === "success") {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2.5 rounded-xl border text-xs"
           style={{ borderColor: "var(--secondary)", background: "rgba(16,185,129,0.08)", color: "var(--secondary)" }}>
        <CheckCircle2 size={14} />
        <span className="font-medium">Thành công!</span>
        <span className="text-text ml-1">{resultMsg}</span>
      </div>
    );
  }
  if (status === "cancelled") {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2 rounded-xl border text-[11px]"
           style={{ borderColor: "var(--outline-variant)", color: "var(--text2)", background: "var(--surface-container)" }}>
        <X size={11} /> Đã hủy thao tác.
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="mt-2 flex items-center gap-2 px-3 py-2.5 rounded-xl border text-xs"
           style={{ borderColor: "var(--error)", background: "rgba(239,68,68,0.08)", color: "var(--error)" }}>
        <AlertCircle size={13} />
        <span>{resultMsg || "Đã xảy ra lỗi."}</span>
      </div>
    );
  }

  // ── Pending / Loading ────────────────────────────────────────────────────
  return (
    <div className="mt-2 rounded-xl border overflow-hidden"
         style={{ borderColor: accentColor + "50", background: accentColor + "0d" }}>

      {/* Header row */}
      <div className="flex items-center gap-2 px-3 py-2 border-b text-xs"
           style={{ borderColor: accentColor + "30" }}>
        <meta.Icon size={13} style={{ color: accentColor }} />
        <span className="font-semibold" style={{ color: accentColor }}>{meta.label}</span>
        <span className="text-text2">· {entityLabel}</span>
        {mutation.display_name && (
          <span className="ml-auto font-medium text-text truncate max-w-[200px]" title={mutation.display_name}>
            {mutation.display_name}
          </span>
        )}
      </div>

      {/* Body — data preview */}
      <div className="px-3 py-2 max-h-48 overflow-y-auto">
        {op === "delete" && (
          <p className="text-xs text-text2 flex items-start gap-1.5">
            <AlertCircle size={12} style={{ color: "var(--error)", marginTop: 2, flexShrink: 0 }} />
            Thao tác xóa <strong>không thể hoàn tác</strong> sau khi xác nhận.
          </p>
        )}

        {op === "delete" && dataEntries.length > 0 && (
          <table className="w-full text-[11px] mt-2">
            <tbody>
              {dataEntries.map(([k, v]) => (
                <tr key={k} className="border-b last:border-0"
                    style={{ borderColor: "var(--border)" }}>
                  <td className="py-0.5 pr-3 font-medium w-2/5" style={{ color: "var(--text2)" }}>
                    {FIELD_LABEL[k] ?? k}
                  </td>
                  <td className="py-0.5 text-text">{fmt(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {op === "insert" && dataEntries.length > 0 && (
          <table className="w-full text-[11px]">
            <tbody>
              {dataEntries.map(([k, v]) => (
                <tr key={k} className="border-b last:border-0"
                    style={{ borderColor: "var(--border)" }}>
                  <td className="py-0.5 pr-3 font-medium w-2/5" style={{ color: "var(--text2)" }}>
                    {FIELD_LABEL[k] ?? k}
                  </td>
                  <td className="py-0.5 text-text">{fmt(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {op === "update" && (changesEntries.length > 0 || dataEntries.length > 0) && (
          <table className="w-full text-[11px]">
            <tbody>
              {changesEntries.length > 0
                ? changesEntries.map(([field, change]) => (
                    <tr key={field} className="border-b last:border-0"
                        style={{ borderColor: "var(--border)" }}>
                      <td className="py-0.5 pr-3 font-medium w-2/5" style={{ color: "var(--text2)" }}>
                        {FIELD_LABEL[field] ?? field}
                      </td>
                      <td className="py-0.5">
                        <span className="line-through" style={{ color: "var(--text2)" }}>
                          {fmt((change as any).old)}
                        </span>
                        <span className="mx-1.5 text-text2">→</span>
                        <span className="font-medium" style={{ color: accentColor }}>
                          {fmt((change as any).new)}
                        </span>
                      </td>
                    </tr>
                  ))
                : dataEntries.map(([k, v]) => (
                    <tr key={k} className="border-b last:border-0"
                        style={{ borderColor: "var(--border)" }}>
                      <td className="py-0.5 pr-3 font-medium w-2/5" style={{ color: "var(--text2)" }}>
                        {FIELD_LABEL[k] ?? k}
                      </td>
                      <td className="py-0.5 font-medium" style={{ color: accentColor }}>
                        {fmt(v)}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 px-3 py-2 border-t"
           style={{ borderColor: accentColor + "30", background: accentColor + "08" }}>
        {status === "loading" ? (
          <span className="flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text2)" }}>
            <Loader2 size={12} className="animate-spin" /> Đang xử lý...
          </span>
        ) : (
          <>
            <button
              onClick={handleConfirm}
              className="btn btn-primary text-xs py-1 px-3 flex items-center gap-1.5"
              style={op === "delete" ? { background: "var(--error)", borderColor: "var(--error)" } : {}}
            >
              {op === "delete" ? <Trash2 size={11} /> : <Check size={11} />}
              Xác nhận
            </button>
            <button
              onClick={() => setStatus("cancelled")}
              className="btn btn-ghost text-xs py-1 px-3"
            >
              Hủy
            </button>
          </>
        )}
      </div>
    </div>
  );
}

// ── Citation badge ────────────────────────────────────────────────────────────
function CitationBadge({ c }: { c: Citation }) {
  const icon =
    c.type === "project"  ? "" :
    c.type === "company"  ? "" :
    c.type === "contact"  ? "" :
    c.type === "web"      ? "" :
    c.type === "graphrag" ? "" : "";

  if (c.type === "web" && c.slug?.startsWith("http")) {
    return (
      <a href={c.slug} target="_blank" rel="noopener noreferrer"
        className="citation hover:underline"
        style={{ color: "var(--primary)" }}>
        {icon} {c.name}
      </a>
    );
  }

  // Project / company / contact → clickable deep-link that focuses graph on node
  if ((c.type === "project" || c.type === "company" || c.type === "contact") && c.slug) {
    const href = `/graph?node=${encodeURIComponent(c.slug)}&from=chat`;
    return (
      <Link
        href={href}
        title={`Xem ${c.name} trong graph`}
        className="citation hover:underline"
        style={{ color: "var(--primary)" }}
      >
        <Network size={10} className="inline-block mr-1 align-[-1px] opacity-70" />
        {icon} {c.name}
      </Link>
    );
  }

  return <span className="citation">{icon} {c.name}</span>;
}

// ── Graph filter notification ─────────────────────────────────────────────────
function GraphFilterNotice({
  f,
}: {
  f: GraphFilter;
}) {
  const parts = [f.province, f.developer].filter(Boolean);
  const label = parts.length > 0 ? parts.join(" · ") : "Bộ lọc đã cập nhật";
  const href = "/graph?from=chat";

  return (
    <div className="flex items-center gap-2 mt-1.5 ml-1 px-3 py-1.5 rounded-lg bg-accent/10 border border-accent/20">
      <Network size={12} className="text-accent flex-shrink-0" />
      <span className="text-[11px] text-accent flex-1">{label} — Graph đã cập nhật</span>
      <Link href={href} className="text-[11px] text-accent underline hover:text-[#818CF8] transition-colors">
        Xem Graph →
      </Link>
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────
function GeneratedReportCard({ report }: { report: AgentReport }) {
  const downloadUrl = report.id ? api.reportDownloadUrl(report.id) : report.download_url;

  return (
    <div className="mt-2 ml-1 rounded-lg border border-accent/20 bg-[var(--surface-container-low)] p-3 shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-text flex items-center gap-2">
            <FileText size={14} className="text-accent flex-shrink-0" />
            <span className="truncate">{report.title || "Báo cáo phân tích"}</span>
          </p>
          {report.summary && (
            <p className="text-[12px] text-text2 mt-1 leading-relaxed">{report.summary}</p>
          )}
        </div>
        {downloadUrl && (
          <a
            className="btn btn-primary text-xs py-1.5 px-3 flex-shrink-0"
            href={downloadUrl}
            target="_blank"
            rel="noreferrer"
          >
            <Download size={12} /> PDF
          </a>
        )}
      </div>

      <ReportHtmlViewer html={report.html} charts={report.charts || []} compact />

      <div className="mt-2 flex justify-end">
        <Link href="/reports" className="text-[11px] text-accent hover:underline">
          Mở trong Reports
        </Link>
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const hasMarkdownTable = useMemo(() => !!parseMarkdownTable(msg.content || ""), [msg.content]);

  if (msg.role === "user") {
    return (
      <div className="chat-user">
        <div className="bubble">{msg.content}</div>
      </div>
    );
  }
  return (
    <div className="chat-ai">
      <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-accent to-violet-500 mt-0.5">
        <Sparkles size={14} color="white" />
      </div>
      <div className="flex flex-col gap-1 flex-1 min-w-0">
        <div className="bubble">
          {msg.loading ? (
            <span className="flex items-center gap-1.5 text-text2">
              {[0, 0.2, 0.4].map((d, i) => (
                <span key={i} className="animate-pulse" style={{ animationDelay: `${d}s` }}>●</span>
              ))}
            </span>
          ) : (
            <AnswerContent text={msg.content} citations={msg.citations} />
          )}
        </div>

        {msg.pendingMutation && (
          <MutationCard mutation={msg.pendingMutation} />
        )}

        {msg.report && (
          <GeneratedReportCard report={msg.report} />
        )}

        {!hasMarkdownTable && msg.graphFilter && (msg.graphFilter.province || msg.graphFilter.developer || (msg.graphFilter.types?.length ?? 0) > 0) && (
          <GraphFilterNotice f={msg.graphFilter} />
        )}

        {msg.citations && msg.citations.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-0.5 ml-1">
            {msg.citations.map((c, i) => <CitationBadge key={i} c={c} />)}
          </div>
        )}

        {msg.contextUsed !== undefined && msg.contextUsed > 0 && (
          <div className="flex items-center gap-1 ml-1 mt-0.5 md-muted">
            <Database size={10} />
            <span className="text-[10px]">
              {msg.graphFilter && Object.values(msg.graphFilter).some(Boolean)
                ? `${msg.contextUsed} thực thể · GraphRAG`
                : `${msg.contextUsed} nguồn`}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

const CHAT_DRAFT_KEY = "leadsmap_chat_draft_v2";

function serializeMessages(messages: Message[]): ChatSessionMessage[] {
  return messages
    .filter((m) => !m.loading)
    .map((m) => ({
      role: m.role,
      content: m.content,
      citations: m.citations,
      context_used: m.contextUsed,
      graph_filter: m.graphFilter,
      report: m.report,
    }));
}

function deserializeMessages(messages: ChatSessionMessage[]): Message[] {
  return (messages || []).map((m) => ({
    role: m.role,
    content: m.content,
    citations: m.citations,
    contextUsed: m.context_used,
    graphFilter: m.graph_filter,
    report: m.report,
  }));
}

function deriveSessionTitle(messages: Message[]): string {
  const firstUser = messages.find((m) => m.role === "user" && m.content.trim());
  if (!firstUser) return "Cuộc trò chuyện";
  return firstUser.content.trim().slice(0, 80);
}

function formatSessionTime(ts?: string): string {
  if (!ts) return "";
  return ts.slice(0, 16).replace("T", " ");
}

// ── Main chat page ────────────────────────────────────────────────────────────
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function refreshSessions() {
    api.chatSessions(30).then((r) => setSessions(r.data)).catch(() => {});
  }

  useEffect(() => {
    refreshSessions();
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CHAT_DRAFT_KEY);
      if (!raw) return;
      const draft = JSON.parse(raw);

      if (Array.isArray(draft.messages)) {
        setMessages(deserializeMessages(draft.messages));
      }
      if (typeof draft.input === "string") {
        setInput(draft.input);
      }
      if (typeof draft.historyOpen === "boolean") {
        setHistoryOpen(draft.historyOpen);
      }
      if (typeof draft.sessionId === "string" && draft.sessionId.trim()) {
        setSessionId(draft.sessionId.trim());
      }
    } catch {
      // ignore invalid draft
    }
  }, []);

  useEffect(() => {
    const last = messages[messages.length - 1];
    const sectionComplete =
      messages.length === 0 || (last && last.role === "ai" && !last.loading);
    if (!sectionComplete || sending) {
      return;
    }

    try {
      localStorage.setItem(
        CHAT_DRAFT_KEY,
        JSON.stringify({
          sessionId: sessionId ?? "",
          input,
          historyOpen,
          messages: serializeMessages(messages),
        })
      );
    } catch {
      // ignore storage errors
    }
  }, [messages, historyOpen, sessionId, sending]);

  async function persistConversation(nextMessages: Message[]) {
    // Save only after a complete turn: user -> AI response.
    const last = nextMessages[nextMessages.length - 1];
    if (!last || last.role !== "ai" || !!last.loading) {
      return;
    }

    const serialized = serializeMessages(nextMessages);
    if (!serialized.length) return;

    try {
      const saved = await api.saveChatSession({
        session_id: sessionId || undefined,
        title: deriveSessionTitle(nextMessages),
        messages: serialized,
      });

      if (saved?.id) {
        setSessionId(saved.id);
      }
      refreshSessions();
    } catch {
      // keep local state even if persistence fails
    }
  }

  function startNewConversation() {
    setSessionId(null);
    setMessages([]);
    setInput("");
    setSending(false);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  async function loadSession(id: string) {
    try {
      const res = await api.chatSession(id);
      const session = res.data;
      setSessionId(session.id);
      setMessages(deserializeMessages(session.messages || []));
      setHistoryOpen(false);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    } catch {
      // session may have been removed
      refreshSessions();
    }
  }

  async function send(query: string) {
    const trimmed = query.trim();
    if (!trimmed || sending) return;
    setInput("");
    setSending(true);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    const userMsg: Message = { role: "user", content: trimmed };
    const loadingMsg: Message = { role: "ai", content: "", loading: true };
    const baseMessages: Message[] = [...messages, userMsg];
    setMessages([...baseMessages, loadingMsg]);

    const hist = messages
      .filter((m) => !m.loading)
      .map((m) => ({
        role: m.role === "user" ? "user" : "model",
        content: m.content,
      }));

    try {
      const savedStyle = (typeof window !== "undefined"
        ? localStorage.getItem("leadsmap_chat_style")
        : null) as "precise" | "natural" | null;
      const style: "precise" | "natural" = savedStyle === "precise" ? "precise" : "natural";
      const res: ChatResponse = await api.chat(trimmed, hist, style);

      const shouldBlockHallucinatedMutation =
        !res.pending_mutation &&
        looksLikeMutationQuery(trimmed) &&
        claimsMutationCompleted(res.answer || "");

      const safeAnswer = shouldBlockHallucinatedMutation
        ? "Mình chưa thực hiện thay đổi dữ liệu vì chưa có thẻ xác nhận. Vui lòng gửi lại yêu cầu để hệ thống tạo thẻ xác nhận trước khi ghi vào database."
        : res.answer;

      if (
        res.graph_filter &&
        (res.graph_filter.province ||
          res.graph_filter.developer ||
          (res.graph_filter.types?.length ?? 0) > 0)
      ) {
        localStorage.setItem("leadsmap_graph_filter", JSON.stringify(res.graph_filter));
      }

      const aiMessage: Message = {
        role: "ai",
        content: safeAnswer,
        citations: res.citations,
        contextUsed: res.context_used,
        graphFilter: res.graph_filter,
        pendingMutation: res.pending_mutation ?? null,
        report: res.report ?? null,
      };
      const finalMessages = [...baseMessages, aiMessage];
      setMessages(finalMessages);

      await persistConversation(finalMessages);
    } catch {
      const errorMessage: Message = {
        role: "ai",
        content: "Lỗi kết nối backend. Kiểm tra backend đang chạy tại port 8000.",
      };
      const finalMessages = [...baseMessages, errorMessage];
      setMessages(finalMessages);

      await persistConversation(finalMessages);
    } finally {
      setSending(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="flex h-screen bg-bg overflow-hidden">

      {/* ── History Sidebar ──────────────────────────────────────────────────── */}
      <div
        className="flex-shrink-0 flex flex-col border-r border-border overflow-hidden transition-all duration-250"
        style={{ width: historyOpen ? 260 : 0, background: "var(--surface)" }}
      >
        {/* Sidebar header */}
        <div
          className="flex items-center justify-between px-3 py-3 border-b border-border flex-shrink-0"
          style={{ background: "var(--surface-container-low)" }}
        >
          <span className="text-xs font-semibold flex items-center gap-1.5" style={{ color: "var(--text)" }}>
            <History size={12} style={{ color: "var(--primary)" }} /> Phiên chat
          </span>
          <button
            onClick={() => setHistoryOpen(false)}
            className="w-6 h-6 rounded-md flex items-center justify-center transition-colors"
            style={{ color: "var(--text2)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "var(--text)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "var(--text2)")}
          >
            <ChevronLeft size={14} />
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-1">
          {sessions.length === 0 ? (
            <p className="text-[11px] px-3 py-6 text-center" style={{ color: "var(--text2)" }}>
              Chưa có hội thoại nào
            </p>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                className="relative group flex items-start"
                style={{ borderBottom: "1px solid var(--surface-container)" }}
              >
                <button
                  onClick={() => loadSession(s.id)}
                  className="flex-1 text-left px-3 py-2.5 pr-8 transition-colors min-w-0"
                  style={{
                    background: sessionId === s.id ? "var(--surface-container-low)" : "transparent",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-container-low)")}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background =
                      sessionId === s.id ? "var(--surface-container-low)" : "transparent";
                  }}
                >
                  <p className="text-[11px] line-clamp-2 leading-snug transition-colors" style={{ color: "var(--text)" }}>
                    {s.title || "Cuộc trò chuyện"}
                  </p>
                  <p className="text-[10px] mt-0.5" style={{ color: "var(--text2)" }}>
                    {s.message_count} tin nhắn · {formatSessionTime(s.updated_at)}
                  </p>
                </button>

                <button
                  title="Xóa"
                  onClick={(e) => {
                    e.stopPropagation();
                    api
                      .deleteChatSession(String(s.id))
                      .then(() => {
                        setSessions((prev) => prev.filter((x) => x.id !== s.id));
                        if (sessionId === s.id) {
                          startNewConversation();
                        }
                      })
                      .catch(() => {});
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-5 h-5 rounded-md
                             flex items-center justify-center opacity-0 group-hover:opacity-100
                             transition-all duration-150"
                  style={{
                    background: "var(--surface-container-high)",
                    color: "var(--error)",
                    border: "1px solid var(--outline-variant)",
                  }}
                >
                  <X size={10} />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Clear-all */}
        {sessions.length > 0 && (
          <div className="px-3 py-2 border-t border-border flex-shrink-0" style={{ background: "var(--surface-container-low)" }}>
            <button
              onClick={() => {
                Promise.all(sessions.map((s) => api.deleteChatSession(String(s.id))))
                  .then(() => {
                    setSessions([]);
                    startNewConversation();
                  })
                  .catch(() => {});
              }}
              className="w-full text-[10px] py-1.5 rounded-lg transition-colors"
              style={{
                color: "var(--text2)",
                background: "var(--surface-container)",
                border: "1px solid var(--outline-variant)",
              }}
            >
              Xóa tất cả hội thoại
            </button>
          </div>
        )}
      </div>

      {/* ── Main chat area ──────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Header */}
        <div className="px-6 py-4 border-b border-border bg-surface/80 backdrop-blur-sm flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => setHistoryOpen((o) => !o)}
            className={`btn btn-ghost p-2 ${historyOpen ? "text-accent" : ""}`}
            title="Lịch sử hội thoại"
          >
            <History size={15} />
          </button>
          <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-accent to-violet-500">
            <Sparkles size={15} color="white" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-text">AI Agent</h1>
            <p className="text-[11px] text-text2">Trợ lí trí tuệ nhân tạo đa tác vụ</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button className="btn btn-ghost text-xs py-1.5 px-3" onClick={startNewConversation}>
              Mới
            </button>
            <Link href="/graph" className="btn btn-ghost text-xs py-1.5 px-3">
              <Network size={13} /> Xem Graph
            </Link>
            {/* <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#10B981]/10 border border-[#10B981]/20">
              <div className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
              <span className="text-[10px] text-[#10B981] font-medium">Online</span>
            </div> */}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-6">
              <div className="text-center">
                <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center bg-gradient-to-br from-accent to-violet-500 shadow-lg shadow-accent/30">
                  <MessageSquare size={26} color="white" />
                </div>
                <h2 className="text-lg font-bold text-text mb-1">Hỏi về dữ liệu BĐS</h2>
                <p className="text-sm text-text2 max-w-[440px] leading-relaxed">
                  Trò chuyện · tra cứu thông tin ·{" "}
                  {/* <span className="text-accent font-medium">bảng, chart, sơ đồ</span> tự động. */}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full max-w-[580px]">
                {STARTERS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="card text-left text-[13px] text-text hover:border-accent/40 transition-all hover:-translate-y-0.5 py-3 px-4"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => <MessageBubble key={i} msg={m} />)
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-8 py-4 border-t border-border bg-surface/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex gap-2 items-end max-w-4xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                className="input resize-none min-h-[44px] max-h-[120px] py-2.5 leading-relaxed"
                placeholder="Hỏi về dự án, chủ đầu tư, liên hệ... (Enter gửi, Shift+Enter xuống dòng)"
                rows={1}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = "auto";
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
                }}
                onKeyDown={handleKey}
              />
            </div>
            <button
              className="btn btn-primary w-11 h-11 p-0 flex items-center justify-center flex-shrink-0 disabled:opacity-40"
              onClick={() => send(input)}
              disabled={sending || !input.trim()}
            >
              <Send size={16} />
            </button>
          </div>
          <p className="text-[10px] text-text2 text-center mt-2">
            AI Agent có thể mắc lỗi. Hãy xác minh thông tin trước khi đồng ý với bất kỳ sửa đổi nào mà Agent đưa ra.
          </p>
        </div>

      </div>
    </div>
  );
}
