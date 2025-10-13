"""
核心接口定义模块

该模块定义了系统的核心接口，遵循SOLID原则中的依赖倒置原则(DIP)，
确保高层模块不依赖低层模块，而是依赖于抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import uuid
from datetime import datetime


# 泛型类型变量
T = TypeVar('T')
ID = TypeVar('ID')


@dataclass
class WorldSnapshot:
    """世界状态快照
    
    封装了世界在特定时刻的完整状态，用于状态持久化、回滚和同步。
    遵循单一职责原则，专门负责状态数据的封装。
    """
    time_min: int
    weather: str
    location: str
    characters: Dict[str, Any]
    positions: Dict[str, Tuple[int, int]]
    relations: Dict[str, int]
    inventory: Dict[str, Dict[str, int]]
    objectives: List[str]
    objective_status: Dict[str, str]
    created_at: datetime
    id: str = str(uuid.uuid4())


class WorldState(ABC):
    """世界状态接口
    
    遵循接口隔离原则(ISP)，只提供世界状态管理的核心方法，
    避免客户端依赖不需要的功能。
    """
    
    @abstractmethod
    def snapshot(self) -> WorldSnapshot:
        """获取当前状态快照
        
        Returns:
            WorldSnapshot: 当前世界状态的完整快照
        """
        pass
    
    @abstractmethod
    def apply_event(self, event: 'WorldEvent') -> None:
        """应用世界事件
        
        Args:
            event: 要应用的世界事件
        """
        pass
    
    @abstractmethod
    def get_character(self, name: str) -> Optional[Dict[str, Any]]:
        """获取角色信息
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Dict[str, Any]]: 角色信息，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def get_position(self, name: str) -> Optional[Tuple[int, int]]:
        """获取角色位置
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Tuple[int, int]]: 角色位置坐标，如果不存在则返回None
        """
        pass


class Repository(ABC, Generic[T, ID]):
    """通用仓储接口
    
    遵循开放/封闭原则(OCP)，通过泛型设计支持不同类型的实体仓储，
    扩展新的仓储类型无需修改现有代码。
    """
    
    @abstractmethod
    def get(self, id: ID) -> Optional[T]:
        """根据ID获取实体
        
        Args:
            id: 实体标识符
            
        Returns:
            Optional[T]: 实体实例，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """保存实体
        
        Args:
            entity: 要保存的实体
        """
        pass
    
    @abstractmethod
    def delete(self, id: ID) -> None:
        """删除实体
        
        Args:
            id: 要删除的实体ID
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """获取所有实体
        
        Returns:
            List[T]: 所有实体列表
        """
        pass
    
    @abstractmethod
    def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """根据条件查找实体
        
        Args:
            criteria: 查找条件
            
        Returns:
            List[T]: 符合条件的实体列表
        """
        pass


class CharacterRepository(Repository['Character', str]):
    """角色仓储接口
    
    专门针对角色实体的仓储接口，继承通用仓储接口并添加角色特定的方法。
    遵循接口隔离原则，只提供角色相关的操作。
    """
    pass


class CombatRepository(Repository['CombatState', str]):
    """战斗仓储接口
    
    专门针对战斗状态的仓储接口。
    """
    pass


class WorldRepository(Repository['WorldState', str]):
    """世界仓储接口
    
    专门针对世界状态的仓储接口。
    """
    pass


class DomainService(ABC):
    """领域服务基类
    
    所有领域服务的抽象基类，遵循里氏替换原则(LSP)，
    确保所有领域服务都可以被统一处理。
    """
    pass


class CharacterService(DomainService):
    """角色领域服务接口
    
    遵循单一职责原则(SRP)，专门负责角色相关的业务逻辑。
    """
    
    @abstractmethod
    def create_character(self, data: Dict[str, Any]) -> 'Character':
        """创建角色
        
        Args:
            data: 角色数据
            
        Returns:
            Character: 创建的角色实例
        """
        pass
    
    @abstractmethod
    def update_position(self, name: str, position: Tuple[int, int]) -> None:
        """更新角色位置
        
        Args:
            name: 角色名称
            position: 新位置坐标
        """
        pass
    
    @abstractmethod
    def get_stat_block(self, name: str) -> Optional['Character']:
        """获取角色状态块
        
        Args:
            name: 角色名称
            
        Returns:
            Optional[Character]: 角色状态，如果不存在则返回None
        """
        pass


class CombatService(DomainService):
    """战斗领域服务接口
    
    专门负责战斗相关的业务逻辑。
    """
    
    @abstractmethod
    def initiate_combat(self, participants: List[str]) -> 'CombatState':
        """发起战斗
        
        Args:
            participants: 参与战斗的角色列表
            
        Returns:
            CombatState: 战斗状态
        """
        pass
    
    @abstractmethod
    def resolve_attack(self, attack_data: 'AttackData') -> 'AttackResult':
        """解析攻击
        
        Args:
            attack_data: 攻击数据
            
        Returns:
            AttackResult: 攻击结果
        """
        pass
    
    @abstractmethod
    def next_turn(self) -> 'TurnResult':
        """推进到下一个回合
        
        Returns:
            TurnResult: 回合结果
        """
        pass


class EventBus(ABC):
    """事件总线接口
    
    遵循开放/封闭原则，支持事件的发布和订阅，
    可以扩展新的事件类型而无需修改现有代码。
    """
    
    @abstractmethod
    def publish(self, event: 'DomainEvent') -> None:
        """发布事件
        
        Args:
            event: 要发布的事件
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: type, handler: 'EventHandler') -> None:
        """订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: type, handler: 'EventHandler') -> None:
        """取消订阅事件
        
        Args:
            event_type: 事件类型
            handler: 事件处理器
        """
        pass


class EventHandler(ABC):
    """事件处理器接口
    
    遵循接口隔离原则，只定义事件处理的核心方法。
    """
    
    @abstractmethod
    def handle(self, event: 'DomainEvent') -> None:
        """处理事件
        
        Args:
            event: 要处理的事件
        """
        pass


class DomainEvent(ABC):
    """领域事件基类
    
    所有领域事件的抽象基类，遵循里氏替换原则。
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.occurred_at = datetime.now()
    
    @abstractmethod
    def get_event_type(self) -> str:
        """获取事件类型
        
        Returns:
            str: 事件类型名称
        """
        pass


class WorldEvent(DomainEvent):
    """世界事件基类
    
    所有世界相关事件的基类。
    """
    pass


class Logger(ABC):
    """日志接口
    
    遵循接口隔离原则，只提供核心的日志记录方法。
    """
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """记录错误日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        pass
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志
        
        Args:
            message: 日志消息
            **kwargs: 额外的日志数据
        """
        pass


class ConfigLoader(ABC):
    """配置加载器接口
    
    遵循单一职责原则，专门负责配置的加载和管理。
    """
    
    @abstractmethod
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        pass
    
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> bool:
        """验证配置
        
        Args:
            config: 配置数据
            
        Returns:
            bool: 验证是否通过
        """
        pass


class GameCoordinator(ABC):
    """游戏协调器接口
    
    遵循单一职责原则，专门负责游戏协调的核心功能。
    """
    
    @abstractmethod
    async def run_game(self) -> None:
        """运行游戏

        该方法是游戏的主要入口点，负责启动和运行游戏循环。
        """
        pass