"""
提示组装领域模型

该模块定义了提示组装相关的领域模型，遵循SOLID原则，
特别是单一职责原则(SRP)和里氏替换原则(LSP)。

模型包括：
1. PromptTemplate - 提示模板模型
2. PromptSection - 提示段落模型
3. PromptContext - 提示上下文模型
4. PromptBuilder - 提示构建器
5. TokenCalculator - Token计算器
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Union, Tuple
from enum import Enum
import re
from datetime import datetime

from .base import AggregateRoot, ValueObject, EntityId
from ...core.interfaces import DomainEvent
from ...core.exceptions import ValidationException, BusinessRuleException


class PromptDomainEvent(DomainEvent):
    """提示领域事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        super().__init__()
        self._event_type = event_type
        self._data = data
    
    def get_event_type(self) -> str:
        return self._event_type
    
    @property
    def data(self) -> Dict[str, Any]:
        return self._data


class PromptSectionType(Enum):
    """提示段落类型枚举"""
    SYSTEM = "system"  # 系统指令
    ROLE = "role"  # 角色描述
    WORLD = "world"  # 世界信息
    HISTORY = "history"  # 聊天历史
    CONTEXT = "context"  # 上下文信息
    INSTRUCTION = "instruction"  # 指令
    EXAMPLE = "example"  # 示例
    CUSTOM = "custom"  # 自定义


class TruncationStrategy(Enum):
    """截断策略枚举"""
    NONE = "none"  # 不截断
    PREFIX = "prefix"  # 从前部截断
    SUFFIX = "suffix"  # 从后部截断
    MIDDLE = "middle"  # 从中间截断
    SMART = "smart"  # 智能截断（保留重要信息）


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    KOBOLDAI = "koboldai"
    CUSTOM = "custom"


@dataclass(frozen=True)
class PromptSection(ValueObject):
    """提示段落值对象
    
    封装提示的一个段落，包含类型、内容和优先级。
    遵循单一职责原则，专门负责提示段落的表示。
    """
    content: str
    section_type: PromptSectionType = PromptSectionType.CUSTOM
    priority: int = 0  # 优先级，数字越大优先级越高
    token_count: int = 0  # 预估token数量
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.content,
            self.section_type,
            self.priority,
            self.token_count,
            tuple(sorted(self.metadata.items()))
        )
    
    def with_variables(self, variables: Dict[str, str]) -> 'PromptSection':
        """使用变量替换内容中的占位符
        
        Args:
            variables: 变量字典
            
        Returns:
            PromptSection: 替换后的新段落
        """
        new_content = self.content
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            new_content = new_content.replace(placeholder, str(value))
        
        return PromptSection(
            content=new_content,
            section_type=self.section_type,
            priority=self.priority,
            token_count=self.token_count,  # 注意：这里没有重新计算
            metadata=self.metadata.copy()
        )


@dataclass(frozen=True)
class PromptContext(ValueObject):
    """提示上下文值对象
    
    封装提示构建的上下文信息，包括角色、世界信息等。
    遵循单一职责原则，专门负责上下文信息的管理。
    """
    character_name: str = ""
    character_description: str = ""
    world_info: str = ""
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    current_input: str = ""
    variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.character_name,
            self.character_description,
            self.world_info,
            tuple(tuple(msg.items()) for msg in self.chat_history),
            self.current_input,
            tuple(sorted(self.variables.items())),
            tuple(sorted(self.metadata.items()))
        )
    
    def with_variable(self, key: str, value: str) -> 'PromptContext':
        """添加或更新变量
        
        Args:
            key: 变量名
            value: 变量值
            
        Returns:
            PromptContext: 更新后的新上下文
        """
        new_variables = self.variables.copy()
        new_variables[key] = value
        
        return PromptContext(
            character_name=self.character_name,
            character_description=self.character_description,
            world_info=self.world_info,
            chat_history=self.chat_history.copy(),
            current_input=self.current_input,
            variables=new_variables,
            metadata=self.metadata.copy()
        )


@dataclass(frozen=True)
class TokenLimit(ValueObject):
    """Token限制值对象
    
    封装不同LLM提供商的Token限制信息。
    遵循单一职责原则，专门负责Token限制的管理。
    """
    provider: LLMProvider
    model_name: str
    max_tokens: int
    reserved_tokens: int = 0  # 预留token数量（用于响应等）
    
    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.provider,
            self.model_name,
            self.max_tokens,
            self.reserved_tokens
        )
    
    @property
    def available_tokens(self) -> int:
        """获取可用token数量"""
        return max(0, self.max_tokens - self.reserved_tokens)


