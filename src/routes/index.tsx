import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Search, ShieldCheck, Eye } from "lucide-react";
import { api, API_URL, getBackendState, type Scan, type ScanType } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ScanResult, verdictLabel } from "@/components/scan-result";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PhishShield — Phishing Detection Console" },
      {
        name: "description",
        content: "PhishShield URL analysis with offline lexical checks, brand lookalike findings and saved scan evidence.",
      },
      { property: "og:title", content: "PhishShield — Phishing Detection Console" },
      {
        property: "og:description",
        content: "Inspect URL warning signs and lookalike domains with transparent, rule-based findings.",
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
  const [selected, setSelected] = useState<Scan | null>(null);

  // Client-only: the backend runs on the user's machine, not the edge server.
  const backend = useQuery({ queryKey: ["backend"], queryFn: getBackendState, refetchInterval: 10000, retry: false });
  const state = backend.data;
  const online = state?.kind === "ready";
  const scans = useQuery({ queryKey: ["scans"], queryFn: api.listScans, retry: false, enabled: online });
  const create = useMutation({
    mutationFn: () => api.createScan(type, value.trim()),
    onSuccess: (scan) => {
      setSelected(scan);
      setValue("");
      qc.invalidateQueries({ queryKey: ["scans"] });
    },
  });
  const inspect = useMutation({ mutationFn: api.getScan, onSuccess: setSelected });

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <header className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-6">
          <div>
            <p className="font-mono text-xs uppercase text-primary">Detection Console / Phase 2</p>
            <h1 className="mt-2 flex items-center gap-3 text-4xl font-bold"><ShieldCheck className="size-9 text-primary" aria-hidden="true" />PhishShield</h1>
          </div>
          <div className="panel flex items-center gap-3 px-4 py-2 font-mono text-xs">
            <span
              className={`status-dot ${
                !state ? "" : state.kind === "ready" ? "status-dot-ok" : state.kind === "db_unavailable" ? "status-dot-warn" : "status-dot-bad"
              }`}
            />
            <span>
              {!state
                ? "connecting…"
                : state.kind === "unreachable"
                  ? "backend unreachable"
                  : state.kind === "db_unavailable"
                    ? `api v${state.health.version} · database unavailable`
                    : `api v${state.health.version} · database ready`}
            </span>
          </div>
        </header>

        {state?.kind === "unreachable" && (
          <div className="panel mt-6 border-destructive/50 p-4 text-sm">
            <p className="font-semibold text-destructive">Can't reach the backend at {API_URL}</p>
            <p className="mt-1 text-muted-foreground">
              No response ({state.reason}). Start it with <code className="font-mono">docker compose up</code>. A
              hosted preview can't reach <code className="font-mono">localhost</code> on your computer — expose the
              API with a public HTTPS URL and set <code className="font-mono">VITE_API_URL</code>.
            </p>
          </div>
        )}
        {state?.kind === "db_unavailable" && (
          <div className="panel mt-6 border-warning/50 p-4 text-sm">
            <p className="font-semibold text-warning">Backend is running, but the database is unavailable</p>
            <p className="mt-1 text-muted-foreground">
              {state.ready?.dependencies["database"]?.error
                ? `Database check failed: ${state.ready.dependencies["database"].error}. `
                : ""}
              Check that PostgreSQL is up and <code className="font-mono">DATABASE_URL</code> is correct.
            </p>
          </div>
        )}

        <section className="mt-8">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (value.trim()) create.mutate();
            }}
            className="space-y-4"
          >
              <div className="flex gap-2" role="group" aria-label="Scan type">
              {(["url", "email", "text"] as ScanType[]).map((t) => (
                <Button
                  type="button"
                  key={t}
                  onClick={() => { setType(t); setValue(""); create.reset(); }}
                  variant={type === t ? "default" : "outline"}
                  size="sm"
                  aria-pressed={type === t}
                >
                  {t}
                </Button>
              ))}
            </div>
            {type === "url" ? (
              <input
                aria-label="URL to analyze"
                maxLength={20000}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="https://suspicious-site.example/login"
                className="field"
              />
            ) : (
              <textarea
                aria-label={type === "email" ? "Email to scan" : "Text to scan"}
                maxLength={20000}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                rows={5}
                placeholder={type === "email" ? "Paste the raw email…" : "Paste the message…"}
                className="field"
              />
            )}
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-xs text-muted-foreground">
                {type === "url" ? "URL rules · No trained-model probability" : "Email and text analysis not available yet"}
              </p>
              <Button type="submit" disabled={!online || create.isPending || !value.trim()}>
                <Search aria-hidden="true" />{create.isPending ? "Submitting…" : type === "url" ? "Analyze URL" : "Submit scan"}
              </Button>
            </div>
            {create.isError && <p className="text-sm text-destructive">{(create.error as Error).message}</p>}
          </form>
          {selected && <ScanResult scan={selected} />}
        </section>

        <section className="mt-10">
          <h2 className="font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground">Scan history</h2>
          {scans.isError && <p className="mt-3 text-sm text-destructive">Could not load scan history. {(scans.error as Error).message}</p>}
          {inspect.isError && <p className="mt-3 text-sm text-destructive">{(inspect.error as Error).message}</p>}
          {scans.isFetching && <p className="mt-3 text-xs text-muted-foreground">Loading history…</p>}
          <ul className="mt-4 space-y-2">
            {scans.data?.length === 0 && <li className="text-sm text-muted-foreground">No scans yet.</li>}
            {scans.data?.map((s) => (
              <li key={s.id} className="panel flex flex-wrap items-center gap-3 px-4 py-3 text-sm">
                <span className="chip chip-active">{s.scan_type}</span>
                <span className="min-w-0 flex-1 truncate font-mono">{s.input_value}</span>
                <span className={`font-mono text-xs ${s.verdict === "suspicious" ? "text-destructive" : s.verdict === "review" ? "text-warning" : "text-muted-foreground"}`}>{verdictLabel(s)}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {new Date(s.created_at).toLocaleString()}
                </span>
                <Button type="button" variant="ghost" size="icon" title="View scan details" aria-label={`View scan ${s.input_value}`} disabled={inspect.isPending} onClick={() => inspect.mutate(s.id)}><Eye /></Button>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
