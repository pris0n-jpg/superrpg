"""
核心基础设施模块

该模块包含系统的核心基础设施组件，遵循SOLID原则，
提供依赖注入、事件系统、接口定义和异常处理等基础功能。

核心模块负责：
1. 依赖注入容器和管理
2. 事件系统和消息传递
3. 核心接口定义
4. 自定义异常层次结构
5. 基础设施抽象
"""

from .container import (
    DIContainer,
    ServiceLifetime,
    ServiceDescriptor,
    ServiceLocator,
)

from .interfaces import (
    WorldState,
    Repository,
    CharacterRepository,
    CombatRepository,
    DomainService,
    CharacterService,
    CombatService,
    EventBus,
    EventHandler,
    DomainEvent,
    WorldEvent,
    Logger,
    ConfigLoader,
    WorldSnapshot,
)

from .events import (
    EventMetadata,
    EventEnvelope,
    EventSubscription,
    InMemoryEventBus,
    EventStore,
    InMemoryEventStore,
)

from .exceptions import (
    BaseException,
    DomainException,
    ValidationException,
    BusinessRuleException,
    NotFoundException,
    DuplicateException,
    InfrastructureException,
    RepositoryException,
    ExternalServiceException,
    ConfigurationException,
    ApplicationException,
    ServiceUnavailableException,
    PermissionDeniedException,
    OperationTimeoutException,
    wrap_exception,
    is_exception_type,
    get_exception_chain,
)

__all__ = [
    # 依赖注入
    'DIContainer',
    'ServiceLifetime',
    'ServiceDescriptor',
    'ServiceLocator',
    
    # 核心接口
    'WorldState',
    'Repository',
    'CharacterRepository',
    'CombatRepository',
    'DomainService',
    'CharacterService',
    'CombatService',
    'EventBus',
    'EventHandler',
    'DomainEvent',
    'WorldEvent',
    'Logger',
    'ConfigLoader',
    'WorldSnapshot',
    
    # 事件系统
    'EventMetadata',
    'EventEnvelope',
    'EventSubscription',
    'InMemoryEventBus',
    'EventStore',
    'InMemoryEventStore',
    
    # 异常处理
    'BaseException',
    'DomainException',
    'ValidationException',
    'BusinessRuleException',
    'NotFoundException',
    'DuplicateException',
    'InfrastructureException',
    'RepositoryException',
    'ExternalServiceException',
    'ConfigurationException',
    'ApplicationException',
    'ServiceUnavailableException',
    'PermissionDeniedException',
    'OperationTimeoutException',
    'wrap_exception',
    'is_exception_type',
    'get_exception_chain',
]