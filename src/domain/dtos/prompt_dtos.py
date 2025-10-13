"""
提示组装数据传输对象

该模块定义了提示组装相关的数据传输对象，遵循SOLID原则，
特别是单一职责原则(SRP)，每个DTO都有明确的职责。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from ..models.prompt import (
    PromptSectionType, TruncationStrategy, LLMProvider,
    PromptSection, PromptContext, PromptTemplate
)


class PromptFormat(Enum):
    """提示格式枚举"""
    JSON = "json"
    TEXT = "text"
    MARKDOWN = "markdown"
    XML = "xml"


@dataclass
class PromptTemplateDto:
    """提示模板数据传输对象
    
    用于传输提示模板的基本信息，遵循单一职责原则，
    专门负责提示模板数据的传输。
    """
    id: str
    name: str
    description: str
    sections: List[Dict[str, Any]] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_domain(cls, template: PromptTemplate) -> 'PromptTemplateDto':
        """从领域对象创建DTO
        
        Args:
            template: 提示模板领域对象
            
        Returns:
            PromptTemplateDto: 提示模板DTO实例
        """
        sections_data = []
        for section in template.sections:
            sections_data.append({
                'content': section.content,
                'section_type': section.section_type.value,
                'priority': section.priority,
                'token_count': section.token_count,
                'metadata': section.metadata
            })
        
        return cls(
            id=str(template.id),
            name=template.name,
            description=template.description,
            sections=sections_data,
            variables=list(template.variables),
            metadata=template.metadata,
            version=template.version,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
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
            'sections': self.sections,
            'variables': self.variables,
            'metadata': self.metadata,
            'version': self.version,
            'is_active': self.is_active,
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        
        return result


@dataclass
class PromptTemplateListDto:
    """提示模板列表响应对象
    
    用于传输提示模板列表信息，遵循单一职责原则，
    专门负责提示模板列表数据的传输。
    """
    templates: List[PromptTemplateDto]
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
            'templates': [t.to_dict() for t in self.templates],
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages,
        }


@dataclass
class PromptSectionDto:
    """提示段落数据传输对象
    
    用于传输提示段落信息，遵循单一职责原则，
    专门负责提示段落数据的传输。
    """
    content: str
    section_type: PromptSectionType = PromptSectionType.CUSTOM
    priority: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_domain(cls, section: PromptSection) -> 'PromptSectionDto':
        """从领域对象创建DTO
        
        Args:
            section: 提示段落领域对象
            
        Returns:
            PromptSectionDto: 提示段落DTO实例
        """
        return cls(
            content=section.content,
            section_type=section.section_type,
            priority=section.priority,
            token_count=section.token_count,
            metadata=section.metadata,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'content': self.content,
            'section_type': self.section_type.value,
            'priority': self.priority,
            'token_count': self.token_count,
            'metadata': self.metadata,
        }


@dataclass
class PromptContextDto:
    """提示上下文数据传输对象
    
    用于传输提示上下文信息，遵循单一职责原则，
    专门负责提示上下文数据的传输。
    """
    character_name: str = ""
    character_description: str = ""
    world_info: str = ""
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    current_input: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_domain(cls, context: PromptContext) -> 'PromptContextDto':
        """从领域对象创建DTO
        
        Args:
            context: 提示上下文领域对象
            
        Returns:
            PromptContextDto: 提示上下文DTO实例
        """
        return cls(
            character_name=context.character_name,
            character_description=context.character_description,
            world_info=context.world_info,
            chat_history=context.chat_history,
            current_input=context.current_input,
            variables=context.variables,
            metadata=context.metadata,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'character_name': self.character_name,
            'character_description': self.character_description,
            'world_info': self.world_info,
            'chat_history': self.chat_history,
            'current_input': self.current_input,
            'variables': self.variables,
            'metadata': self.metadata,
        }


@dataclass
class PromptBuildDto:
    """提示构建请求对象
    
    用于传输构建提示的请求数据，遵循单一职责原则，
    专门负责构建请求数据的传输。
    """
    template_id: str
    context: PromptContextDto
    token_limit: Optional[Dict[str, Any]] = None
    truncation_strategy: TruncationStrategy = TruncationStrategy.SMART
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.template_id or not self.template_id.strip():
            errors.append("模板ID不能为空")
        
        # 验证上下文
        context_errors = self.context.validate()
        errors.extend(context_errors)
        
        # 验证token限制
        if self.token_limit:
            if not isinstance(self.token_limit, dict):
                errors.append("token_limit必须是字典格式")
            else:
                required_fields = ['provider', 'model_name', 'max_tokens']
                for field in required_fields:
                    if field not in self.token_limit:
                        errors.append(f"token_limit缺少必需字段: {field}")
        
        return errors


@dataclass
class PromptPreviewDto:
    """提示预览响应对象
    
    用于传输提示预览的响应数据，遵循单一职责原则，
    专门负责预览响应数据的传输。
    """
    prompt: str
    token_count: int
    sections: List[PromptSectionDto]
    variables_used: Dict[str, str]
    missing_variables: List[str]
    truncation_applied: bool = False
    build_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'prompt': self.prompt,
            'token_count': self.token_count,
            'sections': [s.to_dict() for s in self.sections],
            'variables_used': self.variables_used,
            'missing_variables': self.missing_variables,
            'truncation_applied': self.truncation_applied,
            'build_time_ms': self.build_time_ms,
        }


@dataclass
class PromptStatisticsDto:
    """提示统计信息对象
    
    用于传输提示统计信息，遵循单一职责原则，
    专门负责统计信息数据的传输。
    """
    template_id: str
    template_name: str
    total_sections: int
    total_tokens: int
    sections_by_type: Dict[str, int]
    tokens_by_type: Dict[str, int]
    variable_count: int
    average_section_tokens: float
    largest_section: Dict[str, Any]
    created_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        result = {
            'template_id': self.template_id,
            'template_name': self.template_name,
            'total_sections': self.total_sections,
            'total_tokens': self.total_tokens,
            'sections_by_type': self.sections_by_type,
            'tokens_by_type': self.tokens_by_type,
            'variable_count': self.variable_count,
            'average_section_tokens': self.average_section_tokens,
            'largest_section': self.largest_section,
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.last_used:
            result['last_used'] = self.last_used.isoformat()
        
        return result


@dataclass
class PromptTemplateCreateDto:
    """创建提示模板请求对象
    
    用于传输创建提示模板的请求数据，遵循单一职责原则，
    专门负责创建请求数据的传输。
    """
    name: str
    description: str = ""
    sections: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("模板名称不能为空")
        
        # 验证段落
        for i, section_data in enumerate(self.sections):
            if not section_data.get('content', '').strip():
                errors.append(f"段落 {i} 内容不能为空")
            
            section_type = section_data.get('section_type', 'custom')
            try:
                PromptSectionType(section_type)
            except ValueError:
                errors.append(f"段落 {i} 类型无效: {section_type}")
            
            priority = section_data.get('priority', 0)
            if not isinstance(priority, int):
                errors.append(f"段落 {i} 优先级必须是整数")
        
        # 验证版本
        if not self.version or not self.version.strip():
            errors.append("版本不能为空")
        
        return errors


@dataclass
class PromptTemplateUpdateDto:
    """更新提示模板请求对象
    
    用于传输更新提示模板的请求数据，遵循单一职责原则，
    专门负责更新请求数据的传输。
    """
    name: Optional[str] = None
    description: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证名称
        if self.name is not None and not self.name.strip():
            errors.append("模板名称不能为空")
        
        # 验证段落
        if self.sections is not None:
            for i, section_data in enumerate(self.sections):
                if not section_data.get('content', '').strip():
                    errors.append(f"段落 {i} 内容不能为空")
                
                section_type = section_data.get('section_type', 'custom')
                try:
                    PromptSectionType(section_type)
                except ValueError:
                    errors.append(f"段落 {i} 类型无效: {section_type}")
                
                priority = section_data.get('priority', 0)
                if not isinstance(priority, int):
                    errors.append(f"段落 {i} 优先级必须是整数")
        
        # 验证版本
        if self.version is not None and not self.version.strip():
            errors.append("版本不能为空")
        
        return errors


@dataclass
class PromptTokenCountDto:
    """Token计数请求对象
    
    用于传输Token计数的请求数据，遵循单一职责原则，
    专门负责Token计数请求数据的传输。
    """
    text: str
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-3.5-turbo"
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.text.strip():
            errors.append("文本内容不能为空")
        
        if not self.model_name or not self.model_name.strip():
            errors.append("模型名称不能为空")
        
        return errors


@dataclass
class PromptTokenCountResponseDto:
    """Token计数响应对象
    
    用于传输Token计数的响应数据，遵循单一职责原则，
    专门负责Token计数响应数据的传输。
    """
    token_count: int
    character_count: int
    provider: LLMProvider
    model_name: str
    calculation_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'token_count': self.token_count,
            'character_count': self.character_count,
            'provider': self.provider.value,
            'model_name': self.model_name,
            'calculation_time_ms': self.calculation_time_ms,
        }


@dataclass
class PromptExportDto:
    """导出提示模板响应对象
    
    用于传输导出提示模板的响应数据，遵循单一职责原则，
    专门负责导出响应数据的传输。
    """
    data: Dict[str, Any]
    format: PromptFormat = PromptFormat.JSON
    filename: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'data': self.data,
            'format': self.format.value,
            'filename': self.filename,
        }


@dataclass
class PromptImportDto:
    """导入提示模板请求对象
    
    用于传输导入提示模板的请求数据，遵循单一职责原则，
    专门负责导入请求数据的传输。
    """
    data: Dict[str, Any]
    format: PromptFormat = PromptFormat.JSON
    overwrite: bool = False
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.data:
            errors.append("导入数据不能为空")
        
        if self.format not in [PromptFormat.JSON, PromptFormat.TEXT]:
            errors.append("不支持的导入格式")
        
        if self.format == PromptFormat.JSON:
            if not self.data.get("name"):
                errors.append("模板名称不能为空")
        
        return errors


# 为PromptContextDto添加validate方法
def _prompt_context_dto_validate(self) -> List[str]:
    """验证上下文数据
    
    Returns:
        List[str]: 验证错误列表，空列表表示验证通过
    """
    errors = []
    
    # 验证聊天历史格式
    if self.chat_history:
        for i, message in enumerate(self.chat_history):
            if not isinstance(message, dict):
                errors.append(f"聊天历史消息 {i} 必须是字典格式")
                continue
            
            if 'role' not in message:
                errors.append(f"聊天历史消息 {i} 缺少role字段")
            
            if 'content' not in message:
                errors.append(f"聊天历史消息 {i} 缺少content字段")
    
    return errors


# 动态添加方法到类
PromptContextDto.validate = _prompt_context_dto_validate