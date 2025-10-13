"""
应用服务基类模块

该模块定义了应用服务的基础类，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

应用服务基类负责：
1. 提供应用服务的通用功能
2. 处理事务和异常
3. 协调领域对象和基础设施
4. 实现横切关注点
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from contextlib import contextmanager

import asyncio

from ...core.interfaces import DomainEvent, EventBus, Logger
from ...core.exceptions import (
    BaseException,
    ApplicationException,
    ValidationException,
    BusinessRuleException
)


T = TypeVar('T')
R = TypeVar('R')


@dataclass
class CommandResult:
    """命令结果
    
    封装命令执行的结果，包括成功状态、数据和错误信息。
    遵循单一职责原则，专门负责命令结果的封装。
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[BaseException] = None
    message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    
    @classmethod
    def success_result(cls, data: Any = None, message: str = None) -> 'CommandResult':
        """创建成功结果
        
        Args:
            data: 结果数据
            message: 成功消息
            
        Returns:
            CommandResult: 成功结果
        """
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def failure_result(cls, error: BaseException, message: str = None) -> 'CommandResult':
        """创建失败结果
        
        Args:
            error: 错误异常
            message: 错误消息
            
        Returns:
            CommandResult: 失败结果
        """
        return cls(success=False, error=error, message=message or str(error))


@dataclass
class QueryResult(Generic[T]):
    """查询结果
    
    封装查询执行的结果，包括数据列表和分页信息。
    遵循单一职责原则，专门负责查询结果的封装。
    """
    data: List[T]
    total_count: int
    page_number: int
    page_size: int
    has_next_page: bool
    has_previous_page: bool
    
    @classmethod
    def create(cls, data: List[T], page_number: int = 1, page_size: int = 50, 
               total_count: Optional[int] = None) -> 'QueryResult[T]':
        """创建查询结果
        
        Args:
            data: 数据列表
            page_number: 页码
            page_size: 页大小
            total_count: 总数量
            
        Returns:
            QueryResult[T]: 查询结果
        """
        if total_count is None:
            total_count = len(data)
        
        total_pages = (total_count + page_size - 1) // page_size
        has_next_page = page_number < total_pages
        has_previous_page = page_number > 1
        
        return cls(
            data=data,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page
        )


