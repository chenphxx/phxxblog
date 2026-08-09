@echo off
chcp 65001 >nul
title phxxblog - 一键启动
cd /d "%~dp0"

echo ============================================
echo   phxxblog 一键启动脚本
echo ============================================
echo.

REM 检查后端虚拟环境
if not exist "backend\.venv\Scripts\python.exe" (
    echo [错误] 未找到后端虚拟环境, 请先手动执行:
    echo.
    echo     cd backend
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 检查前端依赖
if not exist "frontend\node_modules" (
    echo [错误] 未找到前端依赖, 请先手动执行:
    echo.
    echo     cd frontend
    echo     npm install
    echo.
    pause
    exit /b 1
)

REM 检查后端配置文件
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo [提示] 已生成 backend\.env, 请填写数据库密码后重新运行
    echo.
    pause
    exit /b 1
)

REM 端口占用提示
netstat -ano | findstr LISTENING | findstr ":8000" >nul && echo [提示] 8000 端口已被占用, 可能已有后端在运行
netstat -ano | findstr LISTENING | findstr ":5173" >nul && echo [提示] 5173 端口已被占用, 可能已有前端在运行
echo.

echo 启动后端(窗口请保留)...
start "phxxblog-backend" /d "%~dp0backend" cmd /k ".venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"

echo 启动前端(窗口请保留)...
start "phxxblog-frontend" /d "%~dp0frontend" cmd /k "npm.cmd run dev"

echo.
echo 等待服务启动...
timeout /t 5 /nobreak >nul

echo 检查服务状态:
netstat -ano | findstr LISTENING | findstr ":8000" >nul && echo   [OK] 后端已启动  http://127.0.0.1:8000/docs || echo   [失败] 后端未启动, 请看后端窗口的报错
netstat -ano | findstr LISTENING | findstr ":5173" >nul && echo   [OK] 前端已启动  http://localhost:5173 || echo   [失败] 前端未启动, 请看前端窗口的报错
echo.

echo 在浏览器中打开博客前台...
start "" http://localhost:5173
echo.
echo 访问地址:
echo   博客前台: http://localhost:5173
echo   管理后台: http://localhost:5173/#/admin
echo   接口文档: http://127.0.0.1:8000/docs
echo.
pause
