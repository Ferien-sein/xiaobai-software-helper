@echo off
rem ============================================================
rem  Build the Windows executable (onedir mode).
rem
rem  NOTE: this file is intentionally pure ASCII. cmd.exe reads
rem  .bat files using the system ANSI codepage, so UTF-8 Chinese
rem  here would turn into garbage and break the script.
rem
rem  Output: dist\xiaobai-software-helper\
rem          (the whole folder must stay together - _internal
rem           next to the .exe is required at runtime)
rem ============================================================
setlocal
cd /d "%~dp0"

echo.
echo  [1/3] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   ERROR: python was not found in PATH.
  echo   Install Python 3.9+ from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH" during setup.
  echo.
  pause
  exit /b 1
)
python -c "import sys; print('       Python', sys.version.split()[0])"

echo.
echo  [2/3] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
  echo        Installing PyInstaller...
  python -m pip install --disable-pip-version-check pyinstaller
  if errorlevel 1 (
    echo.
    echo   ERROR: failed to install PyInstaller. Check your network.
    echo.
    pause
    exit /b 1
  )
)
python -c "import PyInstaller; print('       PyInstaller', PyInstaller.__version__)"

echo.
echo  [3/3] Building...
python -m PyInstaller --noconfirm --clean --onedir --noconsole ^
  --name "xiaobai-software-helper" ^
  --distpath dist --workpath build --specpath build ^
  "src\app.py"
if errorlevel 1 (
  echo.
  echo   ERROR: build failed. See the messages above.
  echo.
  pause
  exit /b 1
)

echo.
echo  ============================================================
echo   Done.
echo   Output folder: %cd%\dist\xiaobai-software-helper
echo   Run:           dist\xiaobai-software-helper\xiaobai-software-helper.exe
echo.
echo   Keep the _internal folder together with the .exe.
echo  ============================================================
echo.
pause
