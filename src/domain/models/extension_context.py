"""
扩展上下文模型模块

该模块实现扩展上下文的数据模型，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责扩展运行时上下文的管理。
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from ...core.interfaces import ExtensionContext as BaseExtensionContext


@dataclass
class ExtensionConfig:
    """扩展配置
    
    封装扩展的配置信息，遵循单一职责原则。
    """
    
    config_data: Dict[str, Any] = field(default_factory=dict)
    config_file: Optional[str] = None
    auto_save: bool = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data
        
        # 导航到父级字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 自动保存
        if self.auto_save and self.config_file:
            self.save()
    
    def has(self, key: str) -> bool:
        """检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None
    
    def remove(self, key: str) -> bool:
        """移除配置
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否成功移除
        """
        keys = key.split('.')
        config = self.config_data
        
        # 导航到父级字典
        for k in keys[:-1]:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False
        
        # 移除键
        if keys[-1] in config:
            del config[keys[-1]]
            
            # 自动保存
            if self.auto_save and self.config_file:
                self.save()
            
            return True
        
        return False
    
    def update(self, data: Dict[str, Any]) -> None:
        """批量更新配置
        
        Args:
            data: 配置数据
        """
        self.config_data.update(data)
        
        # 自动保存
        if self.auto_save and self.config_file:
            self.save()
    
    def clear(self) -> None:
        """清空配置"""
        self.config_data.clear()
        
        # 自动保存
        if self.auto_save and self.config_file:
            self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.config_data.copy()
    
    def load_from_file(self, file_path: str) -> None:
        """从文件加载配置
        
        Args:
            file_path: 配置文件路径
        """
        if not os.path.exists(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.json'):
                data = json.load(f)
            elif file_path.endswith(('.yaml', '.yml')):
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {file_path}")
        
        self.config_data = data
        self.config_file = file_path
    
    def save(self) -> None:
        """保存配置到文件"""
        if not self.config_file:
            return
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            if self.config_file.endswith('.json'):
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
            elif self.config_file.endswith(('.yaml', '.yml')):
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"不支持的配置文件格式: {self.config_file}")


