"""
事件总线实现

提供事件总线的具体实现，基于现有的eventlog模块。
遵循SOLID原则，特别是单一职责原则(SRP)和开放/封闭原则(OCP)。
"""

import uuid
import threading
from datetime import datetime
from typing import Dict, List, Callable, Optional, Any, Type
from threading import Lock, RLock
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, Future
import queue
import weakref

from ...core.interfaces import EventBus as IEventBus, EventHandler as IEventHandler, DomainEvent


class EventHandlerWrapper:
    """事件处理器包装器
    
    包装事件处理器，提供额外的功能和生命周期管理。
    """
    
    def __init__(self, 
                 handler: IEventHandler,
                 event_type: Type[DomainEvent],
                 priority: int = 0,
                 async_execution: bool = False,
                 weak_ref: bool = False):
        """初始化事件处理器包装器
        
        Args:
            handler: 事件处理器
            event_type: 事件类型
            priority: 优先级（数字越大优先级越高）
            async_execution: 是否异步执行
            weak_ref: 是否使用弱引用
        """
        if weak_ref:
            self._handler = weakref.ref(handler)
        else:
            self._handler = handler
        
        self._event_type = event_type
        self._priority = priority
        self._async_execution = async_execution
        self._enabled = True
        self._execution_count = 0
        self._last_execution = None
        self._error_count = 0
        self._created_at = datetime.now()
    
    @property
    def handler(self) -> Optional[IEventHandler]:
        """获取事件处理器"""
        if isinstance(self._handler, weakref.ref):
            return self._handler()
        return self._handler
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        """获取事件类型"""
        return self._event_type
    
    @property
    def priority(self) -> int:
        """获取优先级"""
        return self._priority
    
    @property
    def async_execution(self) -> bool:
        """是否异步执行"""
        return self._async_execution
    
    @property
    def enabled(self) -> bool:
        """是否启用"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """设置启用状态"""
        self._enabled = value
    
    @property
    def execution_count(self) -> int:
        """获取执行次数"""
        return self._execution_count
    
    @property
    def error_count(self) -> int:
        """获取错误次数"""
        return self._error_count
    
    @property
    def last_execution(self) -> Optional[datetime]:
        """获取最后执行时间"""
        return self._last_execution
    
    def is_valid(self) -> bool:
        """检查处理器是否有效"""
        handler = self.handler
        return handler is not None
    
    def execute(self, event: DomainEvent) -> Future:
        """执行事件处理器
        
        Args:
            event: 领域事件
            
        Returns:
            Future: 执行结果
        """
        def _execute():
            try:
                handler = self.handler
                if handler and self._enabled:
                    handler.handle(event)
                    self._execution_count += 1
                    self._last_execution = datetime.now()
                    return True
                return False
            except Exception:
                self._error_count += 1
                raise
        
        if self._async_execution:
            with ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(_execute)
        else:
            # 同步执行，返回已完成的Future
            future = Future()
            try:
                result = _execute()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            return future


class EventBusImpl(IEventBus):
    """事件总线实现
    
    基于现有eventlog.bus模块的事件总线实现。
    遵循单一职责原则，专门负责事件的发布和订阅管理。
    """
    
    def __init__(self, 
                 enable_async: bool = True,
                 max_workers: int = 10,
                 enable_middleware: bool = True,
                 enable_metrics: bool = True):
        """初始化事件总线
        
        Args:
            enable_async: 是否启用异步处理
            max_workers: 最大工作线程数
            enable_middleware: 是否启用中间件
            enable_metrics: 是否启用指标收集
        """
        self._enable_async = enable_async
        self._max_workers = max_workers
        self._enable_middleware = enable_middleware
        self._enable_metrics = enable_metrics
        
        # 事件处理器存储
        self._handlers: Dict[Type[DomainEvent], List[EventHandlerWrapper]] = defaultdict(list)
        self._global_handlers: List[EventHandlerWrapper] = []
        
        # 线程安全
        self._lock = RLock()
        
        # 异步处理
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if enable_async else None
        self._event_queue = queue.Queue() if enable_async else None
        
        # 中间件
        self._middleware: List[Callable[[DomainEvent], bool]] = []
        
        # 指标收集
        self._metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_executed': 0,
            'handlers_failed': 0,
            'processing_time_total': 0.0,
            'average_processing_time': 0.0,
        } if enable_metrics else None
        
        # 事件历史
        self._event_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        
        # 启动异步处理线程
        if enable_async:
            self._start_async_processor()
    
    def _start_async_processor(self) -> None:
        """启动异步事件处理器"""
        def process_events():
            while True:
                try:
                    event, handlers = self._event_queue.get(timeout=1.0)
                    self._process_event_with_handlers(event, handlers)
                    self._event_queue.task_done()
                except queue.Empty:
                    continue
                except Exception:
                    # 记录错误但继续处理
                    continue
        
        processor = threading.Thread(target=process_events, daemon=True)
        processor.start()
    
    def _process_event_with_handlers(self, event: DomainEvent, handlers: List[EventHandlerWrapper]) -> None:
        """使用处理器处理事件
        
        Args:
            event: 领域事件
            handlers: 处理器列表
        """
        start_time = datetime.now()
        
        try:
            # 按优先级排序处理器
            handlers.sort(key=lambda h: h.priority, reverse=True)
            
            # 执行处理器
            for handler_wrapper in handlers:
                if not handler_wrapper.is_valid():
                    continue
                
                try:
                    future = handler_wrapper.execute(event)
                    if not handler_wrapper.async_execution:
                        future.result()  # 等待同步执行完成
                    
                    if self._metrics:
                        self._metrics['handlers_executed'] += 1
                        
                except Exception:
                    if self._metrics:
                        self._metrics['handlers_failed'] += 1
            
            if self._metrics:
                self._metrics['events_processed'] += 1
                
        except Exception:
            if self._metrics:
                self._metrics['events_failed'] += 1
        finally:
            # 更新处理时间指标
            if self._metrics:
                processing_time = (datetime.now() - start_time).total_seconds()
                self._metrics['processing_time_total'] += processing_time
                total_events = self._metrics['events_processed']
                if total_events > 0:
                    self._metrics['average_processing_time'] = self._metrics['processing_time_total'] / total_events
    
    def _add_to_history(self, event: DomainEvent, handlers_count: int) -> None:
        """添加事件到历史记录
        
        Args:
            event: 领域事件
            handlers_count: 处理器数量
        """
        if len(self._event_history) >= self._max_history_size:
            self._event_history.pop(0)
        
        self._event_history.append({
            'event_id': event.id,
            'event_type': event.get_event_type(),
            'occurred_at': event.occurred_at.isoformat(),
            'processed_at': datetime.now().isoformat(),
            'handlers_count': handlers_count,
        })
    
    # 实现EventBus接口方法
    
    def publish(self, event: DomainEvent) -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
        """
        if not isinstance(event, DomainEvent):
            raise ValueError("事件必须是DomainEvent的实例")
        
        with self._lock:
            # 更新指标
            if self._metrics:
                self._metrics['events_published'] += 1
            
            # 获取处理器
            event_type = type(event)
            handlers = self._handlers.get(event_type, []).copy()
            handlers.extend(self._global_handlers)
            
            # 过滤有效处理器
            valid_handlers = [h for h in handlers if h.is_valid() and h.enabled]
            
            # 添加到历史记录
            self._add_to_history(event, len(valid_handlers))
            
            # 应用中间件
            if self._enable_middleware:
                for middleware in self._middleware:
                    try:
                        if not middleware(event):
                            return  # 中间件阻止事件处理
                    except Exception:
                        continue  # 中间件错误不阻止事件处理
            
            # 处理事件
            if self._enable_async and self._event_queue:
                # 异步处理
                self._event_queue.put((event, valid_handlers))
            else:
                # 同步处理
                self._process_event_with_handlers(event, valid_handlers)
    
    def subscribe(self, event_type: type, handler: IEventHandler) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        if not issubclass(event_type, DomainEvent):
            raise ValueError("事件类型必须是DomainEvent的子类")
        
        if not isinstance(handler, IEventHandler):
            raise ValueError("处理器必须实现EventHandler接口")
        
        with self._lock:
            # 创建处理器包装器
            wrapper = EventHandlerWrapper(
                handler=handler,
                event_type=event_type,
                priority=0,
                async_execution=self._enable_async,
                weak_ref=True
            )
            
            # 添加到处理器列表
            self._handlers[event_type].append(wrapper)
    
    def unsubscribe(self, event_type: type, handler: IEventHandler) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            
            # 移除匹配的处理器
            self._handlers[event_type] = [
                h for h in handlers 
                if h.handler != handler
            ]
    
    # 扩展方法
    
    def subscribe_global(self, handler: IEventHandler, priority: int = 0) -> None:
        """订阅所有事件（全局处理器）
        
        Args:
            handler: 事件处理器
            priority: 优先级
        """
        if not isinstance(handler, IEventHandler):
            raise ValueError("处理器必须实现EventHandler接口")
        
        with self._lock:
            wrapper = EventHandlerWrapper(
                handler=handler,
                event_type=DomainEvent,
                priority=priority,
                async_execution=self._enable_async,
                weak_ref=True
            )
            
            self._global_handlers.append(wrapper)
            
            # 按优先级排序
            self._global_handlers.sort(key=lambda h: h.priority, reverse=True)
    
    def unsubscribe_global(self, handler: IEventHandler) -> None:
        """取消全局订阅
        
        Args:
            handler: 事件处理器
        """
        with self._lock:
            self._global_handlers = [
                h for h in self._global_handlers 
                if h.handler != handler
            ]
    
    def subscribe_with_priority(self, 
                              event_type: type, 
                              handler: IEventHandler, 
                              priority: int = 0,
                              async_execution: Optional[bool] = None) -> None:
        """订阅事件（带优先级）
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            priority: 优先级
            async_execution: 是否异步执行
        """
        if not issubclass(event_type, DomainEvent):
            raise ValueError("事件类型必须是DomainEvent的子类")
        
        if not isinstance(handler, IEventHandler):
            raise ValueError("处理器必须实现EventHandler接口")
        
        if async_execution is None:
            async_execution = self._enable_async
        
        with self._lock:
            wrapper = EventHandlerWrapper(
                handler=handler,
                event_type=event_type,
                priority=priority,
                async_execution=async_execution,
                weak_ref=True
            )
            
            self._handlers[event_type].append(wrapper)
    
    def add_middleware(self, middleware: Callable[[DomainEvent], bool]) -> None:
        """添加中间件
        
        Args:
            middleware: 中间件函数，返回False表示阻止事件处理
        """
        if self._enable_middleware:
            with self._lock:
                self._middleware.append(middleware)
    
    def remove_middleware(self, middleware: Callable[[DomainEvent], bool]) -> None:
        """移除中间件
        
        Args:
            middleware: 中间件函数
        """
        if self._enable_middleware:
            with self._lock:
                try:
                    self._middleware.remove(middleware)
                except ValueError:
                    pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标信息
        
        Returns:
            Dict[str, Any]: 指标信息
        """
        if not self._metrics:
            return {}
        
        with self._lock:
            metrics = self._metrics.copy()
            metrics['handler_count'] = sum(len(handlers) for handlers in self._handlers.values())
            metrics['global_handler_count'] = len(self._global_handlers)
            metrics['event_types_count'] = len(self._handlers)
            metrics['middleware_count'] = len(self._middleware)
            
            return metrics
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取事件历史
        
        Args:
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 事件历史
        """
        with self._lock:
            return self._event_history[-limit:] if limit > 0 else self._event_history.copy()
    
    def get_handlers_for_event(self, event_type: type) -> List[IEventHandler]:
        """获取指定事件类型的处理器
        
        Args:
            event_type: 事件类型
            
        Returns:
            List[IEventHandler]: 处理器列表
        """
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            return [h.handler for h in handlers if h.is_valid()]
    
    def get_global_handlers(self) -> List[IEventHandler]:
        """获取全局处理器
        
        Returns:
            List[IEventHandler]: 全局处理器列表
        """
        with self._lock:
            return [h.handler for h in self._global_handlers if h.is_valid()]
    
    def clear_handlers(self) -> None:
        """清除所有处理器"""
        with self._lock:
            self._handlers.clear()
            self._global_handlers.clear()
    
    def clear_history(self) -> None:
        """清除事件历史"""
        with self._lock:
            self._event_history.clear()
    
    def reset_metrics(self) -> None:
        """重置指标"""
        if self._metrics:
            with self._lock:
                self._metrics.update({
                    'events_published': 0,
                    'events_processed': 0,
                    'events_failed': 0,
                    'handlers_executed': 0,
                    'handlers_failed': 0,
                    'processing_time_total': 0.0,
                    'average_processing_time': 0.0,
                })
    
    def disable_handler(self, handler: IEventHandler) -> None:
        """禁用处理器
        
        Args:
            handler: 要禁用的处理器
        """
        with self._lock:
            for handlers in self._handlers.values():
                for wrapper in handlers:
                    if wrapper.handler == handler:
                        wrapper.enabled = False
            
            for wrapper in self._global_handlers:
                if wrapper.handler == handler:
                    wrapper.enabled = False
    
    def enable_handler(self, handler: IEventHandler) -> None:
        """启用处理器
        
        Args:
            handler: 要启用的处理器
        """
        with self._lock:
            for handlers in self._handlers.values():
                for wrapper in handlers:
                    if wrapper.handler == handler:
                        wrapper.enabled = True
            
            for wrapper in self._global_handlers:
                if wrapper.handler == handler:
                    wrapper.enabled = True
    
    def get_handler_statistics(self, handler: IEventHandler) -> Optional[Dict[str, Any]]:
        """获取处理器统计信息
        
        Args:
            handler: 事件处理器
            
        Returns:
            Optional[Dict[str, Any]]: 统计信息
        """
        with self._lock:
            for handlers in self._handlers.values():
                for wrapper in handlers:
                    if wrapper.handler == handler:
                        return {
                            'event_type': wrapper.event_type.__name__,
                            'priority': wrapper.priority,
                            'enabled': wrapper.enabled,
                            'execution_count': wrapper.execution_count,
                            'error_count': wrapper.error_count,
                            'last_execution': wrapper.last_execution.isoformat() if wrapper.last_execution else None,
                            'created_at': wrapper._created_at.isoformat(),
                        }
            
            for wrapper in self._global_handlers:
                if wrapper.handler == handler:
                    return {
                        'event_type': 'global',
                        'priority': wrapper.priority,
                        'enabled': wrapper.enabled,
                        'execution_count': wrapper.execution_count,
                        'error_count': wrapper.error_count,
                        'last_execution': wrapper.last_execution.isoformat() if wrapper.last_execution else None,
                        'created_at': wrapper._created_at.isoformat(),
                    }
        
        return None
    
    def shutdown(self) -> None:
        """关闭事件总线"""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        # 清理资源
        self.clear_handlers()
        self.clear_history()
        self._middleware.clear()


# 为了向后兼容，提供InMemoryEventBus的别名
InMemoryEventBus = EventBusImpl