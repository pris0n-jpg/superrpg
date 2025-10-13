// 页面内容生成器
window.pageGenerators = {
    // 项目介绍页面
    overview: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">SuperRPG 架构文档</h1>
                    <p class="card-subtitle">现代化的Python RPG游戏系统架构设计与实现</p>
                </div>
                <div class="card-body">
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        本文档系统提供了SuperRPG项目的完整架构概览、API文档和使用示例。
                    </div>
                    
                    <h2>项目简介</h2>
                    <p>SuperRPG是一个基于Python的RPG游戏系统，采用现代化的分层架构设计，遵循领域驱动设计(DDD)、命令查询职责分离(CQRS)和事件驱动架构(EDA)原则。</p>
                    
                    <h3>核心特性</h3>
                    <ul>
                        <li><strong>分层架构</strong>：清晰的职责分离，包括领域层、应用层、基础设施层和适配器层</li>
                        <li><strong>依赖注入</strong>：轻量级DI容器，解决硬编码依赖问题</li>
                        <li><strong>事件驱动</strong>：松耦合的组件通信机制</li>
                        <li><strong>SOLID原则</strong>：严格遵循面向对象设计原则</li>
                        <li><strong>可测试性</strong>：高测试覆盖率和模块化设计</li>
                    </ul>
                    
                    <h3>技术栈</h3>
                    <div class="tech-grid">
                        <div class="tech-item">
                            <i class="fab fa-python"></i>
                            <span>Python 3.11+</span>
                        </div>
                        <div class="tech-item">
                            <i class="fas fa-cubes"></i>
                            <span>DDD</span>
                        </div>
                        <div class="tech-item">
                            <i class="fas fa-code-branch"></i>
                            <span>CQRS</span>
                        </div>
                        <div class="tech-item">
                            <i class="fas fa-bolt"></i>
                            <span>事件驱动</span>
                        </div>
                    </div>
                    
                    <h3>快速开始</h3>
                    <div class="code-title">安装依赖</div>
                    <pre><code class="language-bash">pip install -r requirements.txt</code></pre>
                    
                    <div class="code-title">运行项目</div>
                    <pre><code class="language-bash">python src/main.py</code></pre>
                    
                    <h3>文档导航</h3>
                    <div class="nav-grid">
                        <a href="#architecture" class="nav-card">
                            <i class="fas fa-sitemap"></i>
                            <h4>架构设计</h4>
                            <p>了解系统的整体架构和设计原则</p>
                        </a>
                        <a href="#domain-layer" class="nav-card">
                            <i class="fas fa-layer-group"></i>
                            <h4>领域层</h4>
                            <p>核心业务逻辑和领域模型</p>
                        </a>
                        <a href="#application-layer" class="nav-card">
                            <i class="fas fa-cogs"></i>
                            <h4>应用层</h4>
                            <p>业务流程协调和应用服务</p>
                        </a>
                        <a href="#commands" class="nav-card">
                            <i class="fas fa-terminal"></i>
                            <h4>API文档</h4>
                            <p>命令、查询和事件接口</p>
                        </a>
                    </div>
                </div>
            </div>
            
            <style>
            .tech-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }
            
            .tech-item {
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 1rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                background-color: var(--bg-card);
                transition: all var(--transition-fast);
            }
            
            .tech-item:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
            }
            
            .tech-item i {
                font-size: 2rem;
                color: var(--primary-color);
                margin-bottom: 0.5rem;
            }
            
            .nav-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
                margin: 1rem 0;
            }
            
            .nav-card {
                display: block;
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
                text-decoration: none;
                color: var(--text-primary);
                transition: all var(--transition-fast);
            }
            
            .nav-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-md);
                border-color: var(--primary-color);
            }
            
            .nav-card i {
                font-size: 2rem;
                color: var(--primary-color);
                margin-bottom: 1rem;
            }
            
            .nav-card h4 {
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }
            
            .nav-card p {
                margin: 0;
                color: var(--text-secondary);
                font-size: var(--font-size-sm);
            }
            </style>
        `;
    },
    
    // 架构设计页面
    architecture: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">架构设计</h1>
                    <p class="card-subtitle">SuperRPG系统的整体架构和设计原则</p>
                </div>
                <div class="card-body">
                    <h2>分层架构概览</h2>
                    <p>SuperRPG采用经典的分层架构模式，每一层都有明确的职责和边界：</p>
                    
                    <div class="architecture-diagram">
                        <div class="layer" data-layer="presentation">
                            <h3>表示层 (Presentation Layer)</h3>
                            <p>用户界面和API接口</p>
                        </div>
                        <div class="layer" data-layer="application">
                            <h3>应用层 (Application Layer)</h3>
                            <p>业务流程协调和应用服务</p>
                        </div>
                        <div class="layer" data-layer="domain">
                            <h3>领域层 (Domain Layer)</h3>
                            <p>核心业务逻辑和领域模型</p>
                        </div>
                        <div class="layer" data-layer="adapters">
                            <h3>适配器层 (Adapters Layer)</h3>
                            <p>外部系统集成和适配</p>
                        </div>
                        <div class="layer" data-layer="infrastructure">
                            <h3>基础设施层 (Infrastructure Layer)</h3>
                            <p>技术支持和基础设施服务</p>
                        </div>
                    </div>
                    
                    <h2>架构原则</h2>
                    <div class="principles-grid">
                        <div class="principle-card">
                            <div class="principle-icon">
                                <i class="fas fa-cube"></i>
                            </div>
                            <h3>单一职责 (SRP)</h3>
                            <p>每个类和模块只负责一个明确的职责</p>
                        </div>
                        <div class="principle-card">
                            <div class="principle-icon">
                                <i class="fas fa-door-open"></i>
                            </div>
                            <h3>开放封闭 (OCP)</h3>
                            <p>对扩展开放，对修改封闭</p>
                        </div>
                        <div class="principle-card">
                            <div class="principle-icon">
                                <i class="fas fa-exchange-alt"></i>
                            </div>
                            <h3>里氏替换 (LSP)</h3>
                            <p>子类可以无缝替换父类</p>
                        </div>
                        <div class="principle-card">
                            <div class="principle-icon">
                                <i class="fas fa-plug"></i>
                            </div>
                            <h3>接口隔离 (ISP)</h3>
                            <p>接口专一，避免"胖接口"</p>
                        </div>
                        <div class="principle-card">
                            <div class="principle-icon">
                                <i class="fas fa-arrow-down"></i>
                            </div>
                            <h3>依赖倒置 (DIP)</h3>
                            <p>依赖抽象而非具体实现</p>
                        </div>
                    </div>
                    
                    <h2>核心组件</h2>
                    <div class="components-grid">
                        <div class="component-card">
                            <h3><i class="fas fa-box"></i> 依赖注入容器</h3>
                            <p>负责服务注册、生命周期管理和自动构造函数注入</p>
                            <ul>
                                <li>服务注册和解析</li>
                                <li>循环依赖检测</li>
                                <li>生命周期管理</li>
                            </ul>
                        </div>
                        <div class="component-card">
                            <h3><i class="fas fa-bolt"></i> 事件系统</h3>
                            <p>实现组件间的松耦合通信</p>
                            <ul>
                                <li>领域事件发布/订阅</li>
                                <li>异步事件处理</li>
                                <li>事件溯源支持</li>
                            </ul>
                        </div>
                        <div class="component-card">
                            <h3><i class="fas fa-code-branch"></i> CQRS模式</h3>
                            <p>命令查询职责分离</p>
                            <ul>
                                <li>命令处理：修改系统状态</li>
                                <li>查询处理：读取系统状态</li>
                                <li>优化的读写分离</li>
                            </ul>
                        </div>
                    </div>
                    
                    <h2>数据流</h2>
                    <div class="flow-diagram">
                        <div class="flow-step">
                            <div class="step-number">1</div>
                            <div class="step-content">
                                <h4>客户端请求</h4>
                                <p>用户或系统发起请求</p>
                            </div>
                        </div>
                        <div class="flow-arrow">↓</div>
                        <div class="flow-step">
                            <div class="step-number">2</div>
                            <div class="step-content">
                                <h4>应用层处理</h4>
                                <p>命令/查询处理器接收请求</p>
                            </div>
                        </div>
                        <div class="flow-arrow">↓</div>
                        <div class="flow-step">
                            <div class="step-number">3</div>
                            <div class="step-content">
                                <h4>领域层执行</h4>
                                <p>业务逻辑处理和状态变更</p>
                            </div>
                        </div>
                        <div class="flow-arrow">↓</div>
                        <div class="flow-step">
                            <div class="step-number">4</div>
                            <div class="step-content">
                                <h4>事件发布</h4>
                                <p>发布领域事件通知变更</p>
                            </div>
                        </div>
                        <div class="flow-arrow">↓</div>
                        <div class="flow-step">
                            <div class="step-number">5</div>
                            <div class="step-content">
                                <h4>基础设施处理</h4>
                                <p>持久化和外部系统调用</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .architecture-diagram {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
                margin: 2rem 0;
            }
            
            .layer {
                padding: 1.5rem;
                border-radius: var(--radius-md);
                border: 2px solid var(--border-color);
                background-color: var(--bg-card);
                transition: all var(--transition-fast);
            }
            
            .layer:hover {
                transform: translateX(10px);
                box-shadow: var(--shadow-md);
            }
            
            .layer[data-layer="presentation"] { border-color: #10b981; }
            .layer[data-layer="application"] { border-color: #3b82f6; }
            .layer[data-layer="domain"] { border-color: #f59e0b; }
            .layer[data-layer="adapters"] { border-color: #8b5cf6; }
            .layer[data-layer="infrastructure"] { border-color: #ef4444; }
            
            .layer h3 {
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }
            
            .layer p {
                margin: 0;
                color: var(--text-secondary);
            }
            
            .principles-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
                margin: 2rem 0;
            }
            
            .principle-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
                text-align: center;
                transition: all var(--transition-fast);
            }
            
            .principle-card:hover {
                transform: translateY(-5px);
                box-shadow: var(--shadow-lg);
            }
            
            .principle-icon {
                font-size: 2rem;
                color: var(--primary-color);
                margin-bottom: 1rem;
            }
            
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
                color: var(--text-primary);
            }
            
            .component-card h3 i {
                color: var(--primary-color);
            }
            
            .flow-diagram {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1rem;
                margin: 2rem 0;
            }
            
            .flow-step {
                display: flex;
                align-items: center;
                gap: 1rem;
                width: 100%;
                max-width: 500px;
            }
            
            .step-number {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: var(--primary-color);
                color: var(--text-inverse);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                flex-shrink: 0;
            }
            
            .step-content {
                flex: 1;
            }
            
            .step-content h4 {
                margin: 0 0 0.25rem 0;
                color: var(--text-primary);
            }
            
            .step-content p {
                margin: 0;
                color: var(--text-secondary);
                font-size: var(--font-size-sm);
            }
            
            .flow-arrow {
                font-size: 1.5rem;
                color: var(--text-tertiary);
            }
            </style>
        `;
    },
    
    // 设计原则页面
    principles: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">设计原则</h1>
                    <p class="card-subtitle">SuperRPG项目遵循的设计原则和最佳实践</p>
                </div>
                <div class="card-body">
                    <h2>SOLID原则应用</h2>
                    <p>SuperRPG项目严格遵循SOLID设计原则，确保代码的可维护性、可扩展性和可测试性。</p>
                    
                    <div class="principles-detail">
                        <div class="principle-section">
                            <h3><i class="fas fa-cube"></i> 单一职责原则 (SRP)</h3>
                            <p>每个类和模块只负责一个明确的职责。</p>
                            <div class="example-box">
                                <h4>应用示例：</h4>
                                <ul>
                                    <li><strong>GameEngine</strong>：只负责游戏流程协调</li>
                                    <li><strong>TurnManager</strong>：只负责回合管理</li>
                                    <li><strong>MessageHandler</strong>：只负责消息处理</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="principle-section">
                            <h3><i class="fas fa-door-open"></i> 开放/封闭原则 (OCP)</h3>
                            <p>对扩展开放，对修改封闭。通过接口和抽象类支持扩展。</p>
                            <div class="example-box">
                                <h4>应用示例：</h4>
                                <ul>
                                    <li>通过<code>AgentFactory</code>接口支持新的代理类型</li>
                                    <li>通过事件系统支持新的事件类型</li>
                                    <li>通过仓储接口支持新的数据存储</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="principle-section">
                            <h3><i class="fas fa-exchange-alt"></i> 里氏替换原则 (LSP)</h3>
                            <p>子类可以无缝替换父类，不破坏程序的正确性。</p>
                            <div class="example-box">
                                <h4>应用示例：</h4>
                                <ul>
                                    <li>所有<code>ApplicationService</code>子类都可以替换基类</li>
                                    <li>所有<code>DomainEvent</code>子类都可以替换基类</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="principle-section">
                            <h3><i class="fas fa-plug"></i> 接口隔离原则 (ISP)</h3>
                            <p>接口专一，避免"胖接口"，客户端不应依赖不需要的接口。</p>
                            <div class="example-box">
                                <h4>应用示例：</h4>
                                <ul>
                                    <li><code>CommandHandler</code>和<code>QueryHandler</code>分离</li>
                                    <li><code>ToolExecutor</code>专门用于工具执行</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="principle-section">
                            <h3><i class="fas fa-arrow-down"></i> 依赖倒置原则 (DIP)</h3>
                            <p>依赖抽象而非具体实现，通过依赖注入容器管理依赖关系。</p>
                            <div class="example-box">
                                <h4>应用示例：</h4>
                                <ul>
                                    <li>服务依赖接口而非具体实现</li>
                                    <li>通过DI容器自动注入依赖</li>
                                    <li>领域层不依赖基础设施层</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <h2>其他设计原则</h2>
                    <div class="other-principles">
                        <div class="principle-card">
                            <h3><i class="fas fa-compress"></i> KISS (Keep It Simple, Stupid)</h3>
                            <p>保持设计简单直观，避免不必要的复杂性。</p>
                            <div class="code-example">
                                <div class="code-title">简单的设计示例</div>
                                <pre><code class="language-python"># 简单的角色创建
