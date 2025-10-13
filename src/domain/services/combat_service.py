"""
战斗领域服务

提供战斗相关的业务逻辑和操作，协调战斗聚合根与其他领域对象的交互。
遵循单一职责原则，专门负责战斗相关的业务服务。
"""

from typing import Dict, List, Optional, Tuple
import random

from ..models.combat import Combat, CombatState, RangeBand, CoverLevel
from ..models.characters import Character, Ability, Position
from ..models.items import Item
from ..models.world import World
from ...core.exceptions import BusinessRuleException, ValidationException


class CombatService:
    """战斗领域服务
    
    提供战斗相关的业务逻辑和操作，包括：
    - 战斗创建和管理
    - 战斗流程控制
    - 战斗动作处理
    - 战斗状态计算
    - 战斗结果处理
    """
    
    def __init__(self):
        """初始化战斗服务"""
        pass
    
    def create_combat(self, location: str, participants: List[str], world: World) -> Combat:
        """创建新战斗
        
        Args:
            location: 战斗地点
            participants: 参与者列表
            world: 世界对象
            
        Returns:
            Combat: 创建的战斗对象
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证输入
        if not location or not location.strip():
            raise ValidationException("战斗地点不能为空")
        
        if len(participants) < 2:
            raise ValidationException("战斗至少需要2个参与者")
        
        # 检查所有参与者是否存在且存活
        for participant_name in participants:
            character = world.characters.get(participant_name)
            if not character:
                raise ValidationException(f"参与者 {participant_name} 不存在")
            
            if not character.is_alive:
                raise BusinessRuleException(f"参与者 {participant_name} 已经死亡，无法参与战斗")
        
        # 检查是否已有活跃战斗
        if world.is_in_combat:
            raise BusinessRuleException("世界已有活跃战斗，无法创建新战斗")
        
        # 创建战斗
        combat = Combat(location=location.strip())
        combat.start_combat(participants)
        
        return combat
    
    def end_combat(self, combat: Combat, world: World) -> bool:
        """结束战斗
        
        Args:
            combat: 战斗对象
            world: 世界对象
            
        Returns:
            bool: 是否成功结束
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not combat.is_active:
            raise BusinessRuleException("只能结束活跃的战斗")
        
        # 结束战斗
        combat.end_combat()
        
        # 从世界中移除战斗
        if world.combat == combat:
            world.combat = None
        
        return True
    
    def next_turn(self, combat: Combat) -> Optional[str]:
        """推进到下一个回合
        
        Args:
            combat: 战斗对象
            
        Returns:
            Optional[str]: 当前行动者名称，如果没有可行动者则返回None
        """
        if not combat.is_active:
            raise BusinessRuleException("只能推进活跃战斗的回合")
        
        return combat.next_turn()
    
    def use_action(self, combat: Combat, character_name: str, action_type: str = "action") -> bool:
        """使用动作
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            action_type: 动作类型 (action/bonus/reaction)
            
        Returns:
            bool: 是否成功使用
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not combat.is_active:
            raise BusinessRuleException("战斗未活跃，无法使用动作")
        
        if combat.current_actor != character_name:
            raise BusinessRuleException("不是当前行动角色，无法使用动作")
        
        return combat.use_action(character_name, action_type)
    
    def consume_movement(self, combat: Combat, character_name: str, distance: int) -> bool:
        """消耗移动力
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            distance: 移动距离
            
        Returns:
            bool: 是否成功消耗
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not combat.is_active:
            raise BusinessRuleException("战斗未活跃，无法移动")
        
        if combat.current_actor != character_name:
            raise BusinessRuleException("不是当前行动角色，无法移动")
        
        if distance <= 0:
            raise BusinessRuleException("移动距离必须大于0")
        
        return combat.consume_movement(character_name, distance)
    
    def move_character_in_combat(
        self,
        combat: Combat,
        character_name: str,
        target_position: Position,
        world: World
    ) -> Tuple[bool, int]:
        """在战斗中移动角色
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            target_position: 目标位置
            world: 世界对象
            
        Returns:
            Tuple[bool, int]: (是否成功移动, 实际移动距离)
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not combat.is_active:
            raise BusinessRuleException("战斗未活跃，无法移动")
        
        if combat.current_actor != character_name:
            raise BusinessRuleException("不是当前行动角色，无法移动")
        
        # 获取角色
        character = world.characters.get(character_name)
        if not character or not character.position:
            raise BusinessRuleException("角色不存在或没有位置信息")
        
        # 计算移动距离
        distance = character.position.distance_to(target_position)
        
        # 检查是否有足够的移动力
        if not combat.consume_movement(character_name, distance):
            return False, 0
        
        # 移动角色
        character.move_to(target_position)
        
        # 更新距离带
        self._update_range_bands_for_character(combat, character_name, world)
        
        return True, distance
    
    def set_cover(self, combat: Combat, character_name: str, cover_level: CoverLevel) -> bool:
        """设置角色的掩体等级
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            cover_level: 掩体等级
            
        Returns:
            bool: 是否成功设置
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not combat.is_active:
            raise BusinessRuleException("战斗未活跃，无法设置掩体")
        
        combat.set_cover(character_name, cover_level)
        return True
    
    def get_range_band(self, combat: Combat, char_a: str, char_b: str) -> RangeBand:
        """获取两个角色间的距离带
        
        Args:
            combat: 战斗对象
            char_a: 角色A名称
            char_b: 角色B名称
            
        Returns:
            RangeBand: 距离带
        """
        return combat.get_range_band(char_a, char_b)
    
    def get_cover_bonus(self, combat: Combat, character_name: str) -> Tuple[int, bool]:
        """获取角色的掩体加值
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            
        Returns:
            Tuple[int, bool]: (护甲加值, 是否完全掩护)
        """
        return combat.get_cover_bonus(character_name)
    
    def is_in_range(self, combat: Combat, attacker: str, defender: str, max_range: int) -> bool:
        """检查防御者是否在攻击者的攻击范围内
        
        Args:
            combat: 战斗对象
            attacker: 攻击者名称
            defender: 防御者名称
            max_range: 最大攻击范围（步数）
            
        Returns:
            bool: 是否在范围内
        """
        # 获取角色位置
        attacker_pos = None
        defender_pos = None
        
        # 这里需要从世界对象获取角色位置
        # 简化实现，使用距离带判断
        range_band = self.get_range_band(combat, attacker, defender)
        
        if max_range <= 1:
            return range_band == RangeBand.ENGAGED
        elif max_range <= 6:
            return range_band in [RangeBand.ENGAGED, RangeBand.NEAR]
        elif max_range <= 12:
            return range_band in [RangeBand.ENGAGED, RangeBand.NEAR, RangeBand.FAR]
        else:
            return True  # 长距离武器可以攻击任何距离带
    
    def can_attack(self, combat: Combat, attacker: str, defender: str, world: World) -> Tuple[bool, str]:
        """检查是否可以攻击
        
        Args:
            combat: 战斗对象
            attacker: 攻击者名称
            defender: 防御者名称
            world: 世界对象
            
        Returns:
            Tuple[bool, str]: (是否可以攻击, 原因)
        """
        # 检查战斗是否活跃
        if not combat.is_active:
            return False, "战斗未活跃"
        
        # 检查是否为当前行动者
        if combat.current_actor != attacker:
            return False, "不是当前行动角色"
        
        # 检查角色是否存在且存活
        attacker_char = world.characters.get(attacker)
        defender_char = world.characters.get(defender)
        
        if not attacker_char or not attacker_char.is_alive:
            return False, "攻击者不存在或已死亡"
        
        if not defender_char or not defender_char.is_alive:
            return False, "防御者不存在或已死亡"
        
        # 检查是否在攻击范围内
        reach = attacker_char.stats.reach_steps
        if not self.is_in_range(combat, attacker, defender, reach):
            return False, "目标不在攻击范围内"
        
        return True, ""
    
    def roll_attack(
        self,
        combat: Combat,
        attacker: str,
        defender: str,
        world: World,
        attack_bonus: int = 0,
        damage_dice: str = "1d6"
    ) -> Tuple[bool, int, int]:
        """执行攻击检定
        
        Args:
            combat: 战斗对象
            attacker: 攻击者名称
            defender: 防御者名称
            attack_bonus: 攻击加值
            damage_dice: 伤害骰子表达式
            world: 世界对象
            
        Returns:
            Tuple[bool, int, int]: (是否命中, 攻击检定值, 伤害值)
        """
        # 获取角色
        attacker_char = world.characters.get(attacker)
        defender_char = world.characters.get(defender)
        
        if not attacker_char or not defender_char:
            return False, 0, 0
        
        # 计算攻击加值
        attack_roll = random.randint(1, 20) + attack_bonus
        
        # 计算护甲等级
        ac = defender_char.stats.armor_class
        
        # 检查掩体加值
        cover_bonus, total_cover = self.get_cover_bonus(combat, defender)
        if total_cover:
            return False, attack_roll, 0
        
        ac += cover_bonus
        
        # 判断是否命中
        hit = attack_roll >= ac
        
        # 计算伤害
        damage = 0
        if hit:
            damage = self._roll_damage(damage_dice, attacker_char)
        
        return hit, attack_roll, damage
    
    def apply_damage(self, combat: Combat, defender: str, damage: int, world: World) -> bool:
        """对角色造成伤害
        
        Args:
            combat: 战斗对象
            defender: 防御者名称
            damage: 伤害值
            world: 世界对象
            
        Returns:
            bool: 是否成功造成伤害
        """
        defender_char = world.characters.get(defender)
        if not defender_char:
            return False
        
        defender_char.take_damage(damage)
        return True
    
    def queue_trigger(self, combat: Combat, trigger_type: str, payload: Dict[str, any]) -> None:
        """添加触发器到队列
        
        Args:
            combat: 战斗对象
            trigger_type: 触发器类型
            payload: 触发器载荷
        """
        combat.queue_trigger(trigger_type, payload)
    
    def pop_triggers(self, combat: Combat) -> List[Dict[str, any]]:
        """获取并清空触发器队列
        
        Args:
            combat: 战斗对象
            
        Returns:
            List[Dict[str, any]]: 触发器列表
        """
        return combat.pop_triggers()
    
    def _update_range_bands_for_character(
        self, combat: Combat, character_name: str, world: World
    ) -> None:
        """更新角色的距离带
        
        Args:
            combat: 战斗对象
            character_name: 角色名称
            world: 世界对象
        """
        character = world.characters.get(character_name)
        if not character or not character.position:
            return
        
        # 更新与其他所有参与者的距离带
        for other_name in combat.participants:
            if other_name == character_name:
                continue
            
            other_character = world.characters.get(other_name)
            if not other_character or not other_character.position:
                continue
            
            distance = character.position.distance_to(other_character.position)
            
            # 根据距离设置距离带
            if distance <= 1:
                combat.set_range_band(character_name, other_name, RangeBand.ENGAGED)
            elif distance <= 6:
                combat.set_range_band(character_name, other_name, RangeBand.NEAR)
            elif distance <= 12:
                combat.set_range_band(character_name, other_name, RangeBand.FAR)
            else:
                combat.set_range_band(character_name, other_name, RangeBand.LONG)
    
    def _roll_damage(self, damage_dice: str, attacker: Character) -> int:
        """掷伤害骰子
        
        Args:
            damage_dice: 伤害骰子表达式
            attacker: 攻击者
            
        Returns:
            int: 伤害值
        """
        # 简化实现，只支持基本的XdY格式
        try:
            if 'd' in damage_dice:
                parts = damage_dice.lower().split('d')
                if len(parts) == 2:
                    num_dice = int(parts[0])
                    dice_sides = int(parts[1])
                    total = 0
                    for _ in range(num_dice):
                        total += random.randint(1, dice_sides)
                    return total
        except (ValueError, IndexError):
            pass
        
        # 默认伤害
        return random.randint(1, 6)
