@echo off
echo ============================================
echo   B站视频转文本 - 打包脚本
echo ============================================
echo.

REM 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller
)

echo [信息] 开始打包...
echo.

pyinstaller ^
    --name "B站视频转文本" ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --add-data "BBDown.exe;." ^
    --hidden-import "whisper" ^
    --hidden-import "torch" ^
    --hidden-import "tqdm" ^
    --hidden-import "tiktoken" ^
    --hidden-import "tiktoken_ext" ^
    --hidden-import "tiktoken_ext.openai_public" ^
    --collect-data "whisper" ^
    --icon NONE ^
    main.py

echo.
if errorlevel 1 (
    echo [错误] 打包失败！
    pause
    exit /b 1
)

echo ============================================
echo [成功] 打包完成！
echo 输出目录: dist\B站视频转文本\
echo ============================================
echo.
echo 请将 dist\B站视频转文本\ 文件夹整体发给别人即可使用。
pause
