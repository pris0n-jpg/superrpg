"""
传说书数据传输对象

该模块定义了传说书相关的数据传输对象，遵循SOLID原则，
特别是单一职责原则(SRP)，每个DTO都有明确的职责。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class KeywordPatternDto:
    """关键词模式数据传输对象
    
    用于传输关键词匹配模式信息，遵循单一职责原则，
    专门负责关键词模式数据的传输。
    """
    pattern: str
    type: str = "exact"  # exact, partial, wildcard, regex
    case_sensitive: bool = False
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'pattern': self.pattern,
            'type': self.type,
            'case_sensitive': self.case_sensitive,
            'weight': self.weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeywordPatternDto':
        """从字典创建DTO
        
        Args:
            data: 字典数据
            
        Returns:
            KeywordPatternDto: 关键词模式DTO实例
        """
        return cls(
            pattern=data.get('pattern', ''),
            type=data.get('type', 'exact'),
            case_sensitive=data.get('case_sensitive', False),
            weight=data.get('weight', 1.0)
        )


@dataclass
class ActivationRuleDto:
    """激活规则数据传输对象
    
    用于传输条目激活规则信息，遵循单一职责原则，
    专门负责激活规则数据的传输。
    """
    type: str = "keyword"  # always, keyword, regex, manual
    keywords: List[KeywordPatternDto] = field(default_factory=list)
    priority: int = 0
    max_activations: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'type': self.type,
            'keywords': [keyword.to_dict() for keyword in self.keywords],
            'priority': self.priority,
            'max_activations': self.max_activations,
            'cooldown_seconds': self.cooldown_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivationRuleDto':
        """从字典创建DTO
        
        Args:
            data: 字典数据
            
        Returns:
            ActivationRuleDto: 激活规则DTO实例
        """
        keywords_data = data.get('keywords', [])
        keywords = [KeywordPatternDto.from_dict(k) for k in keywords_data]
        
        return cls(
            type=data.get('type', 'keyword'),
            keywords=keywords,
            priority=data.get('priority', 0),
            max_activations=data.get('max_activations'),
            cooldown_seconds=data.get('cooldown_seconds')
        )


@dataclass
class LorebookEntryDto:
    """传说书条目数据传输对象
    
    用于传输传说书条目信息，遵循单一职责原则，
    专门负责条目数据的传输。
    """
    id: str
    title: str
    content: str
    keywords: List[KeywordPatternDto] = field(default_factory=list)
    activation_rule: ActivationRuleDto = field(default_factory=ActivationRuleDto)
    tags: List[str] = field(default_factory=list)
    is_active: bool = True
    activation_count: int = 0
    last_activated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_domain(cls, lorebook_entry) -> 'LorebookEntryDto':
        """从领域对象创建DTO
        
        Args:
            lorebook_entry: 传说书条目领域对象
            
        Returns:
            LorebookEntryDto: 传说书条目DTO实例
        """
        # 转换关键词
        keywords = [
            KeywordPatternDto(
                pattern=keyword.pattern,
                type=keyword.type.value,
                case_sensitive=keyword.case_sensitive,
                weight=keyword.weight
            ) for keyword in lorebook_entry.keywords
        ]
        
        # 转换激活规则
        activation_rule = ActivationRuleDto(
            type=lorebook_entry.activation_rule.type.value,
            keywords=keywords,
            priority=lorebook_entry.activation_rule.priority,
            max_activations=lorebook_entry.activation_rule.max_activations,
            cooldown_seconds=lorebook_entry.activation_rule.cooldown_seconds
        )
        
        return cls(
            id=str(lorebook_entry.id),
            title=lorebook_entry.title,
            content=lorebook_entry.content,
            keywords=keywords,
            activation_rule=activation_rule,
            tags=list(lorebook_entry.tags),
            is_active=lorebook_entry.is_active,
            activation_count=lorebook_entry.activation_count,
            last_activated_at=lorebook_entry.last_activated_at,
            metadata=lorebook_entry.metadata,
            created_at=lorebook_entry.created_at,
            updated_at=lorebook_entry.updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'keywords': [keyword.to_dict() for keyword in self.keywords],
            'activation_rule': self.activation_rule.to_dict(),
            'tags': self.tags,
            'is_active': self.is_active,
            'activation_count': self.activation_count,
            'metadata': self.metadata
        }
        
        if self.last_activated_at:
            result['last_activated_at'] = self.last_activated_at.isoformat()
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LorebookEntryDto':
        """从字典创建DTO
        
        Args:
            data: 字典数据
            
        Returns:
            LorebookEntryDto: 传说书条目DTO实例
        """
        keywords_data = data.get('keywords', [])
        keywords = [KeywordPatternDto.from_dict(k) for k in keywords_data]
        
        activation_rule_data = data.get('activation_rule', {})
        activation_rule = ActivationRuleDto.from_dict(activation_rule_data)
        
        # 处理时间字段
        last_activated_at = None
        if data.get('last_activated_at'):
            last_activated_at = datetime.fromisoformat(data['last_activated_at'])
        
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            keywords=keywords,
            activation_rule=activation_rule,
            tags=data.get('tags', []),
            is_active=data.get('is_active', True),
            activation_count=data.get('activation_count', 0),
            last_activated_at=last_activated_at,
            metadata=data.get('metadata', {}),
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class LorebookDto:
    """传说书数据传输对象
    
    用于传输传说书信息，遵循单一职责原则，
    专门负责传说书数据的传输。
    """
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    entries: List[LorebookEntryDto] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_domain(cls, lorebook) -> 'LorebookDto':
        """从领域对象创建DTO
        
        Args:
            lorebook: 传说书领域对象
            
        Returns:
            LorebookDto: 传说书DTO实例
        """
        entries = [LorebookEntryDto.from_domain(entry) for entry in lorebook.entries]
        
        return cls(
            id=str(lorebook.id),
            name=lorebook.name,
            description=lorebook.description,
            version=lorebook.version,
            tags=list(lorebook.tags),
            metadata=lorebook.metadata,
            entries=entries,
            created_at=lorebook.created_at,
            updated_at=lorebook.updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'tags': self.tags,
            'metadata': self.metadata,
            'entries': [entry.to_dict() for entry in self.entries]
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LorebookDto':
        """从字典创建DTO
        
        Args:
            data: 字典数据
            
        Returns:
            LorebookDto: 传说书DTO实例
        """
        entries_data = data.get('entries', [])
        entries = [LorebookEntryDto.from_dict(entry) for entry in entries_data]
        
        # 处理时间字段
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'])
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            entries=entries,
            created_at=created_at,
            updated_at=updated_at
        )


@dataclass
class LorebookListDto:
    """传说书列表响应对象
    
    用于传输传说书列表信息，遵循单一职责原则，
    专门负责传说书列表数据的传输。
    """
    lorebooks: List[LorebookDto]
    total_count: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'lorebooks': [lorebook.to_dict() for lorebook in self.lorebooks],
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages
        }


@dataclass
class LorebookCreateDto:
    """创建传说书请求对象
    
    用于传输创建传说书的请求数据，遵循单一职责原则，
    专门负责创建请求数据的传输。
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("传说书名称不能为空")
        
        if self.version and not self.version.strip():
            errors.append("版本号不能为空字符串")
        
        return errors


