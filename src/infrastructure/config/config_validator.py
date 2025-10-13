"""
配置验证器模块

提供配置验证和健康检查功能，确保配置加载的可见性和可调试性。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .config_loader import ConfigLoaderImpl
from ...core.exceptions import ConfigurationError


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    config_info: Dict[str, Any]
    
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """是否有警告"""
        return len(self.warnings) > 0


class ConfigValidator:
    """配置验证器
    
    提供配置验证、健康检查和诊断功能。
    """
    
    def __init__(self, config_loader: ConfigLoaderImpl):
        """初始化配置验证器
        
        Args:
            config_loader: 配置加载器实例
        """
        self.config_loader = config_loader
        self.logger = logging.getLogger(__name__)
    
    def validate_all_configs(self) -> ConfigValidationResult:
        """验证所有配置文件
        
        Returns:
            ConfigValidationResult: 验证结果
        """
        self.logger.info("开始验证所有配置文件")
        
        errors = []
        warnings = []
        config_info = {}
        
        # 定义要验证的配置文件
        config_files = [
            "model.json",
            "feature_flags.json", 
            "characters.json",
            "story.json"
        ]
        
        for config_file in config_files:
            try:
                result = self.validate_single_config(config_file)
                config_info[config_file] = result.config_info
                errors.extend(result.errors)
                warnings.extend(result.warnings)
                
                if result.has_errors():
                    self.logger.error(f"配置文件验证失败: {config_file}")
                else:
                    self.logger.info(f"配置文件验证通过: {config_file}")
                    
            except Exception as e:
                error_msg = f"验证配置文件时发生异常: {config_file}, 错误: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
        
        # 验证配置一致性
        consistency_errors = self._validate_config_consistency()
        errors.extend(consistency_errors)
        
        # 验证关键配置
        critical_errors = self._validate_critical_configs()
        errors.extend(critical_errors)
        
        is_valid = len(errors) == 0
        
        result = ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            config_info=config_info
        )
        
        if is_valid:
            self.logger.info("所有配置文件验证通过")
        else:
            self.logger.error(f"配置验证失败，发现 {len(errors)} 个错误")
        
        return result
    
    def validate_single_config(self, config_path: str) -> ConfigValidationResult:
        """验证单个配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            ConfigValidationResult: 验证结果
        """
        errors = []
        warnings = []
        config_info = {}
        
        try:
            # 尝试加载配置
            config_data = self.config_loader.load(config_path)
            
            # 收集基本信息
            config_info = {
                "path": config_path,
                "size": len(str(config_data)),
                "keys": list(config_data.keys()) if isinstance(config_data, dict) else [],
                "type": type(config_data).__name__
            }
            
            # 特定配置验证
            if config_path == "model.json":
                model_errors, model_warnings = self._validate_model_config(config_data)
                errors.extend(model_errors)
                warnings.extend(model_warnings)
                config_info["has_api_key"] = bool(config_data.get("api_key"))
                config_info["api_key_length"] = len(config_data.get("api_key", ""))
                
            elif config_path == "characters.json":
                char_errors, char_warnings = self._validate_characters_config(config_data)
                errors.extend(char_errors)
                warnings.extend(char_warnings)
                config_info["character_count"] = len([k for k in config_data.keys() if k != "relations"])
                
            elif config_path == "feature_flags.json":
                flag_errors, flag_warnings = self._validate_feature_flags_config(config_data)
                errors.extend(flag_errors)
                warnings.extend(flag_warnings)
                config_info["flag_count"] = len(config_data)
                
            elif config_path == "story.json":
                story_errors, story_warnings = self._validate_story_config(config_data)
                errors.extend(story_errors)
                warnings.extend(story_warnings)
                
        except Exception as e:
            error_msg = f"加载配置文件失败: {config_path}, 错误: {str(e)}"
            self.logger.error(error_msg)
            errors.append(error_msg)
        
        return ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            config_info=config_info
        )
    
    def _validate_model_config(self, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """验证模型配置"""
        errors = []
        warnings = []
        
        # 检查必需字段
        if "api_key" not in config:
            errors.append("模型配置缺少api_key字段")
        elif not config["api_key"]:
            errors.append("模型配置中api_key为空")
        elif len(config["api_key"]) < 10:
            warnings.append("API密钥长度可能不足")
        
        if "base_url" not in config:
            errors.append("模型配置缺少base_url字段")
        elif not config["base_url"]:
            errors.append("模型配置中base_url为空")
        elif not config["base_url"].startswith(("http://", "https://")):
            warnings.append("base_url可能不是有效的HTTP URL")
        
        # 检查NPC配置
        if "npc" in config:
            npc_config = config["npc"]
            if not isinstance(npc_config, dict):
                errors.append("npc配置必须是字典类型")
            else:
                if "model" not in npc_config:
                    warnings.append("NPC配置缺少model字段")
                if "temperature" in npc_config:
                    temp = npc_config["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        warnings.append("temperature值建议在0-2之间")
        
        return errors, warnings
    
    def _validate_characters_config(self, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """验证角色配置"""
        errors = []
        warnings = []
        
        # 检查角色数量
        character_keys = [k for k in config.keys() if k != "relations"]
        if len(character_keys) == 0:
            warnings.append("配置中没有定义角色")
        
        # 检查每个角色
        for char_name, char_data in config.items():
            if char_name == "relations":
                continue
                
            if not isinstance(char_data, dict):
                errors.append(f"角色 {char_name} 的配置必须是字典类型")
                continue
            
            # 检查必需字段
            required_fields = ["type", "persona"]
            for field in required_fields:
                if field not in char_data:
                    warnings.append(f"角色 {char_name} 缺少 {field} 字段")
            
            # 检查D&D配置
            if "dnd" in char_data:
                dnd_config = char_data["dnd"]
                if not isinstance(dnd_config, dict):
                    errors.append(f"角色 {char_name} 的D&D配置必须是字典类型")
                else:
                    required_dnd_fields = ["level", "ac", "max_hp", "abilities"]
                    for field in required_dnd_fields:
                        if field not in dnd_config:
                            warnings.append(f"角色 {char_name} 的D&D配置缺少 {field} 字段")
        
        # 检查关系配置
        if "relations" in config:
            relations = config["relations"]
            if not isinstance(relations, dict):
                errors.append("relations配置必须是字典类型")
            else:
                for char1, relations_data in relations.items():
                    if not isinstance(relations_data, dict):
                        errors.append(f"角色 {char1} 的关系配置必须是字典类型")
                    else:
                        for char2, value in relations_data.items():
                            if not isinstance(value, int):
                                warnings.append(f"关系值 {char1}->{char2} 应该是整数")
        
        return errors, warnings
    
    def _validate_feature_flags_config(self, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """验证功能标志配置"""
        errors = []
        warnings = []
        
        if not isinstance(config, dict):
            errors.append("功能标志配置必须是字典类型")
            return errors, warnings
        
        # 检查每个标志
        for flag_name, flag_value in config.items():
            if not isinstance(flag_value, bool):
                warnings.append(f"功能标志 {flag_name} 应该是布尔值")
        
        return errors, warnings
    
    def _validate_story_config(self, config: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """验证故事配置"""
        errors = []
        warnings = []
        
        if not isinstance(config, dict):
            errors.append("故事配置必须是字典类型")
            return errors, warnings
        
        # 检查必需部分
        required_sections = ["meta", "scene"]
        for section in required_sections:
            if section not in config:
                errors.append(f"故事配置缺少 {section} 部分")
        
        # 检查场景配置
        if "scene" in config:
            scene = config["scene"]
            if not isinstance(scene, dict):
                errors.append("场景配置必须是字典类型")
            else:
                if "name" not in scene:
                    warnings.append("场景配置缺少名称")
                if "objectives" in scene and not isinstance(scene["objectives"], list):
                    warnings.append("场景目标应该是列表类型")
        
        return errors, warnings
    
    def _validate_config_consistency(self) -> List[str]:
        """验证配置一致性"""
        errors = []
        
        try:
            # 检查角色和故事配置的一致性
            characters_config = self.config_loader.load("characters.json")
            story_config = self.config_loader.load("story.json")
            
            # 获取故事中的角色
            story_characters = set()
            if "initial_positions" in story_config:
                story_characters.update(story_config["initial_positions"].keys())
            
            # 获取配置中的角色
            config_characters = set()
            for key in characters_config.keys():
                if key != "relations":
                    config_characters.add(key)
            
            # 检查一致性
            missing_in_config = story_characters - config_characters
            missing_in_story = config_characters - story_characters
            
            if missing_in_config:
                errors.append(f"故事中引用但配置中缺失的角色: {', '.join(missing_in_config)}")
            
            if missing_in_story:
                self.logger.warning(f"配置中定义但故事中未使用的角色: {', '.join(missing_in_story)}")
                
        except Exception as e:
            self.logger.warning(f"配置一致性检查失败: {str(e)}")
        
        return errors
    
    def _validate_critical_configs(self) -> List[str]:
        """验证关键配置"""
        errors = []
        
        try:
            # 验证模型配置
            model_config = self.config_loader.load("model.json")
            if not model_config.get("api_key"):
                errors.append("关键配置缺失: model.json中缺少有效的API密钥")
            
            # 验证功能标志
            feature_flags = self.config_loader.load("feature_flags.json")
            if not isinstance(feature_flags, dict):
                errors.append("关键配置错误: feature_flags.json格式不正确")
            
        except Exception as e:
            errors.append(f"关键配置验证失败: {str(e)}")
        
        return errors
    
    def get_config_health_report(self) -> Dict[str, Any]:
        """获取配置健康报告
        
        Returns:
            Dict[str, Any]: 健康报告
        """
        result = self.validate_all_configs()
        
        report = {
            "overall_status": "healthy" if result.is_valid else "unhealthy",
            "total_errors": len(result.errors),
            "total_warnings": len(result.warnings),
            "configs_checked": len(result.config_info),
            "config_details": result.config_info,
            "errors": result.errors,
            "warnings": result.warnings,
            "timestamp": str(Path().resolve())
        }
        
        return report