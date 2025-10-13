"""
日志中间件模块

该模块实现日志中间件，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责请求和响应的日志记录。
"""

import time
import json
from typing import Dict, Any, Optional, List
from .middleware_base import MiddlewareBase, MiddlewareContext, MiddlewareResult


class LoggingMiddleware(MiddlewareBase):
    """日志中间件
    
    负责记录API请求和响应的详细信息，遵循单一职责原则。
    """
    
    def __init__(self, 
                 logger: Any,
                 log_request_body: bool = True,
                 log_response_body: bool = True,
                 max_body_size: int = 1000,
                 exclude_paths: Optional[List[str]] = None,
                 include_headers: Optional[List[str]] = None,
                 priority: int = 1000):
        """初始化日志中间件
        
        Args:
            logger: 日志记录器
            log_request_body: 是否记录请求体
            log_response_body: 是否记录响应体
            max_body_size: 最大记录的请求体/响应体大小
            exclude_paths: 排除的路径列表
            include_headers: 包含的头部列表
            priority: 中间件优先级
        """
        super().__init__(name="LoggingMiddleware", priority=priority)
        self.logger = logger
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.exclude_paths = exclude_paths or []
        self.include_headers = include_headers or []
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求日志
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 检查是否在排除路径中
        if self._is_excluded_path(context.request.path):
            return MiddlewareResult.continue_execution()
        
        # 记录请求开始时间
        start_time = time.time()
        context.set_metadata("request_start_time", start_time)
        
        # 记录请求信息
        await self._log_request(context)
        
        return MiddlewareResult.continue_execution()
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应日志
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 检查是否在排除路径中
        if self._is_excluded_path(context.request.path):
            return MiddlewareResult.continue_execution()
        
        # 记录响应信息
        await self._log_response(context)
        
        return MiddlewareResult.continue_execution()
    
    async def _log_request(self, context: MiddlewareContext) -> None:
        """记录请求信息
        
        Args:
            context: 中间件上下文
        """
        request = context.request
        
        # 构建日志数据
        log_data = {
            "type": "request",
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "query_params": request.query_params,
            "timestamp": request.timestamp.isoformat(),
        }
        
        # 添加用户信息
        if request.user:
            log_data["user_id"] = request.user.get("user_id")
            log_data["username"] = request.user.get("username")
        
        # 添加头部信息
        if self.include_headers:
            headers = {}
            for header_name in self.include_headers:
                value = request.get_header(header_name)
                if value:
                    headers[header_name] = value
            if headers:
                log_data["headers"] = headers
        
        # 添加请求体
        if self.log_request_body and request.body:
            log_data["body"] = self._sanitize_body(request.body)
        
        # 记录日志
        self.logger.info(f"API请求: {request.method} {request.path}", extra=log_data)
    
    async def _log_response(self, context: MiddlewareContext) -> None:
        """记录响应信息
        
        Args:
            context: 中间件上下文
        """
        request = context.request
        response = context.response
        
        # 计算处理时间
        start_time = context.get_metadata("request_start_time")
        processing_time = None
        if start_time:
            processing_time = time.time() - start_time
        
        # 构建日志数据
        log_data = {
            "type": "response",
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "content_type": response.content_type,
            "timestamp": time.time(),
        }
        
        # 添加处理时间
        if processing_time is not None:
            log_data["processing_time_ms"] = round(processing_time * 1000, 2)
        
        # 添加用户信息
        if request.user:
            log_data["user_id"] = request.user.get("user_id")
            log_data["username"] = request.user.get("username")
        
        # 添加响应体
        if self.log_response_body and response.body:
            log_data["body"] = self._sanitize_body(response.body)
        
        # 根据状态码选择日志级别
        if response.status_code >= 500:
            self.logger.error(f"API响应: {response.status_code} {request.method} {request.path}", extra=log_data)
        elif response.status_code >= 400:
            self.logger.warning(f"API响应: {response.status_code} {request.method} {request.path}", extra=log_data)
        else:
            self.logger.info(f"API响应: {response.status_code} {request.method} {request.path}", extra=log_data)
    
    def _sanitize_body(self, body: Any) -> Any:
        """清理请求体/响应体
        
        移除敏感信息并限制大小。
        
        Args:
            body: 请求体/响应体
            
        Returns:
            Any: 清理后的数据
        """
        if body is None:
            return None
        
        # 转换为字符串
        if isinstance(body, (dict, list)):
            body_str = json.dumps(body, ensure_ascii=False)
        else:
            body_str = str(body)
        
        # 检查大小
        if len(body_str) > self.max_body_size:
            return f"<数据过大，已截断。原始大小: {len(body_str)} 字节>"
        
        # 移除敏感信息
        if isinstance(body, dict):
            sanitized = {}
            sensitive_keys = ["password", "token", "secret", "key", "auth"]
            
            for key, value in body.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "<已隐藏>"
                else:
                    sanitized[key] = value
            
            return sanitized
        
        return body
    
    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否排除
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False


