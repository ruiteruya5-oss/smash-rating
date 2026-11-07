@echo off
cd /d "%~dp0"

echo ====================================================
echo Starting Smash Bros Rating System...
echo ====================================================

REM 1. Check Python in Local AppData
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    echo Using Python 3.12: %LOCALAPPDATA%\Programs\Python\Python312\python.exe
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" app.py
    goto FINISH
)

REM 2. Check py launcher
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Using py launcher
    py app.py
    goto FINISH
)

REM 3. Check python in PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo Using python in PATH
    python app.py
    goto FINISH
)

echo [ERROR] Python not found!
pause
exit /b 1

:FINISH
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Program exited with an error.
    pause
)
