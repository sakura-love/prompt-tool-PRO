@echo off
chcp 65001 >nul
title 专业AI提示词生成器 v1.5.1 - onefile打包脚本

echo.
echo ========================================
echo    专业AI提示词生成器 v1.5.1
echo    onefile打包脚本
echo ========================================
echo.

REM 检查Python环境
echo [检查] 检测Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)
echo [完成] Python环境正常
echo.

REM 检查PyInstaller
echo [检查] 检测PyInstaller...
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [安装] 正在安装PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] PyInstaller安装失败
        pause
        exit /b 1
    )
)
echo [完成] PyInstaller已就绪
echo.

REM 清理旧的打包文件
echo [清理] 清理旧的打包文件...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "release" rd /s /q "release"
if exist "*.spec" del /q "*.spec"
echo [完成] 清理完成
echo.

REM 创建spec文件
echo [准备] 创建spec文件...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['launcher.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('app.py', '.'^),
echo         ^('templates', 'templates'^),
echo         ^('static', 'static'^),
echo     ],
echo     hiddenimports=['app', 'flask', 'werkzeug', 'jinja2'],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='专业AI提示词生成器',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     onefile=True,
echo ^)
) > build.spec
echo [完成] spec文件已创建
echo.

REM 开始打包
echo [1/6] 开始打包应用...
echo 这可能需要几分钟时间，请耐心等待...
echo.

python -m PyInstaller build.spec

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo [完成] 打包成功
echo.

REM 创建发布目录
echo [2/6] 创建发布目录...
mkdir "release"
echo [完成] 发布目录已创建
echo.

REM 复制可执行文件
echo [3/6] 复制可执行文件...
copy "dist\专业AI提示词生成器.exe" "release\" >nul
echo [完成] 可执行文件已复制
echo.

REM 复制文档文件
echo [4/6] 复制文档文件...
copy "使用说明.txt" "release\" >nul
copy "README.md" "release\" >nul
copy "LICENSE" "release\" >nul
echo [完成] 文档文件已复制
echo.

REM 创建示例配置文件
echo [5/6] 创建示例配置文件...
echo { > "release\launcher_config.json"
echo     "api_key": "", >> "release\launcher_config.json"
echo     "volc_api_key": "", >> "release\launcher_config.json"
echo     "save_api": false, >> "release\launcher_config.json"
echo     "hide_api": false >> "release\launcher_config.json"
echo } >> "release\launcher_config.json"
echo [完成] 配置文件已创建
echo.

REM 清理临时文件
echo [6/6] 清理临时文件...
rd /s /q "build"
rd /s /q "dist"
del /q "build.spec"
echo [完成] 临时文件已清理
echo.

REM 显示打包结果
echo.
echo ========================================
echo    打包完成！
echo ========================================
echo.
echo 发布目录: %cd%\release
echo.
echo 发布包包含:
dir /b "release"
echo.
echo 版本信息:
echo   版本号: v1.5.1
echo   发布日期: %date% %time%
echo.
echo 下一步:
echo   1. 测试release目录中的应用程序
echo   2. 确认功能正常后，将release文件夹打包分发
echo.
echo 注意事项:
echo   - 首次运行需要输入API Key
echo   - 确保网络连接正常
echo   - 建议在Windows 10/11系统上运行
echo.

pause
