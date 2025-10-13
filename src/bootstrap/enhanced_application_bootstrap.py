
"""
增强应用启动器模块

该模块实现增强的应用启动器，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责模块化组件加载、扩展自动发现和健康检查。
"""

import asyncio
import logging
import signal
import sys
import time
import threading
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from ..core.container import DIContainer, ServiceLocator
from ..core.interfaces import Logger, EventBus
from ..application.services.extension_manager_service import (
    ExtensionManagerImpl, ExtensionRegistryImpl, ExtensionLoaderImpl
)
from ..infrastructure.events.enhanced_event_bus import EnhancedEventBus
from ..infrastructure.config.enhanced_config_manager import EnhancedConfigManager, ConfigSchema
from ..application.container_config import (
    configure_application_container,
    get_default_application_config
)
from ..adapters.api_gateway import ApiGateway
from ..adapters.middleware import (
    AuthMiddleware, LoggingMiddleware, CorsMiddleware,
    RateLimitMiddleware, ErrorHandlerMiddleware
)
from ..domain.responses.api_response import HealthCheckResponse, ResponseBuilder
from ..core.exceptions import (
    BaseException as CustomBaseException, InfrastructureException,
    ConfigurationException, ServiceUnavailableException
)


class LoggerAdapter(Logger):
    """日志记录器适配器

    将标准库的logging.Logger适配为符合Logger接口的实现。
    遵循适配器模式和依赖倒置原则(DIP)。
    """

    def __init__(self, logger: logging.Logger):
        """初始化日志适配器

        Args:
            logger: 标准库的日志记录器
        """
        self._logger = logger

    def info(self, message: str, **kwargs) -> None:
        """记录信息日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """记录错误日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.debug(message, extra=kwargs)


@dataclass
class ModuleInfo:
    """模块信息
    
    封装模块的基本信息，遵循单一职责原则。
    """
    
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 0
    config_schema: Optional[List[ConfigSchema]] = None
    health_check_endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 模块信息的字典表示
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "dependencies": self.dependencies,
            "enabled": self.enabled,
            "priority": self.priority,
            "health_check_endpoint": self.health_check_endpoint
        }


