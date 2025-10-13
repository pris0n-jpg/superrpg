"""
工具适配器模块

该模块实现工具适配器，将现有的actions/npc.py适配到新的工具系统。
遵循适配器模式，确保新旧架构之间的兼容性。

工具适配器负责：
1. 封装现有的make_npc_actions函数
2. 提供与新架构一致的工具接口
3. 处理工具注册和分发
4. 支持渐进式迁移
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
import logging

# 导入现有的工具工厂
try:
    from ..actions.npc import make_npc_actions
except ImportError:
    # 如果新架构中不存在，从旧路径导入
    from actions.npc import make_npc_actions

# 导入新架构的接口
try:
    from ..core.interfaces import ToolExecutor, ToolRegistry
except ImportError:
    # 如果新架构接口不存在，定义基本接口
    class ToolExecutor:
        def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
            pass
    
    class ToolRegistry:
        def register_tool(self, name: str, tool_func: Callable) -> None:
            pass


class ToolsAdapter:
    """工具适配器类
    
    该类作为现有actions/npc.py与新架构之间的适配器，
    提供统一的工具管理接口，同时保持向后兼容性。
    """
    
    def __init__(self, enable_legacy_mode: bool = True):
        """初始化工具适配器
        
        Args:
            enable_legacy_mode: 是否启用遗留模式支持
        """
        self.enable_legacy_mode = enable_legacy_mode
        self._tool_list: List[object] = []
        self._tool_dispatch: Dict[str, object] = {}
        self._tool_registry: Dict[str, Callable] = {}
        self._world_adapter = None
        self._logger = logging.getLogger(__name__)
    
    def initialize_tools(self, world_adapter=None) -> Tuple[List[object], Dict[str, object]]:
        """初始化工具
        
        该方法封装了原有的make_npc_actions函数，提供统一的工具初始化接口。
        
        Args:
            world_adapter: 世界适配器实例
            
        Returns:
            Tuple[List[object], Dict[str, object]]: 工具列表和工具分发字典
        """
        try:
            self._world_adapter = world_adapter
            
            # 使用原有的make_npc_actions函数
            if world_adapter:
                tool_list, tool_dispatch = make_npc_actions(world=world_adapter.get_legacy_world())
            else:
                # 如果没有提供世界适配器，尝试使用原始world
                try:
                    import world.tools as world_impl
                except ImportError:
                    from ..world import tools as world_impl
                tool_list, tool_dispatch = make_npc_actions(world=world_impl)
            
            # 缓存工具信息
            self._tool_list = tool_list
            self._tool_dispatch = tool_dispatch
            
            # 注册到新架构的工具注册表
            self._register_tools_to_new_registry()
            
            self._logger.info(f"工具初始化完成，共加载 {len(tool_list)} 个工具")
            
            return tool_list, tool_dispatch
            
        except Exception as e:
            error_msg = f"工具初始化失败: {str(e)}"
            if self.enable_legacy_mode:
                error_msg += " (使用遗留模式)"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_tool_list(self) -> List[object]:
        """获取工具列表
        
        Returns:
            List[object]: 工具列表
        """
        return self._tool_list.copy()
    
    def get_tool_dispatch(self) -> Dict[str, object]:
        """获取工具分发字典
        
        Returns:
            Dict[str, object]: 工具分发字典
        """
        return self._tool_dispatch.copy()
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            Any: 工具执行结果
            
        Raises:
            ValueError: 当工具不存在或执行失败时
        """
        try:
            # 从工具分发字典中获取工具函数
            tool_func = self._tool_dispatch.get(tool_name)
            if not tool_func:
                raise ValueError(f"未知工具: {tool_name}")
            
            # 执行工具
            result = tool_func(**params)
            
            self._logger.debug(f"工具执行成功: {tool_name}, 参数: {params}")
            return result
            
        except Exception as e:
            error_msg = f"工具执行失败: {tool_name}, 错误: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def register_custom_tool(self, name: str, tool_func: Callable) -> None:
        """注册自定义工具
        
        Args:
            name: 工具名称
            tool_func: 工具函数
        """
        self._tool_registry[name] = tool_func
        self._tool_dispatch[name] = tool_func
        self._tool_list.append(tool_func)
        
        self._logger.info(f"自定义工具注册成功: {name}")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 是否成功注销
        """
        if tool_name in self._tool_dispatch:
            del self._tool_dispatch[tool_name]
            
            # 从工具列表中移除
            self._tool_list = [
                tool for tool in self._tool_list 
                if tool != self._tool_dispatch.get(tool_name)
            ]
            
            # 从注册表中移除
            if tool_name in self._tool_registry:
                del self._tool_registry[tool_name]
            
            self._logger.info(f"工具注销成功: {tool_name}")
            return True
        
        return False
    
    def get_tool_info(self) -> Dict[str, Any]:
        """获取工具信息
        
        Returns:
            Dict[str, Any]: 工具信息统计
        """
        return {
            "total_tools": len(self._tool_list),
            "dispatch_tools": len(self._tool_dispatch),
            "custom_tools": len(self._tool_registry),
            "tool_names": list(self._tool_dispatch.keys()),
            "custom_tool_names": list(self._tool_registry.keys())
        }
    
    def validate_tool_params(self, tool_name: str, params: Dict[str, Any]) -> List[str]:
        """验证工具参数
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查工具是否存在
        if tool_name not in self._tool_dispatch:
            errors.append(f"未知工具: {tool_name}")
            return errors
        
        # 基本参数验证
        if not isinstance(params, dict):
            errors.append("参数必须是字典类型")
            return errors
        
        # 可以在这里添加特定工具的参数验证逻辑
        # 目前只做基本验证
        
        return errors
    
    def _register_tools_to_new_registry(self) -> None:
        """将工具注册到新架构的注册表"""
        try:
            # 尝试获取新架构的工具注册表
            from ..core.container import ServiceLocator
            from ..core.interfaces import ToolRegistry
            
            if ServiceLocator.is_registered(ToolRegistry):
                registry = ServiceLocator.resolve(ToolRegistry)
                
                # 注册所有工具到新架构
                for tool_name, tool_func in self._tool_dispatch.items():
                    registry.register_tool(tool_name, tool_func)
                
                self._logger.info("工具已注册到新架构的注册表")
        except ImportError:
            # 新架构接口不存在，跳过注册
            self._logger.debug("新架构接口不存在，跳过工具注册")
        except Exception as e:
            self._logger.warning(f"工具注册到新架构失败: {str(e)}")


