@echo off
REM Script to create superuser account on Windows

echo ============================================================
echo Creating Superuser Account
echo ============================================================
echo.

python scripts\create_superuser.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to create superuser
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Script completed successfully!
pause
