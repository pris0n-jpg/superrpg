"""
应用服务层依赖注入容器配置

该模块配置了应用服务层的依赖注入容器，遵循SOLID原则，
特别是依赖倒置原则(DIP)，确保高层模块不依赖低层模块。

容器配置负责：
1. 注册应用服务
2. 注册命令和查询处理器
3. 注册协调器
4. 配置服务生命周期
"""

from typing import Dict, Any, List
from ..core.container import DIContainer, ServiceLifetime
from ..core.interfaces import EventBus, Logger
from ..infrastructure.events.event_bus_impl import InMemoryEventBus
from ..infrastructure.logging.event_logger_impl import EventLoggerImpl
from ..domain.services.character_service import CharacterService
from ..domain.services.combat_service import CombatService
from ..domain.services.world_service import WorldService
from ..domain.models.relations import RelationshipNetwork
from ..domain.models.objectives import ObjectiveTracker
from ..domain.repositories.character_repository import CharacterRepository
from ..infrastructure.repositories.character_repository_impl import CharacterRepositoryImpl
from ..domain.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from ..domain.repositories.prompt_repository import PromptRepository
from ..infrastructure.repositories.lorebook_repository_impl import LorebookRepositoryImpl, LorebookEntryRepositoryImpl
from ..infrastructure.repositories.prompt_repository_impl import PromptRepositoryImpl
from .services.game_engine import GameEngineService
from .services.token_counter_service import TokenCounterService
from .services.prompt_template_service import PromptTemplateService
from .services.prompt_assembly_service import PromptAssemblyService
from .services.turn_manager import TurnManagerService
from .services.message_handler import MessageHandlerService
from .services.agent_service import AgentService
from .services.character_card_service import CharacterCardService
from .services.keyword_matcher_service import KeywordMatcherService
from .services.lorebook_service import LorebookService
from ..adapters.prompt_controller import PromptController
from .commands.character_commands import CharacterCommandHandler
from .commands.world_commands import WorldCommandHandler
from .queries.character_queries import CharacterQueryHandler
from .queries.world_queries import WorldQueryHandler
from .coordinators.game_coordinator import GameCoordinator
from ..core.interfaces import GameCoordinator as IGameCoordinator


