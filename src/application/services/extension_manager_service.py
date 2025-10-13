"""
扩展管理器服务模块

该模块实现扩展管理器，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责扩展的生命周期管理。
"""

import asyncio
import importlib
import sys
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Type, Set
from collections import defaultdict

from ...core.interfaces import (
    Extension, ExtensionMetadata, ExtensionContext, ExtensionStatus,
    ExtensionType, ExtensionRegistry, ExtensionManager, ExtensionLoader,
    ExtensionEvent, ExtensionEventHandler
)
from ...core.exceptions import (
    DomainException, InfrastructureException, 
    NotFoundException, ValidationException
)


class ExtensionLoadException(InfrastructureException):
    """扩展加载异常
    
    当扩展加载失败时抛出此异常。
    """
    
    def __init__(self, message: str, extension_name: str, cause: Optional[Exception] = None):
        super().__init__(message, "EXTENSION_LOAD_ERROR", component="ExtensionManager")
        self.extension_name = extension_name
        self.cause = cause


class ExtensionDependencyException(DomainException):
    """扩展依赖异常
    
    当扩展依赖解析失败时抛出此异常。
    """
    
    def __init__(self, message: str, extension_name: str, missing_dependencies: List[str]):
        super().__init__(message, "EXTENSION_DEPENDENCY_ERROR")
        self.extension_name = extension_name
        self.missing_dependencies = missing_dependencies


