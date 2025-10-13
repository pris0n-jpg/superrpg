"""
增强事件总线模块

该模块实现增强的事件总线，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责事件的发布、订阅、持久化和重放。
"""

import asyncio
import json
import uuid
import time
import threading
from typing import Dict, List, Callable, Optional, Any, Type, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
from enum import Enum
import pickle
import sqlite3
import os
from pathlib import Path

from ...core.interfaces import EventBus as IEventBus, EventHandler as IEventHandler, DomainEvent


class EventPriority(Enum):
    """事件优先级枚举
    
    定义事件的优先级级别。
    """
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(Enum):
    """事件状态枚举
    
    定义事件的处理状态。
    """
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class EventMetadata:
    """事件元数据
    
    封装事件的元数据信息，遵循单一职责原则。
    """
    
    event_id: str
    event_type: str
    source: str
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 元数据的字典表示
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "tags": self.tags,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        """从字典创建元数据
        
        Args:
            data: 字典数据
            
        Returns:
            EventMetadata: 元数据实例
        """
        timestamp = datetime.fromisoformat(data["timestamp"])
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])
        
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            source=data["source"],
            priority=EventPriority(data["priority"]),
            timestamp=timestamp,
            expires_at=expires_at,
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            tags=data["tags"],
            correlation_id=data["correlation_id"],
            causation_id=data["causation_id"]
        )


@dataclass
class StoredEvent:
    """存储的事件
    
    封装持久化存储的事件信息，遵循单一职责原则。
    """
    
    metadata: EventMetadata
    event_data: Dict[str, Any]
    status: EventStatus = EventStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 存储事件的字典表示
        """
        return {
            "metadata": self.metadata.to_dict(),
            "event_data": self.event_data,
            "status": self.status.value,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoredEvent':
        """从字典创建存储事件
        
        Args:
            data: 字典数据
            
        Returns:
            StoredEvent: 存储事件实例
        """
        metadata = EventMetadata.from_dict(data["metadata"])
        created_at = datetime.fromisoformat(data["created_at"])
        updated_at = datetime.fromisoformat(data["updated_at"])
        
        return cls(
            metadata=metadata,
            event_data=data["event_data"],
            status=EventStatus(data["status"]),
            error_message=data["error_message"],
            created_at=created_at,
            updated_at=updated_at
        )


class EventFilter:
    """事件过滤器
    
    提供事件过滤功能，遵循单一职责原则。
    """
    
    def __init__(self):
        """初始化事件过滤器"""
        self.event_types: Set[str] = set()
        self.sources: Set[str] = set()
        self.tags: Set[str] = set()
        self.priority_range: Optional[tuple] = None
        self.time_range: Optional[tuple] = None
        self.custom_filters: List[Callable[[StoredEvent], bool]] = []
    
    def add_event_type(self, event_type: str) -> 'EventFilter':
        """添加事件类型过滤
        
        Args:
            event_type: 事件类型
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.event_types.add(event_type)
        return self
    
    def add_source(self, source: str) -> 'EventFilter':
        """添加事件源过滤
        
        Args:
            source: 事件源
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.sources.add(source)
        return self
    
    def add_tag(self, tag: str) -> 'EventFilter':
        """添加标签过滤
        
        Args:
            tag: 标签
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.tags.add(tag)
        return self
    
    def set_priority_range(self, min_priority: EventPriority, max_priority: EventPriority) -> 'EventFilter':
        """设置优先级范围过滤
        
        Args:
            min_priority: 最小优先级
            max_priority: 最大优先级
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.priority_range = (min_priority.value, max_priority.value)
        return self
    
    def set_time_range(self, start_time: datetime, end_time: datetime) -> 'EventFilter':
        """设置时间范围过滤
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.time_range = (start_time, end_time)
        return self
    
    def add_custom_filter(self, filter_func: Callable[[StoredEvent], bool]) -> 'EventFilter':
        """添加自定义过滤器
        
        Args:
            filter_func: 过滤函数
            
        Returns:
            EventFilter: 返回自身以支持链式调用
        """
        self.custom_filters.append(filter_func)
        return self
    
    def matches(self, stored_event: StoredEvent) -> bool:
        """检查事件是否匹配过滤器
        
        Args:
            stored_event: 存储的事件
            
        Returns:
            bool: 是否匹配
        """
        metadata = stored_event.metadata
        
        # 事件类型过滤
        if self.event_types and metadata.event_type not in self.event_types:
            return False
        
        # 事件源过滤
        if self.sources and metadata.source not in self.sources:
            return False
        
        # 标签过滤
        if self.tags and not any(tag in metadata.tags for tag in self.tags):
            return False
        
        # 优先级过滤
        if self.priority_range:
            min_p, max_p = self.priority_range
            if not (min_p <= metadata.priority.value <= max_p):
                return False
        
        # 时间过滤
        if self.time_range:
            start_time, end_time = self.time_range
            if not (start_time <= metadata.timestamp <= end_time):
                return False
        
        # 自定义过滤
        for filter_func in self.custom_filters:
            if not filter_func(stored_event):
                return False
        
        return True