@dataclass
class BootstrapConfig:
    """启动器配置
    
    封装启动器的配置信息，遵循单一职责原则。
    """
    
    enable_extensions: bool = True
    enable_api_gateway: bool = True
    enable_health_checks: bool = True
    enable_graceful_shutdown: bool = True
    shutdown_timeout: int = 30
    health_check_interval: int = 30
    extensions_dir: str = "extensions"
    config_dir: str = "configs"
    log_level: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 配置的字典表示
        """
        return {
            "enable_extensions": self.enable_extensions,
            "enable_api_gateway": self.enable_api_gateway,
            "enable_health_checks": self.enable_health_checks,
            "enable_graceful_shutdown": self.enable_graceful_shutdown,
            "shutdown_timeout": self.shutdown_timeout,
            "health_check_interval": self.health_check_interval,
            "extensions_dir": self.extensions_dir,
            "config_dir": self.config_dir,
            "log_level": self.log_level
        }


class HealthChecker:
    """健康检查器
    
    提供健康检查功能，遵循单一职责原则。
    """
    
    def __init__(self, logger: Logger):
        """初始化健康检查器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        self.health_checks: Dict[str, Callable] = {}
        self.last_check_time: Optional[datetime] = None
        self.check_results: Dict[str, Dict[str, Any]] = {}
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """注册健康检查
        
        Args:
            name: 检查名称
            check_func: 检查函数
        """
        self.health_checks[name] = check_func
    
    def unregister_health_check(self, name: str) -> bool:
        """注销健康检查
        
        Args:
            name: 检查名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self.health_checks:
            del self.health_checks[name]
            if name in self.check_results:
                del self.check_results[name]
            return True
        return False
    
    async def check_health(self) -> HealthCheckResponse:
        """执行健康检查
        
        Returns:
            HealthCheckResponse: 健康检查响应
        """
        self.last_check_time = datetime.now()
        services = {}
        overall_status = "healthy"
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = time.time() - start_time
                
                # 解析结果
                if isinstance(result, dict):
                    status = result.get("status", "healthy")
                    message = result.get("message", "OK")
                elif isinstance(result, bool):
                    status = "healthy" if result else "unhealthy"
                    message = "OK" if result else "Check failed"
                else:
                    status = "healthy"
                    message = str(result)
                
                services[name] = {
                    "status": status,
                    "message": message,
                    "duration_ms": round(duration * 1000, 2),
                    "timestamp": self.last_check_time.isoformat()
                }
                
                if status != "healthy":
                    overall_status = "unhealthy"
                    
            except Exception as e:
                services[name] = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": self.last_check_time.isoformat()
                }
                overall_status = "error"
                
                self.logger.error(f"健康检查失败 {name}: {str(e)}")
        
        # 保存检查结果
        self.check_results = services.copy()
        
        # 计算运行时间
        uptime = time.time() if hasattr(self, '_start_time') else 0
        
        return ResponseBuilder.health(
            status=overall_status,
            version="1.0.0",
            uptime=uptime,
            services=services
        )
    
    def get_last_results(self) -> Dict[str, Dict[str, Any]]:
        """获取最后一次检查结果
        
        Returns:
            Dict[str, Dict[str, Any]]: 检查结果
        """
        return self.check_results.copy()
    
    def set_start_time(self, start_time: float) -> None:
        """设置启动时间
        
        Args:
            start_time: 启动时间戳
        """
        self._start_time = start_time


class GracefulShutdown:
    """优雅关闭处理器
    
    负责应用的优雅关闭，遵循单一职责原则。
    """
    
    def __init__(self, logger: Logger, timeout: int = 30):
        """初始化优雅关闭处理器
        
        Args:
            logger: 日志记录器
            timeout: 关闭超时时间（秒）
        """
        self.logger = logger
        self.timeout = timeout
        self.shutdown_handlers: List[Callable] = []
        self.is_shutting_down = False
        self.shutdown_event = threading.Event()
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """注册关闭处理器
        
        Args:
            handler: 关闭处理器函数
        """
        self.shutdown_handlers.append(handler)
    
    async def shutdown(self) -> None:
        """执行优雅关闭"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        self.logger.info("开始优雅关闭...")
        
        try:
            # 并行执行所有关闭处理器
            tasks = []
            for handler in self.shutdown_handlers:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler())
                else:
                    # 在线程池中执行同步处理器
                    loop = asyncio.get_event_loop()
                    task = loop.run_in_executor(None, handler)
                    tasks.append(task)
            
            if tasks:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=self.timeout
                )
            
            self.logger.info("优雅关闭完成")
            
        except asyncio.TimeoutError:
            self.logger.warning(f"优雅关闭超时（{self.timeout}秒）")
        except Exception as e:
            self.logger.error(f"优雅关闭过程中出错: {str(e)}")
        finally:
            self.shutdown_event.set()
    
    def wait_for_shutdown(self) -> None:
        """等待关闭完成"""
        self.shutdown_event.wait()


