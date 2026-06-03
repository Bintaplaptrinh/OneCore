"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { api, ChatResponse, Project, Stats } from "@/lib/api";
import {
  Building2,
  ChevronDown,
  ChevronUp,
  Columns3,
  CoinsIcon,
  Download,
  MapPin,
  MessageSquare,
  Network,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Table2,
  Users,
  X,
} from "lucide-react";

const LIMIT = 50;

function MetricCard({ icon: Icon, label, value, sub, color }: {
  icon: any;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <div className="metric-card">
      <div className="flex justify-between items-start gap-4">
        <div className="min-w-0">
          <p className="text-[11px] text-text2 uppercase tracking-[0.8px] mb-2">{label}</p>
          <p className="text-[27px] font-bold text-text leading-none truncate">{value}</p>
          {sub && <p className="text-xs text-text2 mt-1">{sub}</p>}
        </div>
        <div
          className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: `${color}20` }}
        >
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  );
}

function FunctionTile({ icon: Icon, label, href, tone }: {
  icon: any;
  label: string;
  href: string;
  tone: "coral" | "orange" | "cyan" | "violet";
}) {
  return (
    <Link href={href} className={`function-tile function-tile-${tone}`}>
      <span className="function-tile-icon"><Icon size={16} /></span>
      <span className="function-tile-label">{label}</span>
      <span className="function-tile-dots" aria-hidden="true">...</span>
    </Link>
  );
}

function MiniBarChart({ bars }: {
  bars: { label: string; color: string; height: number }[];
}) {
  return (
    <div className="mini-bars">
      {bars.map((bar) => (
        <div className="mini-bar" key={bar.label}>
          <div className="mini-bar-track">
            <span
              className="mini-bar-fill"
              style={{ height: `${bar.height}%`, background: bar.color }}
            />
          </div>
          <span>{bar.label}</span>
        </div>
      ))}
    </div>
  );
}

interface ChatMsg {
  role: "user" | "ai";
  content: string;
  loading?: boolean;
}

