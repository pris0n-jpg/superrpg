#!/usr/bin/env python3
"""
SuperRPG 应用程序主入口

该模块是SuperRPG应用程序的主入口点，集成了所有模块化架构组件。
使用增强应用启动器提供统一的启动、配置和管理功能。

主要职责：
1. 启动模块化应用
2. 配置应用参数
3. 集成所有核心模块
4. 处理应用生命周期
5. 提供错误处理和日志记录
"""

import asyncio
import logging
import sys
import os
import traceback
from typing import Dict, Any, Optional
from pathlib import Path

# 导入增强应用启动器
try:
    # 尝试相对导入（作为模块运行时）
    from .bootstrap.enhanced_application_bootstrap import (
        EnhancedApplicationBootstrap,
        EnhancedApplicationContext,
        BootstrapConfig,
        run_enhanced_application
    )
    from .infrastructure.config.enhanced_config_manager import EnhancedConfigManager
    from .adapters.api_documentation import DocumentationManager
    from .adapters.api_gateway import ApiGateway
    from .core.interfaces import Logger, GameCoordinator as IGameCoordinator
except ImportError:
    # 回退到绝对导入（直接运行脚本时）
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.bootstrap.enhanced_application_bootstrap import (
        EnhancedApplicationBootstrap,
        EnhancedApplicationContext,
        BootstrapConfig,
        run_enhanced_application
    )
    from src.infrastructure.config.enhanced_config_manager import EnhancedConfigManager
    from src.adapters.api_documentation import DocumentationManager
    from src.adapters.api_gateway import ApiGateway
    from src.core.interfaces import Logger, GameCoordinator as IGameCoordinator


def configure_logging() -> None:
    """配置日志系统"""
    # 确保logs目录存在
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/application.log', encoding='utf-8')
        ]
    )
    
    # 设置第三方库日志级别
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('watchdog').setLevel(logging.WARNING)


