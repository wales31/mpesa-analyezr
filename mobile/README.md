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

## Android Studio setup

This project is already prebuilt for Android. You can import it into Android Studio without running `expo prebuild`.

1. Install Java, Android Studio, and the Android SDK.
2. From `mobile/`, install JavaScript dependencies:

```bash
npm install
```

3. Open Android Studio and choose one of these folders:

- `mobile/` if you want Android Studio to detect the lightweight wrapper project first
- `mobile/android/` if you want to open the Android app module directly

4. Let Gradle sync finish. This project resolves Expo and React Native Gradle plugins from `node_modules`, so the sync will fail until `npm install` has completed.
5. Build or run the `app` configuration from Android Studio.

If Android Studio cannot find the SDK, set `ANDROID_HOME` or `ANDROID_SDK_ROOT` before syncing so Gradle can auto-create `mobile/android/local.properties`, or create that file manually with your local SDK path.

## Run locally (LAN)

By default, `npm run start:lan` now starts Expo in **development client** mode so you do not get blocked by an outdated Expo Go install when the project SDK is newer than the store version on your device.

1. Start backend API from repo root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. Install JavaScript dependencies and build the native app once for the device/emulator you want to use:

```bash
cd mobile
npm install
npm run android
```

Use `npm run ios` instead when targeting iOS.

3. Start Metro over LAN:

```bash
cd mobile
npm run start:lan
```

4. Open the installed development build on your device/emulator.

- Android emulator default API base: `http://10.0.2.2:8000`
- iOS simulator default API base: `http://127.0.0.1:8000`
- Physical phone API base: set your LAN IP in-app, for example `http://192.168.1.24:8000`

### Expo Go fallback

If you have the matching Expo Go version installed already and want the QR-code flow, use:

```bash
cd mobile
npm run start:go
```

If Expo Go shows **"Project is incompatible with this version of Expo Go"**, either update Expo Go from the App Store / Play Store or use the development-client flow above.

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

You can then run the app from Android Studio against the same Metro server, or build from the terminal with:

```bash
cd mobile/android
./gradlew assembleDebug
```

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
