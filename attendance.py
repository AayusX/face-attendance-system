from config import RECOGNITION_THRESHOLD
from database import (
    add_student,
    delete_student,
    init_db,
    load_students,
)
from face_utils import match_known, mean_encoding


class AttendanceSystem:
    def __init__(self, threshold=RECOGNITION_THRESHOLD):
        init_db()
        self.threshold = threshold
        self.students = []
        self.known_encodings = []
        self.reload_students()

    def reload_students(self):
        self.students = load_students()
        self.known_encodings = [s["encoding"] for s in self.students]

    def register(self, student_id, name, encodings):
        add_student(student_id, name, mean_encoding(encodings))
        self.reload_students()

    def remove_student(self, student_id):
        delete_student(student_id)
        self.reload_students()

    def recognize(self, encoding):
        best, distance = match_known(encoding, self.known_encodings)
        if best is None or distance > self.threshold:
            return None
        return self.students[best]

    def find_by_face(self, encoding):
        return self.recognize(encoding)