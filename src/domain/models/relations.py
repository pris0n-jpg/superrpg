"""
关系领域模型
包含角色间关系的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum

from .base import Entity, ValueObject, AggregateRoot


class RelationType(Enum):
    """关系类型枚举"""
    FRIENDSHIP = "friendship"
    ROMANTIC = "romantic"
    FAMILY = "family"
    PROFESSIONAL = "professional"
    RIVALRY = "rivalry"
    ALLIANCE = "alliance"
    ENMITY = "enmity"
    MENTORSHIP = "mentorship"
    ACQUAINTANCE = "acquaintance"


class RelationStrength(Enum):
    """关系强度枚举"""
    HATED = -5
    HOSTILE = -3
    UNFRIENDLY = -1
    NEUTRAL = 0
    FRIENDLY = 1
    GOOD_FRIEND = 3
    BEST_FRIEND = 5


@dataclass(frozen=True)
class RelationKey(ValueObject):
    """关系键值对象"""
    source: str
    target: str

    def __post_init__(self):
        """初始化后处理"""
        if not self.source:
            raise ValueError("关系源不能为空")
        if not self.target:
            raise ValueError("关系目标不能为空")
        if self.source == self.target:
            raise ValueError("关系源和目标不能相同")

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件
        
        Returns:
            tuple: 用于相等性比较的组件元组
        """
        return (self.source, self.target)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.source}->{self.target}"

    def to_undirected_key(self) -> Tuple[str, str]:
        """转换为无向键"""
        return tuple(sorted([self.source, self.target]))


