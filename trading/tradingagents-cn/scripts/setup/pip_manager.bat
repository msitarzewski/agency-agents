@echo off
REM pip管理脚本 - 使用国内镜像

echo 🔧 pip管理工具
echo ================

echo.
echo 1. 升级pip
python -m pip install --upgrade pip

echo.
echo 2. 安装常用包
python -m pip install pymongo redis pandas requests

echo.
echo 3. 显示已安装包
python -m pip list

echo.
echo 4. 检查pip配置
python -m pip config list

echo.
echo ✅ 完成!
pause
