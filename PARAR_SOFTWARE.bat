@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%tools\parar_software.ps1"
if errorlevel 1 pause
exit /b %errorlevel%
