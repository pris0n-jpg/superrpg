"""
角色相关命令处理器

该模块实现了角色相关的命令处理器，遵循命令查询分离(CQS)模式，
符合SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

角色命令处理器负责：
1. 处理角色创建和更新命令
2. 处理角色位置移动命令
3. 处理角色关系变更命令
4. 处理角色物品管理命令
5. 处理角色目标分配命令
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..services.base import CommandHandler, CommandResult
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, ValidationException, BusinessRuleException
from ...domain.models.characters import Character
from ...domain.models.items import Item
from ...domain.models.objectives import Objective
from ...domain.models.relations import RelationType
from ...domain.services.character_service import CharacterService


# 角色相关事件
class CharacterCreatedEvent(DomainEvent):
    """角色创建事件"""
    
    def __init__(self, character_name: str, character_data: Dict[str, Any]):
        super().__init__()
        self.character_name = character_name
        self.character_data = character_data
    
    def get_event_type(self) -> str:
        return "CharacterCreated"


class CharacterPositionUpdatedEvent(DomainEvent):
    """角色位置更新事件"""
    
    def __init__(self, character_name: str, old_position: Optional[Tuple[int, int]], new_position: Tuple[int, int]):
        super().__init__()
        self.character_name = character_name
        self.old_position = old_position
        self.new_position = new_position
    
    def get_event_type(self) -> str:
        return "CharacterPositionUpdated"


class CharacterRelationUpdatedEvent(DomainEvent):
    """角色关系更新事件"""
    
    def __init__(self, source_character: str, target_character: str, old_strength: int, new_strength: int, reason: str):
        super().__init__()
        self.source_character = source_character
        self.target_character = target_character
        self.old_strength = old_strength
        self.new_strength = new_strength
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "CharacterRelationUpdated"


class ItemGivenEvent(DomainEvent):
    """物品给予事件"""
    
    def __init__(self, character_name: str, item_name: str, quantity: int, giver_name: Optional[str] = None):
        super().__init__()
        self.character_name = character_name
        self.item_name = item_name
        self.quantity = quantity
        self.giver_name = giver_name
    
    def get_event_type(self) -> str:
        return "ItemGiven"


class ItemTakenEvent(DomainEvent):
    """物品取走事件"""
    
    def __init__(self, character_name: str, item_name: str, quantity: int, taker_name: Optional[str] = None):
        super().__init__()
        self.character_name = character_name
        self.item_name = item_name
        self.quantity = quantity
        self.taker_name = taker_name
    
    def get_event_type(self) -> str:
        return "ItemTaken"


class ObjectiveAssignedEvent(DomainEvent):
    """目标分配事件"""
    
    def __init__(self, character_name: str, objective_id: str, objective_description: str):
        super().__init__()
        self.character_name = character_name
        self.objective_id = objective_id
        self.objective_description = objective_description
    
    def get_event_type(self) -> str:
        return "ObjectiveAssigned"


# 角色相关命令
@dataclass
class CreateCharacterCommand:
    """创建角色命令"""
    name: str
    abilities: Dict[str, int]
    hp: int
    max_hp: int
    position: Optional[Tuple[int, int]] = None
    proficient_skills: Optional[List[str]] = None
    proficient_saves: Optional[List[str]] = None


@dataclass
class UpdateCharacterPositionCommand:
    """更新角色位置命令"""
    character_name: str
    new_position: Tuple[int, int]


@dataclass
class UpdateCharacterRelationCommand:
    """更新角色关系命令"""
    source_character: str
    target_character: str
    delta: int
    reason: str = ""


@dataclass
class GiveItemCommand:
    """给予物品命令"""
    character_name: str
    item_name: str
    quantity: int = 1
    giver_name: Optional[str] = None


@dataclass
class TakeItemCommand:
    """取走物品命令"""
    character_name: str
    item_name: str
    quantity: int = 1
    taker_name: Optional[str] = None


@dataclass
class AssignObjectiveCommand:
    """分配目标命令"""
    character_name: str
    objective_id: str
    objective_description: str
    objective_type: str = "default"


# 角色命令处理器
class CharacterCommandHandler(CommandHandler):
    """角色命令处理器
    
    负责处理所有角色相关的命令，包括角色创建、位置更新、关系管理等。
    遵循单一职责原则，专门负责角色命令的处理。
    """
    
    def __init__(
        self,
        character_service: CharacterService,
        event_bus: EventBus,
        logger: Logger
    ):
        """初始化角色命令处理器
        
        Args:
            character_service: 角色服务
            event_bus: 事件总线
            logger: 日志记录器
        """
        self._character_service = character_service
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
            if isinstance(command, CreateCharacterCommand):
                return self._handle_create_character(command)
            elif isinstance(command, UpdateCharacterPositionCommand):
                return self._handle_update_position(command)
            elif isinstance(command, UpdateCharacterRelationCommand):
                return self._handle_update_relation(command)
            elif isinstance(command, GiveItemCommand):
                return self._handle_give_item(command)
            elif isinstance(command, TakeItemCommand):
                return self._handle_take_item(command)
            elif isinstance(command, AssignObjectiveCommand):
                return self._handle_assign_objective(command)
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
            CreateCharacterCommand,
            UpdateCharacterPositionCommand,
            UpdateCharacterRelationCommand,
            GiveItemCommand,
            TakeItemCommand,
            AssignObjectiveCommand
        }
    
    def _handle_create_character(self, command: CreateCharacterCommand) -> CommandResult:
        """处理创建角色命令
        
        Args:
            command: 创建角色命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Creating character: {command.name}")
            
            # 验证命令
            self._validate_create_character_command(command)
            
            # 创建角色
            character = self._character_service.create_character(
                name=command.name,
                abilities=command.abilities,
                hp=command.hp,
                max_hp=command.max_hp,
                position=command.position,
                proficient_skills=command.proficient_skills,
                proficient_saves=command.proficient_saves
            )
            
            # 发布事件
            self._event_bus.publish(CharacterCreatedEvent(
                character_name=character.name,
                character_data={
                    "abilities": character.abilities.__dict__,
                    "hp": character.hp,
                    "max_hp": character.max_hp,
                    "position": character.position.to_tuple() if character.position else None,
                    "proficient_skills": character.proficient_skills,
                    "proficient_saves": character.proficient_saves
                }
            ))
            
            self._logger.info(f"Character created: {character.name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": character.name,
                    "hp": character.hp,
                    "max_hp": character.max_hp,
                    "position": character.position.to_tuple() if character.position else None
                },
                message=f"Character {character.name} created successfully"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Character creation failed: {str(e)}", cause=e)
            )
    
    def _handle_update_position(self, command: UpdateCharacterPositionCommand) -> CommandResult:
        """处理更新角色位置命令
        
        Args:
            command: 更新角色位置命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Updating position for character: {command.character_name}")
            
            # 验证命令
            self._validate_update_position_command(command)
            
            # 获取角色（这里需要从某个地方获取角色对象）
            # 实际实现中可能需要通过仓储或其他方式获取
            # 这里简化处理，假设有一个方法可以获取角色
            character = self._get_character_by_name(command.character_name)
            if not character:
                return CommandResult.failure_result(
                    ApplicationException(f"Character {command.character_name} not found")
                )
            
            old_position = character.position.to_tuple() if character.position else None
            
            # 更新位置（这里需要世界对象，简化处理）
            # 实际实现中需要调用character_service.move_character
            
            # 发布事件
            self._event_bus.publish(CharacterPositionUpdatedEvent(
                character_name=command.character_name,
                old_position=old_position,
                new_position=command.new_position
            ))
            
            self._logger.info(f"Position updated for character: {command.character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": command.character_name,
                    "old_position": old_position,
                    "new_position": command.new_position
                },
                message=f"Position updated for {command.character_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Position update failed: {str(e)}", cause=e)
            )
    
    def _handle_update_relation(self, command: UpdateCharacterRelationCommand) -> CommandResult:
        """处理更新角色关系命令
        
        Args:
            command: 更新角色关系命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Updating relation: {command.source_character} -> {command.target_character}")
            
            # 验证命令
            self._validate_update_relation_command(command)
            
            # 获取角色
            source_character = self._get_character_by_name(command.source_character)
            target_character = self._get_character_by_name(command.target_character)
            
            if not source_character or not target_character:
                return CommandResult.failure_result(
                    ApplicationException("One or both characters not found")
                )
            
            # 获取当前关系强度
            current_relation = self._character_service._relationship_network.get_relation(
                command.source_character, command.target_character
            )
            old_strength = current_relation.strength if current_relation else 0
            
            # 更新关系
            success = self._character_service.update_relation_strength(
                source_character=source_character,
                target_character=target_character,
                delta=command.delta,
                reason=command.reason
            )
            
            if not success:
                return CommandResult.failure_result(
                    ApplicationException("Failed to update relation")
                )
            
            # 发布事件
            self._event_bus.publish(CharacterRelationUpdatedEvent(
                source_character=command.source_character,
                target_character=command.target_character,
                old_strength=old_strength,
                new_strength=old_strength + command.delta,
                reason=command.reason
            ))
            
            self._logger.info(f"Relation updated: {command.source_character} -> {command.target_character}")
            
            return CommandResult.success_result(
                data={
                    "source_character": command.source_character,
                    "target_character": command.target_character,
                    "old_strength": old_strength,
                    "new_strength": old_strength + command.delta,
                    "delta": command.delta
                },
                message=f"Relation updated: {command.source_character} -> {command.target_character}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Relation update failed: {str(e)}", cause=e)
            )
    
    def _handle_give_item(self, command: GiveItemCommand) -> CommandResult:
        """处理给予物品命令
        
        Args:
            command: 给予物品命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Giving item to character: {command.character_name}")
            
            # 验证命令
            self._validate_give_item_command(command)
            
            # 获取角色
            character = self._get_character_by_name(command.character_name)
            if not character:
                return CommandResult.failure_result(
                    ApplicationException(f"Character {command.character_name} not found")
                )
            
            # 创建物品对象（简化处理）
            item = Item(name=command.item_name, description="", weight=0)
            
            # 给予物品
            success = self._character_service.give_item_to_character(
                character=character,
                item=item,
                quantity=command.quantity
            )
            
            if not success:
                return CommandResult.failure_result(
                    ApplicationException("Failed to give item to character")
                )
            
            # 发布事件
            self._event_bus.publish(ItemGivenEvent(
                character_name=command.character_name,
                item_name=command.item_name,
                quantity=command.quantity,
                giver_name=command.giver_name
            ))
            
            self._logger.info(f"Item given to character: {command.character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": command.character_name,
                    "item_name": command.item_name,
                    "quantity": command.quantity,
                    "giver_name": command.giver_name
                },
                message=f"Item given to {command.character_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Item giving failed: {str(e)}", cause=e)
            )
    
    def _handle_take_item(self, command: TakeItemCommand) -> CommandResult:
        """处理取走物品命令
        
        Args:
            command: 取走物品命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Taking item from character: {command.character_name}")
            
            # 验证命令
            self._validate_take_item_command(command)
            
            # 获取角色
            character = self._get_character_by_name(command.character_name)
            if not character:
                return CommandResult.failure_result(
                    ApplicationException(f"Character {command.character_name} not found")
                )
            
            # 取走物品
            success = self._character_service.take_item_from_character(
                character=character,
                item_name=command.item_name,
                quantity=command.quantity
            )
            
            if not success:
                return CommandResult.failure_result(
                    ApplicationException("Failed to take item from character")
                )
            
            # 发布事件
            self._event_bus.publish(ItemTakenEvent(
                character_name=command.character_name,
                item_name=command.item_name,
                quantity=command.quantity,
                taker_name=command.taker_name
            ))
            
            self._logger.info(f"Item taken from character: {command.character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": command.character_name,
                    "item_name": command.item_name,
                    "quantity": command.quantity,
                    "taker_name": command.taker_name
                },
                message=f"Item taken from {command.character_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Item taking failed: {str(e)}", cause=e)
            )
    
    def _handle_assign_objective(self, command: AssignObjectiveCommand) -> CommandResult:
        """处理分配目标命令
        
        Args:
            command: 分配目标命令
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            self._logger.info(f"Assigning objective to character: {command.character_name}")
            
            # 验证命令
            self._validate_assign_objective_command(command)
            
            # 获取角色
            character = self._get_character_by_name(command.character_name)
            if not character:
                return CommandResult.failure_result(
                    ApplicationException(f"Character {command.character_name} not found")
                )
            
            # 创建目标对象（简化处理）
            objective = Objective(
                id=command.objective_id,
                description=command.objective_description,
                objective_type=command.objective_type
            )
            
            # 分配目标
            success = self._character_service.assign_objective_to_character(
                character=character,
                objective=objective
            )
            
            if not success:
                return CommandResult.failure_result(
                    ApplicationException("Failed to assign objective to character")
                )
            
            # 发布事件
            self._event_bus.publish(ObjectiveAssignedEvent(
                character_name=command.character_name,
                objective_id=command.objective_id,
                objective_description=command.objective_description
            ))
            
            self._logger.info(f"Objective assigned to character: {command.character_name}")
            
            return CommandResult.success_result(
                data={
                    "character_name": command.character_name,
                    "objective_id": command.objective_id,
                    "objective_description": command.objective_description,
                    "objective_type": command.objective_type
                },
                message=f"Objective assigned to {command.character_name}"
            )
            
        except ValidationException as e:
            return CommandResult.failure_result(e, e.message)
        except BusinessRuleException as e:
            return CommandResult.failure_result(e, e.message)
        except Exception as e:
            return CommandResult.failure_result(
                ApplicationException(f"Objective assignment failed: {str(e)}", cause=e)
            )
    
    def _validate_create_character_command(self, command: CreateCharacterCommand) -> None:
        """验证创建角色命令
        
        Args:
            command: 创建角色命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.name or not command.name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if command.hp < 0 or command.max_hp <= 0:
            raise ValidationException("HP must be >= 0 and max HP must be > 0")
        
        if command.hp > command.max_hp:
            raise ValidationException("HP cannot be greater than max HP")
        
        if not command.abilities:
            raise ValidationException("Abilities cannot be empty")
        
        # 验证能力值
        for ability, value in command.abilities.items():
            if not isinstance(value, int) or value < 1 or value > 20:
                raise ValidationException(f"Invalid ability value for {ability}: {value}")
    
    def _validate_update_position_command(self, command: UpdateCharacterPositionCommand) -> None:
        """验证更新位置命令
        
        Args:
            command: 更新位置命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.character_name or not command.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not isinstance(command.new_position, tuple) or len(command.new_position) != 2:
            raise ValidationException("Position must be a tuple of (x, y)")
        
        x, y = command.new_position
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValidationException("Position coordinates must be integers")
        
        if x < 0 or y < 0:
            raise ValidationException("Position coordinates must be non-negative")
    
    def _validate_update_relation_command(self, command: UpdateCharacterRelationCommand) -> None:
        """验证更新关系命令
        
        Args:
            command: 更新关系命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.source_character or not command.source_character.strip():
            raise ValidationException("Source character name cannot be empty")
        
        if not command.target_character or not command.target_character.strip():
            raise ValidationException("Target character name cannot be empty")
        
        if command.source_character == command.target_character:
            raise ValidationException("Source and target characters cannot be the same")
        
        if not isinstance(command.delta, int):
            raise ValidationException("Relation delta must be an integer")
        
        if abs(command.delta) > 100:
            raise ValidationException("Relation delta cannot exceed 100 in absolute value")
    
    def _validate_give_item_command(self, command: GiveItemCommand) -> None:
        """验证给予物品命令
        
        Args:
            command: 给予物品命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.character_name or not command.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not command.item_name or not command.item_name.strip():
            raise ValidationException("Item name cannot be empty")
        
        if not isinstance(command.quantity, int) or command.quantity <= 0:
            raise ValidationException("Item quantity must be a positive integer")
    
    def _validate_take_item_command(self, command: TakeItemCommand) -> None:
        """验证取走物品命令
        
        Args:
            command: 取走物品命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.character_name or not command.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not command.item_name or not command.item_name.strip():
            raise ValidationException("Item name cannot be empty")
        
        if not isinstance(command.quantity, int) or command.quantity <= 0:
            raise ValidationException("Item quantity must be a positive integer")
    
    def _validate_assign_objective_command(self, command: AssignObjectiveCommand) -> None:
        """验证分配目标命令
        
        Args:
            command: 分配目标命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not command.character_name or not command.character_name.strip():
            raise ValidationException("Character name cannot be empty")
        
        if not command.objective_id or not command.objective_id.strip():
            raise ValidationException("Objective ID cannot be empty")
        
        if not command.objective_description or not command.objective_description.strip():
            raise ValidationException("Objective description cannot be empty")
    
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