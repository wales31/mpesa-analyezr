1. Overview

 REST API 
 
The API receives transaction message data, converts it into structured transaction records, and returns summaries and insights for visualization.

Goals

Provide a simple interface for ingesting transaction messages

Return structured outputs suitable for dashboards and reporting

Support bulk processing for meaningful summaries

Keep internals (parsing and categorization logic) abstracted from clients


2. Conventions
2.1 Content Types

All requests and responses use JSON unless otherwise stated.

Request header:

Content-Type: application/json

Authentication header (required for protected endpoints):

Authorization: Bearer <access_token>

Public endpoints:

- GET /
- POST /auth/register
- POST /auth/login

Local client notes:

- Browser UI on `localhost` or a LAN IP defaults to the backend on the same host at port `8000`.
- Private-network browser origins such as `http://192.168.x.x:5173` are accepted by default in local development.
- Android emulator usually reaches the backend at `http://10.0.2.2:8000`.
- iOS simulator usually reaches the backend at `http://127.0.0.1:8000`.
- A physical phone must use a reachable LAN IP or USB port reverse.

Note: `X-User-ID` is only accepted when `MPESA_ALLOW_LEGACY_USER_HEADER=true` is set on the backend.

2.2 Response Format

Success responses return data under stable keys.
Error responses return an error message (FastAPI uses `detail`).

Error format (typical)

{ "detail": "Human readable error message" }

2.3 Date/Time Format

All timestamps use ISO 8601 format.
Example:

"2026-02-03T10:15:30Z"
"2026-02-03T10:15:30+03:00"

3. Data Models
3.1 Transaction (Output)

A normalized transaction record returned by the API.

{
  "id": 1,
  "amount": 500.0,
  "currency": "KES",
  "category": "uncategorized",
  "direction": "expense",
  "transaction_type": "sent",
  "recipient": "JOHN DOE",
  "reference": "QBC123XYZ",
  "occurred_at": "2026-02-03T10:15:30+03:00",
  "date": "2026-02-03",
  "time": "10:15",
  "user_note": "lunch",
  "ingestion_mode": "single_upload",
  "ingestion_batch_id": "single_upload-bacd33012e2a",
  "source_message_id": "android-sms-19495",
  "source_received_at": "2026-02-03T10:15:30+03:00",
  "source": "manual_upload"
}


Field Notes

category may be "uncategorized" when classification is not available.

reference may be null/omitted if not present in the input.

recipient may be null/omitted depending on transaction type.

direction is one of: income | expense | transfer.

date/time are convenience fields derived from occurred_at.

user_note is optional user-provided context (what the money was for) that can improve categorization.

ingestion_mode tracks how the record entered the backend (`single_upload`, `inbox_sync`, `statement_import`).

ingestion_batch_id groups one sync/import session for retries and auditing.

source_message_id stores the Android SMS id (or statement row id) when available.

source_received_at stores the original device/statement timestamp if provided by the client.

4. Endpoints
4.0 Register
POST /auth/register

Purpose: Create a new user and return an access token.

Request Body

{
  "email": "you@example.com",
  "username": "yourname",
  "password": "YourStrongPassword123"
}

Response 201

{
  "access_token": "<token>",
  "token_type": "bearer",
  "expires_at": "2026-02-08T12:00:00Z",
  "user": {
    "id": "user_abc123",
    "email": "you@example.com",
    "username": "yourname"
  }
}

4.0.1 Login
POST /auth/login

Purpose: Sign in with email or username and return an access token.

Request Body

{
  "identifier": "you@example.com",
  "password": "YourStrongPassword123"
}

Response 200

{
  "access_token": "<token>",
  "token_type": "bearer",
  "expires_at": "2026-02-08T12:00:00Z",
  "user": {
    "id": "user_abc123",
    "email": "you@example.com",
    "username": "yourname"
  }
}

4.0.2 Current User
GET /auth/me

Purpose: Verify token and return the signed-in user.

Response 200

{
  "id": "user_abc123",
  "email": "you@example.com",
  "username": "yourname"
}

4.1 Health Check
GET /

