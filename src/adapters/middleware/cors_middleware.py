"""
CORS中间件模块

该模块实现CORS（跨域资源共享）中间件，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责跨域请求的处理。
"""

from typing import Dict, List, Optional, Union
from .middleware_base import MiddlewareBase, MiddlewareContext, MiddlewareResult, ResponseContext


class CorsMiddleware(MiddlewareBase):
    """CORS中间件
    
    负责处理跨域资源共享，遵循单一职责原则。
    """
    
    def __init__(self,
                 allowed_origins: Optional[List[str]] = None,
                 allowed_methods: Optional[List[str]] = None,
                 allowed_headers: Optional[List[str]] = None,
                 exposed_headers: Optional[List[str]] = None,
                 allow_credentials: bool = False,
                 max_age: Optional[int] = None,
                 priority: int = 50):
        """初始化CORS中间件
        
        Args:
            allowed_origins: 允许的源列表，* 表示允许所有源
            allowed_methods: 允许的HTTP方法列表
            allowed_headers: 允许的请求头列表
            exposed_headers: 暴露的响应头列表
            allow_credentials: 是否允许携带凭据
            max_age: 预检请求的缓存时间（秒）
            priority: 中间件优先级
        """
        super().__init__(name="CorsMiddleware", priority=priority)
        
        # 设置默认值
        self.allowed_origins = allowed_origins or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = allowed_headers or ["Content-Type", "Authorization", "X-Requested-With"]
        self.exposed_headers = exposed_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求，检查CORS
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        request = context.request
        response = context.response
        
        # 获取请求头信息
        origin = request.get_header("origin")
        request_method = request.get_header("access-control-request-method")
        request_headers = request.get_header("access-control-request-headers")
        
        # 处理预检请求（OPTIONS）
        if request.method.upper() == "OPTIONS":
            return await self._handle_preflight_request(context, origin, request_method, request_headers)
        
        # 处理实际请求
        return await self._handle_actual_request(context, origin)
    
    async def process_response(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理响应，添加CORS头
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 在响应处理阶段确保CORS头已设置
        return MiddlewareResult.continue_execution()
    
    async def _handle_preflight_request(self, 
                                       context: MiddlewareContext,
                                       origin: Optional[str],
                                       request_method: Optional[str],
                                       request_headers: Optional[str]) -> MiddlewareResult:
        """处理预检请求
        
        Args:
            context: 中间件上下文
            origin: 请求源
            request_method: 请求方法
            request_headers: 请求头
            
        Returns:
            MiddlewareResult: 处理结果
        """
        response = context.response
        
        # 检查源是否允许
        if not self._is_origin_allowed(origin):
            response.status_code = 403
            response.body = {"error": "CORS: Origin not allowed"}
            return MiddlewareResult.stop_execution()
        
        # 检查方法是否允许
        if request_method and not self._is_method_allowed(request_method):
            response.status_code = 405
            response.body = {"error": "CORS: Method not allowed"}
            return MiddlewareResult.stop_execution()
        
        # 检查请求头是否允许
        if request_headers and not self._are_headers_allowed(request_headers):
            response.status_code = 400
            response.body = {"error": "CORS: Headers not allowed"}
            return MiddlewareResult.stop_execution()
        
        # 设置CORS响应头
        self._set_cors_headers(response, origin, is_preflight=True)
        
        # 预检请求返回204 No Content
        response.status_code = 204
        response.body = None
        
        return MiddlewareResult.stop_execution()
    
    async def _handle_actual_request(self, 
                                    context: MiddlewareContext,
                                    origin: Optional[str]) -> MiddlewareResult:
        """处理实际请求
        
        Args:
            context: 中间件上下文
            origin: 请求源
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 检查源是否允许
        if not self._is_origin_allowed(origin):
            # 如果源不允许，不设置CORS头，让浏览器处理
            return MiddlewareResult.continue_execution()
        
        # 设置CORS响应头
        self._set_cors_headers(context.response, origin, is_preflight=False)
        
        return MiddlewareResult.continue_execution()
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """检查源是否允许
        
        Args:
            origin: 请求源
            
        Returns:
            bool: 是否允许
        """
        if not origin:
            return True  # 没有Origin头的请求不是跨域请求
        
        if "*" in self.allowed_origins:
            return True
        
        return origin in self.allowed_origins
    
    def _is_method_allowed(self, method: Optional[str]) -> bool:
        """检查方法是否允许
        
        Args:
            method: HTTP方法
            
        Returns:
            bool: 是否允许
        """
        if not method:
            return True
        
        return method.upper() in [m.upper() for m in self.allowed_methods]
    
    def _are_headers_allowed(self, headers: Optional[str]) -> bool:
        """检查请求头是否允许
        
        Args:
            headers: 请求头（逗号分隔）
            
        Returns:
            bool: 是否允许
        """
        if not headers:
            return True
        
        if "*" in self.allowed_headers:
            return True
        
        requested_headers = [h.strip().lower() for h in headers.split(",")]
        allowed_headers = [h.lower() for h in self.allowed_headers]
        
        return all(header in allowed_headers for header in requested_headers)
    
    def _set_cors_headers(self, 
                         response: ResponseContext,
                         origin: Optional[str],
                         is_preflight: bool = False) -> None:
        """设置CORS响应头
        
        Args:
            response: 响应上下文
            origin: 请求源
            is_preflight: 是否为预检请求
        """
        # 设置Access-Control-Allow-Origin
        if "*" in self.allowed_origins:
            response.set_header("Access-Control-Allow-Origin", "*")
        elif origin:
            response.set_header("Access-Control-Allow-Origin", origin)
        
        # 设置Access-Control-Allow-Credentials
        if self.allow_credentials and "*" not in self.allowed_origins:
            response.set_header("Access-Control-Allow-Credentials", "true")
        
        # 设置Access-Control-Allow-Methods（预检请求）
        if is_preflight:
            response.set_header(
                "Access-Control-Allow-Methods",
                ", ".join(self.allowed_methods)
            )
        
        # 设置Access-Control-Allow-Headers（预检请求）
        if is_preflight:
            if "*" in self.allowed_headers:
                response.set_header("Access-Control-Allow-Headers", "*")
            else:
                response.set_header(
                    "Access-Control-Allow-Headers",
                    ", ".join(self.allowed_headers)
                )
        
        # 设置Access-Control-Expose-Headers（实际请求）
        if not is_preflight and self.exposed_headers:
            response.set_header(
                "Access-Control-Expose-Headers",
                ", ".join(self.exposed_headers)
            )
        
        # 设置Access-Control-Max-Age（预检请求）
        if is_preflight and self.max_age:
            response.set_header("Access-Control-Max-Age", str(self.max_age))
    
    def add_allowed_origin(self, origin: str) -> None:
        """添加允许的源
        
        Args:
            origin: 源地址
        """
        if origin not in self.allowed_origins:
            self.allowed_origins.append(origin)
    
    def remove_allowed_origin(self, origin: str) -> None:
        """移除允许的源
        
        Args:
            origin: 源地址
        """
        if origin in self.allowed_origins:
            self.allowed_origins.remove(origin)
    
    def add_allowed_method(self, method: str) -> None:
        """添加允许的HTTP方法
        
        Args:
            method: HTTP方法
        """
        method_upper = method.upper()
        if method_upper not in [m.upper() for m in self.allowed_methods]:
            self.allowed_methods.append(method_upper)
    
    def remove_allowed_method(self, method: str) -> None:
        """移除允许的HTTP方法
        
        Args:
            method: HTTP方法
        """
        method_upper = method.upper()
        self.allowed_methods = [
            m for m in self.allowed_methods 
            if m.upper() != method_upper
        ]
    
    def add_allowed_header(self, header: str) -> None:
        """添加允许的请求头
        
        Args:
            header: 请求头
        """
        if header not in self.allowed_headers:
            self.allowed_headers.append(header)
    
    def remove_allowed_header(self, header: str) -> None:
        """移除允许的请求头
        
        Args:
            header: 请求头
        """
        if header in self.allowed_headers:
            self.allowed_headers.remove(header)
    
    def add_exposed_header(self, header: str) -> None:
        """添加暴露的响应头
        
        Args:
            header: 响应头
        """
        if header not in self.exposed_headers:
            self.exposed_headers.append(header)
    
    def remove_exposed_header(self, header: str) -> None:
        """移除暴露的响应头
        
        Args:
            header: 响应头
        """
        if header in self.exposed_headers:
            self.exposed_headers.remove(header)
    
    def get_config(self) -> Dict[str, Union[List[str], bool, int]]:
        """获取当前CORS配置
        
        Returns:
            Dict[str, Union[List[str], bool, int]]: CORS配置
        """
        return {
            "allowed_origins": self.allowed_origins,
            "allowed_methods": self.allowed_methods,
            "allowed_headers": self.allowed_headers,
            "exposed_headers": self.exposed_headers,
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age
        }