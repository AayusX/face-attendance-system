# Face Attendance System

A light, portable face-recognition attendance app for Windows (and Linux). Webcam-only,
no external services. Built with **Python + Tkinter + dlib / face_recognition + OpenCV**.

## Features

- **Face recognition attendance** — live webcam preview, faces are detected and matched automatically
- **Automatic attendance** — starts running on launch, marks present students and logs it
- **Duplicate registration guard** — a face can be registered once; re-registering requires deleting the old record first
- **Undo / manage students** — register, rename, delete; live attendance table
- **Reports & filters** — by date range, present / absent, text search
- **Nepali (Bikram Sambat) calendar** — header, dashboard, reports and exports show Nepali dates; the same input field accepts both AD (2026-09-13) and BS (2083-05-28) dates
- **Exports** — CSV and Excel with a `date (BS)` column and BS filenames
- **Light UI theme**, login screen (default: `admin` / `admin`)
- **Fully portable build** — no Python or packages needed on target machines

## Quick start (from source)

```
# Linux
./run.sh

# Windows (Python 3.12+)
python -m pip install -r requirements-windows.txt
python main.py
```

Default login: **admin / admin**

## Build the portable app

The Windows build is produced by GitHub Actions (see `.github/workflows/build-exe.yml`): on every tagged release it builds a self-contained `dist/FaceAttendance/` folder and uploads it as a zip. Download it from the **Releases** page — unzip on any Windows PC and run `FaceAttendance.exe`. No installation required.

Build locally on Windows:

```
build_windows.bat        # -> dist\FaceAttendance\ + FaceAttendance-portable.zip
```

Or on Linux:

```
./build_linux.sh         # -> dist/FaceAttendance/
```

Verify a bundle on any machine without installing dependencies:

```
FaceAttendance.exe --selftest    # writes selftest_result.txt ("OK ..." = healthy)
```

## Notes

- The bundle is ~320 MB (dlib models + OpenCV + Tk runtime are heavy).
- Windows SmartScreen complains about unsigned exes: **More info → Run anyway**.
- All app data (database, exports, logs) is created next to the executable, so the whole folder is portable.

## License

MIT — see [LICENSE](LICENSE).