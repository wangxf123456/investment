@echo off
echo ========================================
echo 期权链数据Dashboard启动器
echo ========================================
echo.

echo 正在启动Dashboard服务器...
echo 请稍候...
echo.

start http://localhost:5000

python dashboard.py

pause
