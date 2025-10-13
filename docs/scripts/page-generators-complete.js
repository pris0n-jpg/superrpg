// 完整页面内容生成器
window.pageGeneratorsComplete = {
    // 合并原有的页面生成器
    ...window.pageGenerators,
    ...window.pageGeneratorsExtended,
    ...window.apiGenerators,
    ...window.exampleGenerators,

    // 设计原则页面（显式暴露，避免键名被覆盖）
    principles: function() {
        return window.pageGenerators && typeof window.pageGenerators.principles === 'function'
            ? window.pageGenerators.principles()
            : '';
    },

    // 命令接口页面
    commands: function() {
        if (window.apiGenerators && typeof window.apiGenerators.commands === 'function') {
            return window.apiGenerators.commands();
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">命令接口</h1>
                    <p class="card-subtitle">Commands - 修改系统状态的操作入口</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        SuperRPG 的命令遵循 CQRS 模式，用于创建或更新领域状态。以下概览涵盖主要命令分类与调用流程。
                    </div>

                    <h2>命令分类</h2>
                    <div class="command-grid">
                        <div class="command-card">
                            <h3><i class="fas fa-user-plus"></i> 角色管理</h3>
                            <ul>
                                <li>CreateCharacterCommand</li>
                                <li>UpdateAbilitiesCommand</li>
                                <li>AssignToolCommand</li>
                            </ul>
                        </div>
                        <div class="command-card">
                            <h3><i class="fas fa-globe"></i> 世界管理</h3>
                            <ul>
                                <li>CreateWorldCommand</li>
                                <li>AdvanceTimeCommand</li>
                                <li>UpdateSceneCommand</li>
                            </ul>
                        </div>
                        <div class="command-card">
                            <h3><i class="fas fa-swords"></i> 战斗管理</h3>
                            <ul>
                                <li>StartCombatCommand</li>
                                <li>ExecuteActionCommand</li>
                                <li>EndCombatCommand</li>
                            </ul>
                        </div>
                    </div>

                    <h2>命令执行流程</h2>
                    <div class="code-example">
                        <div class="code-title">处理角色创建命令</div>
                        <pre><code class="language-python">class CreateCharacterCommand:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config


class CharacterCommandHandler:
    def handle(self, command: CreateCharacterCommand) -> CommandResult:
        character = self.character_service.create_character(
            command.name,
            command.config
        )
        return CommandResult.success_result(data=character)</code></pre>
                    </div>

                    <h2>良好实践</h2>
                    <ul class="guideline-list">
                        <li>命名采用动词短语，清晰表达状态变化意图</li>
                        <li>命令对象保持不可变，便于审计与记录</li>
                        <li>处理器只负责协调领域服务，不直接持久化</li>
                    </ul>
                </div>
            </div>

            <style>
            .command-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }

            .command-card {
                padding: 1rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                background-color: var(--bg-card);
            }

            .command-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }

            .guideline-list {
                margin: 1rem 0 0 0;
                padding-left: 1.25rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    },

    // 查询接口页面
    queries: function() {
        if (window.apiGenerators && typeof window.apiGenerators.queries === 'function') {
            return window.apiGenerators.queries();
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">查询接口</h1>
                    <p class="card-subtitle">Queries - 获取领域状态的只读入口</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        查询接口提供一致的只读访问通道，配合命令实现读写分离，提升可扩展性与性能。
                    </div>

                    <h2>常用查询</h2>
                    <div class="query-grid">
                        <div class="query-card">
                            <h3><i class="fas fa-users"></i> 角色查询</h3>
                            <ul>
                                <li>GetCharacterByNameQuery</li>
                                <li>ListPartyMembersQuery</li>
                                <li>GetCharacterStatusQuery</li>
                            </ul>
                        </div>
                        <div class="query-card">
                            <h3><i class="fas fa-map"></i> 世界状态</h3>
                            <ul>
                                <li>GetCurrentSceneQuery</li>
                                <li>GetWorldSnapshotQuery</li>
                                <li>ListActiveObjectivesQuery</li>
                            </ul>
                        </div>
                        <div class="query-card">
                            <h3><i class="fas fa-dice"></i> 战斗信息</h3>
                            <ul>
                                <li>GetCombatStateQuery</li>
                                <li>GetInitiativeOrderQuery</li>
                                <li>ListPendingActionsQuery</li>
                            </ul>
                        </div>
                    </div>

                    <h2>查询处理器示例</h2>
                    <div class="code-example">
                        <div class="code-title">获取当前场景信息</div>
                        <pre><code class="language-python">class GetCurrentSceneQuery:
    def __init__(self, world_id: str):
        self.world_id = world_id


class SceneQueryHandler:
    def handle(self, query: GetCurrentSceneQuery) -> QueryResult:
        world = self.world_repository.get(query.world_id)
        scene = world.current_scene
        return QueryResult.success(data=scene.to_dict())</code></pre>
                    </div>

                    <h2>使用建议</h2>
                    <ul class="guideline-list">
                        <li>查询对象保持最小化，只包含过滤参数</li>
                        <li>结果统一封装为 \`QueryResult\`，便于前端处理</li>
                        <li>复杂读取场景可缓存，命令提交后异步刷新</li>
                    </ul>
                </div>
            </div>

            <style>
            .query-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }

            .query-card {
                padding: 1rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                background-color: var(--bg-card);
            }

            .query-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }
            .guideline-list {
                margin: 1rem 0 0 0;
                padding-left: 1.25rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    },

    // 事件接口页面
    events: function() {
        if (window.apiGenerators && typeof window.apiGenerators.events === 'function') {
            return window.apiGenerators.events();
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">事件系统</h1>
                    <p class="card-subtitle">Events - 构建松耦合协作的关键机制</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        SuperRPG 通过领域事件连接各层组件。事件由应用层发布，基础设施层负责派发与持久化。
                    </div>

                    <h2>核心事件</h2>
                    <div class="event-grid">
                        <div class="event-card">
                            <h3><i class="fas fa-play"></i> TurnStartedEvent</h3>
                            <p>回合开始时触发，广播当前角色及回合序号。</p>
                            <code>payload: character_name, turn_number, timestamp</code>
                        </div>
                        <div class="event-card">
                            <h3><i class="fas fa-check"></i> TurnCompletedEvent</h3>
                            <p>回合结束时触发，包含行动记录与耗时。</p>
                            <code>payload: character_name, actions, duration_ms</code>
                        </div>
                        <div class="event-card">
                            <h3><i class="fas fa-bolt"></i> ToolInvokedEvent</h3>
                            <p>代理调用工具时触发，便于审计与追踪。</p>
                            <code>payload: agent_name, tool_name, parameters</code>
                        </div>
                    </div>

                    <h2>订阅示例</h2>
                    <div class="code-example">
                        <div class="code-title">监听回合结束事件</div>
                        <pre><code class="language-python">@event_bus.subscribe("TurnCompletedEvent")
def on_turn_completed(event: DomainEvent):
    logger.info(
        "Turn %s completed by %s",
        event.payload["turn_number"],
        event.payload["character_name"]
    )
    timeline.store(event)</code></pre>
                    </div>

                    <h2>设计要点</h2>
                    <ul class="guideline-list">
                        <li>事件名称使用过去式，表达已发生的事实</li>
                        <li>事件载荷保持序列化友好，避免复杂对象</li>
                        <li>订阅者专注单一职责，可借助工作队列异步处理</li>
                    </ul>
                </div>
            </div>

            <style>
            .event-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem;
                margin: 1.5rem 0;
            }

            .event-card {
                padding: 1rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                background-color: var(--bg-card);
            }

            .event-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }

            .event-card code {
                display: block;
                margin-top: 0.5rem;
                color: var(--text-secondary);
                font-size: var(--font-size-sm);
            }
            .guideline-list {
                margin: 1rem 0 0 0;
                padding-left: 1.25rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    },

    // 战斗示例页面
    combatExample: function() {
        if (window.exampleGenerators && typeof window.exampleGenerators.combatExample === 'function') {
            return window.exampleGenerators.combatExample();
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">战斗系统示例</h1>
                    <p class="card-subtitle">Combat Example - 模拟一轮战斗的流程</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        以下示例展示如何使用回合管理器与战斗服务模拟单轮战斗，包括初始化、行动与结果分析。
                    </div>

                    <h2>战斗管理器</h2>
                    <div class="code-example">
                        <div class="code-title">CombatManager 核心逻辑</div>
                        <pre><code class="language-python">class CombatManager:
    def __init__(self, turn_manager: TurnManager, combat_service: CombatService):
        self.turn_manager = turn_manager
        self.combat_service = combat_service

    async def simulate_combat_round(self, attacker: str, defender: str) -> Dict[str, Any]:
        await self.turn_manager.start_turn(attacker)
        action = Action(attacker=attacker, defender=defender, action_type="attack")
        result = await self.combat_service.resolve_action(action)
        await self.turn_manager.complete_turn([action])
        return {
            "attacker": attacker,
            "defender": defender,
            "success": result.success,
            "damage": result.data.get("damage", 0),
            "logs": result.data.get("logs", [])
        }</code></pre>
                    </div>

                    <h2>执行战斗</h2>
                    <div class="code-example">
                        <div class="code-title">运行示例</div>
                        <pre><code class="language-python">manager = CombatManager(turn_manager, combat_service)

result = await manager.simulate_combat_round("Amiya", "Goblin")

if result["success"]:
    print(f"造成伤害: {result['damage']}")
else:
    print("攻击未命中")

for log in result["logs"]:
    print(log)</code></pre>
                    </div>

                    <h2>要点总结</h2>
                    <ul class="guideline-list">
                        <li>战斗以回合驱动，确保行动顺序清晰</li>
                        <li>CombatService 负责规则判定与伤害计算</li>
                        <li>返回结果统一结构化，便于 UI 展示与日志记录</li>
                    </ul>
                </div>
            </div>
            <style>
            .guideline-list {
                margin: 1rem 0 0 0;
                padding-left: 1.25rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    },

    // 事件示例页面
    eventExample: function() {
        if (window.exampleGenerators && typeof window.exampleGenerators.eventExample === 'function') {
            return window.exampleGenerators.eventExample();
        }

        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">事件处理示例</h1>
                    <p class="card-subtitle">Event Example - 构建事件驱动的扩展点</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        示例展示如何通过领域事件实现松耦合扩展，包括事件订阅、处理与持久化。
                    </div>

                    <h2>事件总线封装</h2>
                    <div class="code-example">
                        <div class="code-title">注册订阅者</div>
                        <pre><code class="language-python">class AuditEventSubscriber:
    def __init__(self, audit_log: AuditLog):
        self.audit_log = audit_log

    def handle(self, event: DomainEvent) -> None:
        self.audit_log.record({
            "name": event.name,
            "occurred_at": event.occurred_at,
            "payload": event.payload
        })


event_bus.subscribe("TurnCompletedEvent", AuditEventSubscriber(audit_log).handle)</code></pre>
                    </div>

                    <h2>发布事件</h2>
                    <div class="code-example">
                        <div class="code-title">应用层发布事件</div>
                        <pre><code class="language-python">class GameEngineService:
    def _complete_turn(self, result: CommandResult) -> None:
        event = DomainEvent(
            name="TurnCompletedEvent",
            payload=result.data,
            metadata={"source": "GameEngine"}
        )
        self.event_bus.publish(event)</code></pre>
                    </div>

                    <h2>最佳实践</h2>
                    <ul class="guideline-list">
                        <li>订阅者职责单一，可通过 DI 注册</li>
                        <li>必要时使用队列或异步任务削峰填谷</li>
                        <li>将事件记录到审计日志，支持回溯与调试</li>
                    </ul>
                </div>
            </div>
            <style>
            .guideline-list {
                margin: 1rem 0 0 0;
                padding-left: 1.25rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    },

    // 应用层页面
    applicationLayer: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">应用层</h1>
                    <p class="card-subtitle">Application Layer - 业务流程协调和应用服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            应用层负责协调领域层和基础设施层，处理应用程序的业务流程。包括游戏引擎、回合管理器、消息处理器、代理服务等核心服务。
                        </div>
                        
                        <h2>核心服务</h2>
                        <div class="services-grid">
                            <div class="service-card">
                                <h3><i class="fas fa-gamepad"></i> GameEngine</h3>
                                <p>游戏引擎服务，负责游戏的核心逻辑协调。</p>
                                <ul>
                                    <li>游戏流程控制</li>
                                    <li>状态管理</li>
                                    <li>事件处理</li>
                                    <li>游戏配置和初始化</li>
                                </ul>
                            </div>
                            
                            <div class="service-card">
                                <h3><i class="fas fa-clock"></i> TurnManager</h3>
                                <p>回合管理器服务，负责游戏回合的管理。</p>
                                <ul>
                                    <li>回合流程控制</li>
                                    <li>角色行动顺序维护</li>
                                    <li>回合状态跟踪</li>
                                    <li>行动超时处理</li>
                                </ul>
                            </div>
                            
                            <div class="service-card">
                                <h3><i class="fas fa-envelope"></i> MessageHandler</h3>
                                <p>消息处理服务，负责处理游戏中的消息和工具调用。</p>
                                <ul>
                                    <li>消息解析和处理</li>
                                    <li>工具调用识别和执行</li>
                                    <li>消息内容清理和转换</li>
                                    <li>错误处理和日志记录</li>
                                </ul>
                            </div>
                            
                            <div class="service-card">
                                <h3><i class="fas fa-robot"></i> AgentService</h3>
                                <p>代理服务，负责游戏中的代理(AI角色)管理。</p>
                                <ul>
                                    <li>代理的创建和初始化</li>
                                    <li>代理状态的管理</li>
                                    <li>代理交互的协调</li>
                                    <li>代理配置的处理</li>
                                </ul>
                            </div>
                        </div>
                        
                        <h2>CQRS模式应用</h2>
                        <div class="cqrs-section">
                            <div class="cqrs-card">
                                <h3><i class="fas fa-terminal"></i> 命令处理</h3>
                                <p>修改系统状态的操作，通过命令处理器执行。</p>
                                <div class="code-example">
                                    <div class="code-title">命令示例</div>
                                    <pre><code class="language-python"># 创建角色命令
class CreateCharacterCommand:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

# 命令处理器
class CharacterCommandHandler:
    def handle(self, command: CreateCharacterCommand) -> CommandResult:
        character = self.character_service.create_character(
            command.name, command.config
        )
        return CommandResult.success_result(data=character)</code></pre>
                                </div>
                            </div>
                            
                            <div class="cqrs-card">
                                <h3><i class="fas fa-search"></i> 查询处理</h3>
                                <p>读取系统状态的操作，通过查询处理器执行。</p>
                                <div class="code-example">
                                    <div class="code-title">查询示例</div>
                                    <pre><code class="language-python"># 获取角色查询
class GetCharacterQuery:
    def __init__(self, name: str):
        self.name = name

# 查询处理器
class CharacterQueryHandler:
    def handle(self, query: GetCharacterQuery) -> Optional[Character]:
        return self.character_repository.get_by_name(query.name)</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>事件驱动架构</h2>
                        <div class="event-section">
                            <p>应用层通过事件系统实现组件间的松耦合通信：</p>
                            <ul>
                                <li><strong>领域事件发布</strong>：领域层发布业务事件</li>
                                <li><strong>异步事件处理</strong>：应用服务异步处理事件</li>
                                <li><strong>事件溯源支持</strong>：支持事件存储和重放</li>
                                <li><strong>跨模块通信</strong>：通过事件实现模块间通信</li>
                            </ul>
                            
                            <div class="code-example">
                                <div class="code-title">事件发布示例</div>
                                <pre><code class="language-python"># 发布角色移动事件
def move_character(self, character_name: str, new_position: Position):
    character = self.character_repository.get_by_name(character_name)
    old_position = character.position
    character.position = new_position
    
    # 发布领域事件
    self.publish_event(CharacterMovedEvent(
        character_name=character_name,
        old_position=old_position,
        new_position=new_position
    ))</code></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 基础设施层页面
    infrastructureLayer: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">基础设施层</h1>
                    <p class="card-subtitle">Infrastructure Layer - 技术支持和基础设施服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            基础设施层提供技术支持，包括事件总线、日志系统、配置管理、仓储实现等。为上层提供稳定的技术基础。
                        </div>
                        
                        <h2>核心组件</h2>
                        <div class="components-grid">
                            <div class="component-card">
                                <h3><i class="fas fa-bolt"></i> 事件总线</h3>
                                <p>实现组件间的松耦合通信，支持事件发布订阅模式。</p>
                                <div class="code-example">
                                    <div class="code-title">事件总线接口</div>
                                    <pre><code class="language-python">class EventBus(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        pass</code></pre>
                                </div>
                            </div>
                            
                            <div class="component-card">
                                <h3><i class="fas fa-file-alt"></i> 日志系统</h3>
                                <p>提供结构化日志记录，支持多种日志级别和输出格式。</p>
                                <div class="code-example">
                                    <div class="code-title">日志接口</div>
                                    <pre><code class="language-python">class Logger(ABC):
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        pass</code></pre>
                                </div>
                            </div>
                            
                            <div class="component-card">
                                <h3><i class="fas fa-cog"></i> 配置管理</h3>
                                <p>统一的配置加载和管理，支持多种配置源和格式。</p>
                                <div class="code-example">
                                    <div class="code-title">配置加载器</div>
                                    <pre><code class="language-python">class ConfigLoader:
    def load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r') as f:
            return json.load(f)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)</code></pre>
                                </div>
                            </div>
                            
                            <div class="component-card">
                                <h3><i class="fas fa-database"></i> 仓储实现</h3>
                                <p>数据访问层的具体实现，支持内存和文件存储。</p>
                                <div class="code-example">
                                    <div class="code-title">内存仓储实现</div>
                                    <pre><code class="language-python">class InMemoryCharacterRepository(CharacterRepository):
    def __init__(self):
        self._characters: Dict[str, Character] = {}
    
    def get(self, id: str) -> Optional[Character]:
        return self._characters.get(id)
    
    def save(self, character: Character) -> None:
        self._characters[character.name] = character</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>技术特性</h2>
                        <div class="features-section">
                            <div class="feature-item">
                                <h4><i class="fas fa-plug"></i> 插件化架构</h4>
                                <p>支持插件式扩展，可以动态加载和卸载组件。</p>
                            </div>
                            
                            <div class="feature-item">
                                <h4><i class="fas fa-sync"></i> 异步处理</h4>
                                <p>支持异步事件处理和I/O操作，提高系统性能。</p>
                            </div>
                            
                            <div class="feature-item">
                                <h4><i class="fas fa-shield-alt"></i> 错误处理</h4>
                                <p>统一的错误处理机制，支持错误恢复和重试。</p>
                            </div>
                            
                            <div class="feature-item">
                                <h4><i class="fas fa-chart-line"></i> 监控和指标</h4>
                                <p>内置监控和指标收集，支持性能分析和健康检查。</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 适配器层页面
    adaptersLayer: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">适配器层</h1>
                    <p class="card-subtitle">Adapters Layer - 外部系统集成和适配</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            适配器层负责与外部系统的集成，包括代理适配器、工具适配器、世界适配器等。实现新旧架构的平滑过渡。
                        </div>
                        
                        <h2>核心适配器</h2>
                        <div class="adapters-grid">
                            <div class="adapter-card">
                                <h3><i class="fas fa-robot"></i> 代理适配器</h3>
                                <p>将外部AI代理系统适配到内部架构，提供统一的代理接口。</p>
                                <div class="code-example">
                                    <div class="code-title">代理适配器接口</div>
                                    <pre><code class="language-python">class AgentAdapter(ABC):
    @abstractmethod
    def create_agent(self, config: AgentConfig) -> Agent:
        pass
    
    @abstractmethod
    def activate_agent(self, agent: Agent) -> None:
        pass
    
    @abstractmethod
    def get_response(self, agent: Agent, input_data: Any) -> Any:
        pass</code></pre>
                                </div>
                            </div>
                            
                            <div class="adapter-card">
                                <h3><i class="fas fa-tools"></i> 工具适配器</h3>
                                <p>将外部工具系统适配到内部架构，提供统一的工具调用接口。</p>
                                <div class="code-example">
                                    <div class="code-title">工具适配器接口</div>
                                    <pre><code class="language-python">class ToolAdapter(ABC):
    @abstractmethod
    def can_execute(self, tool_name: str) -> bool:
        pass
    
    @abstractmethod
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        pass</code></pre>
                                </div>
                            </div>
                            
                            <div class="adapter-card">
                                <h3><i class="fas fa-globe"></i> 世界适配器</h3>
                                <p>将外部世界系统适配到内部架构，提供统一的世界状态管理。</p>
                                <div class="code-example">
                                    <div class="code-title">世界适配器接口</div>
                                    <pre><code class="language-python">class WorldAdapter(ABC):
    @abstractmethod
    def get_world_state(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def update_world_state(self, updates: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    def get_character(self, name: str) -> Optional[Dict[str, Any]]:
        pass</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>新旧架构映射</h2>
                        <div class="mapping-section">
                            <p>适配器层实现了新旧架构之间的平滑过渡：</p>
                            <ul>
                                <li><strong>接口统一</strong>：为旧系统提供统一的接口</li>
                                <li><strong>数据转换</strong>：处理新旧数据格式转换</li>
                                <li><strong>事件桥接</strong>：将旧系统事件转换为新架构事件</li>
                                <li><strong>渐进迁移</strong>：支持逐步迁移到新架构</li>
                            </ul>
                            
                            <div class="code-example">
                                <div class="code-title">映射示例</div>
                                <pre><code class="language-python"># 旧系统工具调用映射
class LegacyToolAdapter(ToolAdapter):
    def __init__(self, legacy_tools: Dict[str, Any]):
        self.legacy_tools = legacy_tools
    
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        # 映射到旧系统工具名
        legacy_tool_name = self.map_tool_name(tool_name)
        
        # 转换参数格式
        legacy_params = self.convert_parameters(parameters)
        
        # 调用旧系统工具
        return self.legacy_tools[legacy_tool_name](**legacy_params)
    
    def map_tool_name(self, tool_name: str) -> str:
        mapping = {
            "create_character": "create_npc",
            "move_character": "move_npc",
            "attack_target": "npc_attack"
        }
        return mapping.get(tool_name, tool_name)</code></pre>
                            </div>
                        </div>
                        
                        <h2>集成点</h2>
                        <div class="integration-points">
                            <div class="integration-card">
                                <h4><i class="fas fa-plug"></i> Agentscope集成</h4>
                                <p>与Agentscope框架的集成，支持多种AI模型。</p>
                                <ul>
                                    <li>ReActAgent适配</li>
                                    <li>消息格式转换</li>
                                    <li>工具调用桥接</li>
                                </ul>
                            </div>
                            
                            <div class="integration-card">
                                <h4><i class="fas fa-database"></i> 数据存储集成</h4>
                                <p>与多种数据存储系统的集成。</p>
                                <ul>
                                    <li>内存存储</li>
                                    <li>文件存储</li>
                                    <li>数据库存储</li>
                                </ul>
                            </div>
                            
                            <div class="integration-card">
                                <h4><i class="fas fa-cloud"></i> 云服务集成</h4>
                                <p>与云服务API的集成。</p>
                                <ul>
                                    <li>LLM API集成</li>
                                    <li>文件存储服务</li>
                                    <li>监控和日志服务</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 消息处理器API文档
    messageHandler: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">消息处理器 API</h1>
                    <p class="card-subtitle">MessageHandlerService - 消息处理和工具调用服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            消息处理器服务负责处理游戏中的消息和工具调用，包括消息解析、工具调用识别和执行。支持复杂的消息处理逻辑。
                        </div>
                        
                        <h2>核心功能</h2>
                        <div class="features-grid">
                            <div class="feature-card">
                                <h3><i class="fas fa-envelope-open-text"></i> 消息解析</h3>
                                <p>解析消息内容，识别工具调用和自然语言部分。</p>
                                <div class="code-example">
                                    <div class="code-title">消息解析示例</div>
                                    <pre><code class="language-python">class MessageParser:
    def parse_message(self, content: str) -> ProcessedMessage:
        # 解析工具调用
        tool_calls = self._parse_tool_calls(content)
        
        # 清理消息内容
        cleaned_content = self._strip_tool_calls_from_text(content)
        
        return ProcessedMessage(
            original_content=content,
            cleaned_content=cleaned_content,
            tool_calls=tool_calls,
            sender=sender,
            metadata={}
        )</code></pre>
                                </div>
                            </div>
                            
                            <div class="feature-card">
                                <h3><i class="fas fa-tools"></i> 工具调用执行</h3>
                                <p>识别并执行工具调用，支持参数验证和错误处理。</p>
                                <div class="code-example">
                                    <div class="code-title">工具执行示例</div>
                                    <pre><code class="language-python">class ToolExecutor:
    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        # 验证工具调用
        validation = self._validate_tool_call(tool_call)
        if not validation.success:
            return ToolResult.failure(validation.message)
        
        # 执行工具
        try:
            result = self._execute_tool(tool_call.name, tool_call.parameters)
            return ToolResult.success(result)
        except Exception as e:
            return ToolResult.failure(str(e))</code></pre>
                                </div>
                            </div>
                            
                            <div class="feature-card">
                                <h3><i class="fas fa-shield-alt"></i> 安全验证</h3>
                                <p>验证工具调用的安全性，防止恶意调用。</p>
                                <div class="code-example">
                                    <div class="code-title">安全验证示例</div>
                                    <pre><code class="language-python">class SecurityValidator:
    def validate_tool_call(self, tool_call: ToolCall, caller: str) -> ValidationResult:
        # 检查调用者权限
        if not self._is_allowed_caller(caller):
            return ValidationResult.failure("无权限调用工具")
        
        # 检查工具名称
        if not self._is_allowed_tool(tool_call.name):
            return ValidationResult.failure("不允许的工具")
        
        # 检查参数安全性
        if self._has_malicious_params(tool_call.parameters):
            return ValidationResult.failure("参数包含恶意内容")
        
        return ValidationResult.success()</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>公共方法</h2>
                        
                        <div class="method-section">
                            <h3>process_message</h3>
                            <p>处理消息，解析工具调用并返回处理结果。</p>
                            
                            <div class="method-signature">
                                <div class="code-title">方法签名</div>
                                <pre><code class="language-python">def process_message(
    self,
    sender: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> CommandResult:</code></pre>
                            </div>
                            
                            <h4>参数</h4>
                            <table>
                                <thead>
                                    <tr>
                                        <th>参数名</th>
                                        <th>类型</th>
                                        <th>描述</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><code>sender</code></td>
                                        <td><code>str</code></td>
                                        <td>消息发送者</td>
                                    </tr>
                                    <tr>
                                        <td><code>content</code></td>
                                        <td><code>str</code></td>
                                        <td>消息内容</td>
                                    </tr>
                                    <tr>
                                        <td><code>metadata</code></td>
                                        <td><code>Optional[Dict[str, Any]]</code></td>
                                        <td>消息元数据</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <h4>返回值</h4>
                            <p><code>CommandResult</code> - 处理结果，包含清理后的内容和工具调用信息</p>
                            
                            <h4>示例</h4>
                            <div class="code-example">
                                <div class="code-title">使用示例</div>
                                <pre><code class="language-python"># 处理包含工具调用的消息
message_content = "我需要检查角色Amiya的状态。CALL_TOOL {"tool": "get_character", "params": {"name": "Amiya"}}"

result = message_handler.process_message("Player", message_content)
if result.success:
    print(f"清理后的内容: {result.data['cleaned_content']}")
    print(f"工具调用: {result.data['tool_calls']}")
else:
    print(f"处理失败: {result.message}")</code></pre>
                            </div>
                        </div>
                        
                        <div class="method-section">
                            <h3>execute_tool_calls</h3>
                            <p>执行消息中的工具调用。</p>
                            
                            <div class="method-signature">
                                <div class="code-title">方法签名</div>
                                <pre><code class="language-python">def execute_tool_calls(
    self,
    processed_message: ProcessedMessage
) -> CommandResult:</code></pre>
                            </div>
                            
                            <h4>参数</h4>
                            <table>
                                <thead>
                                    <tr>
                                        <th>参数名</th>
                                        <th>类型</th>
                                        <th>描述</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><code>processed_message</code></td>
                                        <td><code>ProcessedMessage</code></td>
                                        <td>处理后的消息对象</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <h4>返回值</h4>
                            <p><code>CommandResult</code> - 执行结果，包含所有工具调用的结果</p>
                        </div>
                        
                        <h2>工具调用格式</h2>
                        <div class="tool-format-section">
                            <p>消息处理器支持以下格式的工具调用：</p>
                            
                            <div class="code-example">
                                <div class="code-title">标准格式</div>
                                <pre><code class="language-text">CALL_TOOL {"tool": "工具名称", "params": {"参数1": "值1", "参数2": "值2"}}</code></pre>
                            </div>
                            
                            <div class="code-example">
                                <div class="code-title">嵌套在消息中</div>
                                <pre><code class="language-text">我想要移动角色Amiya到新位置。CALL_TOOL {"tool": "move_character", "params": {"name": "Amiya", "position": [5, 3]}} 请执行这个操作。</code></pre>
                            </div>
                            
                            <div class="code-example">
                                <div class="code-title">多个工具调用</div>
                                <pre><code class="language-text">我需要检查两个角色的状态。CALL_TOOL {"tool": "get_character", "params": {"name": "Amiya"}} CALL_TOOL {"tool": "get_character", "params": {"name": "Goblin"}} 请提供她们的状态信息。</code></pre>
                            </div>
                        </div>
                        
                        <h2>事件</h2>
                        <p>消息处理器服务会发布以下事件：</p>
                        
                        <div class="events-grid">
                            <div class="event-card">
                                <h4><i class="fas fa-envelope"></i> MessageReceivedEvent</h4>
                                <p>消息接收时发布</p>
                                <div class="event-data">
                                    <strong>数据:</strong>
                                    <ul>
                                        <li><code>sender</code> - 发送者</li>
                                        <li><code>content</code> - 消息内容</li>
                                        <li><code>metadata</code> - 元数据</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="event-card">
                                <h4><i class="fas fa-cogs"></i> MessageProcessedEvent</h4>
                                <p>消息处理完成时发布</p>
                                <div class="event-data">
                                    <strong>数据:</strong>
                                    <ul>
                                        <li><code>sender</code> - 发送者</li>
                                        <li><code>original_content</code> - 原始内容</li>
                                        <li><code>processed_content</code> - 处理后内容</li>
                                        <li><code>tool_calls</code> - 工具调用列表</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="event-card">
                                <h4><i class="fas fa-tools"></i> ToolCallEvent</h4>
                                <p>工具调用时发布</p>
                                <div class="event-data">
                                    <strong>数据:</strong>
                                    <ul>
                                        <li><code>tool_name</code> - 工具名称</li>
                                        <li><code>parameters</code> - 工具参数</li>
                                        <li><code>caller</code> - 调用者</li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="event-card">
                                <h4><i class="fas fa-check"></i> ToolCallResultEvent</h4>
                                <p>工具调用结果发布</p>
                                <div class="event-data">
                                    <strong>数据:</strong>
                                    <ul>
                                        <li><code>tool_name</code> - 工具名称</li>
                                        <li><code>result</code> - 执行结果</li>
                                        <li><code>success</code> - 是否成功</li>
                                        <li><code>error</code> - 错误信息</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 代理服务API文档
    agentService: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">代理服务 API</h1>
                    <p class="card-subtitle">AgentService - 代理(AI角色)管理服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            代理服务负责游戏中的代理(AI角色)管理，包括代理创建、状态管理和交互协调。支持多种类型的AI代理。
                        </div>
                        
                        <h2>核心功能</h2>
                        <div class="features-grid">
                            <div class="feature-card">
                                <h3><i class="fas fa-user-plus"></i> 代理创建</h3>
                                <p>根据配置创建不同类型的AI代理。</p>
                                <div class="code-example">
                                    <div class="code-title">代理创建示例</div>
                                    <pre><code class="language-python">class AgentFactory:
    def create_agent(self, config: AgentConfig) -> Agent:
        if config.agent_type == "react":
            return ReActAgent(config)
        elif config.agent_type == "function":
            return FunctionCallingAgent(config)
        else:
            raise ValueError(f"Unsupported agent type: {config.agent_type}")

# 创建代理配置
agent_config = AgentConfig(
    name="Amiya",
    persona="一位年轻的医生，充满同情心和责任感",
    model_config={"model": "gpt-3.5-turbo", "temperature": 0.7},
    tools=[get_character_tool, move_character_tool]
)

# 创建代理
agent = agent_factory.create_agent(agent_config)</code></pre>
                                </div>
                            </div>
                            
                            <div class="feature-card">
                                <h3><i class="fas fa-play-circle"></i> 代理激活</h3>
                                <p>激活代理，使其能够接收和处理消息。</p>
                                <div class="code-example">
                                    <div class="code-title">代理激活示例</div>
                                    <pre><code class="language-python">class AgentService:
    def activate_agent(self, agent_name: str, context: Dict[str, Any]) -> CommandResult:
        agent = self._agents.get(agent_name)
        if not agent:
            return CommandResult.failure(f"Agent {agent_name} not found")
        
        if agent.is_active():
            return CommandResult.failure(f"Agent {agent_name} is already active")
        
        # 激活代理
        asyncio.create_task(agent.activate(context))
        self._active_agents[agent_name] = agent
        
        return CommandResult.success_result(
            data={"agent_name": agent_name, "is_active": True}
        )

# 激活代理
context = {
    "world_state": world_service.get_world_state(),
    "current_turn": 1,
    "game_objectives": ["调查仓棚", "寻找线索"]
}

result = agent_service.activate_agent("Amiya", context)
if result.success:
    print(f"代理 {result.data['agent_name']} 已激活")
else:
    print(f"激活失败: {result.message}")</code></pre>
                                </div>
                            </div>
                            
                            <div class="feature-card">
                                <h3><i class="fas fa-comments"></i> 响应获取</h3>
                                <p>获取代理对输入的响应，支持异步处理。</p>
                                <div class="code-example">
                                    <div class="code-title">响应获取示例</div>
                                    <pre><code class="language-python">class AgentService:
    async def get_agent_response(
        self,
        agent_name: str,
        input_data: Any,
        timeout: Optional[int] = None
    ) -> CommandResult:
        agent = self._active_agents.get(agent_name)
        if not agent:
            return CommandResult.failure(f"Agent {agent_name} not active")
        
        timeout_duration = timeout or self._default_timeout
        
        try:
            # 获取响应（带超时）
            response = await asyncio.wait_for(
                agent.get_response(input_data),
                timeout=timeout_duration
            )
            
            return CommandResult.success_result(
                data={
                    "agent_name": agent_name,
                    "response": response,
                    "timeout_duration": timeout_duration
                }
            )
            
        except asyncio.TimeoutError:
            return CommandResult.failure(
                f"Agent {agent_name} response timeout after {timeout_duration}s"
            )

# 使用示例
input_data = {
    "message": "我需要检查角色的状态",
    "context": {
        "available_tools": ["get_character", "move_character"]
    }
}

# 获取代理响应
result = await agent_service.get_agent_response("Amiya", input_data, 30)
if result.success:
    print(f"Amiya的响应: {result.data['response']}")
else:
    print(f"获取响应失败: {result.message}")</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>代理配置</h2>
                        <div class="config-section">
                            <div class="code-example">
                                <div class="code-title">代理配置结构</div>
                                <pre><code class="language-python">@dataclass
class AgentConfig:
    name: str
    persona: str
    agent_type: str
    model_config: Dict[str, Any]
    tools: List[Any]
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>代理类型</h2>
                        <div class="agent-types-section">
                            <div class="agent-type-card">
                                <h4><i class="fas fa-robot"></i> ReActAgent</h4>
                                <p>基于推理和行动的代理，使用思维链进行决策。</p>
                                <ul>
                                    <li>支持复杂推理</li>
                                    <li>工具调用链式执行</li>
                                    <li>状态记忆能力</li>
                                </ul>
                            </div>
                            
                            <div class="agent-type-card">
                                <h4><i class="fas fa-code"></i> FunctionCallingAgent</h4>
                                <p>基于函数调用的代理，直接调用工具函数。</p>
                                <ul>
                                    <li>高效工具调用</li>
                                    <li>参数自动验证</li>
                                    <li>结果格式化</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
};
