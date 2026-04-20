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

## Uwagi
- Flask i FastAPI są celowo oddzielone folderami i runtime.
- `.env` jest wykluczony z gita.
- Projekt jest przygotowany pod Docker i testy za reverse proxy.
