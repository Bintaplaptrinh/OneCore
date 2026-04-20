"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import {
  api,
  invalidateGraphCache,
  GraphData,
  Stats,
  GraphFilter,
  Project,
  Contact,
} from "@/lib/api";
import {
  Network, ZoomIn, ZoomOut, RotateCcw, SlidersHorizontal, RefreshCw,
  X, MessageSquare, User, Building2, MapPin, Phone, Mail,
  Tag, ExternalLink, FileText, Search, ArrowLeft, Coins,
} from "lucide-react";

// Load ForceGraph only on client — no SSR.
// IMPORTANT: We wrap it in a forwardRef client component (ForceGraph2DClient)
// because next/dynamic() does not reliably forward refs to the underlying
// react-force-graph-2d forwardRef component in App Router. Without the wrapper
// the zoom/centerAt/zoomToFit methods would be unreachable and the zoom/fit
// buttons would silently do nothing.
const ForceGraph2D = dynamic(
  () => import("@/components/ForceGraph2DClient"),
  { ssr: false }
);

// ── Constants ──────────────────────────────────────────────────────────────────
const NODE_COLORS: Record<string, string> = {
  project: "#6366F1",
  company: "#F59E0B",
  person:  "#10B981",
};
const LINK_WIDTH  = 1.5;
const CHILD_NODE_SCALE = 0.22;
const CHILD_NODE_MIN_SIZE = 2.2;
const DIM_OPACITY = 0.14;
const DIM_LINK_COLOR = "rgba(110,110,110,0.08)";

const DEFAULT_FILTER: GraphFilter = {
  province: "", developer: "", types: ["project", "company"],
};

const NODE_TYPES = [
  { type: "project", label: "Dự án"        },
  { type: "company", label: "Công ty / CĐT" },
  { type: "person",  label: "Liên hệ"       },
];

type GraphTheme = {
  canvasBg: string;
  panelBg: string;
  cardBg: string;
  cardBgElevated: string;
  tooltipBg: string;
  cardBorder: string;
  panelBorder: string;
  blockBg: string;
  blockBgAlt: string;
  blockBorder: string;
  controlBg: string;
  controlBgActive: string;
  controlBorder: string;
  controlIcon: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  linkColor: string;
  blurValue: string;
  divider: string;
};

const LIGHT_THEME: GraphTheme = {
  canvasBg: "#f3f7fb",
  panelBg: "rgba(243,247,251,0.88)",
  cardBg: "#ffffff",
  cardBgElevated: "#ffffff",
  tooltipBg: "rgba(255,255,255,0.96)",
  cardBorder: "1px solid rgba(0,0,0,0.08)",
  panelBorder: "1px solid rgba(0,88,186,0.14)",
  blockBg: "rgba(240,244,249,0.95)",
  blockBgAlt: "rgba(230,236,242,0.95)",
  blockBorder: "1px solid rgba(0,0,0,0.06)",
  controlBg: "rgba(255,255,255,0.92)",
  controlBgActive: "rgba(99,102,241,0.14)",
  controlBorder: "1px solid rgba(0,0,0,0.08)",
  controlIcon: "#4e5f73",
  textPrimary: "#0f172a",
  textSecondary: "#334155",
  textMuted: "#64748b",
  linkColor: "rgba(75,94,121,0.66)",
  blurValue: "blur(10px)",
  divider: "rgba(0,0,0,0.08)",
};

