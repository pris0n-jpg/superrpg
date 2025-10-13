"""
物品领域模型
包含物品的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Union
from enum import Enum

from .base import Entity, ValueObject, AggregateRoot


class ItemType(Enum):
    """物品类型枚举"""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    TOOL = "tool"
    TREASURE = "treasure"
    MISC = "misc"


class ItemRarity(Enum):
    """物品稀有度枚举"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"


class WeaponType(Enum):
    """武器类型枚举"""
    MELEE = "melee"
    RANGED = "ranged"
    THROWN = "thrown"
    NATURAL = "natural"


class DamageType(Enum):
    """伤害类型枚举"""
    BLUDGEONING = "bludgeoning"
    PIERCING = "piercing"
    SLASHING = "slashing"
    ACID = "acid"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    THUNDER = "thunder"


class ArmorType(Enum):
    """护甲类型枚举"""
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SHIELD = "shield"


@dataclass(frozen=True)
class ItemStats(ValueObject):
    """物品属性值对象"""
    weight: float = 0.0
    value: int = 0
    damage_dice: Optional[str] = None
    damage_type: Optional[DamageType] = None
    armor_class: int = 0
    strength_requirement: int = 0
    stealth_disadvantage: bool = False


@dataclass(frozen=True)
class ItemProperties(ValueObject):
    """物品属性值对象"""
    magical: bool = False
    attunement_required: bool = False
    charges: Optional[int] = None
    recharge: Optional[str] = None
    description: str = ""


@dataclass
class Item(Entity):
    """物品实体"""
    name: str
    item_type: ItemType
    rarity: ItemRarity = ItemRarity.COMMON
    stats: ItemStats = field(default_factory=ItemStats)
    properties: ItemProperties = field(default_factory=ItemProperties)
    usable_by: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            raise ValueError("物品名称不能为空")
        
        # 武器特定验证
        if self.item_type == ItemType.WEAPON:
            if not self.stats.damage_dice:
                raise ValueError("武器必须有伤害骰子")
        
        # 护甲特定验证
        if self.item_type == ItemType.ARMOR:
            if self.stats.armor_class <= 0:
                raise ValueError("护甲必须有护甲等级")

    @property
    def is_weapon(self) -> bool:
        """是否为武器"""
        return self.item_type == ItemType.WEAPON

    @property
    def is_armor(self) -> bool:
        """是否为护甲"""
        return self.item_type == ItemType.ARMOR

    @property
    def is_consumable(self) -> bool:
        """是否为消耗品"""
        return self.item_type == ItemType.CONSUMABLE

    @property
    def is_magical(self) -> bool:
        """是否为魔法物品"""
        return self.properties.magical

    @property
    def requires_attunement(self) -> bool:
        """是否需要同调"""
        return self.properties.attunement_required

    def can_be_used_by(self, character_name: str) -> bool:
        """检查是否可以被指定角色使用"""
        if not self.usable_by:
            return True  # 空列表表示所有人都可以使用
        return character_name in self.usable_by

    def has_tag(self, tag: str) -> bool:
        """检查是否有指定标签"""
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        """添加标签"""
        self.tags.add(tag)

    def remove_tag(self, tag: str) -> None:
        """移除标签"""
        self.tags.discard(tag)

    def validate(self) -> None:
        """验证物品状态"""
        if not self.name:
            raise ValueError("物品名称不能为空")
        
        if self.stats.weight < 0:
            raise ValueError("物品重量不能为负数")
        
        if self.stats.value < 0:
            raise ValueError("物品价值不能为负数")

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            ItemMustHaveValidWeight(),
            ItemMustHaveValidValue(),
        ]


