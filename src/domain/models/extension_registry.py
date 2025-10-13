"""
扩展注册表模型模块

该模块实现扩展注册表的数据模型，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责扩展注册信息的管理。
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json

from ..responses.api_response import ApiResponse


@dataclass
class ExtensionInfo:
    """扩展信息
    
    封装扩展的基本信息和状态，遵循单一职责原则。
    """
    
    id: str
    name: str
    version: str
    description: str
    author: str
    extension_type: str
    status: str
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    license: Optional[str] = None
    load_time: Optional[datetime] = None
    activate_time: Optional[datetime] = None
    error_message: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 扩展信息的字典表示
        """
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "extension_type": self.extension_type,
            "status": self.status,
            "dependencies": self.dependencies,
            "optional_dependencies": self.optional_dependencies,
            "tags": self.tags,
            "homepage": self.homepage,
            "license": self.license,
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "activate_time": self.activate_time.isoformat() if self.activate_time else None,
            "error_message": self.error_message,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtensionInfo':
        """从字典创建扩展信息
        
        Args:
            data: 字典数据
            
        Returns:
            ExtensionInfo: 扩展信息实例
        """
        load_time = None
        if data.get("load_time"):
            load_time = datetime.fromisoformat(data["load_time"])
        
        activate_time = None
        if data.get("activate_time"):
            activate_time = datetime.fromisoformat(data["activate_time"])
        
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            author=data["author"],
            extension_type=data["extension_type"],
            status=data["status"],
            dependencies=data.get("dependencies", []),
            optional_dependencies=data.get("optional_dependencies", []),
            tags=data.get("tags", []),
            homepage=data.get("homepage"),
            license=data.get("license"),
            load_time=load_time,
            activate_time=activate_time,
            error_message=data.get("error_message"),
            config=data.get("config", {})
        )


