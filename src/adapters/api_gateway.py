"""
API网关模块

该模块实现API网关，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责请求的路由、分发和管理。
"""

import asyncio
import json
import re
from typing import Dict, Any, Optional, List, Callable, Union, Pattern
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import parse_qs, urlparse

from .middleware import MiddlewarePipeline, MiddlewareContext, RequestContext, ResponseContext
from ..domain.responses.api_response import ApiResponse, ResponseBuilder


@dataclass
class Route:
    """路由定义
    
    封装路由的相关信息，遵循单一职责原则。
    """
    
    path: str
    method: str
    handler: Callable
    name: Optional[str] = None
    middleware: List[Any] = field(default_factory=list)
    version: str = "v1"
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """初始化后处理"""
        self.path_pattern = self._compile_path_pattern()
        self.param_names = self._extract_param_names()
    
    def _compile_path_pattern(self) -> Pattern:
        """编译路径模式
        
        Returns:
            Pattern: 编译后的正则表达式
        """
        # 将路径参数转换为正则表达式
        # 例如: /users/{id}/posts/{post_id} -> /users/([^/]+)/posts/([^/]+)
        pattern = re.sub(r'\{([^}]+)\}', r'([^/]+)', self.path)
        pattern = f"^{pattern}$"
        return re.compile(pattern)
    
    def _extract_param_names(self) -> List[str]:
        """提取路径参数名
        
        Returns:
            List[str]: 参数名列表
        """
        return re.findall(r'\{([^}]+)\}', self.path)
    
    def matches(self, path: str, method: str) -> bool:
        """检查路径和方法是否匹配
        
        Args:
            path: 请求路径
            method: 请求方法
            
        Returns:
            bool: 是否匹配
        """
        return (
            self.path_pattern.match(path) is not None and
            self.method.upper() == method.upper()
        )
    
    def extract_params(self, path: str) -> Dict[str, str]:
        """提取路径参数
        
        Args:
            path: 请求路径
            
        Returns:
            Dict[str, str]: 参数字典
        """
        match = self.path_pattern.match(path)
        if not match:
            return {}
        
        return dict(zip(self.param_names, match.groups()))


@dataclass
class RouteGroup:
    """路由组
    
    将相关的路由组织在一起，遵循单一职责原则。
    """
    
    prefix: str
    routes: List[Route] = field(default_factory=list)
    middleware: List[Any] = field(default_factory=list)
    version: str = "v1"
    description: Optional[str] = None
    
    def add_route(self, route: Route) -> 'RouteGroup':
        """添加路由
        
        Args:
            route: 路由定义
            
        Returns:
            RouteGroup: 返回自身以支持链式调用
        """
        # 为路由添加前缀
        route.path = self.prefix + route.path
        route.version = self.version
        
        # 合并中间件
        route.middleware = self.middleware + route.middleware
        
        self.routes.append(route)
        return self
    
    def get_routes(self) -> List[Route]:
        """获取所有路由
        
        Returns:
            List[Route]: 路由列表
        """
        return self.routes.copy()


