"""
角色仓储接口

定义角色聚合根的持久化契约，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models.characters import Character, Position
from ..models.items import Item
from ..models.relations import Relation, RelationType
from ..models.objectives import Objective


class CharacterRepository(ABC):
    """角色仓储接口
    
    定义角色聚合根的持久化操作契约。
    遵循依赖倒置原则，具体实现由基础设施层提供。
    """
    
    @abstractmethod
    def save(self, character: Character) -> None:
        """保存角色
        
        Args:
            character: 角色聚合根
        """
        pass
    
    @abstractmethod
    def find_by_id(self, character_id: str) -> Optional[Character]:
        """根据ID查找角色
        
        Args:
            character_id: 角色ID
            
        Returns:
            Optional[Character]: 角色对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Character]:
        """根据名称查找角色
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Character]: 角色对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Character]:
        """查找所有角色
        
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_by_position(self, position: Position) -> List[Character]:
        """根据位置查找角色
        
        Args:
            position: 位置对象
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_alive(self) -> List[Character]:
        """查找所有存活角色
        
        Returns:
            List[Character]: 存活角色列表
        """
        pass
    
    @abstractmethod
    def find_by_ability_score(self, ability: str, min_score: int) -> List[Character]:
        """根据能力分数查找角色
        
        Args:
            ability: 能力名称
            min_score: 最小分数
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_by_skill(self, skill: str) -> List[Character]:
        """根据技能查找角色
        
        Args:
            skill: 技能名称
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_by_item(self, item_name: str) -> List[Character]:
        """根据物品查找角色
        
        Args:
            item_name: 物品名称
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_by_relation(self, target_name: str, relation_type: Optional[RelationType] = None) -> List[Character]:
        """根据关系查找角色
        
        Args:
            target_name: 目标角色名称
            relation_type: 关系类型
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def find_by_objective(self, objective_id: str) -> List[Character]:
        """根据目标查找角色
        
        Args:
            objective_id: 目标ID
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def update(self, character: Character) -> None:
        """更新角色
        
        Args:
            character: 角色聚合根
        """
        pass
    
    @abstractmethod
    def delete(self, character_id: str) -> bool:
        """删除角色
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def exists_by_id(self, character_id: str) -> bool:
        """检查角色是否存在（根据ID）
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """检查角色是否存在（根据名称）
        
        Args:
            name: 角色名称
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取角色总数
        
        Returns:
            int: 角色总数
        """
        pass
    
    @abstractmethod
    def count_alive(self) -> int:
        """获取存活角色总数
        
        Returns:
            int: 存活角色总数
        """
        pass
    
    @abstractmethod
    def get_character_statistics(self, character_id: str) -> Dict[str, Any]:
        """获取角色统计信息
        
        Args:
            character_id: 角色ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    def get_party_members(self, leader_name: str) -> List[Character]:
        """获取队伍成员
        
        Args:
            leader_name: 队长名称
            
        Returns:
            List[Character]: 队伍成员列表
        """
        pass
    
    @abstractmethod
    def get_characters_in_range(self, center: Position, range_steps: int) -> List[Character]:
        """获取指定范围内的角色
        
        Args:
            center: 中心位置
            range_steps: 范围（步数）
            
        Returns:
            List[Character]: 范围内角色列表
        """
        pass
    
    @abstractmethod
    def backup_character(self, character_id: str) -> Dict[str, Any]:
        """备份角色数据
        
        Args:
            character_id: 角色ID
            
        Returns:
            Dict[str, Any]: 备份数据
        """
        pass
    
    @abstractmethod
    def restore_character(self, backup_data: Dict[str, Any]) -> Character:
        """从备份数据恢复角色
        
        Args:
            backup_data: 备份数据
            
        Returns:
            Character: 恢复的角色对象
        """
        pass
    
    @abstractmethod
    def get_character_history(self, character_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取角色历史记录
        
        Args:
            character_id: 角色ID
            limit: 记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 历史记录列表
        """
        pass
    
    @abstractmethod
    def search_characters(self, criteria: Dict[str, Any]) -> List[Character]:
        """根据条件搜索角色
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[Character]: 匹配的角色列表
        """
        pass
    
    @abstractmethod
    def get_character_relations_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色关系摘要
        
        Args:
            character_id: 角色ID
            
        Returns:
            Dict[str, Any]: 关系摘要
        """
        pass
    
    @abstractmethod
    def get_character_inventory_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色物品栏摘要
        
        Args:
            character_id: 角色ID
            
        Returns:
            Dict[str, Any]: 物品栏摘要
        """
        pass
    
    @abstractmethod
    def get_character_objectives_summary(self, character_id: str) -> Dict[str, Any]:
        """获取角色目标摘要
        
        Args:
            character_id: 角色ID
            
        Returns:
            Dict[str, Any]: 目标摘要
        """
        pass
    
    @abstractmethod
    def batch_save(self, characters: List[Character]) -> None:
        """批量保存角色
        
        Args:
            characters: 角色列表
        """
        pass
    
    @abstractmethod
    def batch_delete(self, character_ids: List[str]) -> int:
        """批量删除角色
        
        Args:
            character_ids: 角色ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass
    
    @abstractmethod
    def get_character_level_distribution(self) -> Dict[int, int]:
        """获取角色等级分布
        
        Returns:
            Dict[int, int]: 等级分布字典
        """
        pass
    
    @abstractmethod
    def get_character_class_distribution(self) -> Dict[str, int]:
        """获取角色职业分布
        
        Returns:
            Dict[str, int]: 职业分布字典
        """
        pass