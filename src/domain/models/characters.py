"""
角色领域模型
包含角色的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import json
import base64
from datetime import datetime

from .base import Entity, ValueObject, AggregateRoot
from ...core.interfaces import DomainEvent


class CharacterDomainEvent(DomainEvent):
    """角色领域事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        super().__init__()
        self._event_type = event_type
        self._data = data
    
    def get_event_type(self) -> str:
        return self._event_type
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data


class Ability(Enum):
    """能力属性枚举"""
    STRENGTH = "STR"
    DEXTERITY = "DEX"
    CONSTITUTION = "CON"
    INTELLIGENCE = "INT"
    WISDOM = "WIS"
    CHARISMA = "CHA"


class Condition(Enum):
    """状态条件枚举"""
    HIDDEN = "hidden"
    PRONE = "prone"
    GRAPPLED = "grappled"
    RESTRAINED = "restrained"
    DODGE = "dodge"


@dataclass(frozen=True)
class Abilities(ValueObject):
    """角色能力值"""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.strength,
            self.dexterity,
            self.constitution,
            self.intelligence,
            self.wisdom,
            self.charisma
        )

    def get_modifier(self, ability: Ability) -> int:
        """获取能力修正值"""
        ability_map = {
            Ability.STRENGTH: self.strength,
            Ability.DEXTERITY: self.dexterity,
            Ability.CONSTITUTION: self.constitution,
            Ability.INTELLIGENCE: self.intelligence,
            Ability.WISDOM: self.wisdom,
            Ability.CHARISMA: self.charisma,
        }
        score = ability_map.get(ability, 10)
        return (score - 10) // 2

    def get_score(self, ability: Ability) -> int:
        """获取能力值"""
        ability_map = {
            Ability.STRENGTH: self.strength,
            Ability.DEXTERITY: self.dexterity,
            Ability.CONSTITUTION: self.constitution,
            Ability.INTELLIGENCE: self.intelligence,
            Ability.WISDOM: self.wisdom,
            Ability.CHARISMA: self.charisma,
        }
        return ability_map.get(ability, 10)


@dataclass(frozen=True)
class CharacterStats(ValueObject):
    """角色统计数据"""
    level: int = 1
    armor_class: int = 10
    proficiency_bonus: int = 2
    speed_steps: int = 6
    reach_steps: int = 1

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.level,
            self.armor_class,
            self.proficiency_bonus,
            self.speed_steps,
            self.reach_steps
        )


