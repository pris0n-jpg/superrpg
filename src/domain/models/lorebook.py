"""
传说书领域模型

该模块定义了传说书相关的领域模型，遵循SOLID原则，
特别是单一职责原则(SRP)和里氏替换原则(LSP)。

模型包括：
1. LorebookEntry - 传说书条目模型
2. Lorebook - 传说书模型
3. KeywordMatcher - 关键词匹配器
4. ActivationRule - 激活规则
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, Pattern
from enum import Enum
import re
from datetime import datetime

from .base import AggregateRoot, ValueObject, Entity, EntityId
from ...core.interfaces import DomainEvent
from ...core.exceptions import ValidationException, BusinessRuleException


class LorebookDomainEvent(DomainEvent):
    """传说书领域事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        super().__init__()
        self._event_type = event_type
        self._data = data
    
    def get_event_type(self) -> str:
        return self._event_type
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data


class ActivationType(Enum):
    """激活类型枚举"""
    ALWAYS = "always"  # 始终激活
    KEYWORD = "keyword"  # 关键词触发
    REGEX = "regex"  # 正则表达式触发
    MANUAL = "manual"  # 手动激活


class KeywordType(Enum):
    """关键词类型枚举"""
    EXACT = "exact"  # 精确匹配
    PARTIAL = "partial"  # 部分匹配
    WILDCARD = "wildcard"  # 通配符匹配
    REGEX = "regex"  # 正则表达式匹配


@dataclass(frozen=True)
class KeywordPattern(ValueObject):
    """关键词模式值对象
    
    封装关键词匹配模式，支持多种匹配类型。
    遵循单一职责原则，专门负责关键词模式的表示。
    """
    pattern: str
    type: KeywordType = KeywordType.EXACT
    case_sensitive: bool = False
    weight: float = 1.0  # 匹配权重
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.pattern,
            self.type,
            self.case_sensitive,
            self.weight
        )
    
    def compile_regex(self) -> Optional[Pattern]:
        """编译正则表达式
        
        Returns:
            Optional[Pattern]: 编译后的正则表达式，如果不是正则类型则返回None
        """
        if self.type == KeywordType.REGEX:
            try:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return re.compile(self.pattern, flags)
            except re.error:
                return None
        return None
    
    def matches(self, text: str) -> bool:
        """检查文本是否匹配关键词模式
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 是否匹配
        """
        if not text:
            return False
        
        search_text = text if self.case_sensitive else text.lower()
        search_pattern = self.pattern if self.case_sensitive else self.pattern.lower()
        
        if self.type == KeywordType.EXACT:
            return search_pattern == search_text
        elif self.type == KeywordType.PARTIAL:
            return search_pattern in search_text
        elif self.type == KeywordType.WILDCARD:
            # 简单的通配符支持，*匹配任意字符
            regex_pattern = search_pattern.replace('*', '.*')
            return re.fullmatch(regex_pattern, search_text) is not None
        elif self.type == KeywordType.REGEX:
            regex = self.compile_regex()
            return regex.search(text) is not None if regex else False
        
        return False


