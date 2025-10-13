#!/bin/bash

# SuperRPG 测试环境部署脚本
# 用于在测试服务器上部署和配置测试环境

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="superrpg"
DEPLOY_USER="deploy"
DEPLOY_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
SERVICE_NAME="$PROJECT_NAME"
DOCKER_REGISTRY="registry.example.com/$PROJECT_NAME"
VERSION="latest"

# 环境变量
ENVIRONMENT="test"
DATABASE_HOST="localhost"
DATABASE_PORT="5432"
DATABASE_NAME="superrpg_test"
API_PORT="3010"

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

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "请不要以root用户运行此脚本"
        echo "请创建deploy用户并使用该用户运行"
        exit 1
    fi
}

# 检查用户权限
check_permissions() {
    print_header "检查用户权限"
    
    if [[ "$USER" != "$DEPLOY_USER" ]]; then
        print_error "请使用 $DEPLOY_USER 用户运行此脚本"
        exit 1
    fi
    
    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        print_error "$DEPLOY_USER 用户没有sudo权限"
        exit 1
    fi
    
    print_message "用户权限检查通过"
}

# 创建必要的目录
create_directories() {
    print_header "创建部署目录"
    
    # 创建部署目录
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown "$DEPLOY_USER:$DEPLOY_USER" "$DEPLOY_DIR"
    
    # 创建备份目录
    sudo mkdir -p "$BACKUP_DIR"
    sudo chown "$DEPLOY_USER:$DEPLOY_USER" "$BACKUP_DIR"
    
    # 创建日志目录
    sudo mkdir -p "/var/log/$PROJECT_NAME"
    sudo chown "$DEPLOY_USER:$DEPLOY_USER" "/var/log/$PROJECT_NAME"
    
    # 创建配置目录
    sudo mkdir -p "/etc/$PROJECT_NAME"
    sudo chown "$DEPLOY_USER:$DEPLOY_USER" "/etc/$PROJECT_NAME"
    
    print_message "目录创建完成"
}

# 安装Docker
install_docker() {
    print_header "安装Docker"
    
    if command -v docker > /dev/null 2>&1; then
        print_message "Docker已安装"
        docker --version
        return 0
    fi
    
    print_message "安装Docker..."
    
    # 更新包索引
    sudo apt-get update
    
    # 安装依赖
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 设置Docker稳定版仓库
    echo \
        "deb [arch=$(dpkg --print-architecture)] signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker "$DEPLOY_USER"
    
    print_message "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    print_header "安装Docker Compose"
    
    if command -v docker-compose > /dev/null 2>&1; then
        print_message "Docker Compose已安装"
        docker-compose --version
        return 0
    fi
    
    print_message "安装Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 设置可执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_message "Docker Compose安装完成"
}

# 创建Docker网络
create_docker_network() {
    print_header "创建Docker网络"
    
    # 创建应用网络
    docker network create "$PROJECT_NAME-network" 2>/dev/null || \
        print_message "Docker网络已存在"
    
    print_message "Docker网络创建完成"
}

# 部署数据库
deploy_database() {
    print_header "部署数据库"
    
    # 创建数据库数据目录
    mkdir -p "$DEPLOY_DIR/data/postgres"
    
    # 创建数据库环境文件
    cat > "$DEPLOY_DIR/.env.db" << EOF
# 数据库配置
POSTGRES_DB=$DATABASE_NAME
POSTGRES_USER=superrpg
POSTGRES_PASSWORD=test_db_password_123
PGDATA=/var/lib/postgresql/data
EOF
    
    # 创建Docker Compose文件
    cat > "$DEPLOY_DIR/docker-compose.db.yml" << EOF
version: '3.8'

services:
  postgres:
    image: postgres:13
    container_name: $PROJECT_NAME-postgres
    restart: unless-stopped
    env_file:
      - .env.db
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - $DEPLOY_DIR/data/postgres:/var/lib/postgresql/data
      - /var/log/$PROJECT_NAME:/var/log/postgresql
    ports:
      - "$DATABASE_PORT:5432"
    networks:
      - $PROJECT_NAME-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U superrpg -d $DATABASE_NAME"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  postgres_data:
    driver: local

networks:
  $PROJECT_NAME-network:
    driver: bridge
EOF
    
    # 启动数据库
    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.db.yml up -d
    
    # 等待数据库启动
    print_message "等待数据库启动..."
    sleep 30
    
    # 检查数据库状态
    if docker-compose -f docker-compose.db.yml exec -T postgres pg_isready -U superrpg -d "$DATABASE_NAME" > /dev/null; then
        print_message "数据库启动成功"
    else
        print_error "数据库启动失败"
        exit 1
    fi
    
    print_message "数据库部署完成"
}