function MiniChatPanel({ onFilterApply }: {
  onFilterApply: (province?: string, developer?: string) => void;
}) {
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(query: string) {
    const trimmed = query.trim();
    if (!trimmed || sending) return;

    setInput("");
    setSending(true);
    setMessages((prev) => [
      ...prev,
      { role: "user", content: trimmed },
      { role: "ai", content: "", loading: true },
    ]);

    try {
      const res: ChatResponse = await api.chat(trimmed, []);
      if (res.graph_filter) {
        onFilterApply(res.graph_filter.province || undefined, res.graph_filter.developer || undefined);
      }
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "ai", content: res.answer };
        return next;
      });
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { role: "ai", content: "Backend connection error." };
        return next;
      });
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-border flex-shrink-0">
        <div className="w-6 h-6 rounded-lg flex items-center justify-center bg-gradient-to-br from-accent to-[#ff9f0a] flex-shrink-0">
          <Sparkles size={12} color="white" />
        </div>
        <span className="text-xs font-semibold text-text">AI filter</span>
        <span className="ml-auto text-[10px] text-accent">auto table filter</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 flex flex-col gap-2">
        {messages.length === 0 && (
          <div className="flex flex-col gap-1.5 mt-2">
            <p className="text-[11px] text-text2 text-center mb-1">Ask AI to filter this table</p>
            {["Projects in Ha Noi", "Gamuda projects", "Highest value projects"].map((starter) => (
              <button
                key={starter}
                onClick={() => send(starter)}
                className="text-left text-[11px] px-2.5 py-1.5 rounded-lg bg-[var(--surface-container-low)] hover:bg-[var(--surface-container)] text-text transition-colors"
              >
                {starter}
              </button>
            ))}
          </div>
        )}
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "items-start gap-1.5"}`}>
            {message.role === "ai" && (
              <div className="w-5 h-5 rounded-full flex-shrink-0 mt-0.5 flex items-center justify-center bg-gradient-to-br from-accent to-[#ff9f0a]">
                <Sparkles size={9} color="white" />
              </div>
            )}
            <div className={`max-w-[85%] px-2.5 py-1.5 rounded-xl text-[11px] leading-relaxed ${
              message.role === "user" ? "bg-accent text-white" : "bg-[var(--surface-container-high)] text-text"
            }`}>
              {message.loading ? (
                <span className="flex gap-1">
                  {[0, 1, 2].map((delay) => (
                    <span key={delay} className="animate-pulse" style={{ animationDelay: `${delay * 0.2}s` }}>.</span>
                  ))}
                </span>
              ) : (
                <span className="whitespace-pre-wrap">
                  {message.content.slice(0, 500)}{message.content.length > 500 ? "..." : ""}
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-1.5 px-3 py-2.5 border-t border-border flex-shrink-0">
        <input
          className="input flex-1 text-[11px] py-1.5 h-8"
          placeholder="Ask about projects..."
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => { if (event.key === "Enter") send(input); }}
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

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [splitMode, setSplitMode] = useState(false);

  const [province, setProvince] = useState("");
  const [developer, setDeveloper] = useState("");
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const [sortCol, setSortCol] = useState<keyof Project>("name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  useEffect(() => {
    api.stats().then(setStats).catch(console.error);
  }, []);

  useEffect(() => {
    let active = true;
    const timer = setTimeout(() => {
      setLoading(true);
      api.projects({ province, developer, status, search, page, limit: LIMIT })
        .then((result) => {
          if (!active) return;
          setProjects(result.data);
          setTotal(result.total);
        })
        .catch(console.error)
        .finally(() => {
          if (active) setLoading(false);
        });
    }, 300);

    return () => {
      active = false;
      clearTimeout(timer);
    };
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
    if (sortCol === col) {
      setSortDir((direction) => direction === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  }

  function SortIcon({ col }: { col: keyof Project }) {
    if (sortCol !== col) return <span className="opacity-30"><ChevronUp size={12} /></span>;
    return sortDir === "asc" ? <ChevronUp size={12} color="#0058ba" /> : <ChevronDown size={12} color="#0058ba" />;
  }

  function resetFilters() {
    setSearch("");
    setProvince("");
    setStatus("");
    setDeveloper("");
    setPage(1);
  }

  function handleChatFilter(nextProvince?: string, nextDeveloper?: string) {
    if (nextProvince) {
      setProvince(nextProvince);
      setPage(1);
    }
    if (nextDeveloper) {
      setDeveloper(nextDeveloper);
      setPage(1);
    }
  }

  const totalPages = Math.ceil(total / LIMIT);
  const totalRecords = (stats?.total_projects ?? 0) + (stats?.total_contacts ?? 0);
  const projectShare = totalRecords ? Math.round(((stats?.total_projects ?? 0) / totalRecords) * 100) : 25;
  const contactShare = totalRecords ? Math.round(((stats?.total_contacts ?? 0) / totalRecords) * 100) : 50;
  const maxChartValue = Math.max(
    1,
    stats?.total_projects ?? 0,
    stats?.total_contacts ?? 0,
    stats?.total_relationships ?? 0,
    stats?.provinces.length ?? 0
  );
  const chartHeight = (value: number) => Math.max(18, Math.round((value / maxChartValue) * 92));
  const healthScore = totalRecords
    ? Math.min(98, Math.max(58, Math.round(((stats?.total_relationships ?? 0) / Math.max(1, totalRecords)) * 38 + 56)))
    : 58;
  const chartBars = [
    { label: "PRJ", color: "#7ad7e4", height: chartHeight(stats?.total_projects ?? 0) },
    { label: "CON", color: "#c9c3ea", height: chartHeight(stats?.total_contacts ?? 0) },
    { label: "REL", color: "#ff9f0a", height: chartHeight(stats?.total_relationships ?? 0) },
    { label: "LOC", color: "#7ad7e4", height: chartHeight(stats?.provinces.length ?? 0) },
  ];

  return (
    <div className="dashboard-page">
      <div className="dashboard-template-grid">
        <section className="dashboard-core">
          <div className="dashboard-hero">
            <div>
              <p className="dashboard-hello">Hello, Bintaplaptrinh!</p>
              <p className="dashboard-hero-subtitle">Welcome back to CoreOne supporter management</p>
            </div>
            <div className="dashboard-hero-visual" aria-hidden="true">
              <span />
              <span />
              <span />
            </div>
          </div>

          <div className="dashboard-section-head">
            <div>
              <h2>Weekly Reports</h2>
              <p>Live totals from the backend</p>
            </div>
            <div className="dashboard-tabs" aria-label="Report range">
              <span>Today</span>
              <strong>Week</strong>
              <span>Month</span>
            </div>
          </div>

          <div className="dashboard-report-grid">
            <MetricCard icon={Building2} label="Projects" value={stats?.total_projects ?? "-"} sub="records" color="#ff9f0a" />
            <MetricCard icon={Users} label="Contacts" value={stats?.total_contacts ?? "-"} sub="people" color="#10B981" />
            <MetricCard
              icon={CoinsIcon}
              label="Value"
              value={stats ? `${Number(stats.total_value_billion_vnd).toLocaleString("vi-VN")}B` : "-"}
              sub="VND"
              color="#ef536d"
            />
            <MetricCard icon={MapPin} label="Markets" value={stats?.provinces.length ?? "-"} sub="locations" color="#7ad7e4" />
          </div>

          <div className="dashboard-section-head compact">
            <div>
              <h2>Updating Monitoring</h2>
              <p>Index coverage and data density</p>
            </div>
          </div>

          <div className="dashboard-monitoring">
            <div className="monitor-card">
              <div>
                <span>Project Files</span>
                <strong>Share {projectShare}%</strong>
              </div>
              <div className="monitor-ring" style={{ ["--value" as any]: `${projectShare}%` }}>
                <span>{projectShare}%</span>
              </div>
            </div>
            <div className="monitor-card is-primary">
              <div>
                <span>Contact Network</span>
                <strong>Mapped {contactShare}%</strong>
              </div>
              <div className="monitor-ring" style={{ ["--value" as any]: `${contactShare}%` }}>
                <span>{contactShare}%</span>
              </div>
            </div>
          </div>
        </section>

        <aside className="dashboard-side">
          <section className="dashboard-side-section">
            <h2>Other Functions</h2>
            <div className="function-grid">
              <FunctionTile href="/chat" icon={MessageSquare} label="AI Chat" tone="coral" />
              <FunctionTile href="/graph" icon={Network} label="Smart Graph" tone="orange" />
              <FunctionTile href="/tables" icon={Table2} label="Data Manager" tone="cyan" />
              <FunctionTile href="/tables?mode=upload" icon={Table2} label="Upload Data" tone="violet" />
            </div>
          </section>

          <section className="dashboard-side-section">
            <h2>Supporter Statistics</h2>
            <div className="lead-stats-card">
              <div className="lead-stats-head">
                <div>
                  <span>Current index</span>
                  <strong>{healthScore}%</strong>
                </div>
                <ShieldCheck size={18} />
              </div>
              <MiniBarChart bars={chartBars} />
            </div>
          </section>
        </aside>
      </div>

      <section className="dashboard-data-panel">
        <div className="dashboard-data-header">
          <div>
            <h2>Project Pipeline</h2>
            <p>
              Showing {projects.length} / {total} projects
              {splitMode && <span> - AI split view is active</span>}
            </p>
          </div>
          <button
            onClick={() => setSplitMode((mode) => !mode)}
            className={`btn gap-2 ${splitMode ? "btn-primary" : "btn-ghost"}`}
          >
            {splitMode ? <X size={14} /> : <Columns3 size={14} />}
            {splitMode ? "Close Split" : "Split View"}
          </button>
        </div>

        <div className="dashboard-filter-row">
          <div className="relative flex-[2] min-w-[180px]">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text2 pointer-events-none" />
            <input
              className="input pl-8"
              placeholder="Search projects, addresses, notes..."
              value={search}
              onChange={(event) => { setSearch(event.target.value); setPage(1); }}
            />
          </div>
          <select className="input flex-1 min-w-[140px]"
            value={province} onChange={(event) => { setProvince(event.target.value); setPage(1); }}>
            <option value="">All provinces</option>
            {stats?.provinces.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select className="input flex-1 min-w-[160px]"
            value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
            <option value="">All statuses</option>
            {stats?.statuses.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <input
            className="input flex-1 min-w-[140px]"
            placeholder="Developer..."
            value={developer}
            onChange={(event) => { setDeveloper(event.target.value); setPage(1); }}
          />
          <button className="btn btn-ghost" onClick={resetFilters}>
            <RefreshCw size={14} /> Reset
          </button>
          <button className="btn btn-primary" onClick={() => api.exportExcel({ province, developer, status, search })}>
            <Download size={14} /> Export
          </button>
        </div>

        <div className={splitMode ? "dashboard-table-split" : ""}>
          <div className={splitMode ? "flex-1 min-w-0" : ""}>
            <div className="dashboard-table-shell">
              <div className="overflow-x-auto">
                {loading ? (
                  <div className="py-10 text-center text-text2">Loading data...</div>
                ) : (
                  <table className="data-table">
                    <thead>
                      <tr>
                        {[
                          ["name", "Project"],
                          ["province", "Province"],
                          ["developer", "Developer"],
                          ["value_str", "Value"],
                          ["status", "Status"],
                          ["type_tags", "Type"],
                          ["groundbreaking", "Start"],
                          ["handover", "Handover"],
                        ].map(([col, label]) => (
                          <th key={col} onClick={() => toggleSort(col as keyof Project)}>
                            <span className="flex items-center gap-1">{label} <SortIcon col={col as keyof Project} /></span>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sorted.map((project) => (
                        <tr key={project.slug}>
                          <td className="font-medium text-[#0058ba] max-w-[240px]" title={project.name}>{project.name}</td>
                          <td>{project.province}</td>
                          <td title={(project.developer || []).join(", ")}>
                            {(project.developer || []).slice(0, 1).join("")}
                            {(project.developer || []).length > 1 && (
                              <span className="text-[10px] text-text2"> +{(project.developer || []).length - 1}</span>
                            )}
                          </td>
                          <td className="text-[#ff9f0a] font-medium">{project.value_str || "-"}</td>
                          <td>
                            <span className={`badge ${project.status?.toLowerCase().includes("ho") ? "badge-status-ok" : "badge-status-wip"}`}>
                              {project.status?.slice(0, 20) || "-"}
                            </span>
                          </td>
                          <td>
                            {(Array.isArray(project.type_tags) ? project.type_tags : []).map((tag) => (
                              <span key={tag} className="badge badge-project mr-1">{tag}</span>
                            ))}
                          </td>
                          <td className="text-text2">{project.groundbreaking || "-"}</td>
                          <td className="text-text2">{project.handover || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 px-5 py-3 border-t border-border">
                  <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
                  <span className="text-[13px] text-text2">Page {page} / {totalPages}</span>
                  <button className="btn btn-ghost" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>Next</button>
                </div>
              )}
            </div>
          </div>

          {splitMode && (
            <div className="dashboard-chat-panel">
              <MiniChatPanel onFilterApply={handleChatFilter} />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
