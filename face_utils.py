import queue
import threading

import cv2
import face_recognition
import numpy as np


class _DlibExecutor:
    def __init__(self):
        self._q = queue.Queue()
        self._t = threading.Thread(target=self._run, daemon=True, name="dlib-executor")
        self._t.start()

    def _run(self):
        while True:
            fn, args, done = self._q.get()
            try:
                result = fn(*args)
                error = None
            except BaseException as exc:
                result = None
                error = exc
            if done is not None:
                done.put((result, error))

    def call(self, fn, args=()):
        done = queue.Queue(maxsize=1)
        self._q.put((fn, args, done))
        result, error = done.get()
        if error is not None:
            raise error
        return result


_dlib = _DlibExecutor()


def detect_face_locations(frame, upsample=1):
    if frame is None:
        return []
    return _dlib.call(_detect, (frame, upsample))


def encode_face(frame, location):
    return _dlib.call(_encode, (frame, location))


def _detect(frame, upsample):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=upsample)


def _encode(frame, location):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb, [location])
    return encodings[0] if encodings else None


def mean_encoding(encodings):
    return np.mean(np.asarray(encodings, dtype=np.float64), axis=0)


def match_known(encoding, known_encodings):
    if len(known_encodings) == 0:
        return None, None
    distances = face_recognition.face_distance(
        np.asarray(known_encodings, dtype=np.float64),
        np.asarray(encoding, dtype=np.float64),
    )
    best = int(np.argmin(distances))
    return best, float(distances[best])