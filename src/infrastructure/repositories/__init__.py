"""
仓储实现模块

该模块提供领域仓储的具体实现，负责数据持久化和检索。
遵循依赖倒置原则，实现core/interfaces.py中定义的仓储接口。
"""

from .character_repository_impl import CharacterRepositoryImpl
from .world_repository_impl import WorldRepositoryImpl

__all__ = [
    "CharacterRepositoryImpl",
    "WorldRepositoryImpl",
]