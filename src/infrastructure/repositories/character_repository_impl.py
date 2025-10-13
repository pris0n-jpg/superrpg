"""
角色仓储实现

提供角色数据持久化的具体实现，基于内存存储。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...core.interfaces import CharacterRepository as ICharacterRepository
from ...domain.models.characters import Character, CharacterCard, Position, Abilities, CharacterStats, Condition, CharacterCardInfo, PNGMetadata
from ...domain.models.items import Item
from ...domain.models.relations import Relation, RelationType
from ...domain.models.objectives import Objective


class CharacterRepositoryImpl(ICharacterRepository):
    """角色仓储实现
    
    基于内存和JSON文件的角色数据持久化实现。
    遵循单一职责原则，专门负责角色数据的存储和检索。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """初始化角色仓储
        
        Args:
            storage_path: 存储路径，如果为None则使用内存存储
        """
        self._storage_path = storage_path
        self._characters: Dict[str, Character] = {}
        self._character_history: Dict[str, List[Dict[str, Any]]] = {}
        self._backups: Dict[str, Dict[str, Any]] = {}
        
        # 如果指定了存储路径，加载现有数据
        if storage_path and storage_path.exists():
            self._load_from_storage()
    
    def _load_from_storage(self) -> None:
        """从存储加载数据"""
        if not self._storage_path:
            return
            
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 加载角色数据
            for character_data in data.get('characters', []):
                character = self._deserialize_character(character_data)
                if character:
                    self._characters[character.name] = character
            
            # 加载历史记录
            self._character_history = data.get('history', {})
            
            # 加载备份数据
            self._backups = data.get('backups', {})
            
        except Exception:
            # 如果加载失败，初始化空数据
            self._characters = {}
            self._character_history = {}
            self._backups = {}
    
    def _save_to_storage(self) -> None:
        """保存数据到存储"""
        if not self._storage_path:
            return
            
        try:
            # 确保目录存在
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'characters': [self._serialize_character(char) for char in self._characters.values()],
                'history': self._character_history,
                'backups': self._backups,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception:
            # 静默处理保存错误，避免影响业务逻辑
            pass
    
    def _serialize_character(self, character: Character) -> Dict[str, Any]:
        """序列化角色对象
        
        Args:
            character: 角色对象
            
        Returns:
            Dict[str, Any]: 序列化后的数据
        """
        base_data = {
            'id': str(character.id),
            'name': character.name,
            'abilities': {
                'strength': character.abilities.strength,
                'dexterity': character.abilities.dexterity,
                'constitution': character.abilities.constitution,
                'intelligence': character.abilities.intelligence,
                'wisdom': character.abilities.wisdom,
                'charisma': character.abilities.charisma,
            },
            'stats': {
                'level': character.stats.level,
                'armor_class': character.stats.armor_class,
                'proficiency_bonus': character.stats.proficiency_bonus,
                'speed_steps': character.stats.speed_steps,
                'reach_steps': character.stats.reach_steps,
            },
            'hp': character.hp,
            'max_hp': character.max_hp,
            'position': {
                'x': character.position.x,
                'y': character.position.y,
            } if character.position else None,
            'proficient_skills': character.proficient_skills,
            'proficient_saves': character.proficient_saves,
            'conditions': [c.value for c in character.conditions],
            'inventory': character.inventory,
            'created_at': character.created_at.isoformat() if character.created_at else None,
            'updated_at': character.updated_at.isoformat() if character.updated_at else None,
        }
        
        # 如果是CharacterCard，添加角色卡特有字段
        if isinstance(character, CharacterCard):
            base_data.update({
                'card_info': {
                    'description': character.card_info.description,
                    'first_message': character.card_info.first_message,
                    'example_messages': character.card_info.example_messages,
                    'scenario': character.card_info.scenario,
                    'personality_summary': character.card_info.personality_summary,
                    'creator_notes': character.card_info.creator_notes,
                    'tags': character.card_info.tags,
                },
                'png_metadata': {
                    'name': character.png_metadata.name,
                    'description': character.png_metadata.description,
                    'personality': character.png_metadata.personality,
                    'scenario': character.png_metadata.scenario,
                    'first_mes': character.png_metadata.first_mes,
                    'example_dialogue': character.png_metadata.example_dialogue,
                    'mes_example': character.png_metadata.mes_example,
                    'background': character.png_metadata.background,
                } if character.png_metadata else None,
            })
        
        return base_data
    
    def _deserialize_character(self, data: Dict[str, Any]) -> Optional[Character]:
        """反序列化角色对象
        
        Args:
            data: 序列化数据
            
        Returns:
            Optional[Character]: 角色对象，如果失败则返回None
        """
        try:
            abilities_data = data.get('abilities', {})
            abilities = Abilities(
                strength=abilities_data.get('strength', 10),
                dexterity=abilities_data.get('dexterity', 10),
                constitution=abilities_data.get('constitution', 10),
                intelligence=abilities_data.get('intelligence', 10),
                wisdom=abilities_data.get('wisdom', 10),
                charisma=abilities_data.get('charisma', 10),
            )
            
            stats_data = data.get('stats', {})
            stats = CharacterStats(
                level=stats_data.get('level', 1),
                armor_class=stats_data.get('armor_class', 10),
                proficiency_bonus=stats_data.get('proficiency_bonus', 2),
                speed_steps=stats_data.get('speed_steps', 6),
                reach_steps=stats_data.get('reach_steps', 1),
            )
            
            position_data = data.get('position')
            position = None
            if position_data:
                position = Position(x=position_data['x'], y=position_data['y'])
            
            # 检查是否是CharacterCard（通过是否存在card_info字段判断）
            if 'card_info' in data:
                # 创建角色卡信息对象
                card_info_data = data.get('card_info', {})
                card_info = CharacterCardInfo(
                    description=card_info_data.get('description', ''),
                    first_message=card_info_data.get('first_message', ''),
                    example_messages=card_info_data.get('example_messages', []),
                    scenario=card_info_data.get('scenario', ''),
                    personality_summary=card_info_data.get('personality_summary', ''),
                    creator_notes=card_info_data.get('creator_notes', ''),
                    tags=card_info_data.get('tags', []),
                )
                
                # 创建PNG元数据对象
                png_data = data.get('png_metadata', {})
                png_metadata = PNGMetadata(
                    name=png_data.get('name', ''),
                    description=png_data.get('description', ''),
                    personality=png_data.get('personality', ''),
                    scenario=png_data.get('scenario', ''),
                    first_mes=png_data.get('first_mes', ''),
                    example_dialogue=png_data.get('example_dialogue', ''),
                    mes_example=png_data.get('mes_example', ''),
                    background=png_data.get('background', ''),
                ) if png_data else None
                
                # 创建CharacterCard对象
                character = CharacterCard(
                    name=data['name'],
                    card_info=card_info,
                    abilities=abilities,
                    stats=stats,
                    hp=data['hp'],
                    max_hp=data['max_hp'],
                    position=position,
                    png_metadata=png_metadata,
                    proficient_skills=data.get('proficient_skills', []),
                    proficient_saves=data.get('proficient_saves', []),
                    inventory=data.get('inventory', {}),
                )
            else:
                # 创建普通Character对象
                character = Character(
                    name=data['name'],
                    abilities=abilities,
                    stats=stats,
                    hp=data['hp'],
                    max_hp=data['max_hp'],
                    position=position,
                    proficient_skills=data.get('proficient_skills', []),
                    proficient_saves=data.get('proficient_saves', []),
                    inventory=data.get('inventory', {}),
                )
            
            # 设置条件和时间戳
            for condition_str in data.get('conditions', []):
                try:
                    character.add_condition(Condition(condition_str))
                except ValueError:
                    pass
            
            if data.get('created_at'):
                character.created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                character.updated_at = datetime.fromisoformat(data['updated_at'])
            
            return character
            
        except Exception:
            return None
    
    def _add_history_record(self, character_name: str, action: str, data: Dict[str, Any]) -> None:
        """添加历史记录
        
        Args:
            character_name: 角色名称
            action: 操作类型
            data: 操作数据
        """
        if character_name not in self._character_history:
            self._character_history[character_name] = []
            
        record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'data': data,
        }
        
        self._character_history[character_name].append(record)
        
        # 限制历史记录数量
        if len(self._character_history[character_name]) > 100:
            self._character_history[character_name] = self._character_history[character_name][-100:]
    
    # 实现接口方法
    
    def get(self, id: str) -> Optional[Character]:
        """根据ID获取角色"""
        for character in self._characters.values():
            if str(character.id) == id:
                return character
        return None
    
    def save(self, entity: Character) -> None:
        """保存角色"""
        if not entity.name:
            raise ValueError("角色名称不能为空")
            
        is_new = entity.name not in self._characters
        self._characters[entity.name] = entity
        
        # 添加历史记录
        action = "created" if is_new else "updated"
        self._add_history_record(entity.name, action, {
            'character_id': str(entity.id),
            'hp': entity.hp,
            'position': entity.position,
        })
        
        # 保存到存储
        self._save_to_storage()
    
    def delete(self, id: str) -> bool:
        """删除角色"""
        character = None
        for name, char in self._characters.items():
            if str(char.id) == id:
                character = char
                break
                
        if character:
            del self._characters[character.name]
            
            # 添加历史记录
            self._add_history_record(character.name, "deleted", {
                'character_id': str(character.id),
            })
            
            # 保存到存储
            self._save_to_storage()
            return True
        
        return False
    
    def find_all(self) -> List[Character]:
        """获取所有角色"""
        return list(self._characters.values())
    
    def find_by(self, criteria: Dict[str, Any]) -> List[Character]:
        """根据条件查找角色"""
        result = []
        
        for character in self._characters.values():
            match = True
            
            for key, value in criteria.items():
                if key == 'name' and character.name != value:
                    match = False
                elif key == 'is_alive' and character.is_alive != value:
                    match = False
                elif key == 'level' and character.stats.level != value:
                    match = False
                elif key == 'min_hp' and character.hp < value:
                    match = False
                
                if not match:
                    break
            
            if match:
                result.append(character)
        
        return result
    
    # 实现领域特定的仓储方法
    
    def find_by_id(self, character_id: str) -> Optional[Character]:
        """根据ID查找角色"""
        return self.get(character_id)
    
    def find_by_name(self, name: str) -> Optional[Character]:
        """根据名称查找角色"""
        return self._characters.get(name)
    
    def find_by_position(self, position: Position) -> List[Character]:
        """根据位置查找角色"""
        result = []
        for character in self._characters.values():
            if (character.position and 
                character.position.x == position.x and 
                character.position.y == position.y):
                result.append(character)
        return result
    
    def find_alive(self) -> List[Character]:
        """查找所有存活角色"""
        return [char for char in self._characters.values() if char.is_alive]
    
    def find_by_ability_score(self, ability: str, min_score: int) -> List[Character]:
        """根据能力分数查找角色"""
        result = []
        try:
            ability_enum = Ability(ability.lower())
            for character in self._characters.values():
                if character.abilities.get_score(ability_enum) >= min_score:
                    result.append(character)
        except ValueError:
            pass  # 忽略无效的能力名称
        return result
    
    def find_by_skill(self, skill: str) -> List[Character]:
        """根据技能查找角色"""
        return [char for char in self._characters.values() 
                if char.is_proficient_in_skill(skill)]
    
    def find_by_item(self, item_name: str) -> List[Character]:
        """根据物品查找角色"""
        return [char for char in self._characters.values() 
                if item_name in char.inventory]
    
    def find_by_relation(self, target_name: str, relation_type: Optional[RelationType] = None) -> List[Character]:
        """根据关系查找角色"""
        # 简化实现，返回空列表
        # 实际实现需要查询关系网络
        return []
    
    def find_by_objective(self, objective_id: str) -> List[Character]:
        """根据目标查找角色"""
        # 简化实现，返回空列表
        # 实际实现需要查询目标跟踪器
        return []
    
    def update(self, character: Character) -> None:
        """更新角色"""
        self.save(character)
    
    def exists_by_id(self, character_id: str) -> bool:
        """检查角色是否存在（根据ID）"""
        return self.get(character_id) is not None
    
    def exists_by_name(self, name: str) -> bool:
        """检查角色是否存在（根据名称）"""
        return name in self._characters
    
    def count(self) -> int:
        """获取角色总数"""
        return len(self._characters)
    
    def count_alive(self) -> int:
        """获取存活角色总数"""
        return len([char for char in self._characters.values() if char.is_alive])
    
    def get_character_statistics(self, character_id: str) -> Dict[str, Any]:
        """获取角色统计信息"""
        character = self.get(character_id)
        if not character:
            return {}
            
        return {
            'name': character.name,
            'level': character.stats.level,
            'hp': character.hp,
            'max_hp': character.max_hp,
            'is_alive': character.is_alive,
            'position': character.position,
            'inventory_size': len(character.inventory),
            'conditions_count': len(character.conditions),
            'proficient_skills_count': len(character.proficient_skills),
        }
    
    def get_party_members(self, leader_name: str) -> List[Character]:
        """获取队伍成员"""
        # 简化实现，返回空列表
        # 实际实现需要查询关系网络中的队伍关系
        return []
    
    def get_characters_in_range(self, center: Position, range_steps: int) -> List[Character]:
        """获取指定范围内的角色"""
        result = []
        for character in self._characters.values():
            if character.position:
                distance = character.position.distance_to(center)
                if distance <= range_steps:
                    result.append(character)
        return result
    
    def backup_character(self, character_id: str) -> Dict[str, Any]:
        """备份角色数据"""
        character = self.get(character_id)
        if not character:
            return {}
            
        backup_data = {
            'character': self._serialize_character(character),
            'timestamp': datetime.now().isoformat(),
            'backup_id': str(len(self._backups)),
        }
        
        self._backups[character_id] = backup_data
        self._save_to_storage()
        
        return backup_data
    
    def restore_character(self, backup_data: Dict[str, Any]) -> Character:
        """从备份数据恢复角色"""
        character_data = backup_data.get('character')
        if not character_data:
            raise ValueError("备份数据无效")
            
        character = self._deserialize_character(character_data)
        if not character:
            raise ValueError("无法恢复角色数据")
            
        self.save(character)
        return character
    
    def get_character_history(self, character_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取角色历史记录"""
        character = self.get(character_id)
        if not character:
            return []
            
        history = self._character_history.get(character.name, [])
        return history[-limit:] if limit > 0 else history
    
    def search_characters(self, criteria: Dict[str, Any]) -> List[Character]:
        """根据条件搜索角色"""
        return self.find_by(criteria)
    
    def get_character_relations_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色关系摘要"""
        # 简化实现
        return {'relations': [], 'count': 0}
    
    def get_character_inventory_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色物品栏摘要"""
        character = self.get(character_id)
        if not character:
            return {}
            
        return {
            'items': character.inventory,
            'total_items': sum(character.inventory.values()),
            'unique_items': len(character.inventory),
        }
    
    def get_character_objectives_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色目标摘要"""
        # 简化实现
        return {'objectives': [], 'active_count': 0, 'completed_count': 0}
    
    def batch_save(self, characters: List[Character]) -> None:
        """批量保存角色"""
        for character in characters:
            self.save(character)
    
    def batch_delete(self, character_ids: List[str]) -> int:
        """批量删除角色"""
        deleted_count = 0
        for character_id in character_ids:
            if self.exists_by_id(character_id):
                self.delete(character_id)
                deleted_count += 1
        return deleted_count
    
    def get_character_level_distribution(self) -> Dict[int, int]:
        """获取角色等级分布"""
        distribution = {}
        for character in self._characters.values():
            level = character.stats.level
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def get_character_class_distribution(self) -> Dict[str, int]:
        """获取角色职业分布"""
        # 简化实现，因为当前模型中没有职业属性
        return {'unknown': len(self._characters)}