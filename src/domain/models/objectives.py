"""
目标领域模型
包含目标的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum

from .base import Entity, ValueObject, AggregateRoot
from .characters import Position
from ...core.interfaces import DomainEvent


class ObjectiveStatus(Enum):
    """目标状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ObjectivePriority(Enum):
    """目标优先级枚举"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ObjectiveType(Enum):
    """目标类型枚举"""
    KILL = "kill"
    RETRIEVE = "retrieve"
    DELIVER = "deliver"
    ESCORT = "escort"
    DEFEND = "defend"
    EXPLORE = "explore"
    INTERACT = "interact"
    SURVIVE = "survive"
    CUSTOM = "custom"


# 领域事件类定义
class ObjectiveAddedEvent(DomainEvent):
    """目标添加事件"""
    
    def __init__(self, objective_id: str, title: str, objective_type: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.objective_type = objective_type
    
    def get_event_type(self) -> str:
        return "ObjectiveAdded"


class ObjectiveRemovedEvent(DomainEvent):
    """目标移除事件"""
    
    def __init__(self, objective_id: str, title: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
    
    def get_event_type(self) -> str:
        return "ObjectiveRemoved"


class ObjectiveStatusChangedEvent(DomainEvent):
    """目标状态变更事件"""
    
    def __init__(self, objective_id: str, title: str, old_status: str, new_status: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.old_status = old_status
        self.new_status = new_status
    
    def get_event_type(self) -> str:
        return "ObjectiveStatusChanged"


class ObjectiveStartedEvent(DomainEvent):
    """目标开始事件"""
    
    def __init__(self, objective_id: str, title: str, assigned_to: List[str]):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.assigned_to = assigned_to
    
    def get_event_type(self) -> str:
        return "ObjectiveStarted"


class ObjectiveCompletedEvent(DomainEvent):
    """目标完成事件"""
    
    def __init__(self, objective_id: str, title: str, old_status: str, rewards: Dict[str, Any], notes: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.old_status = old_status
        self.rewards = rewards
        self.notes = notes
    
    def get_event_type(self) -> str:
        return "ObjectiveCompleted"


class ObjectiveFailedEvent(DomainEvent):
    """目标失败事件"""
    
    def __init__(self, objective_id: str, title: str, old_status: str, reason: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.old_status = old_status
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "ObjectiveFailed"


class ObjectiveBlockedEvent(DomainEvent):
    """目标阻塞事件"""
    
    def __init__(self, objective_id: str, title: str, old_status: str, reason: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.old_status = old_status
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "ObjectiveBlocked"


class ObjectiveUnblockedEvent(DomainEvent):
    """目标解除阻塞事件"""
    
    def __init__(self, objective_id: str, title: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
    
    def get_event_type(self) -> str:
        return "ObjectiveUnblocked"


class ObjectiveCancelledEvent(DomainEvent):
    """目标取消事件"""
    
    def __init__(self, objective_id: str, title: str, old_status: str, reason: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.old_status = old_status
        self.reason = reason
    
    def get_event_type(self) -> str:
        return "ObjectiveCancelled"


class ObjectiveAssignedEvent(DomainEvent):
    """目标分配事件"""
    
    def __init__(self, objective_id: str, title: str, character: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.character = character
    
    def get_event_type(self) -> str:
        return "ObjectiveAssigned"


class ObjectiveUnassignedEvent(DomainEvent):
    """目标取消分配事件"""
    
    def __init__(self, objective_id: str, title: str, character: str):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.character = character
    
    def get_event_type(self) -> str:
        return "ObjectiveUnassigned"


class ObjectiveConditionUpdatedEvent(DomainEvent):
    """目标条件更新事件"""
    
    def __init__(self, objective_id: str, title: str, condition_index: int, condition_type: str, old_value: Any, new_value: Any, satisfied: bool):
        super().__init__()
        self.objective_id = objective_id
        self.title = title
        self.condition_index = condition_index
        self.condition_type = condition_type
        self.old_value = old_value
        self.new_value = new_value
        self.satisfied = satisfied
    
    def get_event_type(self) -> str:
        return "ObjectiveConditionUpdated"


@dataclass(frozen=True)
class ObjectiveCondition(ValueObject):
    """目标条件值对象"""
    condition_type: str
    target: str
    required_value: Any
    current_value: Any = None
    operator: str = "equals"  # equals, greater_than, less_than, contains

    def __post_init__(self):
        """初始化后处理"""
        if not self.condition_type:
            raise ValueError("条件类型不能为空")
        if not self.target:
            raise ValueError("条件目标不能为空")

    def is_satisfied(self) -> bool:
        """检查条件是否满足"""
        if self.current_value is None:
            return False
        
        if self.operator == "equals":
            return self.current_value == self.required_value
        elif self.operator == "greater_than":
            return self.current_value > self.required_value
        elif self.operator == "less_than":
            return self.current_value < self.required_value
        elif self.operator == "contains":
            return self.required_value in self.current_value
        elif self.operator == "not_equals":
            return self.current_value != self.required_value
        else:
            return False

    def update_progress(self, new_value: Any) -> 'ObjectiveCondition':
        """更新进度
        
        Args:
            new_value: 新的当前值
            
        Returns:
            ObjectiveCondition: 更新后的条件对象
        """
        return ObjectiveCondition(
            condition_type=self.condition_type,
            target=self.target,
            required_value=self.required_value,
            current_value=new_value,
            operator=self.operator
        )


@dataclass(frozen=True)
class ObjectiveReward(ValueObject):
    """目标奖励值对象"""
    experience: int = 0
    gold: int = 0
    items: List[str] = field(default_factory=list)
    reputation: Dict[str, int] = field(default_factory=dict)
    custom_rewards: Dict[str, Any] = field(default_factory=dict)
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件
        
        Returns:
            tuple: 用于相等性比较的组件元组
        """
        return (
            self.experience,
            self.gold,
            tuple(sorted(self.items)),
            tuple(sorted(self.reputation.items())),
            tuple(sorted(self.custom_rewards.items()))
        )


