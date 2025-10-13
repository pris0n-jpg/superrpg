from __future__ import annotations

import os
import logging
from typing import Iterable, Optional, Mapping, Any, List

from agentscope.agent import ReActAgent  # type: ignore
from agentscope.formatter import OpenAIChatFormatter  # type: ignore
from agentscope.memory import InMemoryMemory  # type: ignore
from agentscope.model import OpenAIChatModel  # type: ignore
from agentscope.tool import Toolkit  # type: ignore
from agentscope.message import Msg  # type: ignore

# 导入新架构的适配器
try:
    from ..adapters.agents_adapter import default_agents_adapter
    from ..core.container import ServiceLocator
    from ...core.interfaces import AgentService
    USE_NEW_ARCHITECTURE = True
except ImportError:
    # 如果新架构不可用，使用原有实现
    default_agents_adapter = None
    ServiceLocator = None
    AgentService = None
    USE_NEW_ARCHITECTURE = False

# 设置日志
logger = logging.getLogger(__name__)


DEFAULT_INTENT_SCHEMA = (
    '{{\n  "intent": "attack|talk|investigate|move|assist|use_item|wait",\n'
    '  "target": "目标名称",\n  "skill": "perception|medicine|...",\n'
    '  "ability": "STR|DEX|CON|INT|WIS|CHA",\n  "proficient": true,\n  "dc_hint": 12,\n'
    '  "damage_expr": "1d4+STR",\n  "time_cost": 1\n}}'
)

DEFAULT_PROMPT_HEADER = (
    "你是游戏中的NPC：{name}。\n"
    "人设：{persona}\n"
    "外观特征：{appearance}\n"
    "常用语气/台词：{quotes}\n"
    "当前立场提示（仅你视角）：{relation_brief}\n"
)
DEFAULT_PROMPT_RULES = (
    "对话要求：\n"
    "- 先用中文说1-2句对白/想法/微动作，符合人设。\n"
    "- 当需要执行行动时，直接调用工具（格式：CALL_TOOL tool_name({{\"key\": \"value\"}}))，不要再输出意图 JSON。\n"
    "- 调用工具后等待系统反馈，再根据结果做简短评论或继续对白。\n"
    "- 行动前对照上方立场提示：≥40 视为亲密同伴（避免攻击、优先支援），≥10 为盟友（若要伤害需先说明理由），≤-10 才视为敌方目标，其余保持谨慎中立。\n"
    "- 若必须违背既定关系行事，请在对白中说明充分理由，否则拒绝执行。\n"
    "- 参与者名称（仅可用）：{allowed_names}\n"
)

DEFAULT_PROMPT_TOOL_GUIDE = (
    "可用工具：\n"
    "- perform_attack(attacker, defender, ability='STR', proficient=False, target_ac=None, damage_expr='1d4+STR', advantage='none', auto_move=False)：发动攻击并自动结算伤害；若距离不足可令 auto_move=True 尝试先靠近。\n"
    "- auto_engage(attacker, defender, ability='STR', ...)：先移动到触及范围，再进行一次近战攻击。\n"
    "- advance_position(name, target, steps)：朝指定坐标逐步接近，target可以是字典{{\"x\": 1, \"y\": 1}}或列表[1, 1]。\n"
    "- adjust_relation(a, b, value, reason='')：在合适情境下将关系直接设为目标值。\n"
    "- transfer_item(target, item, n=1)：移交或分配物资。\n"
)

DEFAULT_PROMPT_EXAMPLE = (
    "输出示例：\n"
    "阿米娅压低声音：'靠近目标位置。'\n"
    'CALL_TOOL advance_position({{"name": "Amiya", "target": {{"x": 1, "y": 1}}, "steps": 2}})\n'
)

DEFAULT_PROMPT_TEMPLATE = (
    DEFAULT_PROMPT_HEADER + DEFAULT_PROMPT_RULES + DEFAULT_PROMPT_TOOL_GUIDE + DEFAULT_PROMPT_EXAMPLE
)


class SafeOpenAIChatFormatter(OpenAIChatFormatter):
    """自定义格式化器，处理 get_content_blocks() 返回 None 的情况"""
    
    async def _format(self, messages: List[Msg]) -> List[dict]:
        """重写 _format 方法，添加对 None 值的检查"""
        # 检查整个消息列表是否为None
        if messages is None:
            logger.warning("SafeOpenAIChatFormatter: messages list is None, creating default message")
            return [{
                "role": "system",
                "content": "请继续游戏对话。",
                "name": "System"
            }]
        
        # 确保messages是一个列表
        if not isinstance(messages, list):
            logger.warning(f"SafeOpenAIChatFormatter: messages is not a list (type: {type(messages)}), converting to list")
            try:
                messages = [messages]
            except Exception:
                logger.error("SafeOpenAIChatFormatter: failed to convert messages to list, using default message")
                return [{
                    "role": "system",
                    "content": "请继续游戏对话。",
                    "name": "System"
                }]
        
        # 检查消息列表是否为空
        if len(messages) == 0:
            logger.warning("SafeOpenAIChatFormatter: messages list is empty, creating default message")
            return [{
                "role": "system",
                "content": "请继续游戏对话。",
                "name": "System"
            }]
        
        formatted = []
        for msg in messages:
            try:
                # 检查消息是否为 None
                if msg is None:
                    logger.debug("SafeOpenAIChatFormatter: skipping None message")
                    continue
                    
                # 调用父类的 _format 方法
                parent_formatted = await super()._format([msg])
                if parent_formatted:
                    formatted.extend(parent_formatted)
            except Exception as e:
                # 如果出现错误，尝试创建一个基本的格式化消息
                try:
                    name = getattr(msg, "name", "Unknown")
                    content = getattr(msg, "content", "")
                    role = getattr(msg, "role", "assistant")
                    
                    # 确保内容不为 None
                    if content is None:
                        content = ""
                        
                    formatted.append({
                        "role": role,
                        "content": str(content),
                        "name": name
                    })
                    logger.debug(f"SafeOpenAIChatFormatter: created fallback message for {name}")
                except Exception as fallback_error:
                    # 如果还是失败，跳过此消息
                    logger.error(f"SafeOpenAIChatFormatter: failed to create fallback message: {fallback_error}")
                    continue
        
        # 如果没有成功格式化任何消息，创建一个默认消息
        if len(formatted) == 0:
            logger.warning("SafeOpenAIChatFormatter: no messages were successfully formatted, creating default message")
            return [{
                "role": "system",
                "content": "请继续游戏对话。",
                "name": "System"
            }]
        
        return formatted


