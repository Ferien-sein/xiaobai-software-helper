@echo off
rem ---------------------------------------------------------------
rem  Launcher for the requirement-form app.
rem
rem  NOTE: this file must stay pure ASCII. cmd.exe reads .bat using
rem  the system ANSI codepage; if Chinese characters are written here
rem  in UTF-8, they turn into garbage and the exe name cannot be
rem  resolved. So the exe is located by a wildcard pattern instead.
rem
rem  Use this if double-clicking the .exe does not work.
rem ---------------------------------------------------------------
cd /d "%~dp0"
set "TARGET="
for %%F in ("*.exe") do (
  if not defined TARGET set "TARGET=%%~fF"
)
if not defined TARGET (
  echo.
  echo   ERROR: no .exe found in this folder.
  echo   Keep the .exe and the _internal folder together.
  echo.
  pause
  exit /b 1
)
start "" "%TARGET%"
