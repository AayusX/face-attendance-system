import os
import sqlite3
from datetime import date, datetime

import numpy as np

from config import DB_PATH


def get_connection():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                face_encoding BLOB NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Present'
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance (student_id, date)"
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )"""
        )


def get_setting(key, default=None):
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def add_student(student_id, name, encoding):
    blob = np.asarray(encoding, dtype=np.float64).tobytes()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO students (student_id, name, face_encoding, created_at) VALUES (?, ?, ?, ?)",
            (student_id, name, blob, datetime.now().isoformat(timespec="seconds")),
        )


def rename_student(student_id, new_name):
    with get_connection() as conn:
        conn.execute("UPDATE students SET name = ? WHERE student_id = ?", (new_name, student_id))
        conn.execute("UPDATE attendance SET name = ? WHERE student_id = ?", (new_name, student_id))


def delete_student(student_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))


def student_exists(student_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
    return row is not None


def load_students():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT student_id, name, face_encoding FROM students ORDER BY student_id"
        ).fetchall()
    students = []
    for row in rows:
        students.append(
            {
                "student_id": row["student_id"],
                "name": row["name"],
                "encoding": np.frombuffer(row["face_encoding"], dtype=np.float64),
            }
        )
    return students


def list_students_meta():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT student_id, name, created_at FROM students ORDER BY student_id"
        ).fetchall()
    return [dict(row) for row in rows]


def mark_attendance(student_id, name, when=None):
    when = when or datetime.now()
    date_str = when.strftime("%Y-%m-%d")
    time_str = when.strftime("%H:%M:%S")
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, date_str),
        ).fetchone()
        if existing:
            return False
        conn.execute(
            "INSERT INTO attendance (student_id, name, date, time, status) VALUES (?, ?, ?, ?, 'Present')",
            (student_id, name, date_str, time_str),
        )
        return True


def has_attendance_today(student_id, day=None):
    day = day or date.today().isoformat()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM attendance WHERE student_id = ? AND date = ?",
            (student_id, day),
        ).fetchone()
        return row is not None


def get_attendance(day=None):
    day = day or date.today().isoformat()
    return get_attendance_between(day, day)


def get_attendance_between(start, end):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT student_id, name, date, time, status
               FROM attendance WHERE date BETWEEN ? AND ?
               ORDER BY date, time""",
            (start, end),
        ).fetchall()
    return [dict(row) for row in rows]


def get_present_ids(start, end):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT DISTINCT student_id FROM attendance
               WHERE date BETWEEN ? AND ?""",
            (start, end),
        ).fetchall()
    return {row["student_id"] for row in rows}


def get_absentees(start, end):
    present = get_present_ids(start, end)
    absent = []
    for student in list_students_meta():
        if student["student_id"] not in present:
            absent.append(student)
    return absent


def get_student_attendance(student_id):
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT student_id, name, date, time, status
               FROM attendance WHERE student_id = ?
               ORDER BY date DESC, time DESC""",
            (student_id,),
        ).fetchall()
    return [dict(row) for row in rows]