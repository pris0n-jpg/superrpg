"""
设置管理模块

提供应用程序设置的管理功能，包括默认值、验证和动态更新。
遵循SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from ...core.exceptions import ConfigurationError


class SettingType(Enum):
    """设置类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    PATH = "path"


@dataclass
class SettingDefinition:
    """设置定义"""
    key: str
    setting_type: SettingType
    default_value: Any
    description: str = ""
    required: bool = False
    validator: Optional[Callable[[Any], bool]] = None
    env_var: Optional[str] = None
    category: str = "general"
    
    def __post_init__(self):
        """初始化后处理"""
        if self.env_var is None:
            # 自动生成环境变量名
            self.env_var = f"SUPERRPG_{self.key.upper().replace('.', '_')}"


@dataclass
class SettingCategory:
    """设置类别"""
    name: str
    description: str = ""
    settings: List[str] = field(default_factory=list)


class Settings:
    """设置管理器
    
    负责应用程序设置的加载、验证、获取和更新。
    遵循单一职责原则，专门负责设置数据的管理。
    """
    
    def __init__(self, config_loader=None):
        """初始化设置管理器
        
        Args:
            config_loader: 配置加载器实例
        """
        self._config_loader = config_loader
        self._settings: Dict[str, Any] = {}
        self._definitions: Dict[str, SettingDefinition] = {}
        self._categories: Dict[str, SettingCategory] = {}
        self._change_callbacks: Dict[str, List[Callable]] = {}
        
        # 注册默认设置
        self._register_default_settings()
        
        # 加载初始设置
        self._load_initial_settings()
    
    def _register_default_settings(self) -> None:
        """注册默认设置"""
        # 应用程序基本设置
        self.register_setting(SettingDefinition(
            key="app.name",
            setting_type=SettingType.STRING,
            default_value="SuperRPG",
            description="应用程序名称",
            category="application"
        ))
        
        self.register_setting(SettingDefinition(
            key="app.version",
            setting_type=SettingType.STRING,
            default_value="1.0.0",
            description="应用程序版本",
            category="application"
        ))
        
        self.register_setting(SettingDefinition(
            key="app.debug",
            setting_type=SettingType.BOOLEAN,
            default_value=False,
            description="调试模式",
            env_var="SUPERRPG_DEBUG",
            category="application"
        ))
        
        # 日志设置
        self.register_setting(SettingDefinition(
            key="logging.level",
            setting_type=SettingType.STRING,
            default_value="INFO",
            description="日志级别",
            validator=lambda x: x.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            category="logging"
        ))
        
        self.register_setting(SettingDefinition(
            key="logging.file_path",
            setting_type=SettingType.PATH,
            default_value="logs/app.log",
            description="日志文件路径",
            category="logging"
        ))
        
        self.register_setting(SettingDefinition(
            key="logging.max_file_size",
            setting_type=SettingType.INTEGER,
            default_value=10 * 1024 * 1024,  # 10MB
            description="日志文件最大大小",
            validator=lambda x: x > 0,
            category="logging"
        ))
        
        self.register_setting(SettingDefinition(
            key="logging.backup_count",
            setting_type=SettingType.INTEGER,
            default_value=5,
            description="日志备份数量",
            validator=lambda x: x >= 0,
            category="logging"
        ))
        
        # 数据存储设置
        self.register_setting(SettingDefinition(
            key="storage.type",
            setting_type=SettingType.STRING,
            default_value="file",
            description="存储类型",
            validator=lambda x: x in ["file", "memory", "database"],
            category="storage"
        ))
        
        self.register_setting(SettingDefinition(
            key="storage.data_dir",
            setting_type=SettingType.PATH,
            default_value="data",
            description="数据存储目录",
            category="storage"
        ))
        
        self.register_setting(SettingDefinition(
            key="storage.auto_save",
            setting_type=SettingType.BOOLEAN,
            default_value=True,
            description="自动保存",
            category="storage"
        ))
        
        self.register_setting(SettingDefinition(
            key="storage.save_interval",
            setting_type=SettingType.INTEGER,
            default_value=300,  # 5分钟
            description="自动保存间隔（秒）",
            validator=lambda x: x > 0,
            category="storage"
        ))
        
        # 模型设置
        self.register_setting(SettingDefinition(
            key="model.api_key",
            setting_type=SettingType.STRING,
            default_value="",
            description="模型API密钥",
            required=True,
            env_var="SUPERRPG_API_KEY",
            category="model"
        ))
        
        self.register_setting(SettingDefinition(
            key="model.base_url",
            setting_type=SettingType.STRING,
            default_value="https://chat.sjtu.plus/v1",
            description="模型基础URL",
            category="model"
        ))
        
        self.register_setting(SettingDefinition(
            key="model.timeout",
            setting_type=SettingType.INTEGER,
            default_value=30,
            description="请求超时时间（秒）",
            validator=lambda x: x > 0,
            category="model"
        ))
        
        self.register_setting(SettingDefinition(
            key="model.max_retries",
            setting_type=SettingType.INTEGER,
            default_value=3,
            description="最大重试次数",
            validator=lambda x: x >= 0,
            category="model"
        ))
        
        # 游戏设置
        self.register_setting(SettingDefinition(
            key="game.default_world_name",
            setting_type=SettingType.STRING,
            default_value="默认世界",
            description="默认世界名称",
            category="game"
        ))
        
        self.register_setting(SettingDefinition(
            key="game.max_characters",
            setting_type=SettingType.INTEGER,
            default_value=10,
            description="最大角色数量",
            validator=lambda x: x > 0,
            category="game"
        ))
        
        self.register_setting(SettingDefinition(
            key="game.auto_save_interval",
            setting_type=SettingType.INTEGER,
            default_value=600,  # 10分钟
            description="游戏自动保存间隔（秒）",
            validator=lambda x: x > 0,
            category="game"
        ))
        
        # 注册设置类别
        self._register_default_categories()
    
    def _register_default_categories(self) -> None:
        """注册默认设置类别"""
        categories = [
            SettingCategory("application", "应用程序设置"),
            SettingCategory("logging", "日志设置"),
            SettingCategory("storage", "存储设置"),
            SettingCategory("model", "模型设置"),
            SettingCategory("game", "游戏设置"),
        ]
        
        for category in categories:
            self._categories[category.name] = category
    
    def _load_initial_settings(self) -> None:
        """加载初始设置"""
        # 从环境变量加载设置
        self._load_from_environment()
        
        # 从配置文件加载设置
        if self._config_loader:
            self._load_from_config()
        
        # 应用默认值
        self._apply_defaults()
    
    def _load_from_environment(self) -> None:
        """从环境变量加载设置"""
        for key, definition in self._definitions.items():
            if definition.env_var and definition.env_var in os.environ:
                env_value = os.environ[definition.env_var]
                parsed_value = self._parse_value(env_value, definition.setting_type)
                self._settings[key] = parsed_value
    
    def _load_from_config(self) -> None:
        """从配置文件加载设置"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 尝试加载settings.json
            config = self._config_loader.load("settings.json")
            logger.debug(f"加载settings.json: {config}")
            
            # 递归合并设置
            self._merge_config_into_settings(config)
            
        except ConfigurationError:
            # 如果配置文件不存在或加载失败，使用默认值
            logger.debug("settings.json不存在或加载失败，尝试加载model.json")
            
            # 尝试直接加载model.json
            try:
                model_config = self._config_loader.load("model.json")
                logger.debug(f"加载model.json: {model_config}")
                
                # 手动设置模型相关配置
                if "api_key" in model_config:
                    self._settings["model.api_key"] = model_config["api_key"]
                    logger.info(f"从model.json加载API密钥: {model_config['api_key'][:10]}...")
                
                if "base_url" in model_config:
                    self._settings["model.base_url"] = model_config["base_url"]
                    logger.info(f"从model.json加载基础URL: {model_config['base_url']}")
                
                if "npc" in model_config:
                    self._settings["model.npc"] = model_config["npc"]
                    logger.info(f"从model.json加载NPC配置: {model_config['npc']}")
                    
            except Exception as e:
                logger.error(f"加载model.json失败: {str(e)}")
    
    def _merge_config_into_settings(self, config: Dict[str, Any], prefix: str = "") -> None:
        """递归合并配置到设置中
        
        Args:
            config: 配置数据
            prefix: 键前缀
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"合并配置，前缀: '{prefix}', 配置键: {list(config.keys())}")
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if full_key in self._definitions:
                # 直接设置已定义的设置
                definition = self._definitions[full_key]
                parsed_value = self._parse_value(value, definition.setting_type)
                self._settings[full_key] = parsed_value
                logger.debug(f"设置 {full_key} = {parsed_value}")
            elif isinstance(value, dict):
                # 递归处理嵌套配置
                logger.debug(f"递归处理嵌套配置: {full_key}")
                self._merge_config_into_settings(value, full_key)
            else:
                logger.debug(f"跳过未定义的设置: {full_key}")
    
    def _apply_defaults(self) -> None:
        """应用默认值"""
        for key, definition in self._definitions.items():
            if key not in self._settings:
                self._settings[key] = definition.default_value
    
    def _parse_value(self, value: Any, setting_type: SettingType) -> Any:
        """解析值到指定类型
        
        Args:
            value: 原始值
            setting_type: 设置类型
            
        Returns:
            Any: 解析后的值
        """
        if setting_type == SettingType.STRING:
            return str(value)
        elif setting_type == SettingType.INTEGER:
            return int(value)
        elif setting_type == SettingType.FLOAT:
            return float(value)
        elif setting_type == SettingType.BOOLEAN:
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        elif setting_type == SettingType.LIST:
            if isinstance(value, str):
                return [item.strip() for item in value.split(',')]
            return list(value)
        elif setting_type == SettingType.DICT:
            if isinstance(value, str):
                # 简单的键值对解析
                result = {}
                for pair in value.split(','):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        result[k.strip()] = v.strip()
                return result
            return dict(value)
        elif setting_type == SettingType.PATH:
            return Path(value)
        else:
            return value
    
    def register_setting(self, definition: SettingDefinition) -> None:
        """注册设置定义
        
        Args:
            definition: 设置定义
        """
        self._definitions[definition.key] = definition
        
        # 添加到类别
        if definition.category in self._categories:
            if definition.key not in self._categories[definition.category].settings:
                self._categories[definition.category].settings.append(definition.key)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值
        
        Args:
            key: 设置键
            default: 默认值
            
        Returns:
            Any: 设置值
        """
        if key in self._settings:
            return self._settings[key]
        
        if key in self._definitions:
            return self._definitions[key].default_value
        
        return default
    
    def set(self, key: str, value: Any) -> None:
        """设置值
        
        Args:
            key: 设置键
            value: 设置值
        """
        if key not in self._definitions:
            raise ConfigurationError(f"未定义的设置: {key}")
        
        definition = self._definitions[key]
        
        # 类型转换和验证
        parsed_value = self._parse_value(value, definition.setting_type)
        
        if definition.validator and not definition.validator(parsed_value):
            raise ConfigurationError(f"设置值验证失败: {key}")
        
        old_value = self._settings.get(key)
        self._settings[key] = parsed_value
        
        # 触发变更回调
        self._trigger_change_callbacks(key, old_value, parsed_value)
    
    def has(self, key: str) -> bool:
        """检查设置是否存在
        
        Args:
            key: 设置键
            
        Returns:
            bool: 是否存在
        """
        return key in self._settings or key in self._definitions
    
    def get_definition(self, key: str) -> Optional[SettingDefinition]:
        """获取设置定义
        
        Args:
            key: 设置键
            
        Returns:
            Optional[SettingDefinition]: 设置定义
        """
        return self._definitions.get(key)
    
    def get_category(self, name: str) -> Optional[SettingCategory]:
        """获取设置类别
        
        Args:
            name: 类别名称
            
        Returns:
            Optional[SettingCategory]: 设置类别
        """
        return self._categories.get(name)
    
    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置
        
        Returns:
            Dict[str, Any]: 所有设置
        """
        return self._settings.copy()
    
    def get_settings_by_category(self, category: str) -> Dict[str, Any]:
        """获取指定类别的设置
        
        Args:
            category: 类别名称
            
        Returns:
            Dict[str, Any]: 类别设置
        """
        if category not in self._categories:
            return {}
        
        result = {}
        for key in self._categories[category].settings:
            if key in self._settings:
                result[key] = self._settings[key]
        
        return result
    
    def reset_to_default(self, key: str) -> None:
        """重置设置为默认值
        
        Args:
            key: 设置键
        """
        if key not in self._definitions:
            raise ConfigurationError(f"未定义的设置: {key}")
        
        old_value = self._settings.get(key)
        default_value = self._definitions[key].default_value
        self._settings[key] = default_value
        
        # 触发变更回调
        self._trigger_change_callbacks(key, old_value, default_value)
    
    def reset_all_to_defaults(self) -> None:
        """重置所有设置为默认值"""
        for key in self._definitions:
            self.reset_to_default(key)
    
    def add_change_callback(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """添加设置变更回调
        
        Args:
            key: 设置键
            callback: 回调函数 (key, old_value, new_value)
        """
        if key not in self._change_callbacks:
            self._change_callbacks[key] = []
        
        self._change_callbacks[key].append(callback)
    
    def remove_change_callback(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """移除设置变更回调
        
        Args:
            key: 设置键
            callback: 回调函数
        """
        if key in self._change_callbacks:
            try:
                self._change_callbacks[key].remove(callback)
            except ValueError:
                pass
    
    def _trigger_change_callbacks(self, key: str, old_value: Any, new_value: Any) -> None:
        """触发设置变更回调
        
        Args:
            key: 设置键
            old_value: 旧值
            new_value: 新值
        """
        if key in self._change_callbacks:
            for callback in self._change_callbacks[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception:
                    # 静默处理回调错误，避免影响设置更新
                    pass
    
    def export_settings(self, include_defaults: bool = False) -> Dict[str, Any]:
        """导出设置
        
        Args:
            include_defaults: 是否包含默认值
            
        Returns:
            Dict[str, Any]: 导出的设置
        """
        result = {}
        
        for key, definition in self._definitions.items():
            if key in self._settings:
                # 构建嵌套结构
                self._set_nested_value(result, key, self._settings[key])
            elif include_defaults:
                self._set_nested_value(result, key, definition.default_value)
        
        return result
    
    def import_settings(self, settings: Dict[str, Any]) -> None:
        """导入设置
        
        Args:
            settings: 要导入的设置
        """
        self._merge_config_into_settings(settings)
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """设置嵌套值
        
        Args:
            data: 数据字典
            key: 键（可能包含点号）
            value: 值
        """
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def validate_all_settings(self) -> List[str]:
        """验证所有设置
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        for key, definition in self._definitions.items():
            if definition.required and key not in self._settings:
                errors.append(f"缺少必需设置: {key}")
                continue
            
            if key in self._settings:
                value = self._settings[key]
                
                # 类型验证
                try:
                    self._parse_value(value, definition.setting_type)
                except Exception:
                    errors.append(f"设置类型错误: {key}")
                    continue
                
                # 自定义验证
                if definition.validator and not definition.validator(value):
                    errors.append(f"设置验证失败: {key}")
        
        return errors
    
    def get_all_categories(self) -> Dict[str, SettingCategory]:
        """获取所有设置类别
        
        Returns:
            Dict[str, SettingCategory]: 设置类别字典
        """
        return self._categories.copy()