# 部置应用
deploy_application() {
    print_header "部署应用"
    
    # 创建应用环境文件
    cat > "$DEPLOY_DIR/.env.app" << EOF
# 应用配置
ENVIRONMENT=$ENVIRONMENT
API_HOST=0.0.0.0
API_PORT=$API_PORT
API_DEBUG=false

# 数据库配置
DATABASE_URL=postgresql://superrpg:test_db_password_123@postgres:5432/$DATABASE_NAME

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/$PROJECT_NAME/app.log

# 缓存配置
REDIS_URL=redis://redis:6379/0

# 安全配置
SECRET_KEY=test_secret_key_change_in_production
JWT_SECRET_KEY=test_jwt_secret_key_change_in_production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 性能配置
MAX_WORKERS=4
WORKER_TIMEOUT=30
KEEPALIVE=2
EOF
    
    # 创建Docker Compose文件
    cat > "$DEPLOY_DIR/docker-compose.app.yml" << EOF
version: '3.8'

services:
  app:
    image: $DOCKER_REGISTRY/$PROJECT_NAME:$VERSION
    container_name: $PROJECT_NAME-app
    restart: unless-stopped
    env_file:
      - .env.app
    environment:
      - TZ=Asia/Shanghai
    volumes:
      - /var/log/$PROJECT_NAME:/var/log/$PROJECT_NAME
      - $DEPLOY_DIR/uploads:/app/uploads
    ports:
      - "$API_PORT:3010"
    networks:
      - $PROJECT_NAME-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3010/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  redis:
    image: redis:6-alpine
    container_name: $PROJECT_NAME-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - $DEPLOY_DIR/data/redis:/data
    ports:
      - "6379:6379"
    networks:
      - $PROJECT_NAME-network

  nginx:
    image: nginx:alpine
    container_name: $PROJECT_NAME-nginx
    restart: unless-stopped
    volumes:
      - /etc/$PROJECT_NAME/nginx.conf:/etc/nginx/nginx.conf
      - /var/log/$PROJECT_NAME:/var/log/nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - $PROJECT_NAME-network
    depends_on:
      - app

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  $PROJECT_NAME-network:
    driver: bridge
EOF
    
    # 创建Redis数据目录
    mkdir -p "$DEPLOY_DIR/data/redis"
    
    # 创建上传目录
    mkdir -p "$DEPLOY_DIR/uploads"
    
    # 启动应用
    cd "$DEPLOY_DIR"
    docker-compose -f docker-compose.app.yml up -d
    
    # 等待应用启动
    print_message "等待应用启动..."
    sleep 60
    
    # 检查应用状态
    if curl -f "http://localhost:$API_PORT/health" > /dev/null; then
        print_message "应用启动成功"
    else
        print_error "应用启动失败"
        docker-compose -f docker-compose.app.yml logs app
        exit 1
    fi
    
    print_message "应用部署完成"
}

# 配置Nginx
configure_nginx() {
    print_header "配置Nginx"
    
    # 创建Nginx配置文件
    sudo tee /etc/$PROJECT_NAME/nginx.conf > /dev/null << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                    '\$status \$body_bytes_sent "\$http_referer" '
                    '"\$http_user_agent" "\$http_x_forwarded_for"';

    access_log /var/log/$PROJECT_NAME/nginx/access.log main;
    error_log /var/log/$PROJECT_NAME/nginx/error.log;

    # 基本设置
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # 上游服务器
    upstream app {
        server app:3010;
    }

    # HTTP服务器配置
    server {
        listen 80;
        server_name test.superrpg.com;

        # 重定向到HTTPS
        return 301 https://\$server_name\$request_uri;
    }

    # HTTPS服务器配置
    server {
        listen 443 ssl http2;
        server_name test.superrpg.com;

        # SSL证书（测试环境使用自签名证书）
        ssl_certificate /etc/ssl/certs/test.superrpg.com.crt;
        ssl_certificate_key /etc/ssl/private/test.superrpg.com.key;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # 安全头
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # 代理到应用
        location / {
            proxy_pass http://app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 静态文件
        location /static/ {
            alias $DEPLOY_DIR/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # API请求
        location /api/ {
            proxy_pass http://app;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            
            # 超时设置
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
EOF
    
    # 创建SSL证书目录（测试环境使用自签名证书）
    sudo mkdir -p /etc/ssl/certs /etc/ssl/private
    
    # 生成自签名证书（如果不存在）
    if [ ! -f "/etc/ssl/certs/test.superrpg.com.crt" ]; then
        print_message "生成自签名SSL证书..."
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/ssl/private/test.superrpg.com.key \
            -out /etc/ssl/certs/test.superrpg.com.crt \
            -subj "/C=CN/ST=State/L=City/O=Organization/CN=test.superrpg.com"
    fi
    
    # 重新加载Nginx配置
    sudo nginx -t && sudo systemctl reload nginx
    
    print_message "Nginx配置完成"
}

# 创建系统服务
create_systemd_service() {
    print_header "创建系统服务"
    
    # 创建应用服务文件
    sudo tee /etc/systemd/system/$PROJECT_NAME-app.service > /dev/null << EOF
[Unit]
Description=SuperRPG Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.app.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.app.yml down
ExecReload=/usr/bin/docker-compose -f docker-compose.app.yml up -d
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF
    
    # 创建数据库服务文件
    sudo tee /etc/systemd/system/$PROJECT_NAME-db.service > /dev/null << EOF
[Unit]
Description=SuperRPG Database
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.db.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.db.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    # 启用服务
    sudo systemctl enable $PROJECT_NAME-app.service
    sudo systemctl enable $PROJECT_NAME-db.service
    
    print_message "系统服务创建完成"
}

# 设置日志轮转
setup_log_rotation() {
    print_header "设置日志轮转"
    
    # 创建日志轮转配置
    sudo tee /etc/logrotate.d/$PROJECT_NAME > /dev/null << EOF
/var/log/$PROJECT_NAME/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $DEPLOY_USER $DEPLOY_USER
    postrotate
        docker-compose -f $DEPLOY_DIR/docker-compose.app.yml exec -T app kill -USR1
    endscript
}

/var/log/$PROJECT_NAME/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $DEPLOY_USER $DEPLOY_USER
    postrotate
        docker kill -s USR1 $PROJECT_NAME-nginx
    endscript
}
EOF
    
    print_message "日志轮转设置完成"
}

# 创建备份脚本
create_backup_script() {
    print_header "创建备份脚本"
    
    # 创建备份脚本
    cat > "$DEPLOY_DIR/backup.sh" << 'EOF'
#!/bin/bash

# SuperRPG 备份脚本

set -e

# 配置
PROJECT_NAME="superrpg"
DEPLOY_DIR="/opt/superrpg"
BACKUP_DIR="/opt/backups/superrpg"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "$BACKUP_DIR/$DATE"

# 备份数据库
echo "备份数据库..."
docker-compose -f "$DEPLOY_DIR/docker-compose.db.yml" exec -T postgres pg_dump -U superrpg superrpg_test > "$BACKUP_DIR/$DATE/database.sql"

# 备份应用数据
echo "备份应用数据..."
cp -r "$DEPLOY_DIR/uploads" "$BACKUP_DIR/$DATE/"
cp -r "$DEPLOY_DIR/.env.*" "$BACKUP_DIR/$DATE/"

# 备份配置文件
echo "备份配置文件..."
cp -r "/etc/$PROJECT_NAME" "$BACKUP_DIR/$DATE/"

# 创建备份信息文件
cat > "$BACKUP_DIR/$DATE/backup_info.txt" << EOL
备份时间: $(date)
备份类型: 完整备份
项目名称: $PROJECT_NAME
环境: test
EOL

# 压缩备份
echo "压缩备份..."
cd "$BACKUP_DIR"
tar -czf "$DATE.tar.gz" "$DATE"
rm -rf "$DATE"

# 清理旧备份（保留30天）
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $BACKUP_DIR/$DATE.tar.gz"
EOF
    
    chmod +x "$DEPLOY_DIR/backup.sh"
    
    # 创建定时备份任务
    (crontab -l 2>/dev/null; echo "0 2 * * * $DEPLOY_DIR/backup.sh") | crontab -
    
    print_message "备份脚本创建完成"
}

# 创建监控脚本
create_monitoring_script() {
    print_header "创建监控脚本"
    
    # 创建监控脚本
    cat > "$DEPLOY_DIR/monitor.sh" << 'EOF'
#!/bin/bash

# SuperRPG 监控脚本

set -e

# 配置
PROJECT_NAME="superrpg"
DEPLOY_DIR="/opt/superrpg"
API_URL="http://localhost:3010"
LOG_FILE="/var/log/superrpg/monitor.log"

# 检查服务状态
check_services() {
    echo "$(date): 检查服务状态" >> "$LOG_FILE"
    
    # 检查应用状态
    if curl -f "$API_URL/health" > /dev/null; then
        echo "$(date): 应用运行正常" >> "$LOG_FILE"
    else
        echo "$(date): 应用异常，尝试重启" >> "$LOG_FILE"
        systemctl restart "$PROJECT_NAME-app.service"
    fi
    
    # 检查数据库状态
    if docker-compose -f "$DEPLOY_DIR/docker-compose.db.yml" exec -T postgres pg_isready -U superrpg -d superrpg_test > /dev/null; then
        echo "$(date): 数据库运行正常" >> "$LOG_FILE"
    else
        echo "$(date): 数据库异常，尝试重启" >> "$LOG_FILE"
        systemctl restart "$PROJECT_NAME-db.service"
    fi
}

# 检查磁盘空间
check_disk_space() {
    echo "$(date): 检查磁盘空间" >> "$LOG_FILE"
    
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo "$(date): 磁盘空间不足 (使用率: $DISK_USAGE%)" >> "$LOG_FILE"
        # 发送警报
    fi
}

# 检查内存使用
check_memory_usage() {
    echo "$(date): 检查内存使用" >> "$LOG_FILE"
    
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$MEMORY_USAGE" -gt 80 ]; then
        echo "$(date): 内存使用过高 (使用率: $MEMORY_USAGE%)" >> "$LOG_FILE"
        # 发送警报
    fi
}

# 执行检查
check_services
check_disk_space
check_memory_usage

echo "$(date): 监控检查完成" >> "$LOG_FILE"
EOF
    
    chmod +x "$DEPLOY_DIR/monitor.sh"
    
    # 创建定时监控任务
    (crontab -l 2>/dev/null; echo "*/5 * * * * $DEPLOY_DIR/monitor.sh") | crontab -
    
    print_message "监控脚本创建完成"
}

# 运行部署后测试
run_post_deployment_tests() {
    print_header "运行部署后测试"
    
    # 测试API健康检查
    echo "测试API健康检查..."
    if curl -f "http://localhost:$API_PORT/health" > /dev/null; then
        print_message "API健康检查通过"
    else
        print_error "API健康检查失败"
        return 1
    fi
    
    # 测试数据库连接
    echo "测试数据库连接..."
    if docker-compose -f "$DEPLOY_DIR/docker-compose.db.yml" exec -T postgres psql -U superrpg -d "$DATABASE_NAME" -c "SELECT 1;" > /dev/null; then
        print_message "数据库连接测试通过"
    else
        print_error "数据库连接测试失败"
        return 1
    fi
    
    # 测试基本API功能
    echo "测试基本API功能..."
    
    # 测试角色卡创建
    CHARACTER_DATA='{"name": "测试角色", "race": "人类", "class": "战士", "level": 1}'
    if curl -X POST "http://localhost:$API_PORT/api/v1/characters" \
         -H "Content-Type: application/json" \
         -d "$CHARACTER_DATA" > /dev/null; then
        print_message "API功能测试通过"
    else
        print_error "API功能测试失败"
        return 1
    fi
    
    print_message "部署后测试通过"
}

# 显示部署信息
show_deployment_info() {
    print_header "部署信息"
    
    echo -e "${GREEN}项目名称:${NC} $PROJECT_NAME"
    echo -e "${GREEN}环境:${NC} $ENVIRONMENT"
    echo -e "${GREEN}部署目录:${NC} $DEPLOY_DIR"
    echo -e "${GREEN}API地址:${NC} http://localhost:$API_PORT"
    echo -e "${GREEN}数据库:${NC} postgresql://superrpg:***@localhost:$DATABASE_PORT/$DATABASE_NAME"
    
    echo ""
    echo -e "${GREEN}服务命令:${NC}"
    echo "启动服务: sudo systemctl start $PROJECT_NAME-app.service"
    echo "停止服务: sudo systemctl stop $PROJECT_NAME-app.service"
    echo "重启服务: sudo systemctl restart $PROJECT_NAME-app.service"
    echo "查看日志: sudo journalctl -u $PROJECT_NAME-app.service -f"
    
    echo ""
    echo -e "${GREEN}Docker命令:${NC}"
    echo "查看容器: docker-compose ps"
    echo "查看日志: docker-compose logs"
    echo "重启服务: docker-compose restart"
    
    echo ""
    echo -e "${GREEN}备份命令:${NC}"
    echo "手动备份: $DEPLOY_DIR/backup.sh"
    echo "监控检查: $DEPLOY_DIR/monitor.sh"
}

# 主函数
main() {
    print_header "SuperRPG 测试环境部署"
    
    # 检查权限
    check_root
    check_permissions
    
    # 创建目录
    create_directories
    
    # 安装Docker
    install_docker
    install_docker_compose
    
    # 创建Docker网络
    create_docker_network
    
    # 部署服务
    deploy_database
    deploy_application
    configure_nginx
    
    # 创建系统服务
    create_systemd_service
    
    # 设置日志轮转
    setup_log_rotation
    
    # 创建脚本
    create_backup_script
    create_monitoring_script
    
    # 运行测试
    run_post_deployment_tests
    
    # 显示部署信息
    show_deployment_info
    
    print_message "测试环境部署完成！"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi