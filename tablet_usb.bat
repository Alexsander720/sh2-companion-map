@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "%~dp0server.py" --tablet %*
) else (
    python "%~dp0server.py" --tablet %*
)
