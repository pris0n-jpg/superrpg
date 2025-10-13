"""
消息处理服务

该服务负责处理游戏中的消息和工具调用，从main.py中提取消息处理逻辑，
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。

消息处理服务负责：
1. 消息的解析和处理
2. 工具调用的识别和执行
3. 消息内容的清理和转换
4. 错误处理和日志记录
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .base import ApplicationService, CommandResult
from ...core.interfaces import EventBus, Logger, DomainEvent
from ...core.exceptions import ApplicationException, BusinessRuleException


class MessageReceivedEvent(DomainEvent):
    """消息接收事件"""
    
    def __init__(self, sender: str, content: str, metadata: Dict[str, Any]):
        super().__init__()
        self.sender = sender
        self.content = content
        self.metadata = metadata
    
    def get_event_type(self) -> str:
        return "MessageReceived"


class MessageProcessedEvent(DomainEvent):
    """消息处理事件"""
    
    def __init__(self, sender: str, original_content: str, processed_content: str, tool_calls: List[Dict[str, Any]]):
        super().__init__()
        self.sender = sender
        self.original_content = original_content
        self.processed_content = processed_content
        self.tool_calls = tool_calls
    
    def get_event_type(self) -> str:
        return "MessageProcessed"


class ToolCallEvent(DomainEvent):
    """工具调用事件"""
    
    def __init__(self, tool_name: str, parameters: Dict[str, Any], caller: str):
        super().__init__()
        self.tool_name = tool_name
        self.parameters = parameters
        self.caller = caller
    
    def get_event_type(self) -> str:
        return "ToolCall"


class ToolCallResultEvent(DomainEvent):
    """工具调用结果事件"""
    
    def __init__(self, tool_name: str, result: Any, success: bool, error: Optional[str] = None):
        super().__init__()
        self.tool_name = tool_name
        self.result = result
        self.success = success
        self.error = error
    
    def get_event_type(self) -> str:
        return "ToolCallResult"


@dataclass
class ToolCall:
    """工具调用
    
    封装工具调用的信息，包括工具名称、参数等。
    遵循单一职责原则，专门负责工具调用数据的封装。
    """
    name: str
    parameters: Dict[str, Any]
    raw_text: str
    start_pos: int
    end_pos: int
    
    def is_valid(self) -> bool:
        """检查工具调用是否有效
        
        Returns:
            bool: 是否有效
        """
        return bool(self.name and self.name.strip())


@dataclass
class ProcessedMessage:
    """处理后的消息
    
    封装处理后的消息信息，包括清理后的内容和工具调用。
    遵循单一职责原则，专门负责处理后消息数据的封装。
    """
    original_content: str
    cleaned_content: str
    tool_calls: List[ToolCall]
    sender: str
    metadata: Dict[str, Any]
    
    def has_tool_calls(self) -> bool:
        """检查是否有工具调用
        
        Returns:
            bool: 是否有工具调用
        """
        return len(self.tool_calls) > 0
    
    def get_valid_tool_calls(self) -> List[ToolCall]:
        """获取有效的工具调用
        
        Returns:
            List[ToolCall]: 有效的工具调用列表
        """
        return [call for call in self.tool_calls if call.is_valid()]


class ToolExecutor(ABC):
    """工具执行器接口
    
    定义工具执行的标准接口，遵循依赖倒置原则。
    """
    
    @abstractmethod
    def can_execute(self, tool_name: str) -> bool:
        """检查是否能执行指定工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否能执行
        """
        pass
    
    @abstractmethod
    def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            Any: 执行结果
        """
        pass


