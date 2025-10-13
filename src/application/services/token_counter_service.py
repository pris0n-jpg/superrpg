"""
Token计数服务

提供多种tokenizer的Token计数功能，支持不同LLM提供商的精确计算。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod

from ...domain.models.prompt import LLMProvider, TokenLimit
from ...domain.dtos.prompt_dtos import (
    PromptTokenCountDto, PromptTokenCountResponseDto
)
from ...core.interfaces import EventBus, Logger
from ...core.exceptions import ValidationException, ExternalServiceException
from .base import ApplicationService


class Tokenizer(ABC):
    """Tokenizer抽象基类
    
    定义Token计算的接口，遵循依赖倒置原则。
    """
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        pass
    
    @abstractmethod
    def get_model_limit(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        pass


class OpenAITokenizer(Tokenizer):
    """OpenAI Tokenizer实现
    
    提供OpenAI模型的Token计算功能。
    遵循单一职责原则，专门负责OpenAI的Token计算。
    """
    
    def __init__(self, logger: Logger, event_bus: EventBus | None = None):
        """初始化OpenAI Tokenizer
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
        self._encoder = None
        self._try_load_tiktoken()
    
    def _try_load_tiktoken(self) -> None:
        """尝试加载tiktoken库"""
        try:
            import tiktoken
            # 使用默认的编码器
            self._encoder = tiktoken.get_encoding("cl100k_base")
            self._logger.info("Successfully loaded tiktoken for OpenAI token counting")
        except ImportError:
            self._logger.warning("tiktoken not available, using fallback token counting")
        except Exception as e:
            self._logger.error(f"Failed to load tiktoken: {e}")
    
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        if self._encoder:
            try:
                return len(self._encoder.encode(text))
            except Exception as e:
                self._logger.error(f"Error using tiktoken: {e}")
        
        # 回退到简单的估算
        return self._fallback_count(text)
    
    def _fallback_count(self, text: str) -> int:
        """回退的token计算方法
        
        Args:
            text: 文本
            
        Returns:
            int: 估算的token数量
        """
        # 简单的启发式规则
        # 英文：约4字符 = 1 token
        # 中文：约1.5字符 = 1 token
        # 代码：约3-4字符 = 1 token
        
        if not text:
            return 0
        
        # 计算中文字符数
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        
        # 计算英文字符数
        english_chars = len([c for c in text if c.isascii() and not c.isspace()])
        
        # 计算代码字符数（简单启发式）
        code_chars = len([c for c in text if c in '{}[]();<>'])
        
        # 估算token数
        chinese_tokens = chinese_chars / 1.5
        english_tokens = english_chars / 4.0
        code_tokens = code_chars / 3.0
        
        return int(chinese_tokens + english_tokens + code_tokens)
    
    def get_model_limit(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        model_limits = {
            "gpt-3.5-turbo": (4096, 512),
            "gpt-3.5-turbo-16k": (16384, 2048),
            "gpt-4": (8192, 1024),
            "gpt-4-32k": (32768, 4096),
            "gpt-4-turbo": (128000, 4096),
            "gpt-4o": (128000, 4096),
            "gpt-4o-mini": (128000, 4096),
            "text-davinci-003": (4097, 512),
            "text-curie-001": (2049, 256),
            "text-babbage-001": (2049, 256),
            "text-ada-001": (2049, 256),
        }
        
        max_tokens, reserved = model_limits.get(model_name, (4096, 512))
        
        return TokenLimit(
            provider=LLMProvider.OPENAI,
            model_name=model_name,
            max_tokens=max_tokens,
            reserved_tokens=reserved
        )


class AnthropicTokenizer(Tokenizer):
    """Anthropic Tokenizer实现
    
    提供Anthropic模型的Token计算功能。
    遵循单一职责原则，专门负责Anthropic的Token计算。
    """
    
    def __init__(self, logger: Logger, event_bus: EventBus | None = None):
        """初始化Anthropic Tokenizer
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
    
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        # Anthropic Claude的token计算
        # 简化实现，实际应该使用anthropic库
        return len(text) // 4
    
    def get_model_limit(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        model_limits = {
            "claude-3-opus-20240229": (200000, 4096),
            "claude-3-sonnet-20240229": (200000, 4096),
            "claude-3-haiku-20240307": (200000, 4096),
            "claude-2.1": (200000, 4096),
            "claude-2.0": (100000, 2048),
            "claude-instant-1.2": (100000, 2048),
        }
        
        max_tokens, reserved = model_limits.get(model_name, (200000, 4096))
        
        return TokenLimit(
            provider=LLMProvider.ANTHROPIC,
            model_name=model_name,
            max_tokens=max_tokens,
            reserved_tokens=reserved
        )


class OpenRouterTokenizer(Tokenizer):
    """OpenRouter Tokenizer实现
    
    提供OpenRouter模型的Token计算功能。
    遵循单一职责原则，专门负责OpenRouter的Token计算。
    """
    
    def __init__(self, logger: Logger, event_bus: EventBus | None = None):
        """初始化OpenRouter Tokenizer
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
        self._openai_tokenizer = OpenAITokenizer(logger)
        self._anthropic_tokenizer = AnthropicTokenizer(logger)
    
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        # OpenRouter支持多种模型，这里使用OpenAI的tokenizer作为默认
        return self._openai_tokenizer.count_tokens(text)
    
    def get_model_limit(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        # 根据模型名称判断使用哪个tokenizer的限制
        if "claude" in model_name.lower():
            return self._anthropic_tokenizer.get_model_limit(model_name)
        else:
            return self._openai_tokenizer.get_model_limit(model_name)


class KoboldAITokenizer(Tokenizer):
    """KoboldAI Tokenizer实现
    
    提供KoboldAI模型的Token计算功能。
    遵循单一职责原则，专门负责KoboldAI的Token计算。
    """
    
    def __init__(self, logger: Logger, event_bus: EventBus | None = None):
        """初始化KoboldAI Tokenizer
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
    
    def count_tokens(self, text: str) -> int:
        """计算token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            int: token数量
        """
        if not text:
            return 0
        
        # KoboldAI通常使用不同的tokenizer，这里使用简单的估算
        return len(text) // 3
    
    def get_model_limit(self, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
        """
        model_limits = {
            "default": (2048, 256),
            "fairseq-13b": (2048, 256),
            "gpt-neox-20b": (2048, 256),
            "opt-13b": (2048, 256),
            "opt-30b": (2048, 256),
        }
        
        max_tokens, reserved = model_limits.get(model_name, (2048, 256))
        
        return TokenLimit(
            provider=LLMProvider.KOBOLDAI,
            model_name=model_name,
            max_tokens=max_tokens,
            reserved_tokens=reserved
        )


class TokenCounterService(ApplicationService):
    """Token计数服务
    
    提供统一的Token计数接口，支持多种LLM提供商。
    遵循单一职责原则，专门负责Token计数的业务逻辑。
    """
    
    def __init__(self, logger: Logger, event_bus: EventBus | None = None):
        """初始化Token计数服务
        
        Args:
            logger: 日志记录器
        """
        super().__init__(event_bus, logger)
        self._tokenizers = {
            LLMProvider.OPENAI: OpenAITokenizer(logger),
            LLMProvider.ANTHROPIC: AnthropicTokenizer(logger),
            LLMProvider.OPENROUTER: OpenRouterTokenizer(logger),
            LLMProvider.KOBOLDAI: KoboldAITokenizer(logger),
        }
    
    def count_tokens(self, request: PromptTokenCountDto) -> PromptTokenCountResponseDto:
        """计算token数量
        
        Args:
            request: Token计数请求对象
            
        Returns:
            PromptTokenCountResponseDto: Token计数响应对象
            
        Raises:
            ValidationException: 验证失败时抛出
            ExternalServiceException: 外部服务错误时抛出
        """
        start_time = time.time()
        
        # 验证请求
        errors = request.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        try:
            # 获取对应的tokenizer
            tokenizer = self._tokenizers.get(request.provider)
            if not tokenizer:
                raise ValidationException(f"不支持的提供商: {request.provider.value}")
            
            # 计算token数量
            token_count = tokenizer.count_tokens(request.text)
            character_count = len(request.text)
            
            # 计算耗时
            calculation_time_ms = int((time.time() - start_time) * 1000)
            
            self._logger.info(f"Counted {token_count} tokens for {request.provider.value}/{request.model_name}")
            
            return PromptTokenCountResponseDto(
                token_count=token_count,
                character_count=character_count,
                provider=request.provider,
                model_name=request.model_name,
                calculation_time_ms=calculation_time_ms
            )
            
        except Exception as e:
            self._logger.error(f"Error counting tokens: {e}")
            raise ExternalServiceException("Token计数失败", "TokenCounter", cause=e)
    
    def get_token_limit(self, provider: LLMProvider, model_name: str) -> TokenLimit:
        """获取模型的token限制
        
        Args:
            provider: LLM提供商
            model_name: 模型名称
            
        Returns:
            TokenLimit: Token限制对象
            
        Raises:
            ValidationException: 验证失败时抛出
            ExternalServiceException: 外部服务错误时抛出
        """
        try:
            tokenizer = self._tokenizers.get(provider)
            if not tokenizer:
                raise ValidationException(f"不支持的提供商: {provider.value}")
            
            return tokenizer.get_model_limit(model_name)
            
        except Exception as e:
            self._logger.error(f"Error getting token limit: {e}")
            raise ExternalServiceException("获取token限制失败", "TokenCounter", cause=e)
    
    def count_tokens_by_sections(self, sections: List[Dict[str, Any]], 
                                provider: LLMProvider = LLMProvider.OPENAI) -> Dict[str, int]:
        """按段落计算token数量
        
        Args:
            sections: 段落列表
            provider: LLM提供商
            
        Returns:
            Dict[str, int]: 段落类型到token数量的映射
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        tokenizer = self._tokenizers.get(provider)
        if not tokenizer:
            raise ValidationException(f"不支持的提供商: {provider.value}")
        
        result = {}
        
        for section in sections:
            content = section.get('content', '')
            section_type = section.get('section_type', 'custom')
            
            token_count = tokenizer.count_tokens(content)
            result[section_type] = result.get(section_type, 0) + token_count
        
        return result
    
    def estimate_tokens_for_template(self, template_content: str, 
                                    variables: Dict[str, str] = None,
                                    provider: LLMProvider = LLMProvider.OPENAI) -> int:
        """估算模板的token数量
        
        Args:
            template_content: 模板内容
            variables: 变量字典
            provider: LLM提供商
            
        Returns:
            int: 估算的token数量
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        tokenizer = self._tokenizers.get(provider)
        if not tokenizer:
            raise ValidationException(f"不支持的提供商: {provider.value}")
        
        # 替换变量
        processed_content = template_content
        if variables:
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                processed_content = processed_content.replace(placeholder, str(value))
        
        return tokenizer.count_tokens(processed_content)
    
    def validate_token_limit(self, text: str, provider: LLMProvider, 
                           model_name: str, reserved_tokens: int = 0) -> Tuple[bool, int, int]:
        """验证文本是否超过token限制
        
        Args:
            text: 文本内容
            provider: LLM提供商
            model_name: 模型名称
            reserved_tokens: 预留token数量
            
        Returns:
            Tuple[bool, int, int]: (是否超过限制, 当前token数, 最大token数)
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        tokenizer = self._tokenizers.get(provider)
        if not tokenizer:
            raise ValidationException(f"不支持的提供商: {provider.value}")
        
        token_limit = tokenizer.get_model_limit(model_name)
        current_tokens = tokenizer.count_tokens(text)
        max_tokens = token_limit.max_tokens - max(reserved_tokens, token_limit.reserved_tokens)
        
        is_over_limit = current_tokens > max_tokens
        
        return is_over_limit, current_tokens, max_tokens
    
    def get_supported_providers(self) -> List[Dict[str, Any]]:
        """获取支持的提供商列表
        
        Returns:
            List[Dict[str, Any]]: 支持的提供商列表
        """
        return [
            {
                'provider': provider.value,
                'name': provider.value.title(),
                'supported': True
            }
            for provider in LLMProvider
        ]
    
    def get_supported_models(self, provider: LLMProvider) -> List[Dict[str, Any]]:
        """获取指定提供商支持的模型列表
        
        Args:
            provider: LLM提供商
            
        Returns:
            List[Dict[str, Any]]: 支持的模型列表
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        tokenizer = self._tokenizers.get(provider)
        if not tokenizer:
            raise ValidationException(f"不支持的提供商: {provider.value}")
        
        # 这里应该从tokenizer获取支持的模型列表
        # 简化实现，返回一些常见模型
        if provider == LLMProvider.OPENAI:
            return [
                {'model_name': 'gpt-3.5-turbo', 'max_tokens': 4096},
                {'model_name': 'gpt-3.5-turbo-16k', 'max_tokens': 16384},
                {'model_name': 'gpt-4', 'max_tokens': 8192},
                {'model_name': 'gpt-4-32k', 'max_tokens': 32768},
                {'model_name': 'gpt-4-turbo', 'max_tokens': 128000},
                {'model_name': 'gpt-4o', 'max_tokens': 128000},
                {'model_name': 'gpt-4o-mini', 'max_tokens': 128000},
            ]
        elif provider == LLMProvider.ANTHROPIC:
            return [
                {'model_name': 'claude-3-opus-20240229', 'max_tokens': 200000},
                {'model_name': 'claude-3-sonnet-20240229', 'max_tokens': 200000},
                {'model_name': 'claude-3-haiku-20240307', 'max_tokens': 200000},
                {'model_name': 'claude-2.1', 'max_tokens': 200000},
                {'model_name': 'claude-2.0', 'max_tokens': 100000},
            ]
        elif provider == LLMProvider.OPENROUTER:
            return [
                {'model_name': 'openai/gpt-3.5-turbo', 'max_tokens': 4096},
                {'model_name': 'openai/gpt-4', 'max_tokens': 8192},
                {'model_name': 'anthropic/claude-3-opus', 'max_tokens': 200000},
                {'model_name': 'anthropic/claude-3-sonnet', 'max_tokens': 200000},
            ]
        elif provider == LLMProvider.KOBOLDAI:
            return [
                {'model_name': 'default', 'max_tokens': 2048},
                {'model_name': 'fairseq-13b', 'max_tokens': 2048},
                {'model_name': 'gpt-neox-20b', 'max_tokens': 2048},
            ]
        
        return []
    def _execute_command_internal(self, command: Any) -> Any:
        raise NotImplementedError("TokenCounterService command execution is not implemented")

    def _execute_query_internal(self, query: Any) -> Any:
        raise NotImplementedError("TokenCounterService query execution is not implemented")
