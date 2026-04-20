# WhiteFly Task
[EN](README.md) | [PL](README.pl.md)

Production-style recruitment solution with two separate apps:
- Flask (`/flask`)
- FastAPI (`/fastapi`)

Both implement:
- Hello World page
- Sync form -> direct PostgreSQL write
- Async form -> Celery + Redis queue -> worker write
- Server-side validation
- Anti-bot protections
- Nginx reverse proxy
- k6 performance tests

## Stack
- Python 3.12
- Flask, FastAPI
- SQLAlchemy, PostgreSQL
- Celery, Redis
- Nginx
- Docker Compose
- k6

## Run
```bash
cp .env.example .env
docker compose up -d --build
```

Open:
- Flask: `http://localhost:8080/flask/`
- FastAPI: `http://localhost:8080/fastapi/`

If you get `502`, restart nginx after web container recreate:
```bash
docker compose restart nginx
```

## Required Env
- `SECRET_KEY`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `FPJS_PUBLIC_KEY`
- `FPJS_SERVER_API_KEY`
- `FPJS_SERVER_API_BASE_URL`
- `FPJS_CONFIDENCE_THRESHOLD`
- `FPJS_VERIFY_TIMEOUT_SECONDS`
- `FPJS_FAIL_OPEN`

## Architecture
- Nginx routes:
  - `/flask/` -> Flask web
  - `/fastapi/` -> FastAPI web
- Redis is used for Celery broker/backend and rate-limit storage.
- PostgreSQL stores all submissions in one table.
- Async flow:
  - web validates and enqueues payload
  - worker inserts `processed` or `failed` record

## Main Endpoints
Flask:
- `GET /flask/`
- `GET|POST /flask/form-sync`
- `GET|POST /flask/form-async`
- `GET /flask/submissions`

FastAPI:
- `GET /fastapi/`
- `GET|POST /fastapi/form-sync`
- `GET|POST /fastapi/form-async`
- `GET /fastapi/submissions`

## Anti-bot
- Honeypot hidden field
- Rate limiting per IP
- Minimum submit time check
- CSRF protection (Flask-WTF / token-based in FastAPI)
- FingerprintJS:
  - frontend sends `requestId` and `visitorId`
  - backend verifies via Fingerprint Server API
  - result is stored in `fp_*` columns

## Load Testing
```bash
k6 run k6/flask_test.js
k6 run k6/fastapi_test.js
```

Compare:
- Sync latency includes direct DB write
- Async usually responds faster, DB work finishes in worker

## Railway Test Report (April 20, 2026)
Target domain:
- `https://nginx-production-2ce8.up.railway.app`

### Scenario A: High load profile (10 VUs, 30s)
Flask (`/flask`):
- checks: `84.44%` (152/180), failed `15.55%`
- http_req_failed: `14.00%` (42/300)
- latency: avg `71.52ms`, p95 `96.79ms`

FastAPI (`/fastapi`):
- checks: `44.44%` (80/180), failed `55.55%`
- http_req_failed: `33.33%` (100/300)
- latency: avg `79.39ms`, p95 `95.85ms`

Interpretation:
- This scenario primarily validated anti-abuse controls.
- FastAPI has endpoint-level limiter (`10 req / 60s` per IP), so many POST requests were intentionally rejected under this profile.
- Nginx and Flask paths also showed request rejections under burst traffic.

### Scenario B: Baseline profile for fair comparison (1 VU, 60s)
Flask (`/flask`):
- checks: `100%` (30/30)
- http_req_failed: `0.00%` (0/50)
- latency: avg `76.25ms`, p95 `99.91ms`
- throughput: `50` requests (`0.781 req/s`)

FastAPI (`/fastapi`):
- checks: `100%` (30/30)
- http_req_failed: `0.00%` (0/50)
- latency: avg `79.54ms`, p95 `97.07ms`
- throughput: `50` requests (`0.779 req/s`)

Final conclusions:
- Both deployments are stable behind Nginx under non-abusive load.
- Flask and FastAPI show very similar baseline performance in this environment.
- High-load failures were expected due to anti-bot/rate-limit protections, not because of core business-flow crashes.
- For final reporting, both baseline and abuse scenarios should be shown together: baseline for performance, abuse for security behavior.

## Notes
- Flask and FastAPI are intentionally separated by folder and runtime.
- `.env` is excluded from git.
- Project is Docker-first and ready for reverse-proxy performance checks.
