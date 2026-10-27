# PhishShield

Real-time AI/ML phishing detection and prevention — final-year major project.

## Layout
| Path | What |
|---|---|
| `src/` | Web frontend (React + TypeScript + Vite/TanStack Start + Tailwind) |
| `services/api/` | FastAPI backend: config, JSON logging, health, scans API, SQLAlchemy models |
| `services/api/migrations/` | Alembic migrations (PostgreSQL) |
| `services/api/tests/` | pytest integration tests (need a migrated Postgres) |
| `apps/mobile/` | Flutter client skeleton (untested) |
| `ml/` | Empty until Phase 3 — no datasets or models exist yet |
| `docker-compose.yml` | Postgres + API |

## Run locally
```bash
docker compose up --build          # Postgres on 5432, API on 8000 (migrations run on start)
cp .env.example .env               # VITE_API_URL=http://localhost:8000
bun install && bun run dev         # web on http://localhost:8080
```

## Tests
```bash
cd services/api && pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://phishshield:phishshield@localhost:5432/phishshield
alembic upgrade head && pytest
```

## API (Phase 1)
- `GET /health` — liveness only (process is running)
- `GET /ready` — readiness; checks PostgreSQL, returns 503 if a dependency is down
- `POST /api/v1/scans` — store a scan request (`url|email|text`). Returns `status: pending`; no verdict is produced until detectors exist.
- `GET /api/v1/scans` — recent scans

## Using the hosted Lovable preview
The preview runs on the internet over HTTPS and cannot reach `localhost` on your computer. Either:
1. **Run the web app locally** (`bun run dev`, open http://localhost:8080) — works with the default `VITE_API_URL`.
2. **Expose your local API with a tunnel**, e.g. `cloudflared tunnel --url http://localhost:8000`, then:
   - in `.env`: `CORS_ORIGIN_REGEX=https://.*\.lovable\.app` and restart `docker compose up`
   - set `VITE_API_URL=https://<your-tunnel>.trycloudflare.com` for the web app and rebuild.
3. **Deploy the API** (Render, Railway, Fly.io, a VPS) with a managed PostgreSQL and use its HTTPS URL as `VITE_API_URL`.

`VITE_API_URL` is public. Never put database passwords or API keys in any `VITE_` variable.