@dataclass
class LorebookUpdateDto:
    """更新传说书请求对象
    
    用于传输更新传说书的请求数据，遵循单一职责原则，
    专门负责更新请求数据的传输。
    """
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if self.name is not None and not self.name.strip():
            errors.append("传说书名称不能为空")
        
        if self.version is not None and not self.version.strip():
            errors.append("版本号不能为空字符串")
        
        return errors


@dataclass
class LorebookEntryCreateDto:
    """创建传说书条目请求对象
    
    用于传输创建传说书条目的请求数据，遵循单一职责原则，
    专门负责创建条目请求数据的传输。
    """
    title: str
    content: str
    keywords: List[KeywordPatternDto] = field(default_factory=list)
    activation_rule: ActivationRuleDto = field(default_factory=ActivationRuleDto)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.title or not self.title.strip():
            errors.append("条目标题不能为空")
        
        if not self.content or not self.content.strip():
            errors.append("条目内容不能为空")
        
        # 验证激活规则
        if self.activation_rule.type in ["keyword", "regex"] and not self.activation_rule.keywords:
            errors.append("关键词或正则激活类型必须指定关键词")
        
        if self.activation_rule.max_activations is not None and self.activation_rule.max_activations <= 0:
            errors.append("最大激活次数必须大于0")
        
        if self.activation_rule.cooldown_seconds is not None and self.activation_rule.cooldown_seconds < 0:
            errors.append("冷却时间不能小于0")
        
        # 验证关键词
        for keyword in self.activation_rule.keywords:
            if keyword.type == "regex":
                try:
                    import re
                    flags = 0 if keyword.case_sensitive else re.IGNORECASE
                    re.compile(keyword.pattern, flags)
                except re.error:
                    errors.append(f"无效的正则表达式: {keyword.pattern}")
        
        return errors


