"""
代理服务

该服务负责游戏中的代理（AI角色）管理，从main.py中提取代理逻辑，
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

代理服务负责：
1. 代理的创建和初始化
2. 代理状态的管理
3. 代理交互的协调
4. 代理配置的处理
"""

import asyncio
import os
import re
from typing import Any, Dict, List, Optional, Callable, Mapping
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .base import ApplicationService, CommandResult
from .message_handler import ProcessedMessage
from ...core.container import ServiceLocator
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, BusinessRuleException
from ...domain.models.characters import Character
from ...domain.models.world import World


class AgentCreatedEvent(DomainEvent):
    """代理创建事件"""
    
    def __init__(self, agent_name: str, agent_type: str, config: Dict[str, Any]):
        super().__init__()
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.config = config
    
    def get_event_type(self) -> str:
        return "AgentCreated"


class AgentActivatedEvent(DomainEvent):
    """代理激活事件"""
    
    def __init__(self, agent_name: str, context: Dict[str, Any]):
        super().__init__()
        self.agent_name = agent_name
        self.context = context
    
    def get_event_type(self) -> str:
        return "AgentActivated"


class AgentRespondedEvent(DomainEvent):
    """代理响应事件"""
    
    def __init__(self, agent_name: str, response: str, metadata: Dict[str, Any]):
        super().__init__()
        self.agent_name = agent_name
        self.response = response
        self.metadata = metadata
    
    def get_event_type(self) -> str:
        return "AgentResponded"


class AgentTimeoutEvent(DomainEvent):
    """代理超时事件"""
    
    def __init__(self, agent_name: str, timeout_duration: int):
        super().__init__()
        self.agent_name = agent_name
        self.timeout_duration = timeout_duration
    
    def get_event_type(self) -> str:
        return "AgentTimeout"


@dataclass
class AgentConfig:
    """代理配置
    
    封装代理的配置信息，包括人设、外观等。
    遵循单一职责原则，专门负责代理配置数据的封装。
    """
    name: str
    persona: str
    appearance: Optional[str] = None
    quotes: Optional[List[str]] = None
    relation_brief: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None
    tools: Optional[List[Any]] = None
    allowed_names: Optional[str] = None
    
    def __post_init__(self):
        if self.quotes is None:
            self.quotes = []


class Agent(ABC):
    """代理接口
    
    定义代理的标准接口，遵循依赖倒置原则。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """获取代理名称
        
        Returns:
            str: 代理名称
        """
        pass
    
    @abstractmethod
    async def activate(self, context: Dict[str, Any]) -> None:
        """激活代理
        
        Args:
            context: 激活上下文
        """
        pass
    
    @abstractmethod
    async def get_response(self, input_data: Any) -> Any:
        """获取代理响应
        
        Args:
            input_data: 输入数据
            
        Returns:
            Any: 响应数据
        """
        pass
    
    @abstractmethod
    def is_active(self) -> bool:
        """检查代理是否激活
        
        Returns:
            bool: 是否激活
        """
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """停用代理"""
        pass


class AgentFactory(ABC):
    """代理工厂接口
    
    定义代理创建的标准接口，遵循依赖倒置原则。
    """
    
    @abstractmethod
    def can_create(self, agent_type: str) -> bool:
        """检查是否能创建指定类型的代理
        
        Args:
            agent_type: 代理类型
            
        Returns:
            bool: 是否能创建
        """
        pass
    
    @abstractmethod
    def create_agent(self, config: AgentConfig) -> Agent:
        """创建代理
        
        Args:
            config: 代理配置
            
        Returns:
            Agent: 创建的代理
        """
        pass


class DefaultAgentFactory(AgentFactory):
    """默认代理工厂实现
    
    该工厂使用agentscope库创建代理，提供基本的代理创建功能。
    """
    
    def __init__(self, logger: Logger):
        """初始化默认代理工厂
        
        Args:
            logger: 日志记录器
        """
        self._logger = logger
    
    def can_create(self, agent_type: str) -> bool:
        """检查是否能创建指定类型的代理
        
        Args:
            agent_type: 代理类型
            
        Returns:
            bool: 是否能创建
        """
        # 默认工厂可以创建所有类型的代理
        return True
    
    def create_agent(self, config: AgentConfig) -> Agent:
        """创建代理
        
        Args:
            config: 代理配置
            
        Returns:
            Agent: 创建的代理
        """
        try:
            # 导入agentscope相关模块
            from agentscope.agent import ReActAgent
            from agentscope.formatter import OpenAIChatFormatter
            from agentscope.memory import InMemoryMemory
            from agentscope.model import OpenAIChatModel
            from agentscope.tool import Toolkit
            
            # 创建模型配置
            model_cfg = config.model_config or {}
            api_key = model_cfg.get("api_key", "")
            base_url = model_cfg.get("base_url", "https://api.openai.com/v1")

            enable_remote = model_cfg.get("enable_remote_agent")
            env_flag = os.environ.get("ENABLE_REMOTE_AGENT")
            if env_flag is not None:
                enable_remote = env_flag.strip().lower() in {"1", "true", "yes", "on"}
            elif enable_remote is None:
                enable_remote = bool(api_key)

            if not enable_remote:
                self._logger.info(
                    f"Remote agent disabled for {config.name}, using simple agent"
                )
                return SimpleAgentAdapter(config, self._logger)

            if not api_key:
                self._logger.warning(
                    f"API key missing for agent {config.name}, fallback to simple agent"
                )
                return SimpleAgentAdapter(config, self._logger)
            
            # 获取NPC配置
            npc_config = model_cfg.get("npc", {})
            model_name = npc_config.get("model", "gpt-3.5-turbo")
            temperature = npc_config.get("temperature", 0.7)
            stream = npc_config.get("stream", True)
            
            # 创建模型
            model = OpenAIChatModel(
                model_name=model_name,
                api_key=api_key,
                stream=stream,
                client_args={"base_url": base_url},
                generate_kwargs={"temperature": temperature}
            )
            
            # 创建工具包
            toolkit = Toolkit()
            if config.tools:
                for tool in config.tools:
                    try:
                        toolkit.register_tool_function(tool)
                    except Exception as e:
                        self._logger.warning(f"注册工具失败: {e}")
            
            # 构建系统提示
            sys_prompt = self._build_system_prompt(config)
            
            # 创建代理
            agent = ReActAgent(
                name=config.name,
                sys_prompt=sys_prompt,
                model=model,
                formatter=OpenAIChatFormatter(),
                memory=InMemoryMemory(),
                toolkit=toolkit
            )
            
            # 包装为适配的Agent，传递logger实例
            return AgentscopeAgentAdapter(agent, self._logger)
            
        except Exception as e:
            self._logger.error(f"创建代理失败: {e}")
            raise ApplicationException(f"Agent creation failed: {str(e)}", cause=e)
    
    def _build_system_prompt(self, config: AgentConfig) -> str:
        """构建系统提示
        
        Args:
            config: 代理配置
            
        Returns:
            str: 系统提示
        """
        prompt = f"你是游戏中的NPC：{config.name}。\n"
        prompt += f"人设：{config.persona}\n"
        
        if config.appearance:
            prompt += f"外观特征：{config.appearance}\n"
        
        if config.quotes:
            quotes_text = " / ".join(config.quotes)
            prompt += f"常用语气/台词：{quotes_text}\n"
        
        if config.relation_brief:
            prompt += f"当前立场提示：{config.relation_brief}\n"
        
        prompt += "\n对话要求：\n"
        prompt += "- 先用中文说1-2句对白/想法/微动作，符合人设。\n"
        prompt += "- 当需要执行行动时，直接调用工具。\n"
        prompt += "- 调用工具后等待系统反馈，再根据结果做简短评论或继续对白。\n"
        
        if config.allowed_names:
            prompt += f"- 参与者名称（仅可用）：{config.allowed_names}\n"
        
        return prompt


class AgentscopeAgentAdapter(Agent):
    """AgentScope代理适配器
    
    将AgentScope的代理适配为我们的代理接口。
    """
    
    def __init__(self, agentscope_agent, logger: Optional[Logger] = None):
        """初始化适配器
        
        Args:
            agentscope_agent: AgentScope代理实例
            logger: 日志记录器实例
        """
        self._agent = agentscope_agent
        self._is_active = False
        self._logger = logger
    
    @property
    def name(self) -> str:
        """获取代理名称
        
        Returns:
            str: 代理名称
        """
        return self._agent.name
    
    async def activate(self, context: Dict[str, Any]) -> None:
        """激活代理
        
        Args:
            context: 激活上下文
        """
        try:
            self._is_active = True
            if self._logger:
                self._logger.debug(f"Agent {self.name} activated successfully")
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error activating agent {self.name}: {e}")
            else:
                print(f"ERROR: Error activating agent {self.name}: {e}")
            raise
    
    async def get_response(self, input_data: Any) -> Any:
        """获取代理响应
        
        Args:
            input_data: 输入数据
            
        Returns:
            Any: 响应数据
        """
        if not self._is_active:
            raise ApplicationException("Agent not activated")
        
        # 预处理输入数据，确保不会传递None给代理
        processed_input = self._preprocess_input(input_data)
        
        try:
            # 实际调用AgentScope代理的响应逻辑
            # AgentScope代理可能是同步的，需要在这里处理
            if hasattr(self._agent, '__call__'):
                # 如果代理是可调用的，直接调用
                response = self._agent(processed_input)
                # 如果返回的是协程，需要等待
                if asyncio.iscoroutine(response):
                    return await response
                return response
            elif hasattr(self._agent, 'reply'):
                # 尝试使用reply方法
                response = self._agent.reply(processed_input)
                if asyncio.iscoroutine(response):
                    return await response
                return response
            elif hasattr(self._agent, 'act'):
                # 尝试使用act方法
                response = self._agent.act(processed_input)
                if asyncio.iscoroutine(response):
                    return await response
                return response
            else:
                # 如果代理不可调用，尝试其他方法
                # 创建一个基本的响应，包含代理名称和角色信息
                return self._generate_fallback_response(processed_input)
        except Exception as e:
            # 如果调用失败，记录详细错误信息并生成适当的响应
            return self._handle_response_error(e, processed_input)
    
    def _preprocess_input(self, input_data: Any) -> Any:
        """预处理输入数据
        
        将外部传入的数据转换为 AgentScope 所需的 Msg 结构，
        避免因类型不匹配导致的记忆写入错误。
        """
        try:
            from agentscope.message import Msg  # type: ignore
        except ImportError:  # pragma: no cover - 仅在缺少依赖时触发
            Msg = None  # type: ignore
        
        if Msg and isinstance(input_data, Msg):
            return input_data
        
        if Msg and isinstance(input_data, list) and all(isinstance(item, Msg) for item in input_data):
            return input_data
        
        # 统一整理成文本描述
        prompt_text = self._build_prompt_text(input_data)
        
        if Msg:
            return Msg(
                name="GameMaster",
                content=prompt_text,
                role="user"
            )
        
        return prompt_text
    
    def _build_prompt_text(self, payload: Any) -> str:
        """生成面向代理的文本提示"""
        if payload is None:
            return f"请{self.name}根据当前局势采取行动。"
        
        if isinstance(payload, str):
            return payload
        
        if isinstance(payload, ProcessedMessage):
            entry = self._format_history_entry(payload)
            return entry or f"{payload.sender}: {payload.cleaned_content}"
        
        if isinstance(payload, dict):
            return self._build_prompt_from_dict(payload)
        
        if isinstance(payload, list):
            return self._build_prompt_from_list(payload)
        
        return str(payload)
    
    def _build_prompt_from_dict(self, payload: Dict[str, Any]) -> str:
        """根据游戏上下文构建提示文本"""
        lines: List[str] = []
        
        round_no = payload.get("current_round") or payload.get("round")
        if round_no is not None:
            lines.append(f"当前回合: {round_no}")
        
        participant = payload.get("participant_name") or payload.get("actor")
        if participant:
            lines.append(f"当前角色: {participant}")
        
        game_state = payload.get("game_state")
        scene = None
        participants = None
        if isinstance(game_state, dict):
            scene = game_state.get("scene")
            participants = game_state.get("participants")
        context = payload.get("context")
        if isinstance(context, dict):
            if not scene:
                scene = context.get("scene")
            participants = context.get("participants") or participants
            previous_actions = context.get("previous_actions") or []
        else:
            previous_actions = []
        
        if isinstance(scene, dict):
            scene_parts = []
            if scene.get("name"):
                scene_parts.append(str(scene["name"]))
            if scene.get("description"):
                scene_parts.append(str(scene["description"]))
            if scene_parts:
                lines.append("场景: " + " - ".join(scene_parts))
        
        if participants:
            names = []
            for item in participants:
                if isinstance(item, str):
                    names.append(item)
                elif isinstance(item, dict):
                    names.append(str(item.get("name") or item.get("id") or item))
                else:
                    names.append(str(item))
            if names:
                lines.append("参与者: " + ", ".join(names))
        
        action_texts = []
        for action in previous_actions:
            if isinstance(action, dict):
                label = action.get("description") or action.get("action") or action.get("name")
            else:
                label = str(action)
            if label:
                action_texts.append(str(label))
        if action_texts:
            lines.append("最近行动: " + " | ".join(action_texts))
        
        history = payload.get("message_history") or []
        history_text = self._build_prompt_from_list(history)
        if history_text:
            lines.append("近期对话:\n" + history_text)
        
        instructions = payload.get("instructions")
        if instructions:
            lines.append("额外指示: " + str(instructions))
        
        if not lines:
            return f"请{self.name}根据当前局势采取行动。"
        return "\n".join(lines)
    
    def _build_prompt_from_list(self, items: List[Any]) -> str:
        """将列表内容转换为文本"""
        if not items:
            return ""
        lines: List[str] = []
        for item in items:
            entry = self._format_history_entry(item)
            if entry:
                lines.append(entry)
            elif isinstance(item, dict):
                lines.append(str(item))
            else:
                lines.append(str(item))
        return "\n".join(lines)
    
    def _format_history_entry(self, item: Any) -> Optional[str]:
        """格式化单条历史记录"""
        if isinstance(item, ProcessedMessage):
            content = item.cleaned_content or item.original_content or ""
            if content:
                return f"{item.sender}: {content}"
            return None
        if isinstance(item, dict):
            sender = item.get("sender") or item.get("name") or item.get("role")
            content = item.get("cleaned_content") or item.get("content") or item.get("message")
            if sender and content:
                return f"{sender}: {content}"
        return None
    
    def _generate_fallback_response(self, input_data: Any) -> str:
        """生成备用响应
        
        Args:
            input_data: 输入数据
            
        Returns:
            str: 备用响应
        """
        # 根据输入数据生成更具体的响应
        if isinstance(input_data, dict):
            context = input_data.get("context", {})
            situation = context.get("situation", "游戏进行中")
            
            # 根据情况生成不同的响应
            if "战斗" in situation or "攻击" in situation:
                return f"[{self.name}] 我正在评估当前战斗形势..."
            elif "对话" in situation or "交流" in situation:
                return f"[{self.name}] 我正在思考如何回应..."
            else:
                return f"[{self.name}] 我正在观察当前情况，准备行动..."
        
        return f"[{self.name}] 我正在思考下一步行动..."
    
    def _handle_response_error(self, error: Exception, input_data: Any) -> str:
        """处理响应错误
        
        Args:
            error: 错误对象
            input_data: 输入数据
            
        Returns:
            str: 错误处理响应
        """
        error_msg = str(error)
        
        # 记录详细错误信息用于调试
        try:
            container = None
            try:
                container = ServiceLocator.get_container()
            except Exception:
                container = None

            if container and container.is_registered(Logger):
                logger = container.resolve(Logger)
                logger.error(
                    f"Agent {self.name} response error: {error_msg}, input type: {type(input_data)}"
                )
            else:
                print(
                    f"ERROR: Agent {self.name} response error: {error_msg}, input type: {type(input_data)}"
                )
        except Exception as log_error:
            print(
                f"ERROR: Agent {self.name} response error: {error_msg}, input type: {type(input_data)}"
            )
            print(f"LOGGER ERROR: Failed to get logger: {log_error}")
        
        # 根据错误类型生成不同的响应
        if "'NoneType' object is not iterable" in error_msg:
            # NoneType错误，提供更具体的响应
            return self._generate_fallback_response(input_data)
        elif "timeout" in error_msg.lower():
            return f"[{self.name}] 我需要更多时间来思考..."
        elif "connection" in error_msg.lower() or "network" in error_msg.lower():
            return f"[{self.name}] 我暂时无法连接，稍后再试..."
        else:
            # 其他错误，提供通用响应但不暴露技术细节
            return f"[{self.name}] 我正在处理当前情况..."
    
    def is_active(self) -> bool:
        """检查代理是否激活
        
        Returns:
            bool: 是否激活
        """
        return self._is_active
    
    def deactivate(self) -> None:
        """停用代理"""
        try:
            self._is_active = False
            if self._logger:
                self._logger.debug(f"Agent {self.name} deactivated successfully")
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error deactivating agent {self.name}: {e}")
            else:
                print(f"ERROR: Error deactivating agent {self.name}: {e}")


class SimpleAgentFactory(AgentFactory):
    """简单代理工厂实现
    
    当默认工厂创建失败时使用的备用工厂，提供基本的代理创建功能。
    """
    
    def can_create(self, agent_type: str) -> bool:
        """检查是否能创建指定类型的代理
        
        Args:
            agent_type: 代理类型
            
        Returns:
            bool: 是否能创建
        """
        # 简单工厂可以创建所有类型的代理
        return True
    
    def create_agent(self, config: AgentConfig) -> Agent:
        """创建代理
        
        Args:
            config: 代理配置
            
        Returns:
            Agent: 创建的代理
        """
        return SimpleAgentAdapter(config)


class SimpleAgentAdapter(Agent):
    """简单代理适配器
    
    提供基本的代理实现，不依赖外部库。
    """
    
    def __init__(self, config: AgentConfig, logger: Optional[Logger] = None):
        """初始化适配器
        
        Args:
            config: 代理配置
            logger: 日志记录器实例
        """
        self._config = config
        self._is_active = False
        self._logger = logger
        self._quote_index = 0
        self._response_history: List[str] = []
        self._has_introduced = False
        self._persona_shared = False
        self._default_lines = self._build_default_lines()
        self._default_index = 0
    
    @property
    def name(self) -> str:
        """获取代理名称
        
        Returns:
            str: 代理名称
        """
        return self._config.name
    
    async def activate(self, context: Dict[str, Any]) -> None:
        """激活代理
        
        Args:
            context: 激活上下文
        """
        try:
            self._is_active = True
            if self._logger:
                self._logger.debug(f"SimpleAgent {self.name} activated successfully")
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error activating simple agent {self.name}: {e}")
            else:
                print(f"ERROR: Error activating simple agent {self.name}: {e}")
            raise
    
    async def get_response(self, input_data: Any) -> Any:
        """获取代理响应
        
        Args:
            input_data: 输入数据
            
        Returns:
            Any: 响应数据
        """
        if not self._is_active:
            raise ApplicationException("Agent not activated")
        
        context_text = self._extract_text(input_data)
        response = self._compose_response(context_text)
        self._response_history.append(response)
        if len(self._response_history) > 16:
            self._response_history.pop(0)
        return response
    
    def is_active(self) -> bool:
        """检查代理是否激活
        
        Returns:
            bool: 是否激活
        """
        return self._is_active
    
    def deactivate(self) -> None:
        """停用代理"""
        try:
            self._is_active = False
            if self._logger:
                self._logger.debug(f"SimpleAgent {self.name} deactivated successfully")
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error deactivating simple agent {self.name}: {e}")
            else:
                print(f"ERROR: Error deactivating simple agent {self.name}: {e}")

    def _extract_text(self, payload: Any) -> str:
        """提取输入中的关键文本"""
        if payload is None:
            return ""
        try:
            from agentscope.message import Msg  # type: ignore
            if isinstance(payload, Msg):
                text = payload.get_text_content()
                if text:
                    return text
                content = payload.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    fragments = [str(block.get("text", "")) for block in content if isinstance(block, dict)]
                    return " ".join([frag for frag in fragments if frag])
        except Exception:
            pass
        if isinstance(payload, ProcessedMessage):
            return payload.cleaned_content or payload.original_content or ""
        if isinstance(payload, dict):
            collected: List[str] = []
            for key in ("content", "message", "summary", "instructions"):
                value = payload.get(key)
                if isinstance(value, str):
                    collected.append(value)
            if collected:
                return " ".join(collected)
            return " ".join(f"{k}:{v}" for k, v in payload.items() if isinstance(v, (str, int, float)))
        if isinstance(payload, (list, tuple)):
            parts = [self._extract_text(item) for item in payload if item]
            return "\n".join(part for part in parts if part)
        return str(payload)

    def _compose_response(self, context_text: str) -> str:
        participants = self._extract_participants(context_text)
        recent_context = self._extract_recent_context(context_text)
        action_line = self._build_action_line(recent_context)
        strategy = self._build_strategy_line(recent_context)
        quote = self._next_quote()
        default_line = self._next_default_line(participants)

        speech_line = self._build_speech_line(strategy, quote, default_line)
        response_lines = [line for line in (action_line, speech_line) if line]
        if not response_lines:
            response_lines.append(default_line or f"{self.name}短暂点头，示意继续行动。")

        candidate = "\n".join(response_lines)
        if self._response_history and candidate == self._response_history[-1]:
            candidate += "\n" + f"{self.name}补充道：我们必须保持灵活。"
        return candidate

    def _extract_recent_context(self, text: str) -> str:
        if not text:
            return ""
        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in reversed(cleaned_lines):
            if line.startswith("当前回合") or line.startswith("参与者") or line.startswith("近期对话"):
                continue
            if "current_round" in line or "participant_name" in line or "message_history" in line:
                continue
            trimmed = re.sub(r"^[\-•*\d\.\s]+", "", line)
            trimmed = trimmed.strip()
            if not trimmed:
                continue
            if ":" in trimmed or "：" in trimmed:
                parts = re.split(r"[:：]", trimmed, maxsplit=1)
                if len(parts) == 2 and parts[1].strip():
                    trimmed = f"{parts[0].strip()}的发言：{parts[1].strip()}"
            if len(trimmed) > 80:
                trimmed = trimmed[:80] + "…"
            return trimmed
        ignore_tokens = ("current_round", "participant_name", "message_history", "previous_actions")
        segments = [seg.strip() for seg in re.split(r"[。！？!?]", text) if seg.strip()]
        for seg in reversed(segments):
            if any(token in seg for token in ignore_tokens):
                continue
            return seg[:80] + ("…" if len(seg) > 80 else "")
        return ""

    def _build_action_line(self, recent_context: str) -> Optional[str]:
        parts: List[str] = []
        appearance = (self._config.appearance or "").strip()
        if not self._has_introduced and appearance:
            parts.append(appearance)
            self._has_introduced = True
        if recent_context:
            parts.append(f"留意着{recent_context}")
        if not parts:
            parts.append("沉稳地环视四周")
        return "（" + "，".join(parts) + "）"

    def _build_strategy_line(self, recent_context: str) -> Optional[str]:
        persona_hint = (self._config.persona or "").strip()
        if persona_hint:
            persona_hint = persona_hint.split("。", 1)[0]
        fragments: List[str] = []
        if recent_context:
            fragments.append(f"留意“{recent_context}”的动向")
        if persona_hint and not self._persona_shared:
            fragments.append(persona_hint)
            self._persona_shared = True
        if not fragments:
            return None
        return "，".join(fragments)

    def _next_quote(self) -> Optional[str]:
        quotes = self._config.quotes or []
        if not quotes:
            return None
        quote = quotes[self._quote_index % len(quotes)].strip()
        self._quote_index += 1
        return quote

    def _build_speech_line(self, strategy: Optional[str], quote: Optional[str], fallback: Optional[str]) -> str:
        if strategy and quote:
            return f"{self.name}沉声道：“{strategy}。{quote}”"
        if strategy:
            return f"{self.name}沉声道：“{strategy}。”"
        if quote and fallback:
            return f"{self.name}说道：“{quote} {fallback}”"
        if quote:
            return f"{self.name}说道：“{quote}”"
        if fallback:
            return f"{self.name}轻声回应：“{fallback}”"
        return f"{self.name}轻声回应：“我们保持节奏。”"

    def _extract_participants(self, text: str) -> List[str]:
        match = re.search(r"参与者[:：]\s*(.+)", text)
        if not match:
            return []
        return [item.strip() for item in match.group(1).split(",") if item.strip()]

    def _build_default_lines(self) -> List[str]:
        name = (self._config.name or "").lower()
        if name == "doctor":
            return [
                "注意护卫线，{ally}先把视线吸引过去",
                "战场信息实时同步，任何异常立即汇报",
                "大家保持阵型，我来调配支援"
            ]
        if name == "amiya":
            return [
                "我在后方支援，{ally}请小心",
                "源石技艺准备就绪，请接住这道护盾",
                "只要我们团结起来，就没有跨不过的难关"
            ]
        if name == "mephisto":
            return [
                "浮士德，让你的箭与我的乐章同奏",
                "听好了，{ally}，要用恐惧占领他们的心",
                "感染者们，跟着节拍，将他们席卷"
            ]
        if name == "faust":
            return [
                "锁定角度，{ally}别挡在射线里",
                "风速稳定，再给我两秒确认",
                "目标无掩体，准备下一发"
            ]
        return [
            "保持警惕，随时应对变数",
            "我们要占据主动权",
            "稳扎稳打，胜利就在前方"
        ]

    def _next_default_line(self, participants: List[str]) -> Optional[str]:
        if not self._default_lines:
            return None
        line = self._default_lines[self._default_index % len(self._default_lines)]
        self._default_index += 1
        if "{ally}" in line:
            target = next((p for p in participants if p != self.name), participants[0] if participants else "")
            replacement = target or "同伴"
            line = line.replace("{ally}", replacement)
        return line


class AgentService(ApplicationService):
    """代理服务
    
    负责游戏中的代理管理，包括代理创建、状态管理和交互协调。
    遵循单一职责原则，专门负责代理管理的核心功能。
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        agent_factories: List[AgentFactory] = None,
        default_timeout: int = 30
    ):
        """初始化代理服务
        
        Args:
            event_bus: 事件总线
            logger: 日志记录器
            agent_factories: 代理工厂列表
            default_timeout: 默认超时时间（秒）
        """
        super().__init__(event_bus, logger)
        self._agent_factories = agent_factories or []
        self._default_timeout = default_timeout
        self._agents: Dict[str, Agent] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._active_agents: Dict[str, Agent] = {}
        self._response_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
        
        # 确保至少有一个默认工厂
        if not self._agent_factories:
            self._ensure_default_factory()
    
    def _ensure_default_factory(self) -> None:
        """确保至少有一个默认代理工厂
        
        如果没有提供代理工厂，则创建并注册一个默认工厂。
        """
        try:
            default_factory = DefaultAgentFactory(self._logger)
            self._agent_factories.append(default_factory)
            self._logger.debug("Default agent factory registered")
        except Exception as e:
            self._logger.error(f"Failed to create default agent factory: {e}")
            # 如果默认工厂创建失败，创建一个简单的空工厂
            self._agent_factories.append(SimpleAgentFactory())
            self._logger.warning("Using simple agent factory as fallback")
    
    def register_agent_factory(self, factory: AgentFactory) -> None:
        """注册代理工厂
        
        Args:
            factory: 代理工厂
        """
        self._agent_factories.append(factory)
        self._logger.debug(f"Agent factory registered: {factory.__class__.__name__}")
    
    def create_agent(self, config: AgentConfig, agent_type: str = "default") -> CommandResult:
        """创建代理
        
        Args:
            config: 代理配置
            agent_type: 代理类型
            
        Returns:
            CommandResult: 创建结果
        """
        agent = None
        try:
            self._logger.debug(f"Creating agent: {config.name}")
            
            # 检查代理是否已存在
            if config.name in self._agents:
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {config.name} already exists")
                )
            
            # 查找合适的工厂，优先使用DefaultAgentFactory
            factory = self._find_factory(agent_type)
            if not factory:
                return CommandResult.failure_result(
                    ApplicationException(f"No factory found for agent type: {agent_type}")
                )
            
            # 确保使用DefaultAgentFactory而不是SimpleAgentFactory
            if isinstance(factory, SimpleAgentFactory):
                self._logger.debug(f"Attempting to use SimpleAgentFactory for {config.name}, trying to create DefaultAgentFactory")
                try:
                    default_factory = DefaultAgentFactory(self._logger)
                    factory = default_factory
                    self._logger.debug(f"Successfully created DefaultAgentFactory for {config.name}")
                except Exception as e:
                    self._logger.error(f"Failed to create DefaultAgentFactory for {config.name}: {e}")
            
            # 创建代理
            agent = factory.create_agent(config)
            
            # 存储代理和配置
            self._agents[config.name] = agent
            self._agent_configs[config.name] = config
            
            # 发布代理创建事件
            self.publish_event(AgentCreatedEvent(
                agent_name=config.name,
                agent_type=agent_type,
                config={
                    "persona": config.persona,
                    "appearance": config.appearance,
                    "quotes": config.quotes,
                    "relation_brief": config.relation_brief
                }
            ))
            
            self._logger.debug(f"Agent created: {config.name}")
            
            return CommandResult.success_result(
                data={
                    "agent_name": config.name,
                    "agent_type": agent_type,
                    "is_active": False
                },
                message=f"Agent {config.name} created successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to create agent {config.name}: {e}")
            # 清理可能已创建的代理
            if agent and config.name in self._agents:
                del self._agents[config.name]
            if config.name in self._agent_configs:
                del self._agent_configs[config.name]
            return CommandResult.failure_result(
                ApplicationException(f"Agent creation failed: {str(e)}", cause=e)
            )
    
    async def activate_agent(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> CommandResult:
        """激活代理
        
        Args:
            agent_name: 代理名称
            context: 激活上下文
            
        Returns:
            CommandResult: 激活结果
        """
        try:
            self._logger.debug(f"Activating agent: {agent_name}")
            
            # 检查代理是否存在
            if agent_name not in self._agents:
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} not found")
                )
            
            agent = self._agents[agent_name]
            
            # 检查代理是否已激活
            if agent.is_active():
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} is already active")
                )
            
            # 激活代理（等待激活完成）
            await agent.activate(context or {})
            
            # 添加到活跃代理列表
            self._active_agents[agent_name] = agent
            
            # 发布代理激活事件
            self.publish_event(AgentActivatedEvent(
                agent_name=agent_name,
                context=context or {}
            ))
            
            self._logger.debug(f"Agent activated: {agent_name}")
            
            return CommandResult.success_result(
                data={
                    "agent_name": agent_name,
                    "is_active": True,
                    "context": context or {}
                },
                message=f"Agent {agent_name} activated successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to activate agent {agent_name}: {e}")
            # 激活失败时，确保代理状态被重置
            if agent_name in self._active_agents:
                del self._active_agents[agent_name]
            try:
                agent = self._agents.get(agent_name)
                if agent and agent.is_active():
                    agent.deactivate()
            except Exception as deactivate_error:
                self._logger.error(f"Failed to deactivate agent {agent_name} after activation failure: {deactivate_error}")
            return CommandResult.failure_result(
                ApplicationException(f"Agent activation failed: {str(e)}", cause=e)
            )
    
    async def get_agent_response(self, agent_name: str, input_data: Any, timeout: Optional[int] = None) -> CommandResult:
        """获取代理响应
        
        Args:
            agent_name: 代理名称
            input_data: 输入数据
            timeout: 超时时间
            
        Returns:
            CommandResult: 响应结果
        """
        try:
            self._logger.debug(f"Getting response from agent: {agent_name}")
            
            # 检查代理是否存在且激活
            if agent_name not in self._active_agents:
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} not found or not active")
                )
            
            agent = self._active_agents[agent_name]
            timeout_duration = timeout or self._default_timeout
            
            try:
                # 获取响应（带超时）
                response = await asyncio.wait_for(
                    agent.get_response(input_data),
                    timeout=timeout_duration
                )
                
                # 记录响应历史
                self._add_response_to_history(agent_name, input_data, response, True, None)
                
                # 发布代理响应事件
                self.publish_event(AgentRespondedEvent(
                    agent_name=agent_name,
                    response=str(response),
                    metadata={
                        "input_type": type(input_data).__name__,
                        "response_type": type(response).__name__,
                        "timeout_duration": timeout_duration
                    }
                ))
                
                self._logger.debug(f"Agent {agent_name} responded successfully")
                
                return CommandResult.success_result(
                    data={
                        "agent_name": agent_name,
                        "response": response,
                        "timeout_duration": timeout_duration
                    },
                    message=f"Agent {agent_name} responded successfully"
                )
                
            except asyncio.TimeoutError:
                # 记录超时历史
                self._add_response_to_history(agent_name, input_data, None, False, "timeout")
                
                # 发布代理超时事件
                self.publish_event(AgentTimeoutEvent(
                    agent_name=agent_name,
                    timeout_duration=timeout_duration
                ))
                
                self._logger.warning(f"Agent {agent_name} response timeout")
                
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} response timeout after {timeout_duration}s")
                )
                
        except Exception as e:
            # 记录错误历史
            self._add_response_to_history(agent_name, input_data, None, False, str(e))
            
            self._logger.error(f"Failed to get response from agent {agent_name}: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Agent response failed: {str(e)}", cause=e)
            )
    
    def deactivate_agent(self, agent_name: str, force: bool = False) -> CommandResult:
        """停用代理
        
        Args:
            agent_name: 代理名称
            force: 是否强制停用
            
        Returns:
            CommandResult: 停用结果
        """
        try:
            self._logger.debug(f"Deactivating agent: {agent_name}")
            
            # 检查代理是否在活跃列表中
            if agent_name not in self._active_agents and not force:
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} is not active")
                )
            
            # 获取代理实例
            agent = self._active_agents.get(agent_name)
            if not agent and not force:
                return CommandResult.failure_result(
                    ApplicationException(f"Agent {agent_name} not found in active agents")
                )
            
            # 如果强制停用，尝试从所有代理中获取
            if force and not agent:
                agent = self._agents.get(agent_name)
            
            if agent:
                # 停用代理
                try:
                    agent.deactivate()
                except Exception as deactivate_error:
                    self._logger.error(f"Error deactivating agent {agent_name}: {deactivate_error}")
                    if not force:
                        raise deactivate_error
                
                # 从活跃列表中移除
                if agent_name in self._active_agents:
                    del self._active_agents[agent_name]
            
            self._logger.debug(f"Agent deactivated: {agent_name}")
            
            return CommandResult.success_result(
                data={
                    "agent_name": agent_name,
                    "is_active": False,
                    "forced": force
                },
                message=f"Agent {agent_name} deactivated successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to deactivate agent {agent_name}: {e}")
            # 即使停用失败，也尝试从活跃列表中移除
            if agent_name in self._active_agents:
                del self._active_agents[agent_name]
            return CommandResult.failure_result(
                ApplicationException(f"Agent deactivation failed: {str(e)}", cause=e)
            )
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """获取代理配置
        
        Args:
            agent_name: 代理名称
            
        Returns:
            Optional[AgentConfig]: 代理配置，如果不存在则返回None
        """
        return self._agent_configs.get(agent_name)
    
    def get_active_agents(self) -> List[str]:
        """获取活跃代理列表
        
        Returns:
            List[str]: 活跃代理名称列表
        """
        return list(self._active_agents.keys())
    
    def get_all_agents(self) -> List[str]:
        """获取所有代理列表
        
        Returns:
            List[str]: 所有代理名称列表
        """
        return list(self._agents.keys())
    
    def get_response_history(self, agent_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取响应历史
        
        Args:
            agent_name: 代理名称过滤器
            limit: 返回的最大数量
            
        Returns:
            List[Dict[str, Any]]: 响应历史列表
        """
        history = self._response_history.copy()
        
        if agent_name:
            history = [entry for entry in history if entry.get("agent_name") == agent_name]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def create_agents_from_character_configs(
        self,
        character_configs: Dict[str, Any],
        story_config: Dict[str, Any],
        model_config: Dict[str, Any],
        tools: List[Any],
        factory: Callable
    ) -> CommandResult:
        """从角色配置创建代理
        
        Args:
            character_configs: 角色配置
            story_config: 故事配置
            model_config: 模型配置
            tools: 工具列表
            factory: 代理工厂函数
            
        Returns:
            CommandResult: 创建结果
        """
        try:
            self._logger.debug("Creating agents from character configs")
            
            # 提取参与者
            participants = self._extract_participants(story_config)
            allowed_names_str = ", ".join(participants) if participants else ""
            
            created_agents = []
            
            for name in participants:
                character_config = character_configs.get(name, {})
                
                # 构建关系简述
                relation_brief = self._build_relation_brief(name, character_configs)
                
                # 创建代理配置
                agent_config = AgentConfig(
                    name=name,
                    persona=character_config.get("persona", "一个简短的人设描述"),
                    appearance=character_config.get("appearance"),
                    quotes=character_config.get("quotes"),
                    relation_brief=relation_brief,
                    model_config=model_config,
                    tools=tools,
                    allowed_names=allowed_names_str
                )
                
                # 创建代理
                result = self.create_agent(agent_config)
                if result.success:
                    created_agents.append(name)
                else:
                    self._logger.error(f"Failed to create agent {name}: {result.message}")
            
            self._logger.debug(f"Created {len(created_agents)} agents from character configs")
            
            return CommandResult.success_result(
                data={
                    "created_agents": created_agents,
                    "total_participants": len(participants)
                },
                message=f"Created {len(created_agents)} agents successfully"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to create agents from character configs: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Agent batch creation failed: {str(e)}", cause=e)
            )
    
    def _find_factory(self, agent_type: str) -> Optional[AgentFactory]:
        """查找代理工厂
        
        Args:
            agent_type: 代理类型
            
        Returns:
            Optional[AgentFactory]: 代理工厂，如果找不到则返回None
        """
        for factory in self._agent_factories:
            if factory.can_create(agent_type):
                return factory
        return None
    
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
    
    def _build_relation_brief(self, character_name: str, character_configs: Dict[str, Any]) -> str:
        """构建关系简述
        
        Args:
            character_name: 角色名称
            character_configs: 角色配置
            
        Returns:
            str: 关系简述
        """
        relations_config = character_configs.get("relations", {})
        if not isinstance(relations_config, dict):
            return ""
        
        character_relations = relations_config.get(character_name, {})
        if not isinstance(character_relations, dict):
            return ""
        
        entries = []
        for target, score in character_relations.items():
            if target == character_name:
                continue
            
            try:
                score_int = int(score)
                category = self._relation_category(score_int)
                entries.append(f"{target}:{score_int:+d}（{category}）")
            except (ValueError, TypeError):
                continue
        
        return "；".join(entries)
    
    def _relation_category(self, score: int) -> str:
        """获取关系类别
        
        Args:
            score: 关系分数
            
        Returns:
            str: 关系类别
        """
        if score >= 60:
            return "挚友"
        elif score >= 40:
            return "亲密同伴"
        elif score >= 10:
            return "盟友"
        elif score <= -60:
            return "死敌"
        elif score <= -40:
            return "仇视"
        elif score <= -10:
            return "敌对"
        else:
            return "中立"
    
    def _add_response_to_history(
        self,
        agent_name: str,
        input_data: Any,
        response: Any,
        success: bool,
        error: Optional[str]
    ) -> None:
        """添加响应到历史记录
        
        Args:
            agent_name: 代理名称
            input_data: 输入数据
            response: 响应数据
            success: 是否成功
            error: 错误信息
        """
        entry = {
            "agent_name": agent_name,
            "input_data": str(input_data),
            "response": str(response) if response else None,
            "success": success,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self._response_history.append(entry)
        
        # 限制历史记录大小
        if len(self._response_history) > self._max_history_size:
            self._response_history = self._response_history[-self._max_history_size:]
    
    def _execute_command_internal(self, command: Any) -> Any:
        """内部命令执行方法
        
        Args:
            command: 要执行的命令
            
        Returns:
            Any: 命令执行结果
        """
        raise NotImplementedError("AgentService does not execute commands directly")
    
    def _execute_query_internal(self, query: Any) -> Any:
        """内部查询执行方法
        
        Args:
            query: 要执行的查询
            
        Returns:
            Any: 查询结果
        """
        raise NotImplementedError("AgentService does not execute queries directly")
    
    def force_cleanup_all_agents(self) -> CommandResult:
        """强制清理所有代理
        
        这是一个防御性方法，用于在系统出现异常状态时重置所有代理。
        
        Returns:
            CommandResult: 清理结果
        """
        try:
            self._logger.warning("Force cleaning up all agents")
            
            cleanup_count = 0
            errors = []
            
            # 停用所有活跃代理
            active_agents = list(self._active_agents.keys())
            for agent_name in active_agents:
                try:
                    result = self.deactivate_agent(agent_name, force=True)
                    if result.success:
                        cleanup_count += 1
                    else:
                        errors.append(f"Failed to cleanup agent {agent_name}: {result.message}")
                except Exception as e:
                    errors.append(f"Error cleaning up agent {agent_name}: {str(e)}")
            
            # 清空所有代理列表
            self._agents.clear()
            self._agent_configs.clear()
            self._active_agents.clear()
            
            # 重置响应历史
            self._response_history.clear()
            
            self._logger.warning(f"Force cleanup completed: {cleanup_count} agents cleaned, {len(errors)} errors")
            
            return CommandResult.success_result(
                data={
                    "cleaned_agents": cleanup_count,
                    "errors": errors
                },
                message=f"Force cleanup completed: {cleanup_count} agents cleaned"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to force cleanup agents: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Force cleanup failed: {str(e)}", cause=e)
            )
    
    def reset_agent_state(self, agent_name: str) -> CommandResult:
        """重置代理状态
        
        Args:
            agent_name: 代理名称
            
        Returns:
            CommandResult: 重置结果
        """
        try:
            self._logger.debug(f"Resetting state for agent: {agent_name}")
            
            # 停用代理
            deactivate_result = self.deactivate_agent(agent_name, force=True)
            
            # 重新激活代理
            if agent_name in self._agents:
                agent = self._agents[agent_name]
                config = self._agent_configs.get(agent_name)
                
                if config:
                    # 尝试重新激活
                    try:
                        import asyncio
                        # 检查是否在事件循环中
                        try:
                            loop = asyncio.get_running_loop()
                            # 如果已经在事件循环中，创建任务
                            asyncio.create_task(agent.activate({}))
                        except RuntimeError:
                            # 如果不在事件循环中，创建新的事件循环
                            asyncio.run(agent.activate({}))
                        
                        self._active_agents[agent_name] = agent
                        
                        self._logger.debug(f"Agent state reset successfully: {agent_name}")
                        
                        return CommandResult.success_result(
                            data={
                                "agent_name": agent_name,
                                "deactivated": deactivate_result.success,
                                "reactivated": True
                            },
                            message=f"Agent {agent_name} state reset successfully"
                        )
                    except Exception as reactivate_error:
                        self._logger.error(f"Failed to reactivate agent {agent_name}: {reactivate_error}")
                        return CommandResult.failure_result(
                            ApplicationException(f"Agent reactivation failed: {str(reactivate_error)}", cause=reactivate_error)
                        )
            
            return CommandResult.failure_result(
                ApplicationException(f"Agent {agent_name} not found")
            )
            
        except Exception as e:
            self._logger.error(f"Failed to reset agent state {agent_name}: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Agent state reset failed: {str(e)}", cause=e)
            )
