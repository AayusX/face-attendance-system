import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "attendance.db"
EXPORT_DIR = BASE_DIR / "exports"
SAMPLE_DIR = BASE_DIR / "faces"
LOG_PATH = BASE_DIR / "app.log"

CAMERA_INDEX = 0
FRAME_WIDTH = 480
FRAME_HEIGHT = 360
DETECT_SCALE = 0.5
ENCODE_EVERY_FRAMES = 3
POLL_MS = 40

SAMPLE_COUNT = 5
SAMPLE_DELAY_MS = 350

RECOGNITION_THRESHOLD = 0.5
MARK_EVERY_FRAMES = 6

WINDOW_TITLE = "Face Attendance System"
WINDOW_SIZE = "1120x680"

for path in (DB_PATH.parent, EXPORT_DIR, SAMPLE_DIR):
    path.mkdir(parents=True, exist_ok=True)