class ApiGateway:
    """API网关
    
    负责请求的路由、分发和管理，遵循单一职责原则。
    """
    
    def __init__(self, 
                 name: str = "API Gateway",
                 version: str = "1.0.0",
                 enable_cors: bool = True,
                 enable_rate_limit: bool = True,
                 enable_auth: bool = False):
        """初始化API网关
        
        Args:
            name: 网关名称
            version: 网关版本
            enable_cors: 是否启用CORS
            enable_rate_limit: 是否启用限流
            enable_auth: 是否启用认证
        """
        self.name = name
        self.version = version
        self.enable_cors = enable_cors
        self.enable_rate_limit = enable_rate_limit
        self.enable_auth = enable_auth
        
        # 路由管理
        self.routes: List[Route] = []
        self.route_groups: List[RouteGroup] = []
        
        # 中间件管道
        self.middleware_pipeline = MiddlewarePipeline()
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "routes_count": 0,
            "start_time": datetime.now()
        }
        
        # 初始化默认中间件
        self._initialize_default_middleware()
    
    def _initialize_default_middleware(self) -> None:
        """初始化默认中间件"""
        # 这里会根据配置添加相应的中间件
        # 实际实现中需要从依赖注入容器获取中间件实例
        pass
    
    def add_route(self, 
                  path: str, 
                  method: str, 
                  handler: Callable,
                  name: Optional[str] = None,
                  middleware: Optional[List[Any]] = None,
                  version: str = "v1",
                  description: Optional[str] = None,
                  tags: Optional[List[str]] = None) -> 'ApiGateway':
        """添加路由
        
        Args:
            path: 路由路径
            method: HTTP方法
            handler: 处理函数
            name: 路由名称
            middleware: 中间件列表
            version: API版本
            description: 路由描述
            tags: 标签列表
            
        Returns:
            ApiGateway: 返回自身以支持链式调用
        """
        route = Route(
            path=path,
            method=method,
            handler=handler,
            name=name,
            middleware=middleware or [],
            version=version,
            description=description,
            tags=tags or []
        )
        
        self.routes.append(route)
        self.stats["routes_count"] += 1
        
        return self
    
    def add_route_group(self, route_group: RouteGroup) -> 'ApiGateway':
        """添加路由组
        
        Args:
            route_group: 路由组
            
        Returns:
            ApiGateway: 返回自身以支持链式调用
        """
        self.route_groups.append(route_group)
        self.routes.extend(route_group.get_routes())
        self.stats["routes_count"] += len(route_group.get_routes())
        
        return self
    
    def create_route_group(self, 
                          prefix: str,
                          version: str = "v1",
                          description: Optional[str] = None) -> RouteGroup:
        """创建路由组
        
        Args:
            prefix: 路由前缀
            version: API版本
            description: 路由组描述
            
        Returns:
            RouteGroup: 路由组实例
        """
        return RouteGroup(
            prefix=prefix,
            version=version,
            description=description
        )
    
    def add_middleware(self, middleware: Any) -> 'ApiGateway':
        """添加全局中间件
        
        Args:
            middleware: 中间件实例
            
        Returns:
            ApiGateway: 返回自身以支持链式调用
        """
        self.middleware_pipeline.add_middleware(middleware)
        return self
    
    async def handle_request(self, 
                           method: str,
                           path: str,
                           headers: Optional[Dict[str, str]] = None,
                           query_params: Optional[Dict[str, str]] = None,
                           body: Optional[Any] = None) -> ResponseContext:
        """处理请求
        
        Args:
            method: HTTP方法
            path: 请求路径
            headers: 请求头
            query_params: 查询参数
            body: 请求体
            
        Returns:
            ResponseContext: 响应上下文
        """
        self.stats["total_requests"] += 1
        
        # 创建请求上下文
        request = RequestContext(
            method=method,
            path=path,
            headers=headers or {},
            query_params=query_params or {},
            body=body
        )
        
        # 创建响应上下文
        response = ResponseContext()
        
        # 创建中间件上下文
        context = MiddlewareContext(
            request=request,
            response=response
        )
        
        try:
            # 查找匹配的路由
            route = self._find_route(path, method)
            if not route:
                response.status_code = 404
                response.body = ResponseBuilder.error(
                    message="未找到匹配的路由",
                    code="ROUTE_NOT_FOUND"
                ).to_dict()
                return response
            
            # 提取路径参数
            path_params = route.extract_params(path)
            context.set_metadata("path_params", path_params)
            context.set_metadata("route", route)
            
            # 执行中间件管道（请求阶段）
            middleware_result = await self.middleware_pipeline.process_request(context)
            if not middleware_result.should_continue:
                if middleware_result.response_override:
                    return middleware_result.response_override
                if middleware_result.error:
                    raise middleware_result.error
            
            # 执行路由处理器
            await self._execute_handler(route, context)
            
            # 执行中间件管道（响应阶段）
            middleware_result = await self.middleware_pipeline.process_response(context)
            if not middleware_result.should_continue:
                if middleware_result.response_override:
                    return middleware_result.response_override
            
            self.stats["successful_requests"] += 1
            return response
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            
            # 执行中间件管道（错误处理）
            middleware_result = await self.middleware_pipeline.on_error(context, e)
            if middleware_result.response_override:
                return middleware_result.response_override
            
            # 如果没有中间件处理错误，返回默认错误响应
            response.status_code = 500
            response.body = ResponseBuilder.error(
                message="内部服务器错误",
                code="INTERNAL_SERVER_ERROR"
            ).to_dict()
            
            return response
    
    def _find_route(self, path: str, method: str) -> Optional[Route]:
        """查找匹配的路由
        
        Args:
            path: 请求路径
            method: HTTP方法
            
        Returns:
            Optional[Route]: 匹配的路由
        """
        for route in self.routes:
            if route.matches(path, method):
                return route
        return None
    
    async def _execute_handler(self, route: Route, context: MiddlewareContext) -> None:
        """执行路由处理器
        
        Args:
            route: 路由定义
            context: 中间件上下文
        """
        # 准备处理器参数
        handler_kwargs = {
            "request": context.request,
            "response": context.response,
            "context": context
        }
        
        # 添加路径参数
        path_params = context.get_metadata("path_params", {})
        handler_kwargs.update(path_params)
        
        # 添加查询参数
        handler_kwargs.update(context.request.query_params)
        
        # 执行处理器
        if asyncio.iscoroutinefunction(route.handler):
            result = await route.handler(**handler_kwargs)
        else:
            result = route.handler(**handler_kwargs)
        
        # 处理返回结果
        self._process_handler_result(result, context.response)
    
    def _process_handler_result(self, result: Any, response: ResponseContext) -> None:
        """处理处理器返回结果
        
        Args:
            result: 处理器返回结果
            response: 响应上下文
        """
        if result is None:
            # 处理器没有返回结果，使用默认响应
            response.body = ResponseBuilder.success().to_dict()
        
        elif isinstance(result, ApiResponse):
            # 返回的是ApiResponse对象
            response.body = result.to_dict()
            response.status_code = 200 if result.success else 400
        
        elif isinstance(result, dict):
            # 返回的是字典，直接作为响应体
            response.body = result
        
        elif isinstance(result, (str, int, float, bool)):
            # 返回的是基本类型，包装为响应
            response.body = {"data": result}
        
        else:
            # 其他类型，转换为字符串
            response.body = {"data": str(result)}
        
        # 设置响应头
        if not response.get_header("content-type"):
            response.set_header("content-type", "application/json")
    
    def get_routes_info(self) -> List[Dict[str, Any]]:
        """获取路由信息
        
        Returns:
            List[Dict[str, Any]]: 路由信息列表
        """
        return [
            {
                "path": route.path,
                "method": route.method,
                "name": route.name,
                "version": route.version,
                "description": route.description,
                "tags": route.tags,
                "param_names": route.param_names
            }
            for route in self.routes
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.stats.copy()
        stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
        
        if stats["total_requests"] > 0:
            stats["success_rate"] = round(
                stats["successful_requests"] / stats["total_requests"] * 100, 2
            )
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats.update({
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "start_time": datetime.now()
        })
    
    def get_route_by_name(self, name: str) -> Optional[Route]:
        """根据名称查找路由
        
        Args:
            name: 路由名称
            
        Returns:
            Optional[Route]: 路由定义
        """
        for route in self.routes:
            if route.name == name:
                return route
        return None
    
    def get_routes_by_tag(self, tag: str) -> List[Route]:
        """根据标签查找路由
        
        Args:
            tag: 标签
            
        Returns:
            List[Route]: 路由列表
        """
        return [route for route in self.routes if tag in route.tags]
    
    def get_routes_by_version(self, version: str) -> List[Route]:
        """根据版本查找路由
        
        Args:
            version: API版本
            
        Returns:
            List[Route]: 路由列表
        """
        return [route for route in self.routes if route.version == version]


# 路由装饰器
def route(path: str, 
          method: str = "GET",
          name: Optional[str] = None,
          middleware: Optional[List[Any]] = None,
          version: str = "v1",
          description: Optional[str] = None,
          tags: Optional[List[str]] = None):
    """路由装饰器
    
    用于装饰函数，将其注册为路由处理器。
    
    Args:
        path: 路由路径
        method: HTTP方法
        name: 路由名称
        middleware: 中间件列表
        version: API版本
        description: 路由描述
        tags: 标签列表
    """
    def decorator(func):
        func._route_info = {
            "path": path,
            "method": method,
            "name": name,
            "middleware": middleware,
            "version": version,
            "description": description,
            "tags": tags
        }
        return func
    return decorator


class RouteScanner:
    """路由扫描器
    
    负责自动发现和注册路由，遵循单一职责原则。
    """
    
    def __init__(self, gateway: ApiGateway):
        """初始化路由扫描器
        
        Args:
            gateway: API网关实例
        """
        self.gateway = gateway
    
    def scan_routes(self, module_or_class: Any) -> None:
        """扫描模块或类中的路由
        
        Args:
            module_or_class: 模块或类对象
        """
        if hasattr(module_or_class, '__dict__'):
            # 扫描类或模块的所有属性
            for name, obj in module_or_class.__dict__.items():
                if callable(obj) and hasattr(obj, '_route_info'):
                    route_info = obj._route_info
                    self.gateway.add_route(
                        path=route_info["path"],
                        method=route_info["method"],
                        handler=obj,
                        name=route_info.get("name"),
                        middleware=route_info.get("middleware"),
                        version=route_info.get("version", "v1"),
                        description=route_info.get("description"),
                        tags=route_info.get("tags")
                    )