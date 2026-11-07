@echo off
cd /d "%~dp0"

echo ====================================================
echo Starting Smash Bros Web Server (for Mobile and PC)...
echo ====================================================

REM 1. Check Python in Local AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" server.py
    goto FINISH
)

REM 2. Check py launcher
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py server.py
    goto FINISH
)

REM 3. Check python in PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python server.py
    goto FINISH
)

echo [ERROR] Python not found!
pause
exit /b 1

:FINISH
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server stopped with an error.
    pause
)

