@echo off
cd /d "%~dp0backend"
if not exist .env (
  echo ERROR: backend\.env not found.
  echo Copy backend\.env.example to backend\.env and configure MongoDB Atlas first.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8000