@dataclass
class ExtensionResources:
    """扩展资源管理
    
    管理扩展使用的各种资源，遵循单一职责原则。
    """
    
    data_dir: str
    temp_dir: str
    cache_dir: Optional[str] = None
    log_dir: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
    
    def get_data_file(self, filename: str) -> str:
        """获取数据文件路径
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        return os.path.join(self.data_dir, filename)
    
    def get_temp_file(self, filename: str) -> str:
        """获取临时文件路径
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        return os.path.join(self.temp_dir, filename)
    
    def get_cache_file(self, filename: str) -> str:
        """获取缓存文件路径
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        if not self.cache_dir:
            raise ValueError("缓存目录未设置")
        
        return os.path.join(self.cache_dir, filename)
    
    def get_log_file(self, filename: str) -> str:
        """获取日志文件路径
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件路径
        """
        if not self.log_dir:
            raise ValueError("日志目录未设置")
        
        return os.path.join(self.log_dir, filename)
    
    def cleanup_temp_files(self) -> None:
        """清理临时文件"""
        temp_path = Path(self.temp_dir)
        for file_path in temp_path.glob("*"):
            try:
                if file_path.is_file():
                    file_path.unlink()
                elif file_path.is_dir():
                    # 递归删除目录
                    for item in file_path.glob("*"):
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            item.rmdir()
                    file_path.rmdir()
            except Exception:
                # 忽略清理错误
                pass
    
    def get_disk_usage(self) -> Dict[str, int]:
        """获取磁盘使用情况
        
        Returns:
            Dict[str, int]: 各目录的磁盘使用情况（字节）
        """
        def get_dir_size(path: str) -> int:
            total = 0
            try:
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total += os.path.getsize(filepath)
            except Exception:
                pass
            return total
        
        usage = {
            "data_dir": get_dir_size(self.data_dir),
            "temp_dir": get_dir_size(self.temp_dir)
        }
        
        if self.cache_dir:
            usage["cache_dir"] = get_dir_size(self.cache_dir)
        
        if self.log_dir:
            usage["log_dir"] = get_dir_size(self.log_dir)
        
        usage["total"] = sum(usage.values())
        
        return usage


@dataclass
class ExtensionEventBus:
    """扩展事件总线
    
    为扩展提供事件发布和订阅功能，遵循单一职责原则。
    """
    
    event_handlers: Dict[str, List[Callable]] = field(default_factory=dict)
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            
        Returns:
            bool: 是否成功取消订阅
        """
        if event_type not in self.event_handlers:
            return False
        
        try:
            self.event_handlers[event_type].remove(handler)
            return True
        except ValueError:
            return False
    
    async def publish(self, event_type: str, data: Any = None) -> None:
        """发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        if event_type not in self.event_handlers:
            return
        
        for handler in self.event_handlers[event_type]:
            try:
                if hasattr(handler, '__call__'):
                    # 检查是否是异步函数
                    import asyncio
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event_type, data)
                    else:
                        handler(event_type, data)
            except Exception:
                # 忽略处理器错误，继续执行其他处理器
                pass
    
    def get_subscribed_events(self) -> List[str]:
        """获取已订阅的事件类型
        
        Returns:
            List[str]: 事件类型列表
        """
        return list(self.event_handlers.keys())
    
    def get_handler_count(self, event_type: str) -> int:
        """获取事件类型的处理器数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 处理器数量
        """
        return len(self.event_handlers.get(event_type, []))


class ExtensionContextImpl(BaseExtensionContext):
    """扩展上下文实现
    
    实现扩展上下文接口，为扩展提供完整的运行时环境。
    """
    
    def __init__(self, 
                 extension_id: str,
                 metadata: Any,
                 config: Dict[str, Any],
                 container: Any,
                 event_bus: Any,
                 logger: Any,
                 data_dir: str,
                 temp_dir: str):
        """初始化扩展上下文
        
        Args:
            extension_id: 扩展ID
            metadata: 扩展元数据
            config: 配置数据
            container: 依赖注入容器
            event_bus: 事件总线
            logger: 日志记录器
            data_dir: 数据目录
            temp_dir: 临时目录
        """
        super().__init__(
            extension_id=extension_id,
            metadata=metadata,
            config=config,
            container=container,
            event_bus=event_bus,
            logger=logger,
            data_dir=data_dir,
            temp_dir=temp_dir
        )
        
        # 扩展配置管理
        config_file = os.path.join(data_dir, "config.json")
        self.extension_config = ExtensionConfig(
            config_data=config.copy(),
            config_file=config_file,
            auto_save=True
        )
        
        # 资源管理
        cache_dir = os.path.join(data_dir, "cache")
        log_dir = os.path.join(data_dir, "logs")
        self.resources = ExtensionResources(
            data_dir=data_dir,
            temp_dir=temp_dir,
            cache_dir=cache_dir,
            log_dir=log_dir
        )
        
        # 扩展事件总线
        self.extension_event_bus = ExtensionEventBus()
        
        # 上下文元数据
        self.context_metadata = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 0
        }
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        self._update_access_time()
        return self.extension_config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self._update_access_time()
        self.extension_config.set(key, value)
        # 同时更新基类的配置
        self.config[key] = value
    
    def has_config(self, key: str) -> bool:
        """检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        self._update_access_time()
        return self.extension_config.has(key)
    
    def get_resources(self) -> ExtensionResources:
        """获取资源管理器
        
        Returns:
            ExtensionResources: 资源管理器
        """
        self._update_access_time()
        return self.resources
    
    def get_extension_event_bus(self) -> ExtensionEventBus:
        """获取扩展事件总线
        
        Returns:
            ExtensionEventBus: 扩展事件总线
        """
        self._update_access_time()
        return self.extension_event_bus
    
    def get_context_metadata(self) -> Dict[str, Any]:
        """获取上下文元数据
        
        Returns:
            Dict[str, Any]: 上下文元数据
        """
        self._update_access_time()
        metadata = self.context_metadata.copy()
        metadata["created_at"] = metadata["created_at"].isoformat()
        metadata["last_accessed"] = metadata["last_accessed"].isoformat()
        return metadata
    
    def save_config(self) -> None:
        """保存配置"""
        self.extension_config.save()
    
    def reload_config(self) -> None:
        """重新加载配置"""
        if self.extension_config.config_file:
            self.extension_config.load_from_file(self.extension_config.config_file)
            self.config = self.extension_config.to_dict()
    
    def cleanup(self) -> None:
        """清理上下文资源"""
        # 清理临时文件
        self.resources.cleanup_temp_files()
        
        # 清理事件处理器
        self.extension_event_bus.event_handlers.clear()
    
    def _update_access_time(self) -> None:
        """更新访问时间"""
        self.context_metadata["last_accessed"] = datetime.now()
        self.context_metadata["access_count"] += 1