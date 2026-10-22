@echo off
setlocal
cd /d "%~dp0"
echo Gemini real: exige GEMINI_API_KEY valida no arquivo .env.
echo Encerre a demonstracao anterior antes de iniciar. Pode consumir cota da API.
".venv\Scripts\python.exe" -m tests.ui_server --port 8082 --serve-frontend --real-ai
pause
