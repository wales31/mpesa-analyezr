# Web-to-Mobile Feature Parity Progress

Last updated: 2026-03-23

This checklist tracks the work needed to bring the Flutter mobile app to parity with the web app.

## 0) Foundation

- [x] Flutter app scaffolded
- [x] Auth register/login/me flow
- [x] Secure token persistence
- [x] Summary screen (`/summary`)
- [x] API base configuration in-app

## 1) Navigation + app structure

- [ ] Add tab/stack navigation (Auth, Dashboard, Ingestion, Transactions, Insights, Budget, Notifications)
- [ ] Split feature controllers further as app surface expands
- [ ] Add shared loading/error/empty state components

## 2) Ingestion feature parity (from web `spending.html`)

- [ ] Single message analysis (`POST /analyze`)
- [ ] Bulk message analysis (`POST /analyze/bulk`)
- [ ] Structured ingestion flow (`POST /ingestion/messages`)
- [ ] Ingestion result view (stored/duplicate/failed counts and rows)

## 3) Dashboard + transactions parity (from web `dashboard.html`)

- [ ] Date-range filter (`last_7`, `last_30`, `this_month`, `custom`, `all`)
- [ ] Summary cards and category totals
- [ ] Transactions list (`GET /transactions`) with limit/filter controls
- [ ] Clear transactions action (`DELETE /transactions`)

## 4) Insights + notifications parity

- [ ] Insights panel (`GET /insights`)
- [ ] Refresh notifications (`POST /notifications/refresh`)
- [ ] Notifications list (`GET /notifications`)
- [ ] Mark single notification read (`PATCH /notifications/{id}/read`)
- [ ] Mark all notifications read (`POST /notifications/read-all`)

## 5) Budget feature parity

- [ ] Budget limit settings (`GET/PUT /budget/limit`)
- [ ] Monthly planner UI parity with web budget page (local device state)
- [ ] Planned-vs-actual comparison using `/summary`
- [ ] Backend budget CRUD integration when API is available (currently planned in backend roadmap)

## 6) Android-specific ingestion (Phase 2)

- [ ] SMS inbox permission flow
- [ ] Inbox reader job for M-PESA messages
- [ ] Map inbox records to `/ingestion/messages` with `mode=inbox_sync`
- [ ] Statement import support (`mode=statement_import`)
- [ ] Duplicate handling and sync checkpoints on device

## 7) QA + release readiness

- [ ] Device matrix test (at least 2 Android versions + 1 emulator)
- [ ] Offline/network failure handling tests
- [ ] Auth/session expiry tests
- [ ] Build signed APK/AAB pipeline
- [ ] Release checklist and versioning

## Next sprint recommendation

1. Add app navigation shell and placeholders for remaining features.
2. Implement ingestion screen (`/analyze`, `/analyze/bulk`, `/ingestion/messages`).
3. Implement transactions screen with date filters and pagination/limit.
4. Implement insights + notifications.