def configure_application_container(
    container: DIContainer,
    event_bus: EventBus = None,
    logger: Logger = None,
    custom_config: Dict[str, Any] = None
) -> DIContainer:
    """配置应用服务层容器
    
    Args:
        container: 依赖注入容器
        event_bus: 事件总线（可选）
        logger: 日志记录器（可选）
        custom_config: 自定义配置（可选）
        
    Returns:
        DIContainer: 配置后的容器
    """
    config = custom_config or {}
    
    # 注册基础设施服务
    if event_bus:
        container.register_instance(EventBus, event_bus)
    else:
        container.register_singleton(EventBus, InMemoryEventBus)
    
    if logger:
        container.register_instance(Logger, logger)
    else:
        container.register_singleton(Logger, EventLoggerImpl)
    
    # 注册领域服务
    container.register_singleton(RelationshipNetwork, RelationshipNetwork)
    container.register_singleton(ObjectiveTracker, ObjectiveTracker)
    
    container.register_factory(
        CharacterService,
        lambda: CharacterService(
            relationship_network=container.resolve(RelationshipNetwork),
            objective_tracker=container.resolve(ObjectiveTracker)
        )
    )
    
    container.register_factory(
        CombatService,
        lambda: CombatService()
    )
    
    container.register_factory(
        WorldService,
        lambda: WorldService()
    )
    
    # 注册仓储服务
    container.register_factory(
        CharacterRepository,
        lambda: CharacterRepositoryImpl(
            storage_path=config.get("character_storage_path")
        )
    )
    
    # 注册传说书仓储
    container.register_factory(
        LorebookRepository,
        lambda: LorebookRepositoryImpl(
            storage_path=config.get("lorebook_storage_path")
        )
    )
    
    container.register_factory(
        LorebookEntryRepository,
        lambda: LorebookEntryRepositoryImpl(
            lorebook_repository=container.resolve(LorebookRepository)
        )
    )
    
    # 注册提示仓储
    container.register_factory(
        PromptRepository,
        lambda: PromptRepositoryImpl(
            storage_path=config.get("prompt_storage_path"),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册Token计数服务
    container.register_factory(
        TokenCounterService,
        lambda: TokenCounterService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册提示模板服务
    container.register_factory(
        PromptTemplateService,
        lambda: PromptTemplateService(
            prompt_repository=container.resolve(PromptRepository),
            token_counter=container.resolve(TokenCounterService),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册提示组装服务
    container.register_factory(
        PromptAssemblyService,
        lambda: PromptAssemblyService(
            prompt_repository=container.resolve(PromptRepository),
            token_counter=container.resolve(TokenCounterService),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册提示控制器
    container.register_factory(
        PromptController,
        lambda: PromptController(
            assembly_service=container.resolve(PromptAssemblyService),
            template_service=container.resolve(PromptTemplateService),
            token_counter=container.resolve(TokenCounterService),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册应用服务
    container.register_factory(
        GameEngineService,
        lambda: GameEngineService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger),
            character_service=container.resolve(CharacterService),
            combat_service=container.resolve(CombatService),
            world_service=container.resolve(WorldService)
        )
    )
    
    container.register_factory(
        TurnManagerService,
        lambda: TurnManagerService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger),
            game_engine=container.resolve(GameEngineService),
            timeout_duration=config.get("turn_timeout", 30)
        )
    )
    
    container.register_factory(
        MessageHandlerService,
        lambda: MessageHandlerService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger),
            tool_executors=config.get("tool_executors", [])
        )
    )
    
    container.register_factory(
        AgentService,
        lambda: AgentService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger),
            agent_factories=config.get("agent_factories", []),
            default_timeout=config.get("agent_timeout", 30)
        )
    )
    
    # 注册角色卡服务
    container.register_factory(
        CharacterCardService,
        lambda: CharacterCardService(
            character_repository=container.resolve(CharacterRepository),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册关键词匹配服务
    container.register_factory(
        KeywordMatcherService,
        lambda: KeywordMatcherService(
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册传说书服务
    container.register_factory(
        LorebookService,
        lambda: LorebookService(
            lorebook_repository=container.resolve(LorebookRepository),
            entry_repository=container.resolve(LorebookEntryRepository),
            keyword_matcher=container.resolve(KeywordMatcherService),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册命令处理器
    container.register_factory(
        CharacterCommandHandler,
        lambda: CharacterCommandHandler(
            character_service=container.resolve(CharacterService),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    container.register_factory(
        WorldCommandHandler,
        lambda: WorldCommandHandler(
            world_service=container.resolve(WorldService),
            game_engine=container.resolve(GameEngineService),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册查询处理器
    container.register_factory(
        CharacterQueryHandler,
        lambda: CharacterQueryHandler(
            logger=container.resolve(Logger)
        )
    )
    
    container.register_factory(
        WorldQueryHandler,
        lambda: WorldQueryHandler(
            game_engine=container.resolve(GameEngineService),
            logger=container.resolve(Logger)
        )
    )
    
    # 注册协调器
    container.register_factory(
        IGameCoordinator,
        lambda: GameCoordinator(
            game_engine=container.resolve(GameEngineService),
            turn_manager=container.resolve(TurnManagerService),
            message_handler=container.resolve(MessageHandlerService),
            agent_service=container.resolve(AgentService),
            character_command_handler=container.resolve(CharacterCommandHandler),
            world_command_handler=container.resolve(WorldCommandHandler),
            character_query_handler=container.resolve(CharacterQueryHandler),
            world_query_handler=container.resolve(WorldQueryHandler),
            event_bus=container.resolve(EventBus),
            logger=container.resolve(Logger),
            container=container
        )
    )
    
    return container


def create_application_container(
    event_bus: EventBus = None,
    logger: Logger = None,
    custom_config: Dict[str, Any] = None
) -> DIContainer:
    """创建应用服务层容器
    
    Args:
        event_bus: 事件总线（可选）
        logger: 日志记录器（可选）
        custom_config: 自定义配置（可选）
        
    Returns:
        DIContainer: 创建的容器
    """
    container = DIContainer()
    return configure_application_container(container, event_bus, logger, custom_config)


def get_default_application_config() -> Dict[str, Any]:
    """获取默认应用配置
    
    Returns:
        Dict[str, Any]: 默认配置
    """
    return {
        "turn_timeout": 30,
        "agent_timeout": 30,
        "tool_executors": [],
        "agent_factories": [],
        "max_rounds": 50,
        "require_hostiles": True,
        "debug_mode": False,
        "lorebook_storage_path": None,
        "prompt_storage_path": None
    }


def validate_container_configuration(container: DIContainer) -> List[str]:
    """验证容器配置
    
    Args:
        container: 依赖注入容器
        
    Returns:
        List[str]: 验证错误列表，空列表表示验证通过
    """
    errors = container.validate_dependencies()
    
    # 检查关键服务是否已注册
    required_services = [
        EventBus,
        Logger,
        GameEngineService,
        TurnManagerService,
        MessageHandlerService,
        AgentService,
        CharacterCardService,
        KeywordMatcherService,
        LorebookService,
        LorebookRepository,
        LorebookEntryRepository,
        PromptRepository,
        TokenCounterService,
        PromptTemplateService,
        PromptAssemblyService,
        PromptController,
        CharacterCommandHandler,
        WorldCommandHandler,
        CharacterQueryHandler,
        WorldQueryHandler,
        IGameCoordinator
    ]
    
    for service_type in required_services:
        if not container.is_registered(service_type):
            errors.append(f"Required service not registered: {service_type.__name__}")
    
    return errors