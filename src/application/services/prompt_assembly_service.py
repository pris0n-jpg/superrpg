"""
提示组装服务

提供分层组装提示、上下文管理和Token计算功能。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime

from ...domain.models.prompt import (
    PromptTemplate, PromptContext, PromptBuilder, PromptSection,
    PromptSectionType, TruncationStrategy, LLMProvider, TokenLimit
)
from ...domain.dtos.prompt_dtos import (
    PromptBuildDto, PromptPreviewDto, PromptContextDto,
    PromptSectionDto, PromptStatisticsDto
)
from ...domain.repositories.prompt_repository import PromptRepository
from ...core.interfaces import EventBus, Logger
from ...core.exceptions import ValidationException, NotFoundException, BusinessRuleException
from .token_counter_service import TokenCounterService
from .base import ApplicationService


class PromptAssemblyService(ApplicationService):
    """提示组装服务
    
    提供提示的分层组装、上下文管理和Token计算功能。
    遵循单一职责原则，专门负责提示组装的业务逻辑。
    """
    
    def __init__(
        self,
        prompt_repository: PromptRepository,
        token_counter: TokenCounterService,
        event_bus: EventBus,
        logger: Logger
    ):
        """初始化提示组装服务
        
        Args:
            prompt_repository: 提示仓储
            token_counter: Token计数服务
            logger: 日志记录器
        """
        super().__init__(event_bus, logger)
        self._prompt_repository = prompt_repository
        self._token_counter = token_counter
    
    # 提示构建方法
    
    def build_prompt(self, request: PromptBuildDto) -> PromptPreviewDto:
        """构建提示
        
        Args:
            request: 提示构建请求对象
            
        Returns:
            PromptPreviewDto: 提示预览响应对象
            
        Raises:
            ValidationException: 验证失败时抛出
            NotFoundException: 模板不存在时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        start_time = time.time()
        
        # 验证请求数据
        errors = request.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 获取模板
        template = self._prompt_repository.find_by_id(request.template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {request.template_id}")
        
        if not template.is_active:
            raise BusinessRuleException(f"模板已停用: {template.name}")
        
        # 转换上下文
        context = self._dto_to_context(request.context)
        
        # 设置token限制
        token_limit = None
        if request.token_limit:
            provider = LLMProvider(request.token_limit['provider'])
            model_name = request.token_limit['model_name']
            max_tokens = request.token_limit['max_tokens']
            reserved_tokens = request.token_limit.get('reserved_tokens', 0)
            
            token_limit = TokenLimit(
                provider=provider,
                model_name=model_name,
                max_tokens=max_tokens,
                reserved_tokens=reserved_tokens
            )
        
        # 创建提示构建器
        builder = PromptBuilder(
            template=template,
            context=context,
            token_limit=token_limit,
            truncation_strategy=request.truncation_strategy
        )
        
        # 验证变量
        missing_variables = builder.validate_variables()
        if missing_variables:
            self._logger.warning(f"Missing variables for template {template.name}: {missing_variables}")
        
        # 构建提示
        prompt = builder.build_prompt()
        
        # 计算token数量
        token_count = self._token_counter.count_tokens_by_sections(
            [{'content': section.content, 'section_type': section.section_type.value} 
             for section in template.sections]
        )
        total_tokens = sum(token_count.values())
        
        # 检查是否应用了截断
        truncation_applied = False
        if token_limit:
            is_over_limit, current_tokens, max_tokens = self._token_counter.validate_token_limit(
                prompt, token_limit.provider, token_limit.model_name, token_limit.reserved_tokens
            )
            truncation_applied = is_over_limit
        
        # 转换段落为DTO
        section_dtos = [PromptSectionDto.from_domain(section) for section in template.sections]
        
        # 计算耗时
        build_time_ms = int((time.time() - start_time) * 1000)
        
        self._logger.info(f"Built prompt for template {template.name} ({total_tokens} tokens)")
        
        return PromptPreviewDto(
            prompt=prompt,
            token_count=total_tokens,
            sections=section_dtos,
            variables_used=context.variables,
            missing_variables=missing_variables,
            truncation_applied=truncation_applied,
            build_time_ms=build_time_ms
        )
    
    def preview_prompt(self, template_id: str, context: PromptContextDto, 
                      provider: LLMProvider = LLMProvider.OPENAI, 
                      model_name: str = "gpt-3.5-turbo") -> PromptPreviewDto:
        """预览提示
        
        Args:
            template_id: 模板ID
            context: 提示上下文DTO
            provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            PromptPreviewDto: 提示预览响应对象
            
        Raises:
            NotFoundException: 模板不存在时抛出
            ValidationException: 验证失败时抛出
        """
        # 获取模板
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 转换上下文
        context_domain = self._dto_to_context(context)
        
        # 获取token限制
        token_limit = self._token_counter.get_token_limit(provider, model_name)
        
        # 创建提示构建器
        builder = PromptBuilder(
            template=template,
            context=context_domain,
            token_limit=token_limit,
            truncation_strategy=TruncationStrategy.SMART
        )
        
        # 构建提示
        prompt = builder.build_prompt()
        
        # 计算token数量
        token_count = self._token_counter.count_tokens_by_sections(
            [{'content': section.content, 'section_type': section.section_type.value} 
             for section in template.sections]
        )
        total_tokens = sum(token_count.values())
        
        # 验证变量
        missing_variables = builder.validate_variables()
        
        # 检查是否应用了截断
        is_over_limit, _, _ = self._token_counter.validate_token_limit(
            prompt, provider, model_name, token_limit.reserved_tokens
        )
        
        # 转换段落为DTO
        section_dtos = [PromptSectionDto.from_domain(section) for section in template.sections]
        
        return PromptPreviewDto(
            prompt=prompt,
            token_count=total_tokens,
            sections=section_dtos,
            variables_used=context_domain.variables,
            missing_variables=missing_variables,
            truncation_applied=is_over_limit,
            build_time_ms=0
        )
    
    # 上下文管理方法
    
    def create_context(self, character_name: str = "", character_description: str = "",
                      world_info: str = "", chat_history: List[Dict[str, str]] = None,
                      current_input: str = "", variables: Dict[str, str] = None,
                      metadata: Dict[str, Any] = None) -> PromptContextDto:
        """创建提示上下文
        
        Args:
            character_name: 角色名称
            character_description: 角色描述
            world_info: 世界信息
            chat_history: 聊天历史
            current_input: 当前输入
            variables: 变量字典
            metadata: 元数据
            
        Returns:
            PromptContextDto: 提示上下文DTO
        """
        context = PromptContext(
            character_name=character_name,
            character_description=character_description,
            world_info=world_info,
            chat_history=chat_history or [],
            current_input=current_input,
            variables=variables or {},
            metadata=metadata or {}
        )
        
        return PromptContextDto.from_domain(context)
    
    def update_context(self, context: PromptContextDto, updates: Dict[str, Any]) -> PromptContextDto:
        """更新提示上下文
        
        Args:
            context: 原始上下文DTO
            updates: 更新内容
            
        Returns:
            PromptContextDto: 更新后的上下文DTO
        """
        # 转换为领域对象
        context_domain = self._dto_to_context(context)
        
        # 应用更新
        if 'character_name' in updates:
            context_domain = PromptContext(
                character_name=updates['character_name'],
                character_description=context_domain.character_description,
                world_info=context_domain.world_info,
                chat_history=context_domain.chat_history,
                current_input=context_domain.current_input,
                variables=context_domain.variables,
                metadata=context_domain.metadata
            )
        
        if 'character_description' in updates:
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=updates['character_description'],
                world_info=context_domain.world_info,
                chat_history=context_domain.chat_history,
                current_input=context_domain.current_input,
                variables=context_domain.variables,
                metadata=context_domain.metadata
            )
        
        if 'world_info' in updates:
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=context_domain.character_description,
                world_info=updates['world_info'],
                chat_history=context_domain.chat_history,
                current_input=context_domain.current_input,
                variables=context_domain.variables,
                metadata=context_domain.metadata
            )
        
        if 'chat_history' in updates:
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=context_domain.character_description,
                world_info=context_domain.world_info,
                chat_history=updates['chat_history'],
                current_input=context_domain.current_input,
                variables=context_domain.variables,
                metadata=context_domain.metadata
            )
        
        if 'current_input' in updates:
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=context_domain.character_description,
                world_info=context_domain.world_info,
                chat_history=context_domain.chat_history,
                current_input=updates['current_input'],
                variables=context_domain.variables,
                metadata=context_domain.metadata
            )
        
        if 'variables' in updates:
            new_variables = context_domain.variables.copy()
            new_variables.update(updates['variables'])
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=context_domain.character_description,
                world_info=context_domain.world_info,
                chat_history=context_domain.chat_history,
                current_input=context_domain.current_input,
                variables=new_variables,
                metadata=context_domain.metadata
            )
        
        if 'metadata' in updates:
            new_metadata = context_domain.metadata.copy()
            new_metadata.update(updates['metadata'])
            context_domain = PromptContext(
                character_name=context_domain.character_name,
                character_description=context_domain.character_description,
                world_info=context_domain.world_info,
                chat_history=context_domain.chat_history,
                current_input=context_domain.current_input,
                variables=context_domain.variables,
                metadata=new_metadata
            )
        
        return PromptContextDto.from_domain(context_domain)
    
    def add_chat_message(self, context: PromptContextDto, role: str, content: str) -> PromptContextDto:
        """添加聊天消息到上下文
        
        Args:
            context: 上下文DTO
            role: 消息角色
            content: 消息内容
            
        Returns:
            PromptContextDto: 更新后的上下文DTO
        """
        context_domain = self._dto_to_context(context)
        
        # 添加新消息
        new_chat_history = context_domain.chat_history.copy()
        new_chat_history.append({'role': role, 'content': content})
        
        # 限制历史消息数量（保留最近20条）
        if len(new_chat_history) > 20:
            new_chat_history = new_chat_history[-20:]
        
        updated_context = PromptContext(
            character_name=context_domain.character_name,
            character_description=context_domain.character_description,
            world_info=context_domain.world_info,
            chat_history=new_chat_history,
            current_input=context_domain.current_input,
            variables=context_domain.variables,
            metadata=context_domain.metadata
        )
        
        return PromptContextDto.from_domain(updated_context)
    
    def clear_chat_history(self, context: PromptContextDto) -> PromptContextDto:
        """清除聊天历史
        
        Args:
            context: 上下文DTO
            
        Returns:
            PromptContextDto: 更新后的上下文DTO
        """
        context_domain = self._dto_to_context(context)
        
        updated_context = PromptContext(
            character_name=context_domain.character_name,
            character_description=context_domain.character_description,
            world_info=context_domain.world_info,
            chat_history=[],
            current_input=context_domain.current_input,
            variables=context_domain.variables,
            metadata=context_domain.metadata
        )
        
        return PromptContextDto.from_domain(updated_context)
    
    # Token计算和验证方法
    
    def calculate_tokens(self, template_id: str, context: PromptContextDto) -> Dict[str, Any]:
        """计算提示的token数量
        
        Args:
            template_id: 模板ID
            context: 上下文DTO
            
        Returns:
            Dict[str, Any]: Token计算结果
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        # 获取模板
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 转换上下文
        context_domain = self._dto_to_context(context)
        
        # 创建提示构建器
        builder = PromptBuilder(
            template=template,
            context=context_domain,
            token_limit=None,
            truncation_strategy=TruncationStrategy.NONE
        )
        
        # 构建提示
        prompt = builder.build_prompt()
        
        # 计算token数量
        token_count = self._token_counter.count_tokens_by_sections(
            [{'content': section.content, 'section_type': section.section_type.value} 
             for section in template.sections]
        )
        
        total_tokens = sum(token_count.values())
        
        return {
            'total_tokens': total_tokens,
            'tokens_by_section': token_count,
            'character_count': len(prompt),
            'estimated_sections': len(template.sections)
        }
    
    def validate_token_limit(self, template_id: str, context: PromptContextDto,
                           provider: LLMProvider, model_name: str) -> Dict[str, Any]:
        """验证提示是否超过token限制
        
        Args:
            template_id: 模板ID
            context: 上下文DTO
            provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 验证结果
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        # 获取模板
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 转换上下文
        context_domain = self._dto_to_context(context)
        
        # 创建提示构建器
        builder = PromptBuilder(
            template=template,
            context=context_domain,
            token_limit=None,
            truncation_strategy=TruncationStrategy.NONE
        )
        
        # 构建提示
        prompt = builder.build_prompt()
        
        # 验证token限制
        is_over_limit, current_tokens, max_tokens = self._token_counter.validate_token_limit(
            prompt, provider, model_name
        )
        
        # 获取模型限制
        token_limit = self._token_counter.get_token_limit(provider, model_name)
        
        return {
            'is_over_limit': is_over_limit,
            'current_tokens': current_tokens,
            'max_tokens': max_tokens,
            'available_tokens': token_limit.available_tokens,
            'usage_percentage': (current_tokens / max_tokens * 100) if max_tokens > 0 else 0,
            'provider': provider.value,
            'model_name': model_name
        }
    
    # 调试工具方法
    
    def debug_prompt(self, template_id: str, context: PromptContextDto) -> Dict[str, Any]:
        """调试提示构建过程
        
        Args:
            template_id: 模板ID
            context: 上下文DTO
            
        Returns:
            Dict[str, Any]: 调试信息
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        # 获取模板
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 转换上下文
        context_domain = self._dto_to_context(context)
        
        # 创建提示构建器
        builder = PromptBuilder(
            template=template,
            context=context_domain,
            token_limit=None,
            truncation_strategy=TruncationStrategy.NONE
        )
        
        # 验证变量
        missing_variables = builder.validate_variables()
        
        # 构建提示
        prompt = builder.build_prompt()
        
        # 分析段落
        sections_analysis = []
        for section in template.sections:
            # 应用变量替换
            processed_section = section.with_variables(context_domain.variables)
            
            sections_analysis.append({
                'original_content': section.content,
                'processed_content': processed_section.content,
                'section_type': section.section_type.value,
                'priority': section.priority,
                'token_count': self._token_counter.count_tokens_by_sections(
                    [{'content': processed_section.content, 'section_type': section.section_type.value}]
                ).get(section.section_type.value, 0),
                'has_variables': len(set(self._extract_variables(section.content))) > 0,
                'variables_used': self._find_used_variables(section.content, context_domain.variables)
            })
        
        return {
            'template_name': template.name,
            'template_id': template_id,
            'final_prompt': prompt,
            'total_tokens': self._token_counter.count_tokens_by_sections(
                [{'content': section.content, 'section_type': section.section_type.value} 
                 for section in template.sections]
            ),
            'sections_analysis': sections_analysis,
            'context_variables': context_domain.variables,
            'missing_variables': missing_variables,
            'template_variables': list(template.variables),
            'unused_variables': list(set(context_domain.variables.keys()) - template.variables)
        }
    
    # 辅助方法
    
    def _dto_to_context(self, context_dto: PromptContextDto) -> PromptContext:
        """将DTO转换为领域对象
        
        Args:
            context_dto: 上下文DTO
            
        Returns:
            PromptContext: 上下文领域对象
        """
        return PromptContext(
            character_name=context_dto.character_name,
            character_description=context_dto.character_description,
            world_info=context_dto.world_info,
            chat_history=context_dto.chat_history,
            current_input=context_dto.current_input,
            variables=context_dto.variables,
            metadata=context_dto.metadata
        )
    
    def _extract_variables(self, text: str) -> List[str]:
        """从文本中提取变量
        
        Args:
            text: 文本内容
            
        Returns:
            List[str]: 变量列表
        """
        import re
        pattern = r'\{([^}]+)\}'
        return re.findall(pattern, text)
    
    def _find_used_variables(self, text: str, variables: Dict[str, str]) -> Dict[str, str]:
        """查找文本中使用的变量
        
        Args:
            text: 文本内容
            variables: 变量字典
            
        Returns:
            Dict[str, str]: 使用的变量及其值
        """
        text_variables = self._extract_variables(text)
        used_variables = {}
        
        for var in text_variables:
            if var in variables:
                used_variables[var] = variables[var]
        
        return used_variables
    
    def get_optimization_suggestions(self, template_id: str, context: PromptContextDto,
                                    provider: LLMProvider, model_name: str) -> List[Dict[str, Any]]:
        """获取优化建议
        
        Args:
            template_id: 模板ID
            context: 上下文DTO
            provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            List[Dict[str, Any]]: 优化建议列表
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        suggestions = []
        
        # 获取验证结果
        validation_result = self.validate_token_limit(template_id, context, provider, model_name)
        
        if validation_result['is_over_limit']:
            suggestions.append({
                'type': 'truncation',
                'priority': 'high',
                'title': '提示超过Token限制',
                'description': f"当前提示使用了 {validation_result['current_tokens']} tokens，超过了模型的 {validation_result['max_tokens']} tokens 限制。",
                'suggestion': '考虑使用截断策略或减少内容'
            })
        elif validation_result['usage_percentage'] > 80:
            suggestions.append({
                'type': 'warning',
                'priority': 'medium',
                'title': '提示接近Token限制',
                'description': f"当前提示使用了 {validation_result['usage_percentage']:.1f}% 的可用tokens。",
                'suggestion': '考虑优化内容以留出更多空间'
            })
        
        # 获取调试信息
        debug_info = self.debug_prompt(template_id, context)
        
        # 检查缺失变量
        if debug_info['missing_variables']:
            suggestions.append({
                'type': 'variables',
                'priority': 'medium',
                'title': '存在缺失变量',
                'description': f"模板中定义了但上下文中未提供的变量: {', '.join(debug_info['missing_variables'])}",
                'suggestion': '在上下文中提供这些变量的值'
            })
        
        # 检查未使用变量
        if debug_info['unused_variables']:
            suggestions.append({
                'type': 'variables',
                'priority': 'low',
                'title': '存在未使用变量',
                'description': f"上下文中提供了但模板中未使用的变量: {', '.join(debug_info['unused_variables'])}",
                'suggestion': '考虑移除未使用的变量或在模板中使用它们'
            })
        
        # 检查段落优化
        large_sections = [s for s in debug_info['sections_analysis'] if s['token_count'] > 500]
        if large_sections:
            suggestions.append({
                'type': 'content',
                'priority': 'medium',
                'title': '存在较大段落',
                'description': f"以下段落较大，可能需要优化: {', '.join([s['section_type'] for s in large_sections])}",
                'suggestion': '考虑将大段落拆分为更小的部分或精简内容'
            })
        
        return suggestions
    def _execute_command_internal(self, command: Any) -> Any:
        raise NotImplementedError("PromptAssemblyService command execution is not implemented")

    def _execute_query_internal(self, query: Any) -> Any:
        raise NotImplementedError("PromptAssemblyService query execution is not implemented")
