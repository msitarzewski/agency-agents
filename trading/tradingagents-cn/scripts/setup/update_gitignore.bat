@echo off
REM 更新.gitignore并从Git中移除AI工具目录

echo 🔧 更新Git忽略规则
echo ========================

echo.
echo 📋 当前.gitignore状态:
echo 检查.trae和.augment目录是否已添加到.gitignore...

findstr /C:".trae/" .gitignore >nul
if %errorlevel%==0 (
    echo ✅ .trae/ 已在.gitignore中
) else (
    echo ❌ .trae/ 不在.gitignore中
)

findstr /C:".augment/" .gitignore >nul
if %errorlevel%==0 (
    echo ✅ .augment/ 已在.gitignore中
) else (
    echo ❌ .augment/ 不在.gitignore中
)

echo.
echo 🗂️ 检查目录是否被Git跟踪...

REM 检查.trae目录是否被Git跟踪
git ls-files .trae/ >nul 2>&1
if %errorlevel%==0 (
    echo ⚠️ .trae目录被Git跟踪，需要移除
    echo 📤 从Git中移除.trae目录...
    git rm -r --cached .trae/
    if %errorlevel%==0 (
        echo ✅ .trae目录已从Git中移除
    ) else (
        echo ❌ 移除.trae目录失败
    )
) else (
    echo ✅ .trae目录未被Git跟踪
)

REM 检查.augment目录是否被Git跟踪
git ls-files .augment/ >nul 2>&1
if %errorlevel%==0 (
    echo ⚠️ .augment目录被Git跟踪，需要移除
    echo 📤 从Git中移除.augment目录...
    git rm -r --cached .augment/
    if %errorlevel%==0 (
        echo ✅ .augment目录已从Git中移除
    ) else (
        echo ❌ 移除.augment目录失败
    )
) else (
    echo ✅ .augment目录未被Git跟踪
)

echo.
echo 📊 检查Git状态...
git status --porcelain | findstr -E "\.(trae|augment)" >nul
if %errorlevel%==0 (
    echo ⚠️ 仍有AI工具目录相关的变更
    echo 📋 相关变更:
    git status --porcelain | findstr -E "\.(trae|augment)"
) else (
    echo ✅ 没有AI工具目录相关的变更
)

echo.
echo 💡 说明:
echo 1. .trae/ 和 .augment/ 目录已添加到.gitignore
echo 2. 这些目录包含AI工具的配置和缓存文件
echo 3. 不应该提交到Git仓库中
echo 4. 每个开发者可以有自己的AI工具配置
echo.
echo 🎯 下次提交时，这些目录将被忽略
echo.

pause