class MessageHandlerService(ApplicationService):
    """消息处理服务
    
    负责游戏中的消息处理和工具调用，包括消息解析、工具调用识别和执行。
    遵循单一职责原则，专门负责消息处理的核心功能。
    """
    
    # 工具调用正则表达式
    TOOL_CALL_PATTERN = re.compile(r"CALL_TOOL\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)")
    
    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        tool_executors: List[ToolExecutor] = None
    ):
        """初始化消息处理服务
        
        Args:
            event_bus: 事件总线
            logger: 日志记录器
            tool_executors: 工具执行器列表
        """
        super().__init__(event_bus, logger)
        self._tool_executors = tool_executors or []
        self._allowed_names: set = set()
        self._message_history: List[ProcessedMessage] = []
        self._max_history_size = 1000
    
    def set_allowed_names(self, names: List[str]) -> None:
        """设置允许的角色名称
        
        Args:
            names: 允许的角色名称列表
        """
        self._allowed_names = set(names)
        self._logger.info(f"Allowed names set to: {names}")
    
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
            # 发布消息接收事件
            self.publish_event(MessageReceivedEvent(
                sender=sender,
                content=content,
                metadata=metadata or {}
            ))
            
            # 处理消息
            processed_message = self._parse_message(sender, content, metadata or {})
            
            # 发布消息处理事件
            self.publish_event(MessageProcessedEvent(
                sender=sender,
                original_content=content,
                processed_content=processed_message.cleaned_content,
                tool_calls=[{
                    "name": call.name,
                    "parameters": call.parameters,
                    "raw_text": call.raw_text
                } for call in processed_message.tool_calls]
            ))
            
            # 添加到历史记录
            self._add_to_history(processed_message)
            
            return CommandResult.success_result(
                data={
                    "sender": sender,
                    "cleaned_content": processed_message.cleaned_content,
                    "tool_calls": [
                        {
                            "name": call.name,
                            "parameters": call.parameters,
                            "is_valid": call.is_valid()
                        }
                        for call in processed_message.tool_calls
                    ],
                    "has_tool_calls": processed_message.has_tool_calls()
                },
                message=f"Message processed from {sender}"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to process message from {sender}: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Message processing failed: {str(e)}", cause=e)
            )
    
    def execute_tool_calls(self, processed_message: ProcessedMessage) -> CommandResult:
        """执行工具调用
        
        Args:
            processed_message: 处理后的消息
            
        Returns:
            CommandResult: 执行结果
        """
        if not processed_message.has_tool_calls():
            return CommandResult.success_result(
                data={"results": []},
                message="No tool calls to execute"
            )
        
        try:
            results = []
            valid_calls = processed_message.get_valid_tool_calls()
            
            for tool_call in valid_calls:
                try:
                    # 验证工具调用
                    validation_result = self._validate_tool_call(tool_call, processed_message.sender)
                    if not validation_result.success:
                        results.append({
                            "tool_name": tool_call.name,
                            "success": False,
                            "error": validation_result.message,
                            "parameters": tool_call.parameters
                        })
                        continue
                    
                    # 发布工具调用事件
                    self.publish_event(ToolCallEvent(
                        tool_name=tool_call.name,
                        parameters=tool_call.parameters,
                        caller=processed_message.sender
                    ))
                    
                    # 执行工具调用
                    tool_result = self._execute_tool(tool_call.name, tool_call.parameters)
                    
                    # 发布工具调用结果事件
                    self.publish_event(ToolCallResultEvent(
                        tool_name=tool_call.name,
                        result=tool_result,
                        success=True
                    ))
                    
                    results.append({
                        "tool_name": tool_call.name,
                        "success": True,
                        "result": tool_result,
                        "parameters": tool_call.parameters
                    })
                    
                    self._logger.info(f"Tool {tool_call.name} executed successfully by {processed_message.sender}")
                    
                except Exception as e:
                    # 发布工具调用结果事件（失败）
                    self.publish_event(ToolCallResultEvent(
                        tool_name=tool_call.name,
                        result=None,
                        success=False,
                        error=str(e)
                    ))
                    
                    results.append({
                        "tool_name": tool_call.name,
                        "success": False,
                        "error": str(e),
                        "parameters": tool_call.parameters
                    })
                    
                    self._logger.error(f"Tool {tool_call.name} execution failed: {e}")
            
            return CommandResult.success_result(
                data={"results": results},
                message=f"Executed {len(valid_calls)} tool calls"
            )
            
        except Exception as e:
            self._logger.error(f"Failed to execute tool calls: {e}")
            return CommandResult.failure_result(
                ApplicationException(f"Tool execution failed: {str(e)}", cause=e)
            )
    
    def get_message_history(self, sender: Optional[str] = None, limit: Optional[int] = None) -> List[ProcessedMessage]:
        """获取消息历史
        
        Args:
            sender: 发送者过滤器
            limit: 返回的最大数量
            
        Returns:
            List[ProcessedMessage]: 消息历史列表
        """
        history = self._message_history.copy()
        
        if sender:
            history = [msg for msg in history if msg.sender == sender]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def _parse_message(self, sender: str, content: str, metadata: Dict[str, Any]) -> ProcessedMessage:
        """解析消息
        
        Args:
            sender: 发送者
            content: 消息内容
            metadata: 消息元数据
            
        Returns:
            ProcessedMessage: 处理后的消息
        """
        # 解析工具调用
        tool_calls = self._parse_tool_calls(content)
        
        # 清理消息内容
        cleaned_content = self._strip_tool_calls_from_text(content)
        
        return ProcessedMessage(
            original_content=content,
            cleaned_content=cleaned_content,
            tool_calls=tool_calls,
            sender=sender,
            metadata=metadata
        )
    
    def _parse_tool_calls(self, text: str) -> List[ToolCall]:
        """解析工具调用
        
        Args:
            text: 文本内容
            
        Returns:
            List[ToolCall]: 工具调用列表
        """
        calls = []
        
        if not text:
            return calls
        
        idx = 0
        while True:
            match = self.TOOL_CALL_PATTERN.search(text, idx)
            if not match:
                break
            
            tool_name = match.group("name")
            scan_from = match.end()
            
            # 提取JSON参数
            json_body, end_pos = self._extract_json_after(text, scan_from)
            
            parameters = {}
            if json_body:
                try:
                    parameters = json.loads(json_body)
                except json.JSONDecodeError:
                    parameters = {}
                
                calls.append(ToolCall(
                    name=tool_name,
                    parameters=parameters,
                    raw_text=text[match.start():end_pos],
                    start_pos=match.start(),
                    end_pos=end_pos
                ))
                
                idx = end_pos
            else:
                idx = scan_from
        
        return calls
    
    def _extract_json_after(self, s: str, start_pos: int) -> Tuple[Optional[str], int]:
        """从指定位置提取JSON对象
        
        Args:
            s: 字符串
            start_pos: 开始位置
            
        Returns:
            Tuple[Optional[str], int]: JSON文本和结束位置
        """
        n = len(s)
        i = s.find("{", start_pos)
        if i == -1:
            return None, start_pos
        
        brace = 0
        in_str = False
        esc = False
        j = i
        
        while j < n:
            ch = s[j]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == '{':
                    brace += 1
                elif ch == '}':
                    brace -= 1
                    if brace == 0:
                        return s[i:j+1], j+1
            j += 1
        
        return None, start_pos
    
    def _strip_tool_calls_from_text(self, text: str) -> str:
        """从文本中移除工具调用
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return text
        
        idx = 0
        out_parts = []
        
        while True:
            match = self.TOOL_CALL_PATTERN.search(text, idx)
            if not match:
                out_parts.append(text[idx:])
                break
            
            out_parts.append(text[idx:match.start()])
            scan_from = match.end()
            
            json_body, end_pos = self._extract_json_after(text, scan_from)
            if json_body:
                idx = end_pos
            else:
                idx = scan_from
        
        return "".join(out_parts)
    
    def _validate_tool_call(self, tool_call: ToolCall, caller: str) -> CommandResult:
        """验证工具调用
        
        Args:
            tool_call: 工具调用
            caller: 调用者
            
        Returns:
            CommandResult: 验证结果
        """
        # 检查工具名称是否有效
        if not tool_call.is_valid():
            return CommandResult.failure_result(
                ApplicationException(f"Invalid tool name: {tool_call.name}")
            )
        
        # 检查是否有执行器
        if not any(executor.can_execute(tool_call.name) for executor in self._tool_executors):
            return CommandResult.failure_result(
                ApplicationException(f"No executor found for tool: {tool_call.name}")
            )
        
        # 检查调用者是否在允许列表中
        if self._allowed_names and caller not in self._allowed_names:
            return CommandResult.failure_result(
                ApplicationException(f"Caller {caller} not in allowed list")
            )
        
        # 检查参数中的角色名称
        invalid_actor = self._check_parameters_for_invalid_actors(tool_call.parameters)
        if invalid_actor:
            return CommandResult.failure_result(
                ApplicationException(f"Invalid actor name: {invalid_actor}")
            )
        
        return CommandResult.success_result()
    
    def _check_parameters_for_invalid_actors(self, parameters: Dict[str, Any]) -> Optional[str]:
        """检查参数中的无效角色名称
        
        Args:
            parameters: 参数字典
            
        Returns:
            Optional[str]: 无效的角色名称，如果没有则返回None
        """
        if not self._allowed_names:
            return None
        
        # 定义可能包含角色名称的参数键
        name_keys = {
            "perform_attack": ["attacker", "defender"],
            "auto_engage": ["attacker", "defender"],
            "perform_skill_check": ["name"],
            "advance_position": ["name"],
            "adjust_relation": ["a", "b"],
            "transfer_item": ["target"],
        }
        
        # 检查工具名称对应的参数
        for tool_name, keys in name_keys.items():
            if tool_name in parameters:
                tool_params = parameters[tool_name]
                if isinstance(tool_params, dict):
                    for key in keys:
                        if key in tool_params:
                            actor_name = tool_params[key]
                            if isinstance(actor_name, str) and actor_name not in self._allowed_names:
                                return actor_name
        
        return None
    
    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            
        Returns:
            Any: 执行结果
        """
        for executor in self._tool_executors:
            if executor.can_execute(tool_name):
                return executor.execute(tool_name, parameters)
        
        raise ApplicationException(f"No executor found for tool: {tool_name}")
    
    def _add_to_history(self, message: ProcessedMessage) -> None:
        """添加消息到历史记录
        
        Args:
            message: 处理后的消息
        """
        self._message_history.append(message)
        
        # 限制历史记录大小
        if len(self._message_history) > self._max_history_size:
            self._message_history = self._message_history[-self._max_history_size:]
    
    def _execute_command_internal(self, command: Any) -> Any:
        """内部命令执行方法
        
        Args:
            command: 要执行的命令
            
        Returns:
            Any: 命令执行结果
        """
        raise NotImplementedError("MessageHandlerService does not execute commands directly")
    
    def _execute_query_internal(self, query: Any) -> Any:
        """内部查询执行方法
        
        Args:
            query: 要执行的查询
            
        Returns:
            Any: 查询结果
        """
        raise NotImplementedError("MessageHandlerService does not execute queries directly")