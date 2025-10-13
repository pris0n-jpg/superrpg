"""
领域模型模块

该模块包含所有领域模型的定义，遵循SOLID原则，
特别是单一职责原则(SRP)和开放/封闭原则(OCP)。

领域模型负责：
1. 封装业务逻辑和规则
2. 定义实体的状态和行为
3. 确保数据的一致性和完整性
4. 提供领域特定的方法
"""

from .base import BaseEntity, ValueObject, AggregateRoot, EntityId
from .characters import Character, Ability, Condition, Abilities, CharacterStats, Position
from .combat import Combat, RangeBand, CoverLevel, CombatState, TurnState, InitiativeScore
from .items import Item, ItemType, ItemRarity, WeaponType, DamageType, ArmorType, ItemStats, ItemProperties, Inventory
from .relations import Relation, RelationType, RelationStrength, RelationKey, RelationshipNetwork
from .objectives import Objective, ObjectiveStatus, ObjectivePriority, ObjectiveType, ObjectiveCondition, ObjectiveReward, ObjectiveTracker
from .world import World, Location, Scene, GameTime, Weather, LocationType, TimeOfDay

__all__ = [
    # 基础模型
    'BaseEntity',
    'ValueObject',
    'AggregateRoot',
    'EntityId',
    
    # 角色模型
    'Character',
    'Ability',
    'Condition',
    'Abilities',
    'CharacterStats',
    'Position',
    
    # 战斗模型
    'Combat',
    'RangeBand',
    'CoverLevel',
    'CombatState',
    'TurnState',
    'InitiativeScore',
    
    # 物品模型
    'Item',
    'ItemType',
    'ItemRarity',
    'WeaponType',
    'DamageType',
    'ArmorType',
    'ItemStats',
    'ItemProperties',
    'Inventory',
    
    # 关系模型
    'Relation',
    'RelationType',
    'RelationStrength',
    'RelationKey',
    'RelationshipNetwork',
    
    # 目标模型
    'Objective',
    'ObjectiveStatus',
    'ObjectivePriority',
    'ObjectiveType',
    'ObjectiveCondition',
    'ObjectiveReward',
    'ObjectiveTracker',
    
    # 世界模型
    'World',
    'Location',
    'Scene',
    'GameTime',
    'Weather',
    'LocationType',
    'TimeOfDay',
]