Purpose: Confirm API is running.

Response 200

{ "message": "M-PESA Analyzer API Running" }
4.2 Analyze Single Message
POST /analyze

Purpose: Ingest a single transaction message and return a structured transaction.

Request Body

{
  "message": "Confirmed. Ksh500.00 sent to JOHN DOE 0712345678 on 2/2/26 at 9:14 AM.",
  "user_note": "lunch"
}


Response 200

{
  "stored": true,
  "transaction": {
    "id": 12,
    "amount": 500.0,
    "currency": "KES",
    "category": "uncategorized",
    "direction": "expense",
    "transaction_type": "sent",
    "recipient": "JOHN DOE",
    "reference": null,
    "occurred_at": "2026-02-02T09:14:00+03:00",
    "date": "2026-02-02",
    "time": "09:14",
    "user_note": "lunch",
    "ingestion_mode": "single_upload",
    "ingestion_batch_id": null,
    "source_message_id": null,
    "source_received_at": null,
    "source": "manual_upload"
  }
}

Notes

- If a reference code is present and already stored, the API returns `stored=false` and the existing transaction.


Response 400

{ "detail": "Message could not be processed." }

4.3 Analyze Bulk Messages
POST /analyze/bulk

Purpose: Ingest multiple messages and return processing results.

Request Body

{
  "messages": [
    "Confirmed. Ksh500.00 sent to JOHN DOE 0712345678 on 2/2/26 at 9:14 AM.",
    "Confirmed. Ksh250.00 paid to ABC SHOP on 2/2/26 at 4:22 PM."
  ],
  "user_note": "groceries"
}


Response 200

{
  "stored": 2,
  "failed": 0,
  "transactions": [
    {
      "id": 13,
      "amount": 500.0,
      "currency": "KES",
      "category": "uncategorized",
      "direction": "expense",
      "transaction_type": "sent",
      "recipient": "JOHN DOE",
      "reference": null,
      "occurred_at": "2026-02-03T10:18:10Z",
      "date": "2026-02-03",
      "time": "10:18",
      "user_note": "groceries",
      "ingestion_mode": "single_upload",
      "ingestion_batch_id": null,
      "source_message_id": null,
      "source_received_at": null,
      "source": "manual_upload"
    },
    {
      "id": 14,
      "amount": 250.0,
      "currency": "KES",
      "category": "uncategorized",
      "direction": "expense",
      "transaction_type": "pay",
      "recipient": "ABC SHOP",
      "reference": null,
      "occurred_at": "2026-02-03T10:18:10Z",
      "date": "2026-02-03",
      "time": "10:18",
      "user_note": "groceries",
      "ingestion_mode": "single_upload",
      "ingestion_batch_id": null,
      "source_message_id": null,
      "source_received_at": null,
      "source": "manual_upload"
    }
  ]
}

Notes

- `stored` counts newly inserted rows. Duplicates (same reference) are returned in `transactions` but do not increment `stored`.


Response 400

{ "detail": "No valid messages provided." }

4.3.1 Android Ingestion (Single, Inbox Sync, Statement Import)
POST /ingestion/messages

Purpose: Unified ingestion endpoint for Android workflows.

Request Body

{
  "mode": "inbox_sync",
  "batch_id": "sync-2026-02-28T08:25:00Z",
  "source": "android_inbox",
  "messages": [
    {
      "message": "QBC123XYZ Confirmed. Ksh500.00 sent to JOHN DOE 0712345678 on 2/2/26 at 9:14 AM.",
      "source_message_id": "19495",
      "source_received_at": "2026-02-02T09:14:20+03:00"
    },
    {
      "message": "QBC222AAA Confirmed. Ksh250.00 paid to ABC SHOP on 2/2/26 at 4:22 PM.",
      "source_message_id": "19496",
      "user_note": "snacks"
    }
  ]
}

Mode values

- `single_upload`: one-by-one message upload from app UI.
- `inbox_sync`: bulk sync from Android SMS inbox.
- `statement_import`: parsed lines from uploaded statement files.

Response 200