@dataclass
class PromptTemplate(AggregateRoot):
    """提示模板聚合根
    
    管理提示模板的定义和构建规则。
    遵循单一职责原则，专门负责提示模板的管理。
    """
    name: str
    description: str = ""
    sections: List[PromptSection] = field(default_factory=list)
    variables: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    is_active: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        if not hasattr(self, "_id"):
            AggregateRoot.__init__(self)

        if not self.name or not self.name.strip():
            raise ValidationException("模板名称不能为空")
        
        # 验证段落
        for section in self.sections:
            if not section.content or not section.content.strip():
                raise ValidationException("段落内容不能为空")
        
        # 提取变量
        self._extract_variables()
        
        # 添加领域事件
        self.add_domain_event(PromptDomainEvent("prompt_template_created", {
            "template_id": str(self.id),
            "name": self.name,
            "section_count": len(self.sections)
        }))
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出模板为字典结构"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'sections': [
                {
                    'content': section.content,
                    'section_type': section.section_type.value,
                    'priority': section.priority,
                    'token_count': section.token_count,
                    'metadata': section.metadata,
                }
                for section in self.sections
            ],
            'variables': sorted(self.variables),
            'metadata': self.metadata,
            'version': self.version,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def _extract_variables(self) -> None:
        """从段落内容中提取变量"""
        variable_pattern = r'\{([^}]+)\}'
        self.variables.clear()
        
        for section in self.sections:
            matches = re.findall(variable_pattern, section.content)
            self.variables.update(matches)
    
    def add_section(self, section: PromptSection) -> None:
        """添加段落
        
        Args:
            section: 提示段落
        """
        if not section.content or not section.content.strip():
            raise ValidationException("段落内容不能为空")
        
        self.sections.append(section)
        self._extract_variables()
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(PromptDomainEvent("prompt_section_added", {
            "template_id": str(self.id),
            "section_type": section.section_type.value,
            "content_preview": section.content[:50] + "..." if len(section.content) > 50 else section.content
        }))
    
    def remove_section(self, index: int) -> bool:
        """移除段落
        
        Args:
            index: 段落索引
            
        Returns:
            bool: 是否成功移除
        """
        if 0 <= index < len(self.sections):
            removed_section = self.sections.pop(index)
            self._extract_variables()
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(PromptDomainEvent("prompt_section_removed", {
                "template_id": str(self.id),
                "section_type": removed_section.section_type.value
            }))
            
            return True
        
        return False
    
    def update_section(self, index: int, section: PromptSection) -> bool:
        """更新段落
        
        Args:
            index: 段落索引
            section: 新的提示段落
            
        Returns:
            bool: 是否成功更新
        """
        if 0 <= index < len(self.sections):
            if not section.content or not section.content.strip():
                raise ValidationException("段落内容不能为空")
            
            old_section = self.sections[index]
            self.sections[index] = section
            self._extract_variables()
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(PromptDomainEvent("prompt_section_updated", {
                "template_id": str(self.id),
                "section_type": section.section_type.value,
                "old_section_type": old_section.section_type.value
            }))
            
            return True
        
        return False
    
    def reorder_sections(self, indices: List[int]) -> bool:
        """重新排序段落
        
        Args:
            indices: 新的段落索引列表
            
        Returns:
            bool: 是否成功重排序
        """
        if len(indices) != len(self.sections):
            return False
        
        if set(indices) != set(range(len(self.sections))):
            return False
        
        new_sections = [self.sections[i] for i in indices]
        self.sections = new_sections
        self._mark_as_updated()
        
        # 添加领域事件
        self.add_domain_event(PromptDomainEvent("prompt_sections_reordered", {
            "template_id": str(self.id),
            "new_order": indices
        }))
        
        return True
    
    def get_sections_by_type(self, section_type: PromptSectionType) -> List[PromptSection]:
        """根据类型获取段落
        
        Args:
            section_type: 段落类型
            
        Returns:
            List[PromptSection]: 匹配的段落列表
        """
        return [section for section in self.sections if section.section_type == section_type]
    
    def update_info(self, name: str = None, description: str = None) -> None:
        """更新模板信息
        
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
        self.add_domain_event(PromptDomainEvent("prompt_template_updated", {
            "template_id": str(self.id),
            "old_name": old_name,
            "new_name": self.name
        }))
    
    def activate(self) -> None:
        """激活模板"""
        if not self.is_active:
            self.is_active = True
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(PromptDomainEvent("prompt_template_activated", {
                "template_id": str(self.id),
                "name": self.name
            }))
    
    def deactivate(self) -> None:
        """停用模板"""
        if self.is_active:
            self.is_active = False
            self._mark_as_updated()
            
            # 添加领域事件
            self.add_domain_event(PromptDomainEvent("prompt_template_deactivated", {
                "template_id": str(self.id),
                "name": self.name
            }))
    
    def get_total_tokens(self) -> int:
        """获取总token数量"""
        return sum(section.token_count for section in self.sections)
    
    def validate(self) -> None:
        """验证模板状态
        
        Raises:
            ValidationException: 验证失败时抛出
        """
        if not self.name or not self.name.strip():
            raise ValidationException("模板名称不能为空")
        
        if not self.sections:
            raise ValidationException("模板至少需要一个段落")
        
        # 验证段落
        for i, section in enumerate(self.sections):
            if not section.content or not section.content.strip():
                raise ValidationException(f"段落 {i} 内容不能为空")
    
    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表
        
        Returns:
            List[BusinessRule]: 业务规则列表
        """
        return []


