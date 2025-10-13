"""
世界领域模型
包含世界的属性、状态和行为规则
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from datetime import datetime, time

from .base import Entity, ValueObject, AggregateRoot
from .characters import Character, Position
from .combat import Combat
from .relations import RelationshipNetwork
from .objectives import ObjectiveTracker
from .items import Item


class Weather(Enum):
    """天气枚举"""
    CLEAR = "clear"
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAINY = "rainy"
    STORMY = "stormy"
    SNOWY = "snowy"
    FOGGY = "foggy"
    WINDY = "windy"


class TimeOfDay(Enum):
    """时间段枚举"""
    DAWN = "dawn"        # 5:00-7:00
    MORNING = "morning"  # 7:00-12:00
    NOON = "noon"        # 12:00-14:00
    AFTERNOON = "afternoon"  # 14:00-18:00
    EVENING = "evening"  # 18:00-21:00
    DUSK = "dusk"        # 21:00-23:00
    NIGHT = "night"      # 23:00-5:00


class LocationType(Enum):
    """地点类型枚举"""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    DUNGEON = "dungeon"
    CITY = "city"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    WATER = "water"
    DESERT = "desert"
    SPECIAL = "special"


@dataclass(frozen=True)
class GameTime(ValueObject):
    """游戏时间值对象"""
    day: int = 1
    hour: int = 8
    minute: int = 0

    def __post_init__(self):
        """初始化后处理"""
        if self.day < 1:
            raise ValueError("天数必须大于0")
        if self.hour < 0 or self.hour > 23:
            raise ValueError("小时必须在0-23之间")
        if self.minute < 0 or self.minute > 59:
            raise ValueError("分钟必须在0-59之间")

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (self.day, self.hour, self.minute)

    @property
    def total_minutes(self) -> int:
        """获取总分钟数"""
        return (self.day - 1) * 24 * 60 + self.hour * 60 + self.minute

    @classmethod
    def from_total_minutes(cls, total_minutes: int) -> 'GameTime':
        """从总分钟数创建游戏时间"""
        total_minutes = max(0, total_minutes)
        day = total_minutes // (24 * 60) + 1
        remaining_minutes = total_minutes % (24 * 60)
        hour = remaining_minutes // 60
        minute = remaining_minutes % 60
        return cls(day=day, hour=hour, minute=minute)

    @property
    def time_of_day(self) -> TimeOfDay:
        """获取时间段"""
        if 5 <= self.hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= self.hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= self.hour < 14:
            return TimeOfDay.NOON
        elif 14 <= self.hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= self.hour < 21:
            return TimeOfDay.EVENING
        elif 21 <= self.hour < 23:
            return TimeOfDay.DUSK
        else:
            return TimeOfDay.NIGHT

    @property
    def time_string(self) -> str:
        """获取时间字符串"""
        return f"第{self.day}天 {self.hour:02d}:{self.minute:02d}"

    def advance(self, minutes: int) -> 'GameTime':
        """推进时间
        
        Args:
            minutes: 推进的分钟数
            
        Returns:
            GameTime: 新的时间对象
        """
        return GameTime.from_total_minutes(self.total_minutes + minutes)


@dataclass(frozen=True)
class Location(ValueObject):
    """地点值对象"""
    name: str
    description: str = ""
    location_type: LocationType = LocationType.OUTDOOR
    coordinates: Optional[Position] = None
    parent_location: Optional[str] = None
    child_locations: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            raise ValueError("地点名称不能为空")

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.name,
            self.description,
            self.location_type,
            self.coordinates,
            self.parent_location,
            tuple(sorted(self.child_locations)),
            tuple(sorted(self.properties.items()))
        )

    @property
    def is_indoor(self) -> bool:
        """是否为室内地点"""
        return self.location_type == LocationType.INDOOR

    @property
    def is_outdoor(self) -> bool:
        """是否为室外地点"""
        return self.location_type == LocationType.OUTDOOR

    def has_property(self, key: str) -> bool:
        """检查是否有指定属性"""
        return key in self.properties

    def get_property(self, key: str, default: Any = None) -> Any:
        """获取属性值"""
        return self.properties.get(key, default)


@dataclass(frozen=True)
class Scene(ValueObject):
    """场景值对象"""
    location: Location
    weather: Weather = Weather.CLEAR
    atmosphere: str = ""
    details: List[str] = field(default_factory=list)
    background_events: List[str] = field(default_factory=list)
    tension_level: int = 1  # 0-5

    def __post_init__(self):
        """初始化后处理"""
        if self.tension_level < 0 or self.tension_level > 5:
            raise ValueError("紧张等级必须在0-5之间")

    def _get_equality_components(self) -> tuple:
        """获取相等性比较的组件"""
        return (
            self.location,
            self.weather,
            self.atmosphere,
            tuple(sorted(self.details)),
            tuple(sorted(self.background_events)),
            self.tension_level
        )

    @property
    def location_name(self) -> str:
        """获取地点名称"""
        return self.location.name

    def add_detail(self, detail: str) -> 'Scene':
        """添加细节
        
        Args:
            detail: 细节描述
            
        Returns:
            Scene: 新的场景对象
        """
        new_details = self.details.copy()
        new_details.append(detail)
        return Scene(
            location=self.location,
            weather=self.weather,
            atmosphere=self.atmosphere,
            details=new_details,
            background_events=self.background_events,
            tension_level=self.tension_level
        )

    def add_background_event(self, event: str) -> 'Scene':
        """添加背景事件
        
        Args:
            event: 背景事件描述
            
        Returns:
            Scene: 新的场景对象
        """
        new_events = self.background_events.copy()
        new_events.append(event)
        return Scene(
            location=self.location,
            weather=self.weather,
            atmosphere=self.atmosphere,
            details=self.details,
            background_events=new_events,
            tension_level=self.tension_level
        )

    def adjust_tension(self, delta: int) -> 'Scene':
        """调整紧张等级
        
        Args:
            delta: 调整值
            
        Returns:
            Scene: 新的场景对象
        """
        new_tension = max(0, min(5, self.tension_level + delta))
        return Scene(
            location=self.location,
            weather=self.weather,
            atmosphere=self.atmosphere,
            details=self.details,
            background_events=self.background_events,
            tension_level=new_tension
        )


@dataclass
class World(AggregateRoot):
    """世界聚合根"""
    name: str
    current_time: GameTime = field(default_factory=GameTime)
    current_scene: Optional[Scene] = None
    locations: Dict[str, Location] = field(default_factory=dict)
    characters: Dict[str, Character] = field(default_factory=dict)
    items: Dict[str, Item] = field(default_factory=dict)
    combat: Optional[Combat] = None
    relationship_network: RelationshipNetwork = field(default_factory=RelationshipNetwork)
    objective_tracker: ObjectiveTracker = field(default_factory=ObjectiveTracker)
    global_events: List[Dict[str, Any]] = field(default_factory=list)
    world_state: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        # 手动初始化AggregateRoot的属性
        from .base import EntityId
        self._id = EntityId()
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._version = 1
        self._domain_events = []
        self._child_entities = set()
        
        if not self.name:
            raise ValueError("世界名称不能为空")
        
        # 如果没有设置当前场景，创建默认场景
        if not self.current_scene:
            default_location = Location(name="起始地点")
            self.current_scene = Scene(location=default_location)
            self.locations["起始地点"] = default_location

    @property
    def current_location(self) -> Location:
        """获取当前地点"""
        return self.current_scene.location if self.current_scene else Location(name="未知地点")

    @property
    def is_in_combat(self) -> bool:
        """检查是否在战斗中"""
        return self.combat is not None and self.combat.is_active

    @property
    def character_count(self) -> int:
        """获取角色数量"""
        return len(self.characters)

    @property
    def location_count(self) -> int:
        """获取地点数量"""
        return len(self.locations)

    def advance_time(self, minutes: int) -> None:
        """推进时间
        
        Args:
            minutes: 推进的分钟数
        """
        old_time = self.current_time
        self.current_time = self.current_time.advance(minutes)
        
        # 处理到期的事件
        self._process_due_events()
        
        self.add_domain_event("time_advanced", {
            "old_time": old_time.time_string,
            "new_time": self.current_time.time_string,
            "minutes_advanced": minutes
        })

    def set_scene(self, scene: Scene) -> None:
        """设置当前场景
        
        Args:
            scene: 新场景
        """
        old_scene = self.current_scene
        self.current_scene = scene
        
        # 确保地点存在于世界中
        if scene.location.name not in self.locations:
            self.locations[scene.location.name] = scene.location
        
        self.add_domain_event("scene_changed", {
            "old_location": old_scene.location_name if old_scene else "无",
            "new_location": scene.location_name,
            "weather": scene.weather.value,
            "tension_level": scene.tension_level
        })

    def add_location(self, location: Location) -> None:
        """添加地点
        
        Args:
            location: 地点对象
        """
        self.locations[location.name] = location
        
        self.add_domain_event("location_added", {
            "location_name": location.name,
            "location_type": location.location_type.value
        })

    def remove_location(self, location_name: str) -> bool:
        """移除地点
        
        Args:
            location_name: 地点名称
            
        Returns:
            bool: 是否成功移除
        """
        if location_name not in self.locations:
            return False
        
        # 检查是否有角色在该地点
        for character in self.characters.values():
            if (character.position and 
                self._get_location_name_at_position(character.position) == location_name):
                return False
        
        # 检查是否为当前地点
        if (self.current_scene and 
            self.current_scene.location.name == location_name):
            return False
        
        del self.locations[location_name]
        
        self.add_domain_event("location_removed", {
            "location_name": location_name
        })
        
        return True

    def add_character(self, character: Character) -> None:
        """添加角色
        
        Args:
            character: 角色对象
        """
        self.characters[character.name] = character
        
        # 更新关系网络
        self.relationship_network.characters.add(character.name)
        
        self.add_domain_event("character_added", {
            "character_name": character.name,
            "is_alive": character.is_alive
        })

    def remove_character(self, character_name: str) -> bool:
        """移除角色
        
        Args:
            character_name: 角色名称
            
        Returns:
            bool: 是否成功移除
        """
        if character_name not in self.characters:
            return False
        
        # 检查是否在战斗中
        if (self.combat and 
            character_name in self.combat.participants):
            return False
        
        del self.characters[character_name]
        
        # 从关系网络中移除
        self.relationship_network.characters.discard(character_name)
        
        self.add_domain_event("character_removed", {
            "character_name": character_name
        })
        
        return True

    def add_item(self, item: Item) -> None:
        """添加物品
        
        Args:
            item: 物品对象
        """
        self.items[str(item.id)] = item
        
        self.add_domain_event("item_added", {
            "item_id": str(item.id),
            "item_name": item.name,
            "item_type": item.item_type.value
        })

    def remove_item(self, item_id: str) -> bool:
        """移除物品
        
        Args:
            item_id: 物品ID
            
        Returns:
            bool: 是否成功移除
        """
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        del self.items[item_id]
        
        self.add_domain_event("item_removed", {
            "item_id": item_id,
            "item_name": item.name
        })
        
        return True

    def start_combat(self, location: str, participants: List[str]) -> None:
        """开始战斗
        
        Args:
            location: 战斗地点
            participants: 参与者列表
        """
        if self.is_in_combat:
            raise ValueError("已经在战斗中")
        
        # 检查所有参与者是否存在
        for participant in participants:
            if participant not in self.characters:
                raise ValueError(f"参与者 {participant} 不存在")
        
        self.combat = Combat(location=location)
        self.combat.start_combat(participants)
        
        self.add_domain_event("combat_started", {
            "location": location,
            "participants": participants
        })

    def end_combat(self) -> None:
        """结束战斗"""
        if not self.is_in_combat:
            return
        
        self.combat.end_combat()
        self.combat = None
        
        self.add_domain_event("combat_ended", {})

    def add_global_event(self, event_data: Dict[str, Any], trigger_time: Optional[int] = None) -> None:
        """添加全局事件
        
        Args:
            event_data: 事件数据
            trigger_time: 触发时间（分钟），如果为None则立即触发
        """
        if trigger_time is None:
            trigger_time = self.current_time.total_minutes
        
        event = {
            "id": str(len(self.global_events)),
            "trigger_time": trigger_time,
            "data": event_data,
            "triggered": False
        }
        self.global_events.append(event)
        
        # 按触发时间排序
        self.global_events.sort(key=lambda e: e["trigger_time"])

    def _process_due_events(self) -> None:
        """处理到期事件"""
        current_time = self.current_time.total_minutes
        triggered_events = []
        
        for event in self.global_events:
            if not event["triggered"] and event["trigger_time"] <= current_time:
                event["triggered"] = True
                triggered_events.append(event)
                
                # 执行事件效果
                self._execute_event_effects(event["data"])
        
        if triggered_events:
            self.add_domain_event("global_events_triggered", {
                "events": [event["data"] for event in triggered_events]
            })

    def _execute_event_effects(self, event_data: Dict[str, Any]) -> None:
        """执行事件效果
        
        Args:
            event_data: 事件数据
        """
        effect_type = event_data.get("type")
        
        if effect_type == "character_damage":
            character_name = event_data.get("character")
            damage = event_data.get("damage", 0)
            if character_name in self.characters:
                self.characters[character_name].take_damage(damage)
        
        elif effect_type == "character_heal":
            character_name = event_data.get("character")
            heal = event_data.get("heal", 0)
            if character_name in self.characters:
                self.characters[character_name].heal(heal)
        
        elif effect_type == "change_weather":
            weather_str = event_data.get("weather")
            if weather_str:
                try:
                    new_weather = Weather(weather_str)
                    if self.current_scene:
                        self.current_scene = Scene(
                            location=self.current_scene.location,
                            weather=new_weather,
                            atmosphere=self.current_scene.atmosphere,
                            details=self.current_scene.details,
                            background_events=self.current_scene.background_events,
                            tension_level=self.current_scene.tension_level
                        )
                except ValueError:
                    pass  # 忽略无效的天气值
        
        elif effect_type == "add_objective":
            objective_data = event_data.get("objective", {})
            # 这里应该创建目标并添加到目标跟踪器
            # 简化实现，只记录事件
            pass

    def _get_location_name_at_position(self, position: Position) -> Optional[str]:
        """获取位置对应的地点名称
        
        Args:
            position: 位置
            
        Returns:
            Optional[str]: 地点名称，如果找不到则返回None
        """
        # 简化实现，返回第一个包含该位置的地点
        for location in self.locations.values():
            if (location.coordinates and 
                location.coordinates.x == position.x and 
                location.coordinates.y == position.y):
                return location.name
        return None

    def snapshot(self) -> 'WorldSnapshot':
        """获取世界状态快照
        
        Returns:
            WorldSnapshot: 当前世界状态的完整快照
        """
        from ...core.interfaces import WorldSnapshot
        
        # 获取基础快照数据
        basic_snapshot = self.get_world_snapshot()
        
        # 构建完整的WorldSnapshot对象
        return WorldSnapshot(
            time_min=self.current_time.total_minutes,
            weather=basic_snapshot.get("weather", "unknown"),
            location=basic_snapshot.get("current_location", "unknown"),
            characters={name: {"hp": char.hp, "max_hp": char.max_hp, "is_alive": char.is_alive}
                        for name, char in self.characters.items()},
            positions={name: list(char.position) if char.position else [0, 0]
                       for name, char in self.characters.items()},
            relations={f"{a}->{b}": strength
                       for (a, b), strength in self.relationship_network.relations.items()},
            inventory={},  # TODO: 实现物品系统
            objectives=basic_snapshot.get("objectives", {}).get("active", []),
            objective_status={},  # TODO: 实现目标状态
            created_at=self._created_at
        )

    def get_world_snapshot(self) -> Dict[str, Any]:
        """获取世界快照
        
        Returns:
            Dict[str, Any]: 世界状态快照
        """
        return {
            "name": self.name,
            "time": self.current_time.time_string,
            "current_location": self.current_location.name,
            "weather": self.current_scene.weather.value if self.current_scene else "unknown",
            "characters": list(self.characters.keys()),
            "locations": list(self.locations.keys()),
            "in_combat": self.is_in_combat,
            "tension_level": self.current_scene.tension_level if self.current_scene else 0,
            "objectives": {
                "total": self.objective_tracker.total_objectives,
                "active": self.objective_tracker.active_count,
                "completed": self.objective_tracker.completed_count,
                "failed": self.objective_tracker.failed_count
            }
        }

    def validate(self) -> None:
        """验证世界状态"""
        if not self.name:
            raise ValueError("世界名称不能为空")
        
        # 验证当前时间
        self.current_time.__post_init__()
        
        # 验证当前场景
        if self.current_scene:
            self.current_scene.location.__post_init__()
        
        # 验证所有地点
        for location in self.locations.values():
            location.__post_init__()
        
        # 验证所有角色
        for character in self.characters.values():
            character.validate()
        
        # 验证战斗状态
        if self.combat:
            self.combat.validate()

    def _get_business_rules(self) -> List['BusinessRule']:
        """获取业务规则列表"""
        return [
            WorldMustHaveValidName(),
            WorldMustHaveValidTime(),
            WorldMustHaveValidScene(),
        ]


class WorldMustHaveValidName:
    """世界必须有有效名称规则"""
    
    def is_satisfied_by(self, entity: World) -> bool:
        return bool(entity.name)
    
    def get_error_message(self) -> str:
        return "世界名称不能为空"


class WorldMustHaveValidTime:
    """世界必须有有效时间规则"""
    
    def is_satisfied_by(self, entity: World) -> bool:
        try:
            entity.current_time.__post_init__()
            return True
        except ValueError:
            return False
    
    def get_error_message(self) -> str:
        return "世界时间必须有效"


class WorldMustHaveValidScene:
    """世界必须有有效场景规则"""
    
    def is_satisfied_by(self, entity: World) -> bool:
        if not entity.current_scene:
            return True
        try:
            entity.current_scene.location.__post_init__()
            return True
        except ValueError:
            return False
    
    def get_error_message(self) -> str:
        return "世界场景必须有效"