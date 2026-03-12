@echo off
echo ============================================
echo   B站视频转文本 - 安装依赖
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python 3.8+ : https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 正在安装 Whisper 和依赖...
pip install openai-whisper

echo.
echo [2/3] 检查 ffmpeg...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未检测到 ffmpeg！
    echo Whisper 需要 ffmpeg 来处理音频。
    echo 请安装 ffmpeg: https://www.gyan.dev/ffmpeg/builds/
    echo 或使用: scoop install ffmpeg
    echo.
)

echo [3/3] 检查 GPU 支持...
python -c "import torch; print('CUDA可用:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else '无')" 2>nul
if errorlevel 1 (
    echo [信息] PyTorch 未安装或无法检测 GPU
)

echo.
echo ============================================
echo   安装完成！运行方式:
echo   python main.py
echo ============================================
pause
