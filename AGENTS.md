<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## Architecture rules
- Backend is Python FastAPI in `services/api` with PostgreSQL via SQLAlchemy + Alembic; schema changes always go through a new Alembic migration. Why: the project spec mandates this stack.
- The web app talks to the backend only from the browser via `src/lib/api.ts` and `VITE_API_URL`; no TanStack server functions or Lovable Cloud. Why: the backend runs on the user's machine/Docker, not the edge worker.
- Never return fabricated verdicts, risk scores or metrics; fields stay null until a real detector/model produces them. Why: the user forbids placeholder ML output.
- `apps/mobile` is a Flutter client of the same API and cannot be built in this sandbox; mark it untested.
- URL detection is an offline, versioned Python rules module using the bundled public suffix list and edit-distance library; never fetch or resolve submitted URLs. Why: avoid SSRF and keep results reproducible without inventing model probabilities.
- Store evidence in the existing scans.details JSONB column and keep risk_score null until a calibrated model exists; non-URL scans remain pending. Why: rule findings are not phishing probabilities and need no schema change.
