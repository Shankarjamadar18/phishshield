// Client for the PhishShield FastAPI backend (services/api).
export const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

export type Health = {
  status: "ok" | "degraded";
  service: string;
  version: string;
  database: "up" | "down";
};

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
  health: () => request<Health>("/health"),
  listScans: () => request<Scan[]>("/api/v1/scans"),
  createScan: (scan_type: ScanType, input_value: string) =>
    request<Scan>("/api/v1/scans", {
      method: "POST",
      body: JSON.stringify({ scan_type, input_value }),
    }),
};
