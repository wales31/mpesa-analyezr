# M-PESA Spending Analyzer (v1)

Parse M-PESA SMS messages into structured transactions, categorize them, store them in a local database, and surface
spending insights through a lightweight web UI and an in-progress mobile app foundation.

## Current Status (2026-03-08)

Implemented:

- **Backend (FastAPI)**: health check, auth (`register/login/me`), analyze single/bulk messages, list/delete transactions, summary totals, insights
- **Parsing (v1)**: extracts `amount`, `occurred_at`, optional `reference`, and best-effort `recipient` + `transaction_type`
- **Categorization (v1)**: keyword-based categories (`food`, `transport`, `rent`, `bills`, `airtime`, `betting`, `shopping`)
- **Database**: MySQL/MariaDB (XAMPP-friendly) or SQLite fallback (`backend/database.db`)
- **Web frontend (static HTML + JS)**: auth, ingest messages, view summary/insights, view transactions, budget limit + planner flows
- **Mobile app (Expo + React Native)**: API base configuration, register/login, persisted session, authenticated summary screen

Not implemented yet (planned):

- More comprehensive M-PESA message format coverage and stronger categorization rules
- Full mobile spending-tracker workflows (message ingestion, transaction review, budgeting, notifications)
- Richer budget planning/reporting APIs beyond the current monthly limit workflow

## Quickstart

### 1) Install backend dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure MySQL (XAMPP)

If you want MySQL instead of SQLite, set:

```bash
export MPESA_DB_BACKEND=mysql
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=
export MYSQL_DATABASE=mpesa_analyzer
```

You can also set a full URL:

```bash
export MPESA_DATABASE_URL='mysql+pymysql://root@127.0.0.1:3306/mpesa_analyzer?charset=utf8mb4'
```

### 3) Initialize the database (optional)

Tables are created automatically on API startup, but you can also run:

```bash
python backend/init_db.py
```

### 4) Run the API

```bash
uvicorn backend.main:app --reload
```

Open:

- API health: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`

### 5) Run the frontend

Serve the static files:

```bash
cd frontend/src
python -m http.server 5173
```

Open `http://127.0.0.1:5173/` in your browser.

If you open the frontend from another device on your LAN, use `http://<your-computer-ip>:5173/`. The frontend now
defaults to `http://<same-host>:8000` for private-network hosts, so it aligns with the API when both are running on
your machine.

### 6) Register and sign in

Open `http://127.0.0.1:5173/auth.html`, create an account, then sign in.
The frontend stores the bearer token in `localStorage` and sends it as:

`Authorization: Bearer <token>`

## Configuration

### Database

MySQL/MariaDB is recommended for online/mobile/web usage.
SQLite stores data at `backend/database.db` when MySQL is not configured.

To use MySQL/MariaDB, set one of:

- `MPESA_DATABASE_URL` / `DATABASE_URL` (full SQLAlchemy URL), or
- `MPESA_DB_BACKEND=mysql` and the `MYSQL_*` variables (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`)

If MySQL is configured but unreachable, startup falls back to SQLite by default. Set `MPESA_DB_FALLBACK_TO_SQLITE=0` to force a hard failure instead.

See `docs/database.md`.

### API and CORS

Set `MPESA_CORS_ORIGINS` to a comma-separated list of allowed frontend origins in production, for example:

```bash
export MPESA_CORS_ORIGINS='https://your-domain.com,https://www.your-domain.com'
```

Use `*` only for local testing.

For local LAN development, private-network browser origins such as `http://192.168.x.x:5173` are accepted by default.
If you want stricter control, set `MPESA_CORS_ORIGIN_REGEX` explicitly or define exact `MPESA_CORS_ORIGINS`.

## Go Live (Docker)

This repo includes a production compose stack:

- `web` (Nginx): serves `frontend/src` and proxies `/api/*` to backend
- `api` (FastAPI + Uvicorn workers)
- `db` (MySQL 8)

### 1) Prepare environment

```bash
cp .env.example .env
```

Edit `.env` and set strong DB passwords plus your real domain in `MPESA_CORS_ORIGINS`.

### 2) Start production stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### 3) Verify services

```bash
docker compose -f docker-compose.prod.yml ps
curl http://127.0.0.1:${WEB_PORT:-80}/api/
```

### 4) Point DNS and add HTTPS

Point your domain A record to your server IP, then terminate TLS with your edge/load balancer (for example, Cloudflare, Caddy, Nginx+Certbot, or your cloud provider's HTTPS LB).

### 5) Access app

Open `http://<your-domain>/auth.html` (or `https://<your-domain>/auth.html` after TLS is configured).

The frontend defaults to:

- `http://127.0.0.1:8000` in local development
- `/api` when served from a non-localhost domain

## Docs

- API: `docs/api.md` (or the live Swagger UI at `/docs`)
- Database: `docs/database.md`
- Architecture: `docs/architecture.md`
- ER diagram: `docs/er_diagram.md`

## Privacy note

Treat SMS content as sensitive. Avoid committing real messages into git history.
