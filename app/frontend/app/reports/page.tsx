"use client";
import { useEffect, useState } from "react";
import { api, Report } from "@/lib/api";
import {
  FileText, Download, RefreshCw, Search, FileSpreadsheet,
  Clock, MessageSquare, FileCode,
} from "lucide-react";

function ReportIcon({ title }: { title: string }) {
  if (title.startsWith("Tóm tắt:")) return <FileCode size={18} className="text-accent" />;
  return <FileSpreadsheet size={18} className="text-[#10B981]" />;
}

function formatDate(ts: string) {
  if (!ts) return "";
  return ts.slice(0, 16).replace("T", " ");
}

function ReportCard({ r, onDownload }: { r: Report; onDownload: () => void }) {
  const isMarkdown = r.file_path?.endsWith(".md");
  return (
    <div className="card hover:border-accent/30 transition-all duration-200 flex flex-col gap-2">
      {/* Icon + title */}
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-surface flex-shrink-0 mt-0.5">
          <ReportIcon title={r.title} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text leading-snug line-clamp-2">{r.title}</p>
          <div className="flex items-center gap-1.5 mt-0.5">
            <Clock size={10} className="text-text2" />
            <span className="text-[10px] text-text2">{formatDate(r.timestamp)}</span>
          </div>
        </div>
      </div>

      {/* Query that generated it */}
      {r.query && !r.query.startsWith("summary:") && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 rounded-md bg-[var(--surface-container-low)] border border-border">
          <MessageSquare size={10} className="text-text2 mt-0.5 flex-shrink-0" />
          <p className="text-[11px] text-text2 line-clamp-2 leading-snug">{r.query}</p>
        </div>
      )}

      {/* Download */}
      <button
        onClick={onDownload}
        className="btn btn-ghost w-full text-xs py-1.5 mt-auto"
        disabled={isMarkdown}
        title={isMarkdown ? "Báo cáo dạng văn bản (không tải được)" : "Tải về"}
      >
        <Download size={12} />
        {isMarkdown ? "Báo cáo văn bản" : "Tải lại Excel"}
      </button>
    </div>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]   = useState("");

  function load() {
    setLoading(true);
    api.reports()
      .then(r => setReports(r.data))
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  const filtered = reports.filter(r =>
    r.title.toLowerCase().includes(search.toLowerCase()) ||
    (r.query || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-bg px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-gradient-to-br from-accent to-violet-500 shadow-lg shadow-accent/30">
            <FileText size={18} color="white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-text">Kho Báo cáo</h1>
            <p className="text-xs text-text2">
              {reports.length} báo cáo đã lưu — Excel từ Chat AI · Tạo báo cáo: Coming soon
            </p>
          </div>
        </div>
        <button onClick={load} className="btn btn-ghost text-xs py-1.5 px-3" title="Làm mới">
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} /> Làm mới
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-6 max-w-sm">
        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-text2" />
        <input
          className="input pl-8 text-sm"
          placeholder="Tìm báo cáo..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <RefreshCw size={24} className="text-accent animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-40 gap-3">
          <FileText size={32} className="text-text2/40" />
          {reports.length === 0 ? (
            <>
              <p className="text-sm text-text2">Chưa có báo cáo nào.</p>
              <p className="text-xs text-text2/60 max-w-xs text-center">
                Tạo bảng từ Chat AI (ấn nút Excel). Tính năng tạo báo cáo: Coming soon.
              </p>
            </>
          ) : (
            <p className="text-sm text-text2">Không tìm thấy kết quả</p>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map(r => (
            <ReportCard
              key={r.id}
              r={r}
              onDownload={() => api.reportDownload(r.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