def _join_lines(tpl):
    if isinstance(tpl, list):
        try:
            return "\n".join(str(x) for x in tpl)
        except Exception:
            return "\n".join(tpl)
    return tpl


def make_kimi_npc(
    name: str,
    persona: str,
    model_cfg: Mapping[str, Any],
    prompt_template: Optional[str | list[str]] = None,
    allowed_names: Optional[str] = None,
    appearance: Optional[str] = None,
    quotes: Optional[list[str] | str] = None,
    relation_brief: Optional[str] = None,
    tools: Optional[Iterable[object]] = None,
) -> ReActAgent:
    """Create an LLM-backed NPC using Kimi's OpenAI-compatible API.
    
    该函数现在支持新旧架构：
    - 如果新架构可用，通过适配器创建代理
    - 否则使用原有的实现方式
    """
    # 尝试使用新架构
    if USE_NEW_ARCHITECTURE and default_agents_adapter:
        try:
            logger.info(f"使用新架构创建代理: {name}")
            return default_agents_adapter.create_agent(
                name=name,
                persona=persona,
                model_cfg=model_cfg,
                prompt_template=prompt_template,
                allowed_names=allowed_names,
                appearance=appearance,
                quotes=quotes,
                relation_brief=relation_brief,
                tools=tools
            )
        except Exception as e:
            logger.warning(f"新架构创建代理失败，回退到原有实现: {str(e)}")
    
    # 使用原有实现
    logger.info(f"使用原有实现创建代理: {name}")
    api_key = str(model_cfg.get("api_key") or "")
    if not api_key:
        raise ValueError(
            "API密钥未配置。请在 configs/model.json 中设置 api_key，"
            "或复制 configs/model.json.template 为 configs/model.json 并填入您的API密钥。"
        )
    base_url = str(model_cfg.get("base_url") or "https://chat.sjtu.plus/v1")
    sec = dict(model_cfg.get("npc") or {})
    model_name = sec.get("model") or "z-ai/glm-4.6"

    tools_text = "perform_attack(), auto_engage(), advance_position(), adjust_relation(), transfer_item()"
    intent_schema = DEFAULT_INTENT_SCHEMA
    tpl = _join_lines(prompt_template)

    appearance_text = (appearance or "外观描写未提供，可根据设定自行补充细节。").strip()
    if not appearance_text:
        appearance_text = "外观描写未提供，可根据设定自行补充细节。"
    if isinstance(quotes, (list, tuple)):
        quote_items = [str(q).strip() for q in quotes if str(q).strip()]
        quotes_text = " / ".join(quote_items)
    elif isinstance(quotes, str):
        quotes_text = quotes.strip()
    else:
        quotes_text = "保持原角色语气自行发挥。"
    if not quotes_text:
        quotes_text = "保持原角色语气自行发挥。"

    relation_text = (relation_brief or "暂无明确关系记录，默认保持谨慎中立。").strip()
    if not relation_text:
        relation_text = "暂无明确关系记录，默认保持谨慎中立。"

    format_args = {
        "name": name,
        "persona": persona,
        "appearance": appearance_text,
        "quotes": quotes_text,
        "relation_brief": relation_text,
        "tools": tools_text,
        "intent_schema": intent_schema,
        "allowed_names": allowed_names or "Doctor, Amiya",
    }

    sys_prompt = None
    if tpl:
        try:
            sys_prompt = tpl.format(**format_args)
        except Exception:
            sys_prompt = None
    if not sys_prompt:
        try:
            sys_prompt = DEFAULT_PROMPT_TEMPLATE.format(**format_args)
        except Exception:
            sys_prompt = DEFAULT_PROMPT_TEMPLATE.format(
                name=name,
                persona=persona,
                appearance=appearance_text,
                quotes=quotes_text,
                allowed_names=allowed_names or "Doctor, Amiya",
                intent_schema=intent_schema,
                tools=tools_text,
                relation_brief=relation_text,
            )

    model = OpenAIChatModel(
        model_name=model_name,
        api_key=api_key,
        stream=bool(sec.get("stream", True)),
        client_args={"base_url": base_url},
        generate_kwargs={"temperature": float(sec.get("temperature", 0.7))},
    )

    toolkit = Toolkit()
    if tools:
        for fn in tools:
            try:
                toolkit.register_tool_function(fn)  # type: ignore[arg-type]
            except Exception:
                continue

    return ReActAgent(
        name=name,
        sys_prompt=sys_prompt,
        model=model,
        formatter=SafeOpenAIChatFormatter(),  # 使用自定义的安全格式化器
        memory=InMemoryMemory(),
        toolkit=toolkit,
    )
