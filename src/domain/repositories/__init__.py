"""
仓储接口模块

该模块包含所有仓储接口的定义，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。

仓储接口负责：
1. 定义领域对象的持久化契约
2. 提供对领域对象的集合式访问
3. 封装数据访问细节
4. 支持领域对象的生命周期管理
"""

from .character_repository import CharacterRepository
from .world_repository import WorldRepository

__all__ = [
    'CharacterRepository',
    'WorldRepository',
]