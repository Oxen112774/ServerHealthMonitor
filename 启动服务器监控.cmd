@echo off
setlocal
cd /d "%~dp0"

if not exist "build\server-health-monitor-console.exe" (
	echo 未找到管理控制台程序，正在先构建...
	powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build-desktop.ps1"
	if errorlevel 1 (
		echo 构建失败，请确认已安装 Go、Python 和 PyInstaller。
		pause
		exit /b 1
	)
)

if exist "dist\ServerHealthMonitor.exe" (
	start "Server Health Monitor" "dist\ServerHealthMonitor.exe"
	exit /b 0
)

where py >nul 2>nul
if errorlevel 1 (
	echo 未找到 Python。请先安装 Python 3.11 或更高版本。
	pause
	exit /b 1
)

py -3 desktop\app.py
if errorlevel 1 pause
