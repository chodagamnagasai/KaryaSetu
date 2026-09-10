@echo off
cd /d "%~dp0"
echo KaryaSetu Gemini AI setup
echo.
if not exist "backend\.env" (
  echo ERROR: backend\.env not found.
  echo Copy backend\.env.example to backend\.env and add your MongoDB and Gemini API credentials.
  pause
  exit /b 1
)
findstr /B "GEMINI_API_KEY=" backend\.env
echo.
echo Gemini AI uses the API key configured in backend\.env.
echo No Ollama installation is required.
pause