@dataclass(frozen=True)
class ActivationRule(ValueObject):
    """激活规则值对象
    
    封装条目激活的条件和规则。
    遵循单一职责原则，专门负责激活规则的管理。
    """
    type: ActivationType = ActivationType.KEYWORD
    keywords: List[KeywordPattern] = field(default_factory=list)
    priority: int = 0  # 优先级，数字越大优先级越高
    max_activations: Optional[int] = None  # 最大激活次数
    cooldown_seconds: Optional[int] = None  # 冷却时间（秒）
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.type,
            tuple(self.keywords),
            self.priority,
            self.max_activations,
            self.cooldown_seconds
        )
    
    def should_activate(self, text: str, context: Dict[str, Any] = None) -> bool:
        """判断是否应该激活
        
        Args:
            text: 触发文本
            context: 上下文信息
            
        Returns:
            bool: 是否应该激活
        """
        if self.type == ActivationType.ALWAYS:
            return True
        elif self.type == ActivationType.MANUAL:
            return False
        elif self.type in [ActivationType.KEYWORD, ActivationType.REGEX]:
            # 检查关键词匹配
            for keyword in self.keywords:
                if keyword.matches(text):
                    return True
            return False
        
        return False
    
    def validate(self) -> List[str]:
        """验证激活规则
        
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if self.type in [ActivationType.KEYWORD, ActivationType.REGEX] and not self.keywords:
            errors.append("关键词或正则激活类型必须指定关键词")
        
        if self.max_activations is not None and self.max_activations <= 0:
            errors.append("最大激活次数必须大于0")
        
        if self.cooldown_seconds is not None and self.cooldown_seconds < 0:
            errors.append("冷却时间不能小于0")
        
        # 验证关键词模式
        for keyword in self.keywords:
            if keyword.type == KeywordType.REGEX:
                if not keyword.compile_regex():
                    errors.append(f"无效的正则表达式: {keyword.pattern}")
        
        return errors


@dataclass
class LorebookEntry(Entity):
    """传说书条目实体
    
    表示传说书中的一个条目，包含内容、关键词和激活规则。
    遵循单一职责原则，专门负责条目信息的管理。
    """
    title: str
    content: str
    keywords: List[KeywordPattern] = field(default_factory=list)
    activation_rule: ActivationRule = field(default_factory=ActivationRule)
    tags: Set[str] = field(default_factory=set)
    is_active: bool = True
    activation_count: int = 0
    last_activated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not hasattr(self, "_id"):
            AggregateRoot.__init__(self)
        if not self.title or not self.title.strip():
            raise ValidationException("条目标题不能为空")
        
        if not self.content or not self.content.strip():
            raise ValidationException("条目内容不能为空")
        
        # 验证激活规则
        validation_errors = self.activation_rule.validate()
        if validation_errors:
            raise ValidationException(f"激活规则验证失败: {', '.join(validation_errors)}")
    
    def activate(self, context: Dict[str, Any] = None) -> bool:
        """激活条目
        
        Args:
            context: 激活上下文
            
        Returns:
            bool: 是否成功激活
        """
        if not self.is_active:
            return False
        
        # 检查最大激活次数
        if (self.activation_rule.max_activations is not None and 
            self.activation_count >= self.activation_rule.max_activations):
            return False
        
        # 检查冷却时间
        if (self.activation_rule.cooldown_seconds is not None and 
            self.last_activated_at is not None):
            cooldown_end = self.last_activated_at.timestamp() + self.activation_rule.cooldown_seconds
            if datetime.now().timestamp() < cooldown_end:
                return False
        
        # 激活条目
        self.activation_count += 1
        self.last_activated_at = datetime.now()
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("lorebook_entry_activated", {
            "entry_id": str(self.id),
            "title": self.title,
            "activation_count": self.activation_count,
            "context": context or {}
        }))
        
        return True
    
    def deactivate(self) -> None:
        """停用条目"""
        if self.is_active:
            self.is_active = False
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(LorebookDomainEvent("lorebook_entry_deactivated", {
                "entry_id": str(self.id),
                "title": self.title
            }))
    
    def reactivate(self) -> None:
        """重新激活条目"""
        if not self.is_active:
            self.is_active = True
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(LorebookDomainEvent("lorebook_entry_reactivated", {
                "entry_id": str(self.id),
                "title": self.title
            }))
    
    def update_content(self, title: str, content: str) -> None:
        """更新条目内容
        
        Args:
            title: 新标题
            content: 新内容
        """
        if not title or not title.strip():
            raise ValidationException("条目标题不能为空")
        
        if not content or not content.strip():
            raise ValidationException("条目内容不能为空")
        
        old_title = self.title
        self.title = title
        self.content = content
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("lorebook_entry_updated", {
            "entry_id": str(self.id),
            "old_title": old_title,
            "new_title": title
        }))
    
    def add_keyword(self, keyword: KeywordPattern) -> None:
        """添加关键词
        
        Args:
            keyword: 关键词模式
        """
        self.keywords.append(keyword)
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("keyword_added", {
            "entry_id": str(self.id),
            "keyword": keyword.pattern,
            "type": keyword.type.value
        }))
    
    def remove_keyword(self, keyword_pattern: str) -> bool:
        """移除关键词
        
        Args:
            keyword_pattern: 关键词模式
            
        Returns:
            bool: 是否成功移除
        """
        for i, keyword in enumerate(self.keywords):
            if keyword.pattern == keyword_pattern:
                removed_keyword = self.keywords.pop(i)
                self._mark_as_updated()
                
                # 添加领域事件
                self.add_domain_event(LorebookDomainEvent("keyword_removed", {
                    "entry_id": str(self.id),
                    "keyword": removed_keyword.pattern,
                    "type": removed_keyword.type.value
                }))
                
                return True
        
        return False
    
    def add_tag(self, tag: str) -> None:
        """添加标签
        
        Args:
            tag: 标签
        """
        if tag and tag.strip():
            self.tags.add(tag.strip())
            self._mark_as_updated()
    
    def remove_tag(self, tag: str) -> bool:
        """移除标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功移除
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self._mark_as_updated()
            return True
        return False
    
    def can_activate(self, text: str, context: Dict[str, Any] = None) -> bool:
        """检查是否可以激活
        
        Args:
            text: 触发文本
            context: 上下文信息
            
        Returns:
            bool: 是否可以激活
        """
        if not self.is_active:
            return False
        
        # 检查激活规则
        if not self.activation_rule.should_activate(text, context):
            return False
        
        # 检查最大激活次数
        if (self.activation_rule.max_activations is not None and 
            self.activation_count >= self.activation_rule.max_activations):
            return False
        
        # 检查冷却时间
        if (self.activation_rule.cooldown_seconds is not None and 
            self.last_activated_at is not None):
            cooldown_end = self.last_activated_at.timestamp() + self.activation_rule.cooldown_seconds
            if datetime.now().timestamp() < cooldown_end:
                return False
        
        return True
    
    def get_activation_score(self, text: str) -> float:
        """获取激活分数
        
        Args:
            text: 触发文本
            
        Returns:
            float: 激活分数
        """
        if not self.is_active:
            return 0.0
        
        score = 0.0
        
        # 计算关键词匹配分数
        for keyword in self.keywords:
            if keyword.matches(text):
                score += keyword.weight
        
        # 考虑优先级
        score += self.activation_rule.priority * 0.1
        
        return score
    
    def validate(self) -> None:
        """验证条目状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not self.title or not self.title.strip():
            raise ValidationException("条目标题不能为空")
        
        if not self.content or not self.content.strip():
            raise ValidationException("条目内容不能为空")
        
        # 验证激活规则
        validation_errors = self.activation_rule.validate()
        if validation_errors:
            raise ValidationException(f"激活规则验证失败: {', '.join(validation_errors)}")
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []


@dataclass
class Lorebook(AggregateRoot):
    """传说书聚合根
    
    管理多个传说书条目的集合，提供条目的组织和检索功能。
    遵循单一职责原则，专门负责传说书的管理。
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entries: List[LorebookEntry] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        if not hasattr(self, "_id"):
            AggregateRoot.__init__(self)
        if not self.name or not self.name.strip():
            raise ValidationException("传说书名称不能为空")
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("lorebook_created", {
            "lorebook_id": str(self.id),
            "name": self.name,
            "description": self.description[:100] + "..." if len(self.description) > 100 else self.description
        }))
    
    def add_entry(self, entry: LorebookEntry) -> None:
        """添加条目
        
        Args:
            entry: 传说书条目
        """
        # 检查是否已存在相同标题的条目
        for existing_entry in self.entries:
            if existing_entry.title == entry.title:
                raise BusinessRuleException(f"已存在相同标题的条目: {entry.title}")
        
        self.entries.append(entry)
        self.add_child_entity(entry)
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("lorebook_entry_added", {
            "lorebook_id": str(self.id),
            "entry_id": str(entry.id),
            "title": entry.title
        }))
    
    def remove_entry(self, entry_id: str) -> bool:
        """移除条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            bool: 是否成功移除
        """
        for i, entry in enumerate(self.entries):
            if str(entry.id) == entry_id:
                removed_entry = self.entries.pop(i)
                self.remove_child_entity(removed_entry)
                self._mark_as_updated()
                
                # 添加领域事件
                self.add_domain_event(LorebookDomainEvent("lorebook_entry_removed", {
                    "lorebook_id": str(self.id),
                    "entry_id": entry_id,
                    "title": removed_entry.title
                }))
                
                return True
        
        return False
    
    def get_entry_by_id(self, entry_id: str) -> Optional[LorebookEntry]:
        """根据ID获取条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            Optional[LorebookEntry]: 条目对象，如果不存在则返回None
        """
        for entry in self.entries:
            if str(entry.id) == entry_id:
                return entry
        return None
    
    def get_entry_by_title(self, title: str) -> Optional[LorebookEntry]:
        """根据标题获取条目
        
        Args:
            title: 条目标题
            
        Returns:
            Optional[LorebookEntry]: 条目对象，如果不存在则返回None
        """
        for entry in self.entries:
            if entry.title == title:
                return entry
        return None
    
    def find_entries_by_keyword(self, text: str) -> List[LorebookEntry]:
        """根据关键词查找条目
        
        Args:
            text: 搜索文本
            
        Returns:
            List[LorebookEntry]: 匹配的条目列表
        """
        matching_entries = []
        
        for entry in self.entries:
            if entry.can_activate(text):
                matching_entries.append(entry)
        
        # 按激活分数排序
        matching_entries.sort(key=lambda e: e.get_activation_score(text), reverse=True)
        
        return matching_entries
    
    def find_entries_by_tag(self, tag: str) -> List[LorebookEntry]:
        """根据标签查找条目
        
        Args:
            tag: 标签
            
        Returns:
            List[LorebookEntry]: 匹配的条目列表
        """
        return [entry for entry in self.entries if tag in entry.tags]
    
    def get_active_entries(self) -> List[LorebookEntry]:
        """获取所有活跃条目
        
        Returns:
            List[LorebookEntry]: 活跃条目列表
        """
        return [entry for entry in self.entries if entry.is_active]
    
    def activate_entries(self, text: str, context: Dict[str, Any] = None) -> List[LorebookEntry]:
        """激活匹配的条目
        
        Args:
            text: 触发文本
            context: 上下文信息
            
        Returns:
            List[LorebookEntry]: 成功激活的条目列表
        """
        activated_entries = []
        
        # 找到可以激活的条目
        candidate_entries = self.find_entries_by_keyword(text)
        
        # 按优先级排序
        candidate_entries.sort(key=lambda e: e.activation_rule.priority, reverse=True)
        
        # 激活条目
        for entry in candidate_entries:
            if entry.activate(context):
                activated_entries.append(entry)
        
        if activated_entries:
            # 添加领域事件
            self.add_domain_event(LorebookDomainEvent("lorebook_entries_activated", {
                "lorebook_id": str(self.id),
                "activated_count": len(activated_entries),
                "trigger_text": text,
                "entry_ids": [str(e.id) for e in activated_entries]
            }))
        
        return activated_entries
    
    def update_info(self, name: str = None, description: str = None) -> None:
        """更新传说书信息
        
        Args:
            name: 新名称
            description: 新描述
        """
        old_name = self.name
        
        if name is not None and name.strip():
            self.name = name.strip()
        
        if description is not None:
            self.description = description
        
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(LorebookDomainEvent("lorebook_updated", {
            "lorebook_id": str(self.id),
            "old_name": old_name,
            "new_name": self.name
        }))
    
    def add_tag(self, tag: str) -> None:
        """添加标签
        
        Args:
            tag: 标签
        """
        if tag and tag.strip():
            self.tags.add(tag.strip())
            self._mark_as_updated()
    
    def remove_tag(self, tag: str) -> bool:
        """移除标签
        
        Args:
            tag: 标签
            
        Returns:
            bool: 是否成功移除
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self._mark_as_updated()
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        active_entries = self.get_active_entries()
        total_activations = sum(entry.activation_count for entry in self.entries)
        
        return {
            "total_entries": len(self.entries),
            "active_entries": len(active_entries),
            "total_activations": total_activations,
            "average_activations": total_activations / len(self.entries) if self.entries else 0,
            "tags": list(self.tags),
            "version": self.version
        }
    
    def validate(self) -> None:
        """验证传说书状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not self.name or not self.name.strip():
            raise ValidationException("传说书名称不能为空")
        
        # 验证所有条目
        for entry in self.entries:
            entry.validate()
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []


@dataclass
class KeywordMatcher:
    """关键词匹配器
    
    提供高效的关键词匹配功能，支持多种匹配类型。
    遵循单一职责原则，专门负责关键词匹配逻辑。
    """
    keywords: List[KeywordPattern] = field(default_factory=list)
    case_sensitive: bool = False
    
    def add_keyword(self, keyword: KeywordPattern) -> None:
        """添加关键词
        
        Args:
            keyword: 关键词模式
        """
        self.keywords.append(keyword)
    
    def remove_keyword(self, pattern: str) -> bool:
        """移除关键词
        
        Args:
            pattern: 关键词模式
            
        Returns:
            bool: 是否成功移除
        """
        for i, keyword in enumerate(self.keywords):
            if keyword.pattern == pattern:
                self.keywords.pop(i)
                return True
        return False
    
    def match(self, text: str) -> List[KeywordPattern]:
        """匹配关键词
        
        Args:
            text: 要匹配的文本
            
        Returns:
            List[KeywordPattern]: 匹配的关键词列表
        """
        matched_keywords = []
        
        for keyword in self.keywords:
            if keyword.matches(text):
                matched_keywords.append(keyword)
        
        # 按权重排序
        matched_keywords.sort(key=lambda k: k.weight, reverse=True)
        
        return matched_keywords
    
    def get_best_match(self, text: str) -> Optional[KeywordPattern]:
        """获取最佳匹配
        
        Args:
            text: 要匹配的文本
            
        Returns:
            Optional[KeywordPattern]: 最佳匹配的关键词，如果没有匹配则返回None
        """
        matches = self.match(text)
        return matches[0] if matches else None
    
    def clear(self) -> None:
        """清除所有关键词"""
        self.keywords.clear()