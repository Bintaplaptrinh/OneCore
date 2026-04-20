"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, FieldDef, Stats } from "@/lib/api";
import {
  Table2, GripVertical, X, Download, FileSpreadsheet,
  RefreshCw, Plus, Sparkles, Trash2, Save,
} from "lucide-react";

const TEMPLATES: { id: string; name: string; emoji: string; source: "projects"|"contacts"; columns: string[]; filters: Record<string,string> }[] = [
  { id: "phones",       name: "SĐT theo chủ thầu", emoji: "", source: "contacts",
    columns: ["name","company","role","phone","email"], filters: {} },
  { id: "by_province",  name: "Dự án theo tỉnh",   emoji: "", source: "projects",
    columns: ["name","province","developer","status","value_str"], filters: {} },
  { id: "construction", name: "Dự án đang xây",     emoji: "", source: "projects",
    columns: ["name","province","developer","groundbreaking","handover","value_str"], filters: { status: "xây" } },
  { id: "high_value",   name: "Giá trị lớn",        emoji: "", source: "projects",
    columns: ["name","province","developer","value_str","status"], filters: {} },
  { id: "contacts_dir", name: "Danh bạ liên hệ",   emoji: "", source: "contacts",
    columns: ["name","company","role","phone","email","address"], filters: {} },
  { id: "danang",       name: "Dự án Đà Nẵng",      emoji: "", source: "projects",
    columns: ["name","district","developer","status","type_tags","value_str"], filters: { province: "Danang" } },
];

const PROJECT_FIELDS: FieldDef[] = [
  { key: "name",          label: "Tên dự án"      },
  { key: "province",      label: "Tỉnh/TP"        },
  { key: "district",      label: "Quận/Huyện"     },
  { key: "address",       label: "Địa chỉ"        },
  { key: "developer",     label: "Chủ đầu tư"     },
  { key: "value_str",     label: "Giá trị"         },
  { key: "status",        label: "Trạng thái"     },
  { key: "phase",         label: "Giai đoạn"      },
  { key: "type_tags",     label: "Loại hình"      },
  { key: "site_area",     label: "Diện tích đất"  },
  { key: "floors",        label: "Số tầng"        },
  { key: "groundbreaking",label: "Khởi công"      },
  { key: "handover",      label: "Bàn giao"       },
  { key: "notes",         label: "Ghi chú"        },
];
const CONTACT_FIELDS: FieldDef[] = [
  { key: "name",    label: "Họ tên"          },
  { key: "company", label: "Công ty"         },
  { key: "role",    label: "Chức vụ"         },
  { key: "phone",   label: "Số điện thoại"  },
  { key: "email",   label: "Email"           },
  { key: "address", label: "Địa chỉ"        },
];

const DEFAULT_PROJECT_COLS = ["name", "province", "developer", "status", "value_str"];
const DEFAULT_CONTACT_COLS = ["name", "company", "role", "phone", "email"];
const PAGE_SIZE = 100;

function getLabel(fields: FieldDef[], key: string) {
  return fields.find(f => f.key === key)?.label ?? key;
}
function rowVal(row: Record<string, any>, key: string): string {
  const v = row[key];
  if (Array.isArray(v)) return v.join(", ");
  if (v == null) return "";
  return String(v);
}

