"""
错误处理中间件模块

该模块实现错误处理中间件，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责错误的统一处理和响应。
"""

import traceback
import logging
from typing import Dict, Any, Optional, List, Callable, Type, Union
from .middleware_base import MiddlewareBase, MiddlewareContext, MiddlewareResult, ResponseContext

# 导入自定义异常
try:
    from ...core.exceptions import (
        BaseException as CustomBaseException,
        DomainException,
        InfrastructureException,
        ApplicationException,
        ValidationException,
        NotFoundException,
        ConfigurationException
    )
except ImportError:
    # 如果导入失败，提供基本异常类
    class CustomBaseException(Exception):
        def __init__(self, message: str, error_code: str = None):
            super().__init__(message)
            self.message = message
            self.error_code = error_code or self.__class__.__name__
    
    class DomainException(CustomBaseException):
        pass
    
    class InfrastructureException(CustomBaseException):
        pass
    
    class ApplicationException(CustomBaseException):
        pass
    
    class ValidationException(DomainException):
        pass
    
    class NotFoundException(DomainException):
        pass
    
    class ConfigurationException(InfrastructureException):
        pass


class ErrorHandlerMiddleware(MiddlewareBase):
    """错误处理中间件
    
    负责统一处理应用中的各种异常，遵循单一职责原则。
    """
    
    def __init__(self, 
                 logger: Optional[logging.Logger] = None,
                 include_stack_trace: bool = False,
                 custom_handlers: Optional[Dict[Type[Exception], Callable]] = None,
                 priority: int = 1000):
        """初始化错误处理中间件
        
        Args:
            logger: 日志记录器
            include_stack_trace: 是否包含堆栈跟踪
            custom_handlers: 自定义异常处理器
            priority: 中间件优先级
        """
        super().__init__(name="ErrorHandlerMiddleware", priority=priority)
        self.logger = logger or logging.getLogger(__name__)
        self.include_stack_trace = include_stack_trace
        self.custom_handlers = custom_handlers or {}
        
        # 默认错误映射
        self.error_mapping = {
            ValidationException: (400, "VALIDATION_ERROR"),
            NotFoundException: (404, "NOT_FOUND"),
            DomainException: (400, "DOMAIN_ERROR"),
            InfrastructureException: (500, "INFRASTRUCTURE_ERROR"),
            ApplicationException: (500, "APPLICATION_ERROR"),
            ConfigurationException: (500, "CONFIGURATION_ERROR"),
            PermissionError: (403, "PERMISSION_DENIED"),
            FileNotFoundError: (404, "FILE_NOT_FOUND"),
            ValueError: (400, "INVALID_VALUE"),
            TypeError: (400, "INVALID_TYPE"),
            KeyError: (400, "MISSING_KEY"),
            UnicodeError: (400, "ENCODING_ERROR"),
            TimeoutError: (408, "TIMEOUT"),
            ConnectionError: (503, "SERVICE_UNAVAILABLE"),
        }
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求，捕获异常
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 在请求阶段不处理错误，让错误传播到响应阶段
        return MiddlewareResult.continue_execution()
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应，检查是否有错误
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 在响应阶段不处理错误，让错误传播到错误处理阶段
        return MiddlewareResult.continue_execution()
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareResult:
        """处理错误
        
        Args:
            context: 中间件上下文
            error: 错误信息
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 记录错误日志
        await self._log_error(context, error)
        
        # 检查是否有自定义处理器
        for exception_type, handler in self.custom_handlers.items():
            if isinstance(error, exception_type):
                try:
                    custom_result = await handler(context, error)
                    if isinstance(custom_result, MiddlewareResult):
                        return custom_result
                except Exception as handler_error:
                    # 自定义处理器出错，回退到默认处理
                    self.logger.error(f"自定义错误处理器失败: {handler_error}")
        
        # 使用默认错误处理
        error_response = await self._create_error_response(context, error)
        return MiddlewareResult.stop_execution(response=error_response)
    
    async def _log_error(self, context: MiddlewareContext, error: Exception) -> None:
        """记录错误日志
        
        Args:
            context: 中间件上下文
            error: 错误信息
        """
        request = context.request
        
        # 构建日志数据
        log_data = {
            "type": "error",
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "timestamp": context.metadata.get("error_timestamp"),
        }
        
        # 添加用户信息
        if request.user:
            log_data["user_id"] = request.user.get("user_id")
            log_data["username"] = request.user.get("username")
        
        # 添加堆栈跟踪
        if self.include_stack_trace:
            log_data["stack_trace"] = traceback.format_exc()
        
        # 添加自定义异常的额外信息
        if isinstance(error, CustomBaseException):
            if hasattr(error, 'error_code'):
                log_data["error_code"] = error.error_code
            if hasattr(error, 'details'):
                log_data["error_details"] = error.details
        
        # 根据错误类型选择日志级别
        if isinstance(error, (ValidationException, NotFoundException, DomainException)):
            self.logger.warning(f"应用错误: {error}", extra=log_data)
        else:
            self.logger.error(f"系统错误: {error}", extra=log_data)
    
    async def _create_error_response(self, context: MiddlewareContext, error: Exception) -> ResponseContext:
        """创建错误响应
        
        Args:
            context: 中间件上下文
            error: 错误信息
            
        Returns:
            ResponseContext: 错误响应
        """
        # 确定状态码和错误代码
        status_code, error_code = self._determine_error_response(error)
        
        # 构建错误响应体
        error_body = {
            "success": False,
            "message": self._get_error_message(error),
            "code": error_code,
            "timestamp": context.metadata.get("error_timestamp"),
        }
        
        # 添加错误详情
        if isinstance(error, CustomBaseException):
            if hasattr(error, 'details') and error.details:
                error_body["details"] = error.details
        
        # 添加堆栈跟踪（仅在调试模式下）
        if self.include_stack_trace:
            error_body["stack_trace"] = traceback.format_exc()
        
        # 添加请求信息
        error_body["request_info"] = {
            "method": context.request.method,
            "path": context.request.path,
            "request_id": context.request.request_id
        }
        
        # 创建响应
        response = ResponseContext(
            status_code=status_code,
            headers={"content-type": "application/json"},
            body=error_body
        )
        
        return response
    
    def _determine_error_response(self, error: Exception) -> tuple[int, str]:
        """确定错误响应的状态码和错误代码
        
        Args:
            error: 错误信息
            
        Returns:
            tuple[int, str]: 状态码和错误代码
        """
        # 检查自定义异常
        if isinstance(error, CustomBaseException):
            if hasattr(error, 'error_code'):
                # 根据异常类型确定状态码
                if isinstance(error, ValidationException):
                    return 400, error.error_code
                elif isinstance(error, NotFoundException):
                    return 404, error.error_code
                elif isinstance(error, DomainException):
                    return 400, error.error_code
                elif isinstance(error, InfrastructureException):
                    return 500, error.error_code
                elif isinstance(error, ApplicationException):
                    return 500, error.error_code
                else:
                    return 500, error.error_code
        
        # 检查标准异常
        for exception_type, (status_code, error_code) in self.error_mapping.items():
            if isinstance(error, exception_type):
                return status_code, error_code
        
        # 默认为内部服务器错误
        return 500, "INTERNAL_SERVER_ERROR"
    
    def _get_error_message(self, error: Exception) -> str:
        """获取错误消息
        
        Args:
            error: 错误信息
            
        Returns:
            str: 错误消息
        """
        # 优先使用自定义异常的消息
        if isinstance(error, CustomBaseException):
            if hasattr(error, 'message'):
                return error.message
            elif hasattr(error, 'user_message'):
                return error.user_message
        
        # 使用标准异常的消息
        return str(error)
    
    def add_custom_handler(self, exception_type: Type[Exception], handler: Callable) -> None:
        """添加自定义异常处理器
        
        Args:
            exception_type: 异常类型
            handler: 处理器函数
        """
        self.custom_handlers[exception_type] = handler
    
    def remove_custom_handler(self, exception_type: Type[Exception]) -> bool:
        """移除自定义异常处理器
        
        Args:
            exception_type: 异常类型
            
        Returns:
            bool: 是否成功移除
        """
        if exception_type in self.custom_handlers:
            del self.custom_handlers[exception_type]
            return True
        return False
    
    def add_error_mapping(self, exception_type: Type[Exception], status_code: int, error_code: str) -> None:
        """添加错误映射
        
        Args:
            exception_type: 异常类型
            status_code: HTTP状态码
            error_code: 错误代码
        """
        self.error_mapping[exception_type] = (status_code, error_code)
    
    def remove_error_mapping(self, exception_type: Type[Exception]) -> bool:
        """移除错误映射
        
        Args:
            exception_type: 异常类型
            
        Returns:
            bool: 是否成功移除
        """
        if exception_type in self.error_mapping:
            del self.error_mapping[exception_type]
            return True
        return False


class ErrorReporter:
    """错误报告器
    
    负责收集和报告错误统计信息，遵循单一职责原则。
    """
    
    def __init__(self):
        """初始化错误报告器"""
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "error_codes": {},
            "recent_errors": []
        }
        self.max_recent_errors = 100
    
    def record_error(self, error: Exception, context: Optional[MiddlewareContext] = None) -> None:
        """记录错误
        
        Args:
            error: 错误信息
            context: 中间件上下文
        """
        self.error_stats["total_errors"] += 1
        
        # 记录错误类型
        error_type = error.__class__.__name__
        self.error_stats["error_types"][error_type] = (
            self.error_stats["error_types"].get(error_type, 0) + 1
        )
        
        # 记录错误代码（如果是自定义异常）
        if isinstance(error, CustomBaseException) and hasattr(error, 'error_code'):
            error_code = error.error_code
            self.error_stats["error_codes"][error_code] = (
                self.error_stats["error_codes"].get(error_code, 0) + 1
            )
        
        # 记录最近的错误
        error_info = {
            "timestamp": context.metadata.get("error_timestamp") if context else None,
            "type": error_type,
            "message": str(error),
            "path": context.request.path if context and context.request else None,
            "method": context.request.method if context and context.request else None,
            "user_id": context.request.user.get("user_id") if context and context.request and context.request.user else None
        }
        
        self.error_stats["recent_errors"].append(error_info)
        
        # 限制最近错误的数量
        if len(self.error_stats["recent_errors"]) > self.max_recent_errors:
            self.error_stats["recent_errors"].pop(0)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Any]: 错误统计
        """
        return self.error_stats.copy()
    
    def reset_stats(self) -> None:
        """重置错误统计"""
        self.error_stats = {
            "total_errors": 0,
            "error_types": {},
            "error_codes": {},
            "recent_errors": []
        }
    
    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最常见的错误
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict[str, Any]]: 错误列表
        """
        # 按错误类型排序
        sorted_types = sorted(
            self.error_stats["error_types"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {"type": error_type, "count": count}
            for error_type, count in sorted_types[:limit]
        ]