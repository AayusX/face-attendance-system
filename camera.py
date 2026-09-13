import threading
import time
from queue import Queue

import cv2

from config import CAMERA_INDEX, DETECT_SCALE, ENCODE_EVERY_FRAMES, FRAME_HEIGHT, FRAME_WIDTH
from face_utils import detect_face_locations, encode_face


class CameraStream(threading.Thread):
    def __init__(self, index=CAMERA_INDEX):
        super().__init__(daemon=True)
        self.index = index
        self.latest = None
        self.frame_id = 0
        self.error = None
        self._running = True

    def run(self):
        cap = cv2.VideoCapture(self.index)
        if not cap.isOpened():
            self.error = "Cannot open camera. Check connection or CAMERA_INDEX."
            self._running = False
            return
        while self._running:
            ok, frame = cap.read()
            if ok:
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                self.latest = frame
                self.frame_id += 1
            else:
                time.sleep(0.02)
        cap.release()

    def stop(self):
        self._running = False


class DetectionResult:
    __slots__ = ("frame", "locations", "encodings")

    def __init__(self, frame, locations, encodings):
        self.frame = frame
        self.locations = locations
        self.encodings = encodings


class DetectionWorker(threading.Thread):
    def __init__(self, stream):
        super().__init__(daemon=True)
        self.stream = stream
        self.queue = Queue(maxsize=5)
        self._running = True
        self._last = None
        self.encodings_wanted = False
        self._frame_n = 0
        self._last_locs_key = None
        self._last_encodings = []
        self._wanted_prev = False

    def run(self):
        while self._running:
            frame = self.stream.latest
            if frame is None or frame is self._last:
                time.sleep(0.005)
                continue
            self._last = frame
            height, width = frame.shape[:2]
            small_w = max(int(width * DETECT_SCALE), 32)
            small_h = max(int(height * DETECT_SCALE), 32)
            small = cv2.resize(frame, (small_w, small_h))
            scale = width / small_w
            locations = []
            for top, right, bottom, left in detect_face_locations(small):
                top = min(int(round(top * scale)), height - 1)
                bottom = min(int(round(bottom * scale)), height - 1)
                left = min(int(round(left * scale)), width - 1)
                right = min(int(round(right * scale)), width - 1)
                locations.append((top, right, bottom, left))
            encodings = []
            was_wanted = self._wanted_prev
            self._wanted_prev = self.encodings_wanted
            if self.encodings_wanted:
                if not was_wanted:
                    self._last_locs_key = None
                    self._last_encodings = []
                self._frame_n += 1
                loc_key = tuple(locations)
                if (
                    loc_key == self._last_locs_key and self._frame_n % ENCODE_EVERY_FRAMES != 0
                ):
                    encodings = list(self._last_encodings)
                else:
                    encodings = []
                    for loc in locations:
                        encoding = encode_face(frame, loc)
                        if encoding is not None:
                            encodings.append(encoding)
                    self._last_encodings = list(encodings)
                    self._last_locs_key = loc_key
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except Exception:
                    pass
            self.queue.put(DetectionResult(frame, locations, encodings))

    def stop(self):
        self._running = False