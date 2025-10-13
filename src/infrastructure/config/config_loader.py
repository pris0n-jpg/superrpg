"""
配置加载器实现

提供配置数据加载的具体实现，支持多种配置源和格式。
遵循SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from ...core.interfaces import ConfigLoader as IConfigLoader
from ...core.exceptions import ConfigurationError


@dataclass
class ConfigurationSchema:
    """配置模式定义"""
    required_fields: List[str]
    optional_fields: List[str]
    field_types: Dict[str, type]
    field_validators: Dict[str, callable] = None
    
    def __post_init__(self):
        if self.field_validators is None:
            self.field_validators = {}


class ConfigLoaderImpl(IConfigLoader):
    """配置加载器实现
    
    支持从JSON文件、环境变量等多种来源加载配置。
    遵循单一职责原则，专门负责配置数据的加载和验证。
    """
    
    def __init__(self, 
                 config_dir: Optional[Path] = None,
                 schema_registry: Optional[Dict[str, ConfigurationSchema]] = None):
        """初始化配置加载器
        
        Args:
            config_dir: 配置文件目录，如果为None则使用默认目录
            schema_registry: 配置模式注册表
        """
        self._config_dir = config_dir or self._get_default_config_dir()
        self._schema_registry = schema_registry or {}
        self._loaded_configs: Dict[str, Dict[str, Any]] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
        # 注册默认配置模式
        self._register_default_schemas()
    
    def _get_default_config_dir(self) -> Path:
        """获取默认配置目录"""
        # 尝试从项目根目录查找configs目录
        current_dir = Path(__file__).parent
        for parent in current_dir.parents:
            if (parent / "configs").exists():
                return parent / "configs"
        
        # 如果找不到，使用当前目录下的configs
        return current_dir / "configs"
    
    def _register_default_schemas(self) -> None:
        """注册默认配置模式"""
        # 模型配置模式
        self._schema_registry["model"] = ConfigurationSchema(
            required_fields=["api_key"],
            optional_fields=["base_url", "npc"],
            field_types={
                "api_key": str,
                "base_url": str,
                "npc": dict,
            }
        )
        
        # 角色配置模式
        self._schema_registry["characters"] = ConfigurationSchema(
            required_fields=[],
            optional_fields=["characters", "templates"],
            field_types={
                "characters": dict,
                "templates": dict,
            }
        )
        
        # 故事配置模式
        self._schema_registry["story"] = ConfigurationSchema(
            required_fields=[],
            optional_fields=["plot", "scenes", "characters"],
            field_types={
                "plot": dict,
                "scenes": list,
                "characters": list,
            }
        )
        
        # 功能标志配置模式
        self._schema_registry["feature_flags"] = ConfigurationSchema(
            required_fields=[],
            optional_fields=["features"],
            field_types={
                "features": dict,
            }
        )
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
            
        Raises:
            ConfigurationError: 配置加载失败
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 检查缓存
        if config_path in self._config_cache:
            logger.debug(f"从缓存加载配置: {config_path}")
            return self._config_cache[config_path]
        
        logger.info(f"开始加载配置文件: {config_path}")
        
        # 解析配置路径
        full_path = self._resolve_config_path(config_path)
        logger.debug(f"配置文件完整路径: {full_path}")
        
        try:
            # 根据文件扩展名选择加载方法
            if full_path.suffix.lower() == '.json':
                config_data = self._load_json_config(full_path)
            elif full_path.suffix.lower() in ['.yaml', '.yml']:
                config_data = self._load_yaml_config(full_path)
            else:
                raise ConfigurationError(f"不支持的配置文件格式: {full_path.suffix}")
            
            logger.debug(f"成功加载配置数据，键数量: {len(config_data) if isinstance(config_data, dict) else '非字典类型'}")
            
            # 应用环境变量覆盖
            config_data = self._apply_env_overrides(config_data, config_path)
            
            # 验证配置
            config_name = Path(config_path).stem
            if config_name in self._schema_registry:
                logger.debug(f"验证配置模式: {config_name}")
                self._validate_config(config_data, self._schema_registry[config_name])
                logger.debug(f"配置验证通过: {config_name}")
            
            # 缓存配置
            self._config_cache[config_path] = config_data
            self._loaded_configs[config_path] = config_data
            
            logger.info(f"配置文件加载成功: {config_path}")
            return config_data
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {config_path}, 错误: {str(e)}")
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"加载配置文件失败: {config_path}") from e
    
    def _resolve_config_path(self, config_path: str) -> Path:
        """解析配置文件路径
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Path: 解析后的完整路径
        """
        # 如果是绝对路径，直接返回
        if Path(config_path).is_absolute():
            return Path(config_path)
        
        # 如果是相对路径，相对于配置目录
        full_path = self._config_dir / config_path
        
        # 如果文件不存在，尝试添加.json扩展名
        if not full_path.exists() and not full_path.suffix:
            full_path = full_path.with_suffix('.json')
        
        if not full_path.exists():
            raise ConfigurationError(f"配置文件不存在: {full_path}")
        
        return full_path
    
    def _load_json_config(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON配置文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"JSON格式错误: {file_path}, {e}") from e
        except Exception as e:
            raise ConfigurationError(f"读取文件失败: {file_path}") from e
    
    def _load_yaml_config(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML配置文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        try:
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            raise ConfigurationError("YAML支持未安装，请安装PyYAML")
        except Exception as e:
            raise ConfigurationError(f"读取YAML文件失败: {file_path}") from e
    
    def _apply_env_overrides(self, config_data: Dict[str, Any], config_name: str) -> Dict[str, Any]:
        """应用环境变量覆盖
        
        Args:
            config_data: 原始配置数据
            config_name: 配置名称
            
        Returns:
            Dict[str, Any]: 应用覆盖后的配置数据
        """
        # 环境变量格式: SUPERRPG_{CONFIG_NAME}_{FIELD_NAME}
        prefix = f"SUPERRPG_{config_name.upper()}_"
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                field_name = key[len(prefix):].lower()
                
                # 尝试解析值的类型
                parsed_value = self._parse_env_value(value)
                
                # 嵌套字段支持 (使用下划线分隔)
                self._set_nested_field(config_data, field_name, parsed_value)
        
        return config_data
    
    def _parse_env_value(self, value: str) -> Union[str, int, float, bool, List[str]]:
        """解析环境变量值的类型
        
        Args:
            value: 环境变量值
            
        Returns:
            Union[str, int, float, bool, List[str]]: 解析后的值
        """
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 整数
        try:
            return int(value)
        except ValueError:
            pass
        
        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass
        
        # 逗号分隔的列表
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # 默认为字符串
        return value
    
    def _set_nested_field(self, config_data: Dict[str, Any], field_path: str, value: Any) -> None:
        """设置嵌套字段值
        
        Args:
            config_data: 配置数据
            field_path: 字段路径 (用下划线分隔)
            value: 字段值
        """
        keys = field_path.split('_')
        current = config_data
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        current[keys[-1]] = value
    
    def _validate_config(self, config_data: Dict[str, Any], schema: ConfigurationSchema) -> None:
        """验证配置数据
        
        Args:
            config_data: 配置数据
            schema: 配置模式
            
        Raises:
            ConfigurationError: 验证失败
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"开始验证配置，必需字段: {schema.required_fields}")
        
        # 检查必需字段
        missing_fields = []
        for field in schema.required_fields:
            if field not in config_data:
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"缺少必需字段: {', '.join(missing_fields)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        
        # 检查字段类型
        type_errors = []
        for field, expected_type in schema.field_types.items():
            if field in config_data:
                value = config_data[field]
                if not isinstance(value, expected_type):
                    try:
                        # 尝试类型转换
                        old_value = value
                        config_data[field] = expected_type(value)
                        logger.debug(f"字段 {field} 类型转换: {type(old_value).__name__} -> {expected_type.__name__}")
                    except (ValueError, TypeError) as e:
                        error_msg = f"字段类型错误: {field}, 期望 {expected_type.__name__}, 实际 {type(value).__name__}"
                        logger.error(f"{error_msg}, 转换失败: {str(e)}")
                        type_errors.append(error_msg)
        
        if type_errors:
            raise ConfigurationError(f"类型错误: {'; '.join(type_errors)}")
        
        # 运行自定义验证器
        validation_errors = []
        for field, validator in schema.field_validators.items():
            if field in config_data:
                try:
                    if not validator(config_data[field]):
                        error_msg = f"字段验证失败: {field}"
                        logger.error(error_msg)
                        validation_errors.append(error_msg)
                    else:
                        logger.debug(f"字段验证通过: {field}")
                except Exception as e:
                    error_msg = f"字段验证错误: {field}, {e}"
                    logger.error(error_msg)
                    validation_errors.append(error_msg)
        
        if validation_errors:
            raise ConfigurationError(f"验证错误: {'; '.join(validation_errors)}")
        
        logger.debug("配置验证通过")
    
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 基本验证：配置必须是字典
            if not isinstance(config, dict):
                return False
            
            # 检查是否有有效的配置数据
            return len(config) > 0
            
        except Exception:
            return False
    
    def reload(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 重新加载的配置数据
        """
        # 清除缓存
        if config_path in self._config_cache:
            del self._config_cache[config_path]
        
        # 重新加载
        return self.load(config_path)
    
    def get_loaded_configs(self) -> List[str]:
        """获取已加载的配置列表
        
        Returns:
            List[str]: 配置路径列表
        """
        return list(self._loaded_configs.keys())
    
    def register_schema(self, name: str, schema: ConfigurationSchema) -> None:
        """注册配置模式
        
        Args:
            name: 模式名称
            schema: 配置模式
        """
        self._schema_registry[name] = schema
    
    def get_schema(self, name: str) -> Optional[ConfigurationSchema]:
        """获取配置模式
        
        Args:
            name: 模式名称
            
        Returns:
            Optional[ConfigurationSchema]: 配置模式，如果不存在则返回None
        """
        return self._schema_registry.get(name)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache.clear()
    
    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_config_section(self, config_path: str, section_path: str) -> Any:
        """获取配置的特定部分
        
        Args:
            config_path: 配置文件路径
            section_path: 部分路径 (用点分隔)
            
        Returns:
            Any: 配置部分
        """
        config = self.load(config_path)
        
        keys = section_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current