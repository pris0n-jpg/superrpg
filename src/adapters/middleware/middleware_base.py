"""
中间件基类模块

该模块定义了中间件的基础接口和上下文，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class RequestContext:
    """请求上下文
    
    封装HTTP请求的相关信息，遵循单一职责原则。
    """
    
    method: str
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    user: Optional[Dict[str, Any]] = None
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取请求头
        
        Args:
            name: 头部名称
            default: 默认值
            
        Returns:
            Optional[str]: 头部值
        """
        return self.headers.get(name.lower(), default)
    
    def get_query_param(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取查询参数
        
        Args:
            name: 参数名称
            default: 默认值
            
        Returns:
            Optional[str]: 参数值
        """
        return self.query_params.get(name, default)


@dataclass
class ResponseContext:
    """响应上下文
    
    封装HTTP响应的相关信息，遵循单一职责原则。
    """
    
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    content_type: str = "application/json"
    
    def set_header(self, name: str, value: str) -> None:
        """设置响应头
        
        Args:
            name: 头部名称
            value: 头部值
        """
        self.headers[name.lower()] = value
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """获取响应头
        
        Args:
            name: 头部名称
            default: 默认值
            
        Returns:
            Optional[str]: 头部值
        """
        return self.headers.get(name.lower(), default)


@dataclass
class MiddlewareContext:
    """中间件上下文
    
    封装中间件执行过程中的所有上下文信息，遵循单一职责原则。
    """
    
    request: RequestContext
    response: ResponseContext
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            Any: 元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据
        
        Args:
            key: 键名
            value: 值
        """
        self.metadata[key] = value
    
    def has_metadata(self, key: str) -> bool:
        """检查元数据是否存在
        
        Args:
            key: 键名
            
        Returns:
            bool: 是否存在
        """
        return key in self.metadata


class MiddlewareResult:
    """中间件执行结果
    
    封装中间件的执行结果，遵循单一职责原则。
    """
    
    def __init__(self, 
                 should_continue: bool = True, 
                 error: Optional[Exception] = None,
                 response_override: Optional[ResponseContext] = None):
        """初始化中间件结果
        
        Args:
            should_continue: 是否继续执行后续中间件
            error: 错误信息
            response_override: 覆盖的响应
        """
        self.should_continue = should_continue
        self.error = error
        self.response_override = response_override
    
    @classmethod
    def continue_execution(cls) -> 'MiddlewareResult':
        """创建继续执行的结果
        
        Returns:
            MiddlewareResult: 继续执行的结果
        """
        return cls(should_continue=True)
    
    @classmethod
    def stop_execution(cls, 
                      response: Optional[ResponseContext] = None) -> 'MiddlewareResult':
        """创建停止执行的结果
        
        Args:
            response: 覆盖的响应
            
        Returns:
            MiddlewareResult: 停止执行的结果
        """
        return cls(should_continue=False, response_override=response)
    
    @classmethod
    def error_result(cls, error: Exception) -> 'MiddlewareResult':
        """创建错误结果
        
        Args:
            error: 错误信息
            
        Returns:
            MiddlewareResult: 错误结果
        """
        return cls(should_continue=False, error=error)


class MiddlewareBase(ABC):
    """中间件基类
    
    定义中间件的基础接口，遵循依赖倒置原则。
    所有中间件都应该继承此类并实现相应方法。
    """
    
    def __init__(self, name: Optional[str] = None, priority: int = 0):
        """初始化中间件
        
        Args:
            name: 中间件名称
            priority: 优先级（数字越大优先级越高）
        """
        self.name = name or self.__class__.__name__
        self.priority = priority
        self.enabled = True
    
    @abstractmethod
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求
        
        在请求到达处理器之前执行。
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        pass
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应
        
        在响应返回给客户端之前执行。
        默认实现为继续执行。
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        return MiddlewareResult.continue_execution()
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareResult:
        """处理错误
        
        当处理过程中发生错误时执行。
        默认实现为继续传播错误。
        
        Args:
            context: 中间件上下文
            error: 错误信息
            
        Returns:
            MiddlewareResult: 处理结果
        """
        return MiddlewareResult.error_result(error)
    
    def enable(self) -> None:
        """启用中间件"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用中间件"""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """检查中间件是否启用
        
        Returns:
            bool: 是否启用
        """
        return self.enabled


class MiddlewarePipeline:
    """中间件管道
    
    管理中间件的执行顺序和流程，遵循单一职责原则。
    """
    
    def __init__(self):
        """初始化中间件管道"""
        self._middlewares: List[MiddlewareBase] = []
    
    def add_middleware(self, middleware: MiddlewareBase) -> 'MiddlewarePipeline':
        """添加中间件
        
        Args:
            middleware: 中间件实例
            
        Returns:
            MiddlewarePipeline: 返回自身以支持链式调用
        """
        self._middlewares.append(middleware)
        # 按优先级排序（数字越大优先级越高）
        self._middlewares.sort(key=lambda m: m.priority, reverse=True)
        return self
    
    def remove_middleware(self, middleware: MiddlewareBase) -> 'MiddlewarePipeline':
        """移除中间件
        
        Args:
            middleware: 中间件实例
            
        Returns:
            MiddlewarePipeline: 返回自身以支持链式调用
        """
        if middleware in self._middlewares:
            self._middlewares.remove(middleware)
        return self
    
    def get_middlewares(self) -> List[MiddlewareBase]:
        """获取所有中间件
        
        Returns:
            List[MiddlewareBase]: 中间件列表
        """
        return self._middlewares.copy()
    
    def get_enabled_middlewares(self) -> List[MiddlewareBase]:
        """获取启用的中间件
        
        Returns:
            List[MiddlewareBase]: 启用的中间件列表
        """
        return [m for m in self._middlewares if m.is_enabled()]
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求
        
        按顺序执行所有中间件的请求处理方法。
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        for middleware in self.get_enabled_middlewares():
            try:
                result = await middleware.process_request(context)
                if not result.should_continue:
                    return result
                if result.error:
                    return await self._handle_error(context, result.error)
            except Exception as e:
                return await self._handle_error(context, e)
        
        return MiddlewareResult.continue_execution()
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应
        
        按逆序执行所有中间件的响应处理方法。
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        for middleware in reversed(self.get_enabled_middlewares()):
            try:
                result = await middleware.process_response(context)
                if not result.should_continue:
                    return result
                if result.error:
                    return await self._handle_error(context, result.error)
            except Exception as e:
                return await self._handle_error(context, e)
        
        return MiddlewareResult.continue_execution()
    
    async def _handle_error(self, context: MiddlewareContext, error: Exception) -> MiddlewareResult:
        """处理错误
        
        按顺序执行所有中间件的错误处理方法。
        
        Args:
            context: 中间件上下文
            error: 错误信息
            
        Returns:
            MiddlewareResult: 处理结果
        """
        for middleware in self.get_enabled_middlewares():
            try:
                result = await middleware.on_error(context, error)
                if not result.should_continue:
                    return result
            except Exception:
                # 错误处理方法本身出错，继续尝试下一个中间件
                continue
        
        # 如果没有中间件处理错误，返回错误结果
        return MiddlewareResult.error_result(error)
    
    def clear(self) -> 'MiddlewarePipeline':
        """清除所有中间件
        
        Returns:
            MiddlewarePipeline: 返回自身以支持链式调用
        """
        self._middlewares.clear()
        return self