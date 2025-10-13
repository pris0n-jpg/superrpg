"""
核心接口包

该包定义了系统的核心接口，遵循SOLID原则中的依赖倒置原则(DIP)，
确保高层模块不依赖低层模块，而是依赖于抽象接口。

注意：核心接口定义在 ../core_interfaces.py 文件中，扩展接口定义在 ./extension_interface.py 文件中。
该模块统一导出所有接口以保持向后兼容性。
"""

# 从扩展接口模块导入扩展相关类
from .extension_interface import (
    Extension,
    ExtensionStatus,
    ExtensionType,
    ExtensionMetadata,
    ExtensionContext,
    ExtensionFactory,
    ExtensionRegistry,
    ExtensionManager,
    ExtensionLoader,
    ExtensionEvent,
    ExtensionEventHandler
)

# 从 core_interfaces.py 导入核心接口类
from ..core_interfaces import (
    WorldState,
    Repository,
    CharacterRepository,
    CombatRepository,
    WorldRepository,
    DomainService,
    CharacterService,
    CombatService,
    EventBus,
    EventHandler,
    DomainEvent,
    WorldEvent,
    Logger,
    ConfigLoader,
    GameCoordinator,
    WorldSnapshot,
)

__all__ = [
    # 核心接口
    "WorldState",
    "Repository",
    "CharacterRepository",
    "CombatRepository",
    "WorldRepository",
    "DomainService",
    "CharacterService",
    "CombatService",
    "EventBus",
    "EventHandler",
    "DomainEvent",
    "WorldEvent",
    "Logger",
    "ConfigLoader",
    "GameCoordinator",
    "WorldSnapshot",
    # 扩展接口
    "Extension",
    "ExtensionStatus",
    "ExtensionType",
    "ExtensionMetadata",
    "ExtensionContext",
    "ExtensionFactory",
    "ExtensionRegistry",
    "ExtensionManager",
    "ExtensionLoader",
    "ExtensionEvent",
    "ExtensionEventHandler",
]
