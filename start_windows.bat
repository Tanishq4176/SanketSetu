@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher was not found. Install Python 3.12 from https://www.python.org/downloads/ and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  py -3.12 -m venv .venv
  if errorlevel 1 py -m venv .venv
)
call ".venv\Scripts\activate.bat"
if not exist ".env" copy ".env.example" ".env" >nul
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed. Check your internet connection and Python version.
  pause
  exit /b 1
)
echo.
echo Starting SanketSetu backend in a separate terminal...
start "SanketSetu backend" /D "%CD%" "%CD%\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
timeout /t 3 >nul
start "" http://127.0.0.1:8000
echo SanketSetu should be available at http://127.0.0.1:8000
pause
