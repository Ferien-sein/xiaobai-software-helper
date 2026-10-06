@echo off
rem ============================================================
rem  Run the app straight from source (no packaging needed).
rem  Pure ASCII on purpose: cmd.exe reads .bat with the system
rem  ANSI codepage, so UTF-8 Chinese here would become garbage.
rem ============================================================
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   ERROR: python was not found in PATH.
  echo   Install Python 3.9+ and tick "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

rem Start without a console window when possible.
start "" pythonw "src\app.py" 2>nul
if errorlevel 1 start "" python "src\app.py"
