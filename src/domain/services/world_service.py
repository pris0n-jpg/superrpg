"""
世界领域服务

提供世界相关的业务逻辑和操作，协调世界聚合根与其他领域对象的交互。
遵循单一职责原则，专门负责世界相关的业务服务。
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime

from ..models.world import World, Location, Scene, GameTime, Weather, LocationType
from ..models.characters import Character, Position
from ..models.items import Item
from ..models.combat import Combat
from ..models.objectives import Objective, ObjectiveStatus
from ..models.relations import Relation, RelationType
from ...core.exceptions import BusinessRuleException, ValidationException


class WorldService:
    """世界领域服务
    
    提供世界相关的业务逻辑和操作，包括：
    - 世界创建和管理
    - 时间和天气管理
    - 场景和地点管理
    - 全局事件处理
    - 世界状态管理
    """
    
    def __init__(self):
        """初始化世界服务"""
        pass
    
    def create_world(self, game_config: Dict[str, Any]) -> World:
        """创建新世界
        
        Args:
            game_config: 游戏配置字典
            
        Returns:
            World: 创建的世界对象
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        # 从配置中提取世界名称和初始地点
        world_name = game_config.get("name", "默认世界")
        initial_location = game_config.get("initial_location", "起始地点")
        
        # 验证输入
        if not world_name or not str(world_name).strip():
            raise ValidationException("世界名称不能为空")
        
        if not initial_location or not str(initial_location).strip():
            raise ValidationException("初始地点名称不能为空")
        
        # 创建初始地点
        location = Location(name=str(initial_location).strip())
        
        # 创建初始场景
        scene = Scene(
            location=location,
            weather=Weather.CLEAR,
            atmosphere="平静",
            tension_level=1
        )
        
        # 创建世界
        world = World(name=str(world_name).strip(), current_scene=scene)
        world.locations[location.name] = location
        
        return world
    
    def advance_time(self, world: World, minutes: int) -> bool:
        """推进世界时间
        
        Args:
            world: 世界对象
            minutes: 推进的分钟数
            
        Returns:
            bool: 是否成功推进
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        if minutes <= 0:
            raise ValidationException("推进时间必须大于0")
        
        # 推进时间
        world.advance_time(minutes)
        
        return True
    
    def set_time(self, world: World, day: int, hour: int, minute: int = 0) -> bool:
        """设置世界时间
        
        Args:
            world: 世界对象
            day: 天数
            hour: 小时 (0-23)
            minute: 分钟 (0-59)
            
        Returns:
            bool: 是否成功设置
            
        Raises:
            ValidationException: 验证失败时抛出
        """
        if day < 1:
            raise ValidationException("天数必须大于0")
        
        if hour < 0 or hour > 23:
            raise ValidationException("小时必须在0-23之间")
        
        if minute < 0 or minute > 59:
            raise ValidationException("分钟必须在0-59之间")
        
        # 设置新时间
        old_time = world.current_time
        world.current_time = GameTime(day=day, hour=hour, minute=minute)
        
        # 处理到期事件
        world._process_due_events()
        
        return True
    
    def change_weather(self, world: World, new_weather: Weather) -> bool:
        """改变世界天气
        
        Args:
            world: 世界对象
            new_weather: 新天气
            
        Returns:
            bool: 是否成功改变
        """
        if not world.current_scene:
            return False
        
        # 创建新场景
        new_scene = Scene(
            location=world.current_scene.location,
            weather=new_weather,
            atmosphere=world.current_scene.atmosphere,
            details=world.current_scene.details,
            background_events=world.current_scene.background_events,
            tension_level=world.current_scene.tension_level
        )
        
        world.set_scene(new_scene)
        return True
    
    def add_location(self, world: World, location: Location, parent_location: Optional[str] = None) -> bool:
        """添加地点到世界
        
        Args:
            world: 世界对象
            location: 地点对象
            parent_location: 父地点名称
            
        Returns:
            bool: 是否成功添加
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证地点名称唯一性
        if location.name in world.locations:
            raise BusinessRuleException(f"地点 {location.name} 已存在")
        
        # 验证父地点存在
        if parent_location and parent_location not in world.locations:
            raise BusinessRuleException(f"父地点 {parent_location} 不存在")
        
        # 如果有父地点，更新父子关系
        if parent_location:
            # 创建新的地点对象，包含父地点信息
            location_with_parent = Location(
                name=location.name,
                description=location.description,
                location_type=location.location_type,
                coordinates=location.coordinates,
                parent_location=parent_location,
                child_locations=location.child_locations,
                properties=location.properties
            )
            world.add_location(location_with_parent)
            
            # 更新父地点的子地点列表
            parent = world.locations[parent_location]
            if location.name not in parent.child_locations:
                new_parent = Location(
                    name=parent.name,
                    description=parent.description,
                    location_type=parent.location_type,
                    coordinates=parent.coordinates,
                    parent_location=parent.parent_location,
                    child_locations=parent.child_locations + [location.name],
                    properties=parent.properties
                )
                world.locations[parent_location] = new_parent
        else:
            world.add_location(location)
        
        return True
    
    def remove_location(self, world: World, location_name: str) -> bool:
        """从世界中移除地点
        
        Args:
            world: 世界对象
            location_name: 地点名称
            
        Returns:
            bool: 是否成功移除
        """
        return world.remove_location(location_name)
    
    def travel_to_location(self, world: World, location_name: str, travel_time: int = 0) -> bool:
        """旅行到指定地点
        
        Args:
            world: 世界对象
            location_name: 目标地点名称
            travel_time: 旅行时间（分钟）
            
        Returns:
            bool: 是否成功旅行
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 检查目标地点是否存在
        if location_name not in world.locations:
            raise BusinessRuleException(f"目标地点 {location_name} 不存在")
        
        # 推进旅行时间
        if travel_time > 0:
            self.advance_time(world, travel_time)
        
        # 创建新场景
        target_location = world.locations[location_name]
        new_scene = Scene(
            location=target_location,
            weather=world.current_scene.weather if world.current_scene else Weather.CLEAR,
            atmosphere=world.current_scene.atmosphere if world.current_scene else "平静",
            details=world.current_scene.details if world.current_scene else [],
            background_events=world.current_scene.background_events if world.current_scene else [],
            tension_level=world.current_scene.tension_level if world.current_scene else 1
        )
        
        world.set_scene(new_scene)
        return True
    
    def add_character_to_world(self, world: World, character: Character) -> bool:
        """添加角色到世界
        
        Args:
            world: 世界对象
            character: 角色对象
            
        Returns:
            bool: 是否成功添加
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        # 检查角色名称唯一性
        if character.name in world.characters:
            raise BusinessRuleException(f"角色 {character.name} 已存在")
        
        world.add_character(character)
        return True
    
    def remove_character_from_world(self, world: World, character_name: str) -> bool:
        """从世界中移除角色
        
        Args:
            world: 世界对象
            character_name: 角色名称
            
        Returns:
            bool: 是否成功移除
        """
        return world.remove_character(character_name)
    
    def add_item_to_world(self, world: World, item: Item) -> bool:
        """添加物品到世界
        
        Args:
            world: 世界对象
            item: 物品对象
            
        Returns:
            bool: 是否成功添加
        """
        world.add_item(item)
        return True
    
    def remove_item_from_world(self, world: World, item_id: str) -> bool:
        """从世界中移除物品
        
        Args:
            world: 世界对象
            item_id: 物品ID
            
        Returns:
            bool: 是否成功移除
        """
        return world.remove_item(item_id)
    
    def start_combat_in_world(self, world: World, location: str, participants: List[str]) -> bool:
        """在世界中开始战斗
        
        Args:
            world: 世界对象
            location: 战斗地点
            participants: 参与者列表
            
        Returns:
            bool: 是否成功开始
            
        Raises:
            BusinessRuleException: 业务规则违反时抛出
        """
        if world.is_in_combat:
            raise BusinessRuleException("世界已有活跃战斗")
        
        world.start_combat(location, participants)
        return True
    
    def end_combat_in_world(self, world: World) -> bool:
        """在世界中结束战斗
        
        Args:
            world: 世界对象
            
        Returns:
            bool: 是否成功结束
        """
        if not world.is_in_combat:
            return False
        
        world.end_combat()
        return True
    
    def add_global_event(self, world: World, event_data: Dict[str, Any], trigger_time: Optional[int] = None) -> bool:
        """添加全局事件
        
        Args:
            world: 世界对象
            event_data: 事件数据
            trigger_time: 触发时间（分钟），如果为None则立即触发
            
        Returns:
            bool: 是否成功添加
        """
        world.add_global_event(event_data, trigger_time)
        return True
    
    def update_scene_atmosphere(self, world: World, atmosphere: str) -> bool:
        """更新场景氛围
        
        Args:
            world: 世界对象
            atmosphere: 新氛围描述
            
        Returns:
            bool: 是否成功更新
        """
        if not world.current_scene:
            return False
        
        # 创建新场景
        new_scene = Scene(
            location=world.current_scene.location,
            weather=world.current_scene.weather,
            atmosphere=atmosphere,
            details=world.current_scene.details,
            background_events=world.current_scene.background_events,
            tension_level=world.current_scene.tension_level
        )
        
        world.set_scene(new_scene)
        return True
    
    def add_scene_detail(self, world: World, detail: str) -> bool:
        """添加场景细节
        
        Args:
            world: 世界对象
            detail: 细节描述
            
        Returns:
            bool: 是否成功添加
        """
        if not world.current_scene:
            return False
        
        # 添加细节到当前场景
        new_scene = world.current_scene.add_detail(detail)
        world.set_scene(new_scene)
        return True
    
    def adjust_scene_tension(self, world: World, delta: int) -> bool:
        """调整场景紧张等级
        
        Args:
            world: 世界对象
            delta: 调整值
            
        Returns:
            bool: 是否成功调整
        """
        if not world.current_scene:
            return False
        
        # 调整紧张等级
        new_scene = world.current_scene.adjust_tension(delta)
        world.set_scene(new_scene)
        return True
    
    def add_background_event(self, world: World, event: str) -> bool:
        """添加背景事件
        
        Args:
            world: 世界对象
            event: 背景事件描述
            
        Returns:
            bool: 是否成功添加
        """
        if not world.current_scene:
            return False
        
        # 添加背景事件到当前场景
        new_scene = world.current_scene.add_background_event(event)
        world.set_scene(new_scene)
        return True
    
    def get_world_status(self, world: World) -> Dict[str, Any]:
        """获取世界状态摘要
        
        Args:
            world: 世界对象
            
        Returns:
            Dict[str, Any]: 世界状态摘要
        """
        return world.get_world_snapshot()
    
    def get_characters_at_location(self, world: World, location_name: str) -> List[Character]:
        """获取指定地点的所有角色
        
        Args:
            world: 世界对象
            location_name: 地点名称
            
        Returns:
            List[Character]: 角色列表
        """
        characters = []
        
        for character in world.characters.values():
            # 这里需要根据角色的位置判断是否在指定地点
            # 简化实现，假设所有角色都在当前地点
            if world.current_scene and world.current_scene.location.name == location_name:
                characters.append(character)
        
        return characters
    
    def get_available_locations(self, world: World) -> List[Location]:
        """获取所有可用地点
        
        Args:
            world: 世界对象
            
        Returns:
            List[Location]: 地点列表
        """
        return list(world.locations.values())
    
    def get_travelable_locations(self, world: World, current_location: str) -> List[Location]:
        """获取可以从当前地点旅行到的地点
        
        Args:
            world: 世界对象
            current_location: 当前地点名称
            
        Returns:
            List[Location]: 可旅行地点列表
        """
        if current_location not in world.locations:
            return []
        
        # 获取当前地点
        location = world.locations[current_location]
        travelable = []
        
        # 简化实现，返回所有其他地点
        for loc_name, loc in world.locations.items():
            if loc_name != current_location:
                travelable.append(loc)
        
        return travelable
    
    def process_world_events(self, world: World) -> int:
        """处理世界事件
        
        Args:
            world: 世界对象
            
        Returns:
            int: 处理的事件数量
        """
        # 获取当前时间
        current_time = world.current_time.total_minutes
        
        # 处理到期事件
        triggered_count = 0
        for event in world.global_events:
            if not event["triggered"] and event["trigger_time"] <= current_time:
                event["triggered"] = True
                triggered_count += 1
                
                # 执行事件效果
                world._execute_event_effects(event["data"])
        
        return triggered_count
    
    def set_scene(
        self,
        world: World,
        name: str,
        objectives: Optional[List[str]] = None,
        details: Optional[Union[str, List[str]]] = None,
        time_min: Optional[int] = None,
        weather: Optional[str] = None
    ) -> bool:
        """设置场景
        
        该方法通过适配器调用world/tools.py中的set_scene函数，
        确保新旧架构之间的兼容性。
        
        Args:
            world: 世界对象
            name: 场景名称
            objectives: 目标列表
            details: 场景细节
            time_min: 时间（分钟）
            weather: 天气
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 导入world/tools模块
            from src.world.tools import set_scene as tools_set_scene
            
            # 调用tools模块的set_scene函数
            result = tools_set_scene(
                location=name,
                objectives=objectives,
                details=details,
                time_min=time_min,
                weather=weather
            )
            
            return True
            
        except Exception as e:
            # 记录错误但不抛出异常，保持兼容性
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"设置场景失败: {e}")
            return False
    
    def set_relation(
        self,
        world: World,
        source: str,
        target: str,
        score: int,
        reason: str = "配置设定"
    ) -> bool:
        """设置关系
        
        Args:
            world: 世界对象
            source: 源角色
            target: 目标角色
            score: 关系分数
            reason: 原因
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 导入world/tools模块
            from src.world.tools import set_relation as tools_set_relation
            
            # 调用tools模块的set_relation函数
            result = tools_set_relation(source, target, score, reason)
            
            return True
            
        except Exception as e:
            # 记录错误但不抛出异常，保持兼容性
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"设置关系失败: {e}")
            return False
    
    def set_position(
        self,
        world: World,
        character_name: str,
        x: int,
        y: int
    ) -> bool:
        """设置角色位置
        
        Args:
            world: 世界对象
            character_name: 角色名称
            x: X坐标
            y: Y坐标
            
        Returns:
            bool: 是否成功设置
        """
        try:
            # 导入world/tools模块
            from src.world.tools import set_position as tools_set_position
            
            # 调用tools模块的set_position函数
            result = tools_set_position(character_name, x, y)
            
            return True
            
        except Exception as e:
            # 记录错误但不抛出异常，保持兼容性
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"设置位置失败: {e}")
            return False
    
    def end_combat(self, world: World) -> bool:
        """结束战斗
        
        Args:
            world: 世界对象
            
        Returns:
            bool: 是否成功结束
        """
        return self.end_combat_in_world(world)
    
    def get_current_world(self) -> Optional[World]:
        """获取当前世界对象
        
        Returns:
            Optional[World]: 当前世界对象，如果不存在则返回None
        """
        # 注意：这个方法需要在应用层实现，因为WorldService本身不存储世界状态
        # 这里返回None，实际实现应该由GameEngineService或其他管理器提供
        return None