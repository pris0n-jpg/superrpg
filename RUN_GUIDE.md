# SuperRPG 运行指南

## 概述

SuperRPG 项目现已修复了Python导入问题，支持多种运行方式。本文档详细说明了如何在不同环境中运行应用程序。


## 前后端联调

要体验新的管理界面，需要同时运行后端 API 服务与前端开发服务器：

1. 在项目根目录启动 API 服务（默认端口 3010）：
       python -m src.api.server
   服务会在 data/ 目录下维护 JSON 存储文件，可通过环境变量 SUPERRPG_DATA_DIR 自定义位置。

2. 在 frontend/ 目录启动前端：
       npm run dev
   Vite 会将 /api 请求代理到本地 API 服务，构建版本同样使用相对路径访问接口。


## 运行方式

### 1. 直接运行脚本（推荐）

```bash
python src/main.py
```

这种方式最简单直接，适合快速测试和开发。

### 2. 作为模块运行

```bash
python -m src.main
```

这种方式将 `src` 作为Python包处理，适合更规范的项目结构。

### 3. 在Conda环境中运行

```bash
# 激活npc-talk环境
conda activate npc-talk

# 运行应用程序
python src/main.py
```

或者：

```bash
conda activate npc-talk
python -m src.main
```

## 环境要求

- Python 3.11+
- 推荐使用 conda 环境 `npc-talk`
- 依赖项：agentscope（通过Git安装）

## 项目结构

```
superrpg/
├── src/                    # 源代码目录
│   ├── main.py            # 主入口文件
│   ├── bootstrap.py       # 应用启动器
│   ├── core/              # 核心模块
│   ├── application/       # 应用服务层
│   ├── domain/            # 领域模型
│   ├── adapters/          # 适配器层
│   └── settings/          # 配置加载器
├── configs/               # 配置文件目录
├── docs/                  # 文档目录
└── tests/                 # 测试目录
```

## 导入修复说明

### 问题描述

原始的 `src/main.py` 使用相对导入（如 `from .bootstrap import ...`），当直接运行 `python src/main.py` 时会出现以下错误：

```
ImportError: attempted relative import with no known parent package
```

### 解决方案

实现了智能导入机制，支持两种运行方式：

1. **相对导入优先**：首先尝试使用相对导入（作为模块运行时）
2. **绝对导入回退**：如果相对导入失败，自动回退到绝对导入（直接运行脚本时）

### 修复内容

- **src/main.py**：修复了所有相对导入语句
- **src/bootstrap.py**：修复了核心模块的导入问题
- 保持向后兼容性，不影响现有的模块运行方式

## 配置文件

应用程序会在以下位置查找配置文件：

- `configs/model.json` - 模型配置
- `configs/characters.json` - 角色配置
- `configs/story.json` - 故事配置
- `configs/feature_flags.json` - 功能标志

如果配置文件不存在，应用程序会使用默认配置继续运行。

## 日志输出

应用程序会输出详细的日志信息，包括：

- 应用启动过程
- 配置加载状态
- 依赖注入容器初始化
- 适配器初始化
- 游戏运行状态

日志同时输出到控制台和文件 `logs/application.log`。

## 故障排除

### 导入错误

如果遇到导入错误，请确保：

1. 在项目根目录运行命令
2. Python版本 >= 3.11
3. 所有依赖项已正确安装

### 配置问题

如果配置加载失败，应用程序会：

1. 显示警告信息
2. 使用默认配置继续运行
3. 在遗留模式下提供更好的容错性

### 环境问题

如果遇到环境相关问题：

1. 确保在正确的Python环境中
2. 检查PATH环境变量
3. 验证conda环境是否正确激活

## 开发建议

1. **开发阶段**：使用 `python src/main.py` 快速测试
2. **生产环境**：使用 `python -m src.main` 规范运行
3. **CI/CD**：推荐模块运行方式，更加稳定

## 技术细节

导入修复采用了以下技术：

- **动态路径检测**：自动检测运行环境
- **优雅降级**：相对导入失败时自动回退
- **路径管理**：动态添加项目根目录到Python路径
- **错误处理**：提供详细的错误信息和解决方案

这种修复方式确保了：
- 不破坏现有功能
- 支持多种运行方式
- 保持代码可读性和维护性
- 提供良好的用户体验