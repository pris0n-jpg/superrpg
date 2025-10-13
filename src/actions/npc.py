from __future__ import annotations

"""
Domain-level action wrappers via dependency injection.

This module exposes a factory `make_npc_actions(world=...)` which returns
- a tool list for agent registration, and
- a tool dispatch dict for central orchestration.

现在支持新旧架构：
- 如果新架构可用，通过适配器使用新工具系统
- 否则使用原有的实现方式
"""

import logging
from typing import Optional, Any, Tuple, List, Dict

# 导入新架构的适配器
try:
    from ..adapters.tools_adapter import default_tools_adapter
    from ..core.container import ServiceLocator
    from ...core.interfaces import ToolExecutor
    USE_NEW_ARCHITECTURE = True
except ImportError:
    # 如果新架构不可用，使用原有实现
    default_tools_adapter = None
    ServiceLocator = None
    ToolExecutor = None
    USE_NEW_ARCHITECTURE = False

# 设置日志
_ACTION_LOGGER = logging.getLogger("npc_talk_demo")


def _log_action(msg: str) -> None:
    try:
        if not msg:
            return
        _ACTION_LOGGER.info(f"[ACTION] {msg}")
    except Exception:
        pass


def make_npc_actions(*, world: Any) -> Tuple[List[object], Dict[str, object]]:
    """Create action tools bound to a provided world API (duck-typed).

    该函数现在支持新旧架构：
    - 如果新架构可用，通过适配器使用新工具系统
    - 否则使用原有的实现方式

    The `world` object is expected to provide functions:
      - attack_roll_dnd(...)
      - skill_check_dnd(...)
      - move_towards(...)
      - set_relation(...)
      - grant_item(...)
    """
    # 尝试使用新架构
    if USE_NEW_ARCHITECTURE and default_tools_adapter:
        try:
            _ACTION_LOGGER.info("使用新架构创建NPC工具")
            return default_tools_adapter.initialize_tools()
        except Exception as e:
            _ACTION_LOGGER.warning(f"新架构创建工具失败，回退到原有实现: {str(e)}")
    
    # 使用原有实现
    _ACTION_LOGGER.info("使用原有实现创建NPC工具")

    def perform_attack(
        attacker,
        defender,
        ability: str = "STR",
        proficient: bool = False,
        target_ac: Optional[int] = None,
        damage_expr: str = "1d4+STR",
        advantage: str = "none",
        auto_move: bool = False,
    ):
        resp = world.attack_roll_dnd(
            attacker=attacker,
            defender=defender,
            ability=ability,
            proficient=proficient,
            target_ac=target_ac,
            damage_expr=damage_expr,
            advantage=advantage,
            auto_move=auto_move,
        )
        meta = resp.metadata or {}
        hit = meta.get("hit")
        dmg = meta.get("damage_total")
        hp_before = meta.get("hp_before")
        hp_after = meta.get("hp_after")
        _log_action(
            f"attack {attacker} -> {defender} | hit={hit} dmg={dmg} hp:{hp_before}->{hp_after} "
            f"reach_ok={meta.get('reach_ok')} auto_move={auto_move}"
        )
        return resp

    def auto_engage(
        attacker,
        defender,
        ability: str = "STR",
        proficient: bool = False,
        target_ac: Optional[int] = None,
        damage_expr: str = "1d4+STR",
        advantage: str = "none",
    ):
        return perform_attack(
            attacker=attacker,
            defender=defender,
            ability=ability,
            proficient=proficient,
            target_ac=target_ac,
            damage_expr=damage_expr,
            advantage=advantage,
            auto_move=True,
        )

    def perform_skill_check(name, skill, dc, advantage: str = "none"):
        resp = world.skill_check_dnd(name=name, skill=skill, dc=dc, advantage=advantage)
        meta = resp.metadata or {}
        success = meta.get("success")
        total = meta.get("total")
        roll = meta.get("roll")
        _log_action(
            f"skill_check {name} skill={skill} dc={dc} -> success={success} total={total} roll={roll}"
        )
        return resp

    def advance_position(name, target, steps):
        # 增强参数验证：确保所有参数都有效
        if not name or not isinstance(name, str):
            raise ValueError("角色名称必须是非空字符串")
        
        # 尝试将字符串转换为整数（AI模型可能将数字格式化为字符串）
        try:
            steps_int = int(steps)
        except (ValueError, TypeError):
            raise ValueError("步数必须是数字")
        
        if steps_int < 0:
            raise ValueError("步数必须是非负数")
        
        steps = steps_int  # 确保步数是整数
        
        # 验证并解析目标坐标
        tgt = None
        if isinstance(target, dict):
            if "x" not in target or "y" not in target:
                raise ValueError("目标字典必须包含 'x' 和 'y' 键")
            try:
                tx = int(target["x"])
                ty = int(target["y"])
                tgt = (tx, ty)
            except (ValueError, TypeError):
                raise ValueError("目标坐标必须是整数")
        elif isinstance(target, (list, tuple)) and len(target) >= 2:
            try:
                tx = int(target[0])
                ty = int(target[1])
                tgt = (tx, ty)
            except (ValueError, TypeError):
                raise ValueError("目标坐标必须是整数")
        elif isinstance(target, str):
            # 尝试解析JSON字符串（AI模型可能将字典格式化为字符串）
            try:
                import json
                parsed = json.loads(target)
                if isinstance(parsed, dict) and "x" in parsed and "y" in parsed:
                    tx = int(parsed["x"])
                    ty = int(parsed["y"])
                    tgt = (tx, ty)
                elif isinstance(parsed, (list, tuple)) and len(parsed) >= 2:
                    tx = int(parsed[0])
                    ty = int(parsed[1])
                    tgt = (tx, ty)
                else:
                    raise ValueError("无法解析目标字符串")
            except (json.JSONDecodeError, ValueError, TypeError):
                raise ValueError("目标字符串格式无效")
        else:
            raise ValueError("目标必须是字典、列表/元组或有效的JSON字符串")
        
        # 验证坐标范围（可选：添加合理的边界检查）
        if tgt[0] < -1000 or tgt[0] > 1000 or tgt[1] < -1000 or tgt[1] > 1000:
            raise ValueError("目标坐标超出合理范围 (-1000 到 1000)")
        
        resp = world.move_towards(name=name, target=tgt, steps=steps)
        meta = resp.metadata or {}
        _log_action(
            f"move {name} -> {tgt} steps={steps} moved={meta.get('moved')} remaining={meta.get('remaining')}"
        )
        return resp

    def adjust_relation(a, b, value, reason: str = ""):
        # Set relation to an absolute target value instead of applying a delta
        resp = world.set_relation(a, b, int(value), reason or "")
        meta = resp.metadata or {}
        _log_action(
            f"relation {a}->{b} set={value} score={meta.get('score')} reason={reason or '无'}"
        )
        return resp

    def transfer_item(target, item, n: int = 1):
        resp = world.grant_item(target=target, item=item, n=int(n))
        meta = resp.metadata or {}
        _log_action(
            f"transfer item={item} -> {target} qty={n} total={meta.get('count')}"
        )
        return resp

    tool_list: List[object] = [
        perform_attack,
        auto_engage,
        advance_position,
        adjust_relation,
        transfer_item,
    ]
    tool_dispatch: Dict[str, object] = {
        "perform_attack": perform_attack,
        "advance_position": advance_position,
        "adjust_relation": adjust_relation,
        "transfer_item": transfer_item,
        "auto_engage": auto_engage,
    }

    return tool_list, tool_dispatch


__all__ = ["make_npc_actions"]
