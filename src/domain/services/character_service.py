"""
角色领域服务

提供角色相关的业务逻辑和操作，协调角色聚合根与其他领域对象的交互。
遵循单一职责原则，专门负责角色相关的业务服务。
"""

from typing import Any, Dict, List, Optional, Tuple
from ..models.characters import Character, Ability, Position
from ..models.items import Item, Inventory
from ..models.relations import RelationshipNetwork, Relation, RelationType, RelationKey
from ..models.objectives import Objective, ObjectiveTracker
from ..models.combat import Combat
from ..models.world import World
from ...core.exceptions import BusinessRuleException, ValidationException


class CharacterService:
    """角色领域服务
    
    提供角色相关的业务逻辑和操作，包括：
    - 角色创建和管理
    - 角色间关系处理
    - 角色物品管理
    - 角色目标分配
    - 角色战斗参与
    """
    
    def __init__(self, relationship_network: RelationshipNetwork, objective_tracker: ObjectiveTracker):
        """初始化角色服务
        
        Args:
            relationship_network: 关系网络
            objective_tracker: 目标跟踪器
        """
        self._relationship_network = relationship_network
        self._objective_tracker = objective_tracker
    
    def create_character(
        self,
        name: str,
        abilities: Dict[str, int],
        hp: int,
        max_hp: int,
        position: Optional[Position] = None,
        proficient_skills: Optional[List[str]] = None,
        proficient_saves: Optional[List[str]] = None
    ) -> Character:
        """创建新角色
        
        Args:
            name: 角色名称
            abilities: 能力值字典
            hp: 当前生命值
            max_hp: 最大生命值
            position: 位置
            proficient_skills: 熟练技能列表
            proficient_saves: 熟练豁免列表
            
        Returns:
            Character: 创建的角色对象
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 验证输入
        if not name or not name.strip():
            raise ValidationException("角色名称不能为空")
        
        if hp < 0 or max_hp <= 0:
            raise ValidationException("生命值必须大于等于0，最大生命值必须大于0")
        
        if hp > max_hp:
            hp = max_hp
        
        # 创建角色
        from ..models.characters import Abilities, CharacterStats
        
        character_abilities = Abilities(
            strength=abilities.get("STR", 10),
            dexterity=abilities.get("DEX", 10),
            constitution=abilities.get("CON", 10),
            intelligence=abilities.get("INT", 10),
            wisdom=abilities.get("WIS", 10),
            charisma=abilities.get("CHA", 10)
        )
        
        character_stats = CharacterStats(
            level=1,
            armor_class=10,
            proficiency_bonus=2,
            speed_steps=6,
            reach_steps=1
        )
        
        character = Character(
            name=name.strip(),
            abilities=character_abilities,
            stats=character_stats,
            hp=hp,
            max_hp=max_hp,
            position=position,
            proficient_skills=proficient_skills or [],
            proficient_saves=proficient_saves or []
        )
        
        # 验证角色
        character.validate()
        
        return character
    
    def create_character_from_dnd_config(self, name: str, dnd_config: Dict[str, Any]) -> Character:
        """根据D&D配置创建角色
        
        Args:
            name: 角色名称
            dnd_config: D&D配置字典
            
        Returns:
            Character: 创建的角色对象
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 验证输入
        if not name or not name.strip():
            raise ValidationException("角色名称不能为空")
        
        if not dnd_config or not isinstance(dnd_config, dict):
            raise ValidationException("D&D配置不能为空")
        
        # 提取能力值
        abilities = dnd_config.get("abilities", {})
        hp = dnd_config.get("max_hp", 10)
        max_hp = dnd_config.get("max_hp", 10)
        
        # 提取位置信息（如果有的话）
        position = None
        if "position" in dnd_config:
            pos = dnd_config["position"]
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                try:
                    position = Position(int(pos[0]), int(pos[1]))
                except (ValueError, TypeError):
                    pass
        
        # 提取熟练技能和豁免
        proficient_skills = dnd_config.get("proficient_skills", [])
        proficient_saves = dnd_config.get("proficient_saves", [])
        
        # 创建角色
        from ..models.characters import Abilities, CharacterStats
        
        character_abilities = Abilities(
            strength=abilities.get("STR", 10),
            dexterity=abilities.get("DEX", 10),
            constitution=abilities.get("CON", 10),
            intelligence=abilities.get("INT", 10),
            wisdom=abilities.get("WIS", 10),
            charisma=abilities.get("CHA", 10)
        )
        
        # 从D&D配置中提取统计数据
        character_stats = CharacterStats(
            level=dnd_config.get("level", 1),
            armor_class=dnd_config.get("ac", 10),
            proficiency_bonus=2,  # 可以根据等级计算，但暂时固定为2
            speed_steps=dnd_config.get("move_speed", 6),
            reach_steps=dnd_config.get("reach", 1)
        )
        
        character = Character(
            name=name.strip(),
            abilities=character_abilities,
            stats=character_stats,
            hp=hp,
            max_hp=max_hp,
            position=position,
            proficient_skills=proficient_skills,
            proficient_saves=proficient_saves
        )
        
        return character
    
    def move_character(self, character: Character, new_position: Position, world: World) -> bool:
        """移动角色到新位置
        
        Args:
            character: 角色对象
            new_position: 新位置
            world: 世界对象
            
        Returns:
            bool: 是否成功移动
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        # 检查角色是否可以移动
        if not character.is_alive:
            raise BusinessRuleException("死亡的角色无法移动")
        
        # 检查新位置是否有效
        if not self._is_valid_position(new_position, world):
            raise BusinessRuleException("目标位置无效")
        
        # 检查是否在战斗中且是否有足够的移动力
        if world.is_in_combat and world.combat:
            if character.name != world.combat.current_actor:
                raise BusinessRuleException("不是当前行动角色，无法移动")
            
            # 计算移动距离
            if character.position:
                distance = character.position.distance_to(new_position)
                if not world.combat.consume_movement(character.name, distance):
                    raise BusinessRuleException("移动力不足")
        
        # 移动角色
        character.move_to(new_position)
        
        # 更新战斗中的距离带
        if world.is_in_combat and world.combat:
            self._update_combat_range_bands(character.name, world)
        
        return True
    
    def give_item_to_character(self, character: Character, item: Item, quantity: int = 1) -> bool:
        """给予物品给角色
        
        Args:
            character: 角色对象
            item: 物品对象
            quantity: 数量
            
        Returns:
            bool: 是否成功给予
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if quantity <= 0:
            raise BusinessRuleException("物品数量必须大于0")
        
        if not character.is_alive:
            raise BusinessRuleException("无法给予物品给死亡的角色")
        
        # 添加物品到角色物品栏
        character.add_item(item.name, quantity)
        
        return True
    
    def take_item_from_character(self, character: Character, item_name: str, quantity: int = 1) -> bool:
        """从角色处取走物品
        
        Args:
            character: 角色对象
            item_name: 物品名称
            quantity: 数量
            
        Returns:
            bool: 是否成功取走
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if quantity <= 0:
            raise BusinessRuleException("物品数量必须大于0")
        
        if not character.is_alive:
            raise BusinessRuleException("无法从死亡角色处取走物品")
        
        # 从角色物品栏移除物品
        return character.remove_item(item_name, quantity)
    
    def assign_objective_to_character(self, character: Character, objective: Objective) -> bool:
        """分配目标给角色
        
        Args:
            character: 角色对象
            objective: 目标对象
            
        Returns:
            bool: 是否成功分配
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not character.is_alive:
            raise BusinessRuleException("无法分配目标给死亡的角色")
        
        if objective.is_completed or objective.is_failed:
            raise BusinessRuleException("无法分配已完成或已失败的目标")
        
        # 分配目标给角色
        objective.assign_to(character.name)
        
        # 添加到目标跟踪器
        self._objective_tracker.add_objective(objective)
        
        return True
    
    def create_relation_between_characters(
        self,
        source_character: Character,
        target_character: Character,
        relation_type: RelationType,
        strength: int = 0,
        description: str = "",
        mutual: bool = False
    ) -> Relation:
        """在两个角色间创建关系
        
        Args:
            source_character: 源角色
            target_character: 目标角色
            relation_type: 关系类型
            strength: 关系强度
            description: 关系描述
            mutual: 是否为双向关系
            
        Returns:
            Relation: 创建的关系对象
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if source_character.name == target_character.name:
            raise BusinessRuleException("不能创建角色与自己的关系")
        
        # 创建关系键
        relation_key = RelationKey(
            source=source_character.name,
            target=target_character.name
        )
        
        # 创建关系
        relation = Relation(
            key=relation_key,
            relation_type=relation_type,
            strength=strength,
            description=description,
            mutual=mutual
        )
        
        # 添加到关系网络
        self._relationship_network.add_relation(relation)
        
        # 如果是双向关系，创建反向关系
        if mutual:
            reverse_key = RelationKey(
                source=target_character.name,
                target=source_character.name
            )
            reverse_relation = Relation(
                key=reverse_key,
                relation_type=relation_type,
                strength=strength,
                description=description,
                mutual=mutual
            )
            self._relationship_network.add_relation(reverse_relation)
        
        return relation
    
    def update_relation_strength(
        self,
        source_character: Character,
        target_character: Character,
        delta: int,
        reason: str = ""
    ) -> bool:
        """更新两个角色间的关系强度
        
        Args:
            source_character: 源角色
            target_character: 目标角色
            delta: 调整值
            reason: 调整原因
            
        Returns:
            bool: 是否成功更新
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if source_character.name == target_character.name:
            raise BusinessRuleException("不能更新角色与自己的关系")
        
        return self._relationship_network.update_relation_strength(
            source_character.name,
            target_character.name,
            delta,
            reason
        )
    
    def get_character_relations(self, character: Character) -> List[Relation]:
        """获取角色的所有关系
        
        Args:
            character: 角色对象
            
        Returns:
            List[Relation]: 关系列表
        """
        return self._relationship_network.get_relations_for_character(character.name)
    
    def get_character_objectives(self, character: Character) -> List[Objective]:
        """获取角色的所有目标
        
        Args:
            character: 角色对象
            
        Returns:
            List[Objective]: 目标列表
        """
        return self._objective_tracker.get_objectives_for_character(character.name)
    
    def get_character_active_objectives(self, character: Character) -> List[Objective]:
        """获取角色的所有活跃目标
        
        Args:
            character: 角色对象
            
        Returns:
            List[Objective]: 活跃目标列表
        """
        return self._objective_tracker.get_active_objectives_for_character(character.name)
    
    def can_character_participate_in_combat(self, character: Character, combat: Combat) -> bool:
        """检查角色是否可以参与战斗
        
        Args:
            character: 角色对象
            combat: 战斗对象
            
        Returns:
            bool: 是否可以参与
        """
        if not character.is_alive:
            return False
        
        if character.name in combat.participants:
            return False
        
        return True
    
    def add_character_to_combat(self, character: Character, combat: Combat) -> bool:
        """添加角色到战斗
        
        Args:
            character: 角色对象
            combat: 战斗对象
            
        Returns:
            bool: 是否成功添加
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if not self.can_character_participate_in_combat(character, combat):
            raise BusinessRuleException("角色无法参与此战斗")
        
        # 添加到战斗参与者列表
        combat.participants.append(character.name)
        
        # 如果战斗已经开始，需要重新计算先攻
        if combat.is_active:
            combat.roll_initiative()
        
        return True
    
    def remove_character_from_combat(self, character: Character, combat: Combat) -> bool:
        """从战斗中移除角色
        
        Args:
            character: 角色对象
            combat: 战斗对象
            
        Returns:
            bool: 是否成功移除
        """
        if character.name not in combat.participants:
            return False
        
        # 从参与者列表中移除
        combat.participants.remove(character.name)
        
        # 从先攻顺序中移除
        if character.name in combat.initiative_order:
            combat.initiative_order.remove(character.name)
        
        # 从先攻分数中移除
        if character.name in combat.initiative_scores:
            del combat.initiative_scores[character.name]
        
        # 从回合状态中移除
        if character.name in combat.turn_states:
            del combat.turn_states[character.name]
        
        # 如果移除的是当前行动者，推进到下一个回合
        if combat.current_actor == character.name:
            combat.next_turn()
        
        return True
    
    def heal_character(self, character: Character, amount: int) -> bool:
        """治疗角色
        
        Args:
            character: 角色对象
            amount: 治疗量
            
        Returns:
            bool: 是否成功治疗
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if amount <= 0:
            raise BusinessRuleException("治疗量必须大于0")
        
        if not character.is_alive:
            raise BusinessRuleException("无法治疗死亡的角色")
        
        character.heal(amount)
        return True
    
    def damage_character(self, character: Character, amount: int) -> bool:
        """对角色造成伤害
        
        Args:
            character: 角色对象
            amount: 伤害量
            
        Returns:
            bool: 是否成功造成伤害
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if amount <= 0:
            raise BusinessRuleException("伤害量必须大于0")
        
        character.take_damage(amount)
        return True
    
    def _is_valid_position(self, position: Position, world: World) -> bool:
        """检查位置是否有效
        
        Args:
            position: 位置对象
            world: 世界对象
            
        Returns:
            bool: 是否有效
        """
        # 简化实现，所有位置都有效
        # 实际实现中可能需要检查边界、障碍物等
        return True
    
    def _update_combat_range_bands(self, character_name: str, world: World) -> None:
        """更新战斗中的距离带
        
        Args:
            character_name: 角色名称
            world: 世界对象
        """
        if not world.combat:
            return
        
        character = world.characters.get(character_name)
        if not character or not character.position:
            return
        
        # 更新与其他所有参与者的距离带
        for other_name in world.combat.participants:
            if other_name == character_name:
                continue
            
            other_character = world.characters.get(other_name)
            if not other_character or not other_character.position:
                continue
            
            distance = character.position.distance_to(other_character.position)
            
            # 根据距离设置距离带
            if distance <= 1:
                from ..models.combat import RangeBand
                world.combat.set_range_band(character_name, other_name, RangeBand.ENGAGED)
            elif distance <= 6:
                from ..models.combat import RangeBand
                world.combat.set_range_band(character_name, other_name, RangeBand.NEAR)
            elif distance <= 12:
                from ..models.combat import RangeBand
                world.combat.set_range_band(character_name, other_name, RangeBand.FAR)
            else:
                from ..models.combat import RangeBand
                world.combat.set_range_band(character_name, other_name, RangeBand.LONG)