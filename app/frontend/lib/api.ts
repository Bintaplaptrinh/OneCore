const API = process.env.NEXT_PUBLIC_API_URL || "";

type CacheEntry<T> = {
  expiresAt: number;
  data?: T;
  inFlight?: Promise<T>;
};

const requestCache = new Map<string, CacheEntry<any>>();

export interface Project {
  slug: string; name: string; province: string; district: string;
  address: string; developer: string[]; value_billion_vnd: number | null;
  value_str: string; status: string; phase: string; type_tags: string[];
  site_area: string; floors: string; groundbreaking: string; handover: string;
  notes: string;
}
export interface Contact {
  slug: string; name: string; company: string; role: string;
  phone: string; email: string; address: string; image_path: string;
}
export interface Stats {
  total_projects: number; total_contacts: number; total_relationships: number;
  total_value_billion_vnd: number; provinces: string[]; statuses: string[];
}
export interface GraphData {
  nodes: { id: string; name: string; type: string; color: string; size: number; province?: string }[];
  links: { source: string; target: string; type: string }[];
}
export interface Citation { name: string; type: string; slug: string; }
export interface GraphFilter { province: string; developer: string; types: string[]; }
export interface Community { id: string; label: string; entity_count: number; report: string; province: string; }
export interface PendingMutation {
  operation: "insert" | "update" | "delete";
  entity: "project" | "contact";
  display_name: string;
  slug?: string | null;
  data?: Record<string, any> | null;
  changes?: Record<string, { old: any; new: any }> | null;
  summary?: string;
}
export interface MutateExecutePayload {
  operation: string;
  entity: string;
  slug?: string | null;
  display_name?: string;
  data?: Record<string, any> | null;
  confirmed?: boolean;
}
export interface MutateExecuteResponse {
  success: boolean;
  message: string;
  entity_key?: string | null;
}
export interface ReportChartSpec {
  id: string;
  title: string;
  type: "bar" | "line" | "pie";
  data: { label: string; value: number }[];
}
export interface AgentReport {
  id: string;
  title: string;
  summary: string;
  html: string;
  charts: ReportChartSpec[];
  download_url?: string;
}
export interface ChatResponse {
  answer: string;
  citations: Citation[];
  context_used: number;
  graph_filter?: GraphFilter | null;
  pending_mutation?: PendingMutation | null;
  report?: AgentReport | null;
}
export interface QueryLog {
  id: number; query: string; answer: string;
  intent: string; timestamp: string;
}
export interface ChatSessionMessage {
  role: "user" | "ai";
  content: string;
  citations?: Citation[];
  context_used?: number;
  graph_filter?: GraphFilter | null;
  report?: AgentReport | null;
}
export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}
export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatSessionMessage[];
}
export interface Report {
  id: string; title: string; file_path: string;
  query: string; timestamp: string;
  kind?: "html" | "pdf" | "excel";
  html_available?: boolean;
  html?: string;
  charts?: ReportChartSpec[];
}
export interface FieldDef { key: string; label: string; }
export interface FieldsResponse { projects: FieldDef[]; contacts: FieldDef[]; }
export interface SaveTableChangesPayload {
  source: "projects" | "contacts";
  changes: { row_id?: string; values: Record<string, string> }[];
  deletes?: string[];
}
export interface SaveTableChangesResponse {
  success: boolean;
  updated: number;
  inserted: number;
  deleted: number;
  skipped: number;
  errors: string[];
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const base = API || (typeof window !== "undefined" ? window.location.origin : "http://localhost:3000");
  const url = new URL(`${base}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    });
  }
  return url.toString();
}

/**
 * Drop cached responses whose URL contains any of the given path fragments.
 * Pass no args to wipe the entire cache.
 *
 * Example:
 *   invalidateCache(["/api/graph", "/api/stats", "/api/projects"])
 */
export function invalidateCache(fragments?: string[]): void {
  if (!fragments || fragments.length === 0) {
    requestCache.clear();
    return;
  }
  const keysToRemove: string[] = [];
  requestCache.forEach((_, url) => {
    if (fragments.some((f) => url.includes(f))) keysToRemove.push(url);
  });
  keysToRemove.forEach((k) => requestCache.delete(k));
}

/** Convenience: clear caches that depend on project/contact data. */
export function invalidateGraphCache(): void {
  invalidateCache(["/api/graph", "/api/stats", "/api/projects", "/api/contacts", "/api/query"]);
}

async function get<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
  options?: { ttlMs?: number }
): Promise<T> {
  const url = buildUrl(path, params);
  const ttlMs = options?.ttlMs ?? 0;
  const now = Date.now();

  if (ttlMs > 0) {
    const cached = requestCache.get(url) as CacheEntry<T> | undefined;
    if (cached) {
      if (cached.data !== undefined && cached.expiresAt > now) return cached.data;
      if (cached.inFlight) return cached.inFlight;
    }
  }

  const fetchPromise = fetch(url).then(async (res) => {
    if (!res.ok) throw new Error(`API error ${res.status}`);
    const payload = (await res.json()) as T;

    if (ttlMs > 0) {
      requestCache.set(url, {
        data: payload,
        expiresAt: Date.now() + ttlMs,
      });
    }

    return payload;
  }).catch((err) => {
    requestCache.delete(url);
    throw err;
  });

  if (ttlMs > 0) {
    requestCache.set(url, {
      expiresAt: now + ttlMs,
      inFlight: fetchPromise,
    });
  }

  return fetchPromise;
}

export const api = {
  stats: () => get<Stats>("/api/stats", undefined, { ttlMs: 60_000 }),
  projects: (params?: {
    province?: string; developer?: string; status?: string;
    type_tag?: string; search?: string; page?: number; limit?: number;
  }) => get<{ data: Project[]; total: number; page: number; limit: number }>("/api/projects", params as any, { ttlMs: 6_000 }),
  project: (slug: string) => get<Project>(`/api/projects/${slug}`, undefined, { ttlMs: 30_000 }),
  contacts: (params?: { company?: string; search?: string; page?: number }) =>
    get<{ data: Contact[]; total: number }>("/api/contacts", params as any, { ttlMs: 6_000 }),
  contact: (slug: string) => get<Contact>(`/api/contacts/${slug}`, undefined, { ttlMs: 30_000 }),
  graph: () => get<GraphData>("/api/graph", undefined, { ttlMs: 60_000 }),
  communities: () => get<{ communities: Community[] }>("/api/graph/communities", undefined, { ttlMs: 300_000 }),
  chat: (
    query: string,
    history: {role: string; content: string}[] = [],
    style: "natural" | "precise" = "natural",
  ) =>
    fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, history, style }),
    }).then(r => r.json()) as Promise<ChatResponse>,
  exportTable: (headers: string[], rows: string[][], title = "CoreOne") => {
    fetch(`${API}/api/export/table`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ headers, rows, title }),
    }).then(res => res.blob()).then(blob => {
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `${title}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    });
  },
  exportExcel: (params?: Record<string, string>) => {
    const url = new URL(buildUrl("/api/export/excel"));
    if (params) Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
    window.open(url.toString(), "_blank");
  },
  // Query history
  chatHistory: (limit = 30) =>
    get<{ data: QueryLog[] }>("/api/chat/history", { limit }, { ttlMs: 5_000 }),
  deleteHistory: (id: string) =>
    fetch(`${API}/api/chat/history/${id}`, { method: "DELETE" }).then(r => r.json()) as Promise<{ success: boolean }>,
  // Full conversation sessions
  chatSessions: (limit = 30) =>
    get<{ data: ChatSessionSummary[] }>("/api/chat/sessions", { limit }, { ttlMs: 3_000 }),
  chatSession: (id: string) =>
    get<{ data: ChatSession }>(`/api/chat/sessions/${id}`),
  saveChatSession: (payload: {
    session_id?: string;
    title?: string;
    messages: ChatSessionMessage[];
  }) =>
    fetch(`${API}/api/chat/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json()) as Promise<{ success: boolean; id: string }>,
  deleteChatSession: (id: string) =>
    fetch(`${API}/api/chat/sessions/${id}`, { method: "DELETE" }).then(r => r.json()) as Promise<{ success: boolean }>,
  // Reports vault
  reports: () => get<{ data: Report[] }>("/api/reports", undefined, { ttlMs: 10_000 }),
  reportDownloadUrl: (id: string) => `${API}/api/reports/${id}/download`,
  reportHtml: (id: string) =>
    get<{ html: string; report: Report }>(`/api/reports/${id}/html`),
  createAgentReport: (query: string, language = "vi") =>
    fetch(`${API}/api/reports/agent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language }),
    }).then(r => r.json()) as Promise<{ success: boolean; report: AgentReport }>,
  reportDownload: (id: string) =>
    window.open(`${API}/api/reports/${id}/download`, "_blank"),
  // Project summary
  projectSummary: (slug: string) =>
    fetch(`${API}/api/projects/${slug}/summary`, { method: "POST" })
      .then(r => r.json()) as Promise<{ summary: string; report_id: number | null; project: string }>,
  // Data Manager
  fields: () => get<FieldsResponse>("/api/fields", undefined, { ttlMs: 60_000 }),
  query: (payload: {
    source: "projects" | "contacts";
    columns: string[];
    filters: Record<string, string>;
    page?: number;
    limit?: number;
  }) => fetch(`${API}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.json()) as Promise<{ data: Record<string, any>[]; total: number; page: number; limit: number }>,
  saveTableChanges: (payload: SaveTableChangesPayload) =>
    fetch(`${API}/api/query/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json()) as Promise<SaveTableChangesResponse>,
  // AI-driven data mutations (confirmed by user)
  mutateExecute: (payload: MutateExecutePayload) =>
    fetch(`${API}/api/mutate/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json()) as Promise<MutateExecuteResponse>,
};