class Inventory:
    """物品栏值对象"""
    
    def __init__(self, capacity: int = 20):
        """初始化物品栏
        
        Args:
            capacity: 物品栏容量（槽位数）
        """
        self._capacity = capacity
        self._items: Dict[str, int] = {}
    
    @property
    def capacity(self) -> int:
        """获取物品栏容量"""
        return self._capacity
    
    @property
    def items(self) -> Dict[str, int]:
        """获取物品字典的副本"""
        return self._items.copy()
    
    @property
    def is_full(self) -> bool:
        """检查物品栏是否已满"""
        return len(self._items) >= self._capacity
    
    @property
    def item_count(self) -> int:
        """获取物品种类数量"""
        return len(self._items)
    
    @property
    def total_quantity(self) -> int:
        """获取物品总数量"""
        return sum(self._items.values())
    
    def add_item(self, item_name: str, quantity: int = 1) -> bool:
        """添加物品
        
        Args:
            item_name: 物品名称
            quantity: 数量
            
        Returns:
            bool: 是否成功添加
        """
        if quantity <= 0:
            return False
        
        if item_name not in self._items and self.is_full:
            return False
        
        self._items[item_name] = self._items.get(item_name, 0) + quantity
        return True
    
    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """移除物品
        
        Args:
            item_name: 物品名称
            quantity: 数量
            
        Returns:
            bool: 是否成功移除
        """
        if quantity <= 0:
            return False
        
        current_quantity = self._items.get(item_name, 0)
        if current_quantity < quantity:
            return False
        
        new_quantity = current_quantity - quantity
        if new_quantity == 0:
            del self._items[item_name]
        else:
            self._items[item_name] = new_quantity
        
        return True
    
    def has_item(self, item_name: str) -> bool:
        """检查是否有指定物品"""
        return item_name in self._items
    
    def get_quantity(self, item_name: str) -> int:
        """获取物品数量"""
        return self._items.get(item_name, 0)
    
    def clear(self) -> None:
        """清空物品栏"""
        self._items.clear()
    
    def transfer_to(self, other: 'Inventory', item_name: str, quantity: int = 1) -> bool:
        """转移物品到另一个物品栏
        
        Args:
            other: 目标物品栏
            item_name: 物品名称
            quantity: 数量
            
        Returns:
            bool: 是否成功转移
        """
        if not self.remove_item(item_name, quantity):
            return False
        
        if not other.add_item(item_name, quantity):
            # 如果添加失败，将物品放回原物品栏
            self.add_item(item_name, quantity)
            return False
        
        return True


class ItemMustHaveValidWeight:
    """物品必须有有效重量规则"""
    
    def is_satisfied_by(self, entity: Item) -> bool:
        return entity.stats.weight >= 0
    
    def get_error_message(self) -> str:
        return "物品重量不能为负数"


class ItemMustHaveValidValue:
    """物品必须有有效价值规则"""
    
    def is_satisfied_by(self, entity: Item) -> bool:
        return entity.stats.value >= 0
    
    def get_error_message(self) -> str:
        return "物品价值不能为负数"


# 预定义的一些常用物品
@dataclass(frozen=True)
class WeaponTemplate(ValueObject):
    """武器模板值对象"""
    name: str
    damage_dice: str
    damage_type: DamageType
    weight: float
    value: int
    weapon_type: WeaponType
    properties: List[str] = field(default_factory=list)
    magical: bool = False
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.name,
            self.damage_dice,
            self.damage_type,
            self.weight,
            self.value,
            self.weapon_type,
            tuple(sorted(self.properties)),
            self.magical
        )


@dataclass(frozen=True)
class ArmorTemplate(ValueObject):
    """护甲模板值对象"""
    name: str
    armor_class: int
    armor_type: ArmorType
    weight: float
    value: int
    strength_requirement: int = 0
    stealth_disadvantage: bool = False
    magical: bool = False
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.name,
            self.armor_class,
            self.armor_type,
            self.weight,
            self.value,
            self.strength_requirement,
            self.stealth_disadvantage,
            self.magical
        )


# 常用武器模板
COMMON_WEAPONS = {
    "dagger": WeaponTemplate(
        name="匕首",
        damage_dice="1d4",
        damage_type=DamageType.PIERCING,
        weight=1.0,
        value=2,
        weapon_type=WeaponType.MELEE,
        properties=["finesse", "light", "thrown"]
    ),
    "longsword": WeaponTemplate(
        name="长剑",
        damage_dice="1d8",
        damage_type=DamageType.SLASHING,
        weight=3.0,
        value=15,
        weapon_type=WeaponType.MELEE,
        properties=["versatile"]
    ),
    "shortbow": WeaponTemplate(
        name="短弓",
        damage_dice="1d6",
        damage_type=DamageType.PIERCING,
        weight=2.0,
        value=25,
        weapon_type=WeaponType.RANGED,
        properties=["ammunition", "two_handed"]
    ),
}

# 常用护甲模板
COMMON_ARMOR = {
    "leather": ArmorTemplate(
        name="皮甲",
        armor_class=11,
        armor_type=ArmorType.LIGHT,
        weight=10.0,
        value=10
    ),
    "chain_mail": ArmorTemplate(
        name="链甲",
        armor_class=16,
        armor_type=ArmorType.HEAVY,
        weight=55.0,
        value=75,
        stealth_disadvantage=True
    ),
    "shield": ArmorTemplate(
        name="盾牌",
        armor_class=2,
        armor_type=ArmorType.SHIELD,
        weight=6.0,
        value=10
    ),
}