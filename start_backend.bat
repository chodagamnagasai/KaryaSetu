@echo off
<<<<<<< HEAD
setlocal
cd /d "%~dp0backend"
if not exist .env (
  echo ERROR: backend\.env not found.
  echo Copy backend\.env.example to backend\.env and configure MongoDB Atlas + Gemini first.
  pause
  exit /b 1
)

echo Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo ERROR: dependency installation failed. Backend was not started.
  pause
  exit /b 1
)

echo Verifying backend imports...
python -c "import fastapi, pydantic, pandas; from google import genai; print('FastAPI:', fastapi.__version__); print('Pydantic:', pydantic.__version__); print('Pandas:', pandas.__version__); print('Gemini SDK: OK')"
if errorlevel 1 (
  echo.
  echo ERROR: backend dependencies are incomplete.
  pause
  exit /b 1
)

python -m uvicorn server:app --host 127.0.0.1 --port 8000
endlocal
=======
cd /d "%~dp0backend"
if not exist .env (
  echo ERROR: backend\.env not found.
  echo Copy backend\.env.example to backend\.env and configure MongoDB Atlas first.
  pause
  exit /b 1
)
python -m pip install -r requirements.txt
python -m uvicorn server:app --host 127.0.0.1 --port 8000
>>>>>>> f23ae37521d7e6b1487fa61cf3628a3e1d1a29ca
