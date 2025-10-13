"""
配置管理模块

该模块提供配置加载和管理的具体实现，负责从各种来源加载配置数据。
遵循依赖倒置原则，实现core/interfaces.py中定义的配置加载器接口。
"""

from .config_loader import ConfigLoaderImpl
from .settings import Settings

__all__ = [
    "ConfigLoaderImpl",
    "Settings",
]