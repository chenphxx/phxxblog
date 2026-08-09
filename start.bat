@echo off
title phxxblog launcher
cd /d "%~dp0"

echo ============================================
echo   phxxblog launcher
echo ============================================
echo.

if exist "backend\.venv\Scripts\python.exe" goto :backend_ok
echo [ERROR] Backend virtual environment not found.
echo Please run these commands first:
echo     cd backend
echo     python -m venv .venv
echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
pause
exit /b 1
:backend_ok

if exist "frontend\node_modules" goto :frontend_ok
echo [ERROR] Frontend dependencies not found.
echo Please run:  cd frontend  ^&^&  npm install
echo.
pause
exit /b 1
:frontend_ok

if exist "backend\.env" goto :env_ok
copy "backend\.env.example" "backend\.env" >nul
echo [HINT] backend\.env has been created.
echo Edit it to set your MySQL password, then run this script again.
echo.
pause
exit /b 1
:env_ok

netstat -ano | findstr LISTENING | findstr ":8000" >nul && echo [HINT] port 8000 already in use
netstat -ano | findstr LISTENING | findstr ":5173" >nul && echo [HINT] port 5173 already in use
echo.

echo Starting backend  http://127.0.0.1:8000 ...
start "phxxblog-backend" /d "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo Starting frontend http://localhost:5173 ...
start "phxxblog-frontend" /d "%~dp0frontend" cmd /k "npm.cmd run dev"

echo.
echo Waiting for services...
timeout /t 5 /nobreak >nul

echo Status:
netstat -ano | findstr LISTENING | findstr ":8000" >nul && echo   [OK] backend  http://127.0.0.1:8000/docs || echo   [FAIL] backend did not start
netstat -ano | findstr LISTENING | findstr ":5173" >nul && echo   [OK] frontend http://localhost:5173 || echo   [FAIL] frontend did not start
echo.

start "" http://localhost:5173
echo URLs:
echo   Blog:     http://localhost:5173
echo   Admin:    http://localhost:5173/#/admin
echo   API docs: http://127.0.0.1:8000/docs
echo.
pause
