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
- `GET /health/live` — liveness
- `GET /health` — liveness + database check
- `POST /api/v1/scans` — store a scan request (`url|email|text`). Returns `status: pending`; no verdict is produced until detectors exist.
- `GET /api/v1/scans` — recent scans