class ExtensionRegistryImpl(ExtensionRegistry):
    """扩展注册表实现
    
    实现扩展注册表接口，负责扩展的注册和发现。
    """
    
    def __init__(self):
        """初始化扩展注册表"""
        self._extensions: Dict[str, Extension] = {}
        self._extensions_by_type: Dict[ExtensionType, List[Extension]] = defaultdict(list)
        self._extensions_by_status: Dict[ExtensionStatus, List[Extension]] = defaultdict(list)
        self._extensions_by_tag: Dict[str, List[Extension]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def register_extension(self, extension: Extension) -> bool:
        """注册扩展
        
        Args:
            extension: 扩展实例
            
        Returns:
            bool: 是否成功注册
        """
        async with self._lock:
            extension_id = f"{extension.metadata.name}:{extension.metadata.version}"
            
            if extension_id in self._extensions:
                return False
            
            self._extensions[extension_id] = extension
            
            # 按类型索引
            self._extensions_by_type[extension.metadata.extension_type].append(extension)
            
            # 按状态索引
            self._extensions_by_status[extension.status].append(extension)
            
            # 按标签索引
            for tag in extension.metadata.tags:
                self._extensions_by_tag[tag].append(extension)
            
            return True
    
    async def unregister_extension(self, extension_id: str) -> bool:
        """注销扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功注销
        """
        async with self._lock:
            if extension_id not in self._extensions:
                return False
            
            extension = self._extensions[extension_id]
            
            # 从所有索引中移除
            del self._extensions[extension_id]
            
            self._extensions_by_type[extension.metadata.extension_type].remove(extension)
            self._extensions_by_status[extension.status].remove(extension)
            
            for tag in extension.metadata.tags:
                if tag in self._extensions_by_tag:
                    self._extensions_by_tag[tag].remove(extension)
            
            return True
    
    async def get_extension(self, extension_id: str) -> Optional[Extension]:
        """获取扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        return self._extensions.get(extension_id)
    
    async def list_extensions(self, 
                             extension_type: Optional[ExtensionType] = None,
                             status: Optional[ExtensionStatus] = None) -> List[Extension]:
        """列出扩展
        
        Args:
            extension_type: 扩展类型过滤
            status: 状态过滤
            
        Returns:
            List[Extension]: 扩展列表
        """
        if extension_type and status:
            # 同时按类型和状态过滤
            type_extensions = self._extensions_by_type.get(extension_type, [])
            status_extensions = self._extensions_by_status.get(status, [])
            return list(set(type_extensions) & set(status_extensions))
        elif extension_type:
            return self._extensions_by_type.get(extension_type, []).copy()
        elif status:
            return self._extensions_by_status.get(status, []).copy()
        else:
            return list(self._extensions.values())
    
    async def find_extensions_by_tag(self, tag: str) -> List[Extension]:
        """根据标签查找扩展
        
        Args:
            tag: 标签
            
        Returns:
            List[Extension]: 扩展列表
        """
        return self._extensions_by_tag.get(tag, []).copy()


class ExtensionLoaderImpl(ExtensionLoader):
    """扩展加载器实现
    
    实现扩展加载器接口，负责从文件系统加载扩展。
    """
    
    def __init__(self):
        """初始化扩展加载器"""
        self._loaded_modules: Dict[str, Any] = {}
    
    async def load_metadata(self, extension_path: str) -> Optional[ExtensionMetadata]:
        """加载扩展元数据
        
        Args:
            extension_path: 扩展路径
            
        Returns:
            Optional[ExtensionMetadata]: 扩展元数据
        """
        try:
            # 查找元数据文件
            metadata_file = self._find_metadata_file(extension_path)
            if not metadata_file:
                return None
            
            # 读取元数据
            with open(metadata_file, 'r', encoding='utf-8') as f:
                if metadata_file.endswith('.json'):
                    data = json.load(f)
                elif metadata_file.endswith(('.yaml', '.yml')):
                    data = yaml.safe_load(f)
                else:
                    return None
            
            # 转换为元数据对象
            return self._dict_to_metadata(data)
            
        except Exception as e:
            raise ExtensionLoadException(
                f"加载扩展元数据失败: {str(e)}",
                extension_path,
                e
            )
    
    async def load_extension(self, 
                           metadata: ExtensionMetadata, 
                           extension_path: str) -> Optional[Extension]:
        """加载扩展
        
        Args:
            metadata: 扩展元数据
            extension_path: 扩展路径
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        try:
            # 确定入口点
            entry_point = metadata.entry_point or "main"
            
            # 构建模块路径
            module_path = self._build_module_path(extension_path, entry_point)
            
            # 加载模块
            if module_path not in self._loaded_modules:
                module = importlib.import_module(module_path)
                self._loaded_modules[module_path] = module
            else:
                module = self._loaded_modules[module_path]
            
            # 查找扩展类
            extension_class = self._find_extension_class(module)
            if not extension_class:
                raise ExtensionLoadException(
                    f"在模块 {module_path} 中未找到扩展类",
                    metadata.name
                )
            
            # 创建扩展实例
            extension = extension_class(metadata)
            
            return extension
            
        except Exception as e:
            raise ExtensionLoadException(
                f"加载扩展失败: {str(e)}",
                metadata.name,
                e
            )
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的扩展格式
        
        Returns:
            List[str]: 支持的扩展格式列表
        """
        return [".py"]
    
    def _find_metadata_file(self, extension_path: str) -> Optional[str]:
        """查找元数据文件
        
        Args:
            extension_path: 扩展路径
            
        Returns:
            Optional[str]: 元数据文件路径
        """
        base_path = Path(extension_path)
        
        # 查找可能的元数据文件
        metadata_files = [
            "extension.json",
            "extension.yaml",
            "extension.yml",
            "metadata.json",
            "metadata.yaml",
            "metadata.yml"
        ]
        
        for filename in metadata_files:
            file_path = base_path / filename
            if file_path.exists():
                return str(file_path)
        
        return None
    
    def _dict_to_metadata(self, data: Dict[str, Any]) -> ExtensionMetadata:
        """将字典转换为元数据对象
        
        Args:
            data: 字典数据
            
        Returns:
            ExtensionMetadata: 元数据对象
        """
        return ExtensionMetadata(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            extension_type=ExtensionType(data.get("extension_type", "utility")),
            dependencies=data.get("dependencies", []),
            optional_dependencies=data.get("optional_dependencies", []),
            min_system_version=data.get("min_system_version", "1.0.0"),
            max_system_version=data.get("max_system_version"),
            tags=data.get("tags", []),
            homepage=data.get("homepage"),
            license=data.get("license"),
            entry_point=data.get("entry_point")
        )
    
    def _build_module_path(self, extension_path: str, entry_point: str) -> str:
        """构建模块路径
        
        Args:
            extension_path: 扩展路径
            entry_point: 入口点
            
        Returns:
            str: 模块路径
        """
        # 将文件路径转换为Python模块路径
        path = Path(extension_path)
        
        # 添加到Python路径（如果不在路径中）
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))
        
        # 构建模块路径
        if entry_point.endswith('.py'):
            entry_point = entry_point[:-3]
        
        return f"{path.name}.{entry_point}"
    
    def _find_extension_class(self, module: Any) -> Optional[Type[Extension]]:
        """查找扩展类
        
        Args:
            module: 模块对象
            
        Returns:
            Optional[Type[Extension]]: 扩展类
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # 检查是否是扩展类的子类
            if (isinstance(attr, type) and 
                issubclass(attr, Extension) and 
                attr != Extension):
                return attr
        
        return None


class ExtensionManagerImpl(ExtensionManager):
    """扩展管理器实现
    
    实现扩展管理器接口，负责扩展的完整生命周期管理。
    """
    
    def __init__(self, 
                 registry: ExtensionRegistry,
                 loader: ExtensionLoader,
                 container: Any,
                 event_bus: Any,
                 logger: Any,
                 extensions_dir: str = "extensions"):
        """初始化扩展管理器
        
        Args:
            registry: 扩展注册表
            loader: 扩展加载器
            container: 依赖注入容器
            event_bus: 事件总线
            logger: 日志记录器
            extensions_dir: 扩展目录
        """
        self.registry = registry
        self.loader = loader
        self.container = container
        self.event_bus = event_bus
        self.logger = logger
        self.extensions_dir = extensions_dir
        
        # 扩展上下文缓存
        self._contexts: Dict[str, ExtensionContext] = {}
        
        # 依赖图
        self._dependency_graph: Dict[str, List[str]] = {}
    
    async def load_extension(self, extension_path: str) -> Optional[Extension]:
        """加载扩展
        
        Args:
            extension_path: 扩展路径
            
        Returns:
            Optional[Extension]: 扩展实例
        """
        try:
            # 加载元数据
            metadata = await self.loader.load_metadata(extension_path)
            if not metadata:
                self.logger.error(f"无法加载扩展元数据: {extension_path}")
                return None
            
            extension_id = f"{metadata.name}:{metadata.version}"
            
            # 检查是否已加载
            existing = await self.registry.get_extension(extension_id)
            if existing:
                self.logger.warning(f"扩展已存在: {extension_id}")
                return existing
            
            # 检查依赖
            await self._check_dependencies(metadata)
            
            # 加载扩展
            extension = await self.loader.load_extension(metadata, extension_path)
            if not extension:
                self.logger.error(f"无法加载扩展: {extension_path}")
                return None
            
            # 创建扩展上下文
            context = self._create_extension_context(extension)
            self._contexts[extension_id] = context
            
            # 注册扩展
            await self.registry.register_extension(extension)
            
            # 初始化扩展
            extension.set_status(ExtensionStatus.INITIALIZING)
            await extension.initialize(context)
            extension.set_status(ExtensionStatus.LOADED)
            
            self.logger.info(f"扩展加载成功: {extension_id}")
            
            # 发布扩展加载事件
            await self._publish_event("extension_loaded", extension_id)
            
            return extension
            
        except Exception as e:
            self.logger.error(f"加载扩展失败: {extension_path}, 错误: {str(e)}")
            return None
    
    async def unload_extension(self, extension_id: str) -> bool:
        """卸载扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功卸载
        """
        try:
            extension = await self.registry.get_extension(extension_id)
            if not extension:
                return False
            
            # 停用扩展（如果处于活动状态）
            if extension.status == ExtensionStatus.ACTIVE:
                await self.deactivate_extension(extension_id)
            
            # 清理扩展
            extension.set_status(ExtensionStatus.DEACTIVATING)
            await extension.cleanup()
            extension.set_status(ExtensionStatus.UNLOADED)
            
            # 移除上下文
            if extension_id in self._contexts:
                del self._contexts[extension_id]
            
            # 注销扩展
            await self.registry.unregister_extension(extension_id)
            
            self.logger.info(f"扩展卸载成功: {extension_id}")
            
            # 发布扩展卸载事件
            await self._publish_event("extension_unloaded", extension_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"卸载扩展失败: {extension_id}, 错误: {str(e)}")
            return False
    
    async def activate_extension(self, extension_id: str) -> bool:
        """激活扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功激活
        """
        try:
            extension = await self.registry.get_extension(extension_id)
            if not extension:
                return False
            
            if extension.status != ExtensionStatus.LOADED:
                self.logger.warning(f"扩展状态不正确，无法激活: {extension_id}")
                return False
            
            # 激活依赖
            dependencies = await self.get_extension_dependencies(extension_id)
            for dep_id in dependencies:
                await self.activate_extension(dep_id)
            
            # 激活扩展
            extension.set_status(ExtensionStatus.ACTIVE)
            await extension.activate()
            
            self.logger.info(f"扩展激活成功: {extension_id}")
            
            # 发布扩展激活事件
            await self._publish_event("extension_activated", extension_id)
            
            return True
            
        except Exception as e:
            extension.set_status(ExtensionStatus.ERROR, str(e))
            self.logger.error(f"激活扩展失败: {extension_id}, 错误: {str(e)}")
            return False
    
    async def deactivate_extension(self, extension_id: str) -> bool:
        """停用扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功停用
        """
        try:
            extension = await self.registry.get_extension(extension_id)
            if not extension:
                return False
            
            if extension.status != ExtensionStatus.ACTIVE:
                self.logger.warning(f"扩展状态不正确，无法停用: {extension_id}")
                return False
            
            # 停用依赖此扩展的其他扩展
            dependents = await self._find_dependents(extension_id)
            for dep_id in dependents:
                await self.deactivate_extension(dep_id)
            
            # 停用扩展
            extension.set_status(ExtensionStatus.DEACTIVATING)
            await extension.deactivate()
            extension.set_status(ExtensionStatus.INACTIVE)
            
            self.logger.info(f"扩展停用成功: {extension_id}")
            
            # 发布扩展停用事件
            await self._publish_event("extension_deactivated", extension_id)
            
            return True
            
        except Exception as e:
            extension.set_status(ExtensionStatus.ERROR, str(e))
            self.logger.error(f"停用扩展失败: {extension_id}, 错误: {str(e)}")
            return False
    
    async def reload_extension(self, extension_id: str) -> bool:
        """重新加载扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            bool: 是否成功重新加载
        """
        # 获取扩展路径
        extension = await self.registry.get_extension(extension_id)
        if not extension:
            return False
        
        # 假设扩展路径与名称相同
        extension_path = os.path.join(self.extensions_dir, extension.metadata.name)
        
        # 卸载并重新加载
        if await self.unload_extension(extension_id):
            new_extension = await self.load_extension(extension_path)
            return new_extension is not None
        
        return False
    
    async def get_extension_dependencies(self, extension_id: str) -> List[str]:
        """获取扩展依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 依赖列表
        """
        extension = await self.registry.get_extension(extension_id)
        if not extension:
            return []
        
        dependencies = []
        for dep_name in extension.metadata.dependencies:
            # 查找依赖的扩展
            deps = await self.registry.list_extensions()
            for dep in deps:
                if dep.metadata.name == dep_name:
                    dep_id = f"{dep.metadata.name}:{dep.metadata.version}"
                    dependencies.append(dep_id)
                    break
        
        return dependencies
    
    async def resolve_dependencies(self, extension_id: str) -> List[str]:
        """解析扩展依赖
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 解析后的依赖顺序
        """
        # 使用拓扑排序解析依赖顺序
        extension = await self.registry.get_extension(extension_id)
        if not extension:
            return []
        
        visited = set()
        result = []
        
        async def visit(ext_id: str):
            if ext_id in visited:
                return
            
            visited.add(ext_id)
            
            # 获取依赖
            deps = await self.get_extension_dependencies(ext_id)
            for dep_id in deps:
                await visit(dep_id)
            
            result.append(ext_id)
        
        await visit(extension_id)
        return result
    
    async def load_all_extensions(self) -> None:
        """加载所有扩展
        
        扫描扩展目录并加载所有找到的扩展。
        """
        if not os.path.exists(self.extensions_dir):
            self.logger.warning(f"扩展目录不存在: {self.extensions_dir}")
            return
        
        # 扫描扩展目录
        for item in os.listdir(self.extensions_dir):
            extension_path = os.path.join(self.extensions_dir, item)
            
            if os.path.isdir(extension_path):
                await self.load_extension(extension_path)
    
    async def _check_dependencies(self, metadata: ExtensionMetadata) -> None:
        """检查扩展依赖
        
        Args:
            metadata: 扩展元数据
            
        Raises:
            ExtensionDependencyException: 依赖检查失败
        """
        missing_dependencies = []
        
        for dep_name in metadata.dependencies:
            # 检查依赖是否存在
            found = False
            extensions = await self.registry.list_extensions()
            for ext in extensions:
                if ext.metadata.name == dep_name:
                    found = True
                    break
            
            if not found:
                missing_dependencies.append(dep_name)
        
        if missing_dependencies:
            raise ExtensionDependencyException(
                f"缺少依赖: {', '.join(missing_dependencies)}",
                metadata.name,
                missing_dependencies
            )
    
    def _create_extension_context(self, extension: Extension) -> ExtensionContext:
        """创建扩展上下文
        
        Args:
            extension: 扩展实例
            
        Returns:
            ExtensionContext: 扩展上下文
        """
        extension_id = f"{extension.metadata.name}:{extension.metadata.version}"
        
        # 创建扩展目录
        data_dir = os.path.join("data", "extensions", extension.metadata.name)
        temp_dir = os.path.join("temp", "extensions", extension.metadata.name)
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        return ExtensionContext(
            extension_id=extension_id,
            metadata=extension.metadata,
            config={},  # 这里可以从配置管理器加载配置
            container=self.container,
            event_bus=self.event_bus,
            logger=self.logger,
            data_dir=data_dir,
            temp_dir=temp_dir
        )
    
    async def _publish_event(self, event_type: str, extension_id: str) -> None:
        """发布扩展事件
        
        Args:
            event_type: 事件类型
            extension_id: 扩展ID
        """
        # 这里需要创建具体的事件类
        # 暂时使用事件总线发布简单事件
        if self.event_bus:
            try:
                # 创建简单事件对象
                event_data = {
                    "event_type": event_type,
                    "extension_id": extension_id,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                # 发布事件（具体实现取决于事件总线接口）
                if hasattr(self.event_bus, 'publish'):
                    await self.event_bus.publish(event_data)
            except Exception as e:
                self.logger.error(f"发布扩展事件失败: {str(e)}")
    
    async def _find_dependents(self, extension_id: str) -> List[str]:
        """查找依赖此扩展的其他扩展
        
        Args:
            extension_id: 扩展ID
            
        Returns:
            List[str]: 依赖此扩展的扩展ID列表
        """
        extension = await self.registry.get_extension(extension_id)
        if not extension:
            return []
        
        dependents = []
        extensions = await self.registry.list_extensions()
        
        for ext in extensions:
            if extension.metadata.name in ext.metadata.dependencies:
                dep_id = f"{ext.metadata.name}:{ext.metadata.version}"
                dependents.append(dep_id)
        
        return dependents