@dataclass
class Objective(Entity):
    """目标实体"""
    title: str
    description: str
    objective_type: ObjectiveType
    status: ObjectiveStatus = ObjectiveStatus.PENDING
    priority: ObjectivePriority = ObjectivePriority.NORMAL
    position: Optional[Position] = None
    assigned_to: List[str] = field(default_factory=list)
    conditions: List[ObjectiveCondition] = field(default_factory=list)
    rewards: ObjectiveReward = field(default_factory=ObjectiveReward)
    prerequisites: List[str] = field(default_factory=list)
    time_limit: Optional[int] = None  # 分钟
    auto_complete: bool = False
    hidden: bool = False
    notes: str = ""

    def __post_init__(self):
        """初始化后处理"""
        # 手动调用基类初始化，因为dataclass不会自动调用父类的__init__
        Entity.__init__(self)
        
        if not self.title:
            raise ValueError("目标标题不能为空")
        if not self.description:
            raise ValueError("目标描述不能为空")

    @property
    def is_active(self) -> bool:
        """检查目标是否活跃"""
        return self.status in [ObjectiveStatus.PENDING, ObjectiveStatus.IN_PROGRESS]

    @property
    def is_completed(self) -> bool:
        """检查目标是否已完成"""
        return self.status == ObjectiveStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """检查目标是否已失败"""
        return self.status == ObjectiveStatus.FAILED

    @property
    def is_blocked(self) -> bool:
        """检查目标是否被阻塞"""
        return self.status == ObjectiveStatus.BLOCKED

    @property
    def all_conditions_satisfied(self) -> bool:
        """检查所有条件是否满足"""
        if not self.conditions:
            return True
        return all(condition.is_satisfied() for condition in self.conditions)

    @property
    def progress_percentage(self) -> float:
        """获取完成百分比"""
        if not self.conditions:
            return 100.0 if self.is_completed else 0.0
        
        satisfied_count = sum(1 for condition in self.conditions if condition.is_satisfied())
        return (satisfied_count / len(self.conditions)) * 100.0

    def start(self) -> None:
        """开始目标"""
        if self.status != ObjectiveStatus.PENDING:
            raise ValueError("只能开始待处理的目标")
        
        self.status = ObjectiveStatus.IN_PROGRESS
        
        event = ObjectiveStartedEvent(
            objective_id=str(self.id),
            title=self.title,
            assigned_to=self.assigned_to.copy()
        )
        self.add_domain_event(event)

    def complete(self, notes: str = "") -> None:
        """完成目标"""
        if self.status not in [ObjectiveStatus.PENDING, ObjectiveStatus.IN_PROGRESS]:
            raise ValueError("只能完成待处理或进行中的目标")
        
        if not self.auto_complete and not self.all_conditions_satisfied:
            raise ValueError("目标条件未满足，无法完成")
        
        old_status = self.status
        self.status = ObjectiveStatus.COMPLETED
        if notes:
            self.notes = f"{self.notes}\n{notes}" if self.notes else notes
        
        event = ObjectiveCompletedEvent(
            objective_id=str(self.id),
            title=self.title,
            old_status=old_status.value,
            rewards={
                "experience": self.rewards.experience,
                "gold": self.rewards.gold,
                "items": self.rewards.items.copy(),
                "reputation": self.rewards.reputation.copy()
            },
            notes=notes
        )
        self.add_domain_event(event)

    def fail(self, reason: str = "") -> None:
        """失败目标"""
        if self.status not in [ObjectiveStatus.PENDING, ObjectiveStatus.IN_PROGRESS]:
            raise ValueError("只能失败待处理或进行中的目标")
        
        old_status = self.status
        self.status = ObjectiveStatus.FAILED
        if reason:
            self.notes = f"{self.notes}\n失败原因：{reason}" if self.notes else f"失败原因：{reason}"
        
        event = ObjectiveFailedEvent(
            objective_id=str(self.id),
            title=self.title,
            old_status=old_status.value,
            reason=reason
        )
        self.add_domain_event(event)

    def block(self, reason: str = "") -> None:
        """阻塞目标"""
        if self.status not in [ObjectiveStatus.PENDING, ObjectiveStatus.IN_PROGRESS]:
            raise ValueError("只能阻塞待处理或进行中的目标")
        
        old_status = self.status
        self.status = ObjectiveStatus.BLOCKED
        if reason:
            self.notes = f"{self.notes}\n阻塞原因：{reason}" if self.notes else f"阻塞原因：{reason}"
        
        event = ObjectiveBlockedEvent(
            objective_id=str(self.id),
            title=self.title,
            old_status=old_status.value,
            reason=reason
        )
        self.add_domain_event(event)

    def unblock(self) -> None:
        """解除阻塞"""
        if self.status != ObjectiveStatus.BLOCKED:
            raise ValueError("只能解除被阻塞的目标")
        
        self.status = ObjectiveStatus.IN_PROGRESS
        
        event = ObjectiveUnblockedEvent(
            objective_id=str(self.id),
            title=self.title
        )
        self.add_domain_event(event)

    def cancel(self, reason: str = "") -> None:
        """取消目标"""
        if self.status == ObjectiveStatus.COMPLETED:
            raise ValueError("不能取消已完成的目标")
        
        old_status = self.status
        self.status = ObjectiveStatus.CANCELLED
        if reason:
            self.notes = f"{self.notes}\n取消原因：{reason}" if self.notes else f"取消原因：{reason}"
        
        event = ObjectiveCancelledEvent(
            objective_id=str(self.id),
            title=self.title,
            old_status=old_status.value,
            reason=reason
        )
        self.add_domain_event(event)

    def assign_to(self, character_name: str) -> None:
        """分配给角色"""
        if character_name not in self.assigned_to:
            self.assigned_to.append(character_name)
            
            event = ObjectiveAssignedEvent(
                objective_id=str(self.id),
                title=self.title,
                character=character_name
            )
            self.add_domain_event(event)

    def unassign_from(self, character_name: str) -> None:
        """取消分配"""
        if character_name in self.assigned_to:
            self.assigned_to.remove(character_name)
            
            event = ObjectiveUnassignedEvent(
                objective_id=str(self.id),
                title=self.title,
                character=character_name
            )
            self.add_domain_event(event)

    def update_condition_progress(self, condition_index: int, new_value: Any) -> bool:
        """更新条件进度
        
        Args:
            condition_index: 条件索引
            new_value: 新的当前值
            
        Returns:
            bool: 是否成功更新
        """
        if condition_index < 0 or condition_index >= len(self.conditions):
            return False
        
        old_condition = self.conditions[condition_index]
        new_condition = old_condition.update_progress(new_value)
        self.conditions[condition_index] = new_condition
        
        event = ObjectiveConditionUpdatedEvent(
            objective_id=str(self.id),
            title=self.title,
            condition_index=condition_index,
            condition_type=old_condition.condition_type,
            old_value=old_condition.current_value,
            new_value=new_value,
            satisfied=new_condition.is_satisfied()
        )
        self.add_domain_event(event)
        
        # 如果所有条件都满足且设置了自动完成，则自动完成目标
        if self.auto_complete and self.all_conditions_satisfied:
            self.complete()
        
        return True

    def add_prerequisite(self, objective_id: str) -> None:
        """添加前置条件"""
        if objective_id not in self.prerequisites:
            self.prerequisites.append(objective_id)

    def remove_prerequisite(self, objective_id: str) -> None:
        """移除前置条件"""
        if objective_id in self.prerequisites:
            self.prerequisites.remove(objective_id)

    def validate(self) -> None:
        """验证目标状态"""
        if not self.title:
            raise ValueError("目标标题不能为空")
        if not self.description:
            raise ValueError("目标描述不能为空")
        
        # 验证时间限制
        if self.time_limit is not None and self.time_limit <= 0:
            raise ValueError("时间限制必须大于0")

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            ObjectiveMustHaveValidTitle(),
            ObjectiveMustHaveValidDescription(),
            ObjectiveMustHaveValidTimeLimit(),
        ]