class PerformanceMiddleware(MiddlewareBase):
    """性能监控中间件
    
    专门负责性能指标的收集和记录，遵循单一职责原则。
    """
    
    def __init__(self, 
                 logger: Any,
                 slow_request_threshold: float = 1.0,
                 priority: int = 900):
        """初始化性能监控中间件
        
        Args:
            logger: 日志记录器
            slow_request_threshold: 慢请求阈值（秒）
            priority: 中间件优先级
        """
        super().__init__(name="PerformanceMiddleware", priority=priority)
        self.logger = logger
        self.slow_request_threshold = slow_request_threshold
        
        # 性能统计
        self.request_count = 0
        self.total_processing_time = 0.0
        self.slow_request_count = 0
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求，记录开始时间
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        start_time = time.time()
        context.set_metadata("performance_start_time", start_time)
        
        return MiddlewareResult.continue_execution()
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应，计算性能指标
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        start_time = context.get_metadata("performance_start_time")
        if start_time:
            processing_time = time.time() - start_time
            self._record_performance(context, processing_time)
        
        return MiddlewareResult.continue_execution()
    
    def _record_performance(self, context: MiddlewareContext, processing_time: float) -> None:
        """记录性能指标
        
        Args:
            context: 中间件上下文
            processing_time: 处理时间（秒）
        """
        request = context.request
        response = context.response
        
        # 更新统计
        self.request_count += 1
        self.total_processing_time += processing_time
        
        if processing_time > self.slow_request_threshold:
            self.slow_request_count += 1
        
        # 构建性能日志
        performance_data = {
            "type": "performance",
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "processing_time_ms": round(processing_time * 1000, 2),
            "is_slow": processing_time > self.slow_request_threshold,
            "timestamp": time.time(),
        }
        
        # 添加用户信息
        if request.user:
            performance_data["user_id"] = request.user.get("user_id")
        
        # 记录性能日志
        if processing_time > self.slow_request_threshold:
            self.logger.warning(
                f"慢请求检测: {request.method} {request.path} 耗时 {processing_time:.2f}s",
                extra=performance_data
            )
        else:
            self.logger.debug(
                f"请求性能: {request.method} {request.path} 耗时 {processing_time:.2f}s",
                extra=performance_data
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计
        """
        avg_processing_time = (
            self.total_processing_time / self.request_count 
            if self.request_count > 0 else 0
        )
        
        slow_request_rate = (
            self.slow_request_count / self.request_count 
            if self.request_count > 0 else 0
        )
        
        return {
            "request_count": self.request_count,
            "total_processing_time": round(self.total_processing_time, 2),
            "average_processing_time_ms": round(avg_processing_time * 1000, 2),
            "slow_request_count": self.slow_request_count,
            "slow_request_rate": round(slow_request_rate * 100, 2),
            "slow_request_threshold": self.slow_request_threshold
        }
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        self.request_count = 0
        self.total_processing_time = 0.0
        self.slow_request_count = 0