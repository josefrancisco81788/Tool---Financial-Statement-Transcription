@echo off
title Financial Statement Transcription Tool
color 0A

echo.
echo ========================================
echo   Financial Statement Transcription Tool
echo ========================================
echo.

echo [1/3] Cleaning up existing processes...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8560') do (
    echo Killing process %%i...
    taskkill /PID %%i /F >nul 2>&1
)

echo [2/3] Waiting for cleanup...
timeout /t 2 /nobreak >nul

echo [3/3] Starting Streamlit...
echo.
echo Opening http://localhost:8560 in your browser...
echo Press Ctrl+C to stop the application
echo.

streamlit run app.py --server.port 8560 --server.headless false

pause 