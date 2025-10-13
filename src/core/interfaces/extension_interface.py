"""
扩展接口模块

该模块定义了扩展系统的核心接口，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime


class ExtensionStatus(Enum):
    """扩展状态枚举
    
    定义扩展的生命周期状态。
    """
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    INACTIVE = "inactive"
    ERROR = "error"


class ExtensionType(Enum):
    """扩展类型枚举
    
    定义扩展的类型分类。
    """
    SYSTEM = "system"
    API = "api"
    MIDDLEWARE = "middleware"
    SERVICE = "service"
    UI = "ui"
    INTEGRATION = "integration"
    UTILITY = "utility"


@dataclass
class ExtensionMetadata:
    """扩展元数据
    
    封装扩展的基本信息，遵循单一职责原则。
    """
    
    name: str
    version: str
    description: str
    author: str
    extension_type: ExtensionType
    dependencies: List[str] = None
    optional_dependencies: List[str] = None
    min_system_version: str = "1.0.0"
    max_system_version: str = None
    tags: List[str] = None
    homepage: str = None
    license: str = None
    entry_point: str = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.dependencies is None:
            self.dependencies = []
        if self.optional_dependencies is None:
            self.optional_dependencies = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 元数据的字典表示
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "extension_type": self.extension_type.value,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "min_system_version": self.min_system_version,
            "max_system_version": self.max_system_version,
            "tags": self.tags,
            "homepage": self.homepage,
            "license": self.license,
            "entry_point": self.entry_point
        }


@dataclass
class ExtensionContext:
    """扩展上下文
    
    提供扩展运行时的上下文信息，遵循单一职责原则。
    """
    
    extension_id: str
    metadata: ExtensionMetadata
    config: Dict[str, Any]
    container: Any  # 依赖注入容器
    event_bus: Any  # 事件总线
    logger: Any     # 日志记录器
    data_dir: str   # 数据目录
    temp_dir: str   # 临时目录
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
    
    def has_config(self, key: str) -> bool:
        """检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        return key in self.config


class Extension(ABC):
    """扩展基类
    
    所有扩展的抽象基类，定义扩展的生命周期方法，
    遵循里氏替换原则(LSP)。
    """
    
    def __init__(self, metadata: ExtensionMetadata):
        """初始化扩展
        
        Args:
            metadata: 扩展元数据
        """
        self.metadata = metadata
        self.context: Optional[ExtensionContext] = None
        self.status = ExtensionStatus.UNLOADED
        self.error_message: Optional[str] = None
        self.load_time: Optional[datetime] = None
        self.activate_time: Optional[datetime] = None
    
    @abstractmethod
    async def initialize(self, context: ExtensionContext) -> None:
        """初始化扩展
        
        在扩展加载后调用，用于初始化扩展的资源和状态。
        
        Args:
            context: 扩展上下文
        """
        pass
    
    @abstractmethod
    async def activate(self) -> None:
        """激活扩展
        
        在扩展初始化后调用，用于启动扩展的功能。
        """
        pass
    
    @abstractmethod
    async def deactivate(self) -> None:
        """停用扩展
        
        在扩展卸载前调用，用于清理扩展的资源。
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理扩展
        
        在扩展卸载时调用，用于释放所有资源。
        """
        pass
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态
        
        返回扩展的健康状态信息。
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            "status": self.status.value,
            "error_message": self.error_message,
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "activate_time": self.activate_time.isoformat() if self.activate_time else None
        }
    
    def set_status(self, status: ExtensionStatus, error_message: Optional[str] = None) -> None:
        """设置扩展状态
        
        Args:
            status: 新状态
            error_message: 错误消息
        """
        self.status = status
        self.error_message = error_message
        
        if status == ExtensionStatus.LOADED:
            self.load_time = datetime.now()
        elif status == ExtensionStatus.ACTIVE:
            self.activate_time = datetime.now()


