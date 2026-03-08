# Mobile App

This folder contains the React Native Android/iOS app for M-PESA Analyzer.

## Current scope (implemented)

- Expo + React Native TypeScript scaffold
- API base URL configuration in-app
- Auth flow:
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Secure token persistence (`expo-secure-store`)
- Authenticated summary screen:
  - `GET /summary`

See feature parity tracker: `mobile/FEATURE_PARITY_PROGRESS.md`.

## Run locally (LAN)

1. Start backend API from repo root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. Start mobile app:

```bash
cd mobile
npm install
npm run start:lan
```

3. Open on device/emulator:

- Expo Go on Android/iOS: scan QR from Expo terminal
- Android emulator default API base: `http://10.0.2.2:8000`
- iOS simulator default API base: `http://127.0.0.1:8000`
- Physical phone API base: set your LAN IP in-app, for example `http://192.168.1.24:8000`

## Run on physical Android over USB (recommended for reliable progress view)

Use this when LAN is unstable and you want live changes to appear on your phone through USB.

1. Enable phone debugging:

- Turn on `Developer options` and `USB debugging` on Android
- Connect phone via USB and accept debugging prompt

2. Verify device is visible:

```bash
adb devices
```

3. Start backend (repo root):

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Build/install Android dev client once:

```bash
cd mobile
npm install
npm run android
```

5. Forward ports over USB and start Metro:

```bash
cd mobile
npm run start:usb
```

This runs:

- `adb reverse tcp:8081 tcp:8081` (Metro)
- `adb reverse tcp:8000 tcp:8000` (Backend API)
- `expo start --dev-client --localhost`

6. In the app, set API base URL to:

```text
http://127.0.0.1:8000
```

Now every save in your code should refresh on the connected phone.

## Progress checkpoints (Phase 1 complete)

- App opens to Login/Register screen
- API base can be updated and persisted
- Register/login succeeds and persists session
- Home screen loads profile and `/summary`
- Sign out clears session

## Optional env override

You can set API base at start time:

```bash
EXPO_PUBLIC_MPESA_API_BASE=http://192.168.1.24:8000 npm run start
```