@dataclass
class ObjectiveTracker(AggregateRoot):
    """目标跟踪器聚合根"""
    objectives: Dict[str, Objective] = field(default_factory=dict)
    active_objectives: List[str] = field(default_factory=list)
    completed_objectives: List[str] = field(default_factory=list)
    failed_objectives: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        # 手动调用基类初始化
        AggregateRoot.__init__(self)

    @property
    def total_objectives(self) -> int:
        """获取总目标数"""
        return len(self.objectives)

    @property
    def active_count(self) -> int:
        """获取活跃目标数"""
        return len(self.active_objectives)

    @property
    def completed_count(self) -> int:
        """获取已完成目标数"""
        return len(self.completed_objectives)

    @property
    def failed_count(self) -> int:
        """获取已失败目标数"""
        return len(self.failed_objectives)

    def has_objective(self, objective_id: str) -> bool:
        """检查是否有指定目标"""
        return objective_id in self.objectives

    def get_objective(self, objective_id: str) -> Optional[Objective]:
        """获取指定目标
        
        Args:
            objective_id: 目标ID
            
        Returns:
            Optional[Objective]: 目标对象，如果不存在则返回None
        """
        return self.objectives.get(objective_id)

    def add_objective(self, objective: Objective) -> None:
        """添加目标
        
        Args:
            objective: 目标对象
        """
        self.objectives[str(objective.id)] = objective
        
        if objective.is_active:
            self.active_objectives.append(str(objective.id))
        
        # 创建领域事件
        event = ObjectiveAddedEvent(
            objective_id=str(objective.id),
            title=objective.title,
            objective_type=objective.objective_type.value
        )
        self.add_domain_event(event)

    def remove_objective(self, objective_id: str) -> bool:
        """移除目标
        
        Args:
            objective_id: 目标ID
            
        Returns:
            bool: 是否成功移除
        """
        if objective_id not in self.objectives:
            return False
        
        objective = self.objectives[objective_id]
        
        # 从各个列表中移除
        if objective_id in self.active_objectives:
            self.active_objectives.remove(objective_id)
        if objective_id in self.completed_objectives:
            self.completed_objectives.remove(objective_id)
        if objective_id in self.failed_objectives:
            self.failed_objectives.remove(objective_id)
        
        del self.objectives[objective_id]
        
        # 创建领域事件
        event = ObjectiveRemovedEvent(
            objective_id=objective_id,
            title=objective.title
        )
        self.add_domain_event(event)
        
        return True

    def get_objectives_for_character(self, character_name: str) -> List[Objective]:
        """获取角色的所有目标
        
        Args:
            character_name: 角色名称
            
        Returns:
            List[Objective]: 目标列表
        """
        return [
            objective for objective in self.objectives.values()
            if character_name in objective.assigned_to
        ]

    def get_active_objectives_for_character(self, character_name: str) -> List[Objective]:
        """获取角色的所有活跃目标
        
        Args:
            character_name: 角色名称
            
        Returns:
            List[Objective]: 活跃目标列表
        """
        return [
            objective for objective in self.objectives.values()
            if character_name in objective.assigned_to and objective.is_active
        ]

    def update_objective_status(self, objective_id: str, new_status: ObjectiveStatus) -> bool:
        """更新目标状态
        
        Args:
            objective_id: 目标ID
            new_status: 新状态
            
        Returns:
            bool: 是否成功更新
            
        Note:
            如果目标状态没有变化，不会触发事件
        """
        if objective_id not in self.objectives:
            return False
        
        objective = self.objectives[objective_id]
        old_status = objective.status
        
        # 如果状态没有变化，直接返回
        if old_status == new_status:
            return True
        
        # 从旧状态列表中移除
        if objective_id in self.active_objectives:
            self.active_objectives.remove(objective_id)
        if objective_id in self.completed_objectives:
            self.completed_objectives.remove(objective_id)
        if objective_id in self.failed_objectives:
            self.failed_objectives.remove(objective_id)
        
        # 更新状态并添加到新状态列表
        objective.status = new_status
        
        if new_status in [ObjectiveStatus.PENDING, ObjectiveStatus.IN_PROGRESS]:
            self.active_objectives.append(objective_id)
        elif new_status == ObjectiveStatus.COMPLETED:
            self.completed_objectives.append(objective_id)
        elif new_status == ObjectiveStatus.FAILED:
            self.failed_objectives.append(objective_id)
        
        # 创建领域事件
        event = ObjectiveStatusChangedEvent(
            objective_id=objective_id,
            title=objective.title,
            old_status=old_status.value,
            new_status=new_status.value
        )
        self.add_domain_event(event)
        
        return True

    def validate(self) -> None:
        """验证目标跟踪器状态"""
        # 验证所有目标
        for objective in self.objectives.values():
            objective.validate()

    def all_objectives_completed(self) -> bool:
        """检查所有目标是否已完成
        
        Returns:
            bool: 如果所有目标都已完成则返回True，否则返回False
        """
        # 如果没有目标，认为所有目标都已完成
        if not self.objectives:
            return True
        
        # 检查是否有未完成的目标
        for objective in self.objectives.values():
            # 如果目标不是已完成状态，则认为所有目标未完成
            if objective.status != ObjectiveStatus.COMPLETED:
                return False
        
        return True

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            AllObjectivesMustBeValid(),
        ]


class ObjectiveMustHaveValidTitle:
    """目标必须有有效标题规则"""
    
    def is_satisfied_by(self, entity: Objective) -> bool:
        return bool(entity.title)
    
    def get_error_message(self) -> str:
        return "目标标题不能为空"


class ObjectiveMustHaveValidDescription:
    """目标必须有有效描述规则"""
    
    def is_satisfied_by(self, entity: Objective) -> bool:
        return bool(entity.description)
    
    def get_error_message(self) -> str:
        return "目标描述不能为空"


class ObjectiveMustHaveValidTimeLimit:
    """目标必须有有效时间限制规则"""
    
    def is_satisfied_by(self, entity: Objective) -> bool:
        return entity.time_limit is None or entity.time_limit > 0
    
    def get_error_message(self) -> str:
        return "时间限制必须大于0"


class AllObjectivesMustBeValid:
    """所有目标必须有效规则"""
    
    def is_satisfied_by(self, entity: ObjectiveTracker) -> bool:
        try:
            for objective in entity.objectives.values():
                objective.validate()
            return True
        except ValueError:
            return False
    
    def get_error_message(self) -> str:
        return "所有目标必须有效"