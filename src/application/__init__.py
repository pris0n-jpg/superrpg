"""
应用服务层模块

该模块包含所有应用服务的定义，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

应用服务负责：
1. 协调领域对象和基础设施
2. 实现用例和业务流程
3. 处理事务和异常
4. 提供应用层API
"""

from .services import *
from .commands import *
from .queries import *
from .coordinators import *
from .container_config import (
    configure_application_container,
    create_application_container,
    get_default_application_config,
    validate_container_configuration
)

__all__ = [
    # 应用服务
    'ApplicationService',
    'GameEngineService',
    'TurnManagerService',
    'MessageHandlerService',
    'AgentService',
    
    # 命令处理器
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
    
    # 查询处理器
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
    
    # 协调器
    'GameCoordinator',
    
    # 容器配置
    'configure_application_container',
    'create_application_container',
    'get_default_application_config',
    'validate_container_configuration',
]