import { ShieldAlert, ShieldQuestion, SearchCheck } from "lucide-react";
import type { Scan } from "@/lib/api";

export function verdictLabel(scan: Scan) {
  if (scan.verdict === "suspicious") return "Suspicious";
  if (scan.verdict === "review") return "Needs review";
  if (scan.verdict === "no_indicators") return "No indicators found";
  return scan.status === "pending" ? "Pending" : scan.status;
}

export function ScanResult({ scan }: { scan: Scan }) {
  const details = scan.details ?? {};
  const features = details.features;
  const Icon = scan.verdict === "suspicious" ? ShieldAlert : scan.verdict === "review" ? ShieldQuestion : SearchCheck;
  const tone = scan.verdict === "suspicious" ? "text-destructive" : scan.verdict === "review" ? "text-warning" : "text-primary";
  return (
    <section className="mt-6 border-t border-border pt-6" aria-label="Scan result">
      <div className={`flex items-center gap-3 ${tone}`}>
        <Icon aria-hidden="true" className="size-6 shrink-0" />
        <h2 className="text-xl font-semibold">{verdictLabel(scan)}</h2>
      </div>
      <p className="mt-3 break-all font-mono text-sm">{scan.input_value}</p>
      {scan.status === "pending" ? <p className="mt-3 text-sm text-muted-foreground">Awaiting an email or text detector.</p> : (
        <>
          <p className="mt-2 text-xs text-muted-foreground">Offline URL rules · {details.version ?? "unknown version"} · ML probability: not available</p>
          {features && <dl className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
            {[
              ["Destination host", features.hostname],
              ["Registered domain", features.registered_domain ?? "Not available"],
              ["HTTPS", features.uses_https ? "Yes" : "No"],
              ["URL length", `${features.url_length} characters`],
              ["Subdomains", String(features.subdomain_count)],
              ["Domain hyphens", String(features.hyphen_count)],
            ].map(([label, value]) => <div key={label} className="min-w-0"><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 break-all font-mono">{value}</dd></div>)}
          </dl>}
          <ul className="mt-5 divide-y divide-border">
            {details.findings?.map((f, i) => <li key={`${f.code}-${i}`} className="py-3 text-sm">
              <p className={f.severity === "high" ? "font-medium text-destructive" : "font-medium text-warning"}>{f.message}</p>
              <p className="mt-1 break-all font-mono text-xs text-muted-foreground">{f.evidence}</p>
            </li>)}
          </ul>
          <p className="mt-4 text-xs leading-relaxed text-muted-foreground">{details.limitations ?? "No indicators does not mean safe."}</p>
        </>
      )}
    </section>
  );
}