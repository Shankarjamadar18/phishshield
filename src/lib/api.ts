// Client for the PhishShield FastAPI backend (services/api).
export const API_URL: string =
  (import.meta.env["VITE_API_URL"] as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export type Health = { status: "ok"; service: string; version: string };

export type Ready = {
  status: "ready" | "not_ready";
  dependencies: Record<string, { status: "up" | "down"; error: string | null }>;
};

/** unreachable: no HTTP response at all (server down, wrong URL, CORS, mixed content). */
export type BackendState =
  | { kind: "unreachable"; reason: string }
  | { kind: "db_unavailable"; health: Health; ready: Ready | null }
  | { kind: "ready"; health: Health; ready: Ready };

export async function getBackendState(): Promise<BackendState> {
  let health: Health;
  try {
    const res = await fetch(`${API_URL}/health`);
    if (!res.ok) return { kind: "unreachable", reason: `/health returned HTTP ${res.status}` };
    health = (await res.json()) as Health;
  } catch (e) {
    return { kind: "unreachable", reason: e instanceof Error ? e.message : String(e) };
  }
  try {
    const res = await fetch(`${API_URL}/ready`);
    const ready = (await res.json()) as Ready;
    return res.ok && ready.status === "ready"
      ? { kind: "ready", health, ready }
      : { kind: "db_unavailable", health, ready };
  } catch {
    return { kind: "db_unavailable", health, ready: null };
  }
}

export type ScanType = "url" | "email" | "text";

export type Scan = {
  id: string;
  scan_type: ScanType;
  input_value: string;
  status: string;
  verdict: string | null;
  risk_score: number | null;
  created_at: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  listScans: () => request<Scan[]>("/api/v1/scans"),
  createScan: (scan_type: ScanType, input_value: string) =>
    request<Scan>("/api/v1/scans", {
      method: "POST",
      body: JSON.stringify({ scan_type, input_value }),
    }),
};
