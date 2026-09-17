import tkinter as tk
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from attendance import AttendanceSystem
from auth import check_login, change_password, seed_defaults
from camera import CameraStream, DetectionWorker
from config import (
    CAMERA_INDEX,
    MARK_EVERY_FRAMES,
    POLL_MS,
    RECOGNITION_THRESHOLD,
    SAMPLE_COUNT,
    SAMPLE_DELAY_MS,
    WINDOW_SIZE,
    WINDOW_TITLE,
)
from database import (
    get_absentees,
    get_attendance,
    get_attendance_between,
    get_present_ids,
    list_students_meta,
    mark_attendance,
    student_exists,
)
from export import (
    export_attendance,
    export_attendance_excel,
    export_attendance_range,
)
from face_utils import detect_face_locations, encode_face, mean_encoding
from nepali_calendar import ad_from_bs, bs_date_from_ad, today_bs, today_bs_display, to_bs_str
from theme import (apply_theme, ACCENT, ACCENT_DARK, AMBER, BG, BORDER, CARD, GREEN,
                   MUTED, PANEL, RED, TEXT)


def parse_date(text):
    text = (text or "").strip()
    try:
        bs_hint = int(text[:4]) >= 2050
    except (ValueError, TypeError):
        bs_hint = False
    if bs_hint:
        ad = ad_from_bs(text)
        if ad is not None:
            return ad.isoformat()
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        pass
    ad = ad_from_bs(text)
    return ad.isoformat() if ad is not None else None


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{WINDOW_TITLE} - Login")
        self.resizable(True, True)
        self.minsize(420, 500)
        apply_theme(self)
        seed_defaults()

        panel = ttk.Frame(self, style="Card.TFrame", padding=34)
        panel.pack(fill="both", expand=True, padx=24, pady=24)
        self._center(440, 540)

        ttk.Label(panel, text="◉", style="Card.TLabel", foreground=ACCENT,
                  font=("Segoe UI", 38, "bold")).pack()
        ttk.Label(panel, text="Face Attendance", style="Card.TLabel",
                  font=("Segoe UI", 22, "bold")).pack(pady=(2, 0))
        ttk.Label(panel, text="offline · local · private", style="CardMuted.TLabel").pack(pady=(0, 22))

        ttk.Label(panel, text="Username", style="CardMuted.TLabel").pack(anchor="w", pady=(0, 4))
        self.user_var = tk.StringVar(value="admin")
        self.user_entry = ttk.Entry(panel, textvariable=self.user_var)
        self.user_entry.pack(fill="x", pady=(0, 12))

        ttk.Label(panel, text="Password", style="CardMuted.TLabel").pack(anchor="w", pady=(0, 4))
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(panel, textvariable=self.pass_var, show="*")
        self.pass_entry.pack(fill="x", pady=(0, 18))

        ttk.Button(panel, text="Sign In", style="Primary.TButton",
                   command=self.login).pack(fill="x", ipady=5)

        self.status_var = tk.StringVar()
        error_label = ttk.Label(panel, textvariable=self.status_var, foreground=RED,
                                style="Card.TLabel")
        error_label.pack(pady=(12, 0))
        ttk.Label(panel, text="Default: admin / admin (change it in Settings)",
                  style="CardMuted.TLabel").pack(pady=(14, 0))
        ttk.Label(panel, text="Developed by Mr. Aayush Bhandari",
                  style="CardMuted.TLabel").pack(pady=(4, 0))

        self.user_entry.bind("<Return>", lambda e: self.login())
        self.pass_entry.bind("<Return>", lambda e: self.login())
        self.bind("<Map>", self._on_map)
        self.lift()

    def _on_map(self, event):
        if event.widget is not self:
            return
        try:
            self.focus_force()
            self.user_entry.focus_set()
        except tk.TclError:
            pass

    def _center(self, w, h):
        self.update_idletasks()
        x = max((self.winfo_screenwidth() - w) // 2, 0)
        y = max((self.winfo_screenheight() - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def login(self):
        ok, error = check_login(self.user_var.get(), self.pass_var.get())
        if not ok:
            self.status_var.set(error)
            self.pass_var.set("")
            self.pass_entry.focus_set()
            return
        self.destroy()
        app = FaceAttendanceApp()
        app.mainloop()


class PasswordDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Change Login Credentials")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg=BG)

        panel = ttk.Frame(self, style="Card.TFrame", padding=24)
        panel.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(panel, text="Login Credentials", style="Card.TLabel",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        ttk.Label(panel, text="Username", style="CardMuted.TLabel").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.user_var = tk.StringVar(value="admin")
        ttk.Entry(panel, textvariable=self.user_var, width=28).grid(row=1, column=1, pady=6)
        ttk.Label(panel, text="(Edit to also change the username.)", style="CardMuted.TLabel").grid(
            row=1, column=2, sticky="w", padx=8, pady=6)

        ttk.Label(panel, text="Current password", style="CardMuted.TLabel").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.current_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.current_var, show="*", width=28).grid(row=2, column=1, pady=6)

        ttk.Label(panel, text="New password", style="CardMuted.TLabel").grid(row=3, column=0, sticky="e", padx=8, pady=6)
        self.new_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.new_var, show="*", width=28).grid(row=3, column=1, pady=6)

        ttk.Label(panel, text="Confirm new password", style="CardMuted.TLabel").grid(row=4, column=0, sticky="e", padx=8, pady=6)
        self.confirm_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self.confirm_var, show="*", width=28).grid(row=4, column=1, pady=6)

        self.status_var = tk.StringVar()
        ttk.Label(panel, textvariable=self.status_var, foreground=RED,
                  style="Card.TLabel").grid(row=5, column=0, columnspan=2, pady=6)

        buttons = ttk.Frame(panel, style="Card.TFrame")
        buttons.grid(row=6, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(buttons, text="Update", style="Primary.TButton",
                   command=self.save).pack(side="left", padx=6)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=6)

    def save(self):
        current_user = self.user_var.get().strip() or "admin"
        current = self.current_var.get()
        new_pass = self.new_var.get()
        confirm = self.confirm_var.get()
        if len(new_pass) < 4:
            self.status_var.set("New password must be at least 4 characters.")
            return
        if new_pass != confirm:
            self.status_var.set("Passwords do not match.")
            return
        ok, error = change_password(current_user, current, current_user, new_pass)
        if not ok:
            self.status_var.set(error)
            return
        messagebox.showinfo("Updated", "Login credentials updated.", parent=self)
        self.destroy()


class RegisterDialog(tk.Toplevel):
    def __init__(self, parent, stream, system):
        super().__init__(parent)
        self.stream = stream
        self.system = system
        self.samples = []
        self.capture_active = False
        self.last_capture = 0.0
        self.photo = None

        self.title("Register New Student")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg=BG)

        outer = ttk.Frame(self, style="Card.TFrame", padding=18)
        outer.pack(fill="both", expand=True, padx=16, pady=16)

        form = ttk.Frame(outer, style="Card.TFrame")
        form.pack(fill="x")
        ttk.Label(form, text="Register New Student", style="Card.TLabel",
                  font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 14))

        ttk.Label(form, text="Full name", style="CardMuted.TLabel").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.name_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.name_var, width=24).grid(row=1, column=1, pady=6, sticky="ew")

        ttk.Label(form, text="Student ID", style="CardMuted.TLabel").grid(row=1, column=2, sticky="e", padx=(16, 8), pady=6)
        self.id_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.id_var, width=16).grid(row=1, column=3, pady=6, sticky="ew")

        ttk.Label(form, text="Face samples", style="CardMuted.TLabel").grid(row=2, column=0, sticky="e", padx=8, pady=(6, 0))
        self.samples_var = tk.StringVar(value=str(SAMPLE_COUNT))
        ttk.Spinbox(form, from_=3, to=12, textvariable=self.samples_var,
                    width=16).grid(row=2, column=1, sticky="ew", pady=(6, 0))
        ttk.Label(form, text="More samples = more reliable", style="CardMuted.TLabel").grid(
            row=2, column=2, columnspan=2, sticky="w", padx=16, pady=(6, 0))

        preview_card = ttk.Frame(outer, style="Panel.TFrame", padding=8)
        preview_card.pack(fill="both", expand=True, pady=14)
        self.canvas = tk.Canvas(preview_card, width=380, height=280, bg="#000000",
                                highlightthickness=1, highlightbackground=BORDER)
        self.canvas.pack()

        self.status_var = tk.StringVar(value="Enter student details to begin.")
        status_label = ttk.Label(outer, textvariable=self.status_var, foreground=AMBER,
                                 style="Card.TLabel")
        status_label.pack(anchor="w", pady=(10, 4))

        progress_card = ttk.Frame(outer, style="Card.TFrame")
        progress_card.pack(fill="x", pady=(0, 12))
        self.progress_var = tk.StringVar(value="0 / 0 samples")
        ttk.Label(progress_card, textvariable=self.progress_var, style="CardMuted.TLabel").pack(side="right")
        self.progress = ttk.Progressbar(progress_card, maximum=10, value=0)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 12))

        buttons = ttk.Frame(outer, style="Card.TFrame")
        buttons.pack(fill="x")
        self.start_btn = ttk.Button(buttons, text="Start Capture", style="Primary.TButton",
                                    command=self.start_capture)
        self.start_btn.pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")

        self.after(40, self.update_preview)

    def start_capture(self):
        name = self.name_var.get().strip()
        student_id = self.id_var.get().strip()
        if not name or not student_id:
            messagebox.showwarning("Missing info", "Name and Student ID are required.", parent=self)
            return
        if student_exists(student_id):
            messagebox.showwarning(
                "Duplicate ID",
                f"Student ID '{student_id}' is already registered.",
                parent=self,
            )
            return
        count = self._sample_count()
        if count < 3:
            messagebox.showwarning("Too few samples", "Use at least 3 samples for reliability.", parent=self)
            return
        self.samples = []
        self.capture_active = True
        self.progress.config(maximum=count, value=0)
        self.progress_var.set(f"0 / {count} samples")
        self.start_btn.config(state="disabled")

    def _alive(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def update_preview(self):
        if not self._alive():
            return
        frame = self.stream.latest
        if frame is not None:
            display = self._draw_preview(frame)
            if not self._alive():
                return
            self.photo = ImageTk.PhotoImage(display)
            self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
        self.after(40, self.update_preview)

    def _draw_preview(self, frame):
        small = cv2.resize(frame, (380, 280))
        status_text = None
        if self.capture_active:
            total = self._sample_count()
            locations = detect_face_locations(small)
            if len(locations) == 1:
                status_text = f"Face locked — capture sample {len(self.samples) + 1} of {total}..."
                now = datetime.now().timestamp() * 1000
                if now - self.last_capture >= SAMPLE_DELAY_MS:
                    top, right, bottom, left = locations[0]
                    encoding = encode_face(small, (top, right, bottom, left))
                    if encoding is not None:
                        self.samples.append(encoding)
                        self.last_capture = now
                        self.progress.config(value=len(self.samples))
                        self.progress_var.set(f"{len(self.samples)} / {total} samples")
                        self.status_var.set(status_text)
                        cv2.rectangle(small, (left, top), (right, bottom), (0, 255, 0), 2)
                        if len(self.samples) >= total:
                            self._finish()
            else:
                status_text = "No face centered — look straight at the camera."
        else:
            status_text = "Live preview. Press Start Capture when ready."
        if status_text:
            self.status_var.set(status_text)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def _sample_count(self):
        try:
            return int(self.samples_var.get().strip())
        except ValueError:
            return SAMPLE_COUNT

    def _finish(self):
        self.capture_active = False
        if len(self.samples) < 3:
            self.status_var.set("Not enough good samples captured. Try again.")
            self.start_btn.config(state="normal")
            return
        self.status_var.set("Verifying face is not already registered...")
        duplicate = self.system.find_by_face(mean_encoding(self.samples))
        new_id = self.id_var.get().strip()
        if duplicate is not None and duplicate["student_id"] != new_id:
            self.status_var.set(
                f"This face is already registered as {duplicate['name']} "
                f"({duplicate['student_id']}). Delete that record first to re-register."
            )
            self.start_btn.config(state="normal")
            return
        try:
            self.system.register(new_id, self.name_var.get().strip(), self.samples)
            self.status_var.set("Registration complete.")
            messagebox.showinfo(
                "Success",
                f"{self.name_var.get().strip()} registered with {len(self.samples)} face samples.",
                parent=self,
            )
            self.destroy()
        except Exception as exc:
            self.capture_active = True
            self.start_btn.config(state="normal")
            messagebox.showerror("Registration failed", str(exc), parent=self)


class RenameDialog(tk.Toplevel):
    def __init__(self, parent, student_id, current_name, on_saved):
        super().__init__(parent)
        self.student_id = student_id
        self.on_saved = on_saved
        self.title(f"Edit Student {student_id}")
        self.transient(parent)
        self.resizable(False, False)
        self.configure(bg=BG)

        panel = ttk.Frame(self, style="Card.TFrame", padding=24)
        panel.pack(fill="both", expand=True, padx=16, pady=16)
        ttk.Label(panel, text=f"Edit name for {student_id}", style="Card.TLabel",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))
        self.name_var = tk.StringVar(value=current_name)
        ttk.Entry(panel, textvariable=self.name_var, width=32).pack(pady=(0, 14))
        buttons = ttk.Frame(panel, style="Card.TFrame")
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Save", style="Primary.TButton", command=self.save).pack(side="left")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
        self.bind("<Return>", lambda e: self.save())

    def save(self):
        new_name = self.name_var.get().strip()
        if not new_name:
            return
        rename_student(self.student_id, new_name)
        self.on_saved()
        self.destroy()


class FaceAttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(1040, 640)
        apply_theme(self)

        self.system = AttendanceSystem(threshold=RECOGNITION_THRESHOLD)
        self.stream = CameraStream(CAMERA_INDEX)
        self.detection = DetectionWorker(self.stream)
        self.running = False
        self.frame_counter = 0
        self.marked_today = set()
        self.today_count = 0
        self.photo = None
        self._overlay = []
        self._preview_key = None
        self._last_draw = 0.0
        self._closed = False

        self._active = tk.BooleanVar(value=False)

        self._build_menu()
        self._build_header()
        self._build_ui()
        self._build_footer()
        self.stream.start()
        self.detection.start()
        self.detection.encodings_wanted = True
        self.marked_today = {r["student_id"] for r in get_attendance()}
        self.running = True
        self._active.set(True)
        self._update_session()
        self.after(50, self.poll)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_footer(self):
        footer = tk.Frame(self, bg=PANEL, height=30)
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=BORDER, height=1).pack(fill="x", side="top")
        tk.Label(
            footer, text="Developed by Mr. Aayush Bhandari · offline · local · private",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 9),
        ).pack(pady=5)

    def _build_menu(self):
        self.menu_bar = tk.Menu(self, bg=PANEL, fg=TEXT, activebackground=ACCENT_DARK,
                                activeforeground="#ffffff", bd=0, relief="flat")
        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg=PANEL, fg=TEXT,
                            activebackground=ACCENT_DARK, activeforeground="#ffffff")
        file_menu.add_command(label="Export Today (CSV)", command=self.export_today_csv)
        file_menu.add_command(label="Export Today (Excel)", command=self.export_today_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        student_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#131821", fg=TEXT,
                               activebackground=ACCENT_DARK, activeforeground="#ffffff")
        student_menu.add_command(label="Register Student", command=self.open_register)
        student_menu.add_command(label="Edit Selected Student", command=self.edit_selected_student)
        student_menu.add_command(label="Delete Selected Student", command=self.delete_selected_student)
        self.menu_bar.add_cascade(label="Students", menu=student_menu)

        settings_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#131821", fg=TEXT,
                                activebackground=ACCENT_DARK, activeforeground="#ffffff")
        settings_menu.add_command(label="Change Login Credentials", command=self.open_password_dialog)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#131821", fg=TEXT,
                            activebackground=ACCENT_DARK, activeforeground="#ffffff")
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=self.menu_bar)

    def _build_header(self):
        header = tk.Frame(self, bg=PANEL, height=64)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        tk.Frame(header, bg=BORDER, height=1).pack(fill="x", side="bottom")

        left = tk.Frame(header, bg=PANEL)
        left.pack(side="left", padx=20, pady=10)
        tk.Label(left, text="◉  Face Attendance", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 16, "bold")).pack(side="left")
        tk.Label(left, text="  offline · local · private", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(10, 0), pady=(6, 0))

        right = tk.Frame(header, bg=PANEL)
        right.pack(side="right", padx=20)
        self.chip_var = tk.StringVar(value="● IDLE")
        self.chip = tk.Label(right, textvariable=self.chip_var, bg=PANEL,
                             fg=MUTED, font=("Segoe UI", 10, "bold"))
        self.chip.pack(side="right")
        self.header_date = tk.Label(right, text="", bg=PANEL, fg=MUTED,
                                   font=("Segoe UI", 10))
        self.header_date.pack(side="right", padx=(0, 18))

    def _build_ui(self):
        self.notebook = ttk.Notebook(self, style="TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        self.tab_live = ttk.Frame(self.notebook, style="TFrame")
        self.tab_dash = ttk.Frame(self.notebook, style="TFrame")
        self.tab_reports = ttk.Frame(self.notebook, style="TFrame")
        self.tab_students = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_live, text="Live Attendance")
        self.notebook.add(self.tab_dash, text="Dashboard")
        self.notebook.add(self.tab_reports, text="Reports")
        self.notebook.add(self.tab_students, text="Students")

        self._build_live_tab()
        self._build_dashboard_tab()
        self._build_reports_tab()
        self._build_students_tab()

        self._refresh_live()
        self._refresh_dashboard()
        self._refresh_students_tab()

    def _build_live_tab(self):
        root = ttk.Frame(self.tab_live, style="TFrame", padding=12)
        root.pack(fill="both", expand=True)

        video_card = ttk.Frame(root, style="Card.TFrame", padding=10)
        video_card.pack(side="left", fill="both", expand=True)
        self.video_canvas = tk.Canvas(video_card, width=640, height=460, bg="#000000",
                                      highlightthickness=1, highlightbackground=BORDER)
        self.video_canvas.pack(fill="both", expand=True)

        video_footer = ttk.Frame(video_card, style="Card.TFrame")
        video_footer.pack(fill="x", pady=(8, 0))
        self.info_var = tk.StringVar()
        ttk.Label(video_footer, textvariable=self.info_var, style="CardH2.TLabel").pack(side="left")
        self.error_var = tk.StringVar()
        ttk.Label(video_footer, textvariable=self.error_var, foreground=RED,
                  style="Card.TLabel").pack(side="right")

        panel = ttk.Frame(root, style="Panel.TFrame", padding=14, width=320)
        panel.pack(side="right", fill="y", padx=(12, 0))
        panel.pack_propagate(False)

        ttk.Label(panel, text="Attendance Session", style="H2.TLabel").pack(anchor="w")
        ttk.Label(panel, text="Students are marked Present once per day.",
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 14))

        self.start_btn = ttk.Button(panel, text="Start Attendance", style="Primary.TButton",
                                    command=self.start_attendance)
        self.start_btn.pack(fill="x", ipady=4)
        ttk.Button(panel, text="Stop Attendance", command=self.stop_attendance).pack(
            fill="x", ipady=4, pady=(8, 0))

        ttk.Separator(panel).pack(fill="x", pady=16)

        self.session_var = tk.StringVar(value="Marked today: 0 / 0")
        ttk.Label(panel, textvariable=self.session_var, style="CardH2.TLabel").pack(anchor="w", pady=(0, 8))

        columns = ("student_id", "name", "time", "status")
        self.live_table = ttk.Treeview(panel, columns=columns, show="headings", height=13)
        for col, text, width in (
            ("student_id", "ID", 56),
            ("name", "Name", 108),
            ("time", "Time", 70),
            ("status", "Status", 60),
        ):
            self.live_table.heading(col, text=text)
            self.live_table.column(col, width=width, anchor="center")
        self.live_table.pack(fill="both", expand=True)

    def _build_dashboard_tab(self):
        root = ttk.Frame(self.tab_dash, style="TFrame", padding=16)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root, style="TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="Attendance Dashboard", style="H1.TLabel").pack(side="left")
        ttk.Label(top, text="Day (BS):").pack(side="left", padx=(24, 6), pady=(10, 0))
        self.dash_day_var = tk.StringVar(value=today_bs())
        ttk.Entry(top, textvariable=self.dash_day_var, width=12).pack(side="left", pady=(10, 0))
        ttk.Button(top, text="Show", command=self._refresh_dashboard).pack(side="left", padx=6, pady=(10, 0))
        ttk.Button(top, text="Today", command=self._dash_today).pack(side="left", pady=(10, 0))

        cards = ttk.Frame(root, style="TFrame")
        cards.pack(fill="x", pady=18)
        self.card_total = tk.StringVar()
        self.card_present = tk.StringVar()
        self.card_absent = tk.StringVar()
        self.card_pct = tk.StringVar()
        for title, var, color in (
            ("Total Students", self.card_total, ACCENT),
            ("Present", self.card_present, GREEN),
            ("Absent", self.card_absent, RED),
            ("Attendance %", self.card_pct, AMBER),
        ):
            box = ttk.Frame(cards, style="Card.TFrame", padding=18)
            box.pack(side="left", padx=8, fill="both", expand=True)
            tk.Frame(box, bg=color, height=3).pack(fill="x", pady=(0, 14))
            ttk.Label(box, text=title, style="CardMuted.TLabel").pack()
            ttk.Label(box, textvariable=var, style="Card.TLabel",
                      font=("Segoe UI", 26, "bold")).pack(pady=(6, 0))

        bottom = ttk.Frame(root, style="TFrame")
        bottom.pack(fill="both", expand=True, pady=(4, 0))
        left = ttk.Frame(bottom, style="Card.TFrame", padding=12)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Absent Students", style="CardH2.TLabel").pack(anchor="w", pady=(0, 8))
        self.absent_list = tk.Listbox(left, height=9, bg=CARD, fg=TEXT, selectbackground=ACCENT_DARK,
                                      highlightthickness=1, highlightbackground=BORDER,
                                      relief="flat", font=("Segoe UI", 10))
        self.absent_list.pack(fill="both", expand=True)

        right = ttk.Frame(bottom, style="Card.TFrame", padding=12)
        right.pack(side="right", fill="both", expand=True, padx=(16, 0))
        ttk.Label(right, text="Last 7 Days", style="CardH2.TLabel").pack(anchor="w", pady=(0, 8))
        columns = ("day", "present", "total", "pct")
        self.seven_table = ttk.Treeview(right, columns=columns, show="headings", height=8)
        for col, text, width in (
            ("day", "Date", 110),
            ("present", "Present", 90),
            ("total", "Total", 90),
            ("pct", "%", 80),
        ):
            self.seven_table.heading(col, text=text)
            self.seven_table.column(col, width=width, anchor="center")
        self.seven_table.pack(fill="both", expand=True)

    def _dash_today(self):
        self.dash_day_var.set(today_bs())
        self._refresh_dashboard()

    def _build_reports_tab(self):
        root = ttk.Frame(self.tab_reports, style="TFrame", padding=16)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Attendance Reports", style="H1.TLabel").pack(anchor="w", pady=(0, 14))

        filters = ttk.Frame(root, style="Card.TFrame", padding=14)
        filters.pack(fill="x")
        ttk.Label(filters, text="From (BS):", style="CardMuted.TLabel").pack(side="left", padx=(0, 4))
        self.rep_from_var = tk.StringVar(value=today_bs())
        ttk.Entry(filters, textvariable=self.rep_from_var, width=12).pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="To (BS):", style="CardMuted.TLabel").pack(side="left", padx=(0, 4))
        self.rep_to_var = tk.StringVar(value=today_bs())
        ttk.Entry(filters, textvariable=self.rep_to_var, width=12).pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Search:", style="CardMuted.TLabel").pack(side="left", padx=(0, 4))
        self.rep_search_var = tk.StringVar()
        ttk.Entry(filters, textvariable=self.rep_search_var, width=18).pack(side="left", padx=(0, 10))
        ttk.Label(filters, text="Status:", style="CardMuted.TLabel").pack(side="left", padx=(0, 4))
        self.rep_status_var = tk.StringVar(value="All")
        ttk.Combobox(filters, textvariable=self.rep_status_var,
                     values=("All", "Present", "Absent"), state="readonly", width=9).pack(side="left", padx=(0, 12))
        ttk.Button(filters, text="Search", style="Primary.TButton",
                   command=self.run_report).pack(side="left")

        self.rep_count_var = tk.StringVar()
        ttk.Label(root, textvariable=self.rep_count_var, style="Muted.TLabel").pack(anchor="w", pady=(8, 6))

        columns = ("student_id", "name", "date", "time", "status")
        self.report_table = ttk.Treeview(root, columns=columns, show="headings", height=13)
        for col, text, width in (
            ("student_id", "ID", 90),
            ("name", "Name", 200),
            ("date", "Date", 130),
            ("time", "Time", 90),
            ("status", "Status", 90),
        ):
            self.report_table.heading(col, text=text)
            self.report_table.column(col, width=width, anchor="center")
        self.report_table.pack(fill="both", expand=True, pady=(4, 0))

        export_buttons = ttk.Frame(root, style="TFrame")
        export_buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(export_buttons, text="Export CSV", command=self.export_report_csv).pack(side="left")
        ttk.Button(export_buttons, text="Export Excel", command=self.export_report_excel).pack(side="left", padx=6)
        ttk.Label(export_buttons, text="Absent rows show the date range and no time.",
                  style="Muted.TLabel").pack(side="right", pady=(6, 0))

        self._last_report = []

    def _build_students_tab(self):
        root = ttk.Frame(self.tab_students, style="TFrame", padding=16)
        root.pack(fill="both", expand=True)

        ttk.Label(root, text="Student Management", style="H1.TLabel").pack(anchor="w", pady=(0, 14))

        toolbar = ttk.Frame(root, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="＋ Register Student", style="Primary.TButton",
                   command=self.open_register).pack(side="left")
        ttk.Button(toolbar, text="Edit Selected", command=self.edit_selected_student).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected_student).pack(side="left")

        self.students_table = ttk.Treeview(root, columns=("student_id", "name", "created_at"),
                                           show="headings", height=16)
        for col, text, width in (
            ("student_id", "ID", 130),
            ("name", "Name", 300),
            ("created_at", "Registered", 220),
        ):
            self.students_table.heading(col, text=text)
            self.students_table.column(col, width=width, anchor="w")
        self.students_table.pack(fill="both", expand=True)

    def start_attendance(self):
        rows = get_attendance()
        self.marked_today = {r["student_id"] for r in rows}
        self.running = True
        self._active.set(True)
        self.detection.encodings_wanted = True
        self._update_session()
        self._log(f"Attendance session started at {datetime.now().strftime('%H:%M:%S')}")

    def stop_attendance(self):
        self.running = False
        self._active.set(False)
        self.detection.encodings_wanted = False
        self._update_session()
        self._log(f"Attendance session stopped at {datetime.now().strftime('%H:%M:%S')}")

    def _update_session(self):
        if self.running:
            self.chip.configure(fg=GREEN)
            self.chip_var.set("● RUNNING")
        else:
            self.chip.configure(fg=MUTED)
            self.chip_var.set("● IDLE")

    def _refresh_live(self):
        for row in self.live_table.get_children():
            self.live_table.delete(row)
        rows = get_attendance()
        for r in rows:
            self.live_table.insert(
                "", "end", values=(r["student_id"], r["name"], r["time"], r["status"])
            )
        self.today_count = len(rows)
        self.session_var.set(
            f"Marked today: {self.today_count} / {len(self.system.students)}"
        )

    def _refresh_dashboard(self):
        day = parse_date(self.dash_day_var.get()) or date.today().isoformat()
        rows = get_attendance(day)
        total = len(self.system.students)
        present = len(rows)
        absent = max(total - present, 0)
        pct = (present / total * 100) if total else 0.0
        self.card_total.set(str(total))
        self.card_present.set(str(present))
        self.card_absent.set(str(absent))
        self.card_pct.set(f"{pct:.1f}%")

        self.absent_list.delete(0, "end")
        for student in get_absentees(day, day):
            self.absent_list.insert("end", f"{student['student_id']}  {student['name']}")

        for row in self.seven_table.get_children():
            self.seven_table.delete(row)
        today = date.today()
        for offset in range(6, -1, -1):
            d = (today - timedelta(days=offset)).isoformat()
            p = len(get_attendance(d))
            pct_day = (p / total * 100) if total else 0.0
            self.seven_table.insert(
                "", "end", values=(to_bs_str(d), p, total, f"{pct_day:.1f}%")
            )

    def _refresh_students_tab(self):
        for row in self.students_table.get_children():
            self.students_table.delete(row)
        for s in list_students_meta():
            self.students_table.insert(
                "", "end", values=(s["student_id"], s["name"], self._bs_display(s["created_at"]))
            )

    def _bs_display(self, text):
        ad = bs_date_from_ad(text)
        if ad is None:
            return text
        return f"{ad.isoformat()}{text[10:16] if len(text) > 16 else ''}"

    def run_report(self):
        start = parse_date(self.rep_from_var.get()) or date.today().isoformat()
        end = parse_date(self.rep_to_var.get()) or date.today().isoformat()
        if start > end:
            start, end = end, start
        start_bs = to_bs_str(start)
        end_bs = to_bs_str(end)
        search = self.rep_search_var.get().strip().lower()
        status = self.rep_status_var.get()

        results = []
        present_ids = get_present_ids(start, end)
        if status in ("Present", "All"):
            for r in get_attendance_between(start, end):
                if not search or search in r["name"].lower() or search in r["student_id"].lower():
                    results.append(r)
        if status in ("Absent", "All"):
            for s in list_students_meta():
                if s["student_id"] in present_ids:
                    continue
                if not search or search in s["name"].lower() or search in s["student_id"].lower():
                    results.append(
                        {
                            "student_id": s["student_id"],
                            "name": s["name"],
                            "date": f"{start_bs} to {end_bs}",
                            "time": "--",
                            "status": "Absent",
                        }
                    )

        for row in self.report_table.get_children():
            self.report_table.delete(row)
        for r in results:
            self.report_table.insert(
                "",
                "end",
                values=(r["student_id"], r["name"], to_bs_str(r["date"]), r["time"], r["status"]),
            )
        self.rep_count_var.set(
            f"{len(results)} record(s)  ·  {start_bs} → {end_bs} (BS)  ·  filter: {status}"
        )
        self._last_report = results
        self._last_range = (start_bs, end_bs)

    def export_report_csv(self):
        self._export_current(mode="csv")

    def export_report_excel(self):
        self._export_current(mode="excel")

    def _export_current(self, mode="csv"):
        if not self._last_report:
            messagebox.showinfo("Nothing to export", "Run a report search first.")
            return
        start, end = self._last_range
        if mode == "csv":
            path = export_attendance_range(self._last_report, start, end)
        else:
            path = export_attendance_excel(self._last_report, start, end)
        self._log(f"Exported report to {path}")
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")

    def export_today_csv(self):
        self._export_today("csv")

    def export_today_excel(self):
        self._export_today("excel")

    def _export_today(self, mode="csv"):
        rows = get_attendance()
        day_bs = today_bs()
        if mode == "csv":
            path = export_attendance(rows, day_bs)
        else:
            path = export_attendance_excel(rows, day_bs, day_bs)
        self._log(f"Exported today's attendance to {path}")
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")

    def open_register(self):
        RegisterDialog(self, self.stream, self.system)
        self.system.reload_students()
        self._refresh_students_tab()
        self._refresh_dashboard()

    def _selected_student(self):
        selection = self.students_table.selection()
        if not selection:
            messagebox.showinfo("No selection", "Select a student first.")
            return None
        values = self.students_table.item(selection[0], "values")
        return values[0], values[1]

    def edit_selected_student(self):
        selected = self._selected_student()
        if not selected:
            return
        student_id, current_name = selected
        RenameDialog(self, student_id, current_name, self._after_students_change)

    def delete_selected_student(self):
        selected = self._selected_student()
        if not selected:
            return
        student_id, name = selected
        if messagebox.askyesno("Confirm delete", f"Delete {name} ({student_id}) and their face data?"):
            self.system.remove_student(student_id)
            self._log(f"Deleted student {student_id}")
            self._after_students_change()

    def _after_students_change(self):
        self.system.reload_students()
        self._refresh_students_tab()
        self._refresh_dashboard()
        self._refresh_live()
        self._update_session()

    def open_password_dialog(self):
        PasswordDialog(self)

    def show_about(self):
        messagebox.showinfo(
            "About",
            f"{WINDOW_TITLE}\n\nV2 - Proper application\n"
            "Local, privacy-focused attendance. No cloud, no external APIs.\n"
            "Face data is stored as numerical embeddings only.\n\n"
            "Developed by Mr. Aayush Bhandari",
        )

    def _log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def poll(self):
        if self._closed:
            return
        try:
            self.header_date.config(
                text=f"{today_bs_display()}  ·  {datetime.now().strftime('%H:%M:%S')}"
            )
            if self.stream.error and not self.error_var.get():
                self.error_var.set(f"Camera error: {self.stream.error}")
            result = None
            try:
                result = self.detection.queue.get_nowait()
            except Exception:
                result = None
            if result is not None:
                try:
                    self._process_result(result)
                except Exception as exc:
                    print(f"[error] {exc!r}", flush=True)
            self._draw_preview()
        except Exception as exc:
            print(f"[poll error] {exc!r}", flush=True)
        self.after(POLL_MS, self.poll)

    def _draw_preview(self):
        frame = self.stream.latest
        if frame is None:
            return
        now = time.time()
        if now - self._last_draw < 0.05:
            return
        key = (self.stream.frame_id, self.frame_counter)
        if key == self._preview_key:
            return
        self._preview_key = key
        self._last_draw = now
        display = frame.copy()
        for top, right, bottom, left, text, color in self._overlay:
            cv2.rectangle(display, (left, top), (right, bottom), color, 2)
            cv2.putText(
                display, text, (left, max(top - 8, 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
            )
        cv2.putText(
            display,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 200, 80),
            2,
        )
        selected = self.notebook.nametowidget(self.notebook.select())
        if selected is self.tab_live:
            rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb)
            self.photo = ImageTk.PhotoImage(image)
            self.video_canvas.create_image(0, 0, image=self.photo, anchor="nw")

    def _process_result(self, result):
        self.frame_counter += 1
        overlay = []
        for i, (top, right, bottom, left) in enumerate(result.locations):
            encoding = result.encodings[i] if i < len(result.encodings) else None
            matched = self.system.recognize(encoding) if encoding is not None else None
            if matched is not None:
                color = (0, 200, 140)
                text = f"{matched['name']} ({matched['student_id']})"
                if (
                    self.running
                    and self.frame_counter % MARK_EVERY_FRAMES == 0
                    and matched["student_id"] not in self.marked_today
                    and mark_attendance(matched["student_id"], matched["name"])
                ):
                    self.marked_today.add(matched["student_id"])
                    self._log(
                        f"Attendance marked: {matched['name']} at "
                        f"{datetime.now().strftime('%H:%M:%S')}"
                    )
                    self._refresh_live()
            else:
                color = (0, 80, 255)
                text = "Unknown"
            overlay.append((top, right, bottom, left, text, color))
        self._overlay = overlay

        total = len(self.system.students)
        present = len(self.marked_today) if self.running else self.today_count
        self.info_var.set(
            f"Students: {total}   ·   Present: {present}   ·   "
            f"{'LIVE' if self.running else 'Preview'}"
        )
        self.session_var.set(f"Marked today: {present} / {total}")

    def on_close(self):
        self._closed = True
        self.stream.stop()
        self.detection.stop()
        self.destroy()


