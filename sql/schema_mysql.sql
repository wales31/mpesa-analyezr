-- M-PESA Analyzer schema for MySQL/MariaDB
-- Date: 2026-02-05
--
-- Notes:
-- - Uses InnoDB + utf8mb4.

-- Optional (recommended) session settings:
-- SET time_zone = '+00:00';
-- SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
-- SET NAMES utf8mb4;
--
-- database creation:
-- CREATE DATABASE IF NOT EXISTS mpesa_analyzer
--   CHARACTER SET utf8mb4
--   COLLATE utf8mb4_unicode_ci;
-- USE mpesa_analyzer;

-- =========================
-- Users
-- =========================
CREATE TABLE IF NOT EXISTS users (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NULL,
  full_name VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Accounts (M-PESA wallets)
-- =========================
CREATE TABLE IF NOT EXISTS accounts (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  provider VARCHAR(32) NOT NULL DEFAULT 'mpesa',
  label VARCHAR(128) NULL,
  msisdn VARCHAR(32) NULL,
  currency CHAR(3) NOT NULL DEFAULT 'KES',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_accounts_user_id (user_id),
  UNIQUE KEY uq_accounts_user_provider_msisdn (user_id, provider, msisdn),
  CONSTRAINT fk_accounts_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Categories
-- =========================
CREATE TABLE IF NOT EXISTS categories (
  code VARCHAR(64) NOT NULL,
  name VARCHAR(128) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (code),
  UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Optional: keywords that can drive categorization rules (v1 categorizer is code-based).
CREATE TABLE IF NOT EXISTS category_keywords (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  category_code VARCHAR(64) NOT NULL,
  keyword VARCHAR(128) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_category_keywords_cat_kw (category_code, keyword),
  KEY ix_category_keywords_keyword (keyword),
  CONSTRAINT fk_category_keywords_category
    FOREIGN KEY (category_code) REFERENCES categories (code)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed baseline categories (safe to re-run).
INSERT IGNORE INTO categories (code, name) VALUES
  ('uncategorized', 'Uncategorized'),
  ('food', 'Food'),
  ('transport', 'Transport'),
  ('rent', 'Rent'),
  ('bills', 'Bills'),
  ('airtime', 'Airtime'),
  ('betting', 'Betting'),
  ('shopping', 'Shopping');

-- =========================
-- Counterparties (recipients / senders / businesses)
-- =========================
CREATE TABLE IF NOT EXISTS counterparties (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  display_name VARCHAR(255) NOT NULL,
  phone VARCHAR(32) NULL,
  paybill_number VARCHAR(32) NULL,
  till_number VARCHAR(32) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_counterparties_display_name (display_name),
  KEY ix_counterparties_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Raw SMS ingestion (optional, sensitive)
-- =========================
CREATE TABLE IF NOT EXISTS sms_messages (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  account_id BIGINT UNSIGNED NOT NULL,
  source VARCHAR(32) NOT NULL DEFAULT 'mpesa_sms',
  message_hash CHAR(64) NOT NULL,
  message_text MEDIUMTEXT NULL,
  received_at DATETIME NULL,
  parse_status ENUM('pending', 'parsed', 'failed') NOT NULL DEFAULT 'pending',
  parse_error VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_sms_messages_account_hash (account_id, message_hash),
  KEY ix_sms_messages_account_id (account_id),
  KEY ix_sms_messages_received_at (received_at),
  KEY ix_sms_messages_parse_status (parse_status),
  CONSTRAINT fk_sms_messages_account
    FOREIGN KEY (account_id) REFERENCES accounts (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Transactions
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  account_id BIGINT UNSIGNED NOT NULL,
  sms_message_id BIGINT UNSIGNED NULL,

  mpesa_reference VARCHAR(32) NULL,
  direction ENUM('income', 'expense', 'transfer') NOT NULL DEFAULT 'expense',
  transaction_type VARCHAR(32) NULL,

  amount DECIMAL(12, 2) NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'KES',

  category_code VARCHAR(64) NOT NULL DEFAULT 'uncategorized',
  counterparty_id BIGINT UNSIGNED NULL,

  occurred_at DATETIME NULL,
  balance_after DECIMAL(12, 2) NULL,
  fees DECIMAL(12, 2) NULL,
  user_note TEXT NULL,

  source VARCHAR(32) NOT NULL DEFAULT 'mpesa_sms',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (id),
  UNIQUE KEY uq_transactions_account_reference (account_id, mpesa_reference),
  UNIQUE KEY uq_transactions_sms_message (sms_message_id),
  KEY ix_transactions_account_id (account_id),
  KEY ix_transactions_occurred_at (occurred_at),
  KEY ix_transactions_category_code (category_code),
  KEY ix_transactions_direction (direction),
  KEY ix_transactions_counterparty_id (counterparty_id),

  CONSTRAINT fk_transactions_account
    FOREIGN KEY (account_id) REFERENCES accounts (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_transactions_sms_message
    FOREIGN KEY (sms_message_id) REFERENCES sms_messages (id)
    ON DELETE SET NULL,
  CONSTRAINT fk_transactions_category
    FOREIGN KEY (category_code) REFERENCES categories (code)
    ON DELETE RESTRICT,
  CONSTRAINT fk_transactions_counterparty
    FOREIGN KEY (counterparty_id) REFERENCES counterparties (id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Budgets
-- =========================
CREATE TABLE IF NOT EXISTS budgets (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  account_id BIGINT UNSIGNED NOT NULL,

  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'KES',
  planned_income DECIMAL(12, 2) NOT NULL DEFAULT 0,

  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_budgets_user_account_period (user_id, account_id, period_start, period_end),
  KEY ix_budgets_user_id (user_id),
  KEY ix_budgets_account_id (account_id),
  KEY ix_budgets_period_start (period_start),
  CONSTRAINT fk_budgets_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_budgets_account
    FOREIGN KEY (account_id) REFERENCES accounts (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS budget_lines (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  budget_id BIGINT UNSIGNED NOT NULL,
  direction ENUM('income', 'expense') NOT NULL DEFAULT 'expense',
  category_code VARCHAR(64) NOT NULL,
  planned_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_budget_lines_budget_dir_cat (budget_id, direction, category_code),
  KEY ix_budget_lines_budget_id (budget_id),
  KEY ix_budget_lines_category_code (category_code),
  CONSTRAINT fk_budget_lines_budget
    FOREIGN KEY (budget_id) REFERENCES budgets (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_budget_lines_category
    FOREIGN KEY (category_code) REFERENCES categories (code)
    ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =========================
-- Tags (optional)
-- =========================
CREATE TABLE IF NOT EXISTS tags (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  name VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_tags_user_name (user_id, name),
  KEY ix_tags_user_id (user_id),
  CONSTRAINT fk_tags_user
    FOREIGN KEY (user_id) REFERENCES users (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- foreign key has is incorrectly formated
-- dubug
CREATE TABLE IF NOT EXISTS transaction_tags (
  transaction_id BIGINT UNSIGNED NOT NULL,
  tag_id BIGINT UNSIGNED NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (transaction_id, tag_id),
  KEY ix_transaction_tags_tag_id (tag_id),
  CONSTRAINT fk_transaction_tags_transaction
    FOREIGN KEY (transaction_id) REFERENCES transactions (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_transaction_tags_tag
    FOREIGN KEY (tag_id) REFERENCES tags (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
