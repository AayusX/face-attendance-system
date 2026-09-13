#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Face Attendance portable Linux build"
PY=${PYTHON:-"$PWD/.venv/bin/python"}
if [ ! -x "$PY" ]; then
  echo "[ERROR] venv not found. Run run.sh once or create .venv first."
  exit 1
fi

"$PY" -m pip install --quiet pyinstaller

rm -rf build dist
GUI_CONSOLE=0 "$PY" -m PyInstaller app.spec --noconfirm

echo "==> selftest of frozen bundle"
dist/FaceAttendance/FaceAttendance --selftest || { echo "[ERROR] selftest failed"; cat selftest_result.txt; exit 1; }
cat selftest_result.txt
rm -f selftest_result.txt
echo "==> DONE: dist/FaceAttendance/"