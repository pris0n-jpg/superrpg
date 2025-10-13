"""
增强配置管理器模块

该模块实现增强的配置管理器，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责配置的动态更新、验证和类型检查。
"""

import os
import json
import yaml
import asyncio
import threading
import time
from typing import Dict, Any, List, Optional, Type, Callable, Union, Set
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import watchdog.observers
import watchdog.events
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ...core.interfaces import ConfigLoader
from ...core.exceptions import ConfigurationException, ValidationException


class ConfigFormat(Enum):
    """配置格式枚举
    
    定义支持的配置文件格式。
    """
    JSON = "json"
    YAML = "yaml"
    YML = "yml"
    TOML = "toml"
    INI = "ini"


class ConfigChangeType(Enum):
    """配置变更类型枚举
    
    定义配置变更的类型。
    """
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RELOADED = "reloaded"


@dataclass
class ConfigSchema:
    """配置模式
    
    定义配置的结构和验证规则，遵循单一职责原则。
    """
    
    key: str
    type: Type
    required: bool = True
    default: Any = None
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    example: Any = None
    
    def validate(self, value: Any) -> bool:
        """验证配置值
        
        Args:
            value: 配置值
            
        Returns:
            bool: 是否有效
        """
        # 类型检查
        if not isinstance(value, self.type):
            # 允许None类型的可选字段
            if value is None and not self.required:
                return True
            return False
        
        # 自定义验证器
        if self.validator:
            try:
                return self.validator(value)
            except Exception:
                return False
        
        return True


@dataclass
class ConfigChangeEvent:
    """配置变更事件
    
    封装配置变更的信息，遵循单一职责原则。
    """
    
    key: str
    old_value: Any
    new_value: Any
    change_type: ConfigChangeType
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "config_manager"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 事件的字典表示
        """
        return {
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_type": self.change_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件处理器
    
    监听配置文件变更，遵循单一职责原则。
    """
    
    def __init__(self, config_manager: 'EnhancedConfigManager'):
        """初始化配置文件处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
    
    def on_modified(self, event):
        """文件修改事件处理
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            file_path = event.src_path
            if file_path in self.config_manager._watched_files:
                # 延迟处理，避免文件写入未完成
                threading.Timer(1.0, self.config_manager._reload_file, args=[file_path]).start()


class ConfigValidator:
    """配置验证器
    
    提供配置验证功能，遵循单一职责原则。
    """
    
    def __init__(self):
        """初始化配置验证器"""
        self.schemas: Dict[str, ConfigSchema] = {}
        self.group_schemas: Dict[str, List[ConfigSchema]] = {}
    
    def add_schema(self, schema: ConfigSchema) -> None:
        """添加配置模式
        
        Args:
            schema: 配置模式
        """
        self.schemas[schema.key] = schema
    
    def add_group_schema(self, group: str, schemas: List[ConfigSchema]) -> None:
        """添加配置组模式
        
        Args:
            group: 组名
            schemas: 配置模式列表
        """
        self.group_schemas[group] = schemas
        for schema in schemas:
            self.schemas[schema.key] = schema
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        for key, schema in self.schemas.items():
            if key in config:
                if not schema.validate(config[key]):
                    errors.append(f"配置项 '{key}' 验证失败: 值 '{config[key]}' 不符合要求")
            elif schema.required and schema.default is None:
                errors.append(f"缺少必需的配置项: '{key}'")
        
        return errors
    
    def validate_key(self, key: str, value: Any) -> bool:
        """验证单个配置项
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 是否有效
        """
        if key not in self.schemas:
            return True
        
        return self.schemas[key].validate(value)
    
    def get_default_values(self) -> Dict[str, Any]:
        """获取默认值
        
        Returns:
            Dict[str, Any]: 默认值字典
        """
        defaults = {}
        for key, schema in self.schemas.items():
            if schema.default is not None:
                defaults[key] = schema.default
        return defaults


