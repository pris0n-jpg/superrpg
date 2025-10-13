"""
世界仓储接口

定义世界聚合根的持久化契约，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.world import World, Location, Scene, GameTime, Weather
from ..models.characters import Character
from ..models.items import Item
from ..models.combat import Combat
from ..models.objectives import Objective


class WorldRepository(ABC):
    """世界仓储接口
    
    定义世界聚合根的持久化操作契约。
    遵循依赖倒置原则，具体实现由基础设施层提供。
    """
    
    @abstractmethod
    def save(self, world: World) -> None:
        """保存世界
        
        Args:
            world: 世界聚合根
        """
        pass
    
    @abstractmethod
    def find_by_id(self, world_id: str) -> Optional[World]:
        """根据ID查找世界
        
        Args:
            world_id: 世界ID
            
        Returns:
            Optional[World]: 世界对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[World]:
        """根据名称查找世界
        
        Args:
            name: 世界名称
            
        Returns:
            Optional[World]: 世界对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[World]:
        """查找所有世界
        
        Returns:
            List[World]: 世界列表
        """
        pass
    
    @abstractmethod
    def find_active(self) -> Optional[World]:
        """查找活跃世界
        
        Returns:
            Optional[World]: 活跃世界对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def update(self, world: World) -> None:
        """更新世界
        
        Args:
            world: 世界聚合根
        """
        pass
    
    @abstractmethod
    def delete(self, world_id: str) -> bool:
        """删除世界
        
        Args:
            world_id: 世界ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def exists_by_id(self, world_id: str) -> bool:
        """检查世界是否存在（根据ID）
        
        Args:
            world_id: 世界ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """检查世界是否存在（根据名称）
        
        Args:
            name: 世界名称
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取世界总数
        
        Returns:
            int: 世界总数
        """
        pass
    
    @abstractmethod
    def save_location(self, world_id: str, location: Location) -> None:
        """保存地点
        
        Args:
            world_id: 世界ID
            location: 地点对象
        """
        pass
    
    @abstractmethod
    def find_location_by_name(self, world_id: str, location_name: str) -> Optional[Location]:
        """根据名称查找地点
        
        Args:
            world_id: 世界ID
            location_name: 地点名称
            
        Returns:
            Optional[Location]: 地点对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_all_locations(self, world_id: str) -> List[Location]:
        """查找世界的所有地点
        
        Args:
            world_id: 世界ID
            
        Returns:
            List[Location]: 地点列表
        """
        pass
    
    @abstractmethod
    def delete_location(self, world_id: str, location_name: str) -> bool:
        """删除地点
        
        Args:
            world_id: 世界ID
            location_name: 地点名称
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def save_scene(self, world_id: str, scene: Scene) -> None:
        """保存场景
        
        Args:
            world_id: 世界ID
            scene: 场景对象
        """
        pass
    
    @abstractmethod
    def find_current_scene(self, world_id: str) -> Optional[Scene]:
        """查找当前场景
        
        Args:
            world_id: 世界ID
            
        Returns:
            Optional[Scene]: 当前场景对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_scene_history(self, world_id: str, limit: int = 10) -> List[Scene]:
        """查找场景历史
        
        Args:
            world_id: 世界ID
            limit: 记录数量限制
            
        Returns:
            List[Scene]: 场景历史列表
        """
        pass
    
    @abstractmethod
    def save_combat(self, world_id: str, combat: Combat) -> None:
        """保存战斗
        
        Args:
            world_id: 世界ID
            combat: 战斗对象
        """
        pass
    
    @abstractmethod
    def find_active_combat(self, world_id: str) -> Optional[Combat]:
        """查找活跃战斗
        
        Args:
            world_id: 世界ID
            
        Returns:
            Optional[Combat]: 活跃战斗对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_combat_history(self, world_id: str, limit: int = 10) -> List[Combat]:
        """查找战斗历史
        
        Args:
            world_id: 世界ID
            limit: 记录数量限制
            
        Returns:
            List[Combat]: 战斗历史列表
        """
        pass
    
    @abstractmethod
    def get_world_statistics(self, world_id: str) -> Dict[str, Any]:
        """获取世界统计信息
        
        Args:
            world_id: 世界ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    def get_world_timeline(self, world_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取世界时间线
        
        Args:
            world_id: 世界ID
            limit: 记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 时间线事件列表
        """
        pass
    
    @abstractmethod
    def backup_world(self, world_id: str) -> Dict[str, Any]:
        """备份世界数据
        
        Args:
            world_id: 世界ID
            
        Returns:
            Dict[str, Any]: 备份数据
        """
        pass
    
    @abstractmethod
    def restore_world(self, backup_data: Dict[str, Any]) -> World:
        """从备份数据恢复世界
        
        Args:
            backup_data: 备份数据
            
        Returns:
            World: 恢复的世界对象
        """
        pass
    
    @abstractmethod
    def get_world_snapshots(self, world_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取世界快照
        
        Args:
            world_id: 世界ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict[str, Any]]: 快照列表
        """
        pass
    
    @abstractmethod
    def save_world_snapshot(self, world_id: str, snapshot_data: Dict[str, Any]) -> None:
        """保存世界快照
        
        Args:
            world_id: 世界ID
            snapshot_data: 快照数据
        """
        pass
    
    @abstractmethod
    def get_characters_in_world(self, world_id: str) -> List[Character]:
        """获取世界中的所有角色
        
        Args:
            world_id: 世界ID
            
        Returns:
            List[Character]: 角色列表
        """
        pass
    
    @abstractmethod
    def get_items_in_world(self, world_id: str) -> List[Item]:
        """获取世界中的所有物品
        
        Args:
            world_id: 世界ID
            
        Returns:
            List[Item]: 物品列表
        """
        pass
    
    @abstractmethod
    def get_objectives_in_world(self, world_id: str) -> List[Objective]:
        """获取世界中的所有目标
        
        Args:
            world_id: 世界ID
            
        Returns:
            List[Objective]: 目标列表
        """
        pass
    
    @abstractmethod
    def search_worlds(self, criteria: Dict[str, Any]) -> List[World]:
        """根据条件搜索世界
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[World]: 匹配的世界列表
        """
        pass
    
    @abstractmethod
    def get_world_activity_summary(self, world_id: str, days: int = 7) -> Dict[str, Any]:
        """获取世界活动摘要
        
        Args:
            world_id: 世界ID
            days: 天数
            
        Returns:
            Dict[str, Any]: 活动摘要
        """
        pass
    
    @abstractmethod
    def get_location_connections(self, world_id: str, location_name: str) -> List[str]:
        """获取地点连接
        
        Args:
            world_id: 世界ID
            location_name: 地点名称
            
        Returns:
            List[str]: 连接的地点名称列表
        """
        pass
    
    @abstractmethod
    def set_location_connection(self, world_id: str, from_location: str, to_location: str, bidirectional: bool = True) -> None:
        """设置地点连接
        
        Args:
            world_id: 世界ID
            from_location: 起始地点
            to_location: 目标地点
            bidirectional: 是否双向连接
        """
        pass
    
    @abstractmethod
    def remove_location_connection(self, world_id: str, from_location: str, to_location: str) -> None:
        """移除地点连接
        
        Args:
            world_id: 世界ID
            from_location: 起始地点
            to_location: 目标地点
        """
        pass
    
    @abstractmethod
    def get_world_events(self, world_id: str, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取世界事件
        
        Args:
            world_id: 世界ID
            event_type: 事件类型
            limit: 记录数量限制
            
        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        pass
    
    @abstractmethod
    def add_world_event(self, world_id: str, event_data: Dict[str, Any]) -> None:
        """添加世界事件
        
        Args:
            world_id: 世界ID
            event_data: 事件数据
        """
        pass
    
    @abstractmethod
    def get_world_configuration(self, world_id: str) -> Dict[str, Any]:
        """获取世界配置
        
        Args:
            world_id: 世界ID
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        pass
    
    @abstractmethod
    def update_world_configuration(self, world_id: str, config_data: Dict[str, Any]) -> None:
        """更新世界配置
        
        Args:
            world_id: 世界ID
            config_data: 配置数据
        """
        pass
    
    @abstractmethod
    def batch_save_worlds(self, worlds: List[World]) -> None:
        """批量保存世界
        
        Args:
            worlds: 世界列表
        """
        pass
    
    @abstractmethod
    def batch_delete_worlds(self, world_ids: List[str]) -> int:
        """批量删除世界
        
        Args:
            world_ids: 世界ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass
    
    @abstractmethod
    def get_world_creation_date(self, world_id: str) -> Optional[datetime]:
        """获取世界创建日期
        
        Args:
            world_id: 世界ID
            
        Returns:
            Optional[datetime]: 创建日期，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_world_last_modified(self, world_id: str) -> Optional[datetime]:
        """获取世界最后修改时间
        
        Args:
            world_id: 世界ID
            
        Returns:
            Optional[datetime]: 最后修改时间，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def archive_world(self, world_id: str) -> bool:
        """归档世界
        
        Args:
            world_id: 世界ID
            
        Returns:
            bool: 是否成功归档
        """
        pass
    
    @abstractmethod
    def unarchive_world(self, world_id: str) -> bool:
        """取消归档世界
        
        Args:
            world_id: 世界ID
            
        Returns:
            bool: 是否成功取消归档
        """
        pass
    
    @abstractmethod
    def is_world_archived(self, world_id: str) -> bool:
        """检查世界是否已归档
        
        Args:
            world_id: 世界ID
            
        Returns:
            bool: 是否已归档
        """
        pass