export default function TablesPage() {
  const [source, setSource]               = useState<"projects"|"contacts">("projects");
  const [selectedCols, setSelectedCols]   = useState<string[]>(DEFAULT_PROJECT_COLS);
  const [filters, setFilters]             = useState<Record<string,string>>({});
  const [title, setTitle]                 = useState("LeadsMap Export");
  const [previewData, setPreviewData]     = useState<Record<string,any>[]>([]);
  const [previewTotal, setPreviewTotal]   = useState(0);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [currentPage, setCurrentPage]       = useState(1);
  const [pendingTable, setPendingTable]   = useState<{headers:string[];rows:string[][]}|null>(null);
  const [editableRows, setEditableRows]   = useState<string[][]>([]);
  const [originalRows, setOriginalRows]   = useState<string[][]>([]);
  const [rowIds, setRowIds]               = useState<string[]>([]);
  const [deletedRowIds, setDeletedRowIds] = useState<string[]>([]);
  const [activeRowIndex, setActiveRowIndex] = useState<number|null>(null);
  const [pageInput, setPageInput]         = useState("1");
  const [isEditMode, setIsEditMode]       = useState(false);
  const [saveLoading, setSaveLoading]     = useState(false);
  const [stats, setStats]                 = useState<Stats|null>(null);
  const [dragIndex, setDragIndex]         = useState<number|null>(null);
  const [dragOver,  setDragOver]          = useState<number|null>(null);
  const timerRef = useRef<any>(null);

  const allFields = source === "contacts" ? CONTACT_FIELDS : PROJECT_FIELDS;

  useEffect(() => {
    const raw = localStorage.getItem("leadsmap_pending_table");
    if (raw) {
      try { const p = JSON.parse(raw); if (p?.headers) setPendingTable(p); } catch {}
      localStorage.removeItem("leadsmap_pending_table");
    }
    api.stats().then(setStats).catch(() => {});
  }, []);

  useEffect(() => {
    if (pendingTable || selectedCols.length === 0) { if (!pendingTable) { setPreviewData([]); setPreviewTotal(0); } return; }
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      setPreviewLoading(true);
      try {
        const res = await api.query({ source, columns: selectedCols, filters, page: currentPage, limit: PAGE_SIZE });
        const maxPage = Math.max(1, Math.ceil((res.total || 0) / PAGE_SIZE));
        if (currentPage > maxPage) {
          setCurrentPage(maxPage);
          return;
        }
        setPreviewData(res.data);
        setPreviewTotal(res.total);
      } catch {
        setPreviewData([]);
        setPreviewTotal(0);
      }
      finally { setPreviewLoading(false); }
    }, 400);
    return () => clearTimeout(timerRef.current);
  }, [source, selectedCols, filters, pendingTable, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [source, selectedCols, filters, pendingTable]);

  function applyTemplate(t: typeof TEMPLATES[0]) {
    setPendingTable(null); setSource(t.source);
    setSelectedCols(t.columns); setFilters(t.filters); setTitle(t.name); setCurrentPage(1);
  }
  function addCol(key: string) { if (!selectedCols.includes(key)) setSelectedCols(p => [...p, key]); }
  function removeCol(key: string) { setSelectedCols(p => p.filter(k => k !== key)); }

  function handleDragStart(e: React.DragEvent, idx: number) {
    setDragIndex(idx); e.dataTransfer.effectAllowed = "move";
  }
  function handleDragOver(e: React.DragEvent, idx: number) {
    e.preventDefault(); e.dataTransfer.dropEffect = "move"; setDragOver(idx);
  }
  function handleDrop(e: React.DragEvent, targetIdx: number) {
    e.preventDefault();
    if (dragIndex !== null && dragIndex !== targetIdx) {
      const next = [...selectedCols];
      const [rm] = next.splice(dragIndex, 1);
      next.splice(targetIdx, 0, rm);
      setSelectedCols(next);
    }
    setDragIndex(null); setDragOver(null);
  }
  function handleDragEnd() { setDragIndex(null); setDragOver(null); }

  function setFilter(key: string, val: string) { setFilters(p => ({ ...p, [key]: val })); }

  function exportExcel() {
    if (!editableRows.length) return;
    api.exportTable(displayHeaders, editableRows, title);
  }
  function exportCSV() {
    const headers = pendingTable ? pendingTable.headers : selectedCols.map(k => getLabel(allFields, k));
    const rows    = editableRows;
    const csv  = [headers.join(","), ...rows.map(r => r.map(c => `"${String(c).replace(/"/g,'""')}"`).join(","))].join("\n");
    const blob = new Blob(["\uFEFF"+csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `${title}.csv`; a.click(); URL.revokeObjectURL(url);
  }

  function resetEditableRows() {
    setEditableRows(originalRows.map(row => [...row]));
    setDeletedRowIds([]);
    setActiveRowIndex(null);
  }

  function updateCell(rowIndex: number, colIndex: number, value: string) {
    setEditableRows(prev => {
      const next = prev.map(row => [...row]);
      if (!next[rowIndex]) return prev;
      next[rowIndex][colIndex] = value;
      return next;
    });
  }

  function addEmptyRow() {
    const columnCount = displayHeaders.length;
    if (!columnCount) return;
    const defaultInsertAt = pendingTable ? Math.max(0, (currentPage - 1) * PAGE_SIZE) : 0;
    const insertAt = activeRowIndex === null
      ? Math.min(defaultInsertAt, editableRows.length)
      : Math.min(activeRowIndex + 1, editableRows.length);

    const newRow = Array(columnCount).fill("");
    setEditableRows(prev => {
      const next = [...prev];
      next.splice(insertAt, 0, [...newRow]);
      return next;
    });
    setOriginalRows(prev => {
      const next = [...prev];
      next.splice(insertAt, 0, [...newRow]);
      return next;
    });
    setRowIds(prev => {
      const next = [...prev];
      next.splice(insertAt, 0, "");
      return next;
    });
    setActiveRowIndex(insertAt);
  }

  function removeRowAt(index: number) {
    const removedRowId = String(rowIds[index] ?? "").trim();
    if (canPersist && removedRowId) {
      setDeletedRowIds(prev => (prev.includes(removedRowId) ? prev : [...prev, removedRowId]));
    }

    setEditableRows(prev => prev.filter((_, i) => i !== index));
    setOriginalRows(prev => prev.filter((_, i) => i !== index));
    setRowIds(prev => prev.filter((_, i) => i !== index));
    setActiveRowIndex(prev => {
      if (prev === null) return prev;
      if (prev === index) return null;
      if (prev > index) return prev - 1;
      return prev;
    });
  }

  function jumpToPage() {
    const raw = parseInt(pageInput, 10);
    if (Number.isNaN(raw)) {
      setPageInput(String(currentPage));
      return;
    }
    const target = Math.min(totalPages, Math.max(1, raw));
    setCurrentPage(target);
    setPageInput(String(target));
  }

  async function saveChanges() {
    if (!isEditMode || !canPersist || saveLoading) return;

    const changes: { row_id: string; values: Record<string, string> }[] = [];
    const deletes = Array.from(new Set(deletedRowIds.filter(id => id.trim() !== "")));
    for (let i = 0; i < editableRows.length; i += 1) {
      const rowId = String(rowIds[i] ?? "");

      const current = editableRows[i] ?? [];
      const original = originalRows[i] ?? Array(selectedCols.length).fill("");
      let changed = false;
      const values: Record<string, string> = {};

      selectedCols.forEach((col, colIndex) => {
        const nextVal = String(current[colIndex] ?? "");
        const prevVal = String(original[colIndex] ?? "");
        values[col] = nextVal;
        if (nextVal !== prevVal) changed = true;
      });

      if (rowId) {
        if (changed) {
          changes.push({ row_id: rowId, values });
        }
      } else {
        const hasContent = Object.values(values).some(v => v.trim() !== "");
        if (hasContent) {
          changes.push({ row_id: "", values });
        }
      }
    }

    if (changes.length === 0 && deletes.length === 0) {
      setIsEditMode(false);
      return;
    }

    setSaveLoading(true);
    try {
      const res = await api.saveTableChanges({ source, changes, deletes });
      if (!res.success) {
        throw new Error(res.errors?.join("; ") || "Không thể lưu dữ liệu");
      }

      const refreshed = await api.query({ source, columns: selectedCols, filters, page: currentPage, limit: PAGE_SIZE });
      setPreviewData(refreshed.data);
      setPreviewTotal(refreshed.total);
      setIsEditMode(false);
      setDeletedRowIds([]);
      setActiveRowIndex(null);
    } catch (err: any) {
      alert(`Không thể lưu thay đổi: ${err?.message || "Lỗi không xác định"}`);
    } finally {
      setSaveLoading(false);
    }
  }

  useEffect(() => {
    const rows = pendingTable
      ? pendingTable.rows
      : previewData.map(row => selectedCols.map(k => rowVal(row, k)));
    const normalizedRows = rows.map(row => row.map(cell => String(cell ?? "")));
    const ids = pendingTable
      ? normalizedRows.map(() => "")
      : previewData.map(row => String(row.__row_id ?? row.slug ?? ""));

    setEditableRows(normalizedRows.map(row => [...row]));
    setOriginalRows(normalizedRows.map(row => [...row]));
    setRowIds(ids);
    setDeletedRowIds([]);
    setIsEditMode(false);
    setActiveRowIndex(null);
  }, [pendingTable, previewData, selectedCols]);

  const displayHeaders = pendingTable ? pendingTable.headers : selectedCols.map(k => getLabel(allFields, k));
  const displayRows    = editableRows;
  const canPersist     = !pendingTable;
  const allowRowDelete = true;
  const totalRowsForPaging = pendingTable ? displayRows.length : previewTotal;
  const totalPages = Math.max(1, Math.ceil((totalRowsForPaging || 0) / PAGE_SIZE));
  const pageStart = pendingTable ? (currentPage - 1) * PAGE_SIZE : 0;
  const pageRows = pendingTable ? displayRows.slice(pageStart, pageStart + PAGE_SIZE) : displayRows;
  const shownStart = pageRows.length === 0 ? 0 : ((currentPage - 1) * PAGE_SIZE) + 1;
  const shownEnd = pageRows.length === 0 ? 0 : shownStart + pageRows.length - 1;
  const hasUnsavedChanges = useMemo(() => {
    if (!isEditMode || !canPersist) return false;
    if (deletedRowIds.length > 0) return true;
    for (let i = 0; i < editableRows.length; i += 1) {
      const rowId = String(rowIds[i] ?? "");
      const current = editableRows[i] ?? [];
      const original = originalRows[i] ?? Array(selectedCols.length).fill("");

      if (rowId) {
        for (let j = 0; j < selectedCols.length; j += 1) {
          if (String(current[j] ?? "") !== String(original[j] ?? "")) return true;
        }
      } else {
        for (let j = 0; j < selectedCols.length; j += 1) {
          if (String(current[j] ?? "").trim() !== "") return true;
        }
      }
    }
    return false;
  }, [isEditMode, canPersist, editableRows, originalRows, rowIds, selectedCols, deletedRowIds]);
  const availableCols  = allFields.filter(f => !selectedCols.includes(f.key));

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages);
    }
  }, [currentPage, totalPages]);

  useEffect(() => {
    setPageInput(String(currentPage));
  }, [currentPage]);

  return (
    <div className="px-6 py-6 min-h-screen">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-[20px] font-bold text-text flex items-center gap-2">
            <Table2 size={20} className="text-accent" /> Table Builder
          </h1>
          <p className="text-[12px] text-text2 mt-0.5">Tạo bảng tùy chỉnh · kéo thả cột · xuất Excel ngay</p>
        </div>
        <button onClick={() => {
          setSelectedCols(source === "contacts" ? DEFAULT_CONTACT_COLS : DEFAULT_PROJECT_COLS);
          setFilters({});
          setTitle("LeadsMap Export");
          setPendingTable(null);
          setCurrentPage(1);
        }}
          className="btn btn-ghost gap-1.5 text-xs">
          <RefreshCw size={13} /> Đặt lại
        </button>
      </div>

      {/* Pending AI table */}
      {pendingTable && (
        <div className="card mb-4 border-accent/30 bg-accent/5 flex items-center gap-3 py-3">
          <Sparkles size={16} className="text-accent flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-medium text-text">Bảng từ Chat AI</p>
            <p className="text-[11px] text-text2">{pendingTable.rows.length} dòng · {pendingTable.headers.length} cột</p>
          </div>
          <button onClick={() => setPendingTable(null)} className="btn btn-ghost text-xs py-1 px-2"><X size={12} /> Bỏ qua</button>
          <button onClick={exportExcel} className="btn btn-primary text-xs py-1 px-3"><FileSpreadsheet size={12} /> Tải Excel</button>
        </div>
      )}

      {/* Templates */}
      <div className="mb-5">
        <p className="text-[10px] text-text2 uppercase tracking-widest mb-2">Gợi ý bảng</p>
        <div className="flex gap-2 flex-wrap">
          {TEMPLATES.map(t => (
            <button key={t.id} onClick={() => applyTemplate(t)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-border bg-surface hover:border-accent/50 hover:bg-accent/5 transition-all text-xs text-text">
              {t.emoji} {t.name}
            </button>
          ))}
        </div>
      </div>

      {/* Builder + Preview */}
      <div className="flex gap-4 items-start">

        {/* Builder */}
        <div className="w-[300px] flex-shrink-0 flex flex-col gap-3">

          {/* Source */}
          <div className="card">
            <p className="text-[10px] text-text2 uppercase tracking-widest mb-2">Nguồn dữ liệu</p>
            <div className="flex gap-2">
              {(["projects","contacts"] as const).map(s => (
                <button key={s} onClick={() => {
                  setSource(s);
                  setSelectedCols(s === "contacts" ? DEFAULT_CONTACT_COLS : DEFAULT_PROJECT_COLS);
                  setFilters({});
                  setPendingTable(null);
                  setCurrentPage(1);
                }}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    source === s ? "bg-accent text-white border-accent" : "border-border text-text2 hover:border-accent/50"
                  }`}>
                  {s === "projects" ? "Dự án" : "Liên hệ"}
                </button>
              ))}
            </div>
          </div>

          {/* Available columns */}
          <div className="card">
            <p className="text-[10px] text-text2 uppercase tracking-widest mb-2">Cột có sẵn (click để thêm)</p>
            <div className="flex flex-wrap gap-1.5">
              {availableCols.length === 0
                ? <p className="text-[11px] text-text2">Đã chọn tất cả</p>
                : availableCols.map(f => (
                  <button key={f.key} onClick={() => addCol(f.key)}
                    className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[var(--surface-container-low)] hover:bg-accent/20 hover:text-accent text-[11px] text-text2 transition-colors border border-transparent hover:border-accent/30">
                    <Plus size={10} /> {f.label}
                  </button>
                ))
              }
            </div>
          </div>

          {/* Selected columns */}
          <div className="card">
            <p className="text-[10px] text-text2 uppercase tracking-widest mb-2">Cột đã chọn (kéo để sắp xếp)</p>
            {selectedCols.length === 0
              ? <p className="text-[11px] text-text2">Chưa chọn cột nào</p>
              : (
                <div className="flex flex-col gap-1">
                  {selectedCols.map((col, idx) => (
                    <div key={col} draggable
                      onDragStart={e => handleDragStart(e, idx)}
                      onDragOver={e => handleDragOver(e, idx)}
                      onDrop={e => handleDrop(e, idx)}
                      onDragEnd={handleDragEnd}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-lg bg-[var(--surface-container-low)] border transition-colors cursor-grab active:cursor-grabbing ${
                        dragOver === idx ? "border-accent bg-accent/10" : "border-transparent"
                      } ${dragIndex === idx ? "opacity-40" : ""}`}
                    >
                      <GripVertical size={12} className="text-text2 flex-shrink-0" />
                      <span className="flex-1 text-[12px] text-text">{getLabel(allFields, col)}</span>
                      <button onClick={() => removeCol(col)} className="text-text2 hover:text-red-400 transition-colors">
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )
            }
          </div>

          {/* Filters */}
          <div className="card">
            <p className="text-[10px] text-text2 uppercase tracking-widest mb-2">Bộ lọc</p>
            <div className="flex flex-col gap-2">
              {source === "projects" ? (
                <>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Tỉnh/TP</label>
                    <select className="input text-xs py-1.5 h-8"
                      value={filters.province||""} onChange={e => setFilter("province", e.target.value)}>
                      <option value="">Tất cả</option>
                      {(stats?.provinces||[]).map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Chủ đầu tư</label>
                    <input className="input text-xs py-1.5 h-8" placeholder="Tên CĐT..."
                      value={filters.developer||""} onChange={e => setFilter("developer", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Trạng thái</label>
                    <input className="input text-xs py-1.5 h-8" placeholder="VD: đang xây..."
                      value={filters.status||""} onChange={e => setFilter("status", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Tìm kiếm</label>
                    <input className="input text-xs py-1.5 h-8" placeholder="Từ khóa..."
                      value={filters.search||""} onChange={e => setFilter("search", e.target.value)} />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Công ty</label>
                    <input className="input text-xs py-1.5 h-8" placeholder="Tên công ty..."
                      value={filters.company||""} onChange={e => setFilter("company", e.target.value)} />
                  </div>
                  <div>
                    <label className="text-[10px] text-text2 mb-1 block">Tìm kiếm</label>
                    <input className="input text-xs py-1.5 h-8" placeholder="Tên, role, SĐT..."
                      value={filters.search||""} onChange={e => setFilter("search", e.target.value)} />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Title */}
          <div className="card">
            <label className="text-[10px] text-text2 uppercase tracking-widest mb-2 block">Tên file xuất</label>
            <input className="input text-xs py-1.5 h-8" value={title}
              onChange={e => setTitle(e.target.value)} placeholder="LeadsMap Export" />
          </div>
        </div>

        {/* Preview */}
        <div className="flex-1 min-w-0 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div className="text-[12px] text-text2">
              {previewLoading ? "Đang tải..." : pendingTable
                ? <span><span className="text-text font-medium">{pendingTable.rows.length}</span> dòng · trang <span className="text-text font-medium">{currentPage}/{totalPages}</span> · <span className="text-accent">Từ Chat AI</span></span>
                : <span><span className="text-text font-medium">{previewTotal}</span> tổng · trang <span className="text-text font-medium">{currentPage}/{totalPages}</span> · hiển thị <span className="text-text font-medium">{pageRows.length}</span> dòng · nguồn: {source}</span>
              }
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditMode(prev => !prev)}
                disabled={displayRows.length === 0}
                className="btn btn-ghost text-xs gap-1 disabled:opacity-40"
              >
                {isEditMode ? <X size={13} /> : <Sparkles size={13} />} {isEditMode ? "Thoát sửa" : "Chế độ sửa"}
              </button>
              {isEditMode && (
                <button onClick={addEmptyRow} disabled={displayHeaders.length === 0} className="btn btn-ghost text-xs gap-1 disabled:opacity-40">
                  <Plus size={13} /> Thêm dòng
                </button>
              )}
              {isEditMode && (
                <button onClick={resetEditableRows} disabled={previewLoading} className="btn btn-ghost text-xs gap-1 disabled:opacity-40">
                  <RefreshCw size={13} /> Hoàn tác sửa
                </button>
              )}
              {isEditMode && canPersist && (
                <button
                  onClick={saveChanges}
                  disabled={!hasUnsavedChanges || saveLoading}
                  className="btn btn-primary text-xs gap-1 disabled:opacity-40"
                >
                  <Save size={13} /> {saveLoading ? "Đang lưu..." : "Lưu thay đổi"}
                </button>
              )}
              <button onClick={exportCSV} disabled={displayRows.length === 0} className="btn btn-ghost text-xs gap-1 disabled:opacity-40">
                <Download size={13} /> CSV
              </button>
              <button onClick={exportExcel} disabled={displayRows.length === 0} className="btn btn-primary text-xs gap-1 disabled:opacity-40">
                <FileSpreadsheet size={13} /> Tải Excel
              </button>
            </div>
          </div>

          <div className="card !p-0 overflow-hidden">
            <div className="overflow-auto" style={{ maxHeight: "calc(100vh - 280px)" }}>
              {previewLoading ? (
                <div className="py-16 text-center text-text2 text-sm">Đang tải dữ liệu...</div>
              ) : pageRows.length === 0 ? (
                <div className="py-16 text-center text-text2 text-sm">
                  {selectedCols.length === 0 ? "Chọn cột để xem trước" : "Không có dữ liệu khớp bộ lọc. Bạn có thể thêm dòng thủ công."}
                </div>
              ) : (
                <table className="data-table table-builder-table">
                  <thead>
                    <tr>
                      <th className="w-8 text-center">#</th>
                      {displayHeaders.map((h, i) => <th key={i}>{h}</th>)}
                      {isEditMode && allowRowDelete && <th className="w-10 text-center">Xóa</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((row, i) => {
                      const absoluteIndex = pendingTable ? pageStart + i : i;
                      return (
                      <tr key={absoluteIndex}>
                        <td className="text-text2 text-center text-[11px]">{((currentPage - 1) * PAGE_SIZE) + i + 1}</td>
                        {row.map((cell, j) => (
                          <td key={j} className="max-w-[240px]">
                            {isEditMode ? (
                              <input
                                value={String(cell ?? "")}
                                onFocus={() => setActiveRowIndex(absoluteIndex)}
                                onChange={e => updateCell(absoluteIndex, j, e.target.value)}
                                className="w-full bg-transparent text-[12px] text-text px-1.5 py-1 rounded border border-transparent hover:border-border focus:border-accent/50 focus:bg-[var(--surface-container-low)] outline-none"
                                title={String(cell ?? "")}
                              />
                            ) : (
                              <span className="block w-full text-[12px] text-text px-1.5 py-1 truncate" title={String(cell ?? "")} onClick={() => setActiveRowIndex(absoluteIndex)}>
                                {String(cell ?? "") || "-"}
                              </span>
                            )}
                          </td>
                        ))}
                        {isEditMode && allowRowDelete && (
                          <td className="text-center">
                            <button
                              onClick={() => removeRowAt(absoluteIndex)}
                              className="text-text2 hover:text-red-400 transition-colors"
                              title="Xóa dòng"
                            >
                              <Trash2 size={12} />
                            </button>
                          </td>
                        )}
                      </tr>
                    )})}
                  </tbody>
                </table>
              )}
            </div>
            {totalRowsForPaging > 0 && (
              <div className="px-4 py-2 border-t border-border text-[11px] text-text2 flex items-center justify-between gap-2">
                <span>Hiển thị {shownStart}-{shownEnd}/{totalRowsForPaging} dòng</span>
                <div className="flex items-center gap-1.5">
                  <button
                    className="btn btn-ghost text-xs py-1 px-2"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage(1)}
                  >
                    Đầu
                  </button>
                  <button
                    className="btn btn-ghost text-xs py-1 px-2"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  >
                    Trước
                  </button>
                  <span className="px-2">Trang {currentPage}/{totalPages}</span>
                  <button
                    className="btn btn-ghost text-xs py-1 px-2"
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  >
                    Sau
                  </button>
                  <button
                    className="btn btn-ghost text-xs py-1 px-2"
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage(totalPages)}
                  >
                    Cuối
                  </button>
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min={1}
                      max={totalPages}
                      value={pageInput}
                      onChange={e => setPageInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === "Enter") jumpToPage();
                      }}
                      className="input text-xs h-7 w-20 px-2"
                      placeholder="Trang"
                    />
                    <button
                      className="btn btn-ghost text-xs py-1 px-2"
                      onClick={jumpToPage}
                      disabled={totalPages <= 1}
                    >
                      Đi
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
