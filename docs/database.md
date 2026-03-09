## Database Overview

The backend uses SQLAlchemy and supports:

- **MySQL/MariaDB** (recommended for mobile/web deployments and if you're running XAMPP)
- **SQLite** (default; zero setup)

SQLite stores data in a local file at:

- `backend/database.db`

Database URL resolution (highest → lowest priority):

1) `MPESA_DATABASE_URL` / `DATABASE_URL` (full SQLAlchemy URL)
2) `MPESA_DB_BACKEND=mysql|mariadb` (build from `MYSQL_*`)
3) SQLite file under `backend/` (default)

## MySQL / XAMPP setup

1) Start **MySQL/MariaDB** in XAMPP.
2) Create a database (example): `mpesa_analyzer`
3) Point the backend to MySQL using either a full URL or env vars.

### Option A: Full URL (recommended)

Set `MPESA_DATABASE_URL` (or `DATABASE_URL`) to a SQLAlchemy MySQL URL, for example:

`mysql+pymysql://root@127.0.0.1:3306/mpesa_analyzer?charset=utf8mb4`

### Option B: Component env vars

Set `MPESA_DB_BACKEND=mysql` and provide the `MYSQL_*` variables:

- `MYSQL_HOST` (default `127.0.0.1`)
- `MYSQL_PORT` (default `3306`)
- `MYSQL_USER` (default `root`)
- `MYSQL_PASSWORD` (default empty)
- `MYSQL_DATABASE` (default `mpesa_analyzer`)

Note: `MYSQL_*` variables alone do not switch backends; set `MPESA_DB_BACKEND=mysql` (or use a full database URL).


### Automatic fallback for local development

When MySQL is explicitly configured but unreachable, the backend automatically falls back to SQLite by default so local startup still works.

- Disable fallback by setting `MPESA_DB_FALLBACK_TO_SQLITE=0`
- Keep fallback enabled with `MPESA_DB_FALLBACK_TO_SQLITE=1` (default)

## Connecting with the MySQL CLI (Linux / XAMPP)

If you see an error like:

`ERROR 2002 (HY000): Can't connect to local server through socket '/run/mysqld/mysqld.sock'`

it usually means you’re connecting to the wrong **Unix socket path** (common when using XAMPP on Linux).

Use one of:

- TCP (forces network connection): `mysql -u root -p -h 127.0.0.1 -P 3306`
- XAMPP socket: `mysql -u root -p --socket=/opt/lampp/var/mysql/mysql.sock`
- XAMPP mysql client: `/opt/lampp/bin/mysql -u root -p`

If MySQL isn’t running yet in XAMPP, start it first (Linux):

`sudo /opt/lampp/lampp startmysql`

## Tables

### `users`

Application users for login/registration.

Key fields:

- `id` (string primary key)
- `email` (unique)
- `username` (unique)
- `password_hash` (PBKDF2 hash)
- `is_active`

### `auth_tokens`

Bearer access tokens (stored as SHA256 hashes).

Key fields:

- `user_id`
- `token_hash` (unique)
- `expires_at`
- `revoked_at`

### `transactions`

Stores normalized M-PESA transactions (and optional user context).

Key fields:

- `amount` (numeric)
- `currency` (defaults to `KES`)
- `direction` (`income` | `expense` | `transfer`) — used for budgeting math
- `category` (defaults to `uncategorized`)
- `transaction_type` (e.g., `sent`, `received`, `pay`, `paybill`)
- `recipient`, `reference`, `occurred_at`
- `user_note` — optional “what this was for” from the UI
- `user_id` — transaction owner (resolved from bearer token)
- `ingestion_mode` — `single_upload` | `inbox_sync` | `statement_import`
- `ingestion_batch_id` — groups one sync/import run
- `source_message_id` — Android SMS id or statement row id when provided
- `source_received_at` — original message timestamp from device/import
- `source` — ingestion source label (e.g., `manual_upload`, `android_inbox`)

Indexes:

- `occurred_at`, `category`, `direction`, `user_id`
- `ingestion_mode`, `ingestion_batch_id`
- `(user_id, source_message_id)`

### `budgets`

Stores budget headers for a time period (v1 uses monthly budgets).

Note: The v1 UI budget plan is currently stored in browser `localStorage`. Backend budget endpoints are planned, and
these tables are already present to support that.

Key fields:

- `period_start` / `period_end` (dates)
- `planned_income`
- `currency`

### `budget_lines`

Stores budget line items for categories.

Key fields:

- `budget_id` → `budgets.id`
- `direction` (`income` | `expense`) — v1 uses `expense` lines
- `category`
- `planned_amount`

## Initialization

Tables are created automatically when the API starts (see `backend/main.py` startup hook).

You can also create them manually with:

- `python backend/init_db.py` (recommended), or
- `backend/database.py:init_db()` in a Python shell, or
- the DDL in `structure.sql` (legacy v1), or
- the normalized DDL files:
  - `sql/schema_mysql.sql` (MySQL/MariaDB)
  - `sql/schema_sqlite.sql` (SQLite)

See also: `docs/er_diagram.md`.

Note: The normalized schema files are a target design. If you apply them manually, align the backend SQLAlchemy models
to the same structure (or run migrations) to avoid schema drift.