@dataclass
class PromptBuilder:
    """提示构建器
    
    负责根据模板和上下文构建最终的提示文本。
    遵循单一职责原则，专门负责提示的构建逻辑。
    """
    template: PromptTemplate
    context: PromptContext
    token_limit: Optional[TokenLimit] = None
    truncation_strategy: TruncationStrategy = TruncationStrategy.SMART
    
    def build_prompt(self) -> str:
        """构建提示
        
        Returns:
            str: 构建的提示文本
        """
        # 应用变量替换
        processed_sections = []
        for section in self.template.sections:
            processed_section = section.with_variables(self.context.variables)
            processed_sections.append(processed_section)
        
        # 按优先级排序
        processed_sections.sort(key=lambda s: s.priority, reverse=True)
        
        # 分层组装
        prompt_parts = []
        
        # 系统指令
        system_sections = [s for s in processed_sections if s.section_type == PromptSectionType.SYSTEM]
        prompt_parts.extend(s.content for s in system_sections)
        
        # 角色描述
        if self.context.character_description:
            prompt_parts.append(self.context.character_description)
        
        role_sections = [s for s in processed_sections if s.section_type == PromptSectionType.ROLE]
        prompt_parts.extend(s.content for s in role_sections)
        
        # 世界信息
        if self.context.world_info:
            prompt_parts.append(self.context.world_info)
        
        world_sections = [s for s in processed_sections if s.section_type == PromptSectionType.WORLD]
        prompt_parts.extend(s.content for s in world_sections)
        
        # 上下文信息
        context_sections = [s for s in processed_sections if s.section_type == PromptSectionType.CONTEXT]
        prompt_parts.extend(s.content for s in context_sections)
        
        # 聊天历史
        if self.context.chat_history:
            history_text = self._format_chat_history()
            if history_text:
                prompt_parts.append(history_text)
        
        history_sections = [s for s in processed_sections if s.section_type == PromptSectionType.HISTORY]
        prompt_parts.extend(s.content for s in history_sections)
        
        # 指令和示例
        instruction_sections = [s for s in processed_sections if s.section_type == PromptSectionType.INSTRUCTION]
        prompt_parts.extend(s.content for s in instruction_sections)
        
        example_sections = [s for s in processed_sections if s.section_type == PromptSectionType.EXAMPLE]
        prompt_parts.extend(s.content for s in example_sections)
        
        # 自定义段落
        custom_sections = [s for s in processed_sections if s.section_type == PromptSectionType.CUSTOM]
        prompt_parts.extend(s.content for s in custom_sections)
        
        # 当前输入
        if self.context.current_input:
            prompt_parts.append(self.context.current_input)
        
        # 组合提示
        prompt = "\n\n".join(filter(None, prompt_parts))
        
        # 应用截断策略
        if self.token_limit and self.truncation_strategy != TruncationStrategy.NONE:
            prompt = self._apply_truncation(prompt)
        
        return prompt
    
    def _format_chat_history(self) -> str:
        """格式化聊天历史
        
        Returns:
            str: 格式化的聊天历史
        """
        if not self.context.chat_history:
            return ""
        
        formatted_messages = []
        for message in self.context.chat_history:
            role = message.get("role", "")
            content = message.get("content", "")
            if role and content:
                formatted_messages.append(f"{role}: {content}")
        
        return "\n".join(formatted_messages)
    
    def _apply_truncation(self, prompt: str) -> str:
        """应用截断策略
        
        Args:
            prompt: 原始提示
            
        Returns:
            str: 截断后的提示
        """
        if not self.token_limit:
            return prompt
        
        # 这里使用简单的字符数估算，实际应该使用token计算器
        current_length = len(prompt)
        max_length = self.token_limit.available_tokens * 4  # 粗略估算1 token = 4 字符
        
        if current_length <= max_length:
            return prompt
        
        if self.truncation_strategy == TruncationStrategy.PREFIX:
            # 从前部截断
            return prompt[-max_length:]
        elif self.truncation_strategy == TruncationStrategy.SUFFIX:
            # 从后部截断
            return prompt[:max_length]
        elif self.truncation_strategy == TruncationStrategy.MIDDLE:
            # 从中间截断
            half_length = max_length // 2
            return prompt[:half_length] + prompt[-half_length:]
        elif self.truncation_strategy == TruncationStrategy.SMART:
            # 智能截断：优先保留系统指令和角色描述
            return self._smart_truncate(prompt, max_length)
        
        return prompt
    
    def _smart_truncate(self, prompt: str, max_length: int) -> str:
        """智能截断
        
        Args:
            prompt: 原始提示
            max_length: 最大长度
            
        Returns:
            str: 截断后的提示
        """
        # 简化实现：按段落重要性截断
        sections = prompt.split("\n\n")
        important_sections = []
        less_important_sections = []
        
        for section in sections:
            section_lower = section.lower()
            if (any(keyword in section_lower for keyword in ["system", "指令", "规则"]) or
                len(section) < 200):  # 短段落可能是重要信息
                important_sections.append(section)
            else:
                less_important_sections.append(section)
        
        # 优先保留重要段落
        result = "\n\n".join(important_sections)
        
        # 如果还有空间，添加部分次要段落
        if len(result) < max_length:
            remaining_length = max_length - len(result)
            for section in less_important_sections:
                if len(result) + len(section) + 2 <= max_length:  # +2 for "\n\n"
                    result += "\n\n" + section
                else:
                    break
        
        return result
    
    def get_token_estimate(self) -> int:
        """获取token估算
        
        Returns:
            int: 估算的token数量
        """
        prompt = self.build_prompt()
        # 简单估算：1 token ≈ 4 字符
        return len(prompt) // 4
    
    def validate_variables(self) -> List[str]:
        """验证变量
        
        Returns:
            List[str]: 缺失的变量列表
        """
        missing_variables = []
        
        for variable in self.template.variables:
            if variable not in self.context.variables:
                missing_variables.append(variable)
        
        return missing_variables


