# M-PESA Analyzer Flutter Shell

This directory contains Phase 1 of the Flutter migration: a minimal app shell
that mirrors the current mobile flow without any API integration yet.

## Included

- app entrypoint
- theme/colors
- route/navigation skeleton
- loading screen
- auth gate
- placeholder auth screen
- placeholder home screen

## Expected flow

1. App launches into a loading state.
2. After bootstrap completes:
   - if a session exists, show the home screen
   - otherwise show the auth screen

## Notes

- This shell intentionally avoids backend/API work for now.
- Flutter is not installed in this environment, so the Android project could not
  be generated or run here.
- Once Flutter is available locally, generate the platform folders if needed and
  run:

```bash
flutter create .
flutter run
```