class ApplicationService(ABC):
    """应用服务基类
    
    所有应用服务的抽象基类，提供通用的应用服务功能。
    遵循单一职责原则，专门负责应用服务的通用行为管理。
    """
    
    def __init__(self, event_bus: EventBus, logger: Logger):
        """初始化应用服务
        
        Args:
            event_bus: 事件总线
            logger: 日志记录器
        """
        self._event_bus = event_bus
        self._logger = logger
        self._current_user: Optional[str] = None
        self._correlation_id: Optional[str] = None
    
    def set_context(self, user: Optional[str] = None, 
                   correlation_id: Optional[str] = None) -> None:
        """设置执行上下文
        
        Args:
            user: 当前用户
            correlation_id: 关联ID
        """
        self._current_user = user
        self._correlation_id = correlation_id
    
    @contextmanager
    def transaction_scope(self):
        """事务作用域
        
        提供事务管理的上下文管理器。
        """
        start_time = datetime.now()
        try:
            # 开始事务
            self._begin_transaction()
            yield
            # 提交事务
            self._commit_transaction()
            
        except Exception as e:
            # 回滚事务
            self._rollback_transaction()
            raise
        finally:
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._logger.debug(f"Transaction completed in {execution_time:.2f}ms")
    
    def execute_command(self, command: Any) -> CommandResult:
        """执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            CommandResult: 命令执行结果
        """
        start_time = datetime.now()
        
        try:
            self._logger.info(f"Executing command: {command.__class__.__name__}")
            
            # 验证命令
            self._validate_command(command)
            
            # 执行命令
            result_data = self._execute_command_internal(command)
            
            # 计算执行时间
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            self._logger.info(f"Command executed successfully in {execution_time}ms")
            
            return CommandResult.success_result(
                data=result_data,
                message=f"Command {command.__class__.__name__} executed successfully"
            )
            
        except ValidationException as e:
            self._logger.warning(f"Command validation failed: {e}")
            return CommandResult.failure_result(e, f"Validation failed: {e.message}")
            
        except BusinessRuleException as e:
            self._logger.warning(f"Business rule violation: {e}")
            return CommandResult.failure_result(e, f"Business rule violation: {e.message}")
            
        except ApplicationException as e:
            self._logger.error(f"Application error: {e}")
            return CommandResult.failure_result(e, e.user_message)
            
        except Exception as e:
            self._logger.error(f"Unexpected error: {e}")
            wrapped_error = ApplicationException(
                f"Unexpected error executing command: {str(e)}",
                cause=e
            )
            return CommandResult.failure_result(wrapped_error, "An unexpected error occurred")
    
    def execute_query(self, query: Any) -> QueryResult:
        """执行查询
        
        Args:
            query: 要执行的查询
            
        Returns:
            QueryResult: 查询结果
        """
        start_time = datetime.now()
        
        try:
            self._logger.info(f"Executing query: {query.__class__.__name__}")
            
            # 验证查询
            self._validate_query(query)
            
            # 执行查询
            result = self._execute_query_internal(query)
            
            # 计算执行时间
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            self._logger.info(f"Query executed successfully in {execution_time}ms")
            
            return result
            
        except ValidationException as e:
            self._logger.warning(f"Query validation failed: {e}")
            raise
            
        except Exception as e:
            self._logger.error(f"Query execution failed: {e}")
            raise ApplicationException(
                f"Query execution failed: {str(e)}",
                cause=e
            )
    
    def publish_event(self, event: DomainEvent) -> None:
        """发布领域事件
        
        Args:
            event: 要发布的事件
        """
        result = self._event_bus.publish(event)
        if asyncio.iscoroutine(result):
            asyncio.create_task(result)
        self._logger.debug(f"Published event: {event.get_event_type()}")
    
    @abstractmethod
    def _execute_command_internal(self, command: Any) -> Any:
        """内部命令执行方法
        
        Args:
            command: 要执行的命令
            
        Returns:
            Any: 命令执行结果
        """
        pass
    
    @abstractmethod
    def _execute_query_internal(self, query: Any) -> QueryResult:
        """内部查询执行方法
        
        Args:
            query: 要执行的查询
            
        Returns:
            QueryResult: 查询结果
        """
        pass
    
    def _validate_command(self, command: Any) -> None:
        """验证命令
        
        Args:
            command: 要验证的命令
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 基础验证逻辑，子类可以重写
        if command is None:
            raise ValidationException("Command cannot be null")
    
    def _validate_query(self, query: Any) -> None:
        """验证查询
        
        Args:
            query: 要验证的查询
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 基础验证逻辑，子类可以重写
        if query is None:
            raise ValidationException("Query cannot be null")
    
    def _begin_transaction(self) -> None:
        """开始事务
        
        子类可以重写以实现具体的事务逻辑。
        """
        pass
    
    def _commit_transaction(self) -> None:
        """提交事务
        
        子类可以重写以实现具体的事务逻辑。
        """
        pass
    
    def _rollback_transaction(self) -> None:
        """回滚事务
        
        子类可以重写以实现具体的事务逻辑。
        """
        pass
    
    def _check_permission(self, permission: str) -> None:
        """检查权限
        
        Args:
            permission: 所需权限
            
        Raises:
            ApplicationException: 权限不足时抛出
        """
        # 基础权限检查逻辑，子类可以重写
        if not self._current_user:
            raise ApplicationException(
                "Authentication required",
                error_code="AUTHENTICATION_REQUIRED"
            )
        
        # 这里可以实现具体的权限检查逻辑
        # 例如：检查用户是否具有指定权限
    
    def _log_operation(self, operation: str, details: Dict[str, Any] = None) -> None:
        """记录操作日志
        
        Args:
            operation: 操作名称
            details: 操作详情
        """
        log_data = {
            'operation': operation,
            'user': self._current_user,
            'correlation_id': self._correlation_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if details:
            log_data.update(details)
        
        self._logger.info(f"Operation: {operation}", **log_data)


class CommandHandler(Generic[T, R], ABC):
    """命令处理器基类
    
    专门处理特定类型命令的处理器。
    遵循单一职责原则，每个命令处理器只负责一种命令类型。
    """
    
    @abstractmethod
    def handle(self, command: T) -> R:
        """处理命令
        
        Args:
            command: 要处理的命令
            
        Returns:
            R: 处理结果
        """
        pass
    
    @abstractmethod
    def can_handle(self, command_type: type) -> bool:
        """检查是否能处理指定类型的命令
        
        Args:
            command_type: 命令类型
            
        Returns:
            bool: 是否能处理
        """
        pass


class QueryHandler(Generic[T, R], ABC):
    """查询处理器基类
    
    专门处理特定类型查询的处理器。
    遵循单一职责原则，每个查询处理器只负责一种查询类型。
    """
    
    @abstractmethod
    def handle(self, query: T) -> R:
        """处理查询
        
        Args:
            query: 要处理的查询
            
        Returns:
            R: 查询结果
        """
        pass
    
    @abstractmethod
    def can_handle(self, query_type: type) -> bool:
        """检查是否能处理指定类型的查询
        
        Args:
            query_type: 查询类型
            
        Returns:
            bool: 是否能处理
        """
        pass


class ServiceRegistry:
    """服务注册表
    
    管理命令和查询处理器的注册。
    遵循单一职责原则，专门负责服务注册的管理。
    """
    
    def __init__(self):
        """初始化服务注册表"""
        self._command_handlers: Dict[type, CommandHandler] = {}
        self._query_handlers: Dict[type, QueryHandler] = {}
    
    def register_command_handler(self, command_type: type, handler: CommandHandler) -> None:
        """注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 命令处理器
        """
        self._command_handlers[command_type] = handler
    
    def register_query_handler(self, query_type: type, handler: QueryHandler) -> None:
        """注册查询处理器
        
        Args:
            query_type: 查询类型
            handler: 查询处理器
        """
        self._query_handlers[query_type] = handler
    
    def get_command_handler(self, command_type: type) -> Optional[CommandHandler]:
        """获取命令处理器
        
        Args:
            command_type: 命令类型
            
        Returns:
            Optional[CommandHandler]: 命令处理器，如果未找到则返回None
        """
        return self._command_handlers.get(command_type)
    
    def get_query_handler(self, query_type: type) -> Optional[QueryHandler]:
        """获取查询处理器
        
        Args:
            query_type: 查询类型
            
        Returns:
            Optional[QueryHandler]: 查询处理器，如果未找到则返回None
        """
        return self._query_handlers.get(query_type)
    
    def clear(self) -> None:
        """清空所有注册"""
        self._command_handlers.clear()
        self._query_handlers.clear()
