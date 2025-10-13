"""
领域模型基础类模块

该模块定义了领域模型的基础类，遵循SOLID原则，
特别是单一职责原则(SRP)和里氏替换原则(LSP)。

基础类包括：
1. BaseEntity - 实体基类
2. ValueObject - 值对象基类
3. AggregateRoot - 聚合根基类
4. EntityId - 实体ID值对象
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, TypeVar, Generic
from datetime import datetime
import uuid
from enum import Enum

from ...core.interfaces import DomainEvent
from ...core.exceptions import ValidationException, BusinessRuleException


class GenericDomainEvent(DomainEvent):
    """通用领域事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        super().__init__()
        self._event_type = event_type
        self._data = data
    
    def get_event_type(self) -> str:
        return self._event_type
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data


T = TypeVar('T')


class EntityId:
    """实体ID值对象
    
    封装实体的唯一标识符，确保ID的一致性和类型安全。
    遵循单一职责原则，专门负责实体标识的管理。
    """
    
    def __init__(self, value: Optional[str] = None):
        """初始化实体ID
        
        Args:
            value: ID值，如果为None则自动生成UUID
        """
        self._value = value or str(uuid.uuid4())
    
    @property
    def value(self) -> str:
        """获取ID值"""
        return self._value
    
    def __str__(self) -> str:
        """字符串表示"""
        return self._value
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, EntityId):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self._value)
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"{self.__class__.__name__}('{self._value}')"


class ValueObject(ABC):
    """值对象基类
    
    所有值对象的抽象基类，通过值相等性进行比较。
    遵循单一职责原则，专门负责值对象的通用行为。
    """
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, self.__class__):
            return False
        return self._get_equality_components() == other._get_equality_components()
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(tuple(self._get_equality_components()))
    
    @abstractmethod
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件
        
        Returns:
            tuple: 用于相等性比较的组件元组
        """
        pass
    
    def __repr__(self) -> str:
        """对象表示"""
        class_name = self.__class__.__name__
        components = self._get_equality_components()
        return f"{class_name}({', '.join(repr(c) for c in components)})"


class BaseEntity(ABC):
    """实体基类
    
    所有领域实体的抽象基类，提供实体的通用功能。
    遵循单一职责原则，专门负责实体的通用行为管理。
    """
    
    def __init__(self, id: Optional[EntityId] = None):
        """初始化实体
        
        Args:
            id: 实体ID，如果为None则自动生成
        """
        self._id = id or EntityId()
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._version = 1
        self._domain_events: List[DomainEvent] = []
    
    @property
    def id(self) -> EntityId:
        """获取实体ID"""
        return self._id
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        return self._updated_at
    
    @property
    def version(self) -> int:
        """获取版本号"""
        return self._version
    
    @property
    def domain_events(self) -> List[DomainEvent]:
        """获取领域事件列表"""
        return self._domain_events.copy()
    
    def add_domain_event(self, event_or_name, data=None) -> None:
        """添加领域事件
        
        Args:
            event_or_name: 领域事件对象或事件名称
            data: 事件数据（当event_or_name为事件名称时使用）
        """
        if isinstance(event_or_name, DomainEvent):
            # 传递的是事件对象
            self._domain_events.append(event_or_name)
        else:
            # 传递的是事件名称和数据，创建一个通用事件对象
            event = GenericDomainEvent(event_or_name, data or {})
            self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """清除领域事件"""
        self._domain_events.clear()
    
    def _mark_as_updated(self) -> None:
        """标记为已更新"""
        self._updated_at = datetime.now()
        self._version += 1
    
    def __eq__(self, other) -> bool:
        """相等性比较"""
        if not isinstance(other, BaseEntity):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """哈希值"""
        return hash(self._id)
    
    def __repr__(self) -> str:
        """对象表示"""
        return f"{self.__class__.__name__}(id={self._id})"
    
    @abstractmethod
    def validate(self) -> None:
        """验证实体状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        pass
    
    @abstractmethod
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        pass
    
    def check_business_rules(self) -> None:
        """检查业务规则
        
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        for rule in self._get_business_rules():
            if not rule.is_satisfied_by(self):
                raise BusinessRuleException(
                    rule.get_error_message(),
                    rule_name=rule.__class__.__name__,
                    rule_description=rule.get_description()
                )


class Entity(BaseEntity):
    """实体类
    
    具体的实体实现，继承自BaseEntity。
    提供基本的实体功能实现。
    """
    
    def __init__(self, id: Optional[EntityId] = None):
        """初始化实体
        
        Args:
            id: 实体ID，如果为None则自动生成
        """
        super().__init__(id)
    
    def validate(self) -> None:
        """验证实体状态
        
        默认实现为空，子类可以重写此方法。
        """
        pass
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        默认实现返回空列表，子类可以重写此方法。
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []


class AggregateRoot(BaseEntity):
    """聚合根基类
    
    所有聚合根的基类，提供聚合的通用功能。
    遵循单一职责原则，专门负责聚合的通用行为管理。
    """
    
    def __init__(self, id: Optional[EntityId] = None):
        """初始化聚合根
        
        Args:
            id: 聚合根ID
        """
        super().__init__(id)
        self._child_entities: Set[BaseEntity] = set()
    
    @property
    def child_entities(self) -> Set[BaseEntity]:
        """获取子实体集合"""
        return self._child_entities.copy()
    
    def add_child_entity(self, entity: BaseEntity) -> None:
        """添加子实体
        
        Args:
            entity: 子实体
        """
        self._child_entities.add(entity)
    
    def remove_child_entity(self, entity: BaseEntity) -> None:
        """移除子实体
        
        Args:
            entity: 子实体
        """
        self._child_entities.discard(entity)
    
    def get_all_domain_events(self) -> List[DomainEvent]:
        """获取所有领域事件（包括子实体的）
        
        Returns:
            List[DomainEvent]: 所有领域事件列表
        """
        events = self._domain_events.copy()
        
        # 收集子实体的领域事件
        for child in self._child_entities:
            events.extend(child.domain_events)
        
        return events
    
    def clear_all_domain_events(self) -> None:
        """清除所有领域事件（包括子实体的）"""
        self.clear_domain_events()
        
        # 清除子实体的领域事件
        for child in self._child_entities:
            child.clear_domain_events()
    
    def validate_aggregate(self) -> None:
        """验证整个聚合
        
        验证聚合根和所有子实体。
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 验证聚合根
        self.validate()
        
        # 验证所有子实体
        for child in self._child_entities:
            child.validate()


