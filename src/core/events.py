
"""
事件系统基础模块

该模块实现了一个轻量级的事件系统，遵循SOLID原则，
特别是开放/封闭原则(OCP)和接口隔离原则(ISP)。

事件系统负责：
1. 事件的发布和订阅
2. 事件处理器的管理
3. 异步事件处理
4. 事件历史记录
"""

from typing import Dict, List, Callable, Any, Optional, Type, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
import weakref

from .interfaces import DomainEvent, EventHandler, EventBus


@dataclass
class EventMetadata:
    """事件元数据
    
    封装事件的元信息，如时间戳、来源等。
    遵循单一职责原则，专门负责事件元数据的管理。
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    version: str = "1.0"
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class EventEnvelope:
    """事件信封
    
    封装领域事件及其元数据，用于事件传输。
    遵循单一职责原则，专门负责事件的封装和传输。
    """
    event: DomainEvent
    metadata: EventMetadata = field(default_factory=EventMetadata)
    
    def get_event_type(self) -> str:
        """获取事件类型"""
        return self.event.get_event_type()
    
    def get_event_id(self) -> str:
        """获取事件ID"""
        return self.metadata.event_id


class EventSubscription:
    """事件订阅
    
    封装事件订阅的信息，包括事件类型、处理器等。
    """
    
    def __init__(self, event_type: Type[DomainEvent], handler: EventHandler, 
                 filter_func: Optional[Callable[[DomainEvent], bool]] = None):
        self.event_type = event_type
        self.handler = handler
        self.filter_func = filter_func
        self.subscription_id = str(uuid.uuid4())
        self.created_at = datetime.now()
    
    def matches(self, event: DomainEvent) -> bool:
        """检查事件是否匹配订阅"""
        if not isinstance(event, self.event_type):
            return False
        
        if self.filter_func:
            return self.filter_func(event)
        
        return True


class InMemoryEventBus(EventBus):
    """内存事件总线实现
    
    基于内存的事件总线实现，支持同步和异步事件处理。
    遵循单一职责原则，专门负责事件的发布和订阅管理。
    """
    
    def __init__(self, max_workers: int = 4, queue_size: int = 1000):
        """初始化事件总线
        
        Args:
            max_workers: 异步处理的最大工作线程数
            queue_size: 事件队列大小
        """
        self._subscriptions: Dict[Type[DomainEvent], List[EventSubscription]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._event_queue = Queue(maxsize=queue_size)
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._event_history: List[EventEnvelope] = []
        self._max_history_size = 1000
        
        # 弱引用处理器，避免内存泄漏
        self._weak_handlers: Dict[str, weakref.ref] = {}
    
    def publish(self, event: DomainEvent, metadata: Optional[EventMetadata] = None) -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
            metadata: 事件元数据，如果为None则自动创建
        """
        if metadata is None:
            metadata = EventMetadata()
        
        envelope = EventEnvelope(event=event, metadata=metadata)
        
        # 记录事件历史
        self._add_to_history(envelope)
        
        # 同步处理事件
        self._handle_event_sync(envelope)
        
        # 异步处理事件
        try:
            self._event_queue.put(envelope, block=False)
        except:
            # 队列满时，记录警告但不阻塞
            print(f"Event queue is full, dropping event {envelope.get_event_id()}")
    
    def subscribe(self, event_type: Type[DomainEvent], handler: EventHandler, 
                 filter_func: Optional[Callable[[DomainEvent], bool]] = None) -> str:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
            filter_func: 事件过滤函数
            
        Returns:
            str: 订阅ID
        """
        subscription = EventSubscription(event_type, handler, filter_func)
        
        with self._lock:
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            
            self._subscriptions[event_type].append(subscription)
            
            # 使用弱引用存储处理器
            self._weak_handlers[subscription.subscription_id] = weakref.ref(handler)
        
        return subscription.subscription_id
    
    def unsubscribe(self, event_type: Type[DomainEvent], handler: EventHandler) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            if event_type in self._subscriptions:
                # 找到并移除匹配的订阅
                subscriptions_to_remove = []
                for subscription in self._subscriptions[event_type]:
                    if subscription.handler == handler:
                        subscriptions_to_remove.append(subscription)
                        # 清理弱引用
                        if subscription.subscription_id in self._weak_handlers:
                            del self._weak_handlers[subscription.subscription_id]
                
                for subscription in subscriptions_to_remove:
                    self._subscriptions[event_type].remove(subscription)
                
                # 如果没有订阅了，删除事件类型
                if not self._subscriptions[event_type]:
                    del self._subscriptions[event_type]
    
    def unsubscribe_by_id(self, subscription_id: str) -> None:
        """根据订阅ID取消订阅
        
        Args:
            subscription_id: 订阅ID
        """
        with self._lock:
            for event_type, subscriptions in self._subscriptions.items():
                subscriptions_to_remove = []
                for subscription in subscriptions:
                    if subscription.subscription_id == subscription_id:
                        subscriptions_to_remove.append(subscription)
                        # 清理弱引用
                        if subscription_id in self._weak_handlers:
                            del self._weak_handlers[subscription_id]
                
                for subscription in subscriptions_to_remove:
                    subscriptions.remove(subscription)
                
                # 如果没有订阅了，删除事件类型
                if not subscriptions:
                    del self._subscriptions[event_type]
    
    def start_async_processing(self) -> None:
        """启动异步事件处理"""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events_async)
        self._worker_thread.daemon = True
        self._worker_thread.start()
    
    def stop_async_processing(self) -> None:
        """停止异步事件处理"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
            self._worker_thread = None
    
    def get_event_history(self, event_type: Optional[Type[DomainEvent]] = None, 
                         limit: Optional[int] = None) -> List[EventEnvelope]:
        """获取事件历史
        
        Args:
            event_type: 事件类型过滤器
            limit: 返回的最大事件数量
            
        Returns:
            List[EventEnvelope]: 事件历史列表
        """
        history = self._event_history
        
        if event_type:
            history = [env for env in history if isinstance(env.event, event_type)]
        
        if limit:
            history = history[-limit:]
        
        return history.copy()
    
    def clear_history(self) -> None:
        """清空事件历史"""
        self._event_history.clear()
    
    def get_subscription_count(self, event_type: Optional[Type[DomainEvent]] = None) -> int:
        """获取订阅数量
        
        Args:
            event_type: 事件类型，如果为None则返回总订阅数
            
        Returns:
            int: 订阅数量
        """
        with self._lock:
            if event_type:
                return len(self._subscriptions.get(event_type, []))
            else:
                return sum(len(subs) for subs in self._subscriptions.values())
    
    def _handle_event_sync(self, envelope: EventEnvelope) -> None:
        """同步处理事件"""
        event_type = type(envelope.event)
        
        with self._lock:
            subscriptions = self._subscriptions.get(event_type, []).copy()
        
        # 清理失效的弱引用
        valid_subscriptions = []
        for subscription in subscriptions:
            handler_ref = self._weak_handlers.get(subscription.subscription_id)
            if handler_ref and handler_ref() is not None:
                valid_subscriptions.append(subscription)
        
        # 处理事件
        for subscription in valid_subscriptions:
            if subscription.matches(envelope.event):
                try:
                    subscription.handler.handle(envelope.event)
                except Exception as e:
                    # 记录错误但不影响其他处理器
                    print(f"Error handling event {envelope.get_event_id()}: {e}")
    
    def _process_events_async(self) -> None:
        """异步处理事件"""
        while self._running:
            try:
                envelope = self._event_queue.get(timeout=1.0)
                self._handle_event_async(envelope)
                self._event_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"Error in async event processing: {e}")
    
    def _handle_event_async(self, envelope: EventEnvelope) -> None:
        """异步处理单个事件"""
        event_type = type(envelope.event)
        
        with self._lock:
            subscriptions = self._subscriptions.get(event_type, []).copy()
        
        # 清理失效的弱引用
        valid_subscriptions = []
        for subscription in subscriptions:
            handler_ref = self._weak_handlers.get(subscription.subscription_id)
            if handler_ref and handler_ref() is not None:
                valid_subscriptions.append(subscription)
        
        # 提交异步任务
        for subscription in valid_subscriptions:
            if subscription.matches(envelope.event):
                self._executor.submit(self._safe_handle, subscription.handler, envelope.event)
    
    def _safe_handle(self, handler: EventHandler, event: DomainEvent) -> None:
        """安全地处理事件"""
        try:
            handler.handle(event)
        except Exception as e:
            print(f"Error handling event asynchronously: {e}")
    
    def _add_to_history(self, envelope: EventEnvelope) -> None:
        """添加事件到历史记录"""
        self._event_history.append(envelope)
        
        # 限制历史记录大小
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
    
    def __del__(self):
        """析构函数"""
        self.stop_async_processing()


