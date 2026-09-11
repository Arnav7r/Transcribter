@echo off
title InstaTranscribe Hindi Web App
echo =========================================================
echo    Starting InstaTranscribe Hindi Web Application...
echo =========================================================
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" run.py
pause

