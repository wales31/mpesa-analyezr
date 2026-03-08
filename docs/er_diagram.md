# ER Diagram (Normalized Schema)

This diagram matches the normalized schema files:

- `sql/schema_mysql.sql`
- `sql/schema_sqlite.sql`

```mermaid
erDiagram
  USERS {
    BIGINT id PK
    VARCHAR email UK
    VARCHAR full_name
    DATETIME created_at
    DATETIME updated_at
  }

  ACCOUNTS {
    BIGINT id PK
    BIGINT user_id FK
    VARCHAR provider
    VARCHAR label
    VARCHAR msisdn
    CHAR currency
    DATETIME created_at
    DATETIME updated_at
  }

  CATEGORIES {
    VARCHAR code PK
    VARCHAR name UK
    DATETIME created_at
    DATETIME updated_at
  }

  CATEGORY_KEYWORDS {
    BIGINT id PK
    VARCHAR category_code FK
    VARCHAR keyword
    DATETIME created_at
    DATETIME updated_at
  }

  COUNTERPARTIES {
    BIGINT id PK
    VARCHAR display_name
    VARCHAR phone
    VARCHAR paybill_number
    VARCHAR till_number
    DATETIME created_at
    DATETIME updated_at
  }

  SMS_MESSAGES {
    BIGINT id PK
    BIGINT account_id FK
    VARCHAR source
    CHAR message_hash
    DATETIME received_at
    VARCHAR parse_status
    VARCHAR parse_error
    DATETIME created_at
    DATETIME updated_at
  }

  TRANSACTIONS {
    BIGINT id PK
    BIGINT account_id FK
    BIGINT sms_message_id FK
    VARCHAR mpesa_reference
    VARCHAR direction
    VARCHAR transaction_type
    DECIMAL amount
    CHAR currency
    VARCHAR category_code FK
    BIGINT counterparty_id FK
    DATETIME occurred_at
    DECIMAL balance_after
    DECIMAL fees
    TEXT user_note
    DATETIME created_at
    DATETIME updated_at
  }

  BUDGETS {
    BIGINT id PK
    BIGINT account_id FK
    DATE period_start
    DATE period_end
    CHAR currency
    DECIMAL planned_income
    DATETIME created_at
    DATETIME updated_at
  }

  BUDGET_LINES {
    BIGINT id PK
    BIGINT budget_id FK
    VARCHAR direction
    VARCHAR category_code FK
    DECIMAL planned_amount
    DATETIME created_at
    DATETIME updated_at
  }

  TAGS {
    BIGINT id PK
    BIGINT user_id FK
    VARCHAR name
    DATETIME created_at
    DATETIME updated_at
  }

  TRANSACTION_TAGS {
    BIGINT transaction_id PK, FK
    BIGINT tag_id PK, FK
    DATETIME created_at
  }

  USERS ||--o{ ACCOUNTS : has
  ACCOUNTS ||--o{ SMS_MESSAGES : receives
  ACCOUNTS ||--o{ TRANSACTIONS : records

  CATEGORIES ||--o{ CATEGORY_KEYWORDS : has
  CATEGORIES ||--o{ TRANSACTIONS : categorizes
  CATEGORIES ||--o{ BUDGET_LINES : planned_for

  COUNTERPARTIES o|--o{ TRANSACTIONS : involved_in
  SMS_MESSAGES o|--o| TRANSACTIONS : parses_to

  ACCOUNTS ||--o{ BUDGETS : plans
  BUDGETS ||--o{ BUDGET_LINES : contains

  USERS ||--o{ TAGS : owns
  TAGS ||--o{ TRANSACTION_TAGS : used_in
  TRANSACTIONS ||--o{ TRANSACTION_TAGS : tagged_by
```

## Notes

- `sms_messages` is optional (you can store only a hash for dedupe, or omit message storage entirely for privacy).
- `transactions.category_code` defaults to `uncategorized` and references `categories.code`.
- Budgets are modeled as a header (`budgets`) and line items (`budget_lines`) per category and direction.