class EventPersistence:
    """事件持久化
    
    负责事件的持久化存储和查询，遵循单一职责原则。
    """
    
    def __init__(self, db_path: str = "events.db"):
        """初始化事件持久化
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        # 确保数据库目录存在（如果有目录路径的话）
        dir_path = os.path.dirname(self.db_path)
        if dir_path:  # 只有当路径包含目录时才创建
            os.makedirs(dir_path, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    metadata TEXT NOT NULL,
                    event_data TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type ON events (
                    json_extract(metadata, '$.event_type')
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_source ON events (
                    json_extract(metadata, '$.source')
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_status ON events (status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at)
            """)
    
    async def save_event(self, stored_event: StoredEvent) -> bool:
        """保存事件
        
        Args:
            stored_event: 存储的事件
            
        Returns:
            bool: 是否成功保存
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO events 
                        (event_id, metadata, event_data, status, error_message, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        stored_event.metadata.event_id,
                        json.dumps(stored_event.metadata.to_dict()),
                        json.dumps(stored_event.event_data),
                        stored_event.status.value,
                        stored_event.error_message,
                        stored_event.created_at.isoformat(),
                        stored_event.updated_at.isoformat()
                    ))
            
            return True
        except Exception:
            return False
    
    async def get_event(self, event_id: str) -> Optional[StoredEvent]:
        """获取事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            Optional[StoredEvent]: 存储的事件
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT metadata, event_data, status, error_message, created_at, updated_at
                        FROM events WHERE event_id = ?
                    """, (event_id,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    metadata = EventMetadata.from_dict(json.loads(row[0]))
                    event_data = json.loads(row[1])
                    status = EventStatus(row[2])
                    error_message = row[3]
                    created_at = datetime.fromisoformat(row[4])
                    updated_at = datetime.fromisoformat(row[5])
                    
                    return StoredEvent(
                        metadata=metadata,
                        event_data=event_data,
                        status=status,
                        error_message=error_message,
                        created_at=created_at,
                        updated_at=updated_at
                    )
        except Exception:
            return None
    
    async def query_events(self, 
                          event_filter: Optional[EventFilter] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[StoredEvent]:
        """查询事件
        
        Args:
            event_filter: 事件过滤器
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[StoredEvent]: 事件列表
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    # 构建查询
                    query = "SELECT metadata, event_data, status, error_message, created_at, updated_at FROM events"
                    params = []
                    
                    if event_filter:
                        conditions = []
                        
                        # 事件类型过滤
                        if event_filter.event_types:
                            placeholders = ','.join('?' for _ in event_filter.event_types)
                            conditions.append(f"json_extract(metadata, '$.event_type') IN ({placeholders})")
                            params.extend(event_filter.event_types)
                        
                        # 事件源过滤
                        if event_filter.sources:
                            placeholders = ','.join('?' for _ in event_filter.sources)
                            conditions.append(f"json_extract(metadata, '$.source') IN ({placeholders})")
                            params.extend(event_filter.sources)
                        
                        # 状态过滤
                        conditions.append("status = ?")
                        params.append(EventStatus.PROCESSED.value)
                        
                        if conditions:
                            query += " WHERE " + " AND ".join(conditions)
                    
                    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                    
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                    
                    events = []
                    for row in rows:
                        metadata = EventMetadata.from_dict(json.loads(row[0]))
                        event_data = json.loads(row[1])
                        status = EventStatus(row[2])
                        error_message = row[3]
                        created_at = datetime.fromisoformat(row[4])
                        updated_at = datetime.fromisoformat(row[5])
                        
                        stored_event = StoredEvent(
                            metadata=metadata,
                            event_data=event_data,
                            status=status,
                            error_message=error_message,
                            created_at=created_at,
                            updated_at=updated_at
                        )
                        
                        # 应用自定义过滤器
                        if not event_filter or event_filter.matches(stored_event):
                            events.append(stored_event)
                    
                    return events
        except Exception:
            return []
    
    async def update_event_status(self, 
                                 event_id: str, 
                                 status: EventStatus, 
                                 error_message: Optional[str] = None) -> bool:
        """更新事件状态
        
        Args:
            event_id: 事件ID
            status: 新状态
            error_message: 错误消息
            
        Returns:
            bool: 是否成功更新
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE events 
                        SET status = ?, error_message = ?, updated_at = ?
                        WHERE event_id = ?
                    """, (
                        status.value,
                        error_message,
                        datetime.now().isoformat(),
                        event_id
                    ))
            
            return True
        except Exception:
            return False
    
    async def delete_event(self, event_id: str) -> bool:
        """删除事件
        
        Args:
            event_id: 事件ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
            
            return True
        except Exception:
            return False
    
    async def cleanup_old_events(self, days: int = 30) -> int:
        """清理旧事件
        
        Args:
            days: 保留天数
            
        Returns:
            int: 删除的事件数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self._lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM events WHERE created_at < ?
                    """, (cutoff_date.isoformat(),))
                    
                    return cursor.rowcount
        except Exception:
            return 0


class EnhancedEventBus(IEventBus):
    """增强事件总线
    
    提供完整的事件处理功能，包括异步处理、优先级、过滤、持久化和重放。
    """
    
    def __init__(self, 
                 enable_persistence: bool = True,
                 db_path: str = "events.db",
                 max_workers: int = 10,
                 enable_metrics: bool = True,
                 event_retention_days: int = 30):
        """初始化增强事件总线
        
        Args:
            enable_persistence: 是否启用持久化
            db_path: 数据库路径
            max_workers: 最大工作线程数
            enable_metrics: 是否启用指标收集
            event_retention_days: 事件保留天数
        """
        self.enable_persistence = enable_persistence
        self.max_workers = max_workers
        self.enable_metrics = enable_metrics
        self.event_retention_days = event_retention_days
        
        # 事件处理器存储
        self._handlers: Dict[Type[DomainEvent], List[IEventHandler]] = defaultdict(list)
        self._global_handlers: List[IEventHandler] = []
        
        # 线程安全
        self._lock = threading.RLock()
        
        # 异步处理
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._event_queue = asyncio.Queue()
        self._processing = False
        
        # 持久化
        self._persistence = EventPersistence(db_path) if enable_persistence else None
        
        # 事件过滤
        self._global_filters: List[EventFilter] = []
        
        # 指标收集
        self._metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handlers_executed': 0,
            'handlers_failed': 0,
            'processing_time_total': 0.0,
            'average_processing_time': 0.0,
            'queue_size': 0,
            'persistence_errors': 0,
        } if enable_metrics else None
        
        # 事件历史（内存中）
        self._event_history: deque = deque(maxlen=1000)
        
        # 启动事件处理循环
        self._start_processing_loop()
    
    def _start_processing_loop(self) -> None:
        """启动事件处理循环"""
        def process_events():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while True:
                try:
                    event, stored_event = loop.run_until_complete(self._event_queue.get())
                    loop.run_until_complete(self._process_event_with_persistence(event, stored_event))
                except Exception as e:
                    if self._metrics:
                        self._metrics['events_failed'] += 1
                    print(f"事件处理错误: {e}")
        
        processor = threading.Thread(target=process_events, daemon=True)
        processor.start()
        self._processing = True
    
    async def publish(self, event: DomainEvent) -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
        """
        if not isinstance(event, DomainEvent):
            raise ValueError("事件必须是DomainEvent的实例")
        
        # 创建存储事件
        metadata = EventMetadata(
            event_id=str(uuid.uuid4()),
            event_type=event.get_event_type(),
            source="enhanced_event_bus"
        )
        
        # 序列化事件数据
        event_data = self._serialize_event(event)
        
        stored_event = StoredEvent(
            metadata=metadata,
            event_data=event_data
        )
        
        # 应用全局过滤器
        if not self._apply_global_filters(stored_event):
            return
        
        # 更新指标
        if self._metrics:
            self._metrics['events_published'] += 1
            self._metrics['queue_size'] = self._event_queue.qsize()
        
        # 添加到历史记录
        self._event_history.append(stored_event)
        
        # 持久化事件
        if self._persistence:
            success = await self._persistence.save_event(stored_event)
            if not success and self._metrics:
                self._metrics['persistence_errors'] += 1
        
        # 添加到处理队列
        await self._event_queue.put((event, stored_event))
    
    async def _process_event_with_persistence(self, event: DomainEvent, stored_event: StoredEvent) -> None:
        """处理事件（带持久化）
        
        Args:
            event: 领域事件
            stored_event: 存储的事件
        """
        start_time = time.time()
        
        try:
            # 更新事件状态为处理中
            if self._persistence:
                await self._persistence.update_event_status(
                    stored_event.metadata.event_id, 
                    EventStatus.PROCESSING
                )
            
            # 获取处理器
            event_type = type(event)
            handlers = self._handlers.get(event_type, []).copy()
            handlers.extend(self._global_handlers)
            
            # 按优先级排序处理器（如果支持）
            # 这里可以扩展为支持处理器优先级
            
            # 执行处理器
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler.handle):
                        await handler.handle(event)
                    else:
                        # 在线程池中执行同步处理器
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(self._executor, handler.handle, event)
                    
                    if self._metrics:
                        self._metrics['handlers_executed'] += 1
                        
                except Exception as e:
                    if self._metrics:
                        self._metrics['handlers_failed'] += 1
                    print(f"处理器执行错误: {e}")
            
            # 更新事件状态为已处理
            if self._persistence:
                await self._persistence.update_event_status(
                    stored_event.metadata.event_id, 
                    EventStatus.PROCESSED
                )
            
            if self._metrics:
                self._metrics['events_processed'] += 1
                
        except Exception as e:
            # 更新事件状态为失败
            if self._persistence:
                await self._persistence.update_event_status(
                    stored_event.metadata.event_id, 
                    EventStatus.FAILED,
                    str(e)
                )
            
            if self._metrics:
                self._metrics['events_failed'] += 1
            print(f"事件处理失败: {e}")
        
        finally:
            # 更新处理时间指标
            if self._metrics:
                processing_time = time.time() - start_time
                self._metrics['processing_time_total'] += processing_time
                total_events = self._metrics['events_processed']
                if total_events > 0:
                    self._metrics['average_processing_time'] = (
                        self._metrics['processing_time_total'] / total_events
                    )
    
    def _apply_global_filters(self, stored_event: StoredEvent) -> bool:
        """应用全局过滤器
        
        Args:
            stored_event: 存储的事件
            
        Returns:
            bool: 是否通过过滤
        """
        for event_filter in self._global_filters:
            if not event_filter.matches(stored_event):
                return False
        return True
    
    def _serialize_event(self, event: DomainEvent) -> Dict[str, Any]:
        """序列化事件
        
        Args:
            event: 领域事件
            
        Returns:
            Dict[str, Any]: 序列化后的事件数据
        """
        # 简单的序列化实现，实际中可能需要更复杂的序列化逻辑
        return {
            "event_type": event.get_event_type(),
            "event_id": event.id,
            "occurred_at": event.occurred_at.isoformat(),
            # 添加其他事件属性
        }
    
    async def subscribe(self, event_type: type, handler: IEventHandler) -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            self._handlers[event_type].append(handler)
    
    async def unsubscribe(self, event_type: type, handler: IEventHandler) -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass
    
    def add_global_filter(self, event_filter: EventFilter) -> None:
        """添加全局过滤器
        
        Args:
            event_filter: 事件过滤器
        """
        self._global_filters.append(event_filter)
    
    def remove_global_filter(self, event_filter: EventFilter) -> bool:
        """移除全局过滤器
        
        Args:
            event_filter: 事件过滤器
            
        Returns:
            bool: 是否成功移除
        """
        try:
            self._global_filters.remove(event_filter)
            return True
        except ValueError:
            return False
    
    async def replay_events(self, 
                           event_filter: Optional[EventFilter] = None,
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> int:
        """重放事件
        
        Args:
            event_filter: 事件过滤器
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            int: 重放的事件数量
        """
        if not self._persistence:
            return 0
        
        # 构建时间过滤器
        if start_time or end_time:
            time_filter = EventFilter()
            if start_time and end_time:
                time_filter.set_time_range(start_time, end_time)
            
            if event_filter:
                # 合并过滤器
                # 这里需要更复杂的过滤器合并逻辑
                pass
            else:
                event_filter = time_filter
        
        # 查询事件
        stored_events = await self._persistence.query_events(event_filter)
        
        # 重放事件
        replay_count = 0
        for stored_event in stored_events:
            try:
                # 反序列化事件
                event = self._deserialize_event(stored_event.event_data)
                
                # 重新发布事件
                await self.publish(event)
                replay_count += 1
                
            except Exception as e:
                print(f"重放事件失败: {e}")
        
        return replay_count
    
    def _deserialize_event(self, event_data: Dict[str, Any]) -> DomainEvent:
        """反序列化事件
        
        Args:
            event_data: 事件数据
            
        Returns:
            DomainEvent: 领域事件
        """
        # 简单的反序列化实现，实际中需要根据具体事件类型进行反序列化
        # 这里返回一个基础事件作为示例
        class BasicEvent(DomainEvent):
            def __init__(self, event_type: str):
                super().__init__()
                self._event_type = event_type
            
            def get_event_type(self) -> str:
                return self._event_type
        
        return BasicEvent(event_data["event_type"])
    
    async def get_event_history(self, 
                               limit: int = 100,
                               event_filter: Optional[EventFilter] = None) -> List[Dict[str, Any]]:
        """获取事件历史
        
        Args:
            limit: 限制数量
            event_filter: 事件过滤器
            
        Returns:
            List[Dict[str, Any]]: 事件历史列表
        """
        if self._persistence:
            stored_events = await self._persistence.query_events(event_filter, limit)
            return [event.to_dict() for event in stored_events]
        else:
            # 从内存历史中获取
            events = list(self._event_history)
            if event_filter:
                events = [event for event in events if event_filter.matches(event)]
            
            events = events[-limit:] if limit > 0 else events
            return [event.to_dict() for event in events]
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标信息
        
        Returns:
            Dict[str, Any]: 指标信息
        """
        if not self._metrics:
            return {}
        
        metrics = self._metrics.copy()
        metrics['queue_size'] = self._event_queue.qsize()
        metrics['handler_count'] = sum(len(handlers) for handlers in self._handlers.values())
        metrics['global_handler_count'] = len(self._global_handlers)
        metrics['filter_count'] = len(self._global_filters)
        metrics['history_size'] = len(self._event_history)
        
        return metrics
    
    async def cleanup_old_events(self) -> int:
        """清理旧事件
        
        Returns:
            int: 删除的事件数量
        """
        if self._persistence:
            return await self._persistence.cleanup_old_events(self.event_retention_days)
        return 0
    
    def shutdown(self) -> None:
        """关闭事件总线"""
        self._processing = False
        self._executor.shutdown(wait=True)
        
        # 清理资源
        with self._lock:
            self._handlers.clear()
            self._global_handlers.clear()
            self._global_filters.clear()
            self._event_history.clear()