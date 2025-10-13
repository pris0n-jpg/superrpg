"""
命令处理器模块

该模块实现了命令查询分离(CQS)模式中的命令处理部分，
遵循SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

命令处理器负责：
1. 处理系统状态变更的命令
2. 验证命令的有效性
3. 协调领域服务执行业务逻辑
4. 发布相关的领域事件
"""

from .character_commands import *
from .world_commands import *

__all__ = [
    'CreateCharacterCommand',
    'UpdateCharacterPositionCommand',
    'UpdateCharacterRelationCommand',
    'GiveItemCommand',
    'TakeItemCommand',
    'AssignObjectiveCommand',
    'CharacterCommandHandler',
    
    'SetSceneCommand',
    'SetPositionCommand',
    'SetRelationCommand',
    'EndCombatCommand',
    'WorldCommandHandler',
]