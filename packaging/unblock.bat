@echo off
rem ============================================================
rem  Remove the "downloaded from the internet" mark from every
rem  file in this folder, so Windows stops asking you to confirm
rem  before running the program.
rem
rem  Why this is needed: the .exe has no digital signature (making
rem  one for a private tool is not practical), so Windows treats it
rem  as "unknown publisher". Unblocking removes the internet-origin
rem  flag, which is the part Windows is asking you about.
rem
rem  This file must stay pure ASCII: cmd.exe reads .bat with the
rem  system ANSI codepage, so UTF-8 Chinese would turn into garbage.
rem ============================================================
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   Removing the "downloaded from internet" mark...
echo   Folder: %~dp0
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d='%~dp0'; $n=0; $t=0; Get-ChildItem -LiteralPath $d -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $t++; try { Unblock-File -LiteralPath $_.FullName -ErrorAction Stop } catch {} ; $n++ }; Write-Host ''; Write-Host ('  Done. ' + $n + ' files in ' + $t + ' processed.') -ForegroundColor Green; Write-Host '  Now close this window and start the program normally.' -ForegroundColor Green"
echo.
echo   Press any key to close...
pause >nul
