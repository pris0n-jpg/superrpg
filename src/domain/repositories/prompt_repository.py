"""
提示仓储接口

定义提示模板聚合根的持久化契约，遵循SOLID原则，
特别是依赖倒置原则(DIP)和接口隔离原则(ISP)。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..models.prompt import PromptTemplate


class PromptRepository(ABC):
    """提示仓储接口
    
    定义提示模板聚合根的持久化操作契约。
    遵循依赖倒置原则，具体实现由基础设施层提供。
    """
    
    @abstractmethod
    def save(self, template: PromptTemplate) -> None:
        """保存提示模板
        
        Args:
            template: 提示模板聚合根
        """
        pass
    
    @abstractmethod
    def find_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """根据ID查找提示模板
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            Optional[PromptTemplate]: 提示模板对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[PromptTemplate]:
        """根据名称查找提示模板
        
        Args:
            name: 提示模板名称
            
        Returns:
            Optional[PromptTemplate]: 提示模板对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[PromptTemplate]:
        """查找所有提示模板
        
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def find_by_tag(self, tag: str) -> List[PromptTemplate]:
        """根据标签查找提示模板
        
        Args:
            tag: 标签
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def find_by_keyword(self, keyword: str) -> List[PromptTemplate]:
        """根据关键词查找提示模板
        
        Args:
            keyword: 关键词
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def find_active(self) -> List[PromptTemplate]:
        """查找所有活跃的提示模板
        
        Returns:
            List[PromptTemplate]: 活跃的提示模板列表
        """
        pass
    
    @abstractmethod
    def update(self, template: PromptTemplate) -> None:
        """更新提示模板
        
        Args:
            template: 提示模板聚合根
        """
        pass
    
    @abstractmethod
    def delete(self, template_id: str) -> bool:
        """删除提示模板
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            bool: 是否成功删除
        """
        pass
    
    @abstractmethod
    def exists_by_id(self, template_id: str) -> bool:
        """检查提示模板是否存在（根据ID）
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """检查提示模板是否存在（根据名称）
        
        Args:
            name: 提示模板名称
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """获取提示模板总数
        
        Returns:
            int: 提示模板总数
        """
        pass
    
    @abstractmethod
    def count_active(self) -> int:
        """获取活跃提示模板总数
        
        Returns:
            int: 活跃提示模板总数
        """
        pass
    
    @abstractmethod
    def search(self, criteria: Dict[str, Any]) -> List[PromptTemplate]:
        """根据条件搜索提示模板
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[PromptTemplate]: 匹配的提示模板列表
        """
        pass
    
    @abstractmethod
    def get_statistics(self, template_id: str) -> Dict[str, Any]:
        """获取提示模板统计信息
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass
    
    @abstractmethod
    def export_template(self, template_id: str, format: str = "json") -> Dict[str, Any]:
        """导出提示模板
        
        Args:
            template_id: 提示模板ID
            format: 导出格式
            
        Returns:
            Dict[str, Any]: 导出数据
        """
        pass
    
    @abstractmethod
    def import_template(self, data: Dict[str, Any], format: str = "json") -> PromptTemplate:
        """导入提示模板
        
        Args:
            data: 导入数据
            format: 导入格式
            
        Returns:
            PromptTemplate: 导入的提示模板对象
        """
        pass
    
    @abstractmethod
    def batch_save(self, templates: List[PromptTemplate]) -> None:
        """批量保存提示模板
        
        Args:
            templates: 提示模板列表
        """
        pass
    
    @abstractmethod
    def batch_delete(self, template_ids: List[str]) -> int:
        """批量删除提示模板
        
        Args:
            template_ids: 提示模板ID列表
            
        Returns:
            int: 成功删除的数量
        """
        pass
    
    @abstractmethod
    def get_recently_used(self, limit: int = 10) -> List[PromptTemplate]:
        """获取最近使用的提示模板
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def get_most_used(self, limit: int = 10) -> List[PromptTemplate]:
        """获取最常使用的提示模板
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def update_usage_stats(self, template_id: str) -> None:
        """更新使用统计
        
        Args:
            template_id: 提示模板ID
        """
        pass
    
    @abstractmethod
    def get_templates_by_section_type(self, section_type: str) -> List[PromptTemplate]:
        """根据段落类型获取提示模板
        
        Args:
            section_type: 段落类型
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass
    
    @abstractmethod
    def get_templates_with_variables(self, variables: List[str]) -> List[PromptTemplate]:
        """获取包含指定变量的提示模板
        
        Args:
            variables: 变量列表
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        pass