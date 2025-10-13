"""
API响应格式模块

该模块定义了统一的API响应格式，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责响应数据的标准化封装。
"""

from typing import Dict, Any, Optional, List, Union, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
import json

T = TypeVar('T')


@dataclass
class ApiResponse(Generic[T]):
    """API响应基类
    
    提供统一的API响应格式，封装响应数据、状态和元数据。
    遵循单一职责原则，专门负责响应数据的标准化。
    """
    
    success: bool
    message: str
    data: Optional[T] = None
    code: str = "SUCCESS"
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 响应的字典表示
        """
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'code': self.code,
            'timestamp': self.timestamp.isoformat(),
            'request_id': self.request_id,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串
        
        Returns:
            str: JSON格式的响应字符串
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    @classmethod
    def success_response(cls, 
                        data: Optional[T] = None, 
                        message: str = "操作成功",
                        code: str = "SUCCESS",
                        **metadata) -> 'ApiResponse[T]':
        """创建成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            code: 响应代码
            **metadata: 额外的元数据
            
        Returns:
            ApiResponse[T]: 成功响应实例
        """
        return cls(
            success=True,
            message=message,
            data=data,
            code=code,
            metadata=metadata
        )
    
    @classmethod
    def error_response(cls, 
                      message: str, 
                      code: str = "ERROR",
                      data: Optional[T] = None,
                      **metadata) -> 'ApiResponse[T]':
        """创建错误响应
        
        Args:
            message: 错误消息
            code: 错误代码
            data: 错误详情数据
            **metadata: 额外的元数据
            
        Returns:
            ApiResponse[T]: 错误响应实例
        """
        return cls(
            success=False,
            message=message,
            data=data,
            code=code,
            metadata=metadata
        )


@dataclass
class PagedResponse(ApiResponse[List[T]]):
    """分页响应类
    
    扩展自ApiResponse，专门用于分页数据的响应。
    遵循单一职责原则，专门负责分页数据的封装。
    """
    
    page: int = 1
    page_size: int = 10
    total: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
            self.has_next = self.page < self.total_pages
            self.has_prev = self.page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 分页响应的字典表示
        """
        base_dict = super().to_dict()
        base_dict.update({
            'pagination': {
                'page': self.page,
                'page_size': self.page_size,
                'total': self.total,
                'total_pages': self.total_pages,
                'has_next': self.has_next,
                'has_prev': self.has_prev
            }
        })
        return base_dict
    
    @classmethod
    def create_paged_response(cls,
                            items: List[T],
                            page: int,
                            page_size: int,
                            total: int,
                            message: str = "查询成功",
                            **metadata) -> 'PagedResponse[T]':
        """创建分页响应
        
        Args:
            items: 数据项列表
            page: 当前页码
            page_size: 每页大小
            total: 总记录数
            message: 响应消息
            **metadata: 额外的元数据
            
        Returns:
            PagedResponse[T]: 分页响应实例
        """
        return cls(
            success=True,
            message=message,
            data=items,
            page=page,
            page_size=page_size,
            total=total,
            metadata=metadata
        )


@dataclass
class ValidationError:
    """验证错误详情
    
    封装字段验证错误信息，遵循单一职责原则。
    """
    
    field: str
    message: str
    value: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 验证错误的字典表示
        """
        return {
            'field': self.field,
            'message': self.message,
            'value': self.value
        }


@dataclass
class ValidationErrorResponse(ApiResponse[None]):
    """验证错误响应类
    
    专门用于验证失败的响应，包含详细的字段错误信息。
    """
    
    errors: List[ValidationError] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 验证错误响应的字典表示
        """
        base_dict = super().to_dict()
        base_dict['errors'] = [error.to_dict() for error in self.errors]
        return base_dict
    
    @classmethod
    def create_validation_response(cls,
                                 errors: List[ValidationError],
                                 message: str = "数据验证失败") -> 'ValidationErrorResponse':
        """创建验证错误响应
        
        Args:
            errors: 验证错误列表
            message: 错误消息
            
        Returns:
            ValidationErrorResponse: 验证错误响应实例
        """
        return cls(
            success=False,
            message=message,
            code="VALIDATION_ERROR",
            data=None,
            errors=errors
        )


