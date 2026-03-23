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

## First local setup

Generate the Flutter platform folders inside this directory:

```bash
flutter create .
```

For the first successful run, prefer Android instead of Linux desktop:

```bash
flutter devices
flutter run -d android
```

## Linux desktop troubleshooting

If `flutter run` tries to launch on Linux and fails with CMake/Ninja/compiler
errors, that means Flutter selected the Linux desktop target but your machine is
missing native desktop build tools.

You have two choices:

1. **Use Android only for now** and explicitly target it:

```bash
flutter run -d android
```

2. **Install Linux desktop prerequisites** and then run again:

```bash
sudo apt update
sudo apt install clang cmake ninja-build pkg-config libgtk-3-dev
flutter run -d linux
```

If you do not plan to use Linux desktop during Phase 1, you can also disable it:

```bash
flutter config --no-enable-linux-desktop
```

## Next commands

Once Flutter is available locally, generate the platform folders if needed and
run:

```bash
flutter create .
flutter run -d android
```
