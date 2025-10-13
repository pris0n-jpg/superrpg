"""
传说书仓储接口

定义传说书聚合根的持久化契约，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models.lorebook import Lorebook, LorebookEntry


class LorebookRepository(ABC):
    """传说书仓储接口
    
    定义传说书聚合根的持久化操作契约。
    遵循依赖倒置原则，具体实现由基础设施层提供。
    """
    
    @abstractmethod
    def save(self, lorebook: Lorebook) -> None:
        """保存传说书
        
        Args:
            lorebook: 传说书聚合根
        """
        pass
    
    @abstractmethod
    def find_by_id(self, lorebook_id: str) -> Optional[Lorebook]:
        """根据ID查找传说书
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            Optional[Lorebook]: 传说书对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Lorebook]:
        """根据名称查找传说书
        
        Args:
            name: 传说书名称
            
        Returns:
            Optional[Lorebook]: 传说书对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Lorebook]:
        """查找所有传说书
        
        Returns:
            List[Lorebook]: 传说书列表
        """
        pass
    
    @abstractmethod
    def find_by_tag(self, tag: str) -> List[Lorebook]:
        """根据标签查找传说书
        
        Args:
            tag: 标签
            
        Returns:
            List[Lorebook]: 传说书列表
        """
        pass
    
    @abstractmethod
    def find_by_keyword(self, keyword: str) -> List[Lorebook]:
        """根据关键词查找传说书
        
        Args:
            keyword: 关键词
            
        Returns:
            List[Lorebook]: 传说书列表
        """
        pass
    
    @abstractmethod
    def update(self, lorebook: Lorebook) -> None:
        """更新传说书
        
        Args:
            lorebook: 传说书聚合根
        """
        pass
    
    @abstractmethod
    def delete(self, lorebook_id: str) -> bool:
        """删除传说书
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def exists_by_id(self, lorebook_id: str) -> bool:
        """检查传说书是否存在（根据ID）
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """检查传说书是否存在（根据名称）
        
        Args:
            name: 传说书名称
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取传说书总数
        
        Returns:
            int: 传说书总数
        """
        pass
    
    @abstractmethod
    def search(self, criteria: Dict[str, Any]) -> List[Lorebook]:
        """根据条件搜索传说书
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[Lorebook]: 匹配的传说书列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self, lorebook_id: str) -> Dict[str, Any]:
        """获取传说书统计信息
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    def export_lorebook(self, lorebook_id: str, format: str = "json") -> Dict[str, Any]:
        """导出传说书
        
        Args:
            lorebook_id: 传说书ID
            format: 导出格式
            
        Returns:
            Dict[str, Any]: 导出数据
        """
        pass
    
    @abstractmethod
    def import_lorebook(self, data: Dict[str, Any], format: str = "json") -> Lorebook:
        """导入传说书
        
        Args:
            data: 导入数据
            format: 导入格式
            
        Returns:
            Lorebook: 导入的传说书对象
        """
        pass
    
    @abstractmethod
    def batch_save(self, lorebooks: List[Lorebook]) -> None:
        """批量保存传说书
        
        Args:
            lorebooks: 传说书列表
        """
        pass
    
    @abstractmethod
    def batch_delete(self, lorebook_ids: List[str]) -> int:
        """批量删除传说书
        
        Args:
            lorebook_ids: 传说书ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass


class LorebookEntryRepository(ABC):
    """传说书条目仓储接口
    
    定义传说书条目的持久化操作契约。
    遵循依赖倒置原则，具体实现由基础设施层提供。
    """
    
    @abstractmethod
    def save_entry(self, lorebook_id: str, entry: LorebookEntry) -> None:
        """保存条目
        
        Args:
            lorebook_id: 传说书ID
            entry: 条目对象
        """
        pass
    
    @abstractmethod
    def find_entry_by_id(self, lorebook_id: str, entry_id: str) -> Optional[LorebookEntry]:
        """根据ID查找条目
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            Optional[LorebookEntry]: 条目对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_entry_by_title(self, lorebook_id: str, title: str) -> Optional[LorebookEntry]:
        """根据标题查找条目
        
        Args:
            lorebook_id: 传说书ID
            title: 条目标题
            
        Returns:
            Optional[LorebookEntry]: 条目对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_entries_by_lorebook(self, lorebook_id: str) -> List[LorebookEntry]:
        """查找传说书的所有条目
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            List[LorebookEntry]: 条目列表
        """
        pass
    
    @abstractmethod
    def find_active_entries(self, lorebook_id: str) -> List[LorebookEntry]:
        """查找传说书的活跃条目
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            List[LorebookEntry]: 活跃条目列表
        """
        pass
    
    @abstractmethod
    def find_entries_by_tag(self, lorebook_id: str, tag: str) -> List[LorebookEntry]:
        """根据标签查找条目
        
        Args:
            lorebook_id: 传说书ID
            tag: 标签
            
        Returns:
            List[LorebookEntry]: 条目列表
        """
        pass
    
    @abstractmethod
    def find_entries_by_keyword(self, lorebook_id: str, keyword: str) -> List[LorebookEntry]:
        """根据关键词查找条目
        
        Args:
            lorebook_id: 传说书ID
            keyword: 关键词
            
        Returns:
            List[LorebookEntry]: 条目列表
        """
        pass
    
    @abstractmethod
    def update_entry(self, lorebook_id: str, entry: LorebookEntry) -> None:
        """更新条目
        
        Args:
            lorebook_id: 传说书ID
            entry: 条目对象
        """
        pass
    
    @abstractmethod
    def delete_entry(self, lorebook_id: str, entry_id: str) -> bool:
        """删除条目
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def entry_exists(self, lorebook_id: str, entry_id: str) -> bool:
        """检查条目是否存在
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def entry_title_exists(self, lorebook_id: str, title: str) -> bool:
        """检查条目标题是否存在
        
        Args:
            lorebook_id: 传说书ID
            title: 条目标题
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count_entries(self, lorebook_id: str) -> int:
        """获取条目总数
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            int: 条目总数
        """
        pass
    
    @abstractmethod
    def count_active_entries(self, lorebook_id: str) -> int:
        """获取活跃条目总数
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            int: 活跃条目总数
        """
        pass
    
    @abstractmethod
    def search_entries(self, lorebook_id: str, criteria: Dict[str, Any]) -> List[LorebookEntry]:
        """根据条件搜索条目
        
        Args:
            lorebook_id: 传说书ID
            criteria: 搜索条件
            
        Returns:
            List[LorebookEntry]: 匹配的条目列表
        """
        pass
    
    @abstractmethod
    def get_entry_statistics(self, lorebook_id: str, entry_id: str) -> Dict[str, Any]:
        """获取条目统计信息
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    def get_most_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntry]:
        """获取最常激活的条目
        
        Args:
            lorebook_id: 传说书ID
            limit: 返回数量限制
            
        Returns:
            List[LorebookEntry]: 条目列表
        """
        pass
    
    @abstractmethod
    def get_recently_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntry]:
        """获取最近激活的条目
        
        Args:
            lorebook_id: 传说书ID
            limit: 返回数量限制
            
        Returns:
            List[LorebookEntry]: 条目列表
        """
        pass
    
    @abstractmethod
    def batch_save_entries(self, lorebook_id: str, entries: List[LorebookEntry]) -> None:
        """批量保存条目
        
        Args:
            lorebook_id: 传说书ID
            entries: 条目列表
        """
        pass
    
    @abstractmethod
    def batch_delete_entries(self, lorebook_id: str, entry_ids: List[str]) -> int:
        """批量删除条目
        
        Args:
            lorebook_id: 传说书ID
            entry_ids: 条目ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass
    
    @abstractmethod
    def activate_entries(self, lorebook_id: str, text: str, context: Dict[str, Any] = None) -> List[LorebookEntry]:
        """激活匹配的条目
        
        Args:
            lorebook_id: 传说书ID
            text: 触发文本
            context: 上下文信息
            
        Returns:
            List[LorebookEntry]: 成功激活的条目列表
        """
        pass