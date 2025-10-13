@echo off
setlocal enabledelayedexpansion

REM SuperRPG 前端项目自动安装脚本 (Windows)
REM 用于快速设置开发环境

echo 🚀 开始设置 SuperRPG 前端开发环境...

REM 检查 Node.js 版本
echo 📋 检查 Node.js 版本...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Node.js，请先安装 Node.js (版本 ^>= 16.0.0)
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js 版本检查通过: %NODE_VERSION%

REM 检查 npm 版本
echo 📋 检查 npm 版本...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 npm
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✅ npm 版本检查通过: %NPM_VERSION%

REM 清理旧的依赖（如果存在）
if exist node_modules (
    echo 🧹 清理旧的依赖...
    rmdir /s /q node_modules
)

if exist package-lock.json (
    echo 🧹 清理旧的锁定文件...
    del /f package-lock.json
)

REM 安装依赖
echo 📦 安装项目依赖...
npm install
if errorlevel 1 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

REM 运行类型检查
echo 🔍 运行 TypeScript 类型检查...
npm run type-check
if errorlevel 1 (
    echo ⚠️  TypeScript 类型检查发现问题，但继续安装...
)

REM 运行代码检查
echo 🔍 运行 ESLint 检查...
npm run lint
if errorlevel 1 (
    echo ⚠️  ESLint 检查发现问题，但继续安装...
)

REM 运行代码格式化
echo 🎨 运行代码格式化...
npm run format

echo.
echo 🎉 SuperRPG 前端开发环境设置完成！
echo.
echo 📋 可用命令:
echo   npm run dev      - 启动开发服务器
echo   npm run build    - 构建生产版本
echo   npm run preview  - 预览生产版本
echo   npm run lint     - 运行代码检查
echo   npm run format   - 格式化代码
echo   npm run type-check - 运行类型检查
echo.
echo 🌐 开发服务器将在 http://localhost:3000 启动
echo.
echo 现在可以运行 'npm run dev' 启动开发服务器！
pause