const DARK_THEME: GraphTheme = {
  canvasBg: "#0a0f19",
  panelBg: "rgba(17,27,45,0.86)",
  cardBg: "#1a2236",
  cardBgElevated: "#22304a",
  tooltipBg: "rgba(26,34,54,0.98)",
  cardBorder: "1px solid rgba(255,255,255,0.1)",
  panelBorder: "1px solid rgba(143,161,187,0.28)",
  blockBg: "rgba(40,52,74,0.9)",
  blockBgAlt: "rgba(48,62,86,0.9)",
  blockBorder: "1px solid rgba(255,255,255,0.06)",
  controlBg: "rgba(26,34,54,0.9)",
  controlBgActive: "rgba(106,164,255,0.22)",
  controlBorder: "1px solid rgba(143,161,187,0.28)",
  controlIcon: "#c3cee2",
  textPrimary: "#f1f5f9",
  textSecondary: "#cbd5e1",
  textMuted: "#94a3b8",
  linkColor: "rgba(110,138,178,0.64)",
  blurValue: "blur(12px)",
  divider: "rgba(255,255,255,0.08)",
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function nodeVisible(node: any, f: GraphFilter): boolean {
  const types = f.types ?? [];
  if (types.length > 0 && !types.includes(node.type)) return false;
  if (f.province && node.type === "project" && !String(node.province ?? "").includes(f.province)) return false;
  if (f.developer && node.type === "company" &&
    !String(node.name ?? "").toLowerCase().includes(f.developer.toLowerCase())) return false;
  return true;
}

/** Remove Vietnamese diacritics and lower-case for loose search. */
function normalizeVN(s: string): string {
  return (s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/gi, "d")
    .toLowerCase()
    .trim();
}

function hexToRgba(hex: string, alpha: number): string {
  // supports "#RRGGBB"
  const h = hex.replace("#", "");
  if (h.length !== 6) return hex;
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Material-style Detail Card ────────────────────────────────────────────────
function DetailPanel({
  node, detail, onClose, theme,
}: { node: any; detail: Project | Contact | null; onClose: () => void; theme: GraphTheme }) {
  if (!node) return null;

  const isProject = node.type === "project";
  const isContact = node.type === "person";
  const isCompany = node.type === "company";
  const p = isProject && detail ? (detail as Project) : null;
  const c = isContact ? ((detail as Contact) ?? node) : null;

  const typeLabel = isProject ? "Dự án" : isContact ? "Liên hệ" : "Công ty";
  const typeColor = NODE_COLORS[node.type] ?? "#6366F1";

  const sectionStyle: React.CSSProperties = {
    borderRadius: 10,
    background: theme.blockBg,
    border: theme.blockBorder,
    padding: "10px 12px",
  };
  const sectionAltStyle: React.CSSProperties = {
    ...sectionStyle,
    background: theme.blockBgAlt,
  };

  return (
    <div
      className="absolute top-0 right-0 h-full w-[320px] z-40 flex flex-col overflow-hidden"
      style={{
        background: theme.cardBg,
        borderLeft: `1px solid ${theme.divider}`,
        boxShadow: "-4px 0 24px rgba(0,0,0,0.12)",
      }}
    >
      {/* ── Header ── */}
      <div
        className="flex items-center justify-between px-4 py-3 flex-shrink-0"
        style={{ borderBottom: `1px solid ${theme.divider}` }}
      >
        <span
          className="text-[10px] font-semibold px-2.5 py-1 rounded-full uppercase tracking-widest"
          style={{ background: `${typeColor}20`, color: typeColor }}
        >
          {typeLabel}
        </span>
        <button
          onClick={onClose}
          title="Đóng"
          className="w-7 h-7 rounded-full flex items-center justify-center transition-colors"
          style={{ color: theme.textSecondary, background: "transparent" }}
          onMouseEnter={(e) => (e.currentTarget.style.background = theme.blockBg)}
          onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
        >
          <X size={14} />
        </button>
      </div>

      {/* ── Title ── */}
      <div
        className="px-4 py-3 flex-shrink-0"
        style={{ borderBottom: `1px solid ${theme.divider}` }}
      >
        <p
          className="text-[14px] font-semibold leading-snug"
          style={{ color: theme.textPrimary }}
        >
          {node.name}
        </p>
        {node.province && (
          <p className="text-[12px] mt-0.5 flex items-center gap-1" style={{ color: theme.textMuted }}>
            <MapPin size={10} /> {node.province}
          </p>
        )}
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {!detail && (isProject || isContact) && (
          <p className="text-xs" style={{ color: theme.textMuted }}>Đang tải...</p>
        )}

        {/* Project */}
        {p && (
          <>
            <div className="space-y-2" style={sectionStyle}>
              {p.status && <Field icon={<Tag size={11}/>} label="Trạng thái" value={p.status} theme={theme} />}
              {Array.isArray(p.type_tags) && p.type_tags.length > 0 &&
                <Field icon={<Building2 size={11}/>} label="Loại hình" value={p.type_tags.join(", ")} theme={theme} />}
              {p.province && <Field icon={<MapPin size={11}/>} label="Tỉnh" value={p.province} theme={theme} />}
            </div>

            {p.value_str && (
              <div
                className="flex items-center justify-between px-3 py-2.5 rounded-xl"
                style={{
                  background: "rgba(245,158,11,0.14)",
                  border: "1px solid rgba(245,158,11,0.32)",
                }}
              >
                <span className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest" style={{ color: "#b45309" }}>
                  <Coins size={11}/> Giá trị
                </span>
                <span className="text-sm font-bold" style={{ color: "#d97706" }}>{p.value_str}</span>
              </div>
            )}

            {Array.isArray(p.developer) && p.developer.length > 0 && (
              <div style={sectionStyle}>
                <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: theme.textMuted }}>Chủ đầu tư</p>
                <p className="text-xs font-medium" style={{ color: theme.textPrimary }}>{p.developer.join(", ")}</p>
              </div>
            )}

            {(p.groundbreaking || p.handover) && (
              <div className="grid grid-cols-2 gap-2" style={sectionStyle}>
                {p.groundbreaking && (
                  <div>
                    <p className="text-[10px] uppercase tracking-widest mb-0.5" style={{ color: theme.textMuted }}>Khởi công</p>
                    <p className="text-xs" style={{ color: theme.textPrimary }}>{p.groundbreaking}</p>
                  </div>
                )}
                {p.handover && (
                  <div>
                    <p className="text-[10px] uppercase tracking-widest mb-0.5" style={{ color: theme.textMuted }}>Bàn giao</p>
                    <p className="text-xs" style={{ color: theme.textPrimary }}>{p.handover}</p>
                  </div>
                )}
              </div>
            )}

            {p.notes && (
              <div style={sectionAltStyle}>
                <p className="text-[10px] uppercase tracking-widest mb-1" style={{ color: theme.textMuted }}>Ghi chú</p>
                <p className="text-[11px] leading-relaxed line-clamp-5" style={{ color: theme.textSecondary }}>{p.notes}</p>
              </div>
            )}

            <div className="pt-2" style={{ borderTop: `1px solid ${theme.divider}` }}>
              <button
                disabled
                title="Coming soon"
                className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium opacity-70 cursor-not-allowed"
                style={{
                  background: "rgba(99,102,241,0.08)",
                  color: "#6366F1",
                  border: "1px solid rgba(99,102,241,0.24)",
                }}
              >
                <FileText size={12} /> Coming soon
              </button>
            </div>
          </>
        )}

        {/* Contact */}
        {isContact && c && (
          <div className="space-y-2" style={sectionStyle}>
            {(c.company ?? node.company) && <Field icon={<Building2 size={11}/>} label="Công ty" value={c.company ?? node.company} theme={theme} />}
            {(c.role ?? node.role)       && <Field icon={<User size={11}/>}      label="Vai trò" value={c.role ?? node.role} theme={theme} />}
            {(c.phone ?? node.phone)     && <Field icon={<Phone size={11}/>}     label="SĐT"     value={c.phone ?? node.phone} accent theme={theme} />}
            {(c.email ?? node.email)     && <Field icon={<Mail size={11}/>}      label="Email"   value={c.email ?? node.email} theme={theme} />}
          </div>
        )}

        {/* Company */}
        {isCompany && (
          <div
            className="rounded-xl px-3 py-2.5"
            style={{
              background: "rgba(245,158,11,0.1)",
              border: "1px solid rgba(245,158,11,0.28)",
              color: theme.textPrimary,
            }}
          >
            <p className="text-xs" style={{ color: theme.textSecondary }}>
              Chủ đầu tư / Công ty trong Knowledge Graph.
            </p>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      {isContact && (
        <div className="px-4 py-3 flex-shrink-0" style={{ borderTop: `1px solid ${theme.divider}` }}>
          <Link
            href="/contacts"
            className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all"
            style={{
              background: "rgba(16,185,129,0.12)",
              color: "#10B981",
              border: "1px solid rgba(16,185,129,0.32)",
            }}
          >
            <ExternalLink size={11} /> Xem tất cả liên hệ
          </Link>
        </div>
      )}
    </div>
  );
}

function Field({
  icon, label, value, accent, theme,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: boolean;
  theme: GraphTheme;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span
        className="flex items-center gap-1 text-[10px] uppercase tracking-widest flex-shrink-0 mt-0.5"
        style={{ color: theme.textMuted }}
      >
        {icon}{label}
      </span>
      <span
        className={`text-xs text-right leading-snug ${accent ? "font-semibold" : ""}`}
        style={{ color: accent ? "#10B981" : theme.textPrimary }}
      >
        {value}
      </span>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function GraphPage() {
  const router        = useRouter();
  const searchParams  = useSearchParams();

  const [rawData, setRawData]         = useState<GraphData | null>(null);
  const [stats, setStats]             = useState<Stats | null>(null);
  const [loading, setLoading]         = useState(true);
  const [reloading, setReloading]     = useState(false);
  const [error, setError]             = useState<string | null>(null);

  const [filter, setFilter]           = useState<GraphFilter>(DEFAULT_FILTER);
  const [fromChat, setFromChat]       = useState(false);
  const [panelOpen, setPanelOpen]     = useState(true);

  const [hovered, setHovered]         = useState<any>(null);
  const [selected, setSelected]       = useState<any>(null);
  const [nodeDetail, setNodeDetail]   = useState<Project | Contact | null>(null);
  const [isDark, setIsDark]           = useState(true);

  // Search state
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const focusedViaDeepLinkRef         = useRef(false);
  const focusedViaNodesLinkRef        = useRef(false);

  // Pinned nodes from `?nodes=slug1,slug2,slug3` deep link (group from chat).
  // These are highlighted like matched search results but camera fits to
  // the bounding box rather than opening a card.
  const [pinnedIds, setPinnedIds] = useState<Set<string>>(new Set());

  const fgRef = useRef<any>(null);

  const bindGraphInstance = useCallback((instance: any | null) => {
    fgRef.current = instance;
  }, []);

  // Sync dark/light
  useEffect(() => {
    const root = document.documentElement;
    const syncTheme = () => setIsDark(root.classList.contains("dark"));
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(root, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  const graphTheme = useMemo(() => (isDark ? DARK_THEME : LIGHT_THEME), [isDark]);

  // Debounce searchInput -> searchQuery
  useEffect(() => {
    const t = setTimeout(() => setSearchQuery(searchInput.trim()), 180);
    return () => clearTimeout(t);
  }, [searchInput]);

  // ── Load data ────────────────────────────────────────────────────────────────
  const loadData = useCallback(async (opts?: { force?: boolean }) => {
    if (opts?.force) {
      invalidateGraphCache();
      setReloading(true);
    }
    try {
      const [g, s] = await Promise.all([api.graph(), api.stats()]);
      setRawData(g);
      setStats(s);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
      setReloading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Listen for external data-change events (e.g. FloatingChat fires after a mutation)
  useEffect(() => {
    const handler = () => loadData({ force: true });
    window.addEventListener("leadsmap_data_changed", handler);
    return () => window.removeEventListener("leadsmap_data_changed", handler);
  }, [loadData]);

  // ── Chat → Graph filter sync (via localStorage) ─────────────────────────────
  useEffect(() => {
    try {
      const stored = localStorage.getItem("leadsmap_graph_filter");
      if (stored) {
        const f: GraphFilter = JSON.parse(stored);
        if (f.province || f.developer || f.types?.length) {
          setFilter({ ...DEFAULT_FILTER, ...f, types: f.types ?? DEFAULT_FILTER.types });
          setFromChat(true);
        }
        localStorage.removeItem("leadsmap_graph_filter");
      }
    } catch {}
  }, []);

  // Query-param deep-link: ?node=slug | ?nodes=slug1,slug2 | ?q=text&from=chat
  useEffect(() => {
    if (!searchParams) return;
    const q = searchParams.get("q");
    if (q && !searchInput) setSearchInput(q);
    if (searchParams.get("from") === "chat") setFromChat(true);

    // Multi-node group link from chat
    const nodesParam = searchParams.get("nodes");
    if (nodesParam) {
      const slugs = nodesParam
        .split(",")
        .map((s) => decodeURIComponent(s.trim()))
        .filter(Boolean);
      setPinnedIds(slugs.length > 0 ? new Set(slugs) : new Set());
      return;
    }

    // Single-node deep link from chat should also activate highlight/dim mode
    // (same visual emphasis as search focus), not only camera center.
    const nodeParam = searchParams.get("node");
    if (nodeParam) {
      setPinnedIds(new Set([nodeParam]));
      return;
    }

    // No node hints in URL -> clear stale pinned highlight from previous deep links.
    setPinnedIds(new Set());
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Fetch node detail ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!selected) { setNodeDetail(null); return; }
    setNodeDetail(null);
    if (selected.type === "project") {
      api.project(selected.id).then(setNodeDetail).catch(() => setNodeDetail(null));
    } else if (selected.type === "person") {
      api.contact(selected.id).then(setNodeDetail).catch(() => setNodeDetail(null));
    }
  }, [selected]);

  // ── Filtered graph data ───────────────────────────────────────────────────
  const graphData = useMemo(() => {
    if (!rawData) return { nodes: [] as any[], links: [] as any[] };
    const nodes = rawData.nodes.filter((n: any) => nodeVisible(n, filter));
    const ids   = new Set(nodes.map((n: any) => n.id));
    const links = rawData.links.filter((l: any) => {
      const src = typeof l.source === "object" ? l.source.id : l.source;
      const tgt = typeof l.target === "object" ? l.target.id : l.target;
      return ids.has(src) && ids.has(tgt);
    });
    return { nodes, links };
  }, [rawData, filter]);

  // ── Search matching ───────────────────────────────────────────────────────
  const normalizedQuery = useMemo(() => normalizeVN(searchQuery), [searchQuery]);
  const searchActive = normalizedQuery.length > 0;
  const pinnedActive = pinnedIds.size > 0;

  const searchMatchedIds = useMemo(() => {
    if (!searchActive) return new Set<string>();
    const set = new Set<string>();
    for (const n of graphData.nodes) {
      const hay = normalizeVN((n.name ?? "") + " " + (n.province ?? ""));
      if (hay.includes(normalizedQuery)) set.add(n.id);
    }
    return set;
  }, [graphData.nodes, normalizedQuery, searchActive]);

  // Union of search hits + pinned (from ?nodes=...) — drives the highlight
  // effect (pulsing ring + dimming others).
  const matchedIds = useMemo(() => {
    if (!searchActive && !pinnedActive) return new Set<string>();
    const set = new Set<string>(searchMatchedIds);
    if (pinnedActive) pinnedIds.forEach((id) => set.add(id));
    return set;
  }, [searchMatchedIds, pinnedIds, searchActive, pinnedActive]);

  // Truthy whenever anything is highlighted (used for dimming decisions)
  const highlightActive = searchActive || pinnedActive;

  // Auto-focus on a deep-link node once data is ready
  useEffect(() => {
    if (!searchParams || !rawData) return;
    if (focusedViaDeepLinkRef.current) return;
    const nodeParam = searchParams.get("node");
    if (!nodeParam) return;

    const target = rawData.nodes.find((n: any) => n.id === nodeParam);
    if (!target) return;

    focusedViaDeepLinkRef.current = true;
    // wait for graph layout to settle
    const focus = () => {
      const node: any = target;
      if (node && typeof node.x === "number" && typeof node.y === "number") {
        fgRef.current?.centerAt?.(node.x, node.y, 700);
        fgRef.current?.zoom?.(4, 700);
        setSelected(target);
      } else {
        setTimeout(focus, 200);
      }
    };
    setTimeout(focus, 400);
  }, [rawData, searchParams]);

  // Auto-focus if exactly ONE search match
  useEffect(() => {
    if (!searchActive || searchMatchedIds.size !== 1 || !fgRef.current) return;
    const id = [...searchMatchedIds][0];
    const node: any = graphData.nodes.find((n: any) => n.id === id);
    if (!node) return;
    const focus = () => {
      if (typeof node.x === "number" && typeof node.y === "number") {
        fgRef.current?.centerAt?.(node.x, node.y, 500);
        fgRef.current?.zoom?.(3.5, 500);
        setSelected(node);
      } else {
        setTimeout(focus, 200);
      }
    };
    focus();
  }, [searchMatchedIds, searchActive, graphData.nodes]);

  // Auto-focus on `?nodes=slug1,slug2` (group deep link from chat)
  // - exactly 1 pinned id  -> behave like the single-node deep link (center + open card)
  // - 2+ pinned ids       -> fit bounding box, highlight, but DON'T open a card
  useEffect(() => {
    if (!pinnedActive || !rawData || focusedViaNodesLinkRef.current) return;
    // Wait until force layout has produced coordinates for at least one pinned node.
    const nodesWithCoords = graphData.nodes.filter(
      (n: any) => pinnedIds.has(n.id) && typeof n.x === "number" && typeof n.y === "number"
    );
    if (nodesWithCoords.length === 0) return;

    focusedViaNodesLinkRef.current = true;

    const applyFocus = () => {
      const fg = fgRef.current;
      if (!fg) { setTimeout(applyFocus, 200); return; }
      if (pinnedIds.size === 1) {
        // Mirror single-node behaviour: center + zoom + open detail card
        const node: any = nodesWithCoords[0];
        fg.centerAt?.(node.x, node.y, 700);
        fg.zoom?.(4, 700);
        setSelected(node);
      } else {
        // Group: fit bounding box of pinned nodes, no card
        try {
          fg.zoomToFit?.(700, 80, (n: any) => pinnedIds.has(n.id));
        } catch {
          // Fallback: center on the centroid
          const cx = nodesWithCoords.reduce((s: number, n: any) => s + n.x, 0) / nodesWithCoords.length;
          const cy = nodesWithCoords.reduce((s: number, n: any) => s + n.y, 0) / nodesWithCoords.length;
          fg.centerAt?.(cx, cy, 700);
          fg.zoom?.(2.2, 700);
        }
      }
      try { fg.refresh?.(); } catch {}
    };
    setTimeout(applyFocus, 400);
  }, [pinnedActive, pinnedIds, rawData, graphData.nodes]);

  // Trigger canvas repaint so ring pulses animate
  useEffect(() => {
    if (!highlightActive && !selected) return;
    const interval = setInterval(() => {
      try { fgRef.current?.refresh?.(); } catch {}
    }, 80);
    return () => clearInterval(interval);
  }, [highlightActive, selected]);

  // Stable callbacks for the graph
  const getNodeColor = useCallback((n: any) => {
    const base = NODE_COLORS[n.type] ?? "#6366F1";
    if (!highlightActive) return base;
    if (matchedIds.has(n.id)) return base;
    return hexToRgba(base, DIM_OPACITY);
  }, [highlightActive, matchedIds]);

  const getNodeVal = useCallback((n: any) => {
    const baseSize = (n.size as number) || 4;
    return Math.max(baseSize * CHILD_NODE_SCALE, CHILD_NODE_MIN_SIZE);
  }, []);

  const getLinkColor = useCallback((l: any) => {
    if (!highlightActive) return graphTheme.linkColor;
    const src = typeof l.source === "object" ? l.source.id : l.source;
    const tgt = typeof l.target === "object" ? l.target.id : l.target;
    if (matchedIds.has(src) || matchedIds.has(tgt)) return graphTheme.linkColor;
    return DIM_LINK_COLOR;
  }, [graphTheme.linkColor, highlightActive, matchedIds]);

  const getLinkWidth = useCallback(() => LINK_WIDTH, []);

  // Draw a subtle pulsing ring on matched / selected / pinned nodes
  const nodeCanvasObjectMode = useCallback(
    (n: any) => {
      if (selected && selected.id === n.id) return "after";
      if (highlightActive && matchedIds.has(n.id)) return "after";
      return undefined as any;
    },
    [highlightActive, matchedIds, selected]
  );

  const nodeCanvasObject = useCallback(
    (n: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const color = NODE_COLORS[n.type] ?? "#6366F1";
      const val   = getNodeVal(n);
      const baseR = Math.sqrt(Math.max(0, val)) * 4;
      const t = performance.now() / 500;
      const pulse = 0.5 + 0.5 * Math.sin(t);
      const ringR = baseR + 2.5 + pulse * 3;
      ctx.beginPath();
      ctx.arc(n.x, n.y, ringR, 0, 2 * Math.PI);
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.35 + 0.35 * pulse;
      ctx.lineWidth = Math.max(1.2 / globalScale, 0.6);
      ctx.stroke();
      ctx.globalAlpha = 1;
    },
    [getNodeVal]
  );

  const totalVisible = graphData.nodes.length;
  const totalLinks   = graphData.links.length;
  const totalRaw     = rawData?.nodes.filter((n: any) => !n.hidden).length ?? 0;
  const hasFilter    = !!(filter.province || filter.developer ||
    !(filter.types.includes("project") && filter.types.includes("company") && filter.types.length === 2));

  function clearFilter() { setFilter(DEFAULT_FILTER); setFromChat(false); }

  function toggleType(type: string) {
    setFilter(f => ({
      ...f,
      types: f.types.includes(type) ? f.types.filter(t => t !== type) : [...f.types, type],
    }));
  }

  function handleNodeClick(node: any) {
    setSelected((prev: any) => prev?.id === node.id ? null : node);
  }

  function handleRefresh() {
    loadData({ force: true });
  }

  function nudgeRefresh() {
    // Some react-force-graph versions don't repaint until the next tick
    // after a zoom/centerAt call; a manual refresh nudges the canvas along.
    try { fgRef.current?.refresh?.(); } catch {}
  }

  function handleZoomIn() {
    const fg = fgRef.current;
    if (!fg || typeof fg.zoom !== "function") return;
    const z = fg.zoom();
    const next = typeof z === "number" && isFinite(z) ? z * 1.35 : 2;
    fg.zoom(next, 200);
    setTimeout(nudgeRefresh, 220);
  }

  function handleZoomOut() {
    const fg = fgRef.current;
    if (!fg || typeof fg.zoom !== "function") return;
    const z = fg.zoom();
    const next = typeof z === "number" && isFinite(z) ? z / 1.35 : 0.5;
    fg.zoom(next, 200);
    setTimeout(nudgeRefresh, 220);
  }

  function handleFit() {
    const fg = fgRef.current;
    if (!fg || typeof fg.zoomToFit !== "function") return;
    fg.zoomToFit(500, 40);
    setTimeout(nudgeRefresh, 520);
  }

  function handleBackToChat() {
    router.push("/chat");
  }

  // ── Loading / error ────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: graphTheme.canvasBg }}>
        <div className="text-center">
          <Network size={36} className="text-indigo-400 mx-auto mb-3" />
          <p className="text-sm" style={{ color: graphTheme.textMuted }}>Đang tải Knowledge Graph 2D...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen" style={{ background: graphTheme.canvasBg }}>
        <div className="text-center max-w-sm">
          <Network size={36} className="text-red-400 mx-auto mb-3" />
          <p className="text-red-400 text-sm mb-2">Không thể tải dữ liệu graph</p>
          <p className="text-xs" style={{ color: graphTheme.textMuted }}>{error}</p>
          <button
            className="mt-4 px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs"
            onClick={handleRefresh}
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-screen overflow-hidden" style={{ background: graphTheme.canvasBg }}>

      {/* ── Top bar ──────────────────────────────────────────────────────────── */}
      <div className="absolute top-4 left-4 z-30 flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setPanelOpen(o => !o)}
          title="Bộ lọc"
          className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors"
          style={{
            background: panelOpen ? graphTheme.controlBgActive : graphTheme.controlBg,
            border: graphTheme.controlBorder,
          }}
        >
          <SlidersHorizontal size={15} style={{ color: panelOpen ? "#6366F1" : graphTheme.controlIcon }} />
        </button>

        <div
          className="flex items-center gap-2 px-3 py-2 rounded-xl"
          style={{ background: graphTheme.panelBg, border: graphTheme.panelBorder, backdropFilter: graphTheme.blurValue }}
        >
          <Network size={14} className="text-indigo-400" />
          <span className="text-sm font-semibold" style={{ color: graphTheme.textPrimary }}>Knowledge Graph 2D</span>
        </div>

        {/* Search box — live match */}
        <div
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl w-[260px]"
          style={{ background: graphTheme.panelBg, border: graphTheme.panelBorder, backdropFilter: graphTheme.blurValue }}
        >
          <Search size={13} style={{ color: graphTheme.textMuted }} />
          <input
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-[color:var(--text2)]"
            style={{ color: graphTheme.textPrimary }}
            placeholder="Tìm dự án, CĐT, liên hệ..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searchInput && (
            <button
              onClick={() => setSearchInput("")}
              title="Xóa"
              className="p-0.5 rounded hover:opacity-80"
              style={{ color: graphTheme.textMuted }}
            >
              <X size={12} />
            </button>
          )}
        </div>

        {/* Multi-match badge (search) */}
        {searchActive && matchedIds.size > 1 && (
          <div
            className="px-3 py-1.5 rounded-xl text-xs font-medium"
            style={{
              background: "rgba(99,102,241,0.14)",
              color: "#6366F1",
              border: "1px solid rgba(99,102,241,0.32)",
            }}
          >
            {matchedIds.size} nodes matched
          </div>
        )}
        {searchActive && matchedIds.size === 0 && (
          <div
            className="px-3 py-1.5 rounded-xl text-xs"
            style={{
              background: "rgba(239,68,68,0.1)",
              color: "#ef4444",
              border: "1px solid rgba(239,68,68,0.28)",
            }}
          >
            Không tìm thấy
          </div>
        )}

        {/* Pinned-from-chat badge (group link) */}
        {!searchActive && pinnedActive && (
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium"
            style={{
              background: "rgba(99,102,241,0.14)",
              color: "#6366F1",
              border: "1px solid rgba(99,102,241,0.32)",
            }}
          >
            <Network size={11} />
            <span>
              {pinnedIds.size === 1
                ? "1 node từ chat"
                : `${pinnedIds.size} nodes từ chat`}
            </span>
            <button
              onClick={() => {
                setPinnedIds(new Set());
                focusedViaNodesLinkRef.current = false;
              }}
              title="Bỏ chọn"
              className="opacity-70 hover:opacity-100"
            >
              <X size={11} />
            </button>
          </div>
        )}

        {rawData && !searchActive && !pinnedActive && (
          <div
            className="px-3 py-1.5 rounded-xl text-xs"
            style={{
              color: graphTheme.textSecondary,
              background: graphTheme.panelBg,
              border: graphTheme.panelBorder,
              backdropFilter: graphTheme.blurValue,
            }}
          >
            {hasFilter
              ? <><span className="text-indigo-400 font-medium">{totalVisible}</span> / {totalRaw} nodes</>
              : <>{totalVisible} nodes · {totalLinks} links</>}
          </div>
        )}

        {fromChat && (
          <button
            onClick={handleBackToChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs transition-colors"
            style={{
              background: "rgba(99,102,241,0.12)",
              color: "#6366F1",
              border: "1px solid rgba(99,102,241,0.32)",
            }}
            title="Về chat"
          >
            <ArrowLeft size={11} /> Về chat
          </button>
        )}
      </div>

      {/* ── Legend (top-right) ───────────────────────────────────────────────── */}
      <div
        className="absolute top-4 z-30 rounded-xl px-4 py-3"
        style={{
          right: selected ? "336px" : "16px",
          background: graphTheme.panelBg,
          border: graphTheme.panelBorder,
          backdropFilter: graphTheme.blurValue,
        }}
      >
        <p className="text-[10px] uppercase tracking-widest mb-2" style={{ color: graphTheme.textMuted }}>Loại node</p>
        {NODE_TYPES.map(({ type, label }) => (
          <div key={type} className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: NODE_COLORS[type] }} />
            <span className="text-xs" style={{ color: graphTheme.textSecondary }}>{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-2 mt-2 pt-2" style={{ borderTop: `1px solid ${graphTheme.divider}` }}>
          <div className="h-0.5 w-5 rounded" style={{ background: graphTheme.linkColor }} />
          <span className="text-[10px]" style={{ color: graphTheme.textMuted }}>Liên kết</span>
        </div>
      </div>

      {/* ── Zoom / Refresh controls ──────────────────────────────────────────── */}
      <div
        className="absolute bottom-6 z-30 flex flex-col gap-2"
        style={{ right: selected ? "336px" : "16px" }}
      >
        {[
          { icon: ZoomIn,    title: "Phóng to",  fn: handleZoomIn,  spin: false },
          { icon: ZoomOut,   title: "Thu nhỏ",   fn: handleZoomOut, spin: false },
          // { icon: RotateCcw, title: "Khớp màn",  fn: handleFit,     spin: false },
          {
            icon: RefreshCw,
            title: "Tải lại dữ liệu",
            fn: handleRefresh,
            spin: reloading,
          },
        ].map(({ icon: Icon, title, fn, spin }) => (
          <button
            key={title}
            title={title}
            onClick={fn}
            className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors"
            style={{ background: graphTheme.controlBg, border: graphTheme.controlBorder }}
          >
            <Icon
              size={14}
              style={{ color: graphTheme.controlIcon }}
              className={spin ? "animate-spin" : ""}
            />
          </button>
        ))}
      </div>

      {/* ── Filter panel ─────────────────────────────────────────────────────── */}
      {panelOpen && (
        <div
          className="absolute top-16 left-4 z-30 w-[220px] rounded-xl p-4 flex flex-col gap-3"
          style={{ background: graphTheme.panelBg, border: graphTheme.panelBorder, backdropFilter: graphTheme.blurValue }}
        >
          {fromChat && (
            <div
              className="flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px]"
              style={{
                background: "rgba(99,102,241,0.1)",
                color: "#6366F1",
                border: "1px solid rgba(99,102,241,0.28)",
              }}
            >
              <MessageSquare size={10} /> Lọc từ Chat AI
            </div>
          )}

          <div>
            <p className="text-[10px] uppercase tracking-widest mb-1.5" style={{ color: graphTheme.textMuted }}>Tỉnh / Thành</p>
            <select
              className="input text-xs"
              value={filter.province}
              onChange={e => { setFilter(f => ({ ...f, province: e.target.value })); setFromChat(false); }}
            >
              <option value="">Tất cả tỉnh</option>
              {(stats?.provinces ?? []).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>



          <div>
            <p className="text-[10px] uppercase tracking-widest mb-1.5" style={{ color: graphTheme.textMuted }}>Loại node</p>
            {NODE_TYPES.map(({ type, label }) => (
              <label key={type} className="flex items-center gap-2 cursor-pointer py-0.5">
                <input
                  type="checkbox"
                  className="w-3 h-3"
                  checked={filter.types.includes(type)}
                  onChange={() => toggleType(type)}
                />
                <div className="w-2 h-2 rounded-full" style={{ background: NODE_COLORS[type] }} />
                <span className="text-xs" style={{ color: graphTheme.textSecondary }}>{label}</span>
              </label>
            ))}
          </div>

          <div className="flex flex-col gap-1.5 pt-1" style={{ borderTop: `1px solid ${graphTheme.divider}` }}>
            {hasFilter && (
              <button
                onClick={clearFilter}
                className="flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs transition-colors"
                style={{
                  color: graphTheme.textSecondary,
                  background: graphTheme.controlBg,
                  border: graphTheme.controlBorder,
                }}
              >
                <X size={11} /> Xóa bộ lọc
              </button>
            )}
            <Link
              href="/chat"
              className="flex items-center justify-center gap-1 py-1.5 rounded-lg text-xs transition-colors"
              style={{
                background: "rgba(99,102,241,0.1)",
                color: "#6366F1",
                border: "1px solid rgba(99,102,241,0.28)",
              }}
            >
              <MessageSquare size={11} /> Chat để lọc
            </Link>
          </div>
        </div>
      )}

      {/* ── Hover tooltip (even on dimmed nodes) ─────────────────────────────── */}
      {hovered && !selected && (
        <div
          className="absolute bottom-6 left-4 z-30 rounded-xl py-3 px-4 max-w-[260px]"
          style={{
            background: graphTheme.tooltipBg,
            border: graphTheme.cardBorder,
            backdropFilter: graphTheme.blurValue,
            boxShadow: "0 6px 24px rgba(0,0,0,0.2)",
          }}
        >
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full" style={{ background: NODE_COLORS[hovered.type] ?? "#6366F1" }} />
            <span className="text-[10px] uppercase tracking-widest" style={{ color: graphTheme.textMuted }}>{hovered.type}</span>
          </div>
          <p className="text-sm font-semibold" style={{ color: graphTheme.textPrimary }}>{hovered.name}</p>
          {hovered.province  && <p className="text-xs mt-0.5" style={{ color: graphTheme.textSecondary }}>{hovered.province}</p>}
          {hovered.value_str && <p className="text-xs text-yellow-500 mt-0.5">{hovered.value_str}</p>}
          {hovered.role      && <p className="text-xs mt-0.5" style={{ color: graphTheme.textSecondary }}>{hovered.role}</p>}
          <p className="text-[10px] mt-1.5" style={{ color: graphTheme.textMuted }}>Click để xem chi tiết</p>
        </div>
      )}

      <ForceGraph2D
        ref={fgRef}
        onEngineRef={bindGraphInstance}
        graphData={graphData}
        backgroundColor={graphTheme.canvasBg}
        nodeColor={getNodeColor}
        nodeVal={getNodeVal}
        nodeLabel={(n: any) => n.name}
        linkColor={getLinkColor}
        linkWidth={getLinkWidth}
        nodeCanvasObjectMode={nodeCanvasObjectMode}
        nodeCanvasObject={nodeCanvasObject}
        onNodeHover={(n: any) => setHovered(n)}
        onNodeClick={handleNodeClick}
        cooldownTicks={55}
        warmupTicks={10}
        d3AlphaDecay={0.12}
        d3VelocityDecay={0.45}
      />

      <DetailPanel
        node={selected}
        detail={nodeDetail}
        theme={graphTheme}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