def _selftest():
    import os
    import sys
    import traceback

    report = Path("selftest_result.txt")
    try:
        import dlib  # noqa: F401
        import face_recognition
        import openpyxl  # noqa: F401
        from PIL import __version__ as pil_version

        import cv2
        from nepali_calendar import today_bs

        for kind in (
            "dlib_face_recognition_resnet_model_v1",
            "dlib_face_detection_model_location",
            "pose_predictor_68_point_model_location",
        ):
            loc = face_recognition.api.__dict__.get(kind)
            if callable(loc):
                path = loc()
                assert path and os.path.exists(path), f"missing model: {kind} -> {path!r}"
        assert dlib.get_frontal_face_detector() is not None
        locs = detect_face_locations(np.zeros((120, 160, 3), dtype=np.uint8))
        assert isinstance(locs, list)
        best, dist = mean_encoding_match()
        assert best == 0 and dist >= 0.0
        AttendanceSystem().reload_students()
        report.write_text(
            f"OK {cv2.__version__} | pil {pil_version} | bs {today_bs()}\n",
            encoding="utf-8",
        )
        return 0
    except BaseException:
        report.write_text(traceback.format_exc(), encoding="utf-8")
        return 1


def mean_encoding_match():
    from face_utils import match_known

    return match_known(np.zeros(128, dtype=np.float64), [np.zeros(128, dtype=np.float64)])


