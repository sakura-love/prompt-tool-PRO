@echo off
chcp 65001 >nul
echo ========================================
echo   专业AI提示词生成器 v1.7.0 打包脚本
echo ========================================
echo.

echo [1/5] 检查环境...
python --version
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo.

echo [2/5] 安装打包工具...
echo 正在安装 PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo 错误：PyInstaller 安装失败！
    echo 请检查网络连接或手动运行: pip install pyinstaller
    pause
    exit /b 1
)
echo PyInstaller 安装成功！
echo.

echo [2.5/5] 验证 PyInstaller 安装...
python -m PyInstaller --version
if errorlevel 1 (
    echo 错误：PyInstaller 验证失败！
    echo 请尝试手动安装: pip install --upgrade pyinstaller
    pause
    exit /b 1
)
echo.

echo [3/5] 清理旧的构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if not exist "release" mkdir "release"
if exist "release\*.exe" del /q "release\*.exe"
echo.

echo [4/5] 开始打包（单文件模式）...
echo 这可能需要几分钟时间，请耐心等待...
echo.

python -m PyInstaller "专业AI提示词生成器_v1.7.0.spec"

if errorlevel 1 (
    echo.
    echo 错误：打包失败！
    pause
    exit /b 1
)
echo.

echo [5/5] 复制文件到 release 目录...
copy /Y "dist\专业AI提示词生成器_v1.7.0.exe" "release\" >nul
copy /Y "使用说明.txt" "release\" >nul
copy /Y "README.md" "release\" >nul
copy /Y "LICENSE" "release\" >nul
if exist "launcher_config.json" copy /Y "launcher_config.json" "release\" >nul
echo.

echo ========================================
echo   打包完成！
echo ========================================
echo.
echo 可执行文件位置: release\专业AI提示词生成器_v1.7.0.exe
echo.
echo 按任意键退出...
pause >nul
