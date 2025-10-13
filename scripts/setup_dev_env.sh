#!/bin/bash

# SuperRPG 开发环境设置脚本
# 用于快速搭建本地开发环境

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# 检查命令是否存在
check_command() {
    if command -v "$1" > /dev/null 2>&1; then
        print_message "$1 已安装"
        return 0
    else
        print_warning "$1 未安装"
        return 1
    fi
}

# 检查Python版本
check_python() {
    print_header "检查Python环境"
    
    if check_command python3; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        REQUIRED_VERSION="3.8"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_message "Python版本 $PYTHON_VERSION 满足要求 (>= $REQUIRED_VERSION)"
        else
            print_error "Python版本 $PYTHON_VERSION 不满足要求 (>= $REQUIRED_VERSION)"
            exit 1
        fi
    else
        print_error "Python3 未安装"
        exit 1
    fi
}

# 检查并安装Node.js (可选)
check_nodejs() {
    print_header "检查Node.js环境 (可选)"
    
    if check_command node; then
        NODE_VERSION=$(node -v | sed 's/v//')
        print_message "Node.js版本 $NODE_VERSION"
    else
        print_warning "Node.js未安装，某些前端工具可能无法使用"
        read -p "是否安装Node.js? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_nodejs
        fi
    fi
}

# 安装Node.js
install_nodejs() {
    print_message "安装Node.js..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if check_command brew; then
            brew install node
        else
            print_error "请先安装Homebrew或手动安装Node.js"
            exit 1
        fi
    else
        print_error "不支持的操作系统"
        exit 1
    fi
}

# 检查并安装PostgreSQL
check_postgresql() {
    print_header "检查PostgreSQL环境"
    
    if check_command psql; then
        print_message "PostgreSQL已安装"
    else
        print_warning "PostgreSQL未安装"
        read -p "是否安装PostgreSQL? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_postgresql
        fi
    fi
}

# 安装PostgreSQL
install_postgresql() {
    print_message "安装PostgreSQL..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
        sudo systemctl enable postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if check_command brew; then
            brew install postgresql
            brew services start postgresql
        else
            print_error "请先安装Homebrew或手动安装PostgreSQL"
            exit 1
        fi
    else
        print_error "不支持的操作系统"
        exit 1
    fi
}

# 创建Python虚拟环境
create_venv() {
    print_header "创建Python虚拟环境"
    
    VENV_DIR="venv"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虚拟环境 $VENV_DIR 已存在"
        read -p "是否重新创建? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_message "使用现有虚拟环境"
            return 0
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    print_message "虚拟环境创建完成: $VENV_DIR"
}

# 激活虚拟环境并安装依赖
install_dependencies() {
    print_header "安装项目依赖"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    print_message "升级pip..."
    pip install --upgrade pip
    
    # 安装项目依赖
    print_message "安装项目依赖..."
    pip install -e .
    
    # 安装开发依赖
    print_message "安装开发依赖..."
    pip install pytest pytest-cov pytest-asyncio pytest-mock \
                   black isort flake8 mypy \
                   pre-commit \
                   sphinx sphinx-rtd-theme \
                   mkdocs \
                   requests \
                   matplotlib pandas psutil \
                   locust
}

# 设置数据库
setup_database() {
    print_header "设置数据库"
    
    # 检查PostgreSQL是否运行
    if ! pgrep -x postgres > /dev/null; then
        print_warning "PostgreSQL未运行，尝试启动..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start postgresql
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start postgresql
        fi
    fi
    
    # 创建数据库用户和数据库
    print_message "创建数据库用户和数据库..."
    
    # 设置环境变量
    export PGPASSWORD="postgres"
    
    # 创建用户（如果不存在）
    sudo -u postgres psql -c "SELECT 1 FROM pg_roles WHERE rolname='superrpg';" | grep -q 1 || \
        sudo -u postgres createuser -s superrpg
    
    # 创建数据库
    sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname='superrpg_dev';" | grep -q 1 || \
        sudo -u postgres createdb superrpg_dev
    
    # 设置密码
    sudo -u postgres psql -c "ALTER USER superrpg PASSWORD 'superrpg123';"
    
    # 授权
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE superrpg_dev TO superrpg;"
    
    print_message "数据库设置完成"
    print_message "数据库连接信息:"
    print_message "  主机: localhost"
    print_message "  端口: 5432"
    print_message "  数据库: superrpg_dev"
    print_message "  用户: superrpg"
    print_message "  密码: superrpg123"
}

