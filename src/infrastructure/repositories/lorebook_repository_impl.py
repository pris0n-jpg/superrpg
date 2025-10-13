"""
传说书仓储实现

提供传说书数据持久化的具体实现，基于JSON文件存储。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...domain.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from ...domain.models.lorebook import (
    Lorebook, LorebookEntry, KeywordPattern, ActivationRule, 
    ActivationType, KeywordType
)
from ...core.exceptions import ValidationException, BusinessRuleException


class LorebookRepositoryImpl(LorebookRepository):
    """传说书仓储实现
    
    基于JSON文件的传说书数据持久化实现。
    遵循单一职责原则，专门负责传说书数据的存储和检索。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """初始化传说书仓储
        
        Args:
            storage_path: 存储路径，如果为None则使用内存存储
        """
        self._storage_path = storage_path
        self._lorebooks: Dict[str, Lorebook] = {}
        
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
                
            # 加载传说书数据
            for lorebook_data in data.get('lorebooks', []):
                lorebook = self._deserialize_lorebook(lorebook_data)
                if lorebook:
                    self._lorebooks[str(lorebook.id)] = lorebook
                    
        except Exception as e:
            # 如果加载失败，初始化空数据
            self._lorebooks = {}
            print(f"Warning: Failed to load lorebook data: {e}")
    
    def _save_to_storage(self) -> None:
        """保存数据到存储"""
        if not self._storage_path:
            return
            
        try:
            # 确保目录存在
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'lorebooks': [self._serialize_lorebook(lorebook) for lorebook in self._lorebooks.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            # 静默处理保存错误，避免影响业务逻辑
            print(f"Warning: Failed to save lorebook data: {e}")
    
    def _serialize_lorebook(self, lorebook: Lorebook) -> Dict[str, Any]:
        """序列化传说书对象
        
        Args:
            lorebook: 传说书对象
            
        Returns:
            Dict[str, Any]: 序列化后的数据
        """
        return {
            'id': str(lorebook.id),
            'name': lorebook.name,
            'description': lorebook.description,
            'version': lorebook.version,
            'tags': list(lorebook.tags),
            'metadata': lorebook.metadata,
            'entries': [self._serialize_entry(entry) for entry in lorebook.entries],
            'created_at': lorebook.created_at.isoformat() if lorebook.created_at else None,
            'updated_at': lorebook.updated_at.isoformat() if lorebook.updated_at else None,
        }
    
    def _deserialize_lorebook(self, data: Dict[str, Any]) -> Optional[Lorebook]:
        """反序列化传说书对象
        
        Args:
            data: 序列化数据
            
        Returns:
            Optional[Lorebook]: 传说书对象，如果失败则返回None
        """
        try:
            # 创建传说书对象
            lorebook = Lorebook(
                name=data['name'],
                description=data.get('description', ''),
                version=data.get('version', '1.0.0'),
                tags=set(data.get('tags', [])),
                metadata=data.get('metadata', {})
            )
            
            # 设置ID（通过内部属性设置）
            lorebook._id = data['id']
            
            # 设置时间戳
            if data.get('created_at'):
                lorebook._created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                lorebook._updated_at = datetime.fromisoformat(data['updated_at'])
            
            # 加载条目
            for entry_data in data.get('entries', []):
                entry = self._deserialize_entry(entry_data)
                if entry:
                    lorebook.add_entry(entry)
            
            return lorebook
            
        except Exception as e:
            print(f"Warning: Failed to deserialize lorebook: {e}")
            return None
    
    def _serialize_entry(self, entry: LorebookEntry) -> Dict[str, Any]:
        """序列化条目对象
        
        Args:
            entry: 条目对象
            
        Returns:
            Dict[str, Any]: 序列化后的数据
        """
        return {
            'id': str(entry.id),
            'title': entry.title,
            'content': entry.content,
            'keywords': [
                {
                    'pattern': keyword.pattern,
                    'type': keyword.type.value,
                    'case_sensitive': keyword.case_sensitive,
                    'weight': keyword.weight
                } for keyword in entry.keywords
            ],
            'activation_rule': {
                'type': entry.activation_rule.type.value,
                'keywords': [
                    {
                        'pattern': keyword.pattern,
                        'type': keyword.type.value,
                        'case_sensitive': keyword.case_sensitive,
                        'weight': keyword.weight
                    } for keyword in entry.activation_rule.keywords
                ],
                'priority': entry.activation_rule.priority,
                'max_activations': entry.activation_rule.max_activations,
                'cooldown_seconds': entry.activation_rule.cooldown_seconds
            },
            'tags': list(entry.tags),
            'is_active': entry.is_active,
            'activation_count': entry.activation_count,
            'last_activated_at': entry.last_activated_at.isoformat() if entry.last_activated_at else None,
            'metadata': entry.metadata,
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
            'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
        }
    
    def _deserialize_entry(self, data: Dict[str, Any]) -> Optional[LorebookEntry]:
        """反序列化条目对象
        
        Args:
            data: 序列化数据
            
        Returns:
            Optional[LorebookEntry]: 条目对象，如果失败则返回None
        """
        try:
            # 转换关键词
            keywords = []
            for keyword_data in data.get('keywords', []):
                try:
                    keyword_type = KeywordType(keyword_data['type'])
                    keyword = KeywordPattern(
                        pattern=keyword_data['pattern'],
                        type=keyword_type,
                        case_sensitive=keyword_data.get('case_sensitive', False),
                        weight=keyword_data.get('weight', 1.0)
                    )
                    keywords.append(keyword)
                except (ValueError, KeyError):
                    continue
            
            # 转换激活规则
            activation_rule_data = data.get('activation_rule', {})
            activation_keywords = []
            for keyword_data in activation_rule_data.get('keywords', []):
                try:
                    keyword_type = KeywordType(keyword_data['type'])
                    keyword = KeywordPattern(
                        pattern=keyword_data['pattern'],
                        type=keyword_type,
                        case_sensitive=keyword_data.get('case_sensitive', False),
                        weight=keyword_data.get('weight', 1.0)
                    )
                    activation_keywords.append(keyword)
                except (ValueError, KeyError):
                    continue
            
            activation_rule = ActivationRule(
                type=ActivationType(activation_rule_data.get('type', 'keyword')),
                keywords=activation_keywords,
                priority=activation_rule_data.get('priority', 0),
                max_activations=activation_rule_data.get('max_activations'),
                cooldown_seconds=activation_rule_data.get('cooldown_seconds')
            )
            
            # 创建条目对象
            entry = LorebookEntry(
                title=data['title'],
                content=data['content'],
                keywords=keywords,
                activation_rule=activation_rule,
                tags=set(data.get('tags', [])),
                metadata=data.get('metadata', {})
            )
            
            # 设置ID和状态
            entry._id = data['id']
            entry.is_active = data.get('is_active', True)
            entry.activation_count = data.get('activation_count', 0)
            
            # 设置时间戳
            if data.get('last_activated_at'):
                entry.last_activated_at = datetime.fromisoformat(data['last_activated_at'])
            if data.get('created_at'):
                entry._created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                entry._updated_at = datetime.fromisoformat(data['updated_at'])
            
            return entry
            
        except Exception as e:
            print(f"Warning: Failed to deserialize entry: {e}")
            return None
    
    # 实现LorebookRepository接口方法
    
    def save(self, lorebook: Lorebook) -> None:
        """保存传说书"""
        if not lorebook.name:
            raise ValueError("传说书名称不能为空")
            
        self._lorebooks[str(lorebook.id)] = lorebook
        self._save_to_storage()
    
    def find_by_id(self, lorebook_id: str) -> Optional[Lorebook]:
        """根据ID查找传说书"""
        return self._lorebooks.get(lorebook_id)
    
    def find_by_name(self, name: str) -> Optional[Lorebook]:
        """根据名称查找传说书"""
        for lorebook in self._lorebooks.values():
            if lorebook.name == name:
                return lorebook
        return None
    
    def find_all(self) -> List[Lorebook]:
        """查找所有传说书"""
        return list(self._lorebooks.values())
    
    def find_by_tag(self, tag: str) -> List[Lorebook]:
        """根据标签查找传说书"""
        return [lorebook for lorebook in self._lorebooks.values() if tag in lorebook.tags]
    
    def find_by_keyword(self, keyword: str) -> List[Lorebook]:
        """根据关键词查找传说书"""
        matching_lorebooks = []
        
        for lorebook in self._lorebooks.values():
            for entry in lorebook.entries:
                for kw in entry.keywords:
                    if kw.matches(keyword):
                        matching_lorebooks.append(lorebook)
                        break
        
        return matching_lorebooks
    
    def update(self, lorebook: Lorebook) -> None:
        """更新传说书"""
        self.save(lorebook)
    
    def delete(self, lorebook_id: str) -> bool:
        """删除传说书"""
        if lorebook_id in self._lorebooks:
            del self._lorebooks[lorebook_id]
            self._save_to_storage()
            return True
        return False
    
    def exists_by_id(self, lorebook_id: str) -> bool:
        """检查传说书是否存在（根据ID）"""
        return lorebook_id in self._lorebooks
    
    def exists_by_name(self, name: str) -> bool:
        """检查传说书是否存在（根据名称）"""
        return self.find_by_name(name) is not None
    
    def count(self) -> int:
        """获取传说书总数"""
        return len(self._lorebooks)
    
    def search(self, criteria: Dict[str, Any]) -> List[Lorebook]:
        """根据条件搜索传说书"""
        result = []
        
        for lorebook in self._lorebooks.values():
            match = True
            
            for key, value in criteria.items():
                if key == 'name' and lorebook.name != value:
                    match = False
                elif key == 'version' and lorebook.version != value:
                    match = False
                elif key == 'tag' and value not in lorebook.tags:
                    match = False
                elif key == 'min_entries' and len(lorebook.entries) < value:
                    match = False
                
                if not match:
                    break
            
            if match:
                result.append(lorebook)
        
        return result
    
    def get_statistics(self, lorebook_id: str) -> Dict[str, Any]:
        """获取传说书统计信息"""
        lorebook = self.find_by_id(lorebook_id)
        if not lorebook:
            return {}
        
        active_entries = lorebook.get_active_entries()
        total_activations = sum(entry.activation_count for entry in lorebook.entries)
        
        return {
            "total_entries": len(lorebook.entries),
            "active_entries": len(active_entries),
            "total_activations": total_activations,
            "average_activations": total_activations / len(lorebook.entries) if lorebook.entries else 0,
            "tags": list(lorebook.tags),
            "version": lorebook.version
        }
    
    def export_lorebook(self, lorebook_id: str, format: str = "json") -> Dict[str, Any]:
        """导出传说书"""
        lorebook = self.find_by_id(lorebook_id)
        if not lorebook:
            raise ValueError(f"传说书不存在: {lorebook_id}")
        
        if format == "json":
            return self._serialize_lorebook(lorebook)
        elif format == "lorebook":
            # 自定义格式，可以在需要时扩展
            return {
                "format": "lorebook",
                "version": "1.0",
                "data": self._serialize_lorebook(lorebook)
            }
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def import_lorebook(self, data: Dict[str, Any], format: str = "json") -> Lorebook:
        """导入传说书"""
        if format == "json":
            lorebook = self._deserialize_lorebook(data)
        elif format == "lorebook":
            if data.get("format") != "lorebook":
                raise ValueError("无效的传说书格式")
            lorebook = self._deserialize_lorebook(data.get("data", {}))
        else:
            raise ValueError(f"不支持的导入格式: {format}")
        
        if not lorebook:
            raise ValueError("无法解析传说书数据")
        
        # 保存导入的传说书
        self.save(lorebook)
        
        return lorebook
    
    def batch_save(self, lorebooks: List[Lorebook]) -> None:
        """批量保存传说书"""
        for lorebook in lorebooks:
            self._lorebooks[str(lorebook.id)] = lorebook
        self._save_to_storage()
    
    def batch_delete(self, lorebook_ids: List[str]) -> int:
        """批量删除传说书"""
        deleted_count = 0
        for lorebook_id in lorebook_ids:
            if self.delete(lorebook_id):
                deleted_count += 1
        return deleted_count


class LorebookEntryRepositoryImpl(LorebookEntryRepository):
    """传说书条目仓储实现
    
    基于传说书仓储的条目数据持久化实现。
    遵循单一职责原则，专门负责条目数据的存储和检索。
    """
    
    def __init__(self, lorebook_repository: LorebookRepository):
        """初始化条目仓储
        
        Args:
            lorebook_repository: 传说书仓储
        """
        self._lorebook_repository = lorebook_repository
    
    def _get_lorebook(self, lorebook_id: str) -> Lorebook:
        """获取传说书
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            Lorebook: 传说书对象
            
        Raises:
            ValueError: 传说书不存在时抛出
        """
        lorebook = self._lorebook_repository.find_by_id(lorebook_id)
        if not lorebook:
            raise ValueError(f"传说书不存在: {lorebook_id}")
        return lorebook
    
    # 实现LorebookEntryRepository接口方法
    
    def save_entry(self, lorebook_id: str, entry: LorebookEntry) -> None:
        """保存条目"""
        lorebook = self._get_lorebook(lorebook_id)
        lorebook.add_entry(entry)
        self._lorebook_repository.save(lorebook)
    
    def find_entry_by_id(self, lorebook_id: str, entry_id: str) -> Optional[LorebookEntry]:
        """根据ID查找条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.get_entry_by_id(entry_id)
    
    def find_entry_by_title(self, lorebook_id: str, title: str) -> Optional[LorebookEntry]:
        """根据标题查找条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.get_entry_by_title(title)
    
    def find_entries_by_lorebook(self, lorebook_id: str) -> List[LorebookEntry]:
        """查找传说书的所有条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.entries.copy()
    
    def find_active_entries(self, lorebook_id: str) -> List[LorebookEntry]:
        """查找传说书的活跃条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.get_active_entries()
    
    def find_entries_by_tag(self, lorebook_id: str, tag: str) -> List[LorebookEntry]:
        """根据标签查找条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.find_entries_by_tag(tag)
    
    def find_entries_by_keyword(self, lorebook_id: str, keyword: str) -> List[LorebookEntry]:
        """根据关键词查找条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.find_entries_by_keyword(keyword)
    
    def update_entry(self, lorebook_id: str, entry: LorebookEntry) -> None:
        """更新条目"""
        lorebook = self._get_lorebook(lorebook_id)
        
        # 查找并更新现有条目
        for i, existing_entry in enumerate(lorebook.entries):
            if str(existing_entry.id) == str(entry.id):
                lorebook.entries[i] = entry
                break
        
        self._lorebook_repository.save(lorebook)
    
    def delete_entry(self, lorebook_id: str, entry_id: str) -> bool:
        """删除条目"""
        lorebook = self._get_lorebook(lorebook_id)
        success = lorebook.remove_entry(entry_id)
        
        if success:
            self._lorebook_repository.save(lorebook)
        
        return success
    
    def entry_exists(self, lorebook_id: str, entry_id: str) -> bool:
        """检查条目是否存在"""
        return self.find_entry_by_id(lorebook_id, entry_id) is not None
    
    def entry_title_exists(self, lorebook_id: str, title: str) -> bool:
        """检查条目标题是否存在"""
        return self.find_entry_by_title(lorebook_id, title) is not None
    
    def count_entries(self, lorebook_id: str) -> int:
        """获取条目总数"""
        lorebook = self._get_lorebook(lorebook_id)
        return len(lorebook.entries)
    
    def count_active_entries(self, lorebook_id: str) -> int:
        """获取活跃条目总数"""
        lorebook = self._get_lorebook(lorebook_id)
        return len(lorebook.get_active_entries())
    
    def search_entries(self, lorebook_id: str, criteria: Dict[str, Any]) -> List[LorebookEntry]:
        """根据条件搜索条目"""
        lorebook = self._get_lorebook(lorebook_id)
        result = []
        
        for entry in lorebook.entries:
            match = True
            
            for key, value in criteria.items():
                if key == 'title' and entry.title != value:
                    match = False
                elif key == 'is_active' and entry.is_active != value:
                    match = False
                elif key == 'tag' and value not in entry.tags:
                    match = False
                elif key == 'min_activations' and entry.activation_count < value:
                    match = False
                
                if not match:
                    break
            
            if match:
                result.append(entry)
        
        return result
    
    def get_entry_statistics(self, lorebook_id: str, entry_id: str) -> Dict[str, Any]:
        """获取条目统计信息"""
        entry = self.find_entry_by_id(lorebook_id, entry_id)
        if not entry:
            return {}
        
        return {
            "title": entry.title,
            "is_active": entry.is_active,
            "activation_count": entry.activation_count,
            "last_activated_at": entry.last_activated_at.isoformat() if entry.last_activated_at else None,
            "tags": list(entry.tags),
            "keywords_count": len(entry.keywords),
            "content_length": len(entry.content)
        }
    
    def get_most_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntry]:
        """获取最常激活的条目"""
        lorebook = self._get_lorebook(lorebook_id)
        entries = lorebook.entries.copy()
        
        # 按激活次数排序
        entries.sort(key=lambda e: e.activation_count, reverse=True)
        
        return entries[:limit]
    
    def get_recently_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntry]:
        """获取最近激活的条目"""
        lorebook = self._get_lorebook(lorebook_id)
        entries = [e for e in lorebook.entries if e.last_activated_at is not None]
        
        # 按最后激活时间排序
        entries.sort(key=lambda e: e.last_activated_at, reverse=True)
        
        return entries[:limit]
    
    def batch_save_entries(self, lorebook_id: str, entries: List[LorebookEntry]) -> None:
        """批量保存条目"""
        lorebook = self._get_lorebook(lorebook_id)
        
        for entry in entries:
            # 检查是否已存在
            existing_entry = lorebook.get_entry_by_id(str(entry.id))
            if existing_entry:
                # 更新现有条目
                for i, e in enumerate(lorebook.entries):
                    if str(e.id) == str(entry.id):
                        lorebook.entries[i] = entry
                        break
            else:
                # 添加新条目
                lorebook.add_entry(entry)
        
        self._lorebook_repository.save(lorebook)
    
    def batch_delete_entries(self, lorebook_id: str, entry_ids: List[str]) -> int:
        """批量删除条目"""
        lorebook = self._get_lorebook(lorebook_id)
        deleted_count = 0
        
        for entry_id in entry_ids:
            if lorebook.remove_entry(entry_id):
                deleted_count += 1
        
        if deleted_count > 0:
            self._lorebook_repository.save(lorebook)
        
        return deleted_count
    
    def activate_entries(self, lorebook_id: str, text: str, context: Dict[str, Any] = None) -> List[LorebookEntry]:
        """激活匹配的条目"""
        lorebook = self._get_lorebook(lorebook_id)
        return lorebook.activate_entries(text, context)