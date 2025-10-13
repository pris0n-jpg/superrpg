"""
世界适配器模块

该模块实现世界适配器，将现有的world/tools.py适配到新的领域服务。
遵循适配器模式，确保新旧架构之间的兼容性。

世界适配器负责：
1. 封装现有的world/tools.py功能
2. 提供与新架构一致的世界状态接口
3. 处理世界状态转换和持久化
4. 支持渐进式迁移
"""

from typing import Any, Dict, List, Optional, Tuple
import logging

# 导入现有的世界工具
try:
    import world.tools as world_impl
    WORLD_LEGACY = world_impl.WORLD
except ImportError:
    # 如果新架构中不存在，从相对路径导入
    from ..world import tools as world_impl
    WORLD_LEGACY = world_impl.WORLD

# 导入新架构的接口
try:
    from ..core.interfaces import WorldState, CharacterService, CombatService
except ImportError:
    # 如果新架构接口不存在，定义基本接口
    class WorldState:
        def get_snapshot(self) -> Dict[str, Any]:
            return {}
        
        def update_state(self, state: Dict[str, Any]) -> None:
            pass
    
    class CharacterService:
        def get_character(self, name: str) -> Optional[Dict[str, Any]]:
            return None
    
    class CombatService:
        def is_in_combat(self) -> bool:
            return False


