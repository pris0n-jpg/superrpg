#!/bin/bash

# SuperRPG Docker镜像构建脚本
# 用于构建和推送Docker镜像到容器仓库

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

# 默认配置
PROJECT_NAME="superrpg"
DOCKER_REGISTRY="registry.example.com/$PROJECT_NAME"
VERSION="latest"
BUILD_CONTEXT="."
DOCKERFILE="Dockerfile"
PUSH_IMAGE=false
NO_CACHE=false

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            --dockerfile)
                DOCKERFILE="$2"
                shift 2
                ;;
            --context)
                BUILD_CONTEXT="$2"
                shift 2
                ;;
            --push)
                PUSH_IMAGE=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 显示帮助信息
show_help() {
    echo "SuperRPG Docker镜像构建脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --registry REGISTRY    设置Docker仓库地址 (默认: $DOCKER_REGISTRY)"
    echo "  --version VERSION      设置镜像版本 (默认: $VERSION)"
    echo "  --dockerfile FILE      设置Dockerfile路径 (默认: $DOCKERFILE)"
    echo "  --context PATH         设置构建上下文路径 (默认: $BUILD_CONTEXT)"
    echo "  --push                 构建后推送镜像到仓库"
    echo "  --no-cache             构建时不使用缓存"
    echo "  --help                 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                                    # 使用默认配置构建"
    echo "  $0 --version v1.0.0 --push          # 构建v1.0.0版本并推送"
    echo "  $0 --registry myregistry.com --version latest  # 使用自定义仓库和版本"
}

# 检查Docker环境
check_docker() {
    print_header "检查Docker环境"
    
    if ! command -v docker > /dev/null 2>&1; then
        print_error "Docker未安装"
        exit 1
    fi
    
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker守护进程未运行"
        exit 1
    fi
    
    # 检查Docker Buildx（用于多平台构建）
    if ! docker buildx version > /dev/null 2>&1; then
        print_warning "Docker Buildx未安装，无法进行多平台构建"
        MULTI_PLATFORM=false
    else
        MULTI_PLATFORM=true
    fi
    
    print_message "Docker环境检查通过"
}

# 验证构建上下文
validate_build_context() {
    print_header "验证构建上下文"
    
    # 检查Dockerfile是否存在
    if [ ! -f "$BUILD_CONTEXT/$DOCKERFILE" ]; then
        print_error "Dockerfile不存在: $BUILD_CONTEXT/$DOCKERFILE"
        exit 1
    fi
    
    # 检查requirements.txt是否存在
    if [ ! -f "$BUILD_CONTEXT/requirements.txt" ]; then
        print_warning "requirements.txt不存在，可能影响依赖安装"
    fi
    
    # 检查源代码目录
    if [ ! -d "$BUILD_CONTEXT/src" ]; then
        print_error "源代码目录不存在: $BUILD_CONTEXT/src"
        exit 1
    fi
    
    print_message "构建上下文验证通过"
}

