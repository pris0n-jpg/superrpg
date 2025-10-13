"""
回合管理服务

该服务负责游戏回合的管理，从main.py中提取回合逻辑，
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

回合管理服务负责：
1. 回合流程的控制和管理
2. 角色行动顺序的维护
3. 回合状态的跟踪
4. 行动超时的处理
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .base import ApplicationService, CommandResult
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, BusinessRuleException
from ...domain.models.world import World
from ...domain.models.characters import Character
from ...domain.models.combat import Combat, TurnState


class TurnStartedEvent(DomainEvent):
    """回合开始事件"""
    
    def __init__(self, character_name: str, turn_number: int, state: Dict[str, Any]):
        super().__init__()
        self.character_name = character_name
        self.turn_number = turn_number
        self.state = state
    
    def get_event_type(self) -> str:
        return "TurnStarted"


class TurnCompletedEvent(DomainEvent):
    """回合完成事件"""
    
    def __init__(self, character_name: str, turn_number: int, actions: List[str]):
        super().__init__()
        self.character_name = character_name
        self.turn_number = turn_number
        self.actions = actions
    
    def get_event_type(self) -> str:
        return "TurnCompleted"


class TurnSkippedEvent(DomainEvent):
    """回合跳过事件"""
    
    def __init__(self, character_name: str, turn_number: int, reason: str):
        super().__init__()
        self.character_name = character_name
        self.turn_number = turn_number
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "TurnSkipped"


class TurnTimeoutEvent(DomainEvent):
    """回合超时事件"""
    
    def __init__(self, character_name: str, turn_number: int, timeout_duration: int):
        super().__init__()
        self.character_name = character_name
        self.turn_number = turn_number
        self.timeout_duration = timeout_duration
    
    def get_event_type(self) -> str:
        return "TurnTimeout"


@dataclass
class TurnContext:
    """回合上下文
    
    封装回合执行过程中的上下文信息。
    遵循单一职责原则，专门负责回合上下文的管理。
    """
    character_name: str
    turn_number: int
    round_number: int
    start_time: datetime
    timeout_duration: int = 30
    is_skipped: bool = False
    skip_reason: Optional[str] = None
    actions_taken: List[str] = None
    
    def __post_init__(self):
        if self.actions_taken is None:
            self.actions_taken = []
    
    def add_action(self, action: str) -> None:
        """添加行动记录
        
        Args:
            action: 行动描述
        """
        self.actions_taken.append(action)
    
    def skip(self, reason: str) -> None:
        """跳过回合
        
        Args:
            reason: 跳过原因
        """
        self.is_skipped = True
        self.skip_reason = reason
    
    def is_timeout(self) -> bool:
        """检查是否超时
        
        Returns:
            bool: 是否超时
        """
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed > self.timeout_duration


class TurnManagerService(ApplicationService):
    """回合管理服务
    
    负责游戏回合的管理，包括回合流程控制、角色行动顺序维护和状态跟踪。
    遵循单一职责原则，专门负责回合管理的核心功能。
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        game_engine,
        timeout_duration: int = 30
    ):
        """初始化回合管理服务
        
        Args:
            event_bus: 事件总线
            logger: 日志记录器
            game_engine: 游戏引擎服务
            timeout_duration: 默认超时时间（秒）
        """
        super().__init__(event_bus, logger)
        self._game_engine = game_engine
        self._timeout_duration = timeout_duration
        self._current_turn_context: Optional[TurnContext] = None
        self._turn_history: List[TurnContext] = []
        self._max_history_size = 100
    
    def start_turn(self, character_name: str, turn_number: int, round_number: int) -> CommandResult:
        """开始角色回合
        
        Args:
            character_name: 角色名称
            turn_number: 回合数
            round_number: 轮次数
            
        Returns:
            CommandResult: 开始结果
        """
        try:
            # 检查角色是否存在且存活
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            character = world.characters.get(character_name)
            if not character:
                return CommandResult.failure_result(
                    ApplicationException(f"Character {character_name} not found")
                )
            
            if not character.is_alive:
                # 跳过死亡角色的回合
                self._skip_character_turn(character_name, turn_number, round_number, "角色已死亡")
                return CommandResult.success_result(
                    data={"skipped": True, "reason": "角色已死亡"},
                    message=f"Turn for {character_name} skipped (character is dead)"
                )
            
            # 创建回合上下文
            self._current_turn_context = TurnContext(
                character_name=character_name,
                turn_number=turn_number,
                round_number=round_number,
                start_time=datetime.now(),
                timeout_duration=self._timeout_duration
            )
            
            # 重置角色回合状态
            if world.combat:
                turn_state = world.combat.reset_actor_turn(character_name)
                
                # 发布回合开始事件
                self.publish_event(TurnStartedEvent(
                    character_name=character_name,
                    turn_number=turn_number,
                    state=turn_state.metadata if turn_state else {}
                ))
            
            # 移除重复的日志记录，只保留事件发布
            # self._logger.info(f"Turn started for {character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": character_name,
                    "turn_number": turn_number,
                    "round_number": round_number,
                    "timeout_duration": self._timeout_duration
                },
                message=f"Turn started for {character_name}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to start turn for {character_name}: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Turn start failed: {str(e)}", cause=e)
            )
    
    def complete_turn(self, actions: Optional[List[str]] = None) -> CommandResult:
        """完成当前回合
        
        Args:
            actions: 执行的行动列表
            
        Returns:
            CommandResult: 完成结果
        """
        if not self._current_turn_context:
            return CommandResult.failure_result(
                ApplicationException("No active turn to complete")
            )
        
        try:
            context = self._current_turn_context
            
            # 记录行动
            if actions:
                for action in actions:
                    context.add_action(action)
            
            # 发布回合完成事件
            self.publish_event(TurnCompletedEvent(
                character_name=context.character_name,
                turn_number=context.turn_number,
                actions=context.actions_taken.copy()
            ))
            
            # 添加到历史记录
            self._add_to_history(context)
            
            result_data = {
                "character_name": context.character_name,
                "turn_number": context.turn_number,
                "round_number": context.round_number,
                "actions_taken": context.actions_taken.copy(),
                "duration_seconds": (datetime.now() - context.start_time).total_seconds()
            }
            
            # 清除当前上下文
            self._current_turn_context = None
            
            return CommandResult.success_result(
                data=result_data,
                message=f"Turn completed for {context.character_name}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to complete turn: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Turn completion failed: {str(e)}", cause=e)
            )
    
    def skip_turn(self, reason: str) -> CommandResult:
        """跳过当前回合
        
        Args:
            reason: 跳过原因
            
        Returns:
            CommandResult: 跳过结果
        """
        if not self._current_turn_context:
            return CommandResult.failure_result(
                ApplicationException("No active turn to skip")
            )
        
        try:
            context = self._current_turn_context
            context.skip(reason)
            
            # 发布回合跳过事件
            self.publish_event(TurnSkippedEvent(
                character_name=context.character_name,
                turn_number=context.turn_number,
                reason=reason
            ))
            
            # 添加到历史记录
            self._add_to_history(context)
            
            self._logger.info(f"Turn skipped for {context.character_name}: {reason}")
            
            result_data = {
                "character_name": context.character_name,
                "turn_number": context.turn_number,
                "round_number": context.round_number,
                "skip_reason": reason,
                "duration_seconds": (datetime.now() - context.start_time).total_seconds()
            }
            
            # 清除当前上下文
            self._current_turn_context = None
            
            return CommandResult.success_result(
                data=result_data,
                message=f"Turn skipped for {context.character_name}: {reason}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to skip turn: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Turn skip failed: {str(e)}", cause=e)
            )
    
    def check_timeout(self) -> CommandResult:
        """检查当前回合是否超时
        
        Returns:
            CommandResult: 检查结果
        """
        if not self._current_turn_context:
            return CommandResult.failure_result(
                ApplicationException("No active turn to check")
            )
        
        try:
            context = self._current_turn_context
            
            if context.is_timeout():
                # 发布超时事件
                self.publish_event(TurnTimeoutEvent(
                    character_name=context.character_name,
                    turn_number=context.turn_number,
                    timeout_duration=context.timeout_duration
                ))
                
                self._logger.warning(f"Turn timeout for {context.character_name}")
                
                return CommandResult.success_result(
                    data={
                        "character_name": context.character_name,
                        "turn_number": context.turn_number,
                        "timeout_duration": context.timeout_duration,
                        "actual_duration": (datetime.now() - context.start_time).total_seconds()
                    },
                    message=f"Turn timeout for {context.character_name}"
                )
            else:
                remaining_time = context.timeout_duration - (datetime.now() - context.start_time).total_seconds()
                
                return CommandResult.success_result(
                    data={
                        "character_name": context.character_name,
                        "turn_number": context.turn_number,
                        "remaining_time": max(0, remaining_time)
                    },
                    message=f"Turn for {context.character_name} is still active"
                )
                
        except Exception as e:
            self._logger.error(f"Failed to check timeout: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Timeout check failed: {str(e)}", cause=e)
            )
    
    def get_current_turn_context(self) -> Optional[TurnContext]:
        """获取当前回合上下文
        
        Returns:
            Optional[TurnContext]: 当前回合上下文
        """
        return self._current_turn_context
    
    def get_turn_history(self, character_name: Optional[str] = None, limit: Optional[int] = None) -> List[TurnContext]:
        """获取回合历史
        
        Args:
            character_name: 角色名称过滤器
            limit: 返回的最大数量
            
        Returns:
            List[TurnContext]: 回合历史列表
        """
        history = self._turn_history.copy()
        
        if character_name:
            history = [ctx for ctx in history if ctx.character_name == character_name]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def add_action_to_current_turn(self, action: str) -> CommandResult:
        """向当前回合添加行动记录
        
        Args:
            action: 行动描述
            
        Returns:
            CommandResult: 添加结果
        """
        if not self._current_turn_context:
            return CommandResult.failure_result(
                ApplicationException("No active turn to add action to")
            )
        
        try:
            self._current_turn_context.add_action(action)
            
            self._logger.debug(f"Action added to turn for {self._current_turn_context.character_name}: {action}")
            
            return CommandResult.success_result(
                data={
                    "character_name": self._current_turn_context.character_name,
                    "action": action,
                    "total_actions": len(self._current_turn_context.actions_taken)
                },
                message="Action added to current turn"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to add action to turn: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Action addition failed: {str(e)}", cause=e)
            )
    
    def _skip_character_turn(self, character_name: str, turn_number: int, round_number: int, reason: str) -> None:
        """跳过角色回合
        
        Args:
            character_name: 角色名称
            turn_number: 回合数
            round_number: 轮次数
            reason: 跳过原因
        """
        context = TurnContext(
            character_name=character_name,
            turn_number=turn_number,
            round_number=round_number,
            start_time=datetime.now(),
            is_skipped=True,
            skip_reason=reason
        )
        
        # 发布跳过事件
        self.publish_event(TurnSkippedEvent(
            character_name=character_name,
            turn_number=turn_number,
            reason=reason
        ))
        
        # 添加到历史记录
        self._add_to_history(context)
    
    def _add_to_history(self, context: TurnContext) -> None:
        """添加回合上下文到历史记录
        
        Args:
            context: 回合上下文
        """
        self._turn_history.append(context)
        
        # 限制历史记录大小
        if len(self._turn_history) > self._max_history_size:
            self._turn_history = self._turn_history[-self._max_history_size:]
    
    def _execute_command_internal(self, command: Any) -> Any:
        """内部命令执行方法
        
        Args:
            command: 要执行的命令
            
        Returns:
            Any: 命令执行结果
        """
        raise NotImplementedError("TurnManagerService does not execute commands directly")
    
    def _execute_query_internal(self, query: Any) -> Any:
        """内部查询执行方法
        
        Args:
            query: 要执行的查询
            
        Returns:
            Any: 查询结果
        """
        raise NotImplementedError("TurnManagerService does not execute queries directly")