// 扩展页面内容生成器
window.pageGeneratorsExtended = {
    // 领域层页面
    domainLayer: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">领域层</h1>
                    <p class="card-subtitle">Domain Layer - 核心业务逻辑和领域模型</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            领域层是整个架构的核心，包含了业务逻辑、领域模型和领域服务。它独立于基础设施和应用层，专注于表达业务概念和规则。
                        </div>
                        
                        <h2>核心实体</h2>
                        <div class="entities-grid">
                            <div class="entity-card">
                                <h3><i class="fas fa-user"></i> 角色 (Character)</h3>
                                <p>游戏中的核心实体，包含角色的所有属性和行为。</p>
                                <div class="code-example">
                                    <div class="code-title">角色模型定义</div>
                                    <pre><code class="language-python">@dataclass
class Character(AggregateRoot):
    name: str
    abilities: Abilities
    stats: CharacterStats
    hp: int
    max_hp: int
    position: Optional[Position] = None</code></pre>
                                </div>
                            </div>
                            
                            <div class="entity-card">
                                <h3><i class="fas fa-sword"></i> 战斗 (Combat)</h3>
                                <p>战斗状态和规则管理，处理战斗相关的业务逻辑。</p>
                                <div class="code-example">
                                    <div class="code-title">战斗状态定义</div>
                                    <pre><code class="language-python">@dataclass
class CombatState(AggregateRoot):
    in_combat: bool = False
    round: int = 1
    turn_idx: int = 0
    initiative_order: List[str] = field(default_factory=list)</code></pre>
                                </div>
                            </div>
                            
                            <div class="entity-card">
                                <h3><i class="fas fa-globe"></i> 世界 (World)</h3>
                                <p>世界状态管理，包含场景、时间、天气等信息。</p>
                                <div class="code-example">
                                    <div class="code-title">世界模型定义</div>
                                    <pre><code class="language-python">@dataclass
class World(AggregateRoot):
    id: str
    name: str
    time_min: int = 0
    weather: str = "晴朗"
    location: str = "未知地点"</code></pre>
                                </div>
                            </div>
                        </div>
                        
                        <h2>领域服务</h2>
                        <div class="services-grid">
                            <div class="service-card">
                                <h3><i class="fas fa-user-cog"></i> CharacterService</h3>
                                <p>角色领域服务，处理角色相关的业务逻辑。</p>
                                <ul>
                                    <li>从D&D配置创建角色</li>
                                    <li>角色状态管理</li>
                                    <li>角色属性计算</li>
                                </ul>
                            </div>
                            
                            <div class="service-card">
                                <h3><i class="fas fa-shield-alt"></i> CombatService</h3>
                                <p>战斗领域服务，处理战斗相关的业务规则。</p>
                                <ul>
                                    <li>攻击解析和伤害计算</li>
                                    <li>战斗状态管理</li>
                                    <li>战斗规则执行</li>
                                </ul>
                            </div>
                            
                            <div class="service-card">
                                <h3><i class="fas fa-map"></i> WorldService</h3>
                                <p>世界领域服务，处理世界状态和规则。</p>
                                <ul>
                                    <li>世界创建和初始化</li>
                                    <li>场景管理</li>
                                    <li>关系网络管理</li>
                                </ul>
                            </div>
                        </div>
                        
                        <h2>设计原则应用</h2>
                        <div class="principles-section">
                            <div class="principle-item">
                                <h4><i class="fas fa-cube"></i> 单一职责原则 (SRP)</h4>
                                <p>每个领域模型只负责一个业务概念，领域服务专注于特定的业务逻辑。</p>
                            </div>
                            
                            <div class="principle-item">
                                <h4><i class="fas fa-door-open"></i> 开放/封闭原则 (OCP)</h4>
                                <p>通过接口和抽象类支持扩展，新的业务规则可以通过新的领域服务添加。</p>
                            </div>
                            
                            <div class="principle-item">
                                <h4><i class="fas fa-arrow-down"></i> 依赖倒置原则 (DIP)</h4>
                                <p>领域层不依赖基础设施层，通过仓储接口抽象数据访问。</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .entities-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .entity-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .entity-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--primary-color);
            }
            
            .entity-card h3 i {
                color: var(--primary-color);
            }
            
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .service-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .service-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--primary-color);
            }
            
            .service-card h3 i {
                color: var(--primary-color);
            }
            
            .service-card ul {
                margin: 0;
                padding-left: 1.5rem;
            }
            
            .service-card li {
                margin-bottom: 0.5rem;
                color: var(--text-secondary);
            }
            
            .principles-section {
                margin: 2rem 0;
            }
            
            .principle-item {
                margin-bottom: 2rem;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .principle-item h4 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .principle-item h4 i {
                color: var(--primary-color);
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
            
            <style>
            .cqrs-section {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .cqrs-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .cqrs-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--primary-color);
            }
            
            .cqrs-card h3 i {
                color: var(--primary-color);
            }
            
            .event-section {
                margin: 2rem 0;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .event-section ul {
                margin: 1rem 0;
                padding-left: 1.5rem;
            }
            
            .event-section li {
                margin-bottom: 0.5rem;
                color: var(--text-secondary);
            }
            </style>
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
            
            <style>
            .components-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .component-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .component-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--primary-color);
            }
            
            .component-card h3 i {
                color: var(--primary-color);
            }
            
            .features-section {
                margin: 2rem 0;
            }
            
            .feature-item {
                margin-bottom: 2rem;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .feature-item h4 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .feature-item h4 i {
                color: var(--primary-color);
            }
            </style>
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
            
            <style>
            .adapters-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .adapter-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .adapter-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--primary-color);
            }
            
            .adapter-card h3 i {
                color: var(--primary-color);
            }
            
            .mapping-section {
                margin: 2rem 0;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .mapping-section ul {
                margin: 1rem 0;
                padding-left: 1.5rem;
            }
            
            .mapping-section li {
                margin-bottom: 0.5rem;
                color: var(--text-secondary);
            }
            
            .integration-points {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .integration-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .integration-card h4 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .integration-card h4 i {
                color: var(--primary-color);
            }
            
            .integration-card ul {
                margin: 0;
                padding-left: 1.5rem;
            }
            
            .integration-card li {
                margin-bottom: 0.5rem;
                color: var(--text-secondary);
            }
            </style>
        `;
    }
};

// 扩展原有的页面生成器
if (window.pageGenerators) {
    Object.assign(window.pageGenerators, window.pageGeneratorsExtended);
}