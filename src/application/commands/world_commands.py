"""
世界相关命令处理器

该模块实现了世界相关的命令处理器，遵循命令查询分离(CQS)模式，
符合SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

世界命令处理器负责：
1. 处理场景设置命令
2. 处理位置设置命令
3. 处理关系设置命令
4. 处理战斗控制命令
5. 处理世界状态管理命令
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..services.base import CommandHandler, CommandResult
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, ValidationException, BusinessRuleException
from ...domain.models.world import World
from ...domain.services.world_service import WorldService


# 世界相关事件
class SceneSetEvent(DomainEvent):
    """场景设置事件"""
    
    def __init__(self, scene_name: str, scene_data: Dict[str, Any]):
        super().__init__()
        self.scene_name = scene_name
        self.scene_data = scene_data
    
    def get_event_type(self) -> str:
        return "SceneSet"


class PositionSetEvent(DomainEvent):
    """位置设置事件"""
    
    def __init__(self, character_name: str, position: Tuple[int, int]):
        super().__init__()
        self.character_name = character_name
        self.position = position
    
    def get_event_type(self) -> str:
        return "PositionSet"


class RelationSetEvent(DomainEvent):
    """关系设置事件"""
    
    def __init__(self, source_character: str, target_character: str, score: int, reason: str):
        super().__init__()
        self.source_character = source_character
        self.target_character = target_character
        self.score = score
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "RelationSet"


class CombatEndedEvent(DomainEvent):
    """战斗结束事件"""
    
    def __init__(self, reason: str, combat_data: Dict[str, Any]):
        super().__init__()
        self.reason = reason
        self.combat_data = combat_data
    
    def get_event_type(self) -> str:
        return "CombatEnded"


class WorldResetEvent(DomainEvent):
    """世界重置事件"""
    
    def __init__(self, reset_type: str, reset_data: Dict[str, Any]):
        super().__init__()
        self.reset_type = reset_type
        self.reset_data = reset_data
    
    def get_event_type(self) -> str:
        return "WorldReset"


# 世界相关命令
@dataclass
class SetSceneCommand:
    """设置场景命令"""
    scene_name: str
    objectives: Optional[List[str]] = None
    details: Optional[List[str]] = None
    time_min: Optional[int] = None
    weather: Optional[str] = None
    append: bool = False


@dataclass
class SetPositionCommand:
    """设置位置命令"""
    character_name: str
    x: int
    y: int


@dataclass
class SetRelationCommand:
    """设置关系命令"""
    source_character: str
    target_character: str
    score: int
    reason: str = ""


@dataclass
class EndCombatCommand:
    """结束战斗命令"""
    reason: str = ""


@dataclass
class ResetWorldCommand:
    """重置世界命令"""
    reset_type: str = "full"  # full, partial, combat_only
    preserve_characters: bool = True
    preserve_relations: bool = True


# 世界命令处理器
class WorldCommandHandler(CommandHandler):
    """世界命令处理器
    
    负责处理所有世界相关的命令，包括场景设置、位置管理、关系管理等。
    遵循单一职责原则，专门负责世界命令的处理。
    """
    
    def __init__(
        self,
        world_service: WorldService,
        game_engine,
        event_bus: EventBus,
        logger: Logger
    ):
        """初始化世界命令处理器
        
        Args:
            world_service: 世界服务
            game_engine: 游戏引擎服务
            event_bus: 事件总线
            logger: 日志记录器
        """
        self._world_service = world_service
        self._game_engine = game_engine
        self._event_bus = event_bus
        self._logger = logger
    
    def handle(self, command: Any) -> CommandResult:
        """处理命令
        
        Args:
            command: 要处理的命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            if isinstance(command, SetSceneCommand):
                return self._handle_set_scene(command)
            elif isinstance(command, SetPositionCommand):
                return self._handle_set_position(command)
            elif isinstance(command, SetRelationCommand):
                return self._handle_set_relation(command)
            elif isinstance(command, EndCombatCommand):
                return self._handle_end_combat(command)
            elif isinstance(command, ResetWorldCommand):
                return self._handle_reset_world(command)
            else:
                return CommandResult.failure_result(
                    ApplicationException(f"Unsupported command type: {type(command).__name__}")
                )
                
        except Exception as e:
            self._logger.error(f"Failed to handle command {type(command).__name__}: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Command handling failed: {str(e)}", cause=e)
            )
    
    def can_handle(self, command_type: type) -> bool:
        """检查是否能处理指定类型的命令
        
        Args:
            command_type: 命令类型
            
        Returns:
            bool: 是否能处理
        """
        return command_type in {
            SetSceneCommand,
            SetPositionCommand,
            SetRelationCommand,
            EndCombatCommand,
            ResetWorldCommand
        }
    
    def _handle_set_scene(self, command: SetSceneCommand) -> CommandResult:
        """处理设置场景命令
        
        Args:
            command: 设置场景命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Setting scene: {command.scene_name}")
            
            # 验证命令
            self._validate_set_scene_command(command)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            # 记录旧场景信息
            old_scene_name = world.location
            old_objectives = list(world.objectives) if world.objectives else []
            
            # 设置场景
            self._world_service.set_scene(
                world=world,
                name=command.scene_name,
                objectives=command.objectives,
                details=command.details,
                time_min=command.time_min,
                weather=command.weather
            )
            
            # 发布事件
            self._event_bus.publish(SceneSetEvent(
                scene_name=command.scene_name,
                scene_data={
                    "old_scene_name": old_scene_name,
                    "objectives": command.objectives or [],
                    "details": command.details or [],
                    "time_min": command.time_min,
                    "weather": command.weather,
                    "append": command.append
                }
            ))
            
            self._logger.info(f"Scene set: {command.scene_name}")
            
            return CommandResult.success_result(
                data={
                    "scene_name": command.scene_name,
                    "old_scene_name": old_scene_name,
                    "objectives": command.objectives or [],
                    "details": command.details or [],
                    "time_min": command.time_min,
                    "weather": command.weather
                },
                message=f"Scene set to {command.scene_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Scene setting failed: {str(e)}", cause=e)
            )
    
    def _handle_set_position(self, command: SetPositionCommand) -> CommandResult:
        """处理设置位置命令
        
        Args:
            command: 设置位置命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Setting position for character: {command.character_name}")
            
            # 验证命令
            self._validate_set_position_command(command)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            # 记录旧位置
            character = world.characters.get(command.character_name)
            old_position = character.position.to_tuple() if character and character.position else None
            
            # 设置位置
            self._world_service.set_position(
                world=world,
                character_name=command.character_name,
                x=command.x,
                y=command.y
            )
            
            # 发布事件
            self._event_bus.publish(PositionSetEvent(
                character_name=command.character_name,
                position=(command.x, command.y)
            ))
            
            self._logger.info(f"Position set for character: {command.character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": command.character_name,
                    "old_position": old_position,
                    "new_position": (command.x, command.y)
                },
                message=f"Position set for {command.character_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Position setting failed: {str(e)}", cause=e)
            )
    
    def _handle_set_relation(self, command: SetRelationCommand) -> CommandResult:
        """处理设置关系命令
        
        Args:
            command: 设置关系命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Setting relation: {command.source_character} -> {command.target_character}")
            
            # 验证命令
            self._validate_set_relation_command(command)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            # 记录旧关系
            old_relation = world.relationship_network.get_relation(
                command.source_character, command.target_character
            )
            old_score = old_relation.strength if old_relation else 0
            
            # 设置关系
            self._world_service.set_relation(
                world=world,
                source=command.source_character,
                target=command.target_character,
                score=command.score,
                reason=command.reason
            )
            
            # 发布事件
            self._event_bus.publish(RelationSetEvent(
                source_character=command.source_character,
                target_character=command.target_character,
                score=command.score,
                reason=command.reason
            ))
            
            self._logger.info(f"Relation set: {command.source_character} -> {command.target_character}")
            
            return CommandResult.success_result(
                data={
                    "source_character": command.source_character,
                    "target_character": command.target_character,
                    "old_score": old_score,
                    "new_score": command.score,
                    "reason": command.reason
                },
                message=f"Relation set: {command.source_character} -> {command.target_character}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Relation setting failed: {str(e)}", cause=e)
            )
    
    def _handle_end_combat(self, command: EndCombatCommand) -> CommandResult:
        """处理结束战斗命令
        
        Args:
            command: 结束战斗命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info("Ending combat")
            
            # 验证命令
            self._validate_end_combat_command(command)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            # 检查是否在战斗中
            if not world.is_in_combat:
                return CommandResult.failure_result(
                    ApplicationException("Not in combat")
                )
            
            # 记录战斗数据
            combat_data = {}
            if world.combat:
                combat_data = {
                    "participants": list(world.combat.participants),
                    "current_round": world.combat.current_round,
                    "current_actor": world.combat.current_actor,
                    "initiative_order": list(world.combat.initiative_order),
                    "initiative_scores": dict(world.combat.initiative_scores)
                }
            
            # 结束战斗
            self._world_service.end_combat(world)
            
            # 发布事件
            self._event_bus.publish(CombatEndedEvent(
                reason=command.reason or "手动结束",
                combat_data=combat_data
            ))
            
            self._logger.info("Combat ended")
            
            return CommandResult.success_result(
                data={
                    "reason": command.reason or "手动结束",
                    "combat_data": combat_data
                },
                message="Combat ended successfully"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Combat ending failed: {str(e)}", cause=e)
            )
    
    def _handle_reset_world(self, command: ResetWorldCommand) -> CommandResult:
        """处理重置世界命令
        
        Args:
            command: 重置世界命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Resetting world: {command.reset_type}")
            
            # 验证命令
            self._validate_reset_world_command(command)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return CommandResult.failure_result(
                    ApplicationException("No active world")
                )
            
            # 记录重置前的状态
            old_state = world.snapshot()
            
            # 根据重置类型执行重置
            if command.reset_type == "combat_only":
                # 仅重置战斗状态
                if world.is_in_combat:
                    self._world_service.end_combat(world)
            elif command.reset_type == "partial":
                # 部分重置
                if world.is_in_combat:
                    self._world_service.end_combat(world)
                # 重置其他状态但保留角色和关系
                world.objectives.clear()
                world.location = "未知"
                world.time_min = 0
                world.weather = "unknown"
            elif command.reset_type == "full":
                # 完全重置
                if not command.preserve_characters:
                    world.characters.clear()
                if not command.preserve_relations:
                    world.relationship_network.clear()
                world.objectives.clear()
                world.location = "未知"
                world.time_min = 0
                world.weather = "unknown"
                if world.is_in_combat:
                    self._world_service.end_combat(world)
            
            # 发布事件
            self._event_bus.publish(WorldResetEvent(
                reset_type=command.reset_type,
                reset_data={
                    "preserve_characters": command.preserve_characters,
                    "preserve_relations": command.preserve_relations,
                    "old_state": old_state
                }
            ))
            
            self._logger.info(f"World reset: {command.reset_type}")
            
            return CommandResult.success_result(
                data={
                    "reset_type": command.reset_type,
                    "preserve_characters": command.preserve_characters,
                    "preserve_relations": command.preserve_relations
                },
                message=f"World reset ({command.reset_type}) successfully"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"World reset failed: {str(e)}", cause=e)
            )
    
    def _validate_set_scene_command(self, command: SetSceneCommand) -> None:
        """验证设置场景命令
        
        Args:
            command: 设置场景命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.scene_name or not command.scene_name.strip():
            raise ValidationException("Scene name cannot be empty")
        
        if command.time_min is not None and (not isinstance(command.time_min, int) or command.time_min < 0):
            raise ValidationException("Time minutes must be a non-negative integer")
        
        if command.objectives is not None:
            if not isinstance(command.objectives, list):
                raise ValidationException("Objectives must be a list")
            
            for obj in command.objectives:
                if not isinstance(obj, str) or not obj.strip():
                    raise ValidationException("All objectives must be non-empty strings")
        
        if command.details is not None:
            if not isinstance(command.details, list):
                raise ValidationException("Details must be a list")
            
            for detail in command.details:
                if not isinstance(detail, str) or not detail.strip():
                    raise ValidationException("All details must be non-empty strings")
    
    def _validate_set_position_command(self, command: SetPositionCommand) -> None:
        """验证设置位置命令
        
        Args:
            command: 设置位置命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.character_name or not command.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not isinstance(command.x, int) or not isinstance(command.y, int):
            raise ValidationException("Position coordinates must be integers")
        
        if command.x < 0 or command.y < 0:
            raise ValidationException("Position coordinates must be non-negative")
    
    def _validate_set_relation_command(self, command: SetRelationCommand) -> None:
        """验证设置关系命令
        
        Args:
            command: 设置关系命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.source_character or not command.source_character.strip():
            raise ValidationException("Source character name cannot be empty")
        
        if not command.target_character or not command.target_character.strip():
            raise ValidationException("Target character name cannot be empty")
        
        if command.source_character == command.target_character:
            raise ValidationException("Source and target characters cannot be the same")
        
        if not isinstance(command.score, int) or command.score < -100 or command.score > 100:
            raise ValidationException("Relation score must be an integer between -100 and 100")
    
    def _validate_end_combat_command(self, command: EndCombatCommand) -> None:
        """验证结束战斗命令
        
        Args:
            command: 结束战斗命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 结束战斗命令通常不需要额外验证
        # reason字段可以为空
        pass
    
    def _validate_reset_world_command(self, command: ResetWorldCommand) -> None:
        """验证重置世界命令
        
        Args:
            command: 重置世界命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        valid_reset_types = ["full", "partial", "combat_only"]
        if command.reset_type not in valid_reset_types:
            raise ValidationException(f"Reset type must be one of: {', '.join(valid_reset_types)}")
        
        if not isinstance(command.preserve_characters, bool):
            raise ValidationException("Preserve characters must be a boolean")
        
        if not isinstance(command.preserve_relations, bool):
            raise ValidationException("Preserve relations must be a boolean")