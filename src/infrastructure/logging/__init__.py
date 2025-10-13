"""
日志模块

该模块提供日志记录的具体实现，包括事件日志和故事日志。
遵循依赖倒置原则，实现core/interfaces.py中定义的日志接口。
"""

from .event_logger_impl import EventLoggerImpl
from .story_logger_impl import StoryLoggerImpl

__all__ = [
    "EventLoggerImpl",
    "StoryLoggerImpl",
]