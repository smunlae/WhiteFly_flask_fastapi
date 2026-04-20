# WhiteFly Task
[EN](README.md) | [PL](README.pl.md)

Rozwiązanie rekrutacyjne w stylu produkcyjnym z dwoma osobnymi aplikacjami:
- Flask (`/flask`)
- FastAPI (`/fastapi`)

Obie implementują:
- stronę Hello World
- formularz synchroniczny -> bezpośredni zapis do PostgreSQL
- formularz asynchroniczny -> Celery + Redis -> zapis przez worker
- walidację po stronie serwera
- ochronę anty-bot
- reverse proxy Nginx
- testy wydajności k6

## Stack
- Python 3.12
- Flask, FastAPI
- SQLAlchemy, PostgreSQL
- Celery, Redis
- Nginx
- Docker Compose
- k6

## Uruchomienie
```bash
cp .env.example .env
docker compose up -d --build
```

Adresy:
- Flask: `http://localhost:8080/flask/`
- FastAPI: `http://localhost:8080/fastapi/`

Jeśli pojawi się `502`, zrestartuj nginx po odtworzeniu kontenerów web:
```bash
docker compose restart nginx
```

## Wymagane zmienne środowiskowe
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

## Architektura
- Routing Nginx:
  - `/flask/` -> Flask web
  - `/fastapi/` -> FastAPI web
- Redis służy jako broker/backend Celery i storage limitów.
- PostgreSQL przechowuje wszystkie zgłoszenia w jednej tabeli.
- Flow async:
  - web waliduje i wrzuca payload do kolejki
  - worker zapisuje rekord jako `processed` lub `failed`

## Główne endpointy
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

## Ochrona anty-bot
- ukryte pole honeypot
- rate limiting per IP
- minimalny czas wysyłki formularza
- CSRF (Flask-WTF / tokeny w FastAPI)
- FingerprintJS:
  - frontend wysyła `requestId` i `visitorId`
  - backend weryfikuje przez Fingerprint Server API
  - wynik jest zapisywany w kolumnach `fp_*`

## Testy wydajności
```bash
k6 run k6/flask_test.js
k6 run k6/fastapi_test.js
```

Porównanie:
- Sync: opóźnienie zawiera bezpośredni zapis do DB
- Async: odpowiedź zwykle szybsza, zapis kończy worker w tle

## Raport testów Railway (20 kwietnia 2026)
Adres testowany:
- `https://nginx-production-2ce8.up.railway.app`

### Scenariusz A: wysoki ruch (10 VUs, 30s)
Flask (`/flask`):
- checks: `84.44%` (152/180), failed `15.55%`
- http_req_failed: `14.00%` (42/300)
- latency: avg `71.52ms`, p95 `96.79ms`

FastAPI (`/fastapi`):
- checks: `44.44%` (80/180), failed `55.55%`
- http_req_failed: `33.33%` (100/300)
- latency: avg `79.39ms`, p95 `95.85ms`

Interpretacja:
- Ten scenariusz potwierdza działanie zabezpieczeń anty-abuse.
- FastAPI ma limiter endpointów (`10 req / 60s` na IP), więc wiele POST zostało celowo odrzuconych.
- W ruchu burst widać też odrzucenia po stronie Nginx/Flask.

### Scenariusz B: baseline do uczciwego porównania (1 VU, 60s)
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

Wnioski końcowe:
- Oba deploymenty są stabilne za Nginx przy ruchu nie-abusywnym.
- Flask i FastAPI mają bardzo podobną wydajność baseline w tym środowisku.
- Błędy w scenariuszu wysokiego ruchu wynikały z limiterów/ochrony anty-bot, a nie z awarii głównej logiki biznesowej.
- Do raportu końcowego warto pokazać oba scenariusze: baseline (wydajność) i abuse (zachowanie zabezpieczeń).

## Uwagi
- Flask i FastAPI są celowo oddzielone folderami i runtime.
- `.env` jest wykluczony z gita.
- Projekt jest przygotowany pod Docker i testy za reverse proxy.
