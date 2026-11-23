@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 python -m venv .venv
    if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -c "import sys; raise SystemExit(sys.version_info < (3,11) or sys.maxsize < 2**32)"
if errorlevel 1 (
    echo Please install 64-bit Python 3.11 or newer.
    goto :error
)
".venv\Scripts\python.exe" tools\bootstrap.py %*
if errorlevel 1 goto :error
".venv\Scripts\python.exe" server.py %*
if errorlevel 1 goto :error
exit /b 0
:error
echo Startup failed. See the message above.
pause
exit /b 1
