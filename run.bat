@echo off
echo ========================================
echo 甘特图生成工具 - 启动脚本
echo ========================================
echo.

echo [1/3] 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b
)

echo.
echo [2/3] 升级pip...
python -m pip install --upgrade pip

echo.
echo [3/3] 安装依赖包...
python -m pip install -r requirements.txt

echo.
echo ========================================
echo 启动Streamlit应用...
echo ========================================
echo.
python -m streamlit run app.py

pause