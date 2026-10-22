@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente Python ausente. Consulte a instalacao no README.md.
  pause
  exit /b 1
)
if not exist "frontend\dist\index.html" (
  echo Frontend ainda nao compilado. Execute npm ci e npm run build em frontend.
  pause
  exit /b 1
)
echo Abra http://localhost:8082 depois da mensagem de inicializacao.
echo Mantenha esta janela aberta. Ctrl+C para encerrar.
".venv\Scripts\python.exe" -m tests.ui_server --port 8082 --serve-frontend
pause
