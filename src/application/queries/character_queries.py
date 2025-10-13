"""
角色相关查询处理器

该模块实现了角色相关的查询处理器，遵循命令查询分离(CQS)模式，
符合SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

角色查询处理器负责：
1. 处理角色信息查询
2. 处理角色位置查询
3. 处理角色关系查询
4. 处理角色物品查询
5. 处理角色目标查询
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..services.base import QueryHandler, QueryResult
from ...core.interfaces import Logger
from ...core.exceptions import ApplicationException, ValidationException
from ...domain.models.characters import Character
from ...domain.models.items import Item
from ...domain.models.objectives import Objective
from ...domain.models.relations import Relation


# 角色相关查询
@dataclass
class GetCharacterQuery:
    """获取角色查询"""
    character_name: str


@dataclass
class GetCharacterPositionQuery:
    """获取角色位置查询"""
    character_name: str


@dataclass
class GetCharacterRelationsQuery:
    """获取角色关系查询"""
    character_name: str
    include_mutual: bool = True


@dataclass
class GetCharacterInventoryQuery:
    """获取角色物品查询"""
    character_name: str
    item_type: Optional[str] = None


@dataclass
class GetCharacterObjectivesQuery:
    """获取角色目标查询"""
    character_name: str
    status_filter: Optional[str] = None  # active, completed, failed, all


@dataclass
class GetAllCharactersQuery:
    """获取所有角色查询"""
    include_dead: bool = True
    include_npc: bool = True
    include_pc: bool = True


# 角色查询结果
@dataclass
class CharacterInfo:
    """角色信息"""
    name: str
    hp: int
    max_hp: int
    abilities: Dict[str, int]
    position: Optional[Tuple[int, int]]
    is_alive: bool
    proficient_skills: List[str]
    proficient_saves: List[str]


@dataclass
class CharacterRelationInfo:
    """角色关系信息"""
    target_character: str
    strength: int
    relation_type: str
    description: str
    is_mutual: bool


@dataclass
class CharacterInventoryInfo:
    """角色物品信息"""
    item_name: str
    quantity: int
    item_type: Optional[str]
    description: Optional[str]


@dataclass
class CharacterObjectiveInfo:
    """角色目标信息"""
    objective_id: str
    description: str
    status: str
    progress: float
    assigned_at: Optional[str]


# 角色查询处理器
class CharacterQueryHandler(QueryHandler):
    """角色查询处理器
    
    负责处理所有角色相关的查询，包括角色信息、位置、关系、物品和目标查询。
    遵循单一职责原则，专门负责角色查询的处理。
    """
    
    def __init__(self, logger: Logger):
        """初始化角色查询处理器
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
    
    def handle(self, query: Any) -> QueryResult:
        """处理查询
        
        Args:
            query: 要处理的查询
            
        Returns:
            QueryResult: 查询结果
        """
        try:
            if isinstance(query, GetCharacterQuery):
                return self._handle_get_character(query)
            elif isinstance(query, GetCharacterPositionQuery):
                return self._handle_get_character_position(query)
            elif isinstance(query, GetCharacterRelationsQuery):
                return self._handle_get_character_relations(query)
            elif isinstance(query, GetCharacterInventoryQuery):
                return self._handle_get_character_inventory(query)
            elif isinstance(query, GetCharacterObjectivesQuery):
                return self._handle_get_character_objectives(query)
            elif isinstance(query, GetAllCharactersQuery):
                return self._handle_get_all_characters(query)
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
            GetCharacterQuery,
            GetCharacterPositionQuery,
            GetCharacterRelationsQuery,
            GetCharacterInventoryQuery,
            GetCharacterObjectivesQuery,
            GetAllCharactersQuery
        }
    
    def _handle_get_character(self, query: GetCharacterQuery) -> QueryResult[CharacterInfo]:
        """处理获取角色查询
        
        Args:
            query: 获取角色查询
            
        Returns:
            QueryResult[CharacterInfo]: 角色信息查询结果
        """
        try:
            self._logger.info(f"Getting character: {query.character_name}")
            
            # 验证查询
            self._validate_get_character_query(query)
            
            # 获取角色（这里需要从某个地方获取角色对象）
            # 实际实现中可能需要通过仓储或其他方式获取
            character = self._get_character_by_name(query.character_name)
            if not character:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 构建角色信息
            character_info = CharacterInfo(
                name=character.name,
                hp=character.hp,
                max_hp=character.max_hp,
                abilities=character.abilities.__dict__,
                position=character.position.to_tuple() if character.position else None,
                is_alive=character.is_alive,
                proficient_skills=character.proficient_skills.copy(),
                proficient_saves=character.proficient_saves.copy()
            )
            
            self._logger.info(f"Character retrieved: {query.character_name}")
            
            return QueryResult.create(
                [character_info],
                page_number=1,
                page_size=1,
                total_count=1
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Character retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_character_position(self, query: GetCharacterPositionQuery) -> QueryResult[Tuple[int, int]]:
        """处理获取角色位置查询
        
        Args:
            query: 获取角色位置查询
            
        Returns:
            QueryResult[Tuple[int, int]]: 角色位置查询结果
        """
        try:
            self._logger.info(f"Getting character position: {query.character_name}")
            
            # 验证查询
            self._validate_get_character_position_query(query)
            
            # 获取角色
            character = self._get_character_by_name(query.character_name)
            if not character:
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
            # 获取位置
            position = character.position.to_tuple() if character.position else None
            
            if position:
                self._logger.info(f"Character position retrieved: {query.character_name} -> {position}")
                
                return QueryResult.create(
                    [position],
                    page_number=1,
                    page_size=1,
                    total_count=1
                )
            else:
                self._logger.warning(f"Character {query.character_name} has no position")
                
                return QueryResult.create([], page_number=1, page_size=1, total_count=0)
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Character position retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_character_relations(self, query: GetCharacterRelationsQuery) -> QueryResult[CharacterRelationInfo]:
        """处理获取角色关系查询
        
        Args:
            query: 获取角色关系查询
            
        Returns:
            QueryResult[CharacterRelationInfo]: 角色关系查询结果
        """
        try:
            self._logger.info(f"Getting character relations: {query.character_name}")
            
            # 验证查询
            self._validate_get_character_relations_query(query)
            
            # 获取角色
            character = self._get_character_by_name(query.character_name)
            if not character:
                return QueryResult.create([], page_number=1, page_size=50, total_count=0)
            
            # 获取关系（这里需要通过某种方式获取关系）
            # 实际实现中需要通过关系网络或其他服务获取
            relations = self._get_character_relations(character.name, query.include_mutual)
            
            # 构建关系信息
            relation_infos = []
            for relation in relations:
                relation_info = CharacterRelationInfo(
                    target_character=relation.target,
                    strength=relation.strength,
                    relation_type=self._get_relation_type(relation.strength),
                    description=relation.description or "",
                    is_mutual=relation.mutual
                )
                relation_infos.append(relation_info)
            
            self._logger.info(f"Character relations retrieved: {query.character_name} -> {len(relation_infos)} relations")
            
            return QueryResult.create(
                relation_infos,
                page_number=1,
                page_size=len(relation_infos),
                total_count=len(relation_infos)
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Character relations retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_character_inventory(self, query: GetCharacterInventoryQuery) -> QueryResult[CharacterInventoryInfo]:
        """处理获取角色物品查询
        
        Args:
            query: 获取角色物品查询
            
        Returns:
            QueryResult[CharacterInventoryInfo]: 角色物品查询结果
        """
        try:
            self._logger.info(f"Getting character inventory: {query.character_name}")
            
            # 验证查询
            self._validate_get_character_inventory_query(query)
            
            # 获取角色
            character = self._get_character_by_name(query.character_name)
            if not character:
                return QueryResult.create([], page_number=1, page_size=50, total_count=0)
            
            # 获取物品栏
            inventory = character.inventory
            
            # 构建物品信息
            inventory_infos = []
            for item_name, quantity in inventory.items.items():
                if query.item_type is None or self._get_item_type(item_name) == query.item_type:
                    inventory_info = CharacterInventoryInfo(
                        item_name=item_name,
                        quantity=quantity,
                        item_type=self._get_item_type(item_name),
                        description=self._get_item_description(item_name)
                    )
                    inventory_infos.append(inventory_info)
            
            self._logger.info(f"Character inventory retrieved: {query.character_name} -> {len(inventory_infos)} items")
            
            return QueryResult.create(
                inventory_infos,
                page_number=1,
                page_size=len(inventory_infos),
                total_count=len(inventory_infos)
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Character inventory retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_character_objectives(self, query: GetCharacterObjectivesQuery) -> QueryResult[CharacterObjectiveInfo]:
        """处理获取角色目标查询
        
        Args:
            query: 获取角色目标查询
            
        Returns:
            QueryResult[CharacterObjectiveInfo]: 角色目标查询结果
        """
        try:
            self._logger.info(f"Getting character objectives: {query.character_name}")
            
            # 验证查询
            self._validate_get_character_objectives_query(query)
            
            # 获取角色
            character = self._get_character_by_name(query.character_name)
            if not character:
                return QueryResult.create([], page_number=1, page_size=50, total_count=0)
            
            # 获取目标（这里需要通过某种方式获取目标）
            # 实际实现中需要通过目标跟踪器或其他服务获取
            objectives = self._get_character_objectives(character.name, query.status_filter)
            
            # 构建目标信息
            objective_infos = []
            for objective in objectives:
                objective_info = CharacterObjectiveInfo(
                    objective_id=objective.id,
                    description=objective.description,
                    status=objective.status,
                    progress=objective.progress,
                    assigned_at=objective.assigned_at.isoformat() if objective.assigned_at else None
                )
                objective_infos.append(objective_info)
            
            self._logger.info(f"Character objectives retrieved: {query.character_name} -> {len(objective_infos)} objectives")
            
            return QueryResult.create(
                objective_infos,
                page_number=1,
                page_size=len(objective_infos),
                total_count=len(objective_infos)
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"Character objectives retrieval failed: {str(e)}", cause=e)
    
    def _handle_get_all_characters(self, query: GetAllCharactersQuery) -> QueryResult[CharacterInfo]:
        """处理获取所有角色查询
        
        Args:
            query: 获取所有角色查询
            
        Returns:
            QueryResult[CharacterInfo]: 所有角色查询结果
        """
        try:
            self._logger.info("Getting all characters")
            
            # 验证查询
            self._validate_get_all_characters_query(query)
            
            # 获取所有角色（这里需要通过某种方式获取角色列表）
            # 实际实现中需要通过仓储或其他方式获取
            characters = self._get_all_characters_filtered(
                query.include_dead,
                query.include_npc,
                query.include_pc
            )
            
            # 构建角色信息
            character_infos = []
            for character in characters:
                character_info = CharacterInfo(
                    name=character.name,
                    hp=character.hp,
                    max_hp=character.max_hp,
                    abilities=character.abilities.__dict__,
                    position=character.position.to_tuple() if character.position else None,
                    is_alive=character.is_alive,
                    proficient_skills=character.proficient_skills.copy(),
                    proficient_saves=character.proficient_saves.copy()
                )
                character_infos.append(character_info)
            
            self._logger.info(f"All characters retrieved: {len(character_infos)} characters")
            
            return QueryResult.create(
                character_infos,
                page_number=1,
                page_size=len(character_infos),
                total_count=len(character_infos)
            )
            
        except ValidationException as e:
            raise
        except Exception as e:
            raise ApplicationException(f"All characters retrieval failed: {str(e)}", cause=e)
    
    def _validate_get_character_query(self, query: GetCharacterQuery) -> None:
        """验证获取角色查询
        
        Args:
            query: 获取角色查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not query.character_name or not query.character_name.strip():
            raise ValidationException("Character name cannot be empty")
    
    def _validate_get_character_position_query(self, query: GetCharacterPositionQuery) -> None:
        """验证获取角色位置查询
        
        Args:
            query: 获取角色位置查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not query.character_name or not query.character_name.strip():
            raise ValidationException("Character name cannot be empty")
    
    def _validate_get_character_relations_query(self, query: GetCharacterRelationsQuery) -> None:
        """验证获取角色关系查询
        
        Args:
            query: 获取角色关系查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not query.character_name or not query.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not isinstance(query.include_mutual, bool):
            raise ValidationException("Include mutual must be a boolean")
    
    def _validate_get_character_inventory_query(self, query: GetCharacterInventoryQuery) -> None:
        """验证获取角色物品查询
        
        Args:
            query: 获取角色物品查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not query.character_name or not query.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if query.item_type is not None and not isinstance(query.item_type, str):
            raise ValidationException("Item type must be a string")
    
    def _validate_get_character_objectives_query(self, query: GetCharacterObjectivesQuery) -> None:
        """验证获取角色目标查询
        
        Args:
            query: 获取角色目标查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not query.character_name or not query.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if query.status_filter is not None:
            valid_statuses = ["active", "completed", "failed", "all"]
            if query.status_filter not in valid_statuses:
                raise ValidationException(f"Status filter must be one of: {', '.join(valid_statuses)}")
    
    def _validate_get_all_characters_query(self, query: GetAllCharactersQuery) -> None:
        """验证获取所有角色查询
        
        Args:
            query: 获取所有角色查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not isinstance(query.include_dead, bool):
            raise ValidationException("Include dead must be a boolean")
        
        if not isinstance(query.include_npc, bool):
            raise ValidationException("Include NPC must be a boolean")
        
        if not isinstance(query.include_pc, bool):
            raise ValidationException("Include PC must be a boolean")
    
    def _get_character_by_name(self, name: str) -> Optional[Character]:
        """根据名称获取角色
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Character]: 角色对象，如果不存在则返回None
        """
        # 这里应该通过某种方式获取角色，例如从仓储或世界对象
        # 简化实现，返回None
        # 实际实现中需要依赖注入仓储或其他服务
        return None
    
    def _get_character_relations(self, character_name: str, include_mutual: bool) -> List[Relation]:
        """获取角色关系
        
        Args:
            character_name: 角色名称
            include_mutual: 是否包含相互关系
            
        Returns:
            List[Relation]: 关系列表
        """
        # 这里应该通过某种方式获取关系，例如从关系网络
        # 简化实现，返回空列表
        # 实际实现中需要依赖注入关系网络或其他服务
        return []
    
    def _get_character_objectives(self, character_name: str, status_filter: Optional[str]) -> List[Objective]:
        """获取角色目标
        
        Args:
            character_name: 角色名称
            status_filter: 状态过滤器
            
        Returns:
            List[Objective]: 目标列表
        """
        # 这里应该通过某种方式获取目标，例如从目标跟踪器
        # 简化实现，返回空列表
        # 实际实现中需要依赖注入目标跟踪器或其他服务
        return []
    
    def _get_all_characters_filtered(self, include_dead: bool, include_npc: bool, include_pc: bool) -> List[Character]:
        """获取过滤后的所有角色
        
        Args:
            include_dead: 是否包含死亡角色
            include_npc: 是否包含NPC
            include_pc: 是否包含PC
            
        Returns:
            List[Character]: 角色列表
        """
        # 这里应该通过某种方式获取角色，例如从仓储
        # 简化实现，返回空列表
        # 实际实现中需要依赖注入仓储或其他服务
        return []
    
    def _get_relation_type(self, strength: int) -> str:
        """根据强度获取关系类型
        
        Args:
            strength: 关系强度
            
        Returns:
            str: 关系类型
        """
        if strength >= 60:
            return "挚友"
        elif strength >= 40:
            return "亲密同伴"
        elif strength >= 10:
            return "盟友"
        elif strength <= -60:
            return "死敌"
        elif strength <= -40:
            return "仇视"
        elif strength <= -10:
            return "敌对"
        else:
            return "中立"
    
    def _get_item_type(self, item_name: str) -> str:
        """获取物品类型
        
        Args:
            item_name: 物品名称
            
        Returns:
            str: 物品类型
        """
        # 简化实现，返回默认类型
        # 实际实现中可能需要从物品定义或配置中获取
        return "unknown"
    
    def _get_item_description(self, item_name: str) -> str:
        """获取物品描述
        
        Args:
            item_name: 物品名称
            
        Returns:
            str: 物品描述
        """
        # 简化实现，返回空描述
        # 实际实现中可能需要从物品定义或配置中获取
        return ""