# 创建Dockerfile
create_dockerfile() {
    print_header "创建Dockerfile"
    
    # 如果Dockerfile不存在，创建一个默认的
    if [ ! -f "$BUILD_CONTEXT/$DOCKERFILE" ]; then
        print_warning "Dockerfile不存在，创建默认Dockerfile"
        
        cat > "$BUILD_CONTEXT/$DOCKERFILE" << 'EOF'
# 多阶段构建Dockerfile for SuperRPG
FROM python:3.9-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 生产阶段
FROM python:3.9-slim as production

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/*

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# 复制应用代码
COPY src/ ./src/
COPY configs/ ./configs/
COPY scripts/ ./scripts/

# 创建必要的目录
RUN mkdir -p logs uploads static

# 设置权限
RUN chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "src/main.py"]
EOF
    fi
    
    print_message "Dockerfile准备完成"
}

# 构建Docker镜像
build_image() {
    print_header "构建Docker镜像"
    
    # 构建参数
    BUILD_ARGS=""
    
    if [ "$NO_CACHE" = true ]; then
        BUILD_ARGS="--no-cache"
    fi
    
    # 构建镜像
    print_message "开始构建镜像: $DOCKER_REGISTRY:$VERSION"
    
    if [ "$MULTI_PLATFORM" = true ] && [ "${MULTI_PLATFORM_BUILD:-false}" = true ]; then
        # 多平台构建
        print_message "使用多平台构建"
        docker buildx build \
            $BUILD_ARGS \
            --platform linux/amd64,linux/arm64 \
            -t "$DOCKER_REGISTRY:$VERSION" \
            -t "$DOCKER_REGISTRY:latest" \
            -f "$BUILD_CONTEXT/$DOCKERFILE" \
            "$BUILD_CONTEXT"
    else
        # 单平台构建
        docker build \
            $BUILD_ARGS \
            -t "$DOCKER_REGISTRY:$VERSION" \
            -t "$DOCKER_REGISTRY:latest" \
            -f "$BUILD_CONTEXT/$DOCKERFILE" \
            "$BUILD_CONTEXT"
    fi
    
    # 验证镜像
    if docker images "$DOCKER_REGISTRY:$VERSION" | grep -q "$DOCKER_REGISTRY"; then
        print_message "镜像构建成功: $DOCKER_REGISTRY:$VERSION"
        
        # 显示镜像信息
        IMAGE_SIZE=$(docker images "$DOCKER_REGISTRY:$VERSION" --format "{{.Size}}")
        CREATED_TIME=$(docker images "$DOCKER_REGISTRY:$VERSION" --format "{{.CreatedAt}}")
        
        echo "镜像大小: $IMAGE_SIZE"
        echo "创建时间: $CREATED_TIME"
    else
        print_error "镜像构建失败"
        exit 1
    fi
}

# 测试Docker镜像
test_image() {
    print_header "测试Docker镜像"
    
    # 运行容器并测试
    CONTAINER_NAME="$PROJECT_NAME-test-$$"
    
    print_message "启动测试容器: $CONTAINER_NAME"
    
    # 启动容器
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p 8001:8000 \
        -e API_PORT=8000 \
        -e API_DEBUG=false \
        "$DOCKER_REGISTRY:$VERSION"
    
    # 等待容器启动
    print_message "等待容器启动..."
    sleep 30
    
    # 健康检查
    print_message "执行健康检查..."
    if curl -f http://localhost:8001/health > /dev/null; then
        print_message "健康检查通过"
    else
        print_error "健康检查失败"
        docker logs "$CONTAINER_NAME"
        CLEANUP=false
    fi
    
    # API功能测试
    print_message "执行API功能测试..."
    
    # 测试角色卡创建
    CHARACTER_DATA='{"name": "测试角色", "race": "人类", "class": "战士", "level": 1}'
    if curl -X POST "http://localhost:8001/api/v1/characters" \
         -H "Content-Type: application/json" \
         -d "$CHARACTER_DATA" > /dev/null; then
        print_message "API功能测试通过"
    else
        print_error "API功能测试失败"
        docker logs "$CONTAINER_NAME"
        CLEANUP=false
    fi
    
    # 清理测试容器
    if [ "${CLEUPABLE:-true}" = true ]; then
        print_message "清理测试容器"
        docker stop "$CONTAINER_NAME" > /dev/null
        docker rm "$CONTAINER_NAME" > /dev/null
    fi
    
    print_message "Docker镜像测试完成"
}

# 推送Docker镜像
push_image() {
    print_header "推送Docker镜像"
    
    # 检查是否已登录
    if ! docker info | grep -q "Username"; then
        print_error "未登录到Docker仓库"
        echo "请先运行: docker login"
        exit 1
    fi
    
    # 推送镜像
    print_message "推送镜像到仓库: $DOCKER_REGISTRY:$VERSION"
    docker push "$DOCKER_REGISTRY:$VERSION"
    
    # 推送latest标签
    if [ "$VERSION" != "latest" ]; then
        print_message "推送镜像到仓库: $DOCKER_REGISTRY:latest"
        docker push "$DOCKER_REGISTRY:latest"
    fi
    
    print_message "镜像推送完成"
}

# 创建镜像扫描
scan_image() {
    print_header "扫描Docker镜像"
    
    # 检查是否安装了安全扫描工具
    if command -v trivy > /dev/null 2>&1; then
        print_message "使用Trivy进行安全扫描"
        trivy image "$DOCKER_REGISTRY:$VERSION"
    else
        print_warning "Trivy未安装，跳过安全扫描"
        print_message "安装Trivy: https://github.com/aquasecurity/trivy"
    fi
}

# 生成SBOM
generate_sbom() {
    print_header "生成软件物料清单(SBOM)"
    
    # 检查是否安装了Syft
    if command -v syft > /dev/null 2>&1; then
        print_message "使用Syft生成SBOM"
        syft "$DOCKER_REGISTRY:$VERSION" -o cyclonedx-json -o sbom.json
        
        # 显示SBOM信息
        if [ -f "sbom.json" ]; then
            DEPENDENCIES=$(jq '.components | length' sbom.json)
            echo "依赖包数量: $DEPENDENCIES"
            echo "SBOM文件: sbom.json"
        fi
    else
        print_warning "Syft未安装，跳过SBOM生成"
        print_message "安装Syft: https://github.com/anchore/syft"
    fi
}

# 创建构建信息文件
create_build_info() {
    print_header "创建构建信息"
    
    # 创建构建信息文件
    cat > build-info.json << EOF
{
    "project": "$PROJECT_NAME",
    "version": "$VERSION",
    "registry": "$DOCKER_REGISTRY",
    "build_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "docker_version": "$(docker --version 2>/dev/null || echo 'unknown')",
    "build_args": [
        "DOCKERFILE=$DOCKERFILE",
        "BUILD_CONTEXT=$BUILD_CONTEXT",
        "NO_CACHE=$NO_CACHE",
        "PUSH_IMAGE=$PUSH_IMAGE"
    ]
}
EOF
    
    print_message "构建信息已保存到: build-info.json"
}

# 显示构建信息
show_build_info() {
    print_header "构建信息"
    
    echo -e "${GREEN}项目名称:${NC} $PROJECT_NAME"
    echo -e "${GREEN}镜像版本:${NC} $VERSION"
    echo -e "${GREEN}仓库地址:${NC} $DOCKER_REGISTRY"
    echo -e "${GREEN}Dockerfile:${NC} $DOCKERFILE"
    echo -e "${GREEN}构建上下文:${NC} $BUILD_CONTEXT"
    echo -e "${GREEN}推送镜像:${NC} $PUSH_IMAGE"
    echo -e "${GREEN}无缓存构建:${NC} $NO_CACHE"
    
    if [ -f "build-info.json" ]; then
        echo -e "${GREEN}构建信息文件:${NC} build-info.json"
    fi
}

# 主函数
main() {
    print_header "SuperRPG Docker镜像构建"
    
    # 解析命令行参数
    parse_args "$@"
    
    # 显示构建信息
    show_build_info
    
    # 检查Docker环境
    check_docker
    
    # 验证构建上下文
    validate_build_context
    
    # 创建Dockerfile（如果不存在）
    create_dockerfile
    
    # 创建构建信息文件
    create_build_info
    
    # 构建镜像
    build_image
    
    # 测试镜像
    test_image
    
    # 扫描镜像
    scan_image
    
    # 生成SBOM
    generate_sbom
    
    # 推送镜像
    if [ "$PUSH_IMAGE" = true ]; then
        push_image
    fi
    
    print_message "Docker镜像构建完成！"
    
    # 显示后续步骤
    echo ""
    echo -e "${GREEN}后续步骤:${NC}"
    echo "1. 测试镜像:"
    echo "   docker run -p 8000:8000 $DOCKER_REGISTRY:$VERSION"
    echo ""
    echo "2. 推送镜像到仓库:"
    echo "   docker push $DOCKER_REGISTRY:$VERSION"
    echo ""
    echo "3. 使用docker-compose部署:"
    echo "   在docker-compose.yml中指定image: $DOCKER_REGISTRY:$VERSION"
    echo ""
    echo "4. 查看镜像信息:"
    echo "   docker images $DOCKER_REGISTRY:$VERSION"
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 设置默认值
    MULTI_PLATFORM_BUILD=${MULTI_PLATFORM_BUILD:-false}
    CLEANUPABLE=${CLEANUPABLE:-true}
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --multi-platform)
                MULTI_PLATFORM_BUILD=true
                shift
                ;;
            *)
                parse_args "$@"
                break
                ;;
        esac
    done
    
    main "$@"
fi