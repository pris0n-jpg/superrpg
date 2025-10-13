"""
世界仓储实现

提供世界数据持久化的具体实现，基于内存存储。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...core.interfaces import WorldRepository as IWorldRepository
from ...domain.models.world import World, Location, Scene, GameTime, Weather, LocationType
from ...domain.models.characters import Character
from ...domain.models.items import Item
from ...domain.models.combat import Combat
from ...domain.models.objectives import Objective


class WorldRepositoryImpl(IWorldRepository):
    """世界仓储实现
    
    基于内存和JSON文件的世界数据持久化实现。
    遵循单一职责原则，专门负责世界数据的存储和检索。
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """初始化世界仓储
        
        Args:
            storage_path: 存储路径，如果为None则使用内存存储
        """
        self._storage_path = storage_path
        self._worlds: Dict[str, World] = {}
        self._world_snapshots: Dict[str, List[Dict[str, Any]]] = {}
        self._world_events: Dict[str, List[Dict[str, Any]]] = {}
        self._world_configurations: Dict[str, Dict[str, Any]] = {}
        self._archived_worlds: set = set()
        
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
                
            # 加载世界数据
            for world_data in data.get('worlds', []):
                world = self._deserialize_world(world_data)
                if world:
                    self._worlds[world.name] = world
            
            # 加载快照数据
            self._world_snapshots = data.get('snapshots', {})
            
            # 加载事件数据
            self._world_events = data.get('events', {})
            
            # 加载配置数据
            self._world_configurations = data.get('configurations', {})
            
            # 加载归档状态
            self._archived_worlds = set(data.get('archived_worlds', []))
            
        except Exception:
            # 如果加载失败，初始化空数据
            self._worlds = {}
            self._world_snapshots = {}
            self._world_events = {}
            self._world_configurations = {}
            self._archived_worlds = set()
    
    def _save_to_storage(self) -> None:
        """保存数据到存储"""
        if not self._storage_path:
            return
            
        try:
            # 确保目录存在
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'worlds': [self._serialize_world(world) for world in self._worlds.values()],
                'snapshots': self._world_snapshots,
                'events': self._world_events,
                'configurations': self._world_configurations,
                'archived_worlds': list(self._archived_worlds),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception:
            # 静默处理保存错误，避免影响业务逻辑
            pass
    
    def _serialize_world(self, world: World) -> Dict[str, Any]:
        """序列化世界对象
        
        Args:
            world: 世界对象
            
        Returns:
            Dict[str, Any]: 序列化后的数据
        """
        return {
            'id': str(world.id),
            'name': world.name,
            'current_time': {
                'day': world.current_time.day,
                'hour': world.current_time.hour,
                'minute': world.current_time.minute,
            },
            'current_scene': self._serialize_scene(world.current_scene) if world.current_scene else None,
            'locations': {name: self._serialize_location(loc) for name, loc in world.locations.items()},
            'characters': {name: str(char.id) for name, char in world.characters.items()},
            'items': {item_id: str(item.id) for item_id, item in world.items.items()},
            'combat': self._serialize_combat(world.combat) if world.combat else None,
            'global_events': world.global_events,
            'world_state': world.world_state,
            'created_at': world.created_at.isoformat() if world.created_at else None,
            'updated_at': world.updated_at.isoformat() if world.updated_at else None,
        }
    
    def _deserialize_world(self, data: Dict[str, Any]) -> Optional[World]:
        """反序列化世界对象
        
        Args:
            data: 序列化数据
            
        Returns:
            Optional[World]: 世界对象，如果失败则返回None
        """
        try:
            # 反序列化游戏时间
            time_data = data.get('current_time', {})
            current_time = GameTime(
                day=time_data.get('day', 1),
                hour=time_data.get('hour', 8),
                minute=time_data.get('minute', 0),
            )
            
            # 反序列化当前场景
            current_scene = None
            scene_data = data.get('current_scene')
            if scene_data:
                current_scene = self._deserialize_scene(scene_data)
            
            # 反序列化地点
            locations = {}
            for name, loc_data in data.get('locations', {}).items():
                location = self._deserialize_location(loc_data)
                if location:
                    locations[name] = location
            
            # 反序列化战斗
            combat = None
            combat_data = data.get('combat')
            if combat_data:
                combat = self._deserialize_combat(combat_data)
            
            world = World(
                name=data['name'],
                current_time=current_time,
                current_scene=current_scene,
                locations=locations,
                characters={},  # 简化实现，不反序列化角色
                items={},  # 简化实现，不反序列化物品
                combat=combat,
                global_events=data.get('global_events', []),
                world_state=data.get('world_state', {}),
            )
            
            # 设置时间戳
            if data.get('created_at'):
                world.created_at = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                world.updated_at = datetime.fromisoformat(data['updated_at'])
            
            return world
            
        except Exception:
            return None
    
    def _serialize_location(self, location: Location) -> Dict[str, Any]:
        """序列化地点对象"""
        return {
            'name': location.name,
            'description': location.description,
            'location_type': location.location_type.value,
            'coordinates': {
                'x': location.coordinates.x,
                'y': location.coordinates.y,
            } if location.coordinates else None,
            'parent_location': location.parent_location,
            'child_locations': location.child_locations,
            'properties': location.properties,
        }
    
    def _deserialize_location(self, data: Dict[str, Any]) -> Optional[Location]:
        """反序列化地点对象"""
        try:
            coordinates = None
            coords_data = data.get('coordinates')
            if coords_data:
                from ...domain.models.characters import Position
                coordinates = Position(x=coords_data['x'], y=coords_data['y'])
            
            return Location(
                name=data['name'],
                description=data.get('description', ''),
                location_type=LocationType(data.get('location_type', 'outdoor')),
                coordinates=coordinates,
                parent_location=data.get('parent_location'),
                child_locations=data.get('child_locations', []),
                properties=data.get('properties', {}),
            )
        except Exception:
            return None
    
    def _serialize_scene(self, scene: Scene) -> Dict[str, Any]:
        """序列化场景对象"""
        if not scene:
            return None
            
        return {
            'location': self._serialize_location(scene.location),
            'weather': scene.weather.value,
            'atmosphere': scene.atmosphere,
            'details': scene.details,
            'background_events': scene.background_events,
            'tension_level': scene.tension_level,
        }
    
    def _deserialize_scene(self, data: Dict[str, Any]) -> Optional[Scene]:
        """反序列化场景对象"""
        try:
            location = self._deserialize_location(data['location'])
            if not location:
                return None
                
            return Scene(
                location=location,
                weather=Weather(data.get('weather', 'clear')),
                atmosphere=data.get('atmosphere', ''),
                details=data.get('details', []),
                background_events=data.get('background_events', []),
                tension_level=data.get('tension_level', 1),
            )
        except Exception:
            return None
    
    def _serialize_combat(self, combat: Combat) -> Dict[str, Any]:
        """序列化战斗对象"""
        if not combat:
            return None
            
        return {
            'id': str(combat.id),
            'location': combat.location,
            'is_active': combat.is_active,
            'current_round': combat.current_round,
            'participants': combat.participants,
            'combat_state': combat.combat_state,
        }
    
    def _deserialize_combat(self, data: Dict[str, Any]) -> Optional[Combat]:
        """反序列化战斗对象"""
        try:
            combat = Combat(
                location=data['location'],
            )
            combat.id = data['id']
            combat.is_active = data.get('is_active', False)
            combat.current_round = data.get('current_round', 1)
            combat.participants = data.get('participants', [])
            combat.combat_state = data.get('combat_state', {})
            return combat
        except Exception:
            return None
    
    def _add_world_event(self, world_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """添加世界事件
        
        Args:
            world_id: 世界ID
            event_type: 事件类型
            event_data: 事件数据
        """
        if world_id not in self._world_events:
            self._world_events[world_id] = []
            
        event = {
            'id': str(len(self._world_events[world_id])),
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': event_data,
        }
        
        self._world_events[world_id].append(event)
        
        # 限制事件数量
        if len(self._world_events[world_id]) > 1000:
            self._world_events[world_id] = self._world_events[world_id][-1000:]
    
    # 实现接口方法
    
    def get(self, id: str) -> Optional[World]:
        """根据ID获取世界"""
        for world in self._worlds.values():
            if str(world.id) == id:
                return world
        return None
    
    def save(self, entity: World) -> None:
        """保存世界"""
        if not entity.name:
            raise ValueError("世界名称不能为空")
            
        is_new = entity.name not in self._worlds
        self._worlds[entity.name] = entity
        
        # 添加事件记录
        action = "created" if is_new else "updated"
        self._add_world_event(str(entity.id), action, {
            'world_name': entity.name,
            'current_time': entity.current_time.time_string,
        })
        
        # 保存到存储
        self._save_to_storage()
    
    def delete(self, id: str) -> None:
        """删除世界"""
        world = None
        for name, w in self._worlds.items():
            if str(w.id) == id:
                world = w
                break
                
        if world:
            del self._worlds[world.name]
            
            # 添加事件记录
            self._add_world_event(id, "deleted", {
                'world_name': world.name,
            })
            
            # 保存到存储
            self._save_to_storage()
    
    def find_all(self) -> List[World]:
        """获取所有世界"""
        return [world for world in self._worlds.values() 
                if world.name not in self._archived_worlds]
    
    def find_by(self, criteria: Dict[str, Any]) -> List[World]:
        """根据条件查找世界"""
        result = []
        
        for world in self._worlds.values():
            if world.name in self._archived_worlds:
                continue
                
            match = True
            
            for key, value in criteria.items():
                if key == 'name' and world.name != value:
                    match = False
                elif key == 'is_active' and world.is_in_combat != value:
                    match = False
                elif key == 'character_count' and len(world.characters) != value:
                    match = False
                
                if not match:
                    break
            
            if match:
                result.append(world)
        
        return result
    
    # 实现领域特定的仓储方法
    
    def find_by_id(self, world_id: str) -> Optional[World]:
        """根据ID查找世界"""
        return self.get(world_id)
    
    def find_by_name(self, name: str) -> Optional[World]:
        """根据名称查找世界"""
        return self._worlds.get(name)
    
    def find_active(self) -> Optional[World]:
        """查找活跃世界"""
        for world in self._worlds.values():
            if world.name not in self._archived_worlds:
                return world
        return None
    
    def update(self, world: World) -> None:
        """更新世界"""
        self.save(world)
    
    def exists_by_id(self, world_id: str) -> bool:
        """检查世界是否存在（根据ID）"""
        return self.get(world_id) is not None
    
    def exists_by_name(self, name: str) -> bool:
        """检查世界是否存在（根据名称）"""
        return name in self._worlds
    
    def count(self) -> int:
        """获取世界总数"""
        return len([world for world in self._worlds.values() 
                   if world.name not in self._archived_worlds])
    
    def save_location(self, world_id: str, location: Location) -> None:
        """保存地点"""
        world = self.get(world_id)
        if not world:
            return
            
        world.locations[location.name] = location
        self._add_world_event(world_id, "location_saved", {
            'location_name': location.name,
        })
        self.save(world)
    
    def find_location_by_name(self, world_id: str, location_name: str) -> Optional[Location]:
        """根据名称查找地点"""
        world = self.get(world_id)
        if not world:
            return None
        return world.locations.get(location_name)
    
    def find_all_locations(self, world_id: str) -> List[Location]:
        """查找世界的所有地点"""
        world = self.get(world_id)
        if not world:
            return []
        return list(world.locations.values())
    
    def delete_location(self, world_id: str, location_name: str) -> bool:
        """删除地点"""
        world = self.get(world_id)
        if not world or location_name not in world.locations:
            return False
            
        del world.locations[location_name]
        self._add_world_event(world_id, "location_deleted", {
            'location_name': location_name,
        })
        self.save(world)
        return True
    
    def save_scene(self, world_id: str, scene: Scene) -> None:
        """保存场景"""
        world = self.get(world_id)
        if not world:
            return
            
        world.set_scene(scene)
        self._add_world_event(world_id, "scene_saved", {
            'location_name': scene.location_name,
            'weather': scene.weather.value,
        })
        self.save(world)
    
    def find_current_scene(self, world_id: str) -> Optional[Scene]:
        """查找当前场景"""
        world = self.get(world_id)
        if not world:
            return None
        return world.current_scene
    
    def find_scene_history(self, world_id: str, limit: int = 10) -> List[Scene]:
        """查找场景历史"""
        # 简化实现，返回当前场景
        world = self.get(world_id)
        if not world or not world.current_scene:
            return []
        return [world.current_scene]
    
    def save_combat(self, world_id: str, combat: Combat) -> None:
        """保存战斗"""
        world = self.get(world_id)
        if not world:
            return
            
        world.combat = combat
        self._add_world_event(world_id, "combat_saved", {
            'combat_id': str(combat.id),
            'is_active': combat.is_active,
        })
        self.save(world)
    
    def find_active_combat(self, world_id: str) -> Optional[Combat]:
        """查找活跃战斗"""
        world = self.get(world_id)
        if not world:
            return None
        return world.combat if world.is_in_combat else None
    
    def find_combat_history(self, world_id: str, limit: int = 10) -> List[Combat]:
        """查找战斗历史"""
        world = self.get(world_id)
        if not world:
            return []
        return [world.combat] if world.combat else []
    
    def get_world_statistics(self, world_id: str) -> Dict[str, Any]:
        """获取世界统计信息"""
        world = self.get(world_id)
        if not world:
            return {}
            
        return {
            'name': world.name,
            'current_time': world.current_time.time_string,
            'character_count': len(world.characters),
            'location_count': len(world.locations),
            'item_count': len(world.items),
            'in_combat': world.is_in_combat,
            'current_location': world.current_location.name,
            'weather': world.current_scene.weather.value if world.current_scene else 'unknown',
            'tension_level': world.current_scene.tension_level if world.current_scene else 0,
        }
    
    def get_world_timeline(self, world_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取世界时间线"""
        events = self._world_events.get(world_id, [])
        return events[-limit:] if limit > 0 else events
    
    def backup_world(self, world_id: str) -> Dict[str, Any]:
        """备份世界数据"""
        world = self.get(world_id)
        if not world:
            return {}
            
        backup_data = {
            'world': self._serialize_world(world),
            'timestamp': datetime.now().isoformat(),
            'backup_id': str(len(self._world_snapshots.get(world_id, []))),
        }
        
        if world_id not in self._world_snapshots:
            self._world_snapshots[world_id] = []
        
        self._world_snapshots[world_id].append(backup_data)
        self._save_to_storage()
        
        return backup_data
    
    def restore_world(self, backup_data: Dict[str, Any]) -> World:
        """从备份数据恢复世界"""
        world_data = backup_data.get('world')
        if not world_data:
            raise ValueError("备份数据无效")
            
        world = self._deserialize_world(world_data)
        if not world:
            raise ValueError("无法恢复世界数据")
            
        self.save(world)
        return world
    
    def get_world_snapshots(self, world_id: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取世界快照"""
        snapshots = self._world_snapshots.get(world_id, [])
        
        if start_time or end_time:
            filtered_snapshots = []
            for snapshot in snapshots:
                snapshot_time = datetime.fromisoformat(snapshot['timestamp'])
                if start_time and snapshot_time < start_time:
                    continue
                if end_time and snapshot_time > end_time:
                    continue
                filtered_snapshots.append(snapshot)
            return filtered_snapshots
        
        return snapshots
    
    def save_world_snapshot(self, world_id: str, snapshot_data: Dict[str, Any]) -> None:
        """保存世界快照"""
        if world_id not in self._world_snapshots:
            self._world_snapshots[world_id] = []
        
        snapshot = {
            'id': str(len(self._world_snapshots[world_id])),
            'timestamp': datetime.now().isoformat(),
            'data': snapshot_data,
        }
        
        self._world_snapshots[world_id].append(snapshot)
        self._save_to_storage()
    
    def get_characters_in_world(self, world_id: str) -> List[Character]:
        """获取世界中的所有角色"""
        world = self.get(world_id)
        if not world:
            return []
        return list(world.characters.values())
    
    def get_items_in_world(self, world_id: str) -> List[Item]:
        """获取世界中的所有物品"""
        world = self.get(world_id)
        if not world:
            return []
        return list(world.items.values())
    
    def get_objectives_in_world(self, world_id: str) -> List[Objective]:
        """获取世界中的所有目标"""
        # 简化实现
        return []
    
    def search_worlds(self, criteria: Dict[str, Any]) -> List[World]:
        """根据条件搜索世界"""
        return self.find_by(criteria)
    
    def get_world_activity_summary(self, world_id: str, days: int = 7) -> Dict[str, Any]:
        """获取世界活动摘要"""
        events = self._world_events.get(world_id, [])
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        recent_events = []
        for event in events:
            event_time = datetime.fromisoformat(event['timestamp']).timestamp()
            if event_time >= cutoff_time:
                recent_events.append(event)
        
        # 统计事件类型
        event_types = {}
        for event in recent_events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        return {
            'world_id': world_id,
            'days': days,
            'total_events': len(recent_events),
            'event_types': event_types,
            'last_activity': recent_events[-1]['timestamp'] if recent_events else None,
        }
    
    def get_location_connections(self, world_id: str, location_name: str) -> List[str]:
        """获取地点连接"""
        location = self.find_location_by_name(world_id, location_name)
        if not location:
            return []
        return location.child_locations
    
    def set_location_connection(self, world_id: str, from_location: str, to_location: str, bidirectional: bool = True) -> None:
        """设置地点连接"""
        world = self.get(world_id)
        if not world:
            return
            
        from_loc = world.locations.get(from_location)
        to_loc = world.locations.get(to_location)
        
        if from_loc and to_loc:
            if to_location not in from_loc.child_locations:
                from_loc.child_locations.append(to_location)
            
            if bidirectional and from_location not in to_loc.child_locations:
                to_loc.child_locations.append(from_location)
            
            self.save(world)
    
    def remove_location_connection(self, world_id: str, from_location: str, to_location: str) -> None:
        """移除地点连接"""
        world = self.get(world_id)
        if not world:
            return
            
        from_loc = world.locations.get(from_location)
        to_loc = world.locations.get(to_location)
        
        if from_loc and to_location in from_loc.child_locations:
            from_loc.child_locations.remove(to_location)
        
        if to_loc and from_location in to_loc.child_locations:
            to_loc.child_locations.remove(from_location)
        
        self.save(world)
    
    def get_world_events(self, world_id: str, event_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取世界事件"""
        events = self._world_events.get(world_id, [])
        
        if event_type:
            events = [e for e in events if e['event_type'] == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def add_world_event(self, world_id: str, event_data: Dict[str, Any]) -> None:
        """添加世界事件"""
        event_type = event_data.get('type', 'unknown')
        self._add_world_event(world_id, event_type, event_data)
        self._save_to_storage()
    
    def get_world_configuration(self, world_id: str) -> Dict[str, Any]:
        """获取世界配置"""
        return self._world_configurations.get(world_id, {})
    
    def update_world_configuration(self, world_id: str, config_data: Dict[str, Any]) -> None:
        """更新世界配置"""
        if world_id not in self._world_configurations:
            self._world_configurations[world_id] = {}
        
        self._world_configurations[world_id].update(config_data)
        self._save_to_storage()
    
    def batch_save_worlds(self, worlds: List[World]) -> None:
        """批量保存世界"""
        for world in worlds:
            self.save(world)
    
    def batch_delete_worlds(self, world_ids: List[str]) -> int:
        """批量删除世界"""
        deleted_count = 0
        for world_id in world_ids:
            if self.exists_by_id(world_id):
                self.delete(world_id)
                deleted_count += 1
        return deleted_count
    
    def get_world_creation_date(self, world_id: str) -> Optional[datetime]:
        """获取世界创建日期"""
        world = self.get(world_id)
        return world.created_at if world else None
    
    def get_world_last_modified(self, world_id: str) -> Optional[datetime]:
        """获取世界最后修改时间"""
        world = self.get(world_id)
        return world.updated_at if world else None
    
    def archive_world(self, world_id: str) -> bool:
        """归档世界"""
        world = self.get(world_id)
        if not world:
            return False
            
        self._archived_worlds.add(world.name)
        self._add_world_event(world_id, "archived", {
            'world_name': world.name,
        })
        self._save_to_storage()
        return True
    
    def unarchive_world(self, world_id: str) -> bool:
        """取消归档世界"""
        world = self.get(world_id)
        if not world:
            return False
            
        self._archived_worlds.discard(world.name)
        self._add_world_event(world_id, "unarchived", {
            'world_name': world.name,
        })
        self._save_to_storage()
        return True
    
    def is_world_archived(self, world_id: str) -> bool:
        """检查世界是否已归档"""
        world = self.get(world_id)
        if not world:
            return False
        return world.name in self._archived_worlds