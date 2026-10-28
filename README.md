# PhishShield

Real-time AI/ML phishing detection and prevention — final-year major project.

## Layout
| Path | What |
|---|---|
| `src/` | Web frontend (React + TypeScript + Vite/TanStack Start + Tailwind) |
| `services/api/` | FastAPI backend, offline URL detector, health, scans API, SQLAlchemy models |
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

## API (Phase 2)
- `GET /health` — liveness only (process is running)
- `GET /ready` — readiness; checks PostgreSQL, returns 503 if a dependency is down
- `POST /api/v1/scans` — analyze and store valid HTTP(S) URLs immediately; email/text requests remain `pending` with null verdict and risk score. Invalid URLs and blank input return 422.
- `GET /api/v1/scans` — recent scans
- `GET /api/v1/scans/{id}` — persisted scan and its detailed findings; 404 when missing

## Phase 2: completed scope and limits
- URL parsing and IDNA normalization; offline bundled public suffix extraction (including private tenant suffixes).
- Measured lexical features: HTTP/HTTPS, IP hosts, embedded credentials, URL length, hyphens, subdomains, unusual ports, suffix review list, and sensitive keywords.
- Brand review list: PayPal, Google, Microsoft, Apple, Amazon, Facebook, Instagram, Netflix. Limited official domains and one-edit/leet/brand-subdomain/decorated-label checks; not a complete brand or Unicode-confusable database.
- Findings are stored in the existing `scans.details` JSONB column, so Phase 2 needs no schema migration. Existing Phase 1 scans are not retroactively analyzed; submit them again.
- Verdicts: `suspicious` for configured brand lookalikes, `review` for other rule indicators, `no_indicators` when no rule fires. These are **not proof of phishing or safety**. False positives and false negatives are possible.
- `risk_score` stays null: no trained model, calibration, phishing probability, benchmark accuracy, DNS, reputation lookup, page fetching, redirects, blocking, or email detector exists yet.
- The web console displays saved evidence and allows reopening scan details. Authentication is still unimplemented; this is a shared, anonymous development console. Do not expose it publicly with private scan content.
- Flutter and Docker Compose execution have not been verified in this sandbox; Python/API and web flows are tested separately.

### Update your local Docker installation
After downloading the updated project files, run from the project folder:
```bash
docker compose up --build -d
docker compose ps
bun install
bun run dev
```
Docker downloads and runs PostgreSQL; no separate laptop PostgreSQL install is required. Keep the existing `pgdata` volume to retain scans. Do **not** run `docker compose down -v` unless you intend to erase the database.
Try `https://paypa1.com/login` (lookalike), `http://127.0.0.1/login` (review), and `https://www.paypal.com/login` (no configured indicators, not guaranteed safe).

## Using the hosted Lovable preview
The preview runs on the internet over HTTPS and cannot reach `localhost` on your computer. Either:
1. **Run the web app locally** (`bun run dev`, open http://localhost:8080) — works with the default `VITE_API_URL`.
2. **Expose your local API with a tunnel**, e.g. `cloudflared tunnel --url http://localhost:8000`, then:
   - in `.env`: `CORS_ORIGIN_REGEX=https://.*\.lovable\.app` and restart `docker compose up`
   - set `VITE_API_URL=https://<your-tunnel>.trycloudflare.com` for the web app and rebuild.
3. **Deploy the API** (Render, Railway, Fly.io, a VPS) with a managed PostgreSQL and use its HTTPS URL as `VITE_API_URL`.

`VITE_API_URL` is public. Never put database passwords or API keys in any `VITE_` variable.
