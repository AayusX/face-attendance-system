@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==============================================
echo  Face Attendance - portable Windows build
echo ==============================================
echo.

rem ---- locate a suitable Python ----
set PY=
where py >nul 2>nul && set "PY=py -3.12"
if not defined PY (
  python -c "import sys;sys.exit(0)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [ERROR] Python not found. Install Python 3.12 from python.org
  echo         and tick "Add python.exe to PATH", then re-run this script.
  pause & exit /b 1
)

rem ---- create the build venv ----
if not exist build_venv (
  %PY% -m venv build_venv
  if errorlevel 1 (
    echo [ERROR] Could not create build_venv.
    pause & exit /b 1
  )
)
call build_venv\Scripts\activate.bat

rem ---- install deps + pyinstaller (Windows ships dlib/opencv wheels) ----
python -m pip install --upgrade pip wheel
python -m pip install "setuptools<81"
python -m pip install -r requirements-windows.txt
if errorlevel 1 (
  echo [ERROR] Failed to install dependencies.
  pause & exit /b 1
)
python -m pip install pyinstaller
if errorlevel 1 (
  echo [ERROR] Failed to install PyInstaller.
  pause & exit /b 1
)

rem ---- build the bundle ----
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
set GUI_CONSOLE=0
python -m PyInstaller app.spec --noconfirm
if errorlevel 1 (
  echo [ERROR] PyInstaller build failed. See output above.
  pause & exit /b 1
)

rem ---- verify the bundle ----
dist\FaceAttendance\FaceAttendance.exe --selftest
if not exist selftest_result.txt (
  echo [WARN] selftest did not produce a report file.
) else (
  type selftest_result.txt
  findstr /C:"OK " selftest_result.txt >nul && (echo [selftest] PASSED) || (echo [ERROR] selftest FAILED & pause & exit /b 1)
  del selftest_result.txt
)

rem ---- zip it ----
if exist FaceAttendance-portable.zip del FaceAttendance-portable.zip
powershell -NoProfile -Command "Compress-Archive -Force -Path 'dist\FaceAttendance' -DestinationPath 'FaceAttendance-portable.zip'"

echo.
echo ==============================================
echo  DONE. Portable bundle created:
echo    dist\FaceAttendance\     (folder, zip in FaceAttendance-portable.zip)
echo.
echo  Copy the folder (or the zip) to any Windows PC and run FaceAttendance.exe.
echo  No Python or packages needed there. Run with --selftest to verify.
echo ==============================================
pause
endlocal