def _dump_crash(exc):
    try:
        import os
        import traceback

        crash = Path(os.environ.get("TEMP", ".")) / "faceatt_crash.log"
        crash.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass


def _dpi_aware():
    try:
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _capture_shots(outdir):
    import sys
    import time
    from PIL import ImageGrab

    _dpi_aware()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    import database as _db

    for meta in _db.list_students_meta():
        _db.delete_student(meta["student_id"])
    demo = ["Aarav Sharma", "Nirvana Thapa", "Riya Karki", "Saugat Shrestha"]
    for i, name in enumerate(demo, 1):
        _db.add_student(f"D{i:04d}", name, np.random.default_rng(i).random(128))
        for days_ago in range(0, 8):
            if (days_ago + i) % 3:
                _db.mark_attendance(f"D{i:04d}", name, date.today() - timedelta(days=days_ago))

    def grab(window, name):
        window.update_idletasks()
        x, y = window.winfo_rootx(), window.winfo_rooty()
        w, h = window.winfo_width(), window.winfo_height()
        path = outdir / f"{name}.png"
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)
        sys.stdout.write(f"saved {path} ({w}x{h})\n")
        sys.stdout.flush()

    login = LoginWindow()
    login.geometry("1024x640")
    login.update()
    grab(login, "0-login")
    login.destroy()

    app = FaceAttendanceApp()
    app.geometry("1366x768")
    time.sleep(1.0)
    app.lift()
    for index, name in ((0, "1-live"), (2, "2-dashboard"), (3, "3-reports"), (1, "4-students")):
        app.notebook.select(index)
        for _ in range(30):
            app.update()
            time.sleep(0.05)
        grab(app, name)
    app.on_close()
    return 0


def main():
    args = __import__("sys").argv
    if "--selftest" in args:
        raise SystemExit(_selftest())
    if "--capture-shots" in args:
        raise SystemExit(_capture_shots(args[args.index("--capture-shots") + 1]))
    try:
        LoginWindow().mainloop()
    except BaseException:
        _dump_crash(__import__("sys").exc_info())
        raise


if __name__ == "__main__":
    main()