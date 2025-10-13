"""
自定义异常模块

该模块定义了系统中使用的自定义异常类，遵循SOLID原则，
特别是单一职责原则(SRP)，每个异常类都有明确的职责。

异常层次结构：
- BaseException (系统根异常)
  - DomainException (领域异常)
    - ValidationException (验证异常)
    - BusinessRuleException (业务规则异常)
    - NotFoundException (未找到异常)
    - DuplicateException (重复异常)
  - InfrastructureException (基础设施异常)
    - RepositoryException (仓储异常)
    - ExternalServiceException (外部服务异常)
    - ConfigurationException (配置异常)
  - ApplicationException (应用异常)
    - ServiceUnavailableException (服务不可用异常)
    - PermissionDeniedException (权限拒绝异常)
    - OperationTimeoutException (操作超时异常)
"""

from typing import Optional, Dict, Any, List


class BaseException(Exception):
    """系统根异常
    
    所有自定义异常的基类，提供统一的异常处理接口。
    遵循单一职责原则，专门负责异常的基础功能。
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """初始化异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 异常详情
            cause: 原因异常
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        self.timestamp = None  # 将在具体异常中设置
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 异常信息的字典表示
        """
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'cause': str(self.cause) if self.cause else None
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        if self.error_code != self.__class__.__name__:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DomainException(BaseException):
    """领域异常
    
    所有领域相关异常的基类，用于封装业务逻辑中的异常情况。
    遵循单一职责原则，专门负责领域异常的处理。
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, 
                 entity_type: Optional[str] = None, 
                 entity_id: Optional[str] = None):
        """初始化领域异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 异常详情
            entity_type: 实体类型
            entity_id: 实体ID
        """
        super().__init__(message, error_code, details)
        self.entity_type = entity_type
        self.entity_id = entity_id
        
        # 添加实体信息到详情
        if entity_type:
            self.details['entity_type'] = entity_type
        if entity_id:
            self.details['entity_id'] = entity_id


class ValidationException(DomainException):
    """验证异常
    
    当数据验证失败时抛出此异常。
    遵循单一职责原则，专门负责验证失败的处理。
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 field_value: Optional[Any] = None, 
                 validation_errors: Optional[List[str]] = None):
        """初始化验证异常
        
        Args:
            message: 异常消息
            field_name: 字段名称
            field_value: 字段值
            validation_errors: 验证错误列表
        """
        details = {}
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = str(field_value)
        if validation_errors:
            details['validation_errors'] = validation_errors
        
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_errors = validation_errors or []


class BusinessRuleException(DomainException):
    """业务规则异常
    
    当违反业务规则时抛出此异常。
    遵循单一职责原则，专门负责业务规则违反的处理。
    """
    
    def __init__(self, message: str, rule_name: Optional[str] = None, 
                 rule_description: Optional[str] = None):
        """初始化业务规则异常
        
        Args:
            message: 异常消息
            rule_name: 规则名称
            rule_description: 规则描述
        """
        details = {}
        if rule_name:
            details['rule_name'] = rule_name
        if rule_description:
            details['rule_description'] = rule_description
        
        super().__init__(message, "BUSINESS_RULE_VIOLATION", details)
        self.rule_name = rule_name
        self.rule_description = rule_description


class NotFoundException(DomainException):
    """未找到异常
    
    当请求的资源不存在时抛出此异常。
    遵循单一职责原则，专门负责资源未找到的处理。
    """
    
    def __init__(self, message: str, resource_type: str, resource_id: str):
        """初始化未找到异常
        
        Args:
            message: 异常消息
            resource_type: 资源类型
            resource_id: 资源ID
        """
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        
        super().__init__(message, "RESOURCE_NOT_FOUND", details, 
                        entity_type=resource_type, entity_id=resource_id)
        self.resource_type = resource_type
        self.resource_id = resource_id


class DuplicateException(DomainException):
    """重复异常
    
    当尝试创建重复的资源时抛出此异常。
    遵循单一职责原则，专门负责资源重复的处理。
    """
    
    def __init__(self, message: str, resource_type: str, 
                 duplicate_key: str, duplicate_value: Any):
        """初始化重复异常
        
        Args:
            message: 异常消息
            resource_type: 资源类型
            duplicate_key: 重复字段
            duplicate_value: 重复值
        """
        details = {
            'resource_type': resource_type,
            'duplicate_key': duplicate_key,
            'duplicate_value': str(duplicate_value)
        }
        
        super().__init__(message, "DUPLICATE_RESOURCE", details, 
                        entity_type=resource_type)
        self.resource_type = resource_type
        self.duplicate_key = duplicate_key
        self.duplicate_value = duplicate_value


class InfrastructureException(BaseException):
    """基础设施异常
    
    所有基础设施相关异常的基类。
    遵循单一职责原则，专门负责基础设施异常的处理。
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, 
                 component: Optional[str] = None):
        """初始化基础设施异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 异常详情
            component: 组件名称
        """
        super().__init__(message, error_code, details)
        self.component = component
        
        if component:
            self.details['component'] = component


