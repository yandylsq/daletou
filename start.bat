@echo off
echo ====================================
echo 大乐透智能预测系统启动脚本
echo ====================================
echo.

echo [1/3] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误：未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo.
echo [2/3] 激活虚拟环境...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo 警告：未找到虚拟环境，使用系统Python
)

echo.
echo [3/3] 启动Flask服务器...
echo.
echo ====================================
echo 服务器启动成功！
echo 请在浏览器中访问：http://localhost:5000
echo 按 Ctrl+C 停止服务器
echo ====================================
echo.

python app.py

pause
