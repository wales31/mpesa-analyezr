# Mobile App (Flutter)

This folder contains the Flutter mobile client for M-PESA Analyzer.

## Current scope 

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

## Build an Android APK (phone-installable)

From the `mobile/` directory:

```bash
flutter pub get
flutter build apk --release
```

APK output path:

```text
mobile/build/app/outputs/flutter-apk/app-release.apk
```

Install on your phone:

1. Copy `app-release.apk` to the phone (USB, AirDrop-equivalent, cloud drive, or messaging app).
2. On Android, allow installs from unknown sources for the app you used to open the APK.
3. Tap the APK and install.

If your backend runs on your laptop/server over local network, set **API Base URL** in the app to your machine LAN IP (example: `http://192.168.1.24:8000`).

### Phase-1 APK notes

- This APK is suitable for direct install/testing.
- Android cleartext HTTP is enabled so the app can call local `http://` API endpoints during development.
- For Play Store publishing later, switch to HTTPS APIs and configure a proper release signing key.

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