class RepositoryException(InfrastructureException):
    """仓储异常
    
    当仓储操作失败时抛出此异常。
    遵循单一职责原则，专门负责仓储操作异常的处理。
    """
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 entity_type: Optional[str] = None, 
                 entity_id: Optional[str] = None):
        """初始化仓储异常
        
        Args:
            message: 异常消息
            operation: 操作类型
            entity_type: 实体类型
            entity_id: 实体ID
        """
        details = {}
        if operation:
            details['operation'] = operation
        if entity_type:
            details['entity_type'] = entity_type
        if entity_id:
            details['entity_id'] = entity_id
        
        super().__init__(message, "REPOSITORY_ERROR", details, "Repository")
        self.operation = operation
        self.entity_type = entity_type
        self.entity_id = entity_id


class ExternalServiceException(InfrastructureException):
    """外部服务异常
    
    当外部服务调用失败时抛出此异常。
    遵循单一职责原则，专门负责外部服务异常的处理。
    """
    
    def __init__(self, message: str, service_name: str, 
                 status_code: Optional[int] = None, 
                 response_body: Optional[str] = None):
        """初始化外部服务异常
        
        Args:
            message: 异常消息
            service_name: 服务名称
            status_code: HTTP状态码
            response_body: 响应体
        """
        details = {
            'service_name': service_name
        }
        if status_code:
            details['status_code'] = status_code
        if response_body:
            details['response_body'] = response_body
        
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details, service_name)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body


class ConfigurationException(InfrastructureException):
    """配置异常
    
    当配置错误时抛出此异常。
    遵循单一职责原则，专门负责配置异常的处理。
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 config_value: Optional[Any] = None):
        """初始化配置异常
        
        Args:
            message: 异常消息
            config_key: 配置键
            config_value: 配置值
        """
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = str(config_value)
        
        super().__init__(message, "CONFIGURATION_ERROR", details, "Configuration")
        self.config_key = config_key
        self.config_value = config_value


class ApplicationException(BaseException):
    """应用异常
    
    所有应用层异常的基类。
    遵循单一职责原则，专门负责应用层异常的处理。
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None,
                 user_message: Optional[str] = None,
                 cause: Optional[Exception] = None):
        """初始化应用异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 异常详情
            user_message: 用户友好的消息
        """
        super().__init__(message, error_code, details, cause)
        self.user_message = user_message or message
        
        if user_message:
            self.details['user_message'] = user_message


class ServiceUnavailableException(ApplicationException):
    """服务不可用异常
    
    当服务不可用时抛出此异常。
    遵循单一职责原则，专门负责服务不可用异常的处理。
    """
    
    def __init__(self, message: str, service_name: str, 
                 retry_after: Optional[int] = None):
        """初始化服务不可用异常
        
        Args:
            message: 异常消息
            service_name: 服务名称
            retry_after: 重试间隔（秒）
        """
        details = {
            'service_name': service_name
        }
        if retry_after:
            details['retry_after'] = retry_after
        
        super().__init__(message, "SERVICE_UNAVAILABLE", details)
        self.service_name = service_name
        self.retry_after = retry_after


class PermissionDeniedException(ApplicationException):
    """权限拒绝异常
    
    当权限不足时抛出此异常。
    遵循单一职责原则，专门负责权限拒绝异常的处理。
    """
    
    def __init__(self, message: str, required_permission: Optional[str] = None, 
                 user_id: Optional[str] = None):
        """初始化权限拒绝异常
        
        Args:
            message: 异常消息
            required_permission: 所需权限
            user_id: 用户ID
        """
        details = {}
        if required_permission:
            details['required_permission'] = required_permission
        if user_id:
            details['user_id'] = user_id
        
        super().__init__(message, "PERMISSION_DENIED", details)
        self.required_permission = required_permission
        self.user_id = user_id


class OperationTimeoutException(ApplicationException):
    """操作超时异常
    
    当操作超时时抛出此异常。
    遵循单一职责原则，专门负责操作超时异常的处理。
    """
    
    def __init__(self, message: str, operation: str, timeout_seconds: int):
        """初始化操作超时异常
        
        Args:
            message: 异常消息
            operation: 操作名称
            timeout_seconds: 超时时间（秒）
        """
        details = {
            'operation': operation,
            'timeout_seconds': timeout_seconds
        }
        
        super().__init__(message, "OPERATION_TIMEOUT", details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


# 异常处理工具函数
def wrap_exception(exception: Exception, 
                   wrapper_class: type, 
                   message: Optional[str] = None,
                   **kwargs) -> BaseException:
    """包装异常
    
    将标准异常包装为自定义异常。
    
    Args:
        exception: 原始异常
        wrapper_class: 包装异常类
        message: 自定义消息
        **kwargs: 其他参数
        
    Returns:
        BaseException: 包装后的异常
    """
    if message is None:
        message = str(exception)
    
    return wrapper_class(message, cause=exception, **kwargs)


def is_exception_type(exception: Exception, exception_type: type) -> bool:
    """检查异常类型
    
    检查异常是否为指定类型或其子类型。
    
    Args:
        exception: 异常实例
        exception_type: 异常类型
        
    Returns:
        bool: 是否匹配
    """
    return isinstance(exception, exception_type)


def get_exception_chain(exception: Exception) -> List[Exception]:
    """获取异常链
    
    获取异常的所有原因异常链。
    
    Args:
        exception: 异常实例
        
    Returns:
        List[Exception]: 异常链
    """
    chain = []
    current = exception
    
    while current:
        chain.append(current)
        if hasattr(current, 'cause') and current.cause:
            current = current.cause
        elif hasattr(current, '__cause__') and current.__cause__:
            current = current.__cause__
        else:
            break
    
    return chain


# 为了向后兼容，提供ConfigurationError的别名
ConfigurationError = ConfigurationException