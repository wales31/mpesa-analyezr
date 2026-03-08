-- M-PESA Analyzer (normalized) schema for SQLite
-- Date: 2026-02-05
--
-- Notes:
-- - Enables foreign keys.
-- - Uses TEXT timestamps (UTC recommended).
-- - Includes triggers to keep updated_at current.

PRAGMA foreign_keys = ON;

-- =========================
-- Users
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE,
  full_name TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
  UPDATE users SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Accounts (M-PESA wallets)
-- =========================
CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'mpesa',
  label TEXT,
  msisdn TEXT,
  currency TEXT NOT NULL DEFAULT 'KES',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, provider, msisdn)
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts(user_id);

CREATE TRIGGER IF NOT EXISTS trg_accounts_updated_at
AFTER UPDATE ON accounts
FOR EACH ROW
BEGIN
  UPDATE accounts SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Categories
-- =========================
CREATE TABLE IF NOT EXISTS categories (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TRIGGER IF NOT EXISTS trg_categories_updated_at
AFTER UPDATE ON categories
FOR EACH ROW
BEGIN
  UPDATE categories SET updated_at = datetime('now') WHERE code = OLD.code;
END;

CREATE TABLE IF NOT EXISTS category_keywords (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category_code TEXT NOT NULL REFERENCES categories(code) ON DELETE CASCADE,
  keyword TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(category_code, keyword)
);

CREATE INDEX IF NOT EXISTS idx_category_keywords_keyword ON category_keywords(keyword);

CREATE TRIGGER IF NOT EXISTS trg_category_keywords_updated_at
AFTER UPDATE ON category_keywords
FOR EACH ROW
BEGIN
  UPDATE category_keywords SET updated_at = datetime('now') WHERE id = OLD.id;
END;

INSERT OR IGNORE INTO categories(code, name) VALUES
  ('uncategorized', 'Uncategorized'),
  ('food', 'Food'),
  ('transport', 'Transport'),
  ('rent', 'Rent'),
  ('bills', 'Bills'),
  ('airtime', 'Airtime'),
  ('betting', 'Betting'),
  ('shopping', 'Shopping');

-- =========================
-- Counterparties
-- =========================
CREATE TABLE IF NOT EXISTS counterparties (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  phone TEXT,
  paybill_number TEXT,
  till_number TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_counterparties_display_name ON counterparties(display_name);
CREATE INDEX IF NOT EXISTS idx_counterparties_phone ON counterparties(phone);

CREATE TRIGGER IF NOT EXISTS trg_counterparties_updated_at
AFTER UPDATE ON counterparties
FOR EACH ROW
BEGIN
  UPDATE counterparties SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Raw SMS ingestion (optional, sensitive)
-- =========================
CREATE TABLE IF NOT EXISTS sms_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  source TEXT NOT NULL DEFAULT 'mpesa_sms',
  message_hash TEXT NOT NULL,
  message_text TEXT,
  received_at TEXT,
  parse_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (parse_status IN ('pending', 'parsed', 'failed')),
  parse_error TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(account_id, message_hash)
);

CREATE INDEX IF NOT EXISTS idx_sms_messages_account_id ON sms_messages(account_id);
CREATE INDEX IF NOT EXISTS idx_sms_messages_received_at ON sms_messages(received_at);
CREATE INDEX IF NOT EXISTS idx_sms_messages_parse_status ON sms_messages(parse_status);

CREATE TRIGGER IF NOT EXISTS trg_sms_messages_updated_at
AFTER UPDATE ON sms_messages
FOR EACH ROW
BEGIN
  UPDATE sms_messages SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Transactions
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  sms_message_id INTEGER UNIQUE REFERENCES sms_messages(id) ON DELETE SET NULL,

  mpesa_reference TEXT,
  direction TEXT NOT NULL DEFAULT 'expense'
    CHECK (direction IN ('income', 'expense', 'transfer')),
  transaction_type TEXT,

  amount NUMERIC NOT NULL CHECK (amount >= 0),
  currency TEXT NOT NULL DEFAULT 'KES',

  category_code TEXT NOT NULL DEFAULT 'uncategorized' REFERENCES categories(code) ON DELETE RESTRICT,
  counterparty_id INTEGER REFERENCES counterparties(id) ON DELETE SET NULL,

  occurred_at TEXT,
  balance_after NUMERIC CHECK (balance_after IS NULL OR balance_after >= 0),
  fees NUMERIC CHECK (fees IS NULL OR fees >= 0),
  user_note TEXT,

  source TEXT NOT NULL DEFAULT 'mpesa_sms',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),

  UNIQUE(account_id, mpesa_reference)
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_occurred_at ON transactions(occurred_at);
CREATE INDEX IF NOT EXISTS idx_transactions_category_code ON transactions(category_code);
CREATE INDEX IF NOT EXISTS idx_transactions_direction ON transactions(direction);
CREATE INDEX IF NOT EXISTS idx_transactions_counterparty_id ON transactions(counterparty_id);

CREATE TRIGGER IF NOT EXISTS trg_transactions_updated_at
AFTER UPDATE ON transactions
FOR EACH ROW
BEGIN
  UPDATE transactions SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Budgets
-- =========================
CREATE TABLE IF NOT EXISTS budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,

  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  currency TEXT NOT NULL DEFAULT 'KES',
  planned_income NUMERIC NOT NULL DEFAULT 0 CHECK (planned_income >= 0),

  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),

  UNIQUE(account_id, period_start, period_end),
  CHECK (period_end > period_start)
);

CREATE INDEX IF NOT EXISTS idx_budgets_account_id ON budgets(account_id);
CREATE INDEX IF NOT EXISTS idx_budgets_period_start ON budgets(period_start);

CREATE TRIGGER IF NOT EXISTS trg_budgets_updated_at
AFTER UPDATE ON budgets
FOR EACH ROW
BEGIN
  UPDATE budgets SET updated_at = datetime('now') WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS budget_lines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,
  direction TEXT NOT NULL DEFAULT 'expense'
    CHECK (direction IN ('income', 'expense')),
  category_code TEXT NOT NULL REFERENCES categories(code) ON DELETE RESTRICT,
  planned_amount NUMERIC NOT NULL DEFAULT 0 CHECK (planned_amount >= 0),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(budget_id, direction, category_code)
);

CREATE INDEX IF NOT EXISTS idx_budget_lines_budget_id ON budget_lines(budget_id);
CREATE INDEX IF NOT EXISTS idx_budget_lines_category_code ON budget_lines(category_code);

CREATE TRIGGER IF NOT EXISTS trg_budget_lines_updated_at
AFTER UPDATE ON budget_lines
FOR EACH ROW
BEGIN
  UPDATE budget_lines SET updated_at = datetime('now') WHERE id = OLD.id;
END;

-- =========================
-- Tags (optional)
-- =========================
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, name)
);

CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);

CREATE TRIGGER IF NOT EXISTS trg_tags_updated_at
AFTER UPDATE ON tags
FOR EACH ROW
BEGIN
  UPDATE tags SET updated_at = datetime('now') WHERE id = OLD.id;
END;

CREATE TABLE IF NOT EXISTS transaction_tags (
  transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (transaction_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_transaction_tags_tag_id ON transaction_tags(tag_id);