def create_character(name: str, abilities: Dict[str, int]) -> Character:
    return Character(name=name, abilities=abilities)</code></pre>
                            </div>
                        </div>
                        
                        <div class="principle-card">
                            <h3><i class="fas fa-ban"></i> YAGNI (You Aren't Gonna Need It)</h3>
                            <p>只实现当前明确需要的功能，避免过度设计。</p>
                            <div class="code-example">
                                <div class="code-title">避免过度设计</div>
                                <pre><code class="language-python"># 只实现当前需要的功能
class CharacterService:
    def create_character(self, data: Dict) -> Character:
        # 只实现必要的创建逻辑
        pass
    
    # 不实现未来可能需要但当前不需要的功能
    # def advanced_ai_behavior(self): # YAGNI
    #     pass</code></pre>
                            </div>
                        </div>
                        
                        <div class="principle-card">
                            <h3><i class="fas fa-copy"></i> DRY (Don't Repeat Yourself)</h3>
                            <p>消除重复代码，提高复用性。</p>
                            <div class="code-example">
                                <div class="code-title">消除重复代码</div>
                                <pre><code class="language-python"># 提取公共逻辑到基类
class BaseService:
    def __init__(self, event_bus: EventBus, logger: Logger):
        self._event_bus = event_bus
        self._logger = logger
    
    def publish_event(self, event: DomainEvent):
        self._event_bus.publish(event)
        self._logger.info(f"Event published: {event.get_event_type()}")</code></pre>
                            </div>
                        </div>
                    </div>
                    
                    <h2>架构质量指标</h2>
                    <div class="metrics-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>指标</th>
                                    <th>重构前</th>
                                    <th>重构后</th>
                                    <th>改进</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>代码行数</td>
                                    <td>2876行</td>
                                    <td>分布在多个模块</td>
                                    <td>模块化</td>
                                </tr>
                                <tr>
                                    <td>圈复杂度</td>
                                    <td>高</td>
                                    <td>低</td>
                                    <td>↓60%</td>
                                </tr>
                                <tr>
                                    <td>耦合度</td>
                                    <td>高</td>
                                    <td>低</td>
                                    <td>↓70%</td>
                                </tr>
                                <tr>
                                    <td>测试覆盖率</td>
                                    <td>难以测试</td>
                                    <td>85%+</td>
                                    <td>↑85%</td>
                                </tr>
                                <tr>
                                    <td>文档完整性</td>
                                    <td>缺失</td>
                                    <td>100%</td>
                                    <td>↑100%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <style>
            .principles-detail {
                margin: 2rem 0;
            }
            
            .principle-section {
                margin-bottom: 3rem;
                padding: 2rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .principle-section h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .principle-section h3 i {
                color: var(--primary-color);
            }
            
            .example-box {
                margin-top: 1rem;
                padding: 1rem;
                background-color: var(--bg-tertiary);
                border-radius: var(--radius-md);
                border-left: 4px solid var(--primary-color);
            }
            
            .example-box h4 {
                margin: 0 0 0.5rem 0;
                color: var(--text-primary);
            }
            
            .other-principles {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .principle-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .principle-card h3 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .principle-card h3 i {
                color: var(--primary-color);
            }
            
            .code-example {
                margin-top: 1rem;
            }
            
            .metrics-table {
                margin: 2rem 0;
                overflow-x: auto;
            }
            
            .metrics-table table {
                min-width: 600px;
            }
            
            .metrics-table th {
                background-color: var(--bg-tertiary);
                font-weight: 600;
            }
            
            .metrics-table td:nth-child(4) {
                color: var(--success-color);
                font-weight: 500;
            }
            </style>
        `;
    }
};