# 创建默认的工具适配器实例
default_tools_adapter = ToolsAdapter()


def create_tools_adapter(enable_legacy_mode: bool = True) -> ToolsAdapter:
    """创建工具适配器实例
    
    Args:
        enable_legacy_mode: 是否启用遗留模式支持
        
    Returns:
        ToolsAdapter: 工具适配器实例
    """
    return ToolsAdapter(enable_legacy_mode=enable_legacy_mode)


# 便捷函数，保持向后兼容
def make_npc_tools(world_adapter=None) -> Tuple[List[object], Dict[str, object]]:
    """创建NPC工具的便捷函数
    
    该函数提供与原有make_npc_actions函数相同的接口，
    但通过适配器实现，支持新架构的特性。
    
    Args:
        world_adapter: 世界适配器实例
        
    Returns:
        Tuple[List[object], Dict[str, object]]: 工具列表和工具分发字典
    """
    return default_tools_adapter.initialize_tools(world_adapter)


# 工具执行器实现
class AdapterToolExecutor(ToolExecutor):
    """适配器工具执行器
    
    该类实现了新架构的工具执行器接口，
    通过工具适配器执行工具。
    """
    
    def __init__(self, tools_adapter: ToolsAdapter = None):
        """初始化工具执行器
        
        Args:
            tools_adapter: 工具适配器实例
        """
        self.tools_adapter = tools_adapter or default_tools_adapter
    
    def execute(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            Any: 工具执行结果
        """
        return self.tools_adapter.execute_tool(tool_name, params)