class EventStore(ABC):
    """事件存储接口
    
    遵循接口隔离原则，定义事件存储的核心操作。
    """
    
    @abstractmethod
    def save_event(self, envelope: EventEnvelope) -> None:
        """保存事件
        
        Args:
            envelope: 事件信封
        """
        pass
    
    @abstractmethod
    def get_events(self, event_type: Optional[Type[DomainEvent]] = None,
                   limit: Optional[int] = None) -> List[EventEnvelope]:
        """获取事件
        
        Args:
            event_type: 事件类型过滤器
            limit: 返回的最大事件数量
            
        Returns:
            List[EventEnvelope]: 事件列表
        """
        pass
    
    @abstractmethod
    def get_events_by_correlation_id(self, correlation_id: str) -> List[EventEnvelope]:
        """根据关联ID获取事件
        
        Args:
            correlation_id: 关联ID
            
        Returns:
            List[EventEnvelope]: 事件列表
        """
        pass


class InMemoryEventStore(EventStore):
    """内存事件存储实现
    
    基于内存的事件存储实现，用于开发和测试。
    """
    
    def __init__(self, max_size: int = 10000):
        """初始化事件存储
        
        Args:
            max_size: 最大存储事件数量
        """
        self._events: List[EventEnvelope] = []
        self._max_size = max_size
        self._lock = threading.RLock()
    
    def save_event(self, envelope: EventEnvelope) -> None:
        """保存事件"""
        with self._lock:
            self._events.append(envelope)
            
            # 限制存储大小
            if len(self._events) > self._max_size:
                self._events = self._events[-self._max_size:]
    
    def get_events(self, event_type: Optional[Type[DomainEvent]] = None,
                   limit: Optional[int] = None) -> List[EventEnvelope]:
        """获取事件"""
        with self._lock:
            events = self._events.copy()
        
        if event_type:
            events = [env for env in events if isinstance(env.event, event_type)]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_events_by_correlation_id(self, correlation_id: str) -> List[EventEnvelope]:
        """根据关联ID获取事件"""
        with self._lock:
            events = self._events.copy()
        
        return [env for env in events
                if env.metadata.correlation_id == correlation_id]
    
    def clear(self) -> None:
        """清空所有事件"""
        with self._lock:
            self._events.clear()
    
    def count(self) -> int:
        """获取事件总数"""
        with self._lock:
            return len(self._events)
