# WhiteFly Recruitment Task Solution

## 1. Project Overview
This repository contains two parallel backend implementations of the same recruitment assignment:
- `flask_app`: Flask + Jinja2 + SQLAlchemy + Celery
- `fastapi_app`: FastAPI + Jinja2Templates + SQLAlchemy + Celery

Both applications implement:
- Hello World page
- Synchronous form submission directly to PostgreSQL
- Asynchronous form submission through Celery + Redis
- Server-side validation
- Anti-bot mitigation layers
- HTML templates and minimal UI
- Dockerized deployment behind Nginx reverse proxy
- k6 performance test scripts

## 2. Assignment Coverage Mapping
1. Build a Python Flask service that displays Hello World:
- Implemented in Flask `GET /`.

2. Create Flask form collecting user data:
- Implemented with first name and last name forms in `GET /form-sync` and `GET /form-async`.

3. Synchronous POST from Flask form to database:
- `POST /form-sync` validates and writes directly to PostgreSQL with `source_type=sync` and `status=completed`.

4. Asynchronous Flask form via queue:
- `POST /form-async` validates and enqueues a Celery task with payload, then returns quickly.
- Celery worker performs DB insert and writes `processed` or `failed` status.

5. Repeat using FastAPI:
- Equivalent endpoints and flows in `fastapi_app`.

6. Prepare server deployment behind reverse proxy:
- Nginx routes `/flask/` to Flask and `/fastapi/` to FastAPI.
- Forwarded headers and request limiting are configured.

7. Add performance testing using k6:
- `k6/flask_test.js` and `k6/fastapi_test.js` cover home, sync POST, async POST.

8. Anti-bot/fake registration mitigations:
- Honeypot hidden field
- Per-IP rate limiting
- Minimum form submission time gate
- CSRF protection strategy per framework
- Fingerprint-ready optional field storage

## 3. Architecture Overview
- Nginx is the entrypoint and reverse proxy on port `8080`.
- Flask web and FastAPI web services process HTML requests.
- PostgreSQL stores all submissions in a shared `submissions` table.
- Redis serves as:
  - Celery broker/result backend
  - Flask limiter storage
  - FastAPI rate limiter backend
- Separate Celery workers for Flask and FastAPI process async form submissions.

Flow summary:
- Sync flow: request -> validation -> DB insert -> response
- Async flow: request -> validation -> Celery enqueue -> immediate response -> worker DB insert -> status persisted

## 4. Tech Stack
- Python 3.12
- Flask 3
- FastAPI
- SQLAlchemy 2
- PostgreSQL 16
- Redis 7
- Celery 5
- Nginx 1.27
- Docker / Docker Compose
- k6

## 5. Repository Structure
```text
whitefly-task/
├─ flask_app/
│  ├─ app/
│  ├─ templates/
│  ├─ static/
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ run.py
├─ fastapi_app/
│  ├─ app/
│  ├─ templates/
│  ├─ static/
│  ├─ requirements.txt
│  ├─ Dockerfile
│  └─ main.py
├─ nginx/
│  └─ nginx.conf
├─ k6/
│  ├─ flask_test.js
│  └─ fastapi_test.js
├─ docker-compose.yml
├─ .env.example
└─ README.md
```

## 6. Run Locally with Docker Compose
1. Open the repository root:
```bash
cd whitefly-task
```

2. Copy env file:
```bash
cp .env.example .env
```
Set real Fingerprint keys in `.env` for production-like verification:
- `FPJS_PUBLIC_KEY`
- `FPJS_SERVER_API_KEY`
- `FPJS_SERVER_API_BASE_URL` (`https://api.fpjs.io`, `https://eu.api.fpjs.io`, or `https://ap.api.fpjs.io`)
- `FPJS_CONFIDENCE_THRESHOLD`
- `FPJS_VERIFY_TIMEOUT_SECONDS`
- `FPJS_FAIL_OPEN`

3. Start full stack:
```bash
docker compose up --build
```
or if errors (like 502) use:
```bash
docker compose down && docker compose up -d --build
```

4. Open services through Nginx:
- Flask: `http://localhost:8080/flask/`
- FastAPI: `http://localhost:8080/fastapi/`

