@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%tools\iniciar_software.ps1"
if errorlevel 1 (
  echo.
  echo Falha ao iniciar o Software Esquadrias. Leia a mensagem acima.
  pause
  exit /b 1
)
exit /b 0
