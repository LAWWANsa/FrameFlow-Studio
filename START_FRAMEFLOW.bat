@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.11+ is required. Install from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements.txt
py -3 frameflow_studio.py
if errorlevel 1 pause