@dataclass(frozen=True)
class Relation(ValueObject):
    """关系值对象"""
    key: RelationKey
    relation_type: RelationType
    strength: int = 0
    description: str = ""
    mutual: bool = False
    created_at: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.key:
            raise ValueError("关系键不能为空")
        
        # 验证关系强度范围
        if self.strength < RelationStrength.HATED.value or self.strength > RelationStrength.BEST_FRIEND.value:
            raise ValueError(f"关系强度必须在 {RelationStrength.HATED.value} 到 {RelationStrength.BEST_FRIEND.value} 之间")

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件
        
        Returns:
            tuple: 用于相等性比较的组件元组
        """
        return (self.key, self.relation_type, self.strength, self.description, self.mutual, self.created_at)

    @property
    def source(self) -> str:
        """获取关系源"""
        return self.key.source

    @property
    def target(self) -> str:
        """获取关系目标"""
        return self.key.target

    @property
    def is_positive(self) -> bool:
        """是否为正面关系"""
        return self.strength > 0

    @property
    def is_negative(self) -> bool:
        """是否为负面关系"""
        return self.strength < 0

    @property
    def is_neutral(self) -> bool:
        """是否为中性关系"""
        return self.strength == 0

    @property
    def strength_level(self) -> RelationStrength:
        """获取关系强度等级"""
        if self.strength <= RelationStrength.HATED.value:
            return RelationStrength.HATED
        elif self.strength <= RelationStrength.HOSTILE.value:
            return RelationStrength.HOSTILE
        elif self.strength <= RelationStrength.UNFRIENDLY.value:
            return RelationStrength.UNFRIENDLY
        elif self.strength <= RelationStrength.NEUTRAL.value:
            return RelationStrength.NEUTRAL
        elif self.strength <= RelationStrength.FRIENDLY.value:
            return RelationStrength.FRIENDLY
        elif self.strength <= RelationStrength.GOOD_FRIEND.value:
            return RelationStrength.GOOD_FRIEND
        else:
            return RelationStrength.BEST_FRIEND

    def adjust_strength(self, delta: int) -> 'Relation':
        """调整关系强度
        
        Args:
            delta: 调整值（可为负数）
            
        Returns:
            Relation: 新的关系对象
        """
        new_strength = max(RelationStrength.HATED.value, 
                         min(RelationStrength.BEST_FRIEND.value, self.strength + delta))
        return Relation(
            key=self.key,
            relation_type=self.relation_type,
            strength=new_strength,
            description=self.description,
            mutual=self.mutual,
            created_at=self.created_at
        )

    def with_description(self, description: str) -> 'Relation':
        """更新描述
        
        Args:
            description: 新描述
            
        Returns:
            Relation: 新的关系对象
        """
        return Relation(
            key=self.key,
            relation_type=self.relation_type,
            strength=self.strength,
            description=description,
            mutual=self.mutual,
            created_at=self.created_at
        )


@dataclass
class RelationshipNetwork(AggregateRoot):
    """关系网络聚合根"""
    relations: Dict[RelationKey, Relation] = field(default_factory=dict)
    characters: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """初始化后处理"""
        # 从关系中提取角色列表
        for relation in self.relations.values():
            self.characters.add(relation.source)
            self.characters.add(relation.target)

    @property
    def character_count(self) -> int:
        """获取角色数量"""
        return len(self.characters)

    @property
    def relation_count(self) -> int:
        """获取关系数量"""
        return len(self.relations)

    def has_character(self, character_name: str) -> bool:
        """检查是否包含指定角色"""
        return character_name in self.characters

    def has_relation(self, source: str, target: str) -> bool:
        """检查是否存在指定关系"""
        key = RelationKey(source=source, target=target)
        return key in self.relations

    def get_relation(self, source: str, target: str) -> Optional[Relation]:
        """获取指定关系
        
        Args:
            source: 关系源
            target: 关系目标
            
        Returns:
            Optional[Relation]: 关系对象，如果不存在则返回None
        """
        key = RelationKey(source=source, target=target)
        return self.relations.get(key)

    def add_relation(self, relation: Relation) -> None:
        """添加关系
        
        Args:
            relation: 关系对象
        """
        self.relations[relation.key] = relation
        self.characters.add(relation.source)
        self.characters.add(relation.target)
        
        self.add_domain_event("relation_added", {
            "source": relation.source,
            "target": relation.target,
            "type": relation.relation_type.value,
            "strength": relation.strength
        })

    def remove_relation(self, source: str, target: str) -> bool:
        """移除关系
        
        Args:
            source: 关系源
            target: 关系目标
            
        Returns:
            bool: 是否成功移除
        """
        key = RelationKey(source=source, target=target)
        if key not in self.relations:
            return False
        
        relation = self.relations[key]
        del self.relations[key]
        
        # 检查是否还需要保留这些角色
        source_still_has_relations = any(
            rel.source == source or rel.target == source 
            for rel in self.relations.values()
        )
        target_still_has_relations = any(
            rel.source == target or rel.target == target 
            for rel in self.relations.values()
        )
        
        if not source_still_has_relations:
            self.characters.discard(source)
        if not target_still_has_relations:
            self.characters.discard(target)
        
        self.add_domain_event("relation_removed", {
            "source": source,
            "target": target,
            "type": relation.relation_type.value,
            "strength": relation.strength
        })
        
        return True

    def update_relation_strength(self, source: str, target: str, delta: int, reason: str = "") -> bool:
        """更新关系强度
        
        Args:
            source: 关系源
            target: 关系目标
            delta: 调整值
            reason: 调整原因
            
        Returns:
            bool: 是否成功更新
        """
        key = RelationKey(source=source, target=target)
        if key not in self.relations:
            return False
        
        old_relation = self.relations[key]
        new_relation = old_relation.adjust_strength(delta)
        if reason:
            new_relation = new_relation.with_description(
                f"{old_relation.description}; {reason}" if old_relation.description else reason
            )
        
        self.relations[key] = new_relation
        
        self.add_domain_event("relation_strength_changed", {
            "source": source,
            "target": target,
            "old_strength": old_relation.strength,
            "new_strength": new_relation.strength,
            "delta": delta,
            "reason": reason
        })
        
        return True

    def get_relations_for_character(self, character_name: str) -> List[Relation]:
        """获取角色的所有关系
        
        Args:
            character_name: 角色名称
            
        Returns:
            List[Relation]: 关系列表
        """
        return [
            relation for relation in self.relations.values()
            if relation.source == character_name or relation.target == character_name
        ]

    def get_outgoing_relations(self, character_name: str) -> List[Relation]:
        """获取角色的所有对外关系
        
        Args:
            character_name: 角色名称
            
        Returns:
            List[Relation]: 对外关系列表
        """
        return [
            relation for relation in self.relations.values()
            if relation.source == character_name
        ]

    def get_incoming_relations(self, character_name: str) -> List[Relation]:
        """获取角色的所有对内关系
        
        Args:
            character_name: 角色名称
            
        Returns:
            List[Relation]: 对内关系列表
        """
        return [
            relation for relation in self.relations.values()
            if relation.target == character_name
        ]

    def get_mutual_relations(self, character_a: str, character_b: str) -> List[Relation]:
        """获取两个角色间的双向关系
        
        Args:
            character_a: 角色A
            character_b: 角色B
            
        Returns:
            List[Relation]: 双向关系列表
        """
        relations = []
        
        # A -> B 的关系
        relation_ab = self.get_relation(character_a, character_b)
        if relation_ab:
            relations.append(relation_ab)
        
        # B -> A 的关系
        relation_ba = self.get_relation(character_b, character_a)
        if relation_ba:
            relations.append(relation_ba)
        
        return relations

    def get_characters_by_relation_type(self, character_name: str, relation_type: RelationType) -> List[str]:
        """根据关系类型获取相关角色
        
        Args:
            character_name: 角色名称
            relation_type: 关系类型
            
        Returns:
            List[str]: 相关角色列表
        """
        return [
            relation.target if relation.source == character_name else relation.source
            for relation in self.relations.values()
            if relation.relation_type == relation_type and 
               (relation.source == character_name or relation.target == character_name)
        ]

    def get_characters_by_strength_range(self, character_name: str, min_strength: int, max_strength: int) -> List[str]:
        """根据关系强度范围获取相关角色
        
        Args:
            character_name: 角色名称
            min_strength: 最小强度
            max_strength: 最大强度
            
        Returns:
            List[str]: 相关角色列表
        """
        return [
            relation.target if relation.source == character_name else relation.source
            for relation in self.relations.values()
            if min_strength <= relation.strength <= max_strength and
               (relation.source == character_name or relation.target == character_name)
        ]

    def validate(self) -> None:
        """验证关系网络状态"""
        # 验证所有关系
        for relation in self.relations.values():
            if not relation.source:
                raise ValueError("关系源不能为空")
            if not relation.target:
                raise ValueError("关系目标不能为空")
            if relation.source == relation.target:
                raise ValueError("关系源和目标不能相同")

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            RelationMustHaveValidSource(),
            RelationMustHaveValidTarget(),
            RelationSourceAndTargetMustBeDifferent(),
        ]


class RelationMustHaveValidSource:
    """关系必须有有效源规则"""
    
    def is_satisfied_by(self, entity: RelationshipNetwork) -> bool:
        return all(relation.source for relation in entity.relations.values())
    
    def get_error_message(self) -> str:
        return "关系必须有有效的源"


class RelationMustHaveValidTarget:
    """关系必须有有效目标规则"""
    
    def is_satisfied_by(self, entity: RelationshipNetwork) -> bool:
        return all(relation.target for relation in entity.relations.values())
    
    def get_error_message(self) -> str:
        return "关系必须有有效的目标"


class RelationSourceAndTargetMustBeDifferent:
    """关系源和目标必须不同规则"""
    
    def is_satisfied_by(self, entity: RelationshipNetwork) -> bool:
        return all(relation.source != relation.target for relation in entity.relations.values())
    
    def get_error_message(self) -> str:
        return "关系源和目标不能相同"