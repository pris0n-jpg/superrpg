"""
提示仓储实现

提供提示模板的文件系统持久化实现，遵循SOLID原则，
特别是单一职责原则(SRP)和里氏替换原则(LSP)。
"""

import json
import os
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from ...domain.models.base import EntityId
from ...domain.models.prompt import PromptTemplate, PromptSection, PromptSectionType
from ...domain.repositories.prompt_repository import PromptRepository
from ...core.interfaces import Logger
from ...core.exceptions import RepositoryException, ValidationException


class PromptRepositoryImpl(PromptRepository):
    """提示仓储实现
    
    基于文件系统的提示模板持久化实现。
    遵循单一职责原则，专门负责提示模板的文件存储。
    """
    
    def __init__(self, storage_path: Optional[str] = None, logger: Optional[Logger] = None):
        """初始化提示仓储
        
        Args:
            storage_path: 存储路径
            logger: 日志记录器
        """
        self._logger = logger
        self._storage_path = Path(storage_path) if storage_path else Path.cwd() / "data" / "prompts"
        
        # 确保存储目录存在
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # 创建索引文件路径
        self._index_file = self._storage_path / "index.json"
        self._stats_file = self._storage_path / "stats.json"
        
        # 初始化索引和统计
        self._initialize_storage()
    
    def save(self, template: PromptTemplate) -> None:
        """保存提示模板
        
        Args:
            template: 提示模板聚合根
            
        Raises:
            RepositoryException: 保存失败时抛出
        """
        try:
            # 创建模板文件路径
            template_file = self._storage_path / f"{template.id}.json"
            
            # 转换为字典并保存
            template_data = template.export_to_dict()
            template_data['last_used'] = datetime.now().isoformat()
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            # 更新索引
            self._update_index(template)
            
            # 更新统计
            self._update_stats(str(template.id), 'created')
            
            if self._logger:
                self._logger.info(f"Saved prompt template: {template.name} (ID: {template.id})")
                
        except Exception as e:
            error_msg = f"Failed to save prompt template {template.id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="save", entity_type="PromptTemplate", entity_id=str(template.id))
    
    def find_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """根据ID查找提示模板
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            Optional[PromptTemplate]: 提示模板对象，如果不存在则返回None
        """
        try:
            template_file = self._storage_path / f"{template_id}.json"
            
            if not template_file.exists():
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            return self._dict_to_template(template_data)
            
        except Exception as e:
            error_msg = f"Failed to find prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_by_id", entity_type="PromptTemplate", entity_id=template_id)
    
    def find_by_name(self, name: str) -> Optional[PromptTemplate]:
        """根据名称查找提示模板
        
        Args:
            name: 提示模板名称
            
        Returns:
            Optional[PromptTemplate]: 提示模板对象，如果不存在则返回None
        """
        try:
            # 加载索引
            index = self._load_index()
            
            # 在索引中查找名称
            for template_id, template_info in index.items():
                if template_info.get('name') == name:
                    return self.find_by_id(template_id)
            
            return None
            
        except Exception as e:
            error_msg = f"Failed to find prompt template by name {name}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_by_name", entity_type="PromptTemplate")
    
    def find_all(self) -> List[PromptTemplate]:
        """查找所有提示模板
        
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            templates = []
            
            # 遍历所有JSON文件
            for file_path in self._storage_path.glob("*.json"):
                if file_path.name in ["index.json", "stats.json"]:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    template = self._dict_to_template(template_data)
                    templates.append(template)
                    
                except Exception as e:
                    if self._logger:
                        self._logger.warning(f"Failed to load template from {file_path}: {e}")
                    continue
            
            return templates
            
        except Exception as e:
            error_msg = f"Failed to find all prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_all", entity_type="PromptTemplate")
    
    def find_by_tag(self, tag: str) -> List[PromptTemplate]:
        """根据标签查找提示模板
        
        Args:
            tag: 标签
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            all_templates = self.find_all()
            return [t for t in all_templates if tag in t.metadata.get('tags', [])]
            
        except Exception as e:
            error_msg = f"Failed to find prompt templates by tag {tag}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_by_tag", entity_type="PromptTemplate")
    
    def find_by_keyword(self, keyword: str) -> List[PromptTemplate]:
        """根据关键词查找提示模板
        
        Args:
            keyword: 关键词
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            all_templates = self.find_all()
            keyword_lower = keyword.lower()
            
            matching_templates = []
            for template in all_templates:
                # 搜索名称、描述和内容
                if (keyword_lower in template.name.lower() or
                    keyword_lower in template.description.lower() or
                    any(keyword_lower in section.content.lower() for section in template.sections)):
                    matching_templates.append(template)
            
            return matching_templates
            
        except Exception as e:
            error_msg = f"Failed to find prompt templates by keyword {keyword}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_by_keyword", entity_type="PromptTemplate")
    
    def find_active(self) -> List[PromptTemplate]:
        """查找所有活跃的提示模板
        
        Returns:
            List[PromptTemplate]: 活跃的提示模板列表
        """
        try:
            all_templates = self.find_all()
            return [t for t in all_templates if t.is_active]
            
        except Exception as e:
            error_msg = f"Failed to find active prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="find_active", entity_type="PromptTemplate")
    
    def update(self, template: PromptTemplate) -> None:
        """更新提示模板
        
        Args:
            template: 提示模板聚合根
            
        Raises:
            RepositoryException: 更新失败时抛出
        """
        try:
            # 检查模板是否存在
            template_file = self._storage_path / f"{template.id}.json"
            if not template_file.exists():
                raise RepositoryException(f"Template not found: {template.id}", operation="update", entity_type="PromptTemplate", entity_id=str(template.id))
            
            # 保存更新
            self.save(template)
            
            if self._logger:
                self._logger.info(f"Updated prompt template: {template.name} (ID: {template.id})")
                
        except Exception as e:
            error_msg = f"Failed to update prompt template {template.id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="update", entity_type="PromptTemplate", entity_id=str(template.id))
    
    def delete(self, template_id: str) -> bool:
        """删除提示模板
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            bool: 是否成功删除
        """
        try:
            template_file = self._storage_path / f"{template_id}.json"
            
            if not template_file.exists():
                return False
            
            # 删除文件
            template_file.unlink()
            
            # 更新索引
            self._remove_from_index(template_id)
            
            # 更新统计
            self._update_stats(str(template_id), 'deleted')
            
            if self._logger:
                self._logger.info(f"Deleted prompt template: {template_id}")
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="delete", entity_type="PromptTemplate", entity_id=template_id)
    
    def exists_by_id(self, template_id: str) -> bool:
        """检查提示模板是否存在（根据ID）
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            bool: 是否存在
        """
        try:
            template_file = self._storage_path / f"{template_id}.json"
            return template_file.exists()
            
        except Exception as e:
            error_msg = f"Failed to check existence of prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return False
    
    def exists_by_name(self, name: str) -> bool:
        """检查提示模板是否存在（根据名称）
        
        Args:
            name: 提示模板名称
            
        Returns:
            bool: 是否存在
        """
        try:
            return self.find_by_name(name) is not None
            
        except Exception as e:
            error_msg = f"Failed to check existence of prompt template by name {name}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return False
    
    def count(self) -> int:
        """获取提示模板总数
        
        Returns:
            int: 提示模板总数
        """
        try:
            count = 0
            for file_path in self._storage_path.glob("*.json"):
                if file_path.name not in ["index.json", "stats.json"]:
                    count += 1
            return count
            
        except Exception as e:
            error_msg = f"Failed to count prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return 0
    
    def count_active(self) -> int:
        """获取活跃提示模板总数
        
        Returns:
            int: 活跃提示模板总数
        """
        try:
            return len(self.find_active())
            
        except Exception as e:
            error_msg = f"Failed to count active prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return 0
    
    def search(self, criteria: Dict[str, Any]) -> List[PromptTemplate]:
        """根据条件搜索提示模板
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[PromptTemplate]: 匹配的提示模板列表
        """
        try:
            all_templates = self.find_all()
            
            # 应用过滤条件
            filtered_templates = all_templates
            
            # 按名称过滤
            if 'name' in criteria:
                name_filter = criteria['name'].lower()
                filtered_templates = [t for t in filtered_templates if name_filter in t.name.lower()]
            
            # 按描述过滤
            if 'description' in criteria:
                desc_filter = criteria['description'].lower()
                filtered_templates = [t for t in filtered_templates if desc_filter in t.description.lower()]
            
            # 按活跃状态过滤
            if 'is_active' in criteria:
                active_filter = criteria['is_active']
                filtered_templates = [t for t in filtered_templates if t.is_active == active_filter]
            
            # 按标签过滤
            if 'tags' in criteria:
                required_tags = criteria['tags']
                filtered_templates = [t for t in filtered_templates 
                                   if any(tag in t.metadata.get('tags', []) for tag in required_tags)]
            
            # 按变量过滤
            if 'variables' in criteria:
                required_vars = criteria['variables']
                filtered_templates = [t for t in filtered_templates 
                                   if any(var in t.variables for var in required_vars)]
            
            # 按段落类型过滤
            if 'section_types' in criteria:
                required_section_types = criteria['section_types']
                filtered_templates = [t for t in filtered_templates 
                                   if any(section.section_type.value in required_section_types 
                                       for section in t.sections)]
            
            return filtered_templates
            
        except Exception as e:
            error_msg = f"Failed to search prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="search", entity_type="PromptTemplate")
    
    def get_statistics(self, template_id: str) -> Dict[str, Any]:
        """获取提示模板统计信息
        
        Args:
            template_id: 提示模板ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            template = self.find_by_id(template_id)
            if not template:
                return {}
            
            # 获取使用统计
            stats = self._load_stats()
            template_stats = stats.get(template_id, {})
            
            # 计算基本统计
            total_sections = len(template.sections)
            total_tokens = sum(section.token_count for section in template.sections)
            
            # 按类型统计
            sections_by_type = {}
            tokens_by_type = {}
            
            for section in template.sections:
                section_type = section.section_type.value
                sections_by_type[section_type] = sections_by_type.get(section_type, 0) + 1
                tokens_by_type[section_type] = tokens_by_type.get(section_type, 0) + section.token_count
            
            return {
                'template_id': template_id,
                'template_name': template.name,
                'total_sections': total_sections,
                'total_tokens': total_tokens,
                'sections_by_type': sections_by_type,
                'tokens_by_type': tokens_by_type,
                'variable_count': len(template.variables),
                'is_active': template.is_active,
                'version': template.version,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                'usage_count': template_stats.get('usage_count', 0),
                'last_used': template_stats.get('last_used'),
                'created_stats': template_stats.get('created'),
                'modified_stats': template_stats.get('modified')
            }
            
        except Exception as e:
            error_msg = f"Failed to get statistics for prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return {}
    
    def export_template(self, template_id: str, format: str = "json") -> Dict[str, Any]:
        """导出提示模板
        
        Args:
            template_id: 提示模板ID
            format: 导出格式
            
        Returns:
            Dict[str, Any]: 导出数据
        """
        try:
            template = self.find_by_id(template_id)
            if not template:
                raise RepositoryException(f"Template not found: {template_id}", operation="export", entity_type="PromptTemplate", entity_id=template_id)
            
            if format.lower() == "json":
                return template.export_to_dict()
            else:
                raise ValidationException(f"Unsupported export format: {format}")
                
        except Exception as e:
            error_msg = f"Failed to export prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="export", entity_type="PromptTemplate", entity_id=template_id)
    
    def import_template(self, data: Dict[str, Any], format: str = "json") -> PromptTemplate:
        """导入提示模板
        
        Args:
            data: 导入数据
            format: 导入格式
            
        Returns:
            PromptTemplate: 导入的提示模板对象
        """
        try:
            if format.lower() == "json":
                template = self._dict_to_template(data)
                
                # 检查是否已存在同名模板
                if self.exists_by_name(template.name):
                    # 生成新名称
                    base_name = template.name
                    counter = 1
                    while self.exists_by_name(f"{base_name}_{counter}"):
                        counter += 1
                    template.update_info(name=f"{base_name}_{counter}")
                
                # 保存模板
                self.save(template)
                
                if self._logger:
                    self._logger.info(f"Imported prompt template: {template.name} (ID: {template.id})")
                
                return template
            else:
                raise ValidationException(f"Unsupported import format: {format}")
                
        except Exception as e:
            error_msg = f"Failed to import prompt template: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="import", entity_type="PromptTemplate")
    
    def batch_save(self, templates: List[PromptTemplate]) -> None:
        """批量保存提示模板
        
        Args:
            templates: 提示模板列表
        """
        try:
            for template in templates:
                self.save(template)
                
            if self._logger:
                self._logger.info(f"Batch saved {len(templates)} prompt templates")
                
        except Exception as e:
            error_msg = f"Failed to batch save prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="batch_save", entity_type="PromptTemplate")
    
    def batch_delete(self, template_ids: List[str]) -> int:
        """批量删除提示模板
        
        Args:
            template_ids: 提示模板ID列表
            
        Returns:
            int: 成功删除的数量
        """
        try:
            deleted_count = 0
            
            for template_id in template_ids:
                if self.delete(template_id):
                    deleted_count += 1
            
            if self._logger:
                self._logger.info(f"Batch deleted {deleted_count} prompt templates")
            
            return deleted_count
            
        except Exception as e:
            error_msg = f"Failed to batch delete prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            raise RepositoryException(error_msg, operation="batch_delete", entity_type="PromptTemplate")
    
    def get_recently_used(self, limit: int = 10) -> List[PromptTemplate]:
        """获取最近使用的提示模板
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            stats = self._load_stats()
            
            # 按最后使用时间排序
            recently_used = []
            for template_id, template_stats in stats.items():
                if 'last_used' in template_stats:
                    template = self.find_by_id(template_id)
                    if template:
                        recently_used.append((template, template_stats['last_used']))
            
            # 排序并限制数量
            recently_used.sort(key=lambda x: x[1], reverse=True)
            return [template for template, _ in recently_used[:limit]]
            
        except Exception as e:
            error_msg = f"Failed to get recently used prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return []
    
    def get_most_used(self, limit: int = 10) -> List[PromptTemplate]:
        """获取最常使用的提示模板
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            stats = self._load_stats()
            
            # 按使用次数排序
            most_used = []
            for template_id, template_stats in stats.items():
                usage_count = template_stats.get('usage_count', 0)
                if usage_count > 0:
                    template = self.find_by_id(template_id)
                    if template:
                        most_used.append((template, usage_count))
            
            # 排序并限制数量
            most_used.sort(key=lambda x: x[1], reverse=True)
            return [template for template, _ in most_used[:limit]]
            
        except Exception as e:
            error_msg = f"Failed to get most used prompt templates: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return []
    
    def update_usage_stats(self, template_id: str) -> None:
        """更新使用统计
        
        Args:
            template_id: 提示模板ID
        """
        try:
            self._update_stats(str(template_id), 'used')
            
        except Exception as e:
            error_msg = f"Failed to update usage stats for prompt template {template_id}: {e}"
            if self._logger:
                self._logger.error(error_msg)
    
    def get_templates_by_section_type(self, section_type: str) -> List[PromptTemplate]:
        """根据段落类型获取提示模板
        
        Args:
            section_type: 段落类型
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            all_templates = self.find_all()
            return [t for t in all_templates 
                   if any(section.section_type.value == section_type for section in t.sections)]
            
        except Exception as e:
            error_msg = f"Failed to get prompt templates by section type {section_type}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return []
    
    def get_templates_with_variables(self, variables: List[str]) -> List[PromptTemplate]:
        """获取包含指定变量的提示模板
        
        Args:
            variables: 变量列表
            
        Returns:
            List[PromptTemplate]: 提示模板列表
        """
        try:
            all_templates = self.find_all()
            return [t for t in all_templates 
                   if any(var in t.variables for var in variables)]
            
        except Exception as e:
            error_msg = f"Failed to get prompt templates with variables {variables}: {e}"
            if self._logger:
                self._logger.error(error_msg)
            return []
    
    # 私有辅助方法
    
    def _initialize_storage(self) -> None:
        """初始化存储"""
        try:
            # 创建索引文件
            if not self._index_file.exists():
                with open(self._index_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
            
            # 创建统计文件
            if not self._stats_file.exists():
                with open(self._stats_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to initialize storage: {e}")
    
    def _load_index(self) -> Dict[str, Any]:
        """加载索引"""
        try:
            with open(self._index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_index(self, index: Dict[str, Any]) -> None:
        """保存索引"""
        try:
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to save index: {e}")
    
    def _update_index(self, template: PromptTemplate) -> None:
        """更新索引"""
        try:
            index = self._load_index()
            
            index[str(template.id)] = {
                'name': template.name,
                'description': template.description,
                'is_active': template.is_active,
                'version': template.version,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                'variables': list(template.variables),
                'section_types': [section.section_type.value for section in template.sections],
                'tags': template.metadata.get('tags', [])
            }
            
            self._save_index(index)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to update index: {e}")
    
    def _remove_from_index(self, template_id: str) -> None:
        """从索引中移除"""
        try:
            index = self._load_index()
            
            if template_id in index:
                del index[template_id]
                self._save_index(index)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to remove from index: {e}")
    
    def _load_stats(self) -> Dict[str, Any]:
        """加载统计"""
        try:
            with open(self._stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_stats(self, stats: Dict[str, Any]) -> None:
        """保存统计"""
        try:
            with open(self._stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to save stats: {e}")
    
    def _update_stats(self, template_id: str, action: str) -> None:
        """更新统计"""
        try:
            stats = self._load_stats()
            
            if template_id not in stats:
                stats[template_id] = {}
            
            template_stats = stats[template_id]
            now = datetime.now().isoformat()
            
            if action == 'created':
                template_stats['created'] = now
                template_stats['usage_count'] = 0
            elif action == 'used':
                template_stats['usage_count'] = template_stats.get('usage_count', 0) + 1
                template_stats['last_used'] = now
            elif action == 'modified':
                template_stats['modified'] = now
            elif action == 'deleted':
                # 标记为已删除，但保留统计信息
                template_stats['deleted'] = now
            
            self._save_stats(stats)
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to update stats: {e}")
    
    def _dict_to_template(self, data: Dict[str, Any]) -> PromptTemplate:
        """将字典转换为模板对象"""
        try:
            # 转换段落数据
            sections = []
            for section_data in data.get('sections', []):
                try:
                    section_type = PromptSectionType(section_data.get('section_type', 'custom'))
                    section = PromptSection(
                        content=section_data['content'],
                        section_type=section_type,
                        priority=section_data.get('priority', 0),
                        token_count=section_data.get('token_count', 0),
                        metadata=section_data.get('metadata', {})
                    )
                    sections.append(section)
                except ValueError:
                    # 如果段落类型无效，使用默认类型
                    section = PromptSection(
                        content=section_data['content'],
                        section_type=PromptSectionType.CUSTOM,
                        priority=section_data.get('priority', 0),
                        token_count=section_data.get('token_count', 0),
                        metadata=section_data.get('metadata', {})
                    )
                    sections.append(section)
            
            # 创建模板
            template = PromptTemplate(
                name=data['name'],
                description=data.get('description', ''),
                sections=sections,
                metadata=data.get('metadata', {}),
                version=data.get('version', '1.0.0')
            )

            if data.get('id'):
                template._id = EntityId(data['id'])

            template.clear_domain_events()
            
            # 设置活跃状态
            if 'is_active' in data:
                if data['is_active'] and not template.is_active:
                    template.activate()
                elif not data['is_active'] and template.is_active:
                    template.deactivate()
            
            # 设置时间戳
            if data.get('created_at'):
                template._created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                template._updated_at = datetime.fromisoformat(data['updated_at'])
            
            return template
            
        except Exception as e:
            raise ValidationException(f"Invalid template data: {e}")