-- SQLite schema for M-PESA Spending Analyzer
-- Note: Treat transaction data as sensitive.

PRAGMA foreign_keys = ON;

-- =========================
-- Transactions
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  amount NUMERIC NOT NULL,
  currency TEXT NOT NULL DEFAULT 'KES',

  -- direction enables budgeting math
  direction TEXT NOT NULL DEFAULT 'expense'
    CHECK (direction IN ('income', 'expense', 'transfer')),

  category TEXT NOT NULL DEFAULT 'uncategorized',
  transaction_type TEXT,
  recipient TEXT,
  reference TEXT UNIQUE,
  occurred_at TEXT,

  -- user-provided context to improve categorization
  user_note TEXT,

  source TEXT NOT NULL DEFAULT 'mpesa_sms',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_occurred_at ON transactions(occurred_at);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_direction ON transactions(direction);

-- =========================
-- Budgets (monthly, default)
-- =========================
CREATE TABLE IF NOT EXISTS budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- period boundaries (ISO dates, YYYY-MM-DD). For monthly budgets:
  -- period_start = first day of month
  -- period_end   = first day of next month
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,

  currency TEXT NOT NULL DEFAULT 'KES',
  planned_income NUMERIC NOT NULL DEFAULT 0,

  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_budgets_period ON budgets(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_budgets_period_start ON budgets(period_start);

CREATE TABLE IF NOT EXISTS budget_lines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  budget_id INTEGER NOT NULL REFERENCES budgets(id) ON DELETE CASCADE,

  direction TEXT NOT NULL DEFAULT 'expense'
    CHECK (direction IN ('income', 'expense')),

  category TEXT NOT NULL,
  planned_amount NUMERIC NOT NULL DEFAULT 0,

  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_budget_lines_budget_dir_cat
  ON budget_lines(budget_id, direction, category);
CREATE INDEX IF NOT EXISTS idx_budget_lines_budget_id ON budget_lines(budget_id);
