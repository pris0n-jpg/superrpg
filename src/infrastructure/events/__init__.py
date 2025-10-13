"""
事件系统模块

该模块提供事件系统的具体实现，包括事件总线。
遵循依赖倒置原则，实现core/interfaces.py中定义的事件接口。
"""

from .event_bus_impl import EventBusImpl

__all__ = [
    "EventBusImpl",
]