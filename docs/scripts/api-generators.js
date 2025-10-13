// API文档生成器
window.apiGenerators = {
    // 游戏引擎API文档
    gameEngine: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">游戏引擎 API</h1>
                    <p class="card-subtitle">GameEngineService - 游戏核心逻辑协调服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            游戏引擎服务负责游戏的核心逻辑协调，包括游戏流程控制、状态管理和事件处理。
                        </div>
                        
                        <h2>服务概述</h2>
                        <p>GameEngineService是整个系统的核心协调器，负责：</p>
                        <ul>
                            <li>游戏流程的整体控制</li>
                            <li>协调各个应用服务</li>
                            <li>管理游戏状态和生命周期</li>
                            <li>处理游戏配置和初始化</li>
                        </ul>
                    </div>
                    
                    <h2>构造函数</h2>
                    <div class="method-signature">
                        <div class="code-title">构造函数</div>
                        <pre><code class="language-python">def __init__(
    self,
    event_bus: EventBus,
    logger: Logger,
    character_service: CharacterService,
    combat_service: CombatService,
    world_service: WorldService
) -> None:</code></pre>
                        
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
                                    <td><code>event_bus</code></td>
                                    <td><code>EventBus</code></td>
                                    <td>事件总线，用于发布领域事件</td>
                                </tr>
                                <tr>
                                    <td><code>logger</code></td>
                                    <td><code>Logger</code></td>
                                    <td>日志记录器</td>
                                </tr>
                                <tr>
                                    <td><code>character_service</code></td>
                                    <td><code>CharacterService</code></td>
                                    <td>角色服务，处理角色相关业务逻辑</td>
                                </tr>
                                <tr>
                                    <td><code>combat_service</code></td>
                                    <td><code>CombatService</code></td>
                                    <td>战斗服务，处理战斗相关业务逻辑</td>
                                </tr>
                                <tr>
                                    <td><code>world_service</code></td>
                                    <td><code>WorldService</code></td>
                                    <td>世界服务，处理世界状态管理</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <h2>公共方法</h2>
                    
                    <div class="method-section">
                        <h3>initialize_game</h3>
                        <p>初始化游戏，创建世界、角色和场景。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def initialize_game(
    self,
    game_config: Dict[str, Any],
    character_configs: Dict[str, Any],
    story_config: Dict[str, Any]
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
                                    <td><code>game_config</code></td>
                                    <td><code>Dict[str, Any]</code></td>
                                    <td>游戏配置，包含最大回合数、是否需要敌对关系等</td>
                                </tr>
                                <tr>
                                    <td><code>character_configs</code></td>
                                    <td><code>Dict[str, Any]</code></td>
                                    <td>角色配置，包含所有角色的属性和关系</td>
                                </tr>
                                <tr>
                                    <td><code>story_config</code></td>
                                    <td><code>Dict[str, Any]</code></td>
                                    <td>故事配置，包含场景信息和初始位置</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 初始化结果，包含成功状态和数据</p>
                        
                        <h4>示例</h4>
                        <div class="code-example">
                            <div class="code-title">使用示例</div>
                            <pre><code class="language-python"># 初始化游戏
game_config = {
    "max_rounds": 10,
    "require_hostiles": True
}

character_configs = {
    "Amiya": {
        "persona": "一位年轻的医生",
        "dnd": {
            "level": 1,
            "hp": 10,
            "abilities": {"STR": 8, "DEX": 14, "CON": 12}
        }
    }
}

story_config = {
    "scene": {
        "name": "旧城区·北侧仓棚",
        "time_min": 0,
        "weather": "晴朗"
    },
    "initial_positions": {
        "Amiya": [0, 0]
    }
}

result = game_engine.initialize_game(game_config, character_configs, story_config)
if result.success:
    print("游戏初始化成功")
else:
    print(f"初始化失败: {result.message}")</code></pre>
                        </div>
                    </div>
                    
                    <div class="method-section">
                        <h3>start_game</h3>
                        <p>开始游戏，发布游戏开始事件。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def start_game(self) -> CommandResult:</code></pre>
                        </div>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 开始结果，包含当前回合数</p>
                        
                        <h4>示例</h4>
                        <div class="code-example">
                            <div class="code-title">使用示例</div>
                            <pre><code class="language-python">result = game_engine.start_game()
if result.success:
    print(f"游戏开始，当前回合: {result.data['round']}")
else:
    print(f"开始游戏失败: {result.message}")</code></pre>
                        </div>
                    </div>
                    
                    <div class="method-section">
                        <h3>advance_round</h3>
                        <p>推进到下一回合，检查游戏结束条件。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def advance_round(self) -> CommandResult:</code></pre>
                        </div>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 推进结果，包含当前回合数</p>
                        
                        <h4>示例</h4>
                        <div class="code-example">
                            <div class="code-title">使用示例</div>
                            <pre><code class="language-python">result = game_engine.advance_round()
if result.success:
    print(f"回合 {result.data['round']} 开始")
else:
    print(f"推进回合失败: {result.message}")</code></pre>
                        </div>
                    </div>
                    
                    <div class="method-section">
                        <h3>get_game_state</h3>
                        <p>获取当前游戏状态。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def get_game_state(self) -> Dict[str, Any]:</code></pre>
                        </div>
                        
                        <h4>返回值</h4>
                        <p><code>Dict[str, Any]</code> - 游戏状态，包含以下字段：</p>
                        <ul>
                            <li><code>is_running</code> - 游戏是否正在运行</li>
                            <li><code>current_round</code> - 当前回合数</li>
                            <li><code>max_rounds</code> - 最大回合数</li>
                            <li><code>world_state</code> - 世界状态快照</li>
                            <li><code>combat_state</code> - 战斗状态快照</li>
                            <li><code>participants</code> - 活跃参与者列表</li>
                        </ul>
                        
                        <h4>示例</h4>
                        <div class="code-example">
                            <div class="code-title">使用示例</div>
                            <pre><code class="language-python">state = game_engine.get_game_state()
print(f"游戏运行状态: {state['is_running']}")
print(f"当前回合: {state['current_round']}")
print(f"参与者: {state['participants']}")</code></pre>
                        </div>
                    </div>
                    
                    <h2>事件</h2>
                    <p>游戏引擎服务会发布以下事件：</p>
                    
                    <div class="events-grid">
                        <div class="event-card">
                            <h4><i class="fas fa-play"></i> GameStartedEvent</h4>
                            <p>游戏开始时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>world_id</code> - 世界ID</li>
                                    <li><code>max_rounds</code> - 最大回合数</li>
                                    <li><code>require_hostiles</code> - 是否需要敌对关系</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-stop"></i> GameEndedEvent</h4>
                            <p>游戏结束时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>reason</code> - 结束原因</li>
                                    <li><code>final_state</code> - 最终状态</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-redo"></i> RoundStartedEvent</h4>
                            <p>回合开始时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>round_number</code> - 回合数</li>
                                    <li><code>participants</code> - 参与者列表</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-check"></i> RoundEndedEvent</h4>
                            <p>回合结束时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>round_number</code> - 回合数</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .api-overview {
                margin-bottom: 2rem;
            }
            
            .method-section {
                margin-bottom: 3rem;
                padding: 2rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .method-signature {
                margin: 1rem 0;
            }
            
            .method-section h3 {
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .code-example {
                margin: 1rem 0;
            }
            
            .events-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .event-card {
                padding: 1.5rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .event-card h4 {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 0 1rem 0;
                color: var(--text-primary);
            }
            
            .event-card h4 i {
                color: var(--primary-color);
            }
            
            .event-data {
                margin-top: 1rem;
                padding: 1rem;
                background-color: var(--bg-tertiary);
                border-radius: var(--radius-md);
            }
            
            .event-data strong {
                color: var(--text-primary);
            }
            
            .event-data ul {
                margin: 0.5rem 0 0 1rem;
            }
            
            .event-data li {
                margin-bottom: 0.25rem;
                font-family: var(--font-mono);
                font-size: var(--font-size-sm);
            }
            </style>
        `;
    },
    
    // 回合管理器API文档
    turnManager: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">回合管理器 API</h1>
                    <p class="card-subtitle">TurnManagerService - 游戏回合管理服务</p>
                </div>
                <div class="card-body">
                    <div class="api-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            回合管理器服务负责游戏回合的管理，包括回合流程控制、角色行动顺序维护和状态跟踪。
                        </div>
                        
                        <h2>服务概述</h2>
                        <p>TurnManagerService专门负责回合管理，包括：</p>
                        <ul>
                            <li>回合流程的控制和管理</li>
                            <li>角色行动顺序的维护</li>
                            <li>回合状态的跟踪</li>
                            <li>行动超时的处理</li>
                        </ul>
                    </div>
                    
                    <h2>核心类</h2>
                    
                    <div class="class-section">
                        <h3>TurnContext</h3>
                        <p>回合上下文，封装回合执行过程中的上下文信息。</p>
                        
                        <div class="code-example">
                            <div class="code-title">TurnContext定义</div>
                            <pre><code class="language-python">@dataclass
class TurnContext:
    character_name: str
    turn_number: int
    round_number: int
    start_time: datetime
    timeout_duration: int = 30
    is_skipped: bool = False
    skip_reason: Optional[str] = None
    actions_taken: List[str] = None</code></pre>
                        </div>
                        
                        <h4>方法</h4>
                        <ul>
                            <li><code>add_action(action: str) -> None</code> - 添加行动记录</li>
                            <li><code>skip(reason: str) -> None</code> - 跳过回合</li>
                            <li><code>is_timeout() -> bool</code> - 检查是否超时</li>
                        </ul>
                    </div>
                    
                    <h2>公共方法</h2>
                    
                    <div class="method-section">
                        <h3>start_turn</h3>
                        <p>开始角色回合，创建回合上下文。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def start_turn(
    self,
    character_name: str,
    turn_number: int,
    round_number: int
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
                                    <td><code>character_name</code></td>
                                    <td><code>str</code></td>
                                    <td>角色名称</td>
                                </tr>
                                <tr>
                                    <td><code>turn_number</code></td>
                                    <td><code>int</code></td>
                                    <td>回合数</td>
                                </tr>
                                <tr>
                                    <td><code>round_number</code></td>
                                    <td><code>int</code></td>
                                    <td>轮次数</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 开始结果，包含回合上下文信息</p>
                    </div>
                    
                    <div class="method-section">
                        <h3>complete_turn</h3>
                        <p>完成当前回合，记录执行的行动。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def complete_turn(
    self,
    actions: Optional[List[str]] = None
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
                                    <td><code>actions</code></td>
                                    <td><code>Optional[List[str]]</code></td>
                                    <td>执行的行动列表</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 完成结果，包含行动记录和持续时间</p>
                    </div>
                    
                    <div class="method-section">
                        <h3>check_timeout</h3>
                        <p>检查当前回合是否超时。</p>
                        
                        <div class="method-signature">
                            <div class="code-title">方法签名</div>
                            <pre><code class="language-python">def check_timeout(self) -> CommandResult:</code></pre>
                        </div>
                        
                        <h4>返回值</h4>
                        <p><code>CommandResult</code> - 检查结果，包含剩余时间或超时信息</p>
                    </div>
                    
                    <h2>事件</h2>
                    <p>回合管理器服务会发布以下事件：</p>
                    
                    <div class="events-grid">
                        <div class="event-card">
                            <h4><i class="fas fa-play"></i> TurnStartedEvent</h4>
                            <p>回合开始时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>character_name</code> - 角色名称</li>
                                    <li><code>turn_number</code> - 回合数</li>
                                    <li><code>state</code> - 回合状态</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-check"></i> TurnCompletedEvent</h4>
                            <p>回合完成时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>character_name</code> - 角色名称</li>
                                    <li><code>turn_number</code> - 回合数</li>
                                    <li><code>actions</code> - 执行的行动</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-forward"></i> TurnSkippedEvent</h4>
                            <p>回合跳过时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>character_name</code> - 角色名称</li>
                                    <li><code>turn_number</code> - 回合数</li>
                                    <li><code>reason</code> - 跳过原因</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="event-card">
                            <h4><i class="fas fa-clock"></i> TurnTimeoutEvent</h4>
                            <p>回合超时时发布</p>
                            <div class="event-data">
                                <strong>数据:</strong>
                                <ul>
                                    <li><code>character_name</code> - 角色名称</li>
                                    <li><code>turn_number</code> - 回合数</li>
                                    <li><code>timeout_duration</code> - 超时时长</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
};