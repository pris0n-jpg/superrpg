#!/bin/bash

# SuperRPG 前端项目自动安装脚本
# 用于快速设置开发环境

set -e

echo "🚀 开始设置 SuperRPG 前端开发环境..."

# 检查 Node.js 版本
echo "📋 检查 Node.js 版本..."
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js，请先安装 Node.js (版本 >= 16.0.0)"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ 错误: Node.js 版本过低，需要 >= 16.0.0，当前版本: $(node -v)"
    exit 1
fi

echo "✅ Node.js 版本检查通过: $(node -v)"

# 检查 npm 版本
echo "📋 检查 npm 版本..."
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到 npm"
    exit 1
fi

echo "✅ npm 版本检查通过: $(npm -v)"

# 清理旧的依赖（如果存在）
if [ -d "node_modules" ]; then
    echo "🧹 清理旧的依赖..."
    rm -rf node_modules
fi

if [ -f "package-lock.json" ]; then
    echo "🧹 清理旧的锁定文件..."
    rm -f package-lock.json
fi

# 安装依赖
echo "📦 安装项目依赖..."
npm install

# 运行类型检查
echo "🔍 运行 TypeScript 类型检查..."
npm run type-check

# 运行代码检查
echo "🔍 运行 ESLint 检查..."
npm run lint || echo "⚠️  ESLint 检查发现问题，但继续安装..."

# 运行代码格式化
echo "🎨 运行代码格式化..."
npm run format

echo ""
echo "🎉 SuperRPG 前端开发环境设置完成！"
echo ""
echo "📋 可用命令:"
echo "  npm run dev      - 启动开发服务器"
echo "  npm run build    - 构建生产版本"
echo "  npm run preview  - 预览生产版本"
echo "  npm run lint     - 运行代码检查"
echo "  npm run format   - 格式化代码"
echo "  npm run type-check - 运行类型检查"
echo ""
echo "🌐 开发服务器将在 http://localhost:3000 启动"
echo ""
echo "现在可以运行 'npm run dev' 启动开发服务器！"