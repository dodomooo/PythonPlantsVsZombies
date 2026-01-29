@echo off
chcp 65001 > nul 2>&1
setlocal EnableDelayedExpansion
title 植物大战僵尸 - 一键启动
color 0A

echo ═══════════════════════════════════════════════════
echo    植物大战僵尸 - 疯狂模式
echo ═══════════════════════════════════════════════════
echo.
echo 检测到系统: Windows (CMD)
echo.

REM 检查 Python 是否安装
set PYTHON_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python3
    ) else (
        echo [错误] 未检测到 Python，请先安装 Python 3.7+
        echo.
        echo 下载地址: https://www.python.org/downloads/
        echo 安装时请勾选 'Add Python to PATH'
        echo.
        pause
        exit /b 1
    )
)

echo [√] Python 环境已就绪
echo.

REM 检查依赖
echo 正在检查游戏依赖...

REM 检查 pygame
%PYTHON_CMD% -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [!] 缺少 pygame 依赖，正在安装...
    %PYTHON_CMD% -m pip install pygame requests
)

REM 检查 Flask
%PYTHON_CMD% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [!] 缺少 Flask 依赖（服务端），正在安装...
    cd server
    %PYTHON_CMD% -m pip install -r requirements.txt
    cd ..
)

echo [√] 所有依赖已就绪
echo.

REM 显示菜单
:menu
echo 请选择启动模式：
echo.
echo   [1] 完整在线模式（推荐）- 包含排行榜和数据统计
echo   [2] 离线模式 - 无需服务器，单机游戏
echo   [3] 仅启动服务器
echo   [4] 退出
echo.

set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" goto online
if "%choice%"=="2" goto offline
if "%choice%"=="3" goto server_only
if "%choice%"=="4" goto end

echo [错误] 无效选项，请重新输入
echo.
goto menu

:online
echo.
echo ═══════════════════════════════════════════════════
echo    正在启动完整在线模式...
echo ═══════════════════════════════════════════════════
echo.
echo [1/2] 正在启动游戏服务器...

REM 启动服务器（后台运行）
start /B "PvZ Server" %PYTHON_CMD% start_server.py > server.log 2>&1

echo 等待服务器启动...
timeout /t 3 /nobreak > nul

echo [2/2] 正在启动游戏客户端...
echo.
echo 提示：关闭游戏窗口后，记得关闭服务器窗口
echo.

REM 启动游戏（前台运行）
%PYTHON_CMD% start_game.py

REM 游戏结束后尝试停止服务器
echo.
echo 正在停止服务器...
taskkill /F /FI "WINDOWTITLE eq PvZ Server*" >nul 2>&1

timeout /t 1 /nobreak > nul
echo 服务器已停止
goto cleanup

:offline
echo.
echo ═══════════════════════════════════════════════════
echo    正在启动离线模式...
echo ═══════════════════════════════════════════════════
echo.
%PYTHON_CMD% main.py
goto cleanup

:server_only
echo.
echo ═══════════════════════════════════════════════════
echo    正在启动游戏服务器...
echo ═══════════════════════════════════════════════════
echo.
echo 服务器地址: http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo.
%PYTHON_CMD% start_server.py
goto cleanup

:cleanup
echo.
echo 游戏已关闭，感谢游玩！

REM 清理临时文件
if exist server.log del /F /Q server.log >nul 2>&1
if exist server_error.log del /F /Q server_error.log >nul 2>&1

timeout /t 2 /nobreak > nul
goto end

:end
endlocal
exit /b 0