class ExtensionFactory(ABC):
    """扩展工厂接口
    
    定义扩展工厂的接口，用于创建扩展实例。
    """
    
    @abstractmethod
    def create_extension(self, metadata: ExtensionMetadata) -> Extension:
        """创建扩展实例
        
        Args:
            metadata: 扩展元数据
            
        Returns:
            Extension: 扩展实例
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[ExtensionType]:
        """获取支持的扩展类型
        
        Returns:
            List[ExtensionType]: 支持的扩展类型列表
        """
        pass


class ExtensionRegistry(ABC):
    """扩展注册表接口
    
    定义扩展注册表的接口，用于管理扩展的注册和发现。
    """
    
    @abstractmethod
    async def register_extension(self, extension: Extension) -> bool:
        """注册扩展
        
        Args:
            extension: 扩展实例
            
        Returns:
            bool: 是否成功注册
        """
        pass
    
    @abstractmethod
    async def unregister_extension(self, extension_id: str) -> bool:
        """注销扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功注销
        """
        pass
    
    @abstractmethod
    async def get_extension(self, extension_id: str) -> Optional[Extension]:
        """获取扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        pass
    
    @abstractmethod
    async def list_extensions(self, 
                             extension_type: Optional[ExtensionType] = None,
                             status: Optional[ExtensionStatus] = None) -> List[Extension]:
        """列出扩展
        
        Args:
            extension_type: 扩展类型过滤
            status: 状态过滤
            
        Returns:
            List[Extension]: 扩展列表
        """
        pass
    
    @abstractmethod
    async def find_extensions_by_tag(self, tag: str) -> List[Extension]:
        """根据标签查找扩展
        
        Args:
            tag: 标签
            
        Returns:
            List[Extension]: 扩展列表
        """
        pass


class ExtensionManager(ABC):
    """扩展管理器接口
    
    定义扩展管理器的接口，用于管理扩展的生命周期。
    """
    
    @abstractmethod
    async def load_extension(self, extension_path: str) -> Optional[Extension]:
        """加载扩展
        
        Args:
            extension_path: 扩展路径
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        pass
    
    @abstractmethod
    async def unload_extension(self, extension_id: str) -> bool:
        """卸载扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功卸载
        """
        pass
    
    @abstractmethod
    async def activate_extension(self, extension_id: str) -> bool:
        """激活扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功激活
        """
        pass
    
    @abstractmethod
    async def deactivate_extension(self, extension_id: str) -> bool:
        """停用扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功停用
        """
        pass
    
    @abstractmethod
    async def reload_extension(self, extension_id: str) -> bool:
        """重新加载扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功重新加载
        """
        pass
    
    @abstractmethod
    async def get_extension_dependencies(self, extension_id: str) -> List[str]:
        """获取扩展依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 依赖列表
        """
        pass
    
    @abstractmethod
    async def resolve_dependencies(self, extension_id: str) -> List[str]:
        """解析扩展依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 解析后的依赖顺序
        """
        pass


class ExtensionLoader(ABC):
    """扩展加载器接口
    
    定义扩展加载器的接口，用于从不同来源加载扩展。
    """
    
    @abstractmethod
    async def load_metadata(self, extension_path: str) -> Optional[ExtensionMetadata]:
        """加载扩展元数据
        
        Args:
            extension_path: 扩展路径
            
        Returns:
            Optional[ExtensionMetadata]: 扩展元数据
        """
        pass
    
    @abstractmethod
    async def load_extension(self, 
                           metadata: ExtensionMetadata, 
                           extension_path: str) -> Optional[Extension]:
        """加载扩展
        
        Args:
            metadata: 扩展元数据
            extension_path: 扩展路径
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """获取支持的扩展格式
        
        Returns:
            List[str]: 支持的扩展格式列表
        """
        pass


class ExtensionEvent(ABC):
    """扩展事件基类
    
    所有扩展事件的抽象基类。
    """
    
    def __init__(self, extension_id: str):
        """初始化扩展事件
        
        Args:
            extension_id: 扩展ID
        """
        self.extension_id = extension_id
        self.timestamp = datetime.now()
        self.event_id = str(uuid.uuid4())
    
    @abstractmethod
    def get_event_type(self) -> str:
        """获取事件类型
        
        Returns:
            str: 事件类型
        """
        pass


class ExtensionEventHandler(ABC):
    """扩展事件处理器接口
    
    定义扩展事件处理器的接口。
    """
    
    @abstractmethod
    async def handle_event(self, event: ExtensionEvent) -> None:
        """处理扩展事件
        
        Args:
            event: 扩展事件
        """
        pass