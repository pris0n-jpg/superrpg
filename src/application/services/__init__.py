"""
应用服务模块

该模块包含所有应用服务的具体实现，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

应用服务负责：
1. 协调领域对象和基础设施
2. 实现用例和业务流程
3. 处理事务和异常
4. 提供应用层API
"""

from .base import ApplicationService
from .game_engine import GameEngineService
from .turn_manager import TurnManagerService
from .message_handler import MessageHandlerService
from .agent_service import AgentService

__all__ = [
    # 基础应用服务
    'ApplicationService',
    
    # 核心应用服务
    'GameEngineService',
    'TurnManagerService',
    'MessageHandlerService',
    'AgentService',
]