@dataclass
class LorebookEntryUpdateDto:
    """更新传说书条目请求对象
    
    用于传输更新传说书条目的请求数据，遵循单一职责原则，
    专门负责更新条目请求数据的传输。
    """
    title: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[KeywordPatternDto]] = None
    activation_rule: Optional[ActivationRuleDto] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if self.title is not None and not self.title.strip():
            errors.append("条目标题不能为空")
        
        if self.content is not None and not self.content.strip():
            errors.append("条目内容不能为空")
        
        # 验证激活规则
        if self.activation_rule:
            if self.activation_rule.type in ["keyword", "regex"] and not self.activation_rule.keywords:
                errors.append("关键词或正则激活类型必须指定关键词")
            
            if self.activation_rule.max_activations is not None and self.activation_rule.max_activations <= 0:
                errors.append("最大激活次数必须大于0")
            
            if self.activation_rule.cooldown_seconds is not None and self.activation_rule.cooldown_seconds < 0:
                errors.append("冷却时间不能小于0")
            
            # 验证关键词
            for keyword in self.activation_rule.keywords:
                if keyword.type == "regex":
                    try:
                        import re
                        flags = 0 if keyword.case_sensitive else re.IGNORECASE
                        re.compile(keyword.pattern, flags)
                    except re.error:
                        errors.append(f"无效的正则表达式: {keyword.pattern}")
        
        return errors


@dataclass
class LorebookImportDto:
    """导入传说书请求对象
    
    用于传输导入传说书的请求数据，遵循单一职责原则，
    专门负责导入请求数据的传输。
    """
    data: Dict[str, Any]
    format: str = "json"  # json, lorebook
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.data:
            errors.append("导入数据不能为空")
        
        if self.format not in ["json", "lorebook"]:
            errors.append("不支持的导入格式")
        
        if self.format == "json":
            if not self.data.get("name"):
                errors.append("传说书名称不能为空")
        
        return errors


@dataclass
class LorebookExportDto:
    """导出传说书响应对象
    
    用于传输导出传说书的响应数据，遵循单一职责原则，
    专门负责导出响应数据的传输。
    """
    data: Dict[str, Any]
    format: str = "json"  # json, lorebook
    filename: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'data': self.data,
            'format': self.format,
            'filename': self.filename
        }


@dataclass
class LorebookActivationDto:
    """传说书激活请求对象
    
    用于传输激活传说书的请求数据，遵循单一职责原则，
    专门负责激活请求数据的传输。
    """
    text: str
    context: Dict[str, Any] = field(default_factory=dict)
    max_entries: Optional[int] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.text or not self.text.strip():
            errors.append("激活文本不能为空")
        
        if self.max_entries is not None and self.max_entries <= 0:
            errors.append("最大条目数必须大于0")
        
        return errors


@dataclass
class LorebookActivationResultDto:
    """传说书激活结果对象
    
    用于传输传说书激活结果，遵循单一职责原则，
    专门负责激活结果数据的传输。
    """
    activated_entries: List[LorebookEntryDto]
    total_candidates: int
    activation_text: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'activated_entries': [entry.to_dict() for entry in self.activated_entries],
            'total_candidates': self.total_candidates,
            'activation_text': self.activation_text,
            'context': self.context
        }


@dataclass
class LorebookStatisticsDto:
    """传说书统计信息对象
    
    用于传输传说书统计信息，遵循单一职责原则，
    专门负责统计信息数据的传输。
    """
    total_entries: int
    active_entries: int
    total_activations: int
    average_activations: float
    tags: List[str]
    version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'total_entries': self.total_entries,
            'active_entries': self.active_entries,
            'total_activations': self.total_activations,
            'average_activations': self.average_activations,
            'tags': self.tags,
            'version': self.version
        }