# 创建环境配置文件
create_env_file() {
    print_header "创建环境配置文件"
    
    ENV_FILE=".env"
    
    if [ -f "$ENV_FILE" ]; then
        print_warning "环境配置文件 $ENV_FILE 已存在"
        read -p "是否覆盖? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    cat > "$ENV_FILE" << EOF
# SuperRPG 开发环境配置
# 数据库配置
DATABASE_URL=postgresql://superrpg:superrpg123@localhost:5432/superrpg_dev

# API配置
API_HOST=0.0.0.0
API_PORT=3010
API_DEBUG=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 缓存配置
REDIS_URL=redis://localhost:6379/0

# 测试配置
TEST_DATABASE_URL=postgresql://superrpg:superrpg123@localhost:5432/superrpg_test
EOF
    
    print_message "环境配置文件创建完成: $ENV_FILE"
}

# 设置pre-commit钩子
setup_precommit() {
    print_header "设置pre-commit钩子"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装pre-commit
    pip install pre-commit
    
    # 创建pre-commit配置
    cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
EOF
    
    # 安装pre-commit钩子
    pre-commit install
    
    print_message "pre-commit钩子设置完成"
}

# 创建日志目录
create_log_dir() {
    print_header "创建日志目录"
    
    mkdir -p logs
    print_message "日志目录创建完成: logs/"
}

# 运行测试
run_tests() {
    print_header "运行测试"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 运行测试
    pytest tests/ -v --cov=src --cov-report=html --cov-report=term
    
    print_message "测试完成，覆盖率报告已生成在 htmlcov/index.html"
}

# 显示后续步骤
show_next_steps() {
    print_header "开发环境设置完成！"
    
    echo -e "${GREEN}后续步骤:${NC}"
    echo "1. 激活虚拟环境:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 启动开发服务器:"
    echo "   python src/main.py"
    echo ""
    echo "3. 运行测试:"
    echo "   pytest tests/"
    echo ""
    echo "4. 查看API文档:"
    echo "   访问 http://localhost:3010/docs"
    echo ""
    echo "5. 查看项目文档:"
    echo "   mkdocs serve"
    echo ""
    echo -e "${YELLOW}环境变量:${NC}"
    echo "已创建 .env 文件，包含数据库连接信息"
    echo ""
    echo -e "${YELLOW}数据库:${NC}"
    echo "PostgreSQL服务应该已启动"
    echo "数据库: superrpg_dev"
    echo "用户: superrpg"
    echo "密码: superrpg123"
}

# 主函数
main() {
    print_header "SuperRPG 开发环境设置"
    
    # 检查基本工具
    check_command curl || (print_error "curl未安装" && exit 1)
    check_command git || (print_error "git未安装" && exit 1)
    
    # 检查Python环境
    check_python
    
    # 检查可选工具
    check_nodejs
    check_postgresql
    
    # 创建虚拟环境
    create_venv
    
    # 安装依赖
    install_dependencies
    
    # 设置数据库
    setup_database
    
    # 创建环境配置文件
    create_env_file
    
    # 设置pre-commit钩子
    setup_precommit
    
    # 创建日志目录
    create_log_dir
    
    # 运行测试（可选）
    read -p "是否运行测试? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    fi
    
    # 显示后续步骤
    show_next_steps
    
    print_message "开发环境设置完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi