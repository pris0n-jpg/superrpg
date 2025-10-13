"""
战斗领域模型
包含战斗的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum

from .base import Entity, ValueObject, AggregateRoot
from .characters import Character, Position


class RangeBand(Enum):
    """距离带枚举"""
    ENGAGED = "engaged"
    NEAR = "near"
    FAR = "far"
    LONG = "long"


class CoverLevel(Enum):
    """掩体等级枚举"""
    NONE = "none"
    HALF = "half"
    THREE_QUARTERS = "three_quarters"
    TOTAL = "total"


class CombatState(Enum):
    """战斗状态枚举"""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"


@dataclass(frozen=True)
class TurnState(ValueObject):
    """回合状态值对象"""
    action_used: bool = False
    bonus_used: bool = False
    reaction_available: bool = True
    move_left: int = 6
    disengage: bool = False
    dodge: bool = False
    help_target: Optional[str] = None
    ready: Optional[Dict[str, any]] = None


@dataclass(frozen=True)
class InitiativeScore(ValueObject):
    """先攻值对象"""
    character_name: str
    score: int
    dexterity_modifier: int

    def __lt__(self, other: 'InitiativeScore') -> bool:
        """先攻排序：分数 > 敏捷修正 > 名称"""
        if self.score != other.score:
            return self.score > other.score  # 降序
        if self.dexterity_modifier != other.dexterity_modifier:
            return self.dexterity_modifier > other.dexterity_modifier
        return self.character_name < other.character_name


@dataclass
class Combat(AggregateRoot):
    """战斗聚合根"""
    location: str
    participants: List[str] = field(default_factory=list)
    initiative_order: List[str] = field(default_factory=list)
    initiative_scores: Dict[str, int] = field(default_factory=dict)
    round: int = 1
    turn_idx: int = 0
    state: CombatState = CombatState.NOT_STARTED
    turn_states: Dict[str, TurnState] = field(default_factory=dict)
    range_bands: Dict[Tuple[str, str], RangeBand] = field(default_factory=dict)
    cover: Dict[str, CoverLevel] = field(default_factory=dict)
    triggers: List[Dict[str, any]] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.location:
            raise ValueError("战斗地点不能为空")
        if self.state == CombatState.NOT_STARTED and self.participants:
            self.state = CombatState.ACTIVE

    @property
    def current_actor(self) -> Optional[str]:
        """获取当前行动角色"""
        if not self.is_active or not self.initiative_order:
            return None
        if self.turn_idx < 0 or self.turn_idx >= len(self.initiative_order):
            return None
        return self.initiative_order[self.turn_idx]

    @property
    def is_active(self) -> bool:
        """检查战斗是否活跃"""
        return self.state == CombatState.ACTIVE

    def start_combat(self, participants: List[str]) -> None:
        """开始战斗"""
        if self.state != CombatState.NOT_STARTED:
            raise ValueError("战斗已经开始")
        
        self.participants = list(participants)
        self.roll_initiative()
        self.state = CombatState.ACTIVE
        self._reset_turn_tokens_for_current_actor()
        
        self.add_domain_event("combat_started", {
            "location": self.location,
            "participants": self.participants,
            "initiative_order": self.initiative_order
        })

    def roll_initiative(self) -> None:
        """掷先攻"""
        import random
        
        scores = {}
        for name in self.participants:
            # 这里应该从角色模型获取敏捷修正值
            # 暂时使用随机值
            dexterity_mod = 0  # TODO: 从角色获取
            score = random.randint(1, 20) + dexterity_mod
            scores[name] = score
        
        # 按先攻值排序
        self.initiative_scores = scores
        self.initiative_order = sorted(
            self.participants,
            key=lambda name: (
                scores[name],
                0  # TODO: 从角色获取敏捷修正值
            ),
            reverse=True
        )
        
        self.add_domain_event("initiative_rolled", {
            "scores": scores,
            "order": self.initiative_order
        })

    def end_combat(self) -> None:
        """结束战斗"""
        self.state = CombatState.ENDED
        self.clear_all_domain_events()
        
        self.add_domain_event("combat_ended", {
            "location": self.location,
            "round": self.round
        })

    def next_turn(self) -> Optional[str]:
        """推进到下一个回合"""
        if not self.is_active:
            return None
        
        if not self.initiative_order:
            return None
        
        # 寻找下一个存活的角色
        original_idx = self.turn_idx
        n = len(self.initiative_order)
        
        for step in range(1, n + 1):
            idx = (original_idx + step) % n
            if idx <= original_idx:
                self.round += 1
            
            candidate = self.initiative_order[idx]
            # TODO: 检查角色是否存活
            if True:  # 暂时假设所有角色都存活
                self.turn_idx = idx
                self._reset_turn_tokens_for_current_actor()
                
                self.add_domain_event("turn_changed", {
                    "round": self.round,
                    "actor": candidate,
                    "turn_idx": self.turn_idx
                })
                
                return candidate
        
        # 没有可行动的角色
        return None

    def _reset_turn_tokens_for_current_actor(self) -> None:
        """为当前行动者重置回合资源"""
        if not self.current_actor:
            return
        
        actor = self.current_actor
        # TODO: 从角色获取移动力
        move_speed = 6  # 默认移动力
        
        self.turn_states[actor] = TurnState(
            action_used=False,
            bonus_used=False,
            reaction_available=True,
            move_left=move_speed,
            disengage=False,
            dodge=False,
            help_target=None,
            ready=None
        )

    def use_action(self, character_name: str, action_type: str = "action") -> bool:
        """使用动作"""
        if character_name != self.current_actor:
            return False
        
        turn_state = self.turn_states.get(character_name)
        if not turn_state:
            return False
        
        if action_type == "action" and not turn_state.action_used:
            new_state = turn_state._replace(action_used=True)
            self.turn_states[character_name] = new_state
            return True
        elif action_type == "bonus" and not turn_state.bonus_used:
            new_state = turn_state._replace(bonus_used=True)
            self.turn_states[character_name] = new_state
            return True
        elif action_type == "reaction" and turn_state.reaction_available:
            new_state = turn_state._replace(reaction_available=False)
            self.turn_states[character_name] = new_state
            return True
        
        return False

    def consume_movement(self, character_name: str, distance: int) -> bool:
        """消耗移动力"""
        if character_name != self.current_actor:
            return False
        
        turn_state = self.turn_states.get(character_name)
        if not turn_state:
            return False
        
        if distance <= turn_state.move_left:
            new_state = turn_state._replace(
                move_left=turn_state.move_left - distance
            )
            self.turn_states[character_name] = new_state
            return True
        
        return False

    def set_range_band(self, char_a: str, char_b: str, band: RangeBand) -> None:
        """设置两个角色间的距离带"""
        key = tuple(sorted([char_a, char_b]))
        self.range_bands[key] = band
        
        self.add_domain_event("range_band_changed", {
            "character_a": char_a,
            "character_b": char_b,
            "range_band": band.value
        })

    def get_range_band(self, char_a: str, char_b: str) -> RangeBand:
        """获取两个角色间的距离带"""
        key = tuple(sorted([char_a, char_b]))
        return self.range_bands.get(key, RangeBand.NEAR)

    def set_cover(self, character_name: str, level: CoverLevel) -> None:
        """设置角色的掩体等级"""
        self.cover[character_name] = level
        
        self.add_domain_event("cover_changed", {
            "character": character_name,
            "cover_level": level.value
        })

    def get_cover(self, character_name: str) -> CoverLevel:
        """获取角色的掩体等级"""
        return self.cover.get(character_name, CoverLevel.NONE)

    def get_cover_bonus(self, character_name: str) -> Tuple[int, bool]:
        """获取掩体加值"""
        level = self.get_cover(character_name)
        if level == CoverLevel.HALF:
            return 2, False
        elif level == CoverLevel.THREE_QUARTERS:
            return 5, False
        elif level == CoverLevel.TOTAL:
            return 0, True
        else:
            return 0, False

    def queue_trigger(self, trigger_type: str, payload: Dict[str, any]) -> None:
        """添加触发器到队列"""
        self.triggers.append({
            "type": trigger_type,
            "payload": payload
        })

    def pop_triggers(self) -> List[Dict[str, any]]:
        """获取并清空触发器队列"""
        triggers = self.triggers.copy()
        self.triggers.clear()
        return triggers

    def snapshot(self) -> Dict[str, Any]:
        """获取战斗状态快照
        
        Returns:
            Dict[str, Any]: 战斗状态快照
        """
        return {
            "location": self.location,
            "participants": list(self.participants),
            "initiative_order": list(self.initiative_order),
            "initiative_scores": dict(self.initiative_scores),
            "round": self.round,
            "turn_idx": self.turn_idx,
            "state": self.state.value,
            "current_actor": self.current_actor,
            "is_active": self.is_active,
            "range_bands": {f"{a}&{b}": band.value for (a, b), band in self.range_bands.items()},
            "cover": {name: level.value for name, level in self.cover.items()},
            "triggers": list(self.triggers)
        }

    def validate(self) -> None:
        """验证战斗状态"""
        if not self.location:
            raise ValueError("战斗地点不能为空")
        
        if self.state == CombatState.ACTIVE and not self.participants:
            raise ValueError("活跃战斗必须有参与者")

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            CombatMustHaveParticipants(),
            ActiveCombatMustHaveCurrentActor(),
        ]


class CombatMustHaveParticipants:
    """战斗必须有参与者规则"""
    
    def is_satisfied_by(self, entity: Combat) -> bool:
        return entity.state != CombatState.ACTIVE or len(entity.participants) > 0
    
    def get_error_message(self) -> str:
        return "活跃的战斗必须有至少一个参与者"


class ActiveCombatMustHaveCurrentActor:
    """活跃战斗必须有当前行动者规则"""
    
    def is_satisfied_by(self, entity: Combat) -> bool:
        return entity.state != CombatState.ACTIVE or entity.current_actor is not None
    
    def get_error_message(self) -> str:
        return "活跃的战斗必须有当前行动者"