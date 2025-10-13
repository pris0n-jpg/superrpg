"""
世界相关查询处理器

该模块实现了世界相关的查询处理器，遵循命令查询分离(CQS)模式，
符合SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

世界查询处理器负责：
1. 处理世界状态查询
2. 处理世界快照查询
3. 处理战斗状态查询
4. 处理回合状态查询
5. 处理环境信息查询
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..services.base import QueryHandler, QueryResult
from ...core.interfaces import Logger
from ...core.exceptions import ApplicationException, ValidationException
from ...domain.models.world import World
from ...domain.models.combat import Combat


# 世界相关查询
@dataclass
class GetWorldStateQuery:
    """获取世界状态查询"""
    include_characters: bool = True
    include_positions: bool = True
    include_relations: bool = True
    include_objectives: bool = True
    include_inventory: bool = False


@dataclass
class GetWorldSnapshotQuery:
    """获取世界快照查询"""
    timestamp: Optional[str] = None  # 如果为None，获取最新快照
    include_metadata: bool = True


@dataclass
class GetCombatStateQuery:
    """获取战斗状态查询"""
    include_participants: bool = True
    include_initiative: bool = True
    include_turn_states: bool = True


@dataclass
class GetTurnStateQuery:
    """获取回合状态查询"""
    character_name: Optional[str] = None  # 如果为None，获取当前回合状态


@dataclass
class GetEnvironmentInfoQuery:
    """获取环境信息查询"""
    include_weather: bool = True
    include_time: bool = True
    include_location: bool = True
    include_details: bool = True


# 世界查询结果
@dataclass
class WorldStateInfo:
    """世界状态信息"""
    location: str
    time_min: int
    weather: str
    character_count: int
    objective_count: int
    in_combat: bool
    round_number: Optional[int] = None


@dataclass
class CombatStateInfo:
    """战斗状态信息"""
    is_active: bool
    current_round: int
    current_actor: Optional[str]
    participants: List[str]
    initiative_order: List[str]
    combat_type: str


@dataclass
class TurnStateInfo:
    """回合状态信息"""
    character_name: str
    is_current_actor: bool
    has_acted: bool
    movement_remaining: Optional[float]
    reaction_available: bool
    turn_state: Dict[str, Any]


@dataclass
class EnvironmentInfo:
    """环境信息"""
    location: str
    time_formatted: str
    weather: str
    details: List[str]
    objectives: List[str]


# 世界查询处理器
class WorldQueryHandler(QueryHandler):
    """世界查询处理器
    
    负责处理所有世界相关的查询，包括世界状态、战斗状态、回合状态和环境信息查询。
    遵循单一职责原则，专门负责世界查询的处理。
    """
    
    def __init__(self, game_engine, logger: Logger):
        """初始化世界查询处理器
        
        Args:
            game_engine: 游戏引擎服务
            logger: 日志记录器
        """
        self._game_engine = game_engine
        self._logger = logger
    
    def handle(self, query: Any) -> QueryResult:
        """处理查询
        
        Args:
            query: 要处理的查询
            
        Returns:
            QueryResult: 查询结果
        """
        try:
            if isinstance(query, GetWorldStateQuery):
                return self._handle_get_world_state(query)
            elif isinstance(query, GetWorldSnapshotQuery):
                return self._handle_get_world_snapshot(query)
            elif isinstance(query, GetCombatStateQuery):
                return self._handle_get_combat_state(query)
            elif isinstance(query, GetTurnStateQuery):
                return self._handle_get_turn_state(query)
            elif isinstance(query, GetEnvironmentInfoQuery):
                return self._handle_get_environment_info(query)
            else:
                raise ApplicationException(f"Unsupported query type: {type(query).__name__}")
                
        except ValidationException as e:
            self._logger.warning(f"Query validation failed: {e}")
            raise
        except Exception as e:
            self._logger.error(f"Query handling failed: {e}")
            raise ApplicationException(f"Query handling failed: {str(e)}", cause=e)
    
    def can_handle(self, query_type: type) -> bool:
        """检查是否能处理指定类型的查询
        
        Args:
            query_type: 查询类型
            
        Returns:
            bool: 是否能处理
        """
        return query_type in {
            GetWorldStateQuery,
            GetWorldSnapshotQuery,
            GetCombatStateQuery,
            GetTurnStateQuery,
            GetEnvironmentInfoQuery
        }
    
    def _handle_get_world_state(self, query: GetWorldStateQuery) -> QueryResult[WorldStateInfo]:
        """处理获取世界状态查询
        
        Args:
            query: 获取世界状态查询
            
        Returns:
            QueryResult[WorldStateInfo]: 世界状态查询结果
        """
        try:
            self._logger.info("Getting world state")
            
            # 验证查询
            self._validate_get_world_state_query(query)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 构建世界状态信息
            character_count = len(world.characters) if query.include_characters else 0
            objective_count = len(world.objectives) if query.include_objectives else 0
            
            world_state_info = WorldStateInfo(
                location=world.location,
                time_min=world.time_min,
                weather=world.weather,
                character_count=character_count,
                objective_count=objective_count,
                in_combat=world.is_in_combat,
                round_number=world.combat.current_round if world.combat and world.is_in_combat else None
            )
            
            self._logger.info("World state retrieved")
            
            return QueryResult.create(
                [world_state_info],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"World state retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_world_snapshot(self, query: GetWorldSnapshotQuery) -> QueryResult[Dict[str, Any]]:
        """处理获取世界快照查询
        
        Args:
            query: 获取世界快照查询
            
        Returns:
            QueryResult[Dict[str, Any]]: 世界快照查询结果
        """
        try:
            self._logger.info(f"Getting world snapshot: {query.timestamp or 'latest'}")
            
            # 验证查询
            self._validate_get_world_snapshot_query(query)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 获取快照
            snapshot = world.snapshot()
            
            # 如果不需要元数据，移除元数据字段
            if not query.include_metadata:
                snapshot.pop('created_at', None)
                snapshot.pop('id', None)
            
            self._logger.info("World snapshot retrieved")
            
            return QueryResult.create(
                [snapshot],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"World snapshot retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_combat_state(self, query: GetCombatStateQuery) -> QueryResult[CombatStateInfo]:
        """处理获取战斗状态查询
        
        Args:
            query: 获取战斗状态查询
            
        Returns:
            QueryResult[CombatStateInfo]: 战斗状态查询结果
        """
        try:
            self._logger.info("Getting combat state")
            
            # 验证查询
            self._validate_get_combat_state_query(query)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world or not world.is_in_combat or not world.combat:
                # 返回非战斗状态
                combat_state_info = CombatStateInfo(
                    is_active=False,
                    current_round=0,
                    current_actor=None,
                    participants=[],
                    initiative_order=[],
                    combat_type="none"
                )
                
                return QueryResult.create(
                    [combat_state_info],
                    page_number=1,
                    page_size=1,
                    total_count=1
                )
            
            combat = world.combat
            
            # 构建战斗状态信息
            participants = list(combat.participants) if query.include_participants else []
            initiative_order = list(combat.initiative_order) if query.include_initiative else []
            
            combat_state_info = CombatStateInfo(
                is_active=combat.is_active,
                current_round=combat.current_round,
                current_actor=combat.current_actor,
                participants=participants,
                initiative_order=initiative_order,
                combat_type=combat.combat_type
            )
            
            self._logger.info("Combat state retrieved")
            
            return QueryResult.create(
                [combat_state_info],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Combat state retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_turn_state(self, query: GetTurnStateQuery) -> QueryResult[TurnStateInfo]:
        """处理获取回合状态查询
        
        Args:
            query: 获取回合状态查询
            
        Returns:
            QueryResult[TurnStateInfo]: 回合状态查询结果
        """
        try:
            character_name = query.character_name or "current"
            self._logger.info(f"Getting turn state: {character_name}")
            
            # 验证查询
            self._validate_get_turn_state_query(query)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world or not world.is_in_combat or not world.combat:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            combat = world.combat
            
            # 确定要查询的角色名称
            target_character = query.character_name or combat.current_actor
            if not target_character:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 获取回合状态
            turn_state = combat.turn_states.get(target_character)
            if not turn_state:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 构建回合状态信息
            turn_state_info = TurnStateInfo(
                character_name=target_character,
                is_current_actor=(combat.current_actor == target_character),
                has_acted=turn_state.has_acted,
                movement_remaining=turn_state.movement_remaining,
                reaction_available=turn_state.reaction_available,
                turn_state=turn_state.__dict__
            )
            
            self._logger.info(f"Turn state retrieved: {target_character}")
            
            return QueryResult.create(
                [turn_state_info],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Turn state retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_environment_info(self, query: GetEnvironmentInfoQuery) -> QueryResult[EnvironmentInfo]:
        """处理获取环境信息查询
        
        Args:
            query: 获取环境信息查询
            
        Returns:
            QueryResult[EnvironmentInfo]: 环境信息查询结果
        """
        try:
            self._logger.info("Getting environment info")
            
            # 验证查询
            self._validate_get_environment_info_query(query)
            
            # 获取当前世界
            world = self._game_engine.get_current_world()
            if not world:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 格式化时间
            time_formatted = self._format_time(world.time_min)
            
            # 构建环境信息
            environment_info = EnvironmentInfo(
                location=world.location if query.include_location else "",
                time_formatted=time_formatted if query.include_time else "",
                weather=world.weather if query.include_weather else "",
                details=list(world.scene_details) if query.include_details else [],
                objectives=list(world.objectives) if query.include_details else []
            )
            
            self._logger.info("Environment info retrieved")
            
            return QueryResult.create(
                [environment_info],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Environment info retrieval failed: {str(e)}", cause=e)
    
    def _validate_get_world_state_query(self, query: GetWorldStateQuery) -> None:
        """验证获取世界状态查询
        
        Args:
            query: 获取世界状态查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not isinstance(query.include_characters, bool):
            raise ValidationException("Include characters must be a boolean")
        
        if not isinstance(query.include_positions, bool):
            raise ValidationException("Include positions must be a boolean")
        
        if not isinstance(query.include_relations, bool):
            raise ValidationException("Include relations must be a boolean")
        
        if not isinstance(query.include_objectives, bool):
            raise ValidationException("Include objectives must be a boolean")
        
        if not isinstance(query.include_inventory, bool):
            raise ValidationException("Include inventory must be a boolean")
    
    def _validate_get_world_snapshot_query(self, query: GetWorldSnapshotQuery) -> None:
        """验证获取世界快照查询
        
        Args:
            query: 获取世界快照查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if query.timestamp is not None and not isinstance(query.timestamp, str):
            raise ValidationException("Timestamp must be a string")
        
        if not isinstance(query.include_metadata, bool):
            raise ValidationException("Include metadata must be a boolean")
    
    def _validate_get_combat_state_query(self, query: GetCombatStateQuery) -> None:
        """验证获取战斗状态查询
        
        Args:
            query: 获取战斗状态查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not isinstance(query.include_participants, bool):
            raise ValidationException("Include participants must be a boolean")
        
        if not isinstance(query.include_initiative, bool):
            raise ValidationException("Include initiative must be a boolean")
        
        if not isinstance(query.include_turn_states, bool):
            raise ValidationException("Include turn states must be a boolean")
    
    def _validate_get_turn_state_query(self, query: GetTurnStateQuery) -> None:
        """验证获取回合状态查询
        
        Args:
            query: 获取回合状态查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if query.character_name is not None and not isinstance(query.character_name, str):
            raise ValidationException("Character name must be a string")
    
    def _validate_get_environment_info_query(self, query: GetEnvironmentInfoQuery) -> None:
        """验证获取环境信息查询
        
        Args:
            query: 获取环境信息查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not isinstance(query.include_weather, bool):
            raise ValidationException("Include weather must be a boolean")
        
        if not isinstance(query.include_time, bool):
            raise ValidationException("Include time must be a boolean")
        
        if not isinstance(query.include_location, bool):
            raise ValidationException("Include location must be a boolean")
        
        if not isinstance(query.include_details, bool):
            raise ValidationException("Include details must be a boolean")
    
    
    def _format_time(self, time_min: int) -> str:
        """格式化时间
        
        Args:
            time_min: 时间（分钟）
            
        Returns:
            str: 格式化后的时间字符串
        """
        try:
            hours = time_min // 60
            minutes = time_min % 60
            return f"{hours:02d}:{minutes:02d}"
        except (ValueError, TypeError):
            return "未知时间"