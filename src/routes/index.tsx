import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, API_URL, type ScanType } from "@/lib/api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PhishShield — Phishing Detection Console" },
      {
        name: "description",
        content: "PhishShield console: submit URLs, emails and text for phishing analysis.",
      },
      { property: "og:title", content: "PhishShield — Phishing Detection Console" },
      {
        property: "og:description",
        content: "Submit URLs, emails and text for multi-layer phishing analysis.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: Index,
});

function Index() {
  const qc = useQueryClient();
  const [type, setType] = useState<ScanType>("url");
  const [value, setValue] = useState("");

  // Client-only: the backend runs on the user's machine, not the edge server.
  const health = useQuery({ queryKey: ["health"], queryFn: api.health, refetchInterval: 10000, retry: false });
  const scans = useQuery({ queryKey: ["scans"], queryFn: api.listScans, retry: false, enabled: health.isSuccess });
  const create = useMutation({
    mutationFn: () => api.createScan(type, value.trim()),
    onSuccess: () => {
      setValue("");
      qc.invalidateQueries({ queryKey: ["scans"] });
    },
  });

  const online = health.data?.status === "ok";

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.3em] text-primary">PhishShield / Phase 1</p>
            <h1 className="mt-2 text-4xl font-bold tracking-tight">Detection Console</h1>
          </div>
          <div className="panel flex items-center gap-3 px-4 py-2 font-mono text-xs">
            <span className={`status-dot ${online ? "status-dot-ok" : health.isLoading ? "" : "status-dot-bad"}`} />
            <span>
              {health.isLoading
                ? "connecting…"
                : health.isError
                  ? "backend unreachable"
                  : `api v${health.data!.version} · db ${health.data!.database}`}
            </span>
          </div>
        </header>

        {health.isError && (
          <div className="panel mt-6 border-destructive/50 p-4 text-sm">
            <p className="font-semibold text-destructive">Can't reach the backend at {API_URL}</p>
            <p className="mt-1 text-muted-foreground">
              Start it with <code className="font-mono">docker compose up</code> and set{" "}
              <code className="font-mono">VITE_API_URL</code> if it runs elsewhere.
            </p>
          </div>
        )}

        <section className="panel mt-8 p-6">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (value.trim()) create.mutate();
            }}
            className="space-y-4"
          >
            <div className="flex gap-2">
              {(["url", "email", "text"] as ScanType[]).map((t) => (
                <button
                  type="button"
                  key={t}
                  onClick={() => setType(t)}
                  className={`chip ${type === t ? "chip-active" : ""}`}
                >
                  {t}
                </button>
              ))}
            </div>
            {type === "url" ? (
              <input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="https://suspicious-site.example/login"
                className="field"
              />
            ) : (
              <textarea
                value={value}
                onChange={(e) => setValue(e.target.value)}
                rows={5}
                placeholder={type === "email" ? "Paste the raw email…" : "Paste the message…"}
                className="field"
              />
            )}
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs text-muted-foreground">
                Detectors aren't trained yet — scans are stored as <span className="font-mono">pending</span>.
              </p>
              <button type="submit" disabled={!online || create.isPending || !value.trim()} className="btn-primary">
                {create.isPending ? "Submitting…" : "Submit scan"}
              </button>
            </div>
            {create.isError && <p className="text-sm text-destructive">{(create.error as Error).message}</p>}
          </form>
        </section>

        <section className="mt-10">
          <h2 className="font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground">Scan history</h2>
          <ul className="mt-4 space-y-2">
            {scans.data?.length === 0 && <li className="text-sm text-muted-foreground">No scans yet.</li>}
            {scans.data?.map((s) => (
              <li key={s.id} className="panel flex items-center gap-4 px-4 py-3 text-sm">
                <span className="chip chip-active">{s.scan_type}</span>
                <span className="flex-1 truncate font-mono">{s.input_value}</span>
                <span className="font-mono text-xs text-muted-foreground">{s.verdict ?? s.status}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {new Date(s.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
