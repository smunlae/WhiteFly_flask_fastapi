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

## Notes
- Flask and FastAPI are intentionally separated by folder and runtime.
- `.env` is excluded from git.
- Project is Docker-first and ready for reverse-proxy performance checks.
