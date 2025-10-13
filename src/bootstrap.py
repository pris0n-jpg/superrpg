"""
应用启动器模块

该模块实现应用启动器，负责依赖注入容器的初始化和服务注册。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

应用启动器负责：
1. 初始化依赖注入容器
2. 注册所有服务和适配器
3. 配置应用生命周期
4. 提供应用启动入口点
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path

# 导入核心容器和接口
try:
    from .core.container import DIContainer, ServiceLocator
    from .core.interfaces import EventBus, Logger
    from .application.container_config import (
        configure_application_container,
        create_application_container,
        get_default_application_config,
        validate_container_configuration
    )
    from .adapters import AgentsAdapter, ToolsAdapter, WorldAdapter
    from .settings.loader import (
        project_root,
        load_prompts,
        load_model_config,
        load_feature_flags,
        load_story_config,
        load_characters
    )
except ImportError:
    # 回退到绝对导入（直接运行脚本时）
    import sys
    from pathlib import Path
    
    # 添加项目根目录到 Python 路径
    project_root_path = Path(__file__).parent.parent
    if str(project_root_path) not in sys.path:
        sys.path.insert(0, str(project_root_path))
    
    from src.core.container import DIContainer, ServiceLocator
    from src.core.interfaces import EventBus, Logger
    from src.application.container_config import (
        configure_application_container,
        create_application_container,
        get_default_application_config,
        validate_container_configuration
    )
    from src.adapters import AgentsAdapter, ToolsAdapter, WorldAdapter
    try:
        from src.settings.loader import (
            project_root,
            load_prompts,
            load_model_config,
            load_feature_flags,
            load_story_config,
            load_characters
        )
    except ImportError:
        # 如果新架构配置加载器不存在，提供基本实现
        def project_root():
            return Path(__file__).parent.parent
        
        def load_prompts():
            return {}
        
        def load_model_config():
            return {}
        
        def load_feature_flags():
            return {}
        
        def load_story_config():
            return {}
        
        def load_characters():
            return {}


class ApplicationBootstrap:
    """应用启动器类
    
    该类负责应用的完整启动流程，包括容器初始化、
    服务注册、适配器配置等。
    """
    
    def __init__(self, enable_legacy_mode: bool = True):
        """初始化应用启动器
        
        Args:
            enable_legacy_mode: 是否启用遗留模式支持
        """
        self.enable_legacy_mode = enable_legacy_mode
        self.container: Optional[DIContainer] = None
        self.logger = logging.getLogger(__name__)
        
        # 配置加载标志
        self._config_loaded = False
        self._container_initialized = False
        self._adapters_initialized = False
        
        # 加载的配置
        self._prompts: Dict[str, Any] = {}
        self._model_config: Dict[str, Any] = {}
        self._feature_flags: Dict[str, Any] = {}
        self._story_config: Dict[str, Any] = {}
        self._characters: Dict[str, Any] = {}
    
    def load_configurations(self) -> None:
        """加载所有配置文件
        
        该方法加载应用所需的所有配置文件，
        包括提示、模型配置、功能标志等。
        """
        try:
            self.logger.debug("开始加载应用配置...")
            
            # 设置httpx日志级别为WARNING，避免HTTP请求日志
            logging.getLogger('httpx').setLevel(logging.WARNING)
            
            # 加载各种配置
            self._prompts = load_prompts()
            self._model_config = load_model_config()
            self._feature_flags = load_feature_flags()
            self._story_config = load_story_config()
            self._characters = load_characters()
            
            self._config_loaded = True
            self.logger.debug("应用配置加载完成")
            
        except Exception as e:
            error_msg = f"配置加载失败: {str(e)}"
            self.logger.error(error_msg)
            if self.enable_legacy_mode:
                # 在遗留模式下使用默认配置
                self._load_default_configurations()
                self.logger.warning("使用默认配置继续启动")
            else:
                raise RuntimeError(error_msg) from e
    
    def initialize_container(self, custom_config: Dict[str, Any] = None) -> DIContainer:
        """初始化依赖注入容器
        
        Args:
            custom_config: 自定义配置
            
        Returns:
            DIContainer: 初始化的容器
            
        Raises:
            RuntimeError: 当容器初始化失败时
        """
        try:
            self.logger.debug("开始初始化依赖注入容器...")
            
            # 确保配置已加载
            if not self._config_loaded:
                self.load_configurations()
            
            # 创建容器
            self.container = create_application_container(
                custom_config=custom_config or get_default_application_config()
            )
            
            # 设置服务定位器
            ServiceLocator.set_container(self.container)
            
            # 验证容器配置
            validation_errors = validate_container_configuration(self.container)
            if validation_errors:
                error_msg = f"容器配置验证失败: {'; '.join(validation_errors)}"
                self.logger.error(error_msg)
                if not self.enable_legacy_mode:
                    raise RuntimeError(error_msg)
            
            self._container_initialized = True
            self.logger.debug("依赖注入容器初始化完成")
            
            return self.container
            
        except Exception as e:
            error_msg = f"容器初始化失败: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def initialize_adapters(self) -> None:
        """初始化适配器
        
        该方法初始化所有适配器，并将它们注册到容器中。
        """
        try:
            self.logger.debug("开始初始化适配器...")
            
            if not self._container_initialized:
                raise RuntimeError("容器未初始化，请先调用initialize_container")
            
            # 初始化世界适配器
            world_adapter = WorldAdapter(enable_legacy_mode=self.enable_legacy_mode)
            self.container.register_instance(WorldAdapter, world_adapter)
            
            # 初始化工具适配器
            tools_adapter = ToolsAdapter(enable_legacy_mode=self.enable_legacy_mode)
            tools_adapter.initialize_tools(world_adapter)
            self.container.register_instance(ToolsAdapter, tools_adapter)
            
            # 初始化代理适配器
            agents_adapter = AgentsAdapter(enable_legacy_mode=self.enable_legacy_mode)
            self.container.register_instance(AgentsAdapter, agents_adapter)
            
            self._adapters_initialized = True
            self.logger.debug("适配器初始化完成")
            
        except Exception as e:
            error_msg = f"适配器初始化失败: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def bootstrap_application(self, custom_config: Dict[str, Any] = None) -> DIContainer:
        """启动应用程序
        
        该方法执行完整的启动流程，包括配置加载、
        容器初始化、适配器配置等。
        
        Args:
            custom_config: 自定义配置
            
        Returns:
            DIContainer: 初始化的容器
            
        Raises:
            RuntimeError: 当启动失败时
        """
        try:
            self.logger.debug("开始启动应用程序...")
            
            # 1. 加载配置
            self.load_configurations()
            
            # 2. 初始化容器
            self.initialize_container(custom_config)
            
            # 3. 初始化适配器
            self.initialize_adapters()
            
            self.logger.info("应用程序启动完成")
            
            return self.container
            
        except Exception as e:
            error_msg = f"应用程序启动失败: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_container(self) -> DIContainer:
        """获取依赖注入容器
        
        Returns:
            DIContainer: 依赖注入容器
            
        Raises:
            RuntimeError: 当容器未初始化时
        """
        if not self._container_initialized:
            raise RuntimeError("容器未初始化，请先调用bootstrap_application")
        
        return self.container
    
    def get_configuration(self) -> Dict[str, Any]:
        """获取应用配置
        
        Returns:
            Dict[str, Any]: 应用配置
        """
        if not self._config_loaded:
            self.load_configurations()
        
        return {
            "prompts": self._prompts,
            "model_config": self._model_config,
            "feature_flags": self._feature_flags,
            "story_config": self._story_config,
            "characters": self._characters
        }
    
    def shutdown(self) -> None:
        """关闭应用程序
        
        该方法执行清理操作，包括容器清理、
        适配器清理等。
        """
        try:
            self.logger.debug("开始关闭应用程序...")
            
            # 清理适配器
            if self._adapters_initialized and self.container:
                try:
                    tools_adapter = self.container.resolve(ToolsAdapter)
                    tools_adapter.clear_cache()
                except Exception:
                    pass
                
                try:
                    agents_adapter = self.container.resolve(AgentsAdapter)
                    agents_adapter.clear_cache()
                except Exception:
                    pass
            
            # 清理容器
            if self.container:
                self.container.clear_scope()
            
            # 重置服务定位器
            ServiceLocator._container = None
            
            # 重置状态
            self._container_initialized = False
            self._adapters_initialized = False
            
            self.logger.debug("应用程序关闭完成")
            
        except Exception as e:
            self.logger.error(f"应用程序关闭时出错: {str(e)}")
    
    def _load_default_configurations(self) -> None:
        """加载默认配置
        
        在遗留模式下，当配置加载失败时使用默认配置。
        """
        self._prompts = {
            "player_persona": "你是游戏的参与者，需要根据当前情境做出合理的决策。",
            "npc_prompt_template": (
                "你是游戏中的NPC：{name}。\n"
                "人设：{persona}\n"
                "当前立场提示：{relation_brief}\n"
                "参与者：{allowed_names}\n"
            )
        }
        
        self._model_config = {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "npc": {
                "model": "gpt-3.5-turbo",
                "stream": True,
                "temperature": 0.7
            }
        }
        
        self._feature_flags = {
            "max_rounds": 50,
            "require_hostiles": True,
            "debug_mode": False,
            "pre_turn_recap": True,
            "recap_msg_limit": 6,
            "recap_action_limit": 6
        }
        
        self._story_config = {
            "scene": {
                "name": "旧城区·北侧仓棚",
                "description": "铁梁回声震耳，每名战斗者都盯紧了自己的对手——退路已绝，只能分出胜负！",
                "time": "08:00",
                "weather": "晴朗"
            }
        }
        
        self._characters = {}


# 创建默认的应用启动器实例
default_bootstrap = ApplicationBootstrap()


def bootstrap_application(
    enable_legacy_mode: bool = True,
    custom_config: Dict[str, Any] = None
) -> DIContainer:
    """启动应用程序的便捷函数
    
    Args:
        enable_legacy_mode: 是否启用遗留模式支持
        custom_config: 自定义配置
        
    Returns:
        DIContainer: 初始化的容器
    """
    global default_bootstrap
    
    # 重新创建启动器实例
    default_bootstrap = ApplicationBootstrap(enable_legacy_mode=enable_legacy_mode)
    
    return default_bootstrap.bootstrap_application(custom_config)


def get_application_container() -> DIContainer:
    """获取应用程序容器
    
    Returns:
        DIContainer: 应用程序容器
        
    Raises:
        RuntimeError: 当应用程序未启动时
    """
    return default_bootstrap.get_container()


def shutdown_application() -> None:
    """关闭应用程序"""
    default_bootstrap.shutdown()


def get_application_config() -> Dict[str, Any]:
    """获取应用程序配置
    
    Returns:
        Dict[str, Any]: 应用程序配置
    """
    return default_bootstrap.get_configuration()


# 应用程序上下文管理器
class ApplicationContext:
    """应用程序上下文管理器
    
    该类提供了上下文管理器接口，用于自动管理
    应用程序的启动和关闭。
    """
    
    def __init__(self, enable_legacy_mode: bool = True, custom_config: Dict[str, Any] = None):
        """初始化应用程序上下文
        
        Args:
            enable_legacy_mode: 是否启用遗留模式支持
            custom_config: 自定义配置
        """
        self.enable_legacy_mode = enable_legacy_mode
        self.custom_config = custom_config
        self.bootstrap: Optional[ApplicationBootstrap] = None
    
    def __enter__(self) -> DIContainer:
        """进入上下文
        
        Returns:
            DIContainer: 初始化的容器
        """
        self.bootstrap = ApplicationBootstrap(self.enable_legacy_mode)
        return self.bootstrap.bootstrap_application(self.custom_config)
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常跟踪
        """
        if self.bootstrap:
            self.bootstrap.shutdown()