class EnhancedApplicationBootstrap:
    """增强应用启动器
    
    提供完整的应用启动和管理功能，包括模块化加载、扩展管理和健康检查。
    """
    
    def __init__(self, config: Optional[BootstrapConfig] = None):
        """初始化增强应用启动器
        
        Args:
            config: 启动器配置
        """
        self.config = config or BootstrapConfig()
        
        # 核心组件
        self.container: Optional[DIContainer] = None
        self.logger: Optional[Logger] = None
        self.event_bus: Optional[EventBus] = None
        self.config_manager: Optional[EnhancedConfigManager] = None
        self.api_gateway: Optional[ApiGateway] = None
        
        # 扩展系统
        self.extension_manager: Optional[ExtensionManagerImpl] = None
        
        # 健康检查
        self.health_checker: Optional[HealthChecker] = None
        
        # 优雅关闭
        self.graceful_shutdown: Optional[GracefulShutdown] = None
        
        # 模块管理
        self.modules: Dict[str, ModuleInfo] = {}
        self.loaded_modules: List[str] = []
        
        # 启动状态
        self.is_running = False
        self.start_time: Optional[float] = None
        
        # 统计信息
        self.stats = {
            "startup_time": 0.0,
            "modules_loaded": 0,
            "extensions_loaded": 0,
            "health_checks_count": 0,
            "last_health_check": None
        }
    
    async def bootstrap(self, custom_config: Optional[Dict[str, Any]] = None) -> DIContainer:
        """启动应用

        Args:
            custom_config: 自定义配置

        Returns:
            DIContainer: 依赖注入容器
        """
        start_time = time.time()

        try:
            # 1. 初始化基础组件（包括logger）
            await self._initialize_core_components()

            self.logger.info("开始启动增强应用...")

            # 2. 加载配置
            await self._load_configuration(custom_config)

            # 3. 初始化容器
            await self._initialize_container()
            
            # 4. 设置中间件
            await self._setup_middleware()
            
            # 5. 加载模块
            await self._load_modules()
            
            # 6. 初始化扩展系统
            if self.config.enable_extensions:
                await self._initialize_extension_system()
            
            # 7. 初始化健康检查
            if self.config.enable_health_checks:
                await self._initialize_health_checks()
            
            # 8. 初始化API网关
            if self.config.enable_api_gateway:
                await self._initialize_api_gateway()
            
            # 9. 设置优雅关闭
            if self.config.enable_graceful_shutdown:
                await self._setup_graceful_shutdown()
            
            # 10. 启动完成
            self.is_running = True
            self.start_time = time.time()
            self.stats["startup_time"] = self.start_time - start_time
            
            self.logger.info(f"应用启动完成，耗时 {self.stats['startup_time']:.2f} 秒")
            
            return self.container
            
        except Exception as e:
            self.logger.error(f"应用启动失败: {str(e)}")
            await self._cleanup()
            raise
    
    async def _initialize_core_components(self) -> None:
        """初始化核心组件"""
        # 初始化配置管理器
        self.config_manager = EnhancedConfigManager(
            config_dir=self.config.config_dir,
            auto_reload=True,
            enable_validation=True
        )

        # 初始化日志系统
        log_level = getattr(logging, self.config.log_level.upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        # 创建标准库logger并用适配器包装
        stdlib_logger = logging.getLogger("EnhancedApplicationBootstrap")
        self.logger = LoggerAdapter(stdlib_logger)

        # 初始化事件总线
        self.event_bus = EnhancedEventBus(
            enable_persistence=True,
            enable_metrics=True
        )

        self.logger.info("核心组件初始化完成")
    
    async def _load_configuration(self, custom_config: Optional[Dict[str, Any]] = None) -> None:
        """加载配置"""
        try:
            # 加载主配置文件
            config_file = f"{self.config.config_dir}/config.json"
            if Path(config_file).exists():
                self.config_manager.load(config_file)
            
            # 应用自定义配置
            if custom_config:
                for key, value in custom_config.items():
                    self.config_manager.set(key, value, persist=False)
            
            # 添加配置变更监听器
            self.config_manager.add_change_listener(self._on_config_change)
            
            self.logger.info("配置加载完成")
            
        except Exception as e:
            raise ConfigurationException(f"配置加载失败: {str(e)}")
    
    async def _initialize_container(self) -> None:
        """初始化依赖注入容器"""
        self.container = DIContainer()
        
        # 注册核心组件
        self.container.register_instance(Logger, self.logger)
        self.container.register_instance(EventBus, self.event_bus)
        self.container.register_instance(EnhancedConfigManager, self.config_manager)
        
        # 载入应用层配置并注册服务
        app_settings = get_default_application_config()
        game_settings = self.config_manager.get("game", {})
        if isinstance(game_settings, dict):
            app_settings["turn_timeout"] = game_settings.get("turn_timeout", app_settings["turn_timeout"])
            app_settings["agent_timeout"] = game_settings.get("agent_timeout", app_settings["agent_timeout"])
            app_settings["max_rounds"] = game_settings.get("max_rounds", app_settings["max_rounds"])
            app_settings["require_hostiles"] = game_settings.get("require_hostiles", app_settings["require_hostiles"])
            app_settings["debug_mode"] = game_settings.get("debug_mode", app_settings["debug_mode"])

        extensions_settings = self.config_manager.get("extensions", {})
        if isinstance(extensions_settings, dict):
            app_settings["tool_executors"] = extensions_settings.get("tool_executors", app_settings["tool_executors"])
            app_settings["agent_factories"] = extensions_settings.get("agent_factories", app_settings["agent_factories"])

        configure_application_container(
            container=self.container,
            event_bus=self.event_bus,
            logger=self.logger,
            custom_config=app_settings
        )

        # 设置服务定位器，便于遗留调用路径继续工作
        ServiceLocator.set_container(self.container)
        
        self.logger.info("依赖注入容器初始化完成")
    
    async def _setup_middleware(self) -> None:
        """设置中间件"""
        # 这里可以设置全局中间件
        # 具体实现取决于中间件系统
        self.logger.info("中间件设置完成")
    
    async def _load_modules(self) -> None:
        """加载模块"""
        # 加载模块配置
        modules_config_file = f"{self.config.config_dir}/modules.json"
        if Path(modules_config_file).exists():
            modules_config = self.config_manager.load(modules_config_file)
            
            # 注册模块
            for module_data in modules_config.get("modules", []):
                module_info = ModuleInfo(**module_data)
                self.modules[module_info.name] = module_info
            
            # 按优先级排序并加载
            sorted_modules = sorted(
                self.modules.values(),
                key=lambda m: m.priority,
                reverse=True
            )
            
            for module in sorted_modules:
                if module.enabled:
                    await self._load_module(module)
        
        self.logger.info(f"模块加载完成，共加载 {self.stats['modules_loaded']} 个模块")
    
    async def _load_module(self, module_info: ModuleInfo) -> None:
        """加载单个模块
        
        Args:
            module_info: 模块信息
        """
        try:
            # 检查依赖
            for dep in module_info.dependencies:
                if dep not in self.loaded_modules:
                    self.logger.warning(f"模块 {module_info.name} 的依赖 {dep} 未加载")
                    return
            
            # 加载模块（具体实现取决于模块系统）
            # 这里只是示例，实际实现会更复杂
            self.loaded_modules.append(module_info.name)
            self.stats["modules_loaded"] += 1
            
            self.logger.info(f"模块加载成功: {module_info.name}")
            
        except Exception as e:
            self.logger.error(f"模块加载失败 {module_info.name}: {str(e)}")
    
    async def _initialize_extension_system(self) -> None:
        """初始化扩展系统"""
        try:
            # 创建扩展组件
            registry = ExtensionRegistryImpl()
            loader = ExtensionLoaderImpl()
            
            self.extension_manager = ExtensionManagerImpl(
                registry=registry,
                loader=loader,
                container=self.container,
                event_bus=self.event_bus,
                logger=self.logger,
                extensions_dir=self.config.extensions_dir
            )
            
            # 加载所有扩展
            await self.extension_manager.load_all_extensions()
            
            # 注册扩展管理器
            self.container.register_instance(ExtensionManagerImpl, self.extension_manager)
            
            self.logger.info("扩展系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"扩展系统初始化失败: {str(e)}")
    
    async def _initialize_health_checks(self) -> None:
        """初始化健康检查"""
        self.health_checker = HealthChecker(self.logger)
        self.health_checker.set_start_time(time.time())
        
        # 注册基础健康检查
        self.health_checker.register_health_check("application", self._check_application_health)
        self.health_checker.register_health_check("database", self._check_database_health)
        self.health_checker.register_health_check("event_bus", self._check_event_bus_health)
        
        if self.extension_manager:
            self.health_checker.register_health_check("extensions", self._check_extensions_health)
        
        # 启动定期健康检查
        if self.config.health_check_interval > 0:
            asyncio.create_task(self._health_check_loop())
        
        self.logger.info("健康检查系统初始化完成")
    
    async def _initialize_api_gateway(self) -> None:
        """初始化API网关"""
        self.api_gateway = ApiGateway(
            name="SuperRPG API Gateway",
            version="1.0.0"
        )
        
        # 添加健康检查端点
        self.api_gateway.add_route(
            path="/health",
            method="GET",
            handler=self._health_check_handler,
            name="health_check"
        )
        
        # 注册API网关
        self.container.register_instance(ApiGateway, self.api_gateway)
        
        self.logger.info("API网关初始化完成")
    
    async def _setup_graceful_shutdown(self) -> None:
        """设置优雅关闭"""
        self.graceful_shutdown = GracefulShutdown(
            logger=self.logger,
            timeout=self.config.shutdown_timeout
        )
        
        # 注册关闭处理器
        self.graceful_shutdown.register_shutdown_handler(self._cleanup)
        
        # 注册信号处理器
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("优雅关闭设置完成")
    
    async def _health_check_loop(self) -> None:
        """健康检查循环"""
        while self.is_running:
            try:
                await self.health_checker.check_health()
                self.stats["health_checks_count"] += 1
                self.stats["last_health_check"] = datetime.now().isoformat()
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康检查失败: {str(e)}")
                await asyncio.sleep(5)
    
    async def _health_check_handler(self, **kwargs) -> Dict[str, Any]:
        """健康检查处理器
        
        Args:
            **kwargs: 请求参数
            
        Returns:
            Dict[str, Any]: 健康检查响应
        """
        if not self.health_checker:
            return ResponseBuilder.error("健康检查系统未初始化").to_dict()
        
        result = await self.health_checker.check_health()
        return result.to_dict()
    
    async def _check_application_health(self) -> Dict[str, Any]:
        """检查应用健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "message": "应用运行正常" if self.is_running else "应用未运行",
            "uptime": time.time() - self.start_time if self.start_time else 0
        }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """检查数据库健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        # 这里应该实现实际的数据库健康检查
        return {
            "status": "healthy",
            "message": "数据库连接正常"
        }
    
    async def _check_event_bus_health(self) -> Dict[str, Any]:
        """检查事件总线健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        if not self.event_bus:
            return {
                "status": "unhealthy",
                "message": "事件总线未初始化"
            }
        
        # 获取事件总线指标
        if hasattr(self.event_bus, 'get_metrics'):
            metrics = self.event_bus.get_metrics()
            return {
                "status": "healthy",
                "message": "事件总线运行正常",
                "metrics": metrics
            }
        
        return {
            "status": "healthy",
            "message": "事件总线运行正常"
        }
    
    async def _check_extensions_health(self) -> Dict[str, Any]:
        """检查扩展系统健康状态
        
        Returns:
            Dict[str, Any]: 健康状态
        """
        if not self.extension_manager:
            return {
                "status": "unhealthy",
                "message": "扩展系统未初始化"
            }
        
        try:
            # 获取扩展统计
            extensions = await self.extension_manager.registry.list_extensions()
            active_extensions = [ext for ext in extensions if ext.status.value == "active"]
            
            return {
                "status": "healthy",
                "message": "扩展系统运行正常",
                "total_extensions": len(extensions),
                "active_extensions": len(active_extensions)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"扩展系统检查失败: {str(e)}"
            }
    
    def _on_config_change(self, event) -> None:
        """配置变更处理
        
        Args:
            event: 配置变更事件
        """
        self.logger.info(f"配置变更: {event.key} = {event.new_value}")
        
        # 这里可以添加配置变更的具体处理逻辑
        # 例如重新加载某些组件、更新设置等
    
    def _signal_handler(self, signum, frame) -> None:
        """信号处理器
        
        Args:
            signum: 信号编号
            frame: 堆栈帧
        """
        self.logger.info(f"收到信号 {signum}，开始优雅关闭...")
        
        # 在新线程中执行关闭，避免阻塞信号处理
        import threading
        threading.Thread(target=self._shutdown_in_thread, daemon=True).start()
    
    def _shutdown_in_thread(self) -> None:
        """在线程中执行关闭"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.shutdown())
        except Exception as e:
            self.logger.error(f"关闭过程中出错: {str(e)}")
    
    async def shutdown(self) -> None:
        """关闭应用"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("开始关闭应用...")
        
        try:
            # 执行优雅关闭
            if self.graceful_shutdown:
                await self.graceful_shutdown.shutdown()
            
            # 关闭各个组件
            await self._cleanup()
            
            self.logger.info("应用关闭完成")
            
        except Exception as e:
            self.logger.error(f"应用关闭失败: {str(e)}")
    
    async def _cleanup(self) -> None:
        """清理资源"""
        try:
            # 关闭API网关
            if self.api_gateway:
                # 这里可以添加API网关的清理逻辑
                pass
            
            # 关闭扩展系统
            if self.extension_manager:
                # 卸载所有扩展
                extensions = await self.extension_manager.registry.list_extensions()
                for ext in extensions:
                    await self.extension_manager.unload_extension(
                        f"{ext.metadata.name}:{ext.metadata.version}"
                    )
            
            # 关闭事件总线
            if self.event_bus and hasattr(self.event_bus, 'shutdown'):
                self.event_bus.shutdown()
            
            # 关闭配置管理器
            if self.config_manager and hasattr(self.config_manager, 'shutdown'):
                self.config_manager.shutdown()
            
            # 清理容器
            if self.container:
                self.container.clear_scope()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.stats.copy()
        
        if self.start_time:
            stats["uptime"] = time.time() - self.start_time
        
        stats["is_running"] = self.is_running
        stats["loaded_modules"] = self.loaded_modules.copy()
        stats["total_modules"] = len(self.modules)
        
        # 添加组件统计
        if self.health_checker:
            stats["health_checks"] = len(self.health_checker.health_checks)
            stats["last_health_check"] = self.health_checker.last_check_time.isoformat() if self.health_checker.last_check_time else None
        
        if self.extension_manager:
            try:
                extensions = asyncio.run(self.extension_manager.registry.list_extensions())
                stats["extensions"] = {
                    "total": len(extensions),
                    "active": len([ext for ext in extensions if ext.status.value == "active"]),
                    "loaded": len([ext for ext in extensions if ext.status.value in ["loaded", "active"]])
                }
            except Exception:
                stats["extensions"] = {"error": "无法获取扩展统计"}
        
        if self.event_bus and hasattr(self.event_bus, 'get_metrics'):
            stats["event_bus"] = self.event_bus.get_metrics()
        
        if self.config_manager:
            stats["config_manager"] = self.config_manager.get_stats()
        
        return stats
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """获取模块信息
        
        Args:
            module_name: 模块名称
            
        Returns:
            Optional[ModuleInfo]: 模块信息
        """
        return self.modules.get(module_name)
    
    def list_modules(self) -> List[ModuleInfo]:
        """列出所有模块
        
        Returns:
            List[ModuleInfo]: 模块列表
        """
        return list(self.modules.values())
    
    def is_module_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: 是否已加载
        """
        return module_name in self.loaded_modules
    
    async def reload_module(self, module_name: str) -> bool:
        """重新加载模块
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: 是否成功重新加载
        """
        if module_name not in self.modules:
            return False
        
        module_info = self.modules[module_name]
        
        # 卸载模块
        if module_name in self.loaded_modules:
            self.loaded_modules.remove(module_name)
        
        # 重新加载
        await self._load_module(module_info)
        
        return module_name in self.loaded_modules
    
    def add_module(self, module_info: ModuleInfo) -> None:
        """添加模块
        
        Args:
            module_info: 模块信息
        """
        self.modules[module_info.name] = module_info
    
    def remove_module(self, module_name: str) -> bool:
        """移除模块
        
        Args:
            module_name: 模块名称
            
        Returns:
            bool: 是否成功移除
        """
        if module_name in self.modules:
            del self.modules[module_name]
            return True
        return False


# 应用上下文管理器
class EnhancedApplicationContext:
    """增强应用上下文管理器
    
    提供应用生命周期的上下文管理。
    """
    
    def __init__(self, config: Optional[BootstrapConfig] = None, custom_config: Optional[Dict[str, Any]] = None):
        """初始化应用上下文
        
        Args:
            config: 启动器配置
            custom_config: 自定义配置
        """
        self.config = config
        self.custom_config = custom_config
        self.bootstrap: Optional[EnhancedApplicationBootstrap] = None
    
    async def __aenter__(self) -> DIContainer:
        """异步进入上下文
        
        Returns:
            DIContainer: 依赖注入容器
        """
        self.bootstrap = EnhancedApplicationBootstrap(self.config)
        return await self.bootstrap.bootstrap(self.custom_config)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步退出上下文
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常跟踪
        """
        if self.bootstrap:
            await self.bootstrap.shutdown()


# 便捷函数
async def create_enhanced_application(config: Optional[BootstrapConfig] = None,
                                   custom_config: Optional[Dict[str, Any]] = None) -> DIContainer:
    """创建增强应用
    
    Args:
        config: 启动器配置
        custom_config: 自定义配置
        
    Returns:
        DIContainer: 依赖注入容器
    """
    bootstrap = EnhancedApplicationBootstrap(config)
    return await bootstrap.bootstrap(custom_config)


async def run_enhanced_application(config: Optional[BootstrapConfig] = None,
                                  custom_config: Optional[Dict[str, Any]] = None) -> None:
    """运行增强应用
    
    Args:
        config: 启动器配置
        custom_config: 自定义配置
    """
    async with EnhancedApplicationContext(config, custom_config) as container:
        # 获取日志记录器
        logger = container.resolve(Logger)
        
        try:
            # 这里可以添加主应用逻辑
            logger.info("应用运行中...")
            
            # 保持应用运行
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"应用运行出错: {str(e)}")
            raise
