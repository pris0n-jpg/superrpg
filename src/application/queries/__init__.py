"""
查询处理器模块

该模块实现了命令查询分离(CQS)模式中的查询处理部分，
遵循SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

查询处理器负责：
1. 处理系统状态查询的请求
2. 验证查询的有效性
3. 协调领域服务和仓储获取数据
4. 返回只读的查询结果，不修改系统状态
"""

from .character_queries import *
from .world_queries import *

__all__ = [
    'GetCharacterQuery',
    'GetCharacterPositionQuery',
    'GetCharacterRelationsQuery',
    'GetCharacterInventoryQuery',
    'GetCharacterObjectivesQuery',
    'GetAllCharactersQuery',
    'CharacterQueryHandler',
    
    'GetWorldStateQuery',
    'GetWorldSnapshotQuery',
    'GetCombatStateQuery',
    'GetTurnStateQuery',
    'WorldQueryHandler',
]