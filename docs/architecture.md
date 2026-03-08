# Architecture

## Overview

The system follows a simple 3-layer architecture:

Web frontend + mobile app foundation
→ Backend API (FastAPI)
→ Database (SQLite/MySQL)

## Components

### Clients (Presentation)

Purpose: collect SMS messages, call the API, and render summaries.

Current implementation:

- Static HTML/CSS/JS under `frontend/src/`
- Bootstrap 5 (CDN)
- Budget page keeps planner entries in browser `localStorage`, while monthly budget limit uses backend `GET/PUT /budget/limit`
- API base defaults to `http://127.0.0.1:8000` and can be overridden via `window.MPESA_API_BASE`
- Auth page at `frontend/src/auth.html` stores bearer token in `localStorage`
- React Native mobile app under `mobile/`
- Mobile auth flow supports API base configuration, register/login, secure session persistence, and `/summary`

### Backend API (Application)

Purpose: parse messages, categorize transactions, persist data, and return summaries/insights.

Core modules:

- `backend/main.py` — FastAPI routes
- `backend/api/endpoints/auth.py` — registration/login/current-user endpoints
- `backend/parser.py` — SMS → structured fields (v1 patterns)
- `backend/categorizer.py` — keyword-based category assignment (v1)
- `backend/insights.py` — lightweight warnings/highlights (v1)
- `backend/models.py` — SQLAlchemy tables (`users`, `auth_tokens`, `transactions`, `budgets`, `budget_lines`, `user_budget_limits`, `notifications`)
- `backend/database.py` — DB URL resolution + engine/session + `init_db()`
- `backend/init_db.py` — helper script to create tables

### Database (Data)

Recommended: MySQL/MariaDB for online usage.

Default fallback: SQLite file at `backend/database.db`.

Optional: MySQL/MariaDB via env vars (see `docs/database.md`).

Tables:

- `transactions` — normalized transaction records used by the dashboard
- `user_budget_limits` — per-user monthly budget threshold data exposed via API
- `notifications` — generated budget/insight alerts
- `budgets`, `budget_lines` — forward-looking schema for richer planning workflows

## Data Flow (v1)

1) User opens the web client or mobile app
2) User registers/signs in to receive a bearer token
3) User pastes one or more SMS messages in the web UI, or uses the mobile app for authenticated summary access
4) Client calls `POST /ingestion/messages` (or legacy `POST /analyze`, `POST /analyze/bulk`) with `Authorization: Bearer <token>`
5) Backend parses → categorizes → stores normalized records with ingestion metadata (mode, batch, source message id)
6) Client calls `GET /summary`, `GET /insights`, `GET /transactions`, and budget/notification endpoints to render analytics

## Repository Structure (current)

```
mpesa-analyzer/
├── backend/
│   ├── main.py
│   ├── parser.py
│   ├── categorizer.py
│   ├── insights.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── init_db.py
├── frontend/
│   └── src/
│       ├── index.html
│       ├── spending.html
│       ├── dashboard.html
│       ├── budget.html
│       ├── app.js
│       ├── init.js
│       ├── spending.js
│       ├── dashboard.js
│       ├── budget.js
│       └── styles.css
├── mobile/
│   ├── App.tsx
│   └── src/
│       ├── api/
│       ├── auth/
│       ├── config/
│       ├── screens/
│       └── storage/
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── database.md
├── requirements.txt
└── structure.sql
```

## Next (planned)

- Full spending-tracker workflows in the mobile app (ingestion, transactions, insights, budget, notifications)
- Richer backend budget planning endpoints using the existing `budgets` / `budget_lines` tables
- Android inbox reader + statement parser posting to `/ingestion/messages` in `inbox_sync` or `statement_import` mode
- More robust M-PESA message parsing coverage + improved categorization rules
