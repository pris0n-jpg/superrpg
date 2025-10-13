"""
游戏引擎服务

该服务负责游戏的核心逻辑协调，从main.py中提取应用层逻辑，
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

游戏引擎服务负责：
1. 游戏流程的整体控制
2. 协调各个应用服务
3. 管理游戏状态和生命周期
4. 处理游戏配置和初始化
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple, Callable, Mapping
from dataclasses import asdict

from .base import ApplicationService, CommandResult
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, BusinessRuleException
from ...domain.models.world import World
from ...domain.models.characters import Character
from ...domain.models.combat import Combat
from ...domain.services.character_service import CharacterService
from ...domain.services.combat_service import CombatService
from ...domain.services.world_service import WorldService


class GameStartedEvent(DomainEvent):
    """游戏开始事件"""
    
    def __init__(self, game_config: Dict[str, Any]):
        super().__init__()
        self.game_config = game_config
    
    def get_event_type(self) -> str:
        return "GameStarted"


class GameEndedEvent(DomainEvent):
    """游戏结束事件"""
    
    def __init__(self, reason: str, final_state: Dict[str, Any]):
        super().__init__()
        self.reason = reason
        self.final_state = final_state
    
    def get_event_type(self) -> str:
        return "GameEnded"


class RoundStartedEvent(DomainEvent):
    """回合开始事件"""
    
    def __init__(self, round_number: int, participants: List[str]):
        super().__init__()
        self.round_number = round_number
        self.participants = participants
    
    def get_event_type(self) -> str:
        return "RoundStarted"


class RoundEndedEvent(DomainEvent):
    """回合结束事件"""
    
    def __init__(self, round_number: int):
        super().__init__()
        self.round_number = round_number
    
    def get_event_type(self) -> str:
        return "RoundEnded"


class GameEngineService(ApplicationService):
    """游戏引擎服务
    
    负责游戏的核心逻辑协调，包括游戏流程控制、状态管理和事件处理。
    遵循单一职责原则，专门负责游戏引擎的核心功能。
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        character_service: CharacterService,
        combat_service: CombatService,
        world_service: WorldService
    ):
        """初始化游戏引擎服务
        
        Args:
            event_bus: 事件总线
            logger: 日志记录器
            character_service: 角色服务
            combat_service: 战斗服务
            world_service: 世界服务
        """
        super().__init__(event_bus, logger)
        self._character_service = character_service
        self._combat_service = combat_service
        self._world_service = world_service
        self._world: Optional[World] = None
        self._current_round: int = 0
        self._max_rounds: Optional[int] = None
        self._require_hostiles: bool = True
        self._is_running: bool = False
    
    def initialize_game(
        self,
        game_config: Dict[str, Any],
        character_configs: Dict[str, Any],
        story_config: Dict[str, Any]
    ) -> CommandResult:
        """初始化游戏
        
        Args:
            game_config: 游戏配置
            character_configs: 角色配置
            story_config: 故事配置
            
        Returns:
            CommandResult: 初始化结果
        """
        try:
            self._logger.debug("Initializing game")
            
            # 创建世界
            self._world = self._world_service.create_world(game_config)
            
            # 初始化角色
            self._initialize_characters(character_configs, story_config)
            
            # 初始化场景
            self._initialize_scene(story_config)
            
            # 初始化关系
            self._initialize_relations(character_configs, story_config)
            
            # 设置游戏参数
            self._setup_game_parameters(game_config)
            
            self._logger.debug("Game initialized successfully")
            
            return CommandResult.success_result(
                data={"world_id": self._world.id},
                message="Game initialized successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to initialize game: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game initialization failed: {str(e)}", cause=e)
            )
    
    def start_game(self) -> CommandResult:
        """开始游戏
        
        Returns:
            CommandResult: 开始结果
        """
        if not self._world:
            return CommandResult.failure_result(
                ApplicationException("Game not initialized")
            )
        
        if self._is_running:
            return CommandResult.failure_result(
                ApplicationException("Game is already running")
            )
        
        try:
            self._is_running = True
            self._current_round = 1
            
            # 发布游戏开始事件
            self.publish_event(GameStartedEvent({
                "world_id": self._world.id,
                "max_rounds": self._max_rounds,
                "require_hostiles": self._require_hostiles
            }))
            
            self._logger.info("Game started")
            
            return CommandResult.success_result(
                data={"round": self._current_round},
                message="Game started successfully"
            )
            
        except Exception as e:
            self._is_running = False
            self._logger.error(f"Failed to start game: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game start failed: {str(e)}", cause=e)
            )
    
    def end_game(self, reason: str) -> CommandResult:
        """结束游戏
        
        Args:
            reason: 结束原因
            
        Returns:
            CommandResult: 结束结果
        """
        if not self._is_running:
            return CommandResult.failure_result(
                ApplicationException("Game is not running")
            )
        
        try:
            self._is_running = False
            
            # 获取最终状态
            final_state = self._world.snapshot() if self._world else {}
            
            # 发布游戏结束事件
            self.publish_event(GameEndedEvent(reason, final_state))
            
            self._logger.info(f"Game ended: {reason}")
            
            return CommandResult.success_result(
                data={"reason": reason, "final_state": final_state},
                message=f"Game ended: {reason}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to end game: {e}")
            self._logger.error(f"Exception type: {type(e).__name__}")
            self._logger.error(f"Exception module: {e.__class__.__module__}")
            
            # 打印完整的堆栈跟踪
            import traceback
            self._logger.error(f"Full traceback:\n{traceback.format_exc()}")
            
            return CommandResult.failure_result(
                ApplicationException(f"Game end failed: {str(e)}", cause=e)
            )
    
    def advance_round(self) -> CommandResult:
        """推进到下一回合
        
        Returns:
            CommandResult: 推进结果
        """
        if not self._is_running:
            return CommandResult.failure_result(
                ApplicationException("Game is not running")
            )
        
        try:
            # 检查是否应该结束游戏
            if self._should_end_game():
                return self.end_game(self._get_end_reason())
            
            # 发布回合开始事件
            self.publish_event(RoundStartedEvent(
                self._current_round,
                self._get_active_participants()
            ))
            
            self._logger.debug(f"Round {self._current_round} started")
            
            return CommandResult.success_result(
                data={"round": self._current_round},
                message=f"Round {self._current_round} started"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to advance round: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Round advance failed: {str(e)}", cause=e)
            )
    
    def complete_round(self) -> CommandResult:
        """完成当前回合
        
        Returns:
            CommandResult: 完成结果
        """
        if not self._is_running:
            return CommandResult.failure_result(
                ApplicationException("Game is not running")
            )
        
        try:
            # 发布回合结束事件
            self.publish_event(RoundEndedEvent(self._current_round))
            
            self._current_round += 1
            
            self._logger.debug(f"Round {self._current_round - 1} completed")
            
            return CommandResult.success_result(
                data={"next_round": self._current_round},
                message=f"Round {self._current_round - 1} completed"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to complete round: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Round completion failed: {str(e)}", cause=e)
            )
    
    def get_game_state(self) -> Dict[str, Any]:
        """获取游戏状态
        
        Returns:
            Dict[str, Any]: 游戏状态
        """
        if not self._world:
            return {}
        
        return {
            "is_running": self._is_running,
            "current_round": self._current_round,
            "max_rounds": self._max_rounds,
            "require_hostiles": self._require_hostiles,
            "world_state": self._world.snapshot(),
            "combat_state": self._world.combat.snapshot() if self._world.combat else None,
            "participants": self._get_active_participants()
        }
    
    def get_current_world(self) -> Optional[World]:
        """获取当前世界对象
        
        Returns:
            Optional[World]: 当前世界对象，如果不存在则返回None
        """
        return self._world
    
    def _initialize_characters(self, character_configs: Dict[str, Any], story_config: Dict[str, Any]) -> None:
        """初始化角色
        
        Args:
            character_configs: 角色配置
            story_config: 故事配置
        """
        # 提取初始位置
        story_positions = self._extract_story_positions(story_config)
        
        # 创建角色
        for name, config in character_configs.items():
            if name in {"relations", "objective_positions", "participants"}:
                continue
            
            # 获取角色配置
            dnd_config = config.get("dnd", {})
            persona = config.get("persona", "")
            
            # 创建角色
            if dnd_config:
                character = self._character_service.create_character_from_dnd_config(name, dnd_config)
            else:
                # 使用默认配置创建角色
                character = self._character_service.create_character(
                    name=name,
                    abilities={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                    hp=10,
                    max_hp=10
                )
            
            # 设置位置
            if name in story_positions:
                character.position = story_positions[name]
            
            # 添加到世界
            self._world.add_character(character)
    
    def _initialize_scene(self, story_config: Dict[str, Any]) -> None:
        """初始化场景
        
        Args:
            story_config: 故事配置
        """
        scene_config = story_config.get("scene", {})
        
        if scene_config:
            self._world_service.set_scene(
                world=self._world,
                name=scene_config.get("name"),
                objectives=scene_config.get("objectives", []),
                details=scene_config.get("details", []),
                time_min=scene_config.get("time_min"),
                weather=scene_config.get("weather")
            )
    
    def _initialize_relations(self, character_configs: Dict[str, Any], story_config: Dict[str, Any]) -> None:
        """初始化关系
        
        Args:
            character_configs: 角色配置
            story_config: 故事配置
        """
        relations_config = character_configs.get("relations", {})
        
        if relations_config:
            for source, targets in relations_config.items():
                if isinstance(targets, dict):
                    for target, score in targets.items():
                        self._world_service.set_relation(
                            world=self._world,
                            source=source,
                            target=target,
                            score=score,
                            reason="配置设定"
                        )
    
    def _setup_game_parameters(self, game_config: Dict[str, Any]) -> None:
        """设置游戏参数
        
        Args:
            game_config: 游戏配置
        """
        self._max_rounds = game_config.get("max_rounds")
        self._require_hostiles = game_config.get("require_hostiles", True)
    
    def _extract_story_positions(self, story_config: Dict[str, Any]) -> Dict[str, Tuple[int, int]]:
        """提取故事位置
        
        Args:
            story_config: 故事配置
            
        Returns:
            Dict[str, Tuple[int, int]]: 位置字典
        """
        positions = {}
        
        # 从不同位置提取位置信息
        position_sources = [
            story_config.get("initial_positions", {}),
            story_config.get("positions", {}),
            story_config.get("initial", {}).get("positions", {})
        ]
        
        for source in position_sources:
            if isinstance(source, dict):
                for name, pos in source.items():
                    if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                        try:
                            positions[str(name)] = (int(pos[0]), int(pos[1]))
                        except (ValueError, TypeError):
                            continue
        
        return positions
    
    def _get_active_participants(self) -> List[str]:
        """获取活跃参与者
        
        Returns:
            List[str]: 参与者列表
        """
        if not self._world:
            return []
        
        return [name for name, character in self._world.characters.items() if character.is_alive]
    
    def _should_end_game(self) -> bool:
        """检查是否应该结束游戏
        
        Returns:
            bool: 是否应该结束
        """
        if not self._world:
            return True
        
        # 检查最大回合数
        if self._max_rounds and self._current_round > self._max_rounds:
            return True
        
        # 检查目标是否完成 - 只有在真正有目标且目标完成时才结束游戏
        if self._world.objective_tracker:
            # 确保目标跟踪器有目标
            try:
                # 检查是否有实际的目标
                if hasattr(self._world.objective_tracker, 'objectives') and self._world.objective_tracker.objectives:
                    # 修改：只有在有目标且所有目标都完成，并且已经进行了足够回合时才结束游戏
                    if self._world.objective_tracker.all_objectives_completed() and self._current_round > 3:
                        self._logger.info(f"所有目标已完成（第{self._current_round}回合），游戏结束")
                        return True
                    elif self._world.objective_tracker.all_objectives_completed():
                        self._logger.debug(f"所有目标已完成，但游戏刚开始（第{self._current_round}回合），继续游戏")
                else:
                    # 如果没有目标，不基于目标结束游戏
                    self._logger.debug("没有设置目标，跳过目标检查")
            except Exception as e:
                self._logger.warning(f"检查目标状态时出错: {e}")
        
        # 检查是否需要敌对关系
        if self._require_hostiles and not self._has_hostiles():
            return True
        
        return False
    
    def _get_end_reason(self) -> str:
        """获取结束原因
        
        Returns:
            str: 结束原因
        """
        if self._max_rounds and self._current_round > self._max_rounds:
            return f"已达到最大回合 {self._max_rounds}"
        
        if self._world.objective_tracker and self._world.objective_tracker.all_objectives_completed():
            if self._current_round > 3:
                return f"所有目标均已解决（第{self._current_round}回合）"
            else:
                return f"所有目标已解决，但游戏刚开始（第{self._current_round}回合）"
        
        if self._require_hostiles and not self._has_hostiles():
            return "场上已无敌对存活单位"
        
        return "游戏结束"
    
    def _has_hostiles(self) -> bool:
        """检查是否有敌对关系
        
        Returns:
            bool: 是否有敌对关系
        """
        if not self._world or not self._world.relationship_network:
            return False
        
        participants = self._get_active_participants()
        if len(participants) <= 1:
            return False
        
        # 检查参与者之间是否有敌对关系
        for i, source in enumerate(participants):
            for target in participants[i+1:]:
                relation = self._world.relationship_network.get_relation(source, target)
                if relation and relation.strength <= -10:
                    return True
        
        return False
    
    def _execute_command_internal(self, command: Any) -> Any:
        """内部命令执行方法
        
        Args:
            command: 要执行的命令
            
        Returns:
            Any: 命令执行结果
        """
        # 游戏引擎服务不直接处理命令，而是通过协调其他服务
        raise NotImplementedError("GameEngineService coordinates other services")
    
    def _execute_query_internal(self, query: Any) -> Any:
        """内部查询执行方法
        
        Args:
            query: 要执行的查询
            
        Returns:
            Any: 查询结果
        """
        # 游戏引擎服务不直接处理查询，而是通过协调其他服务
        raise NotImplementedError("GameEngineService coordinates other services")