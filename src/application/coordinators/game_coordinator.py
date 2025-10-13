"""
游戏协调器

该模块实现了游戏协调器，负责协调多个应用服务之间的交互，
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

游戏协调器负责：
1. 协调游戏引擎服务、回合管理服务、消息处理服务和代理服务
2. 管理游戏的整体流程
3. 处理服务间的依赖关系
4. 确保游戏流程的一致性和完整性
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable, Mapping
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..services.base import ApplicationService, CommandResult
from ..services.game_engine import GameEngineService
from ..services.turn_manager import TurnManagerService
from ..services.message_handler import MessageHandlerService
from ..services.agent_service import AgentService
from ..commands.character_commands import CharacterCommandHandler
from ..commands.world_commands import WorldCommandHandler
from ..queries.character_queries import CharacterQueryHandler
from ..queries.world_queries import WorldQueryHandler
from ...core.interfaces import EventBus, Logger, DomainEvent, GameCoordinator as IGameCoordinator
from ...core.exceptions import ApplicationException, BusinessRuleException
from ...core.container import DIContainer


class GameCoordinator(IGameCoordinator):
    """游戏协调器
    
    负责协调游戏的所有应用服务，管理游戏的整体流程和服务间的交互。
    遵循单一职责原则，专门负责游戏协调的核心功能。
    """
    
    def __init__(
        self,
        game_engine: GameEngineService,
        turn_manager: TurnManagerService,
        message_handler: MessageHandlerService,
        agent_service: AgentService,
        character_command_handler: CharacterCommandHandler,
        world_command_handler: WorldCommandHandler,
        character_query_handler: CharacterQueryHandler,
        world_query_handler: WorldQueryHandler,
        event_bus: EventBus,
        logger: Logger,
        container: DIContainer
    ):
        """初始化游戏协调器
        
        Args:
            game_engine: 游戏引擎服务
            turn_manager: 回合管理服务
            message_handler: 消息处理服务
            agent_service: 代理服务
            character_command_handler: 角色命令处理器
            world_command_handler: 世界命令处理器
            character_query_handler: 角色查询处理器
            world_query_handler: 世界查询处理器
            event_bus: 事件总线
            logger: 日志记录器
            container: 依赖注入容器
        """
        self._game_engine = game_engine
        self._turn_manager = turn_manager
        self._message_handler = message_handler
        self._agent_service = agent_service
        self._character_command_handler = character_command_handler
        self._world_command_handler = world_command_handler
        self._character_query_handler = character_query_handler
        self._world_query_handler = world_query_handler
        self._event_bus = event_bus
        self._logger = logger
        self._container = container
        
        self._is_initialized = False
        self._is_running = False
        self._game_config: Optional[Dict[str, Any]] = None
    
    def initialize_game(
        self,
        game_config: Dict[str, Any],
        character_configs: Dict[str, Any],
        story_config: Dict[str, Any],
        model_config: Dict[str, Any],
        tools: List[Any],
        agent_factory: Callable
    ) -> CommandResult:
        """初始化游戏
        
        Args:
            game_config: 游戏配置
            character_configs: 角色配置
            story_config: 故事配置
            model_config: 模型配置
            tools: 工具列表
            agent_factory: 代理工厂函数
            
        Returns:
            CommandResult: 初始化结果
        """
        try:
            self._logger.debug("Initializing game through coordinator")
            
            # 保存游戏配置
            self._game_config = game_config
            
            # 初始化游戏引擎
            engine_result = self._game_engine.initialize_game(
                game_config=game_config,
                character_configs=character_configs,
                story_config=story_config
            )
            
            if not engine_result.success:
                return engine_result
            
            # 创建代理
            agent_result = self._agent_service.create_agents_from_character_configs(
                character_configs=character_configs,
                story_config=story_config,
                model_config=model_config,
                tools=tools,
                factory=agent_factory
            )
            
            if not agent_result.success:
                return agent_result
            
            # 设置消息处理服务的允许名称
            participants = self._extract_participants(story_config)
            self._message_handler.set_allowed_names(participants)
            
            # 订阅事件
            self._subscribe_to_events()
            
            self._is_initialized = True
            
            self._logger.debug("Game initialized through coordinator")
            
            return CommandResult.success_result(
                data={
                    "engine_result": engine_result.data,
                    "agent_result": agent_result.data,
                    "participants": participants
                },
                message="Game initialized successfully through coordinator"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to initialize game through coordinator: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game initialization failed: {str(e)}", cause=e)
            )
    
    async def start_game(self) -> CommandResult:
        """开始游戏
        
        Returns:
            CommandResult: 开始结果
        """
        if not self._is_initialized:
            return CommandResult.failure_result(
                ApplicationException("Game not initialized")
            )
        
        try:
            self._logger.debug("Starting game through coordinator")
            
            # 控制台输出游戏开始
            print("\n" + "="*60)
            print("游戏开始！")
            print("="*60 + "\n")
            
            # 启动游戏引擎
            engine_result = self._game_engine.start_game()
            if not engine_result.success:
                return engine_result
            
            self._is_running = True
            
            # 移除重复的日志记录，让game_engine处理
            # self._logger.info("Game started through coordinator")
            
            return CommandResult.success_result(
                data=engine_result.data,
                message="Game started successfully through coordinator"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to start game through coordinator: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game start failed: {str(e)}", cause=e)
            )
    
    async def run_game_loop(self, max_rounds: Optional[int] = None) -> CommandResult:
        """运行游戏循环
        
        Args:
            max_rounds: 最大回合数
            
        Returns:
            CommandResult: 运行结果
        """
        if not self._is_running:
            return CommandResult.failure_result(
                ApplicationException("Game not running")
            )
        
        try:
            self._logger.debug("Starting game loop through coordinator")
            
            while self._is_running:
                # 推进回合
                round_result = self._game_engine.advance_round()
                if not round_result.success:
                    return round_result
                
                # 获取游戏状态
                game_state = self._game_engine.get_game_state()
                current_round = game_state.get("current_round", 1)
                participants = game_state.get("participants", [])
                
                # 控制台输出回合信息（简化版）
                print(f"\n--- 第 {current_round} 回合 ---")
                
                # 检查是否应该结束游戏
                if self._should_end_game():
                    end_reason = self._get_end_reason()
                    print(f"\n游戏结束: {end_reason}")
                    return self._game_engine.end_game(end_reason)
                
                # 检查最大回合数
                if max_rounds and current_round > max_rounds:
                    print(f"\n游戏结束: 已达到最大回合 {max_rounds}")
                    return self._game_engine.end_game(f"已达到最大回合 {max_rounds}")
                
                # 执行参与者回合
                for participant in participants:
                    participant_result = await self._execute_participant_turn(participant)
                    if not participant_result.success:
                        self._logger.warning(f"Participant {participant} turn failed: {participant_result.message}")
                
                # 完成回合
                complete_result = self._game_engine.complete_round()
                if not complete_result.success:
                    return complete_result
            
            return CommandResult.success_result(
                message="Game loop completed successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to run game loop: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game loop execution failed: {str(e)}", cause=e)
            )
    
    async def execute_participant_turn(self, participant_name: str) -> CommandResult:
        """执行参与者回合
        
        Args:
            participant_name: 参与者名称
            
        Returns:
            CommandResult: 执行结果
        """
        return await self._execute_participant_turn(participant_name)
    
    def stop_game(self, reason: str = "手动停止") -> CommandResult:
        """停止游戏
        
        Args:
            reason: 停止原因
            
        Returns:
            CommandResult: 停止结果
        """
        try:
            self._logger.debug(f"Stopping game: {reason}")
            
            # 控制台输出游戏结束
            print(f"\n游戏停止: {reason}")
            print("="*60 + "\n")
            
            self._is_running = False
            
            # 结束游戏
            end_result = self._game_engine.end_game(reason)
            
            # 停用所有代理
            active_agents = self._agent_service.get_active_agents()
            for agent_name in active_agents:
                self._agent_service.deactivate_agent(agent_name)
            
            self._logger.debug(f"Game stopped: {reason}")
            
            return end_result
            
        except Exception as e:
            self._logger.error(f"Failed to stop game: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Game stop failed: {str(e)}", cause=e)
            )
    
    def get_game_status(self) -> Dict[str, Any]:
        """获取游戏状态
        
        Returns:
            Dict[str, Any]: 游戏状态
        """
        if not self._is_initialized:
            return {
                "initialized": False,
                "running": False
            }
        
        game_state = self._game_engine.get_game_state()
        
        return {
            "initialized": self._is_initialized,
            "running": self._is_running,
            "game_state": game_state,
            "active_agents": self._agent_service.get_active_agents(),
            "message_history_size": len(self._message_handler.get_message_history()),
            "turn_history_size": len(self._turn_manager.get_turn_history())
        }
    
    def process_message(self, sender: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> CommandResult:
        """处理消息
        
        Args:
            sender: 发送者
            content: 消息内容
            metadata: 消息元数据
            
        Returns:
            CommandResult: 处理结果
        """
        try:
            # 处理消息
            process_result = self._message_handler.process_message(sender, content, metadata)
            if not process_result.success:
                return process_result
            
            # 执行工具调用
            if process_result.data.get("has_tool_calls"):
                tool_results = self._message_handler.execute_tool_calls(
                    process_result.data["processed_message"]
                )
                
                return CommandResult.success_result(
                    data={
                        "message_result": process_result.data,
                        "tool_results": tool_results.data
                    },
                    message="Message and tool calls processed successfully"
                )
            
            return process_result
            
        except Exception as e:
            self._logger.error(f"Failed to process message: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Message processing failed: {str(e)}", cause=e)
            )
    
    def execute_command(self, command: Any) -> CommandResult:
        """执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            CommandResult: 执行结果
        """
        try:
            # 根据命令类型选择处理器
            if self._character_command_handler.can_handle(type(command)):
                return self._character_command_handler.handle(command)
            elif self._world_command_handler.can_handle(type(command)):
                return self._world_command_handler.handle(command)
            else:
                return CommandResult.failure_result(
                    ApplicationException(f"No handler found for command type: {type(command).__name__}")
                )
                
        except Exception as e:
            self._logger.error(f"Failed to execute command: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Command execution failed: {str(e)}", cause=e)
            )
    
    def execute_query(self, query: Any) -> Any:
        """执行查询
        
        Args:
            query: 要执行的查询
            
        Returns:
            Any: 查询结果
        """
        try:
            # 根据查询类型选择处理器
            if self._character_query_handler.can_handle(type(query)):
                return self._character_query_handler.handle(query)
            elif self._world_query_handler.can_handle(type(query)):
                return self._world_query_handler.handle(query)
            else:
                raise ApplicationException(f"No handler found for query type: {type(query).__name__}")
                
        except Exception as e:
            self._logger.error(f"Failed to execute query: {e}")
            raise ApplicationException(f"Query execution failed: {str(e)}", cause=e)
    
    async def _execute_participant_turn(self, participant_name: str) -> CommandResult:
        """执行参与者回合
        
        Args:
            participant_name: 参与者名称
            
        Returns:
            CommandResult: 执行结果
        """
        try:
            # 开始回合
            game_state = self._game_engine.get_game_state()
            current_round = game_state.get("current_round", 1)
            
            turn_result = self._turn_manager.start_turn(
                character_name=participant_name,
                turn_number=current_round,
                round_number=current_round
            )
            
            if not turn_result.success:
                return turn_result
            
            # 检查是否跳过回合
            if turn_result.data.get("skipped"):
                return turn_result
            
            # 激活代理
            activate_result = await self._agent_service.activate_agent(
                agent_name=participant_name,
                context={
                    "round": current_round,
                    "game_state": game_state
                }
            )
            
            if not activate_result.success:
                return self._turn_manager.skip_turn(f"代理激活失败: {activate_result.message}")
            
            # 获取代理响应 - 准备合适的输入数据
            message_history = self._message_handler.get_message_history()
            game_state = self._game_engine.get_game_state()
            
            # 构建输入数据，包含游戏状态、消息历史和当前上下文
            input_data = {
                "game_state": game_state,
                "message_history": message_history[-5:],  # 只传递最近5条消息，避免上下文过长
                "current_round": current_round,
                "participant_name": participant_name,
                "context": {
                    "scene": game_state.get("scene", {}),
                    "participants": game_state.get("participants", []),
                    "previous_actions": self._turn_manager.get_turn_history()[-3:]  # 最近3个回合的行动
                }
            }
            
            self._logger.debug(f"Prepared input data for {participant_name}: {len(message_history)} messages in history")
            
            response_result = await self._agent_service.get_agent_response(
                agent_name=participant_name,
                input_data=input_data,
                timeout=30
            )
            
            if not response_result.success:
                return self._turn_manager.skip_turn(f"代理响应失败: {response_result.message}")
            
            # 处理代理响应
            response = response_result.data.get("response")
            if response:
                # 添加控制台输出
                self._console_output(participant_name, response)
                
                message_result = self.process_message(
                    sender=participant_name,
                    content=str(response)
                )
                
                if message_result.success:
                    self._turn_manager.add_action_to_current_turn("生成响应")
            
            # 完成回合
            complete_result = self._turn_manager.complete_turn(
                actions=["生成响应"] if response else []
            )
            
            # 停用代理
            self._agent_service.deactivate_agent(participant_name)
            
            return complete_result
            
        except Exception as e:
            self._logger.error(f"Failed to execute participant turn: {e}")
            return self._turn_manager.skip_turn(f"回合执行失败: {str(e)}")
    
    def _should_end_game(self) -> bool:
        """检查是否应该结束游戏
        
        Returns:
            bool: 是否应该结束
        """
        game_state = self._game_engine.get_game_state()
        return game_state.get("should_end", False)
    
    def _get_end_reason(self) -> str:
        """获取结束原因
        
        Returns:
            str: 结束原因
        """
        game_state = self._game_engine.get_game_state()
        return game_state.get("end_reason", "游戏结束")
    
    def _extract_participants(self, story_config: Dict[str, Any]) -> List[str]:
        """提取参与者列表
        
        Args:
            story_config: 故事配置
            
        Returns:
            List[str]: 参与者列表
        """
        participants = set()
        
        # 从不同位置提取参与者
        position_sources = [
            story_config.get("initial_positions", {}),
            story_config.get("positions", {}),
            story_config.get("initial", {}).get("positions", {})
        ]
        
        for source in position_sources:
            if isinstance(source, dict):
                participants.update(source.keys())
        
        return list(participants)
    
    def _subscribe_to_events(self) -> None:
        """订阅事件"""
        # 这里可以订阅各种事件并处理
        # 例如：游戏开始、结束、回合开始、结束等
        pass
    
    def _console_output(self, speaker: str, content: str) -> None:
        """控制台输出
        
        Args:
            speaker: 说话者
            content: 内容
        """
        # 格式化输出 - 简化输出格式
        print(f"\n🎭 {speaker}:")
        print(f"{content}")
    
    async def run_game(self) -> None:
        """运行游戏
        
        该方法是游戏的主要入口点，负责启动和运行游戏循环。
        """
        try:
            # 初始化游戏（如果还没有初始化）
            if not self._is_initialized:
                # 从配置加载器获取实际配置
                try:
                    from ...settings.loader import (
                        load_characters,
                        load_story_config,
                        load_model_config
                    )
                    
                    # 加载实际配置
                    character_configs = load_characters()
                    story_config = load_story_config()
                    model_config = load_model_config()
                    
                    # 转换模型配置为字典格式
                    if hasattr(model_config, '__dict__'):
                        model_config_dict = model_config.__dict__
                    else:
                        model_config_dict = dict(model_config)
                    
                    # 设置游戏配置
                    game_config = {
                        "max_rounds": 100,  # 增加最大回合数
                        "require_hostiles": False,  # 不强制要求敌对关系
                        "debug_mode": False
                    }
                    
                    # 获取工具列表
                    tools = []
                    try:
                        from ...world.tools import get_all_tools
                        tools = get_all_tools()
                    except ImportError:
                        self._logger.warning("无法加载工具列表，使用空工具列表")
                    
                    # 创建代理工厂函数
                    def agent_factory(name, persona):
                        try:
                            from ...agents.factory import make_kimi_npc
                            return make_kimi_npc(
                                name=name,
                                persona=persona,
                                model_cfg=model_config_dict
                            )
                        except Exception as e:
                            self._logger.error(f"创建代理失败: {e}")
                            return None
                    
                    init_result = self.initialize_game(
                        game_config=game_config,
                        character_configs=character_configs,
                        story_config=story_config,
                        model_config=model_config_dict,
                        tools=tools,
                        agent_factory=agent_factory
                    )
                    
                except Exception as e:
                    self._logger.error(f"配置加载失败: {e}")
                    # 如果配置加载失败，使用基本配置
                    game_config = {
                        "max_rounds": 100,  # 增加最大回合数
                        "require_hostiles": False,  # 不强制要求敌对关系
                        "debug_mode": False
                    }
                    character_configs = {}
                    story_config = {
                        "scene": {
                            "name": "默认场景",
                            "description": "这是一个默认的游戏场景"
                        }
                    }
                    model_config = {}
                    tools = []
                    
                    init_result = self.initialize_game(
                        game_config=game_config,
                        character_configs=character_configs,
                        story_config=story_config,
                        model_config=model_config,
                        tools=tools,
                        agent_factory=lambda name, persona: None
                    )
                
                if not init_result.success:
                    self._logger.error(f"Game initialization failed: {init_result.message}")
                    return
            
            # 启动游戏
            start_result = await self.start_game()
            if not start_result.success:
                self._logger.error(f"Game start failed: {start_result.message}")
                return
            
            # 运行游戏循环
            await self.run_game_loop()
            
        except Exception as e:
            self._logger.error(f"Game run failed: {str(e)}")
            raise