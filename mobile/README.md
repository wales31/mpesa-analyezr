# Mobile App (Flutter)

This folder now contains the Flutter mobile client for M-PESA Analyzer.

## Current scope (Phase 1 foundation)

- Flutter scaffold for Android/iOS development
- API base URL configuration in-app
- Auth flow:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Secure token persistence (`flutter_secure_storage`)
- Authenticated summary screen:
  - `GET /summary`

## Project setup

1. Install Flutter and verify tooling:

```bash
flutter doctor -v
```

2. From `mobile/`, install Dart and Flutter dependencies:

```bash
flutter pub get
```

3. If platform folders are not present yet, generate them once from this folder:

```bash
flutter create .
```

This repo intentionally keeps the Flutter app source and configuration in version control, but platform runners may need to be generated locally if Flutter tooling was not available when the repository was updated.

## Run locally

Start the backend API from repo root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Then start the Flutter app from `mobile/`:

```bash
flutter run -d android
```

Use a specific device ID if needed:

```bash
flutter devices
flutter run -d <device-id>
```

### API base defaults

- Android emulator default API base: `http://10.0.2.2:8000`
- iOS simulator default API base: `http://127.0.0.1:8000`
- Real phone API base: set your LAN IP in-app, for example `http://192.168.1.24:8000`

## Phase 1 checkpoints

- App restores persisted session on launch
- App supports login and registration
- API base is configurable and persisted
- Home screen loads signed-in profile and `/summary`
- Sign out clears session state and stored credentials
