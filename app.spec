# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the Face Attendance System.
# Builds a portable one-folder bundle in dist/FaceAttendance/ that can be
# copied to any machine without installing Python or any pip packages.
#   Linux : pyinstaller app.spec --noconfirm
#   Windows: build_windows.bat   (see that file)

import os

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

datas = []
binaries = []
hiddenimports = []

# nepali_datetime ships data/CLDR tables and submodules - collect everything.
for pkg in ("nepali_datetime",):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# dlib's trained model .dat files live in face_recognition_models. These are
# loaded at runtime via pkg_resources, so they must keep their package paths.
datas += collect_data_files("face_recognition_models")
hiddenimports += collect_submodules("face_recognition_models")

hiddenimports += [
    "dlib",
    "cv2",
    "face_recognition",
    "face_recognition_models",
    "pkg_resources",
    "PIL.ImageTk",
    "PIL.Image",
    "tkinter",
    "openpyxl",
    "et_xmlfile",
]

excludes = [
    "pytest",
    "pandas",
    "matplotlib",
    "scipy",
    "IPython",
    "jupyter",
    "PyQt5",
    "PyQt6",
    "PySide6",
    "notebook",
]

CONSOLE = os.environ.get("GUI_CONSOLE") == "1"

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FaceAttendance",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=CONSOLE,
    icon="assets/app.ico" if os.name == "nt" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FaceAttendance",
)