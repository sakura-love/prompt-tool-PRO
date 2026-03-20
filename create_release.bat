@echo off
chcp 65001 >nul
title 创建发布包

echo.
echo ========================================
echo    专业AI提示词生成器 - 创建发布包
echo ========================================
echo.

REM 检查是否已打包
if not exist "dist\专业AI提示词生成器.exe" (
    echo [错误] 未找到可执行文件，请先运行打包命令：
    echo pyinstaller build_exe.spec
    pause
    exit /b 1
)

echo [1/5] 创建发布目录...
if exist "release" rd /s /q "release"
mkdir "release"

echo [2/5] 复制可执行文件...
copy "dist\专业AI提示词生成器.exe" "release\" >nul

echo [3/5] 复制应用文件...
xcopy "app.py" "release\" /Y >nul
xcopy "templates" "release\templates\" /E /I /Y >nul
xcopy "static" "release\static\" /E /I /Y >nul

echo [4/5] 复制文档文件...
copy "使用说明.txt" "release\" >nul
copy "README.txt" "release\" 2>nul
copy "快速开始.md" "release\" 2>nul

echo [5/5] 创建示例配置文件...
echo { > "release\launcher_config.json"
echo     "api_key": "", >> "release\launcher_config.json"
echo     "volc_api_key": "", >> "release\launcher_config.json"
echo     "save_api": false, >> "release\launcher_config.json"
echo     "hide_api": false >> "release\launcher_config.json"
echo } >> "release\launcher_config.json"

echo.
echo ========================================
echo    发布包创建成功！
echo ========================================
echo.
echo 发布目录: %cd%\release
echo.
echo 发布包包含:
dir /b "release"
echo.
echo 您可以将release文件夹打包分发
echo.

pause