class WorldAdapter:
    """世界适配器类
    
    该类作为现有world/tools.py与新架构之间的适配器，
    提供统一的世界状态管理接口，同时保持向后兼容性。
    """
    
    def __init__(self, enable_legacy_mode: bool = True):
        """初始化世界适配器
        
        Args:
            enable_legacy_mode: 是否启用遗留模式支持
        """
        self.enable_legacy_mode = enable_legacy_mode
        self._world = WORLD_LEGACY
        self._logger = logging.getLogger(__name__)
        self._state_cache: Optional[Dict[str, Any]] = None
        self._cache_valid = False
    
    def get_snapshot(self) -> Dict[str, Any]:
        """获取世界状态快照
        
        该方法提供与新架构一致的接口，返回当前世界状态的完整快照。
        
        Returns:
            Dict[str, Any]: 世界状态快照
        """
        try:
            # 使用现有的snapshot方法
            snapshot = self._world.snapshot()
            
            # 缓存快照以提高性能
            self._state_cache = snapshot
            self._cache_valid = True
            
            return snapshot
            
        except Exception as e:
            error_msg = f"获取世界状态快照失败: {str(e)}"
            self._logger.error(error_msg)
            if self.enable_legacy_mode:
                # 在遗留模式下返回空字典而不是抛出异常
                return {}
            raise RuntimeError(error_msg) from e
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """更新世界状态
        
        Args:
            state_updates: 状态更新字典
            
        Raises:
            ValueError: 当状态更新失败时
        """
        try:
            # 直接更新世界状态
            for key, value in state_updates.items():
                if hasattr(self._world, key):
                    setattr(self._world, key, value)
                else:
                    self._logger.warning(f"未知的世界状态字段: {key}")
            
            # 标记缓存无效
            self._cache_valid = False
            
            self._logger.debug(f"世界状态更新完成，更新字段: {list(state_updates.keys())}")
            
        except Exception as e:
            error_msg = f"世界状态更新失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def get_runtime_info(self) -> Dict[str, Any]:
        """获取运行时信息
        
        该方法提供与原有runtime()方法相同的功能，
        但返回标准化的格式。
        
        Returns:
            Dict[str, Any]: 运行时信息
        """
        try:
            # 使用现有的runtime方法
            runtime_info = self._world.runtime()
            
            # 标准化返回格式
            standardized_info = {
                "positions": dict(runtime_info.get("positions", {})),
                "in_combat": bool(runtime_info.get("in_combat", False)),
                "turn_state": dict(runtime_info.get("turn_state", {})),
                "round": int(runtime_info.get("round", 1)),
                "characters": dict(runtime_info.get("characters", {})),
                "location": str(runtime_info.get("location", "未知")),
                "time_min": int(runtime_info.get("time_min", 0)),
                "weather": str(runtime_info.get("weather", "晴天"))
            }
            
            return standardized_info
            
        except Exception as e:
            error_msg = f"获取运行时信息失败: {str(e)}"
            self._logger.error(error_msg)
            if self.enable_legacy_mode:
                # 在遗留模式下返回基本信息
                return {
                    "positions": {},
                    "in_combat": False,
                    "turn_state": {},
                    "round": 1,
                    "characters": {},
                    "location": "未知",
                    "time_min": 0,
                    "weather": "晴天"
                }
            raise RuntimeError(error_msg) from e
    
    def set_dnd_character(self, name: str, **kwargs) -> Any:
        """设置D&D角色
        
        Args:
            name: 角色名称
            **kwargs: 角色属性
            
        Returns:
            Any: 设置结果
        """
        try:
            return self._world.set_dnd_character(name, **kwargs)
        except Exception as e:
            error_msg = f"设置D&D角色失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def set_position(self, name: str, x: int, y: int) -> Any:
        """设置角色位置
        
        Args:
            name: 角色名称
            x: X坐标
            y: Y坐标
            
        Returns:
            Any: 设置结果
        """
        try:
            result = self._world.set_position(name, x, y)
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"设置位置失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def set_scene(self, location: str, **kwargs) -> Any:
        """设置场景
        
        Args:
            location: 场景位置
            **kwargs: 其他场景参数
            
        Returns:
            Any: 设置结果
        """
        try:
            result = self._world.set_scene(location, **kwargs)
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"设置场景失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def set_relation(self, a: str, b: str, value: int, reason: str = "") -> Any:
        """设置关系
        
        Args:
            a: 角色A
            b: 角色B
            value: 关系值
            reason: 原因
            
        Returns:
            Any: 设置结果
        """
        try:
            result = self._world.set_relation(a, b, value, reason)
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"设置关系失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def get_turn(self) -> Any:
        """获取当前回合信息
        
        Returns:
            Any: 回合信息
        """
        try:
            return self._world.get_turn()
        except Exception as e:
            error_msg = f"获取回合信息失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def reset_actor_turn(self, name: str) -> Any:
        """重置角色回合
        
        Args:
            name: 角色名称
            
        Returns:
            Any: 重置结果
        """
        try:
            result = self._world.reset_actor_turn(name)
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"重置角色回合失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def end_combat(self) -> Any:
        """结束战斗
        
        Returns:
            Any: 结束结果
        """
        try:
            result = self._world.end_combat()
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"结束战斗失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def set_dnd_character_from_config(self, name: str, dnd: Dict[str, Any]) -> Any:
        """从配置设置D&D角色
        
        Args:
            name: 角色名称
            dnd: D&D配置字典
            
        Returns:
            Any: 设置结果
        """
        try:
            result = self._world.set_dnd_character_from_config(name, dnd)
            self._cache_valid = False
            return result
        except Exception as e:
            error_msg = f"从配置设置D&D角色失败: {str(e)}"
            self._logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def get_legacy_world(self):
        """获取遗留世界对象
        
        该方法用于适配器内部，提供对原始世界对象的访问。
        
        Returns:
            遗留世界对象
        """
        return self._world
    
    def validate_state(self) -> List[str]:
        """验证世界状态
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        try:
            # 检查基本状态
            snapshot = self.get_snapshot()
            
            # 检查必需字段
            required_fields = ["characters", "positions", "relations"]
            for field in required_fields:
                if field not in snapshot:
                    errors.append(f"缺少必需的状态字段: {field}")
            
            # 检查角色状态一致性
            characters = snapshot.get("characters", {})
            positions = snapshot.get("positions", {})
            
            for char_name in characters:
                if char_name not in positions:
                    errors.append(f"角色 {char_name} 没有位置信息")
            
        except Exception as e:
            errors.append(f"状态验证过程中出错: {str(e)}")
        
        return errors
    
    def get_world_info(self) -> Dict[str, Any]:
        """获取世界信息统计
        
        Returns:
            Dict[str, Any]: 世界信息统计
        """
        try:
            snapshot = self.get_snapshot()
            runtime_info = self.get_runtime_info()
            
            return {
                "total_characters": len(snapshot.get("characters", {})),
                "total_positions": len(snapshot.get("positions", {})),
                "total_relations": len(snapshot.get("relations", {})),
                "total_objectives": len(snapshot.get("objectives", [])),
                "in_combat": runtime_info.get("in_combat", False),
                "current_round": runtime_info.get("round", 1),
                "current_location": runtime_info.get("location", "未知"),
                "current_time": runtime_info.get("time_min", 0),
                "weather": runtime_info.get("weather", "晴天"),
                "cache_valid": self._cache_valid
            }
        except Exception as e:
            self._logger.error(f"获取世界信息失败: {str(e)}")
            return {
                "error": str(e),
                "cache_valid": False
            }


# 创建默认的世界适配器实例
default_world_adapter = WorldAdapter()


def create_world_adapter(enable_legacy_mode: bool = True) -> WorldAdapter:
    """创建世界适配器实例
    
    Args:
        enable_legacy_mode: 是否启用遗留模式支持
        
    Returns:
        WorldAdapter: 世界适配器实例
    """
    return WorldAdapter(enable_legacy_mode=enable_legacy_mode)


# 世界状态实现
class AdapterWorldState(WorldState):
    """适配器世界状态实现
    
    该类实现了新架构的世界状态接口，
    通过世界适配器访问世界状态。
    """
    
    def __init__(self, world_adapter: WorldAdapter = None):
        """初始化世界状态
        
        Args:
            world_adapter: 世界适配器实例
        """
        self.world_adapter = world_adapter or default_world_adapter
    
    def get_snapshot(self) -> Dict[str, Any]:
        """获取状态快照"""
        return self.world_adapter.get_snapshot()
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """更新状态"""
        self.world_adapter.update_state(state)
    
    def get_runtime_info(self) -> Dict[str, Any]:
        """获取运行时信息"""
        return self.world_adapter.get_runtime_info()
    
    def validate_state(self) -> List[str]:
        """验证状态"""
        return self.world_adapter.validate_state()