@dataclass
class TokenCalculator:
    """Token计算器
    
    负责计算文本的token数量，支持多种tokenizer。
    遵循单一职责原则，专门负责token计算。
    """
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-3.5-turbo"
    
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        # 简化实现：基于字符数的估算
        # 实际实现应该使用对应的tokenizer库
        if self.provider == LLMProvider.OPENAI:
            return self._count_openai_tokens(text)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._count_anthropic_tokens(text)
        elif self.provider == LLMProvider.OPENROUTER:
            return self._count_openrouter_tokens(text)
        elif self.provider == LLMProvider.KOBOLDAI:
            return self._count_koboldai_tokens(text)
        else:
            # 默认估算
            return len(text) // 4
    
    def _count_openai_tokens(self, text: str) -> int:
        """计算OpenAI模型的token数量
        
        Args:
            text: 文本
            
        Returns:
            int: token数量
        """
        # 简化实现，实际应该使用tiktoken库
        return len(text) // 4
    
    def _count_anthropic_tokens(self, text: str) -> int:
        """计算Anthropic模型的token数量
        
        Args:
            text: 文本
            
        Returns:
            int: token数量
        """
        # 简化实现，实际应该使用anthropic库
        return len(text) // 4
    
    def _count_openrouter_tokens(self, text: str) -> int:
        """计算OpenRouter模型的token数量
        
        Args:
            text: 文本
            
        Returns:
            int: token数量
        """
        # 简化实现，根据模型类型选择计算方法
        return len(text) // 4
    
    def _count_koboldai_tokens(self, text: str) -> int:
        """计算KoboldAI模型的token数量
        
        Args:
            text: 文本
            
        Returns:
            int: token数量
        """
        # 简化实现
        return len(text) // 3  # KoboldAI通常使用不同的tokenizer
    
    def count_tokens_by_sections(self, sections: List[PromptSection]) -> Dict[str, int]:
        """按段落计算token数量
        
        Args:
            sections: 段落列表
            
        Returns:
            Dict[str, int]: 段落类型到token数量的映射
        """
        result = {}
        
        for section in sections:
            section_type = section.section_type.value
            token_count = self.count_tokens(section.content)
            result[section_type] = result.get(section_type, 0) + token_count
        
        return result
    
    def get_token_limit_for_model(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        # 简化实现，返回一些常见模型的限制
        model_limits = {
            "gpt-3.5-turbo": (4096, 512),
            "gpt-4": (8192, 1024),
            "gpt-4-32k": (32768, 4096),
            "claude-3-sonnet": (200000, 4096),
            "claude-3-opus": (200000, 4096),
        }
        
        max_tokens, reserved = model_limits.get(model_name, (4096, 512))
        
        return TokenLimit(
            provider=self.provider,
            model_name=model_name,
            max_tokens=max_tokens,
            reserved_tokens=reserved
        )