@dataclass
class HealthCheckResponse(ApiResponse[Dict[str, Any]]):
    """健康检查响应类
    
    专门用于健康检查的响应，包含系统状态信息。
    """
    
    status: str = "healthy"
    version: str = "1.0.0"
    uptime: float = 0.0
    services: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 健康检查响应的字典表示
        """
        base_dict = super().to_dict()
        base_dict.update({
            'status': self.status,
            'version': self.version,
            'uptime': self.uptime,
            'services': self.services
        })
        return base_dict
    
    @classmethod
    def create_health_response(cls,
                             status: str = "healthy",
                             version: str = "1.0.0",
                             uptime: float = 0.0,
                             services: Optional[Dict[str, str]] = None) -> 'HealthCheckResponse':
        """创建健康检查响应
        
        Args:
            status: 系统状态
            version: 版本号
            uptime: 运行时间（秒）
            services: 服务状态字典
            
        Returns:
            HealthCheckResponse: 健康检查响应实例
        """
        return cls(
            success=True,
            message="系统运行正常",
            data={"system_info": "SuperRPG API"},
            code="HEALTH_OK",
            status=status,
            version=version,
            uptime=uptime,
            services=services or {}
        )


# 响应构建器工具类
class ResponseBuilder:
    """响应构建器
    
    提供便捷的响应构建方法，遵循单一职责原则。
    """
    
    @staticmethod
    def success(data: Optional[Any] = None, message: str = "操作成功", **metadata) -> ApiResponse:
        """构建成功响应
        
        Args:
            data: 响应数据
            message: 响应消息
            **metadata: 额外的元数据
            
        Returns:
            ApiResponse: 成功响应实例
        """
        return ApiResponse.success_response(data=data, message=message, **metadata)
    
    @staticmethod
    def error(message: str, code: str = "ERROR", **metadata) -> ApiResponse:
        """构建错误响应
        
        Args:
            message: 错误消息
            code: 错误代码
            **metadata: 额外的元数据
            
        Returns:
            ApiResponse: 错误响应实例
        """
        return ApiResponse.error_response(message=message, code=code, **metadata)
    
    @staticmethod
    def paged(items: List[Any], 
              page: int, 
              page_size: int, 
              total: int,
              message: str = "查询成功", 
              **metadata) -> PagedResponse:
        """构建分页响应
        
        Args:
            items: 数据项列表
            page: 当前页码
            page_size: 每页大小
            total: 总记录数
            message: 响应消息
            **metadata: 额外的元数据
            
        Returns:
            PagedResponse: 分页响应实例
        """
        return PagedResponse.create_paged_response(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            message=message,
            **metadata
        )
    
    @staticmethod
    def validation(errors: List[ValidationError], 
                   message: str = "数据验证失败") -> ValidationErrorResponse:
        """构建验证错误响应
        
        Args:
            errors: 验证错误列表
            message: 错误消息
            
        Returns:
            ValidationErrorResponse: 验证错误响应实例
        """
        return ValidationErrorResponse.create_validation_response(
            errors=errors,
            message=message
        )
    
    @staticmethod
    def health(status: str = "healthy",
               version: str = "1.0.0",
               uptime: float = 0.0,
               services: Optional[Dict[str, str]] = None) -> HealthCheckResponse:
        """构建健康检查响应
        
        Args:
            status: 系统状态
            version: 版本号
            uptime: 运行时间（秒）
            services: 服务状态字典
            
        Returns:
            HealthCheckResponse: 健康检查响应实例
        """
        return HealthCheckResponse.create_health_response(
            status=status,
            version=version,
            uptime=uptime,
            services=services
        )