class BusinessRule(ABC):
    """业务规则基类
    
    所有业务规则的抽象基类，定义业务规则的通用接口。
    遵循单一职责原则，专门负责业务规则的抽象定义。
    """
    
    @abstractmethod
    def is_satisfied_by(self, entity: BaseEntity) -> bool:
        """检查实体是否满足业务规则
        
        Args:
            entity: 要检查的实体
            
        Returns:
            bool: 是否满足规则
        """
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """获取错误消息
        
        Returns:
            str: 错误消息
        """
        pass
    
    def get_description(self) -> str:
        """获取规则描述
        
        Returns:
            str: 规则描述
        """
        return self.__class__.__doc__ or "No description available"


class EntityState(Enum):
    """实体状态枚举
    
    定义实体的生命周期状态。
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    ARCHIVED = "archived"


@dataclass
class AuditInfo:
    """审计信息值对象
    
    封装实体的审计信息，如创建者、修改者等。
    遵循单一职责原则，专门负责审计信息的管理。
    """
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def mark_updated(self, updated_by: Optional[str] = None) -> None:
        """标记为已更新
        
        Args:
            updated_by: 更新者
        """
        self.updated_at = datetime.now()
        if updated_by:
            self.updated_by = updated_by


class SoftDeletableEntity(BaseEntity):
    """软删除实体基类
    
    支持软删除功能的实体基类。
    遵循单一职责原则，专门负责软删除功能的管理。
    """
    
    def __init__(self, id: Optional[EntityId] = None):
        """初始化软删除实体
        
        Args:
            id: 实体ID
        """
        super().__init__(id)
        self._state = EntityState.ACTIVE
        self._deleted_at: Optional[datetime] = None
        self._deleted_by: Optional[str] = None
    
    @property
    def state(self) -> EntityState:
        """获取实体状态"""
        return self._state
    
    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self._state == EntityState.ACTIVE
    
    @property
    def is_deleted(self) -> bool:
        """是否已删除"""
        return self._state == EntityState.DELETED
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        """获取删除时间"""
        return self._deleted_at
    
    @property
    def deleted_by(self) -> Optional[str]:
        """获取删除者"""
        return self._deleted_by
    
    def soft_delete(self, deleted_by: Optional[str] = None) -> None:
        """软删除
        
        Args:
            deleted_by: 删除者
        """
        if self._state == EntityState.DELETED:
            return
        
        self._state = EntityState.DELETED
        self._deleted_at = datetime.now()
        self._deleted_by = deleted_by
        self._mark_as_updated()
    
    def restore(self) -> None:
        """恢复"""
        if self._state != EntityState.DELETED:
            return
        
        self._state = EntityState.ACTIVE
        self._deleted_at = None
        self._deleted_by = None
        self._mark_as_updated()
    
    def activate(self) -> None:
        """激活"""
        if self._state == EntityState.DELETED:
            raise BusinessRuleException("Cannot activate a deleted entity")
        
        self._state = EntityState.ACTIVE
        self._mark_as_updated()
    
    def deactivate(self) -> None:
        """停用"""
        if self._state == EntityState.DELETED:
            raise BusinessRuleException("Cannot deactivate a deleted entity")
        
        self._state = EntityState.INACTIVE
        self._mark_as_updated()


class TimestampedEntity(BaseEntity):
    """时间戳实体基类
    
    支持时间戳功能的实体基类。
    遵循单一职责原则，专门负责时间戳功能的管理。
    """
    
    def __init__(self, id: Optional[EntityId] = None):
        """初始化时间戳实体
        
        Args:
            id: 实体ID
        """
        super().__init__(id)
        self._last_activity_at = datetime.now()
    
    @property
    def last_activity_at(self) -> datetime:
        """获取最后活动时间"""
        return self._last_activity_at
    
    def update_last_activity(self) -> None:
        """更新最后活动时间"""
        self._last_activity_at = datetime.now()
        self._mark_as_updated()
    
    def is_inactive_for(self, duration_seconds: int) -> bool:
        """检查是否非活跃超过指定时间
        
        Args:
            duration_seconds: 时间间隔（秒）
            
        Returns:
            bool: 是否非活跃
        """
        elapsed = (datetime.now() - self._last_activity_at).total_seconds()
        return elapsed > duration_seconds