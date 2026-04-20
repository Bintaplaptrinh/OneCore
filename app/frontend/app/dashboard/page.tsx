"use client";
import { useEffect, useState, useMemo, useRef } from "react";
import { api, Project, Stats, ChatResponse } from "@/lib/api";
import {
  Building2, Users, DollarSign, MapPin,
  Search, Download, RefreshCw, ChevronUp, ChevronDown,
  Columns3, X, Send, Sparkles,
  CoinsIcon,
} from "lucide-react";

// ── Metric Card ───────────────────────────────────────────────────────────────
function MetricCard({ icon: Icon, label, value, sub, color }: {
  icon: any; label: string; value: string | number; sub?: string; color: string;
}) {
  return (
    <div className="metric-card">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-[11px] text-text2 uppercase tracking-[0.8px] mb-2">{label}</p>
          <p className="text-[28px] font-bold text-text leading-none">{value}</p>
          {sub && <p className="text-xs text-text2 mt-1">{sub}</p>}
        </div>
        <div className="w-10 h-10 rounded-[10px] flex items-center justify-center flex-shrink-0"
          style={{ background: `${color}20` }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  );
}

// ── Mini Chat Panel ───────────────────────────────────────────────────────────
interface ChatMsg { role: "user" | "ai"; content: string; loading?: boolean; }

function MiniChatPanel({ onFilterApply }: {
  onFilterApply: (province?: string, developer?: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput]       = useState("");
  const [sending, setSending]   = useState(false);
  const bottomRef               = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(query: string) {
    if (!query.trim() || sending) return;
    setInput("");
    setSending(true);
    setMessages(prev => [
      ...prev,
      { role: "user", content: query },
      { role: "ai", content: "", loading: true },
    ]);

    try {
      const res: ChatResponse = await api.chat(query, []);
      if (res.graph_filter) {
        const gf = res.graph_filter;
        onFilterApply(gf.province || undefined, gf.developer || undefined);
      }
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = { role: "ai", content: res.answer };
        return next;
      });
    } catch {
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = { role: "ai", content: "Lỗi kết nối backend." };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border flex-shrink-0">
        <div className="w-6 h-6 rounded-lg flex items-center justify-center bg-gradient-to-br from-accent to-violet-500 flex-shrink-0">
          <Sparkles size={12} color="white" />
        </div>
        <span className="text-xs font-semibold text-text">Chat AI</span>
        <span className="ml-auto text-[10px] text-accent">Tự động lọc bảng</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 flex flex-col gap-2">
        {messages.length === 0 && (
          <div className="flex flex-col gap-1.5 mt-2">
            <p className="text-[11px] text-text2 text-center mb-1">Chat để lọc bảng tự động</p>
            {["Dự án đang xây ở Hà Nội", "Gamuda có dự án nào?", "Dự án giá trị lớn nhất"].map(s => (
              <button key={s} onClick={() => send(s)}
                className="text-left text-[11px] px-2.5 py-1.5 rounded-lg bg-[var(--surface-container-low)] hover:bg-[var(--surface-container)] text-text transition-colors">
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "items-start gap-1.5"}`}>
            {m.role === "ai" && (
              <div className="w-5 h-5 rounded-full flex-shrink-0 mt-0.5 flex items-center justify-center bg-gradient-to-br from-accent to-violet-500">
                <Sparkles size={9} color="white" />
              </div>
            )}
            <div className={`max-w-[85%] px-2.5 py-1.5 rounded-xl text-[11px] leading-relaxed ${
              m.role === "user" ? "bg-accent text-white" : "bg-[var(--surface-container-high)] text-text"
            }`}>
              {m.loading
                ? <span className="flex gap-1">{[0,1,2].map(d => <span key={d} className="animate-pulse" style={{ animationDelay: `${d*0.2}s` }}>●</span>)}</span>
                : <span className="whitespace-pre-wrap">{m.content.slice(0, 500)}{m.content.length > 500 ? "..." : ""}</span>
              }
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-1.5 px-3 py-2.5 border-t border-border flex-shrink-0">
        <input
          className="input flex-1 text-[11px] py-1.5 h-8"
          placeholder="Hỏi về dự án... (Enter gửi)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") send(input); }}
          disabled={sending}
        />
        <button
          className="btn btn-primary w-8 h-8 p-0 flex items-center justify-center flex-shrink-0 disabled:opacity-40"
          onClick={() => send(input)}
          disabled={sending || !input.trim()}
        >
          <Send size={12} />
        </button>
      </div>
    </div>
  );
}


// ── Main Dashboard ─────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [stats, setStats]       = useState<Stats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [splitMode, setSplitMode] = useState(false);

  const [province, setProvince]   = useState("");
  const [developer, setDeveloper] = useState("");
  const [status, setStatus]       = useState("");
  const [search, setSearch]       = useState("");
  const [page, setPage]           = useState(1);
  const LIMIT = 50;

  const [sortCol, setSortCol] = useState<keyof Project>("name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  useEffect(() => { api.stats().then(setStats).catch(console.error); }, []);

  useEffect(() => {
    let active = true;
    const t = setTimeout(() => {
      setLoading(true);
      api.projects({ province, developer, status, search, page, limit: LIMIT })
        .then(r => { if (active) { setProjects(r.data); setTotal(r.total); } })
        .catch(console.error)
        .finally(() => { if (active) setLoading(false); });
    }, 300);
    return () => { active = false; clearTimeout(t); };
  }, [province, developer, status, search, page]);

  const sorted = useMemo(() => {
    return [...projects].sort((a, b) => {
      if (sortCol === "value_str") {
        const va = (a.value_billion_vnd as number) || 0;
        const vb = (b.value_billion_vnd as number) || 0;
        return sortDir === "asc" ? va - vb : vb - va;
      }
      const va = String(a[sortCol] ?? "");
      const vb = String(b[sortCol] ?? "");
      return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }, [projects, sortCol, sortDir]);

  function toggleSort(col: keyof Project) {
    if (sortCol === col) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortCol(col); setSortDir("asc"); }
  }

  function SortIcon({ col }: { col: keyof Project }) {
    if (sortCol !== col) return <span className="opacity-30"><ChevronUp size={12} /></span>;
    return sortDir === "asc" ? <ChevronUp size={12} color="#6366F1" /> : <ChevronDown size={12} color="#6366F1" />;
  }

  const totalPages = Math.ceil(total / LIMIT);

  function handleChatFilter(p?: string, dev?: string) {
    if (p) { setProvince(p); setPage(1); }
    if (dev) { setDeveloper(dev); setPage(1); }
  }

  return (
    <div className="px-8 py-7">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="page-header">Dashboard</h1>
          <p className="text-[13px] text-text2 mt-0.5">Tổng quan toàn bộ hệ thống dữ liệu bất động sản</p>
        </div>
        <button
          onClick={() => setSplitMode(m => !m)}
          className={`btn gap-2 ${splitMode ? "btn-primary" : "btn-ghost"}`}
        >
          {splitMode ? <X size={14} /> : <Columns3 size={14} />}
          {splitMode ? "Tắt Split" : "Split View"}
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-4 gap-4 mb-7">
        <MetricCard icon={Building2}  label="Dự án"       value={stats?.total_projects ?? "—"} sub="projects"   color="#6366F1" />
        <MetricCard icon={Users}      label="Liên hệ"     value={stats?.total_contacts ?? "—"} sub="contacts"   color="#10B981" />
        <MetricCard icon={CoinsIcon} label="Tổng giá trị" value={stats ? `${Number(stats.total_value_billion_vnd).toLocaleString("vi-VN")} tỷ` : "—"} sub="VNĐ" color="#F59E0B" />
        <MetricCard icon={MapPin}     label="Tỉnh/Thành"  value={stats?.provinces.length ?? "—"} sub="địa phương" color="#EC4899" />
      </div>

      {/* Filter bar */}
      <div className="card mb-4">
        <div className="flex gap-2.5 flex-wrap items-center">
          <div className="relative flex-[2] min-w-[180px]">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text2 pointer-events-none" />
            <input className="input pl-8" placeholder="Tìm dự án, địa chỉ, ghi chú..."
              value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} />
          </div>
          <select className="input flex-1 min-w-[140px]"
            value={province} onChange={e => { setProvince(e.target.value); setPage(1); }}>
            <option value="">Tất cả tỉnh</option>
            {stats?.provinces.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="input flex-1 min-w-[160px]"
            value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}>
            <option value="">Tất cả trạng thái</option>
            {stats?.statuses.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <input className="input flex-1 min-w-[140px]" placeholder="Chủ đầu tư..."
            value={developer} onChange={e => { setDeveloper(e.target.value); setPage(1); }} />
          <button className="btn btn-ghost" onClick={() => { setSearch(""); setProvince(""); setStatus(""); setDeveloper(""); setPage(1); }}>
            <RefreshCw size={14} /> Reset
          </button>
          <button className="btn btn-primary" onClick={() => api.exportExcel({ province, developer, status, search })}>
            <Download size={14} /> Export Excel
          </button>
        </div>
        <p className="text-[11px] text-text2 mt-2.5">
          Hiển thị {projects.length} / {total} dự án
          {splitMode && <span className="ml-2 text-accent">· Chat AI sẽ tự động lọc bảng</span>}
        </p>
      </div>

      {/* ── Table + optional Chat panel ──────────────────────────────────────── */}
      <div className={splitMode ? "flex gap-4 items-start" : ""}>

        {/* Table */}
        <div className={splitMode ? "flex-1 min-w-0" : ""}>
          <div className="card !p-0 overflow-hidden">
            <div className="overflow-x-auto">
              {loading ? (
                <div className="py-10 text-center text-text2">Đang tải...</div>
              ) : (
                <table className="data-table">
                  <thead>
                    <tr>
                      {[
                        ["name","Tên dự án"],["province","Tỉnh"],["developer","Chủ đầu tư"],
                        ["value_str","Giá trị"],["status","Trạng thái"],["type_tags","Loại hình"],
                        ["groundbreaking","Khởi công"],["handover","Bàn giao"],
                      ].map(([col, label]) => (
                        <th key={col} onClick={() => toggleSort(col as keyof Project)}>
                          <span className="flex items-center gap-1">{label} <SortIcon col={col as keyof Project} /></span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map(p => (
                      <tr key={p.slug}>
                        <td className="font-medium text-[#818CF8] max-w-[240px]" title={p.name}>{p.name}</td>
                        <td>{p.province}</td>
                        <td title={(p.developer || []).join(", ")}>
                          {(p.developer || []).slice(0, 1).join("")}
                          {(p.developer || []).length > 1 && <span className="text-[10px] text-text2"> +{(p.developer || []).length - 1}</span>}
                        </td>
                        <td className="text-[#FCD34D] font-medium">{p.value_str || "—"}</td>
                        <td>
                          <span className={`badge ${p.status?.includes("Hoàn") ? "badge-status-ok" : "badge-status-wip"}`}>
                            {p.status?.slice(0, 20) || "—"}
                          </span>
                        </td>
                        <td>{(Array.isArray(p.type_tags) ? p.type_tags : []).map(t => <span key={t} className="badge badge-project mr-1">{t}</span>)}</td>
                        <td className="text-text2">{p.groundbreaking || "—"}</td>
                        <td className="text-text2">{p.handover || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-2 px-5 py-3 border-t border-border">
                <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Trước</button>
                <span className="text-[13px] text-text2">Trang {page} / {totalPages}</span>
                <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Sau →</button>
              </div>
            )}
          </div>
        </div>

        {/* Chat panel — split mode only */}
        {splitMode && (
          <div className="w-[340px] flex-shrink-0 card !p-0 overflow-hidden" style={{ height: 560 }}>
            <MiniChatPanel onFilterApply={handleChatFilter} />
          </div>
        )}
      </div>
    </div>
  );
}
