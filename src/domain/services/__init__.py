"""
领域服务模块

该模块包含所有领域服务的定义，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

领域服务负责：
1. 协调多个聚合根的交互
2. 实现跨聚合根的业务逻辑
3. 封装复杂的领域操作
4. 提供领域特定的业务服务
"""

from .character_service import CharacterService
from .combat_service import CombatService
from .world_service import WorldService

__all__ = [
    'CharacterService',
    'CombatService',
    'WorldService',
]