def create_bootstrap_config() -> BootstrapConfig:
    """创建启动器配置
    
    Returns:
        BootstrapConfig: 启动器配置
    """
    # 从环境变量获取配置
    env = os.environ
    
    return BootstrapConfig(
        enable_extensions=env.get('ENABLE_EXTENSIONS', 'true').lower() == 'true',
        enable_api_gateway=env.get('ENABLE_API_GATEWAY', 'true').lower() == 'true',
        enable_health_checks=env.get('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
        enable_graceful_shutdown=env.get('ENABLE_GRACEFUL_SHUTDOWN', 'true').lower() == 'true',
        shutdown_timeout=int(env.get('SHUTDOWN_TIMEOUT', '30')),
        health_check_interval=int(env.get('HEALTH_CHECK_INTERVAL', '30')),
        extensions_dir=env.get('EXTENSIONS_DIR', 'extensions'),
        config_dir=env.get('CONFIG_DIR', 'configs'),
        log_level=env.get('LOG_LEVEL', 'INFO')
    )


def create_application_config() -> Dict[str, Any]:
    """创建应用配置
    
    Returns:
        Dict[str, Any]: 应用配置
    """
    return {
        # 游戏配置
        "game": {
            "max_rounds": int(os.environ.get('MAX_ROUNDS', '50')),
            "turn_timeout": int(os.environ.get('TURN_TIMEOUT', '30')),
            "agent_timeout": int(os.environ.get('AGENT_TIMEOUT', '30')),
            "require_hostiles": os.environ.get('REQUIRE_HOSTILES', 'true').lower() == 'true',
            "debug_mode": os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
        },
        
        # AI配置
        "ai": {
            "model": os.environ.get('AI_MODEL', 'gpt-3.5-turbo'),
            "api_key": os.environ.get('AI_API_KEY', ''),
            "base_url": os.environ.get('AI_BASE_URL', 'https://api.openai.com/v1'),
            "temperature": float(os.environ.get('AI_TEMPERATURE', '0.7')),
            "max_tokens": int(os.environ.get('AI_MAX_TOKENS', '1000'))
        },
        
        # API配置
        "api": {
            "host": os.environ.get('API_HOST', 'localhost'),
            "port": int(os.environ.get('API_PORT', '3010')),
            "enable_cors": os.environ.get('API_ENABLE_CORS', 'true').lower() == 'true',
            "enable_docs": os.environ.get('API_ENABLE_DOCS', 'true').lower() == 'true'
        },
        
        # 数据库配置
        "database": {
            "url": os.environ.get('DATABASE_URL', 'sqlite:///game.db'),
            "echo": os.environ.get('DATABASE_ECHO', 'false').lower() == 'true'
        },
        
        # 扩展配置
        "extensions": {
            "auto_load": os.environ.get('EXTENSIONS_AUTO_LOAD', 'true').lower() == 'true',
            "auto_activate": os.environ.get('EXTENSIONS_AUTO_ACTIVATE', 'true').lower() == 'true'
        }
    }


async def setup_api_routes(bootstrap: EnhancedApplicationBootstrap) -> None:
    """设置API路由
    
    Args:
        bootstrap: 应用启动器
    """
    if not bootstrap.api_gateway:
        return
    
    gateway = bootstrap.api_gateway
    
    # 健康检查路由
    async def health_handler(**kwargs):
        if bootstrap.health_checker:
            return await bootstrap.health_checker.check_health().to_dict()
        return {"status": "ok"}
    
    gateway.add_route(
        path="/health",
        method="GET",
        handler=health_handler,
        name="health_check",
        tags=["health"]
    )
    
    # 应用信息路由
    async def info_handler(**kwargs):
        stats = bootstrap.get_stats()
        return {
            "success": True,
            "data": {
                "application": "SuperRPG",
                "version": "2.0.0",
                "description": "模块化角色扮演游戏系统",
                "stats": stats
            }
        }
    
    gateway.add_route(
        path="/info",
        method="GET",
        handler=info_handler,
        name="app_info",
        tags=["info"]
    )
    
    # 模块信息路由
    async def modules_handler(**kwargs):
        modules = bootstrap.list_modules()
        return {
            "success": True,
            "data": {
                "modules": [module.to_dict() for module in modules],
                "loaded": bootstrap.loaded_modules
            }
        }
    
    gateway.add_route(
        path="/modules",
        method="GET",
        handler=modules_handler,
        name="modules_info",
        tags=["modules"]
    )
    
    # 扩展信息路由
    async def extensions_handler(**kwargs):
        if not bootstrap.extension_manager:
            return {"success": True, "data": {"extensions": []}}
        
        try:
            extensions = await bootstrap.extension_manager.registry.list_extensions()
            return {
                "success": True,
                "data": {
                    "extensions": [
                        {
                            "name": ext.metadata.name,
                            "version": ext.metadata.version,
                            "status": ext.status.value,
                            "type": ext.metadata.extension_type.value,
                            "description": ext.metadata.description
                        }
                        for ext in extensions
                    ]
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取扩展信息失败: {str(e)}"
            }
    
    gateway.add_route(
        path="/extensions",
        method="GET",
        handler=extensions_handler,
        name="extensions_info",
        tags=["extensions"]
    )


async def generate_documentation(bootstrap: EnhancedApplicationBootstrap) -> None:
    """生成API文档
    
    Args:
        bootstrap: 应用启动器
    """
    if not bootstrap.api_gateway:
        return
    
    try:
        # 创建文档管理器
        docs_manager = DocumentationManager(
            gateway=bootstrap.api_gateway,
            output_dir="docs"
        )
        
        # 添加自定义模式
        docs_manager.add_schema("GameConfig", {
            "type": "object",
            "properties": {
                "max_rounds": {"type": "integer"},
                "turn_timeout": {"type": "integer"},
                "require_hostiles": {"type": "boolean"}
            }
        })
        
        # 生成所有格式的文档
        file_paths = docs_manager.generate_all_formats("superrpg_api")
        
        logger = bootstrap.container.resolve(Logger)
        logger.info(f"API文档生成完成: {file_paths}")
        
    except Exception as e:
        logger = bootstrap.container.resolve(Logger)
        logger.error(f"生成API文档失败: {str(e)}")


async def run_game_application(bootstrap: EnhancedApplicationBootstrap) -> None:
    """运行游戏应用
    
    Args:
        bootstrap: 应用启动器
    """
    container = bootstrap.container
    logger = container.resolve(Logger)
    
    try:
        # 检查是否启用游戏模式
        app_config = container.resolve(EnhancedConfigManager).get("game", {})
        
        if not app_config.get("debug_mode", False):
            logger.info("启动游戏模式...")
            
            # 解析游戏协调器（依赖接口以遵循DIP）
            game_coordinator = container.resolve(IGameCoordinator)
            
            # 运行游戏
            await game_coordinator.run_game()
            
            logger.info("游戏运行完成")
        else:
            logger.info("调试模式：跳过游戏运行")
            
            # 在调试模式下，保持应用运行
            logger.info("应用运行中，按 Ctrl+C 停止...")
            while True:
                await asyncio.sleep(1)
        
    except Exception as e:
        logger.error(f"游戏应用运行失败: {str(e)}")
        raise


def print_startup_banner(config: BootstrapConfig) -> None:
    """打印启动横幅
    
    Args:
        config: 启动器配置
    """
    print("=" * 80)
    print("SuperRPG 应用程序 (模块化架构版本)")
    print("=" * 80)
    print(f"版本: 2.0.0")
    print(f"Python: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    print("\n[配置信息]")
    print(f"  扩展系统: {'启用' if config.enable_extensions else '禁用'}")
    print(f"  API网关: {'启用' if config.enable_api_gateway else '禁用'}")
    print(f"  健康检查: {'启用' if config.enable_health_checks else '禁用'}")
    print(f"  优雅关闭: {'启用' if config.enable_graceful_shutdown else '禁用'}")
    print(f"  配置目录: {config.config_dir}")
    
    if config.enable_extensions:
        print(f"  扩展目录: {config.extensions_dir}")
    
    print("\n[模块状态]")
    print("  核心系统: core, event_bus, api_gateway")
    print("  游戏系统: game_engine, character_system, world_system")
    print("  基础设施: extension_system, documentation")
    
    print("=" * 80)


async def main() -> None:
    """应用程序主入口"""
    # 配置日志
    configure_logging()
    logger = logging.getLogger(__name__)

    # 创建配置
    bootstrap_config = create_bootstrap_config()
    app_config = create_application_config()

    # 打印启动横幅
    print_startup_banner(bootstrap_config)

    bootstrap = None
    try:
        # 创建并启动应用
        bootstrap = EnhancedApplicationBootstrap(bootstrap_config)
        container = await bootstrap.bootstrap(app_config)

        logger.info("应用程序启动成功")

        # 设置API路由
        await setup_api_routes(bootstrap)

        # 生成API文档
        if app_config.get("api", {}).get("enable_docs", True):
            await generate_documentation(bootstrap)

        # 运行游戏应用
        await run_game_application(bootstrap)

        logger.info("应用程序运行完成")

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭应用程序...")
    except Exception as e:
        logger.error(f"应用程序运行失败: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"\n错误详情:\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        # 清理资源
        if bootstrap:
            await bootstrap.shutdown()

    print("\n" + "=" * 80)
    print("程序已正常结束")
    print("=" * 80)


if __name__ == "__main__":
    # 运行主程序
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n收到中断信号，程序退出")
        sys.exit(0)
