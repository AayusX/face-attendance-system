#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PY=python3
VENV=.venv
PYTHON_BIN="$VENV/bin/python"

echo "==> Face Attendance System launcher"

if [ ! -d "$VENV" ]; then
    echo "==> Creating virtual environment..."
    $PY -m venv "$VENV"
fi

if ! "$PYTHON_BIN" -c "import cv2, face_recognition" >/dev/null 2>&1; then
    echo "==> Installing dependencies (first run may take a while)..."
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet "setuptools<81"
    "$VENV/bin/pip" install --quiet -r requirements.txt
fi

echo "==> Running environment self-check..."
"$PYTHON_BIN" - <<'EOF'
import cv2, numpy, face_recognition
print("    cv2:", cv2.__version__)
print("    numpy:", numpy.__version__)
print("    face_recognition: OK")

ok, frame = cv2.VideoCapture(0).read()
print("    camera:", "OK" if ok else "NOT RESPONDING")

try:
    import openpyxl
    print("    openpyxl:", openpyxl.__version__)
except ImportError:
    print("    openpyxl: MISSING (Excel export will fail)")

try:
    import nepali_datetime
    print("    nepali_datetime: OK")
except ImportError:
    print("    nepali_datetime: MISSING (Nepali calendar will fail)")
EOF

echo "==> Launching application..."
exec "$PYTHON_BIN" main.py