class EnhancedConfigManager(ConfigLoader):
    """增强配置管理器
    
    提供完整的配置管理功能，包括动态更新、验证和类型检查。
    """
    
    def __init__(self, 
                 config_dir: str = "configs",
                 auto_reload: bool = True,
                 enable_validation: bool = True,
                 enable_change_notifications: bool = True):
        """初始化增强配置管理器
        
        Args:
            config_dir: 配置目录
            auto_reload: 是否自动重载
            enable_validation: 是否启用验证
            enable_change_notifications: 是否启用变更通知
        """
        self.config_dir = config_dir
        self.auto_reload = auto_reload
        self.enable_validation = enable_validation
        self.enable_change_notifications = enable_change_notifications
        
        # 配置数据
        self._config: Dict[str, Any] = {}
        self._config_files: Dict[str, str] = {}  # 文件路径到配置键的映射
        self._watched_files: Set[str] = set()
        
        # 验证器
        self._validator = ConfigValidator() if enable_validation else None
        
        # 变更通知
        self._change_listeners: List[Callable[[ConfigChangeEvent], None]] = []
        
        # 文件监听
        self._observer: Optional[Observer] = None
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            "load_count": 0,
            "reload_count": 0,
            "validation_errors": 0,
            "change_notifications": 0,
            "last_reload_time": None
        }
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        with self._lock:
            try:
                # 确定文件格式
                file_format = self._detect_format(config_path)
                
                # 读取文件内容
                with open(config_path, 'r', encoding='utf-8') as f:
                    if file_format == ConfigFormat.JSON:
                        data = json.load(f)
                    elif file_format in (ConfigFormat.YAML, ConfigFormat.YML):
                        data = yaml.safe_load(f)
                    else:
                        raise ConfigurationException(
                            f"不支持的配置文件格式: {file_format.value}",
                            config_path
                        )
                
                # 验证配置
                if self._validator:
                    errors = self._validator.validate_config(data)
                    if errors:
                        self._stats["validation_errors"] += len(errors)
                        raise ValidationException(
                            f"配置验证失败: {'; '.join(errors)}",
                            validation_errors=errors
                        )
                
                # 合并配置
                old_config = self._config.copy()
                self._merge_config(data)
                
                # 记录文件
                self._config_files[config_path] = list(data.keys())
                
                # 发送变更通知
                if self.enable_change_notifications:
                    self._notify_changes(old_config, self._config, ConfigChangeType.RELOADED)
                
                # 启用文件监听
                if self.auto_reload and config_path not in self._watched_files:
                    self._watch_file(config_path)
                
                self._stats["load_count"] += 1
                
                return self._config.copy()
                
            except Exception as e:
                raise ConfigurationException(
                    f"加载配置失败: {str(e)}",
                    config_path
                )
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 验证是否通过
        """
        if not self._validator:
            return True
        
        errors = self._validator.validate_config(config)
        if errors:
            self._stats["validation_errors"] += len(errors)
            return False
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        with self._lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any, persist: bool = True) -> None:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
            persist: 是否持久化到文件
        """
        with self._lock:
            # 验证配置
            if self._validator and not self._validator.validate_key(key, value):
                raise ValidationException(f"配置值验证失败: {key} = {value}")
            
            # 获取旧值
            old_value = self.get(key)
            
            # 设置新值
            keys = key.split('.')
            config = self._config
            
            # 导航到父级字典
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            
            # 发送变更通知
            if self.enable_change_notifications:
                change_type = ConfigChangeType.MODIFIED if old_value is not None else ConfigChangeType.ADDED
                self._notify_change(ConfigChangeEvent(
                    key=key,
                    old_value=old_value,
                    new_value=value,
                    change_type=change_type
                ))
            
            # 持久化
            if persist:
                self._persist_config()
    
    def has(self, key: str) -> bool:
        """检查配置是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None
    
    def delete(self, key: str, persist: bool = True) -> bool:
        """删除配置项
        
        Args:
            key: 配置键
            persist: 是否持久化到文件
            
        Returns:
            bool: 是否成功删除
        """
        with self._lock:
            # 获取旧值
            old_value = self.get(key)
            if old_value is None:
                return False
            
            # 删除配置
            keys = key.split('.')
            config = self._config
            
            # 导航到父级字典
            for k in keys[:-1]:
                if isinstance(config, dict) and k in config:
                    config = config[k]
                else:
                    return False
            
            # 删除键
            if keys[-1] in config:
                del config[keys[-1]]
                
                # 发送变更通知
                if self.enable_change_notifications:
                    self._notify_change(ConfigChangeEvent(
                        key=key,
                        old_value=old_value,
                        new_value=None,
                        change_type=ConfigChangeType.DELETED
                    ))
                
                # 持久化
                if persist:
                    self._persist_config()
                
                return True
            
            return False
    
    def add_schema(self, schema: ConfigSchema) -> None:
        """添加配置模式
        
        Args:
            schema: 配置模式
        """
        if self._validator:
            self._validator.add_schema(schema)
    
    def add_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> None:
        """添加变更监听器
        
        Args:
            listener: 监听器函数
        """
        self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[ConfigChangeEvent], None]) -> bool:
        """移除变更监听器
        
        Args:
            listener: 监听器函数
            
        Returns:
            bool: 是否成功移除
        """
        try:
            self._change_listeners.remove(listener)
            return True
        except ValueError:
            return False
    
    def reload_all(self) -> None:
        """重新加载所有配置文件"""
        with self._lock:
            for config_path in list(self._config_files.keys()):
                try:
                    self._reload_file(config_path)
                except Exception as e:
                    print(f"重新加载配置文件失败 {config_path}: {e}")
            
            self._stats["reload_count"] += 1
            self._stats["last_reload_time"] = datetime.now()
    
    def get_config_snapshot(self) -> Dict[str, Any]:
        """获取配置快照
        
        Returns:
            Dict[str, Any]: 配置快照
        """
        with self._lock:
            return {
                "config": self._config.copy(),
                "config_files": self._config_files.copy(),
                "stats": self._stats.copy(),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        stats["config_keys_count"] = len(self._flatten_config(self._config))
        stats["watched_files_count"] = len(self._watched_files)
        stats["change_listeners_count"] = len(self._change_listeners)
        return stats
    
    def _detect_format(self, file_path: str) -> ConfigFormat:
        """检测文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            ConfigFormat: 文件格式
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        try:
            return ConfigFormat(ext)
        except ValueError:
            raise ConfigurationException(f"无法识别的配置文件格式: {ext}", file_path)
    
    def _merge_config(self, new_config: Dict[str, Any]) -> None:
        """合并配置
        
        Args:
            new_config: 新配置
        """
        def merge_dict(target: Dict[str, Any], source: Dict[str, Any]) -> None:
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value
        
        merge_dict(self._config, new_config)
    
    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """扁平化配置
        
        Args:
            config: 配置字典
            prefix: 前缀
            
        Returns:
            Dict[str, Any]: 扁平化后的配置
        """
        result = {}
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_config(value, full_key))
            else:
                result[full_key] = value
        
        return result
    
    def _watch_file(self, file_path: str) -> None:
        """监听文件变更
        
        Args:
            file_path: 文件路径
        """
        if not self._observer:
            self._observer = Observer()
            self._observer.schedule(
                ConfigFileHandler(self),
                self.config_dir,
                recursive=True
            )
            self._observer.start()
        
        self._watched_files.add(file_path)
    
    def _reload_file(self, file_path: str) -> None:
        """重新加载文件
        
        Args:
            file_path: 文件路径
        """
        if file_path not in self._config_files:
            return
        
        # 获取旧配置
        old_config = self._config.copy()
        
        # 重新加载
        self.load(file_path)
        
        # 发送变更通知
        if self.enable_change_notifications:
            self._notify_changes(old_config, self._config, ConfigChangeType.MODIFIED)
    
    def _notify_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any], change_type: ConfigChangeType) -> None:
        """通知配置变更
        
        Args:
            old_config: 旧配置
            new_config: 新配置
            change_type: 变更类型
        """
        # 扁平化配置以便比较
        old_flat = self._flatten_config(old_config)
        new_flat = self._flatten_config(new_config)
        
        # 找出变更的键
        all_keys = set(old_flat.keys()) | set(new_flat.keys())
        
        for key in all_keys:
            old_value = old_flat.get(key)
            new_value = new_flat.get(key)
            
            if old_value != new_value:
                # 确定具体变更类型
                if old_value is None:
                    actual_change_type = ConfigChangeType.ADDED
                elif new_value is None:
                    actual_change_type = ConfigChangeType.DELETED
                else:
                    actual_change_type = ConfigChangeType.MODIFIED
                
                event = ConfigChangeEvent(
                    key=key,
                    old_value=old_value,
                    new_value=new_value,
                    change_type=actual_change_type
                )
                
                self._notify_change(event)
    
    def _notify_change(self, event: ConfigChangeEvent) -> None:
        """通知单个变更
        
        Args:
            event: 变更事件
        """
        self._stats["change_notifications"] += 1
        
        for listener in self._change_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"配置变更监听器错误: {e}")
    
    def _persist_config(self) -> None:
        """持久化配置到文件"""
        # 找到主配置文件
        main_config_file = os.path.join(self.config_dir, "config.json")
        
        if not os.path.exists(main_config_file):
            main_config_file = os.path.join(self.config_dir, "config.yaml")
        
        if not os.path.exists(main_config_file):
            # 创建默认配置文件
            main_config_file = os.path.join(self.config_dir, "config.json")
        
        try:
            file_format = self._detect_format(main_config_file)
            
            with open(main_config_file, 'w', encoding='utf-8') as f:
                if file_format == ConfigFormat.JSON:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
                else:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
                    
        except Exception as e:
            raise ConfigurationException(f"持久化配置失败: {str(e)}", main_config_file)
    
    def shutdown(self) -> None:
        """关闭配置管理器"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        
        with self._lock:
            self._config.clear()
            self._config_files.clear()
            self._watched_files.clear()
            self._change_listeners.clear()