{
  "mode": "inbox_sync",
  "batch_id": "sync-2026-02-28T08:25:00Z",
  "total": 2,
  "stored": 2,
  "duplicates": 0,
  "failed": 0,
  "results": [
    {
      "index": 0,
      "status": "stored",
      "source_message_id": "19495",
      "error": null,
      "transaction": {
        "id": 91,
        "amount": 500.0,
        "currency": "KES",
        "category": "uncategorized",
        "direction": "expense",
        "transaction_type": "sent",
        "recipient": "JOHN DOE",
        "reference": "QBC123XYZ",
        "occurred_at": "2026-02-02T09:14:00+03:00",
        "date": "2026-02-02",
        "time": "09:14",
        "user_note": null,
        "ingestion_mode": "inbox_sync",
        "ingestion_batch_id": "sync-2026-02-28T08:25:00Z",
        "source_message_id": "19495",
        "source_received_at": "2026-02-02T09:14:20+03:00",
        "source": "android_inbox"
      }
    },
    {
      "index": 1,
      "status": "stored",
      "source_message_id": "19496",
      "error": null,
      "transaction": { "...": "..." }
    }
  ]
}

Notes

- Per-item `status` can be `stored`, `duplicate`, or `failed`.
- Deduplication checks M-PESA `reference` first, then `source_message_id` within the same `mode`.

4.4 List Transactions
GET /transactions

Purpose: Retrieve stored transactions for tables and filters.

Query Parameters (optional)

limit (integer, default 50)

category (string)

type (string; e.g., sent, received, pay, paybill)

from (ISO timestamp)

to (ISO timestamp)

Example

GET /transactions?category=food&limit=20


Response 200

{
  "count": 1,
  "transactions": [
    {
      "id": 14,
      "amount": 250.0,
      "currency": "KES",
      "category": "food",
      "direction": "expense",
      "transaction_type": "pay",
      "recipient": "ABC SHOP",
      "reference": null,
      "occurred_at": "2026-02-03T10:18:10Z",
      "date": "2026-02-03",
      "time": "10:18",
      "user_note": null,
      "ingestion_mode": "inbox_sync",
      "ingestion_batch_id": "sync-2026-02-28T08:25:00Z",
      "source_message_id": "19496",
      "source_received_at": "2026-02-03T10:18:10+03:00",
      "source": "android_inbox"
    }
  ]
}

4.5 Summary (Category Totals)
GET /summary

Purpose: Return aggregated totals for charts.
Notes: only expenses (`direction=expense`) are included in `total_spent` and `categories`.

Query Parameters (optional)

from (ISO timestamp)

to (ISO timestamp)

Response 200

{
  "currency": "KES",
  "total_spent": 1750.0,
  "categories": [
    { "category": "food", "amount": 600.0 },
    { "category": "transport", "amount": 400.0 },
    { "category": "airtime", "amount": 150.0 }
  ]
}

4.6 Insights (Warnings & Highlights)
GET /insights

Purpose: Return high-level insights derived from stored transactions.

Response 200

{
  "warnings": [
    "High spending detected in betting category.",
    "Frequent small transfers detected."
  ],
  "highlights": [
    "Top spending category: food",
    "Average daily spending: 250.0"
  ]
}

4.7 Clear Stored Data (Development Only)
DELETE /transactions

Purpose: Remove stored transactions to reset the development environment.

Response 200

{ "message": "All transactions deleted." }


Note: This endpoint should be restricted or removed in production deployments.

5. Status Codes

200 OK — successful request

400 Bad Request — invalid input or unsupported format

404 Not Found — unknown route/resource

500 Internal Server Error — unexpected error

6. Security & Privacy Notes

The API should avoid storing raw personal data beyond what is required for analysis.

Raw SMS message text should be processed but not stored (store only derived fields and user-provided notes).

Production deployments should use authentication and transport security (HTTPS).

Client applications should handle transaction message data as sensitive content.

7. Versioning

API versioning may be introduced later using one of the following patterns:

Path versioning: /v1/analyze

Header versioning: Accept: application/vnd.mpesa-analyzer.v1+json

For now, all endpoints are considered v1 (implicit).
