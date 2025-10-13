"""
事件日志实现

提供结构化事件日志记录的具体实现，基于现有的eventlog模块。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, TextIO
from datetime import datetime
from threading import Lock

from ...core.interfaces import Logger as ILogger
from ...core.events import DomainEvent


class EventLoggerImpl(ILogger):
    """事件日志实现
    
    基于Python标准logging模块和结构化日志的事件记录实现。
    遵循单一职责原则，专门负责事件日志的记录和管理。
    """
    
    def __init__(self, 
                 name: str = "superrpg",
                 log_file: Optional[Path] = None,
                 log_level: str = "INFO",
                 enable_console: bool = True,
                 enable_structured: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        """初始化事件日志
        
        Args:
            name: 日志器名称
            log_file: 日志文件路径
            log_level: 日志级别
            enable_console: 是否启用控制台输出
            enable_structured: 是否启用结构化日志
            max_file_size: 最大文件大小
            backup_count: 备份文件数量
        """
        self._name = name
        self._log_file = log_file
        self._log_level = getattr(logging, log_level.upper())
        self._enable_console = enable_console
        self._enable_structured = enable_structured
        self._max_file_size = max_file_size
        self._backup_count = backup_count
        self._lock = Lock()
        
        # 初始化日志器
        self._logger = self._setup_logger()
        
        # 事件计数器
        self._event_counters: Dict[str, int] = {}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志器
        
        Returns:
            logging.Logger: 配置好的日志器
        """
        logger = logging.getLogger(self._name)
        logger.setLevel(self._log_level)
        
        # 防止日志传播到根日志器，避免重复日志
        logger.propagate = False
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 设置格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if self._enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if self._log_file:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                self._log_file,
                maxBytes=self._max_file_size,
                backupCount=self._backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self._log_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _log_structured(self, level: str, message: str, **kwargs) -> None:
        """记录结构化日志
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        if not self._enable_structured:
            return
        
        structured_data = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'logger': self._name,
            'message': message,
            **kwargs
        }
        
        # 如果有日志文件，写入结构化日志
        if self._log_file:
            structured_file = self._log_file.parent / f"{self._log_file.stem}_structured.jsonl"
            try:
                with open(structured_file, 'a', encoding='utf-8') as f:
                    json.dump(structured_data, f, ensure_ascii=False)
                    f.write('\n')
            except Exception:
                # 静默处理写入错误
                pass
    
    def _update_event_counter(self, event_type: str) -> None:
        """更新事件计数器
        
        Args:
            event_type: 事件类型
        """
        with self._lock:
            self._event_counters[event_type] = self._event_counters.get(event_type, 0) + 1
    
    def _get_log_level_method(self, level: str) -> callable:
        """获取日志级别方法
        
        Args:
            level: 日志级别
            
        Returns:
            callable: 日志方法
        """
        level_methods = {
            'debug': self._logger.debug,
            'info': self._logger.info,
            'warning': self._logger.warning,
            'error': self._logger.error,
            'critical': self._logger.critical,
        }
        return level_methods.get(level.lower(), self._logger.info)
    
    # 实现Logger接口方法
    
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.info(message)
        self._log_structured('info', message, **kwargs)
        
        # 更新事件计数器
        event_type = kwargs.get('event_type', 'info')
        self._update_event_counter(event_type)
    
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.warning(message)
        self._log_structured('warning', message, **kwargs)
        
        # 更新事件计数器
        event_type = kwargs.get('event_type', 'warning')
        self._update_event_counter(event_type)
    
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.error(message)
        self._log_structured('error', message, **kwargs)
        
        # 更新事件计数器
        event_type = kwargs.get('event_type', 'error')
        self._update_event_counter(event_type)
    
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        self._logger.debug(message)
        self._log_structured('debug', message, **kwargs)
        
        # 更新事件计数器
        event_type = kwargs.get('event_type', 'debug')
        self._update_event_counter(event_type)
    
    # 扩展方法
    
    def log_domain_event(self, event: DomainEvent, **kwargs) -> None:
        """记录领域事件
        
        Args:
            event: 领域事件
            **kwargs: 额外的日志数据
        """
        event_data = {
            'event_id': event.id,
            'event_type': event.get_event_type(),
            'occurred_at': event.occurred_at.isoformat(),
            **kwargs
        }
        
        # 如果事件有额外属性，添加到日志数据中
        if hasattr(event, '__dict__'):
            for key, value in event.__dict__.items():
                if key not in ['id', 'occurred_at'] and not key.startswith('_'):
                    event_data[key] = value
        
        self.info(f"领域事件: {event.get_event_type()}", **event_data)
    
    def log_system_event(self, event_type: str, message: str, **kwargs) -> None:
        """记录系统事件
        
        Args:
            event_type: 事件类型
            message: 事件消息
            **kwargs: 额外的日志数据
        """
        event_data = {
            'event_type': event_type,
            'event_category': 'system',
            **kwargs
        }
        
        self.info(f"系统事件: {message}", **event_data)
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """记录性能日志
        
        Args:
            operation: 操作名称
            duration: 持续时间（秒）
            **kwargs: 额外的日志数据
        """
        perf_data = {
            'operation': operation,
            'duration_ms': duration * 1000,
            'event_category': 'performance',
            **kwargs
        }
        
        if duration > 1.0:  # 超过1秒的操作记录为警告
            self.warning(f"性能警告: {operation} 耗时 {duration:.2f}秒", **perf_data)
        else:
            self.debug(f"性能日志: {operation} 耗时 {duration:.3f}秒", **perf_data)
    
    def log_user_action(self, user: str, action: str, **kwargs) -> None:
        """记录用户操作
        
        Args:
            user: 用户标识
            action: 操作描述
            **kwargs: 额外的日志数据
        """
        action_data = {
            'user': user,
            'action': action,
            'event_category': 'user_action',
            **kwargs
        }
        
        self.info(f"用户操作: {user} 执行了 {action}", **action_data)
    
    def log_security_event(self, event_type: str, message: str, **kwargs) -> None:
        """记录安全事件
        
        Args:
            event_type: 事件类型
            message: 事件消息
            **kwargs: 额外的日志数据
        """
        security_data = {
            'event_type': event_type,
            'event_category': 'security',
            'severity': kwargs.get('severity', 'medium'),
            **kwargs
        }
        
        self.warning(f"安全事件: {message}", **security_data)
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """获取事件统计信息
        
        Returns:
            Dict[str, Any]: 事件统计信息
        """
        with self._lock:
            total_events = sum(self._event_counters.values())
            
            return {
                'total_events': total_events,
                'event_types': dict(self._event_counters),
                'most_common': max(self._event_counters.items(), key=lambda x: x[1]) if self._event_counters else None,
                'logger_name': self._name,
                'log_level': logging.getLevelName(self._log_level),
                'structured_logging_enabled': self._enable_structured,
                'console_logging_enabled': self._enable_console,
                'log_file': str(self._log_file) if self._log_file else None,
            }
    
    def reset_counters(self) -> None:
        """重置事件计数器"""
        with self._lock:
            self._event_counters.clear()
    
    def set_log_level(self, level: str) -> None:
        """设置日志级别
        
        Args:
            level: 日志级别
        """
        self._log_level = getattr(logging, level.upper())
        self._logger.setLevel(self._log_level)
        
        # 更新所有处理器的级别
        for handler in self._logger.handlers:
            handler.setLevel(self._log_level)
    
    def add_custom_handler(self, handler: logging.Handler) -> None:
        """添加自定义处理器
        
        Args:
            handler: 日志处理器
        """
        self._logger.addHandler(handler)
    
    def remove_handler(self, handler: logging.Handler) -> None:
        """移除处理器
        
        Args:
            handler: 日志处理器
        """
        self._logger.removeHandler(handler)
    
    def flush(self) -> None:
        """刷新所有处理器"""
        with self._lock:
            for handler in self._logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
    
    def close(self) -> None:
        """关闭日志器"""
        with self._lock:
            for handler in self._logger.handlers:
                if hasattr(handler, 'close'):
                    handler.close()
            self._logger.handlers.clear()


class EventLoggerFactory:
    """事件日志工厂
    
    提供便捷的日志器创建方法。
    """
    
    @staticmethod
    def create_default_logger(name: str = "superrpg", log_dir: Optional[Path] = None) -> EventLoggerImpl:
        """创建默认日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            
        Returns:
            EventLoggerImpl: 日志器实例
        """
        if log_dir is None:
            log_dir = Path("logs")
        
        log_file = log_dir / f"{name}.log"
        
        return EventLoggerImpl(
            name=name,
            log_file=log_file,
            log_level="INFO",
            enable_console=True,
            enable_structured=True
        )
    
    @staticmethod
    def create_debug_logger(name: str = "superrpg_debug", log_dir: Optional[Path] = None) -> EventLoggerImpl:
        """创建调试日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            
        Returns:
            EventLoggerImpl: 日志器实例
        """
        if log_dir is None:
            log_dir = Path("logs")
        
        log_file = log_dir / f"{name}.log"
        
        return EventLoggerImpl(
            name=name,
            log_file=log_file,
            log_level="DEBUG",
            enable_console=True,
            enable_structured=True
        )
    
    @staticmethod
    def create_production_logger(name: str = "superrpg", log_dir: Optional[Path] = None) -> EventLoggerImpl:
        """创建生产环境日志器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录
            
        Returns:
            EventLoggerImpl: 日志器实例
        """
        if log_dir is None:
            log_dir = Path("logs")
        
        log_file = log_dir / f"{name}.log"
        
        return EventLoggerImpl(
            name=name,
            log_file=log_file,
            log_level="INFO",
            enable_console=False,
            enable_structured=True,
            max_file_size=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )