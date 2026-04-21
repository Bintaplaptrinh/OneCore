"use client";
import { useState, useCallback } from "react";
import { Upload, CheckCircle, Edit3, AlertCircle, Loader2, ChevronRight } from "lucide-react";

type ParsedRow = Record<string, string>;
type PreviewData = {
  headers: string[];
  field_keys: string[];
  rows: ParsedRow[];
  entity_type: string;
  raw_parsed: Record<string, unknown>; // original parsed_data from backend
};

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export default function UploadPage() {
  const [phase, setPhase] = useState<"drop" | "preview" | "confirm" | "done">("drop");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [editedRows, setEditedRows] = useState<ParsedRow[]>([]);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [fileName, setFileName] = useState("");

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setFileName(file.name);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/upload/preview`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to parse file");
      }

      const resp = await res.json();
      // Backend returns: { ok, type, parsed_data, preview: { headers, field_keys, rows, entity_type } }
      const pv = resp.preview ?? {};
      const previewData: PreviewData = {
        headers:     Array.isArray(pv.headers)    ? pv.headers    : [],
        field_keys:  Array.isArray(pv.field_keys) ? pv.field_keys : [],
        rows:        Array.isArray(pv.rows)        ? pv.rows        : [],
        entity_type: pv.entity_type ?? "mixed",
        raw_parsed:  resp.parsed_data ?? {},
      };
      setPreview(previewData);
      setEditedRows([...previewData.rows]);
      setPhase("preview");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const file = files[0];

    if (file) {
      handleFile(file);
    }
  };

  const handleCellEdit = (rowIdx: number, col: string, value: string) => {
    setEditedRows((prev) =>
      prev.map((row, i) =>
        i === rowIdx ? { ...row, [col]: value } : row
      )
    );
  };

  const handleConfirm = async () => {
    if (!preview) return;

    setLoading(true);
    setError(null);

    try {
      // Reconstruct parsed_data in backend format from edited rows
      const et = preview.entity_type;
      let reconstructedData: Record<string, unknown>;
      if (et === "contact") {
        reconstructedData = { ...preview.raw_parsed, contacts: editedRows };
      } else if (et === "project") {
        reconstructedData = { ...preview.raw_parsed, projects: editedRows };
      } else {
        // mixed: split by _type field if present, else fall back to raw
        const proj = editedRows.filter(r => r._type === "Dự án" || !r._type);
        const cont = editedRows.filter(r => r._type === "Liên hệ");
        reconstructedData = { ...preview.raw_parsed, projects: proj, contacts: cont };
      }

      const res = await fetch(`${API_BASE}/api/upload/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parsed_data: reconstructedData }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to save data");
      }

      const data = await res.json();
      setResult(data);
      setPhase("done");
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Unknown error occurred";
      setError(errorMsg);
      setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  // Phase 1: Drop zone
  if (phase === "drop") {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="page-header">Upload & OCR</h1>
          <p className="text-text2 mt-1 text-sm">Tải lên tài liệu — hệ thống sẽ tự động trích xuất và phân tích</p>
        </div>

        {/* Supported formats info */}
        <div className="card mb-6 p-4">
          <p className="text-sm text-text2">
            Hỗ trợ: <span className="text-text font-medium">Excel (.xlsx, .csv)</span> ·
            <span className="text-text font-medium"> PDF</span> ·
            <span className="text-text font-medium"> Ảnh (.jpg, .png, .webp)</span>
          </p>
        </div>

        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          className={`border-2 border-dashed rounded-2xl p-16 text-center transition-all cursor-pointer ${
            dragging
              ? "border-primary bg-primary/5 scale-[1.02]"
              : "border-outline-variant hover:border-primary/50 hover:bg-surface-container-low"
          }`}
          onClick={() => document.getElementById("file-input")?.click()}
        >
          <Upload size={40} className="mx-auto mb-4 text-text2" />
          <p className="text-base font-medium text-text mb-1">Kéo thả hoặc nhấn để chọn file</p>
          <p className="text-sm text-text2">Tối đa 25MB</p>
          <input
            id="file-input"
            type="file"
            className="hidden"
            accept=".xlsx,.xls,.csv,.pdf,.jpg,.jpeg,.png,.webp"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
        </div>

        {loading && (
          <div className="mt-6 card flex items-center gap-3 p-4">
            <Loader2 size={20} className="animate-spin text-primary" />
            <div>
              <p className="font-medium text-sm">Đang phân tích với Gemma4...</p>
              <p className="text-xs text-text2">OCR → Trích xuất thực thể → Chuẩn hóa</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-center gap-2 text-error text-sm p-3 bg-error/5 rounded-xl">
            <AlertCircle size={16} /> {error}
          </div>
        )}
      </div>
    );
  }

  // Phase 2: Preview & Edit Table
  if (phase === "preview" && preview) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="page-header">Xem trước & Chỉnh sửa</h1>
            <p className="text-text2 text-sm mt-1">
              Kiểm tra và chỉnh sửa dữ liệu trước khi lưu · {fileName}
            </p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => setPhase("drop")} className="btn btn-ghost">
              ← Tải file khác
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="btn btn-primary gap-2 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <CheckCircle size={14} />
              )}
              Xác nhận & Lưu ({editedRows.length} mục)
            </button>
          </div>
        </div>

        {/* Entity type badge */}
        <div className="mb-4 flex items-center gap-2">
          <span
            className="badge"
            style={{
              background: "rgba(99,102,241,0.1)",
              color: "#6366F1",
            }}
          >
            {preview.entity_type === "contact"
              ? "📇 Liên hệ"
              : preview.entity_type === "project"
              ? "🏗️ Dự án"
              : "📋 Hỗn hợp"}
          </span>
          <span className="text-xs text-text2">
            <Edit3 size={11} className="inline mr-1" />
            Nhấn vào ô để chỉnh sửa
          </span>
        </div>

        {/* Editable table */}
        <div className="surface-elevated overflow-auto rounded-lg">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th style={{ width: 40 }}>#</th>
                {preview.headers.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {editedRows.map((row, rowIdx) => (
                <tr key={rowIdx}>
                  <td className="text-text2 text-xs">{rowIdx + 1}</td>
                  {preview.field_keys.map((key) => (
                    <td key={key}>
                      <input
                        value={String(row[key] ?? "")}
                        onChange={(e) => handleCellEdit(rowIdx, key, e.target.value)}
                        className="w-full bg-transparent outline-none focus:bg-surface-container-low px-1 rounded text-sm"
                        placeholder="-"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 text-error text-sm p-3 bg-error/5 rounded-xl">
            <AlertCircle size={16} /> {error}
          </div>
        )}
      </div>
    );
  }

  // Phase 3: Done
  if (phase === "done" && result) {
    return (
      <div className="p-8 max-w-lg mx-auto text-center">
        <div className="card p-8">
          <CheckCircle size={48} className="mx-auto mb-4 text-secondary" />
          <h2 className="section-title text-xl mb-2">Đã lưu thành công!</h2>
          <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
            {[
              ["Dự án", (result.projects_added as number) || 0],
              ["Liên hệ", (result.contacts_added as number) || 0],
              ["Công ty", (result.companies_added as number) || 0],
              ["Quan hệ", (result.relationships_added as number) || 0],
            ].map(([label, count]) => (
              <div key={String(label)} className="bg-surface-container-low rounded-xl p-3">
                <div className="text-2xl font-bold text-primary">{String(count)}</div>
                <div className="text-text2">{String(label)}</div>
              </div>
            ))}
          </div>
          {(result.errors as string[])?.length > 0 && (
            <div className="mt-4 text-left">
              <p className="text-xs font-medium text-error mb-1">
                Lỗi ({(result.errors as string[]).length}):
              </p>
              {(result.errors as string[])
                .slice(0, 3)
                .map((e, i) => (
                  <p key={i} className="text-xs text-text2 truncate">
                    {e}
                  </p>
                ))}
            </div>
          )}
          <button
            onClick={() => {
              setPhase("drop");
              setResult(null);
              setPreview(null);
              setEditedRows([]);
              setError(null);
            }}
            className="btn btn-primary mt-6 mx-auto"
          >
            Upload file khác
          </button>
        </div>
      </div>
    );
  }

  return null;
}