@dataclass(frozen=True)
class Position(ValueObject):
    """位置坐标"""
    x: int
    y: int

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (self.x, self.y)

    def distance_to(self, other: 'Position') -> int:
        """计算到另一个位置的曼哈顿距离"""
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass
class Character(AggregateRoot):
    """角色聚合根"""
    name: str
    abilities: Abilities
    stats: CharacterStats
    hp: int
    max_hp: int
    position: Optional[Position] = None
    proficient_skills: List[str] = field(default_factory=list)
    proficient_saves: List[str] = field(default_factory=list)
    conditions: Set[Condition] = field(default_factory=set)
    inventory: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            raise ValueError("角色名称不能为空")
        if self.hp < 0:
            self.hp = 0
        if self.hp > self.max_hp:
            self.hp = self.max_hp

    @property
    def is_alive(self) -> bool:
        """检查角色是否存活"""
        return self.hp > 0

    @property
    def dexterity_modifier(self) -> int:
        """敏捷修正值"""
        return self.abilities.get_modifier(Ability.DEXTERITY)

    def take_damage(self, amount: int) -> None:
        """受到伤害"""
        if amount < 0:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.add_domain_event(CharacterDomainEvent("character_knocked_out", {
                "character_name": self.name,
                "damage": amount
            }))

    def heal(self, amount: int) -> None:
        """恢复生命值"""
        if amount < 0:
            return
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > old_hp:
            self.add_domain_event(CharacterDomainEvent("character_healed", {
                "character_name": self.name,
                "amount": amount,
                "old_hp": old_hp,
                "new_hp": self.hp
            }))

    def move_to(self, position: Position) -> None:
        """移动到新位置"""
        old_position = self.position
        self.position = position
        self.add_domain_event(CharacterDomainEvent("character_moved", {
            "character_name": self.name,
            "old_position": old_position,
            "new_position": position
        }))

    def add_condition(self, condition: Condition) -> None:
        """添加状态条件"""
        if condition not in self.conditions:
            self.conditions.add(condition)
            self.add_domain_event(CharacterDomainEvent("condition_added", {
                "character_name": self.name,
                "condition": condition.value
            }))

    def remove_condition(self, condition: Condition) -> None:
        """移除状态条件"""
        if condition in self.conditions:
            self.conditions.remove(condition)
            self.add_domain_event(CharacterDomainEvent("condition_removed", {
                "character_name": self.name,
                "condition": condition.value
            }))

    def has_condition(self, condition: Condition) -> bool:
        """检查是否有指定状态条件"""
        return condition in self.conditions

    def add_item(self, item_name: str, quantity: int = 1) -> None:
        """添加物品到物品栏"""
        if quantity <= 0:
            return
        current_quantity = self.inventory.get(item_name, 0)
        self.inventory[item_name] = current_quantity + quantity
        self.add_domain_event(CharacterDomainEvent("item_added", {
            "character_name": self.name,
            "item_name": item_name,
            "quantity": quantity,
            "total_quantity": self.inventory[item_name]
        }))

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """从物品栏移除物品"""
        if quantity <= 0:
            return False
        current_quantity = self.inventory.get(item_name, 0)
        if current_quantity < quantity:
            return False
        
        new_quantity = current_quantity - quantity
        if new_quantity == 0:
            del self.inventory[item_name]
        else:
            self.inventory[item_name] = new_quantity
        
        self.add_domain_event(CharacterDomainEvent("item_removed", {
            "character_name": self.name,
            "item_name": item_name,
            "quantity": quantity,
            "remaining_quantity": new_quantity
        }))
        return True

    def is_proficient_in_skill(self, skill: str) -> bool:
        """检查是否熟练指定技能"""
        return skill.lower() in [s.lower() for s in self.proficient_skills]

    def is_proficient_in_save(self, ability: Ability) -> bool:
        """检查是否熟练指定豁免"""
        return ability.value in self.proficient_saves

    def get_skill_modifier(self, skill: str) -> int:
        """获取技能修正值"""
        # 技能到能力的映射
        skill_to_ability = {
            "acrobatics": Ability.DEXTERITY,
            "animal handling": Ability.WISDOM,
            "arcana": Ability.INTELLIGENCE,
            "athletics": Ability.STRENGTH,
            "deception": Ability.CHARISMA,
            "history": Ability.INTELLIGENCE,
            "insight": Ability.WISDOM,
            "intimidation": Ability.CHARISMA,
            "investigation": Ability.INTELLIGENCE,
            "medicine": Ability.WISDOM,
            "nature": Ability.INTELLIGENCE,
            "perception": Ability.WISDOM,
            "performance": Ability.CHARISMA,
            "persuasion": Ability.CHARISMA,
            "religion": Ability.INTELLIGENCE,
            "sleight of hand": Ability.DEXTERITY,
            "stealth": Ability.DEXTERITY,
            "survival": Ability.WISDOM,
        }
        
        ability = skill_to_ability.get(skill.lower())
        if not ability:
            return 0
        
        modifier = self.abilities.get_modifier(ability)
        if self.is_proficient_in_skill(skill):
            modifier += self.stats.proficiency_bonus
        
        return modifier
    
    def validate(self) -> None:
        """验证角色状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not self.name or not self.name.strip():
            raise ValidationException("角色名称不能为空")
        
        if self.max_hp <= 0:
            raise ValidationException("最大生命值必须大于0")
        
        if self.hp < 0:
            raise ValidationException("当前生命值不能小于0")
        
        if self.hp > self.max_hp:
            raise ValidationException("当前生命值不能大于最大生命值")
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []

    def get_save_modifier(self, ability: Ability) -> int:
        """获取豁免修正值"""
        modifier = self.abilities.get_modifier(ability)
        if self.is_proficient_in_save(ability):
            modifier += self.stats.proficiency_bonus
        return modifier


@dataclass(frozen=True)
class CharacterCardInfo(ValueObject):
    """角色卡信息值对象
    
    封装角色卡的核心信息，包括描述、对话示例等。
    遵循单一职责原则，专门负责角色卡信息的管理。
    """
    description: str = ""
    first_message: str = ""
    example_messages: List[str] = field(default_factory=list)
    scenario: str = ""
    personality_summary: str = ""
    creator_notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.description,
            self.first_message,
            tuple(self.example_messages),
            self.scenario,
            self.personality_summary,
            self.creator_notes,
            tuple(self.tags)
        )


@dataclass(frozen=True)
class PNGMetadata(ValueObject):
    """PNG图像元数据值对象
    
    封装PNG图像中的角色卡元数据，兼容TavernAI格式。
    遵循单一职责原则，专门负责PNG元数据的管理。
    """
    name: str = ""
    description: str = ""
    personality: str = ""
    scenario: str = ""
    first_mes: str = ""
    example_dialogue: str = ""
    mes_example: str = ""
    background: str = ""
    data: Optional[bytes] = None
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.name,
            self.description,
            self.personality,
            self.scenario,
            self.first_mes,
            self.example_dialogue,
            self.mes_example,
            self.background
        )
    
    @classmethod
    def from_base64(cls, base64_data: str) -> 'PNGMetadata':
        """从Base64数据创建PNG元数据
        
        Args:
            base64_data: Base64编码的数据
            
        Returns:
            PNGMetadata: PNG元数据对象
        """
        try:
            # 解码Base64数据
            json_data = base64.b64decode(base64_data).decode('utf-8')
            data = json.loads(json_data)
            
            return cls(
                name=data.get('name', ''),
                description=data.get('description', ''),
                personality=data.get('personality', ''),
                scenario=data.get('scenario', ''),
                first_mes=data.get('first_mes', ''),
                example_dialogue=data.get('example_dialogue', ''),
                mes_example=data.get('mes_example', ''),
                background=data.get('background', ''),
                data=base64.b64decode(base64_data)
            )
        except Exception:
            # 如果解析失败，返回空的元数据对象
            return cls()
    
    def to_base64(self) -> str:
        """转换为Base64字符串
        
        Returns:
            str: Base64编码的字符串
        """
        data = {
            'name': self.name,
            'description': self.description,
            'personality': self.personality,
            'scenario': self.scenario,
            'first_mes': self.first_mes,
            'example_dialogue': self.example_dialogue,
            'mes_example': self.mes_example,
            'background': self.background
        }
        
        json_data = json.dumps(data, ensure_ascii=False)
        return base64.b64encode(json_data.encode('utf-8')).decode('utf-8')


class CharacterCard(AggregateRoot):
    """角色卡聚合根
    
    扩展自Character聚合根，添加角色卡特有的功能。
    遵循单一职责原则，专门负责角色卡的管理。
    """
    
    def __init__(self, name: str, card_info: CharacterCardInfo,
                 abilities: Optional[Abilities] = None,
                 stats: Optional[CharacterStats] = None,
                 hp: int = 100, max_hp: int = 100,
                 position: Optional[Position] = None,
                 png_metadata: Optional[PNGMetadata] = None,
                 **kwargs):
        """初始化角色卡
        
        Args:
            name: 角色名称
            card_info: 角色卡信息
            abilities: 角色能力值
            stats: 角色统计数据
            hp: 当前生命值
            max_hp: 最大生命值
            position: 角色位置
            png_metadata: PNG元数据
            **kwargs: 其他角色属性
        """
        super().__init__()
        
        # 基本角色属性
        self.name = name
        self.abilities = abilities or Abilities()
        self.stats = stats or CharacterStats()
        self.hp = hp
        self.max_hp = max_hp
        self.position = position
        self.proficient_skills = kwargs.get('proficient_skills', [])
        self.proficient_saves = kwargs.get('proficient_saves', [])
        self.conditions = set(kwargs.get('conditions', []))
        self.inventory = kwargs.get('inventory', {})
        
        # 角色卡特有属性
        self.card_info = card_info
        self.png_metadata = png_metadata or PNGMetadata()
        
        # 验证角色卡
        self.validate()
        
        # 添加领域事件
        self.add_domain_event(CharacterDomainEvent("character_card_created", {
            "character_name": self.name,
            "description": self.card_info.description[:100] + "..." if len(self.card_info.description) > 100 else self.card_info.description
        }))
    
    def update_card_info(self, card_info: CharacterCardInfo) -> None:
        """更新角色卡信息
        
        Args:
            card_info: 新的角色卡信息
        """
        old_info = self.card_info
        self.card_info = card_info
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(CharacterDomainEvent("character_card_updated", {
            "character_name": self.name,
            "old_description": old_info.description[:50] + "..." if len(old_info.description) > 50 else old_info.description,
            "new_description": card_info.description[:50] + "..." if len(card_info.description) > 50 else card_info.description
        }))
    
    def update_png_metadata(self, png_metadata: PNGMetadata) -> None:
        """更新PNG元数据
        
        Args:
            png_metadata: 新的PNG元数据
        """
        self.png_metadata = png_metadata
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(CharacterDomainEvent("png_metadata_updated", {
            "character_name": self.name,
            "has_data": png_metadata.data is not None
        }))
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典格式
        
        Returns:
            Dict[str, Any]: 角色卡数据的字典表示
        """
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.card_info.description,
            'first_message': self.card_info.first_message,
            'example_messages': self.card_info.example_messages,
            'scenario': self.card_info.scenario,
            'personality_summary': self.card_info.personality_summary,
            'creator_notes': self.card_info.creator_notes,
            'tags': self.card_info.tags,
            'abilities': {
                'strength': self.abilities.strength,
                'dexterity': self.abilities.dexterity,
                'constitution': self.abilities.constitution,
                'intelligence': self.abilities.intelligence,
                'wisdom': self.abilities.wisdom,
                'charisma': self.abilities.charisma,
            },
            'stats': {
                'level': self.stats.level,
                'armor_class': self.stats.armor_class,
                'proficiency_bonus': self.stats.proficiency_bonus,
                'speed_steps': self.stats.speed_steps,
                'reach_steps': self.stats.reach_steps,
            },
            'hp': self.hp,
            'max_hp': self.max_hp,
            'position': {
                'x': self.position.x,
                'y': self.position.y,
            } if self.position else None,
            'proficient_skills': self.proficient_skills,
            'proficient_saves': self.proficient_saves,
            'conditions': [c.value for c in self.conditions],
            'inventory': self.inventory,
            'png_metadata': {
                'name': self.png_metadata.name,
                'description': self.png_metadata.description,
                'personality': self.png_metadata.personality,
                'scenario': self.png_metadata.scenario,
                'first_mes': self.png_metadata.first_mes,
                'example_dialogue': self.png_metadata.example_dialogue,
                'mes_example': self.png_metadata.mes_example,
                'background': self.png_metadata.background,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterCard':
        """从字典创建角色卡
        
        Args:
            data: 角色卡数据字典
            
        Returns:
            CharacterCard: 角色卡实例
        """
        # 创建能力值对象
        abilities_data = data.get('abilities', {})
        abilities = Abilities(
            strength=abilities_data.get('strength', 10),
            dexterity=abilities_data.get('dexterity', 10),
            constitution=abilities_data.get('constitution', 10),
            intelligence=abilities_data.get('intelligence', 10),
            wisdom=abilities_data.get('wisdom', 10),
            charisma=abilities_data.get('charisma', 10),
        )
        
        # 创建统计数据对象
        stats_data = data.get('stats', {})
        stats = CharacterStats(
            level=stats_data.get('level', 1),
            armor_class=stats_data.get('armor_class', 10),
            proficiency_bonus=stats_data.get('proficiency_bonus', 2),
            speed_steps=stats_data.get('speed_steps', 6),
            reach_steps=stats_data.get('reach_steps', 1),
        )
        
        # 创建位置对象
        position_data = data.get('position')
        position = None
        if position_data:
            position = Position(x=position_data['x'], y=position_data['y'])
        
        # 创建角色卡信息对象
        card_info = CharacterCardInfo(
            description=data.get('description', ''),
            first_message=data.get('first_message', ''),
            example_messages=data.get('example_messages', []),
            scenario=data.get('scenario', ''),
            personality_summary=data.get('personality_summary', ''),
            creator_notes=data.get('creator_notes', ''),
            tags=data.get('tags', []),
        )
        
        # 创建PNG元数据对象
        png_data = data.get('png_metadata', {})
        png_metadata = PNGMetadata(
            name=png_data.get('name', ''),
            description=png_data.get('description', ''),
            personality=png_data.get('personality', ''),
            scenario=png_data.get('scenario', ''),
            first_mes=png_data.get('first_mes', ''),
            example_dialogue=png_data.get('example_dialogue', ''),
            mes_example=png_data.get('mes_example', ''),
            background=png_data.get('background', ''),
        )
        
        # 创建角色卡
        character_card = cls(
            name=data['name'],
            card_info=card_info,
            abilities=abilities,
            stats=stats,
            hp=data.get('hp', 100),
            max_hp=data.get('max_hp', 100),
            position=position,
            png_metadata=png_metadata,
            proficient_skills=data.get('proficient_skills', []),
            proficient_saves=data.get('proficient_saves', []),
            inventory=data.get('inventory', {}),
        )
        
        # 设置条件和时间戳
        for condition_str in data.get('conditions', []):
            try:
                character_card.add_condition(Condition(condition_str))
            except ValueError:
                pass
        
        # 设置时间戳（通过内部属性设置）
        if data.get('created_at'):
            character_card._created_at = datetime.fromisoformat(data['created_at'])
        if data.get('updated_at'):
            character_card._updated_at = datetime.fromisoformat(data['updated_at'])
        
        return character_card
    
    def validate(self) -> None:
        """验证角色卡状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        from ...core.exceptions import ValidationException
        
        if not self.name or not self.name.strip():
            raise ValidationException("角色名称不能为空")
        
        if self.max_hp <= 0:
            raise ValidationException("最大生命值必须大于0")
        
        if self.hp < 0:
            raise ValidationException("当前生命值不能小于0")
        
        if self.hp > self.max_hp:
            raise ValidationException("当前生命值不能大于最大生命值")
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []
    
    # 继承Character类的其他方法
    @property
    def is_alive(self) -> bool:
        """检查角色是否存活"""
        return self.hp > 0
    
    @property
    def dexterity_modifier(self) -> int:
        """敏捷修正值"""
        return self.abilities.get_modifier(Ability.DEXTERITY)
    
    def take_damage(self, amount: int) -> None:
        """受到伤害"""
        if amount < 0:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.add_domain_event(CharacterDomainEvent("character_knocked_out", {
                "character_name": self.name,
                "damage": amount
            }))
        self._mark_as_updated()
    
    def heal(self, amount: int) -> None:
        """恢复生命值"""
        if amount < 0:
            return
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        if self.hp > old_hp:
            self.add_domain_event(CharacterDomainEvent("character_healed", {
                "character_name": self.name,
                "amount": amount,
                "old_hp": old_hp,
                "new_hp": self.hp
            }))
        self._mark_as_updated()
    
    def move_to(self, position: Position) -> None:
        """移动到新位置"""
        old_position = self.position
        self.position = position
        self.add_domain_event(CharacterDomainEvent("character_moved", {
            "character_name": self.name,
            "old_position": old_position,
            "new_position": position
        }))
        self._mark_as_updated()
    
    def add_condition(self, condition: Condition) -> None:
        """添加状态条件"""
        if condition not in self.conditions:
            self.conditions.add(condition)
            self.add_domain_event(CharacterDomainEvent("condition_added", {
                "character_name": self.name,
                "condition": condition.value
            }))
            self._mark_as_updated()
    
    def remove_condition(self, condition: Condition) -> None:
        """移除状态条件"""
        if condition in self.conditions:
            self.conditions.remove(condition)
            self.add_domain_event(CharacterDomainEvent("condition_removed", {
                "character_name": self.name,
                "condition": condition.value
            }))
            self._mark_as_updated()
    
    def has_condition(self, condition: Condition) -> bool:
        """检查是否有指定状态条件"""
        return condition in self.conditions
    
    def add_item(self, item_name: str, quantity: int = 1) -> None:
        """添加物品到物品栏"""
        if quantity <= 0:
            return
        current_quantity = self.inventory.get(item_name, 0)
        self.inventory[item_name] = current_quantity + quantity
        self.add_domain_event(CharacterDomainEvent("item_added", {
            "character_name": self.name,
            "item_name": item_name,
            "quantity": quantity,
            "total_quantity": self.inventory[item_name]
        }))
        self._mark_as_updated()
    
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """从物品栏移除物品"""
        if quantity <= 0:
            return False
        current_quantity = self.inventory.get(item_name, 0)
        if current_quantity < quantity:
            return False
        
        new_quantity = current_quantity - quantity
        if new_quantity == 0:
            del self.inventory[item_name]
        else:
            self.inventory[item_name] = new_quantity
        
        self.add_domain_event(CharacterDomainEvent("item_removed", {
            "character_name": self.name,
            "item_name": item_name,
            "quantity": quantity,
            "remaining_quantity": new_quantity
        }))
        self._mark_as_updated()
        return True
    
    def is_proficient_in_skill(self, skill: str) -> bool:
        """检查是否熟练指定技能"""
        return skill.lower() in [s.lower() for s in self.proficient_skills]
    
    def is_proficient_in_save(self, ability: Ability) -> bool:
        """检查是否熟练指定豁免"""
        return ability.value in self.proficient_saves
    
    def get_skill_modifier(self, skill: str) -> int:
        """获取技能修正值"""
        # 技能到能力的映射
        skill_to_ability = {
            "acrobatics": Ability.DEXTERITY,
            "animal handling": Ability.WISDOM,
            "arcana": Ability.INTELLIGENCE,
            "athletics": Ability.STRENGTH,
            "deception": Ability.CHARISMA,
            "history": Ability.INTELLIGENCE,
            "insight": Ability.WISDOM,
            "intimidation": Ability.CHARISMA,
            "investigation": Ability.INTELLIGENCE,
            "medicine": Ability.WISDOM,
            "nature": Ability.INTELLIGENCE,
            "perception": Ability.WISDOM,
            "performance": Ability.CHARISMA,
            "persuasion": Ability.CHARISMA,
            "religion": Ability.INTELLIGENCE,
            "sleight of hand": Ability.DEXTERITY,
            "stealth": Ability.DEXTERITY,
            "survival": Ability.WISDOM,
        }
        
        ability = skill_to_ability.get(skill.lower())
        if not ability:
            return 0
        
        modifier = self.abilities.get_modifier(ability)
        if self.is_proficient_in_skill(skill):
            modifier += self.stats.proficiency_bonus
        
        return modifier
    
    def get_save_modifier(self, ability: Ability) -> int:
        """获取豁免修正值"""
        modifier = self.abilities.get_modifier(ability)
        if self.is_proficient_in_save(ability):
            modifier += self.stats.proficiency_bonus
        return modifier