## 7. Endpoints
### Flask endpoints
- `GET /flask/`
- `GET /flask/form-sync`
- `POST /flask/form-sync`
- `GET /flask/form-async`
- `POST /flask/form-async`
- `GET /flask/submissions`

### FastAPI endpoints
- `GET /fastapi/`
- `GET /fastapi/form-sync`
- `POST /fastapi/form-sync`
- `GET /fastapi/form-async`
- `POST /fastapi/form-async`
- `GET /fastapi/submissions`

## 8. Database Model
Table: `submissions`
- `id`
- `first_name`
- `last_name`
- `framework`
- `source_type`
- `status`
- `client_ip`
- `user_agent`
- `fingerprint`
- `honeypot_triggered`
- `processing_error`
- `created_at`

Why PostgreSQL:
- production-grade transactional consistency
- mature indexing and operational tooling
- strong compatibility with SQLAlchemy and scaling patterns

## 9. Sync vs Async Flow
### Synchronous
- Form request is validated server-side.
- Record is inserted in PostgreSQL in the same request lifecycle.
- User gets response after DB write is complete.

### Asynchronous
- Form request is validated server-side.
- Celery task is enqueued immediately.
- User gets fast response while worker performs the DB write in background.
- Worker stores async submissions with `processed` or `failed` status.

Why Redis + Celery:
- simple and proven queue-based architecture
- decouples user latency from background processing
- easy path for retries, dedicated queues, and horizontal worker scaling

## 10. Anti-Bot Protections (Defense in Depth)
This implementation intentionally combines multiple layers:

1. Honeypot hidden field:
- Hidden `website` input in both sync and async forms.
- If populated, submission is rejected.

2. Rate limiting per IP:
- Flask uses `Flask-Limiter` with Redis backend.
- FastAPI uses `fastapi-limiter` with Redis backend.

3. Minimum submission time:
- Form issue timestamp is stored in session.
- Submissions faster than configured threshold are rejected.

4. CSRF:
- Flask uses `Flask-WTF` CSRF protection.
- FastAPI uses session-backed token generation/verification for HTML forms.

5. Fingerprint-ready field:
- Forms load Fingerprint JS agent and submit `requestId` and `visitorId` in hidden fields.
- Backend verifies `requestId` through Fingerprint Server API using `FPJS_SERVER_API_KEY`.
- Backend compares submitted `visitorId` with verified event `visitorId` to detect tampering.
- `fp_*` verification results are persisted in PostgreSQL for audit and analysis.
- `FPJS_FAIL_OPEN` controls behavior during verification outages.

No single control is complete. Combined layers reduce automated abuse risk while keeping implementation maintainable.

## 11. k6 Performance Testing
Run from `whitefly-task` directory after stack starts:

Flask scenario:
```bash
k6 run k6/flask_test.js
```

FastAPI scenario:
```bash
k6 run k6/fastapi_test.js
```

What scripts cover:
- `GET /` home page
- `POST /form-sync`
- `POST /form-async`
- status checks for expected responses

How to compare:
- Sync endpoint latency includes immediate DB insert.
- Async endpoint should often return quicker for user-facing latency, while work finalization happens in Celery worker.

## 12. Why Nginx in Front
Nginx provides:
- stable public entrypoint for both apps
- reverse proxy routing by prefix
- forwarding headers needed for client context
- baseline request limiting
- environment close to production setups used for load tests

## 13. Suggested Production Improvements
1. Add Alembic migrations and migration CI checks.
2. Add structured logging and centralized log aggregation.
3. Add Celery retries, dead-letter strategy, and monitoring.
4. Add stronger bot detection scoring and anomaly detection.
5. Add OpenTelemetry tracing and metrics dashboards.
6. Add TLS termination and secure cookies in production.
7. Add WAF/CDN integration for internet-facing deployment.
8. Split submission tables or add partitioning at higher scale.

## 14. Trade-offs and Engineering Notes
- A single shared `submissions` table keeps the demo concise and easy to compare across frameworks.
- SQLAlchemy `create_all` is used for simplicity in recruitment-task scope; production should prefer migrations.
- FastAPI CSRF is implemented explicitly for HTML forms to keep dependency footprint controlled.
- Session-based minimum-time checks are lightweight but should be combined with telemetry and fraud scoring in real systems.