@dataclass
class ExtensionDependency:
    """扩展依赖关系
    
    封装扩展之间的依赖关系，遵循单一职责原则。
    """
    
    extension_id: str
    dependency_id: str
    dependency_type: str  # required, optional
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 依赖关系的字典表示
        """
        return {
            "extension_id": self.extension_id,
            "dependency_id": self.dependency_id,
            "dependency_type": self.dependency_type,
            "min_version": self.min_version,
            "max_version": self.max_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtensionDependency':
        """从字典创建依赖关系
        
        Args:
            data: 字典数据
            
        Returns:
            ExtensionDependency: 依赖关系实例
        """
        return cls(
            extension_id=data["extension_id"],
            dependency_id=data["dependency_id"],
            dependency_type=data["dependency_type"],
            min_version=data.get("min_version"),
            max_version=data.get("max_version")
        )


@dataclass
class ExtensionRegistry:
    """扩展注册表
    
    管理所有扩展的注册信息，遵循单一职责原则。
    """
    
    extensions: Dict[str, ExtensionInfo] = field(default_factory=dict)
    dependencies: List[ExtensionDependency] = field(default_factory=list)
    categories: Dict[str, List[str]] = field(default_factory=dict)
    tags_index: Dict[str, Set[str]] = field(default_factory=dict)
    
    def register_extension(self, extension_info: ExtensionInfo) -> bool:
        """注册扩展
        
        Args:
            extension_info: 扩展信息
            
        Returns:
            bool: 是否成功注册
        """
        if extension_info.id in self.extensions:
            return False
        
        self.extensions[extension_info.id] = extension_info
        
        # 更新标签索引
        for tag in extension_info.tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = set()
            self.tags_index[tag].add(extension_info.id)
        
        return True
    
    def unregister_extension(self, extension_id: str) -> bool:
        """注销扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功注销
        """
        if extension_id not in self.extensions:
            return False
        
        extension_info = self.extensions[extension_id]
        
        # 从标签索引中移除
        for tag in extension_info.tags:
            if tag in self.tags_index:
                self.tags_index[tag].discard(extension_id)
                if not self.tags_index[tag]:
                    del self.tags_index[tag]
        
        # 移除扩展
        del self.extensions[extension_id]
        
        # 移除相关依赖关系
        self.dependencies = [
            dep for dep in self.dependencies
            if dep.extension_id != extension_id and dep.dependency_id != extension_id
        ]
        
        return True
    
    def get_extension(self, extension_id: str) -> Optional[ExtensionInfo]:
        """获取扩展信息
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            Optional[ExtensionInfo]: 扩展信息
        """
        return self.extensions.get(extension_id)
    
    def list_extensions(self, 
                       status: Optional[str] = None,
                       extension_type: Optional[str] = None,
                       tags: Optional[List[str]] = None) -> List[ExtensionInfo]:
        """列出扩展
        
        Args:
            status: 状态过滤
            extension_type: 类型过滤
            tags: 标签过滤
            
        Returns:
            List[ExtensionInfo]: 扩展列表
        """
        extensions = list(self.extensions.values())
        
        # 状态过滤
        if status:
            extensions = [ext for ext in extensions if ext.status == status]
        
        # 类型过滤
        if extension_type:
            extensions = [ext for ext in extensions if ext.extension_type == extension_type]
        
        # 标签过滤
        if tags:
            extensions = [
                ext for ext in extensions
                if all(tag in ext.tags for tag in tags)
            ]
        
        return extensions
    
    def find_extensions_by_tag(self, tag: str) -> List[ExtensionInfo]:
        """根据标签查找扩展
        
        Args:
            tag: 标签
            
        Returns:
            List[ExtensionInfo]: 扩展列表
        """
        if tag not in self.tags_index:
            return []
        
        return [
            self.extensions[ext_id] 
            for ext_id in self.tags_index[tag]
            if ext_id in self.extensions
        ]
    
    def get_popular_tags(self, limit: int = 10) -> List[tuple]:
        """获取热门标签
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[tuple]: 标签和使用次数的列表
        """
        tag_counts = [
            (tag, len(ext_ids)) 
            for tag, ext_ids in self.tags_index.items()
        ]
        
        tag_counts.sort(key=lambda x: x[1], reverse=True)
        return tag_counts[:limit]
    
    def add_dependency(self, dependency: ExtensionDependency) -> None:
        """添加依赖关系
        
        Args:
            dependency: 依赖关系
        """
        # 检查是否已存在
        for existing in self.dependencies:
            if (existing.extension_id == dependency.extension_id and
                existing.dependency_id == dependency.dependency_id):
                return
        
        self.dependencies.append(dependency)
    
    def remove_dependency(self, extension_id: str, dependency_id: str) -> bool:
        """移除依赖关系
        
        Args:
            extension_id: 扩展ID
            dependency_id: 依赖ID
            
        Returns:
            bool: 是否成功移除
        """
        original_length = len(self.dependencies)
        self.dependencies = [
            dep for dep in self.dependencies
            if not (dep.extension_id == extension_id and dep.dependency_id == dependency_id)
        ]
        
        return len(self.dependencies) < original_length
    
    def get_dependencies(self, extension_id: str) -> List[ExtensionDependency]:
        """获取扩展的依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[ExtensionDependency]: 依赖列表
        """
        return [
            dep for dep in self.dependencies
            if dep.extension_id == extension_id
        ]
    
    def get_dependents(self, extension_id: str) -> List[ExtensionDependency]:
        """获取依赖此扩展的其他扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[ExtensionDependency]: 依赖此扩展的列表
        """
        return [
            dep for dep in self.dependencies
            if dep.dependency_id == extension_id
        ]
    
    def resolve_load_order(self, extension_ids: List[str]) -> List[str]:
        """解析扩展加载顺序
        
        使用拓扑排序解析扩展的依赖关系，确定正确的加载顺序。
        
        Args:
            extension_ids: 扩展ID列表
            
        Returns:
            List[str]: 排序后的扩展ID列表
        """
        # 构建依赖图
        graph = {}
        in_degree = {}
        
        for ext_id in extension_ids:
            graph[ext_id] = []
            in_degree[ext_id] = 0
        
        # 添加依赖边
        for ext_id in extension_ids:
            dependencies = self.get_dependencies(ext_id)
            for dep in dependencies:
                if dep.dependency_id in graph:
                    graph[dep.dependency_id].append(ext_id)
                    in_degree[ext_id] += 1
        
        # 拓扑排序
        queue = [ext_id for ext_id in extension_ids if in_degree[ext_id] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环依赖
        if len(result) != len(extension_ids):
            raise ValueError("检测到循环依赖")
        
        return result
    
    def validate_dependencies(self, extension_id: str) -> List[str]:
        """验证扩展依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 缺失的依赖列表
        """
        missing_deps = []
        dependencies = self.get_dependencies(extension_id)
        
        for dep in dependencies:
            if dep.dependency_type == "required" and dep.dependency_id not in self.extensions:
                missing_deps.append(dep.dependency_id)
        
        return missing_deps
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        status_counts = {}
        type_counts = {}
        
        for ext in self.extensions.values():
            # 状态统计
            status_counts[ext.status] = status_counts.get(ext.status, 0) + 1
            # 类型统计
            type_counts[ext.extension_type] = type_counts.get(ext.extension_type, 0) + 1
        
        return {
            "total_extensions": len(self.extensions),
            "total_dependencies": len(self.dependencies),
            "status_counts": status_counts,
            "type_counts": type_counts,
            "total_tags": len(self.tags_index),
            "popular_tags": self.get_popular_tags(5)
        }
    
    def export_registry(self) -> Dict[str, Any]:
        """导出注册表
        
        Returns:
            Dict[str, Any]: 注册表的完整数据
        """
        return {
            "extensions": {
                ext_id: ext.to_dict() 
                for ext_id, ext in self.extensions.items()
            },
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "categories": self.categories,
            "tags_index": {
                tag: list(ext_ids) 
                for tag, ext_ids in self.tags_index.items()
            }
        }
    
    def import_registry(self, data: Dict[str, Any]) -> None:
        """导入注册表
        
        Args:
            data: 注册表数据
        """
        # 清空现有数据
        self.extensions.clear()
        self.dependencies.clear()
        self.categories.clear()
        self.tags_index.clear()
        
        # 导入扩展
        for ext_id, ext_data in data.get("extensions", {}).items():
            extension_info = ExtensionInfo.from_dict(ext_data)
            self.register_extension(extension_info)
        
        # 导入依赖关系
        for dep_data in data.get("dependencies", []):
            dependency = ExtensionDependency.from_dict(dep_data)
            self.add_dependency(dependency)
        
        # 导入分类
        self.categories.update(data.get("categories", {}))
        
        # 导入标签索引
        for tag, ext_ids in data.get("tags_index", {}).items():
            self.tags_index[tag] = set(ext_ids)
    
    def save_to_file(self, file_path: str) -> None:
        """保存到文件
        
        Args:
            file_path: 文件路径
        """
        data = self.export_registry()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: str) -> None:
        """从文件加载
        
        Args:
            file_path: 文件路径
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.import_registry(data)