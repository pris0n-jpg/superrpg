"""
依赖注入容器模块

该模块实现了一个轻量级的依赖注入容器，遵循SOLID原则，
特别是依赖倒置原则(DIP)和单一职责原则(SRP)。

容器负责：
1. 服务注册和生命周期管理
2. 自动构造函数注入
3. 循环依赖检测
4. 服务解析和实例化
"""

from typing import Dict, Type, TypeVar, Callable, Any, Optional, List, Set, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import inspect


T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举
    
    定义了服务实例的生命周期类型：
    - TRANSIENT: 每次请求都创建新实例
    - SINGLETON: 整个容器生命周期内只创建一个实例
    - SCOPED: 在特定作用域内是单例
    """
    TRANSIENT = "transient"
    SINGLETON = "singleton"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """服务描述符
    
    封装了服务的注册信息，包括实现类型、工厂方法、生命周期等。
    遵循单一职责原则，专门负责服务元数据的封装。
    """
    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.dependencies is None:
            self.dependencies = []
        
        # 如果提供了实现类型，自动分析其依赖
        if self.implementation and not self.factory:
            self.dependencies = self._analyze_dependencies()
    
    def _analyze_dependencies(self) -> List[Type]:
        """分析实现类型的依赖
        
        通过反射分析构造函数参数，提取依赖类型。
        
        Returns:
            List[Type]: 依赖类型列表
        """
        if not self.implementation:
            return []
        
        dependencies = []
        try:
            sig = inspect.signature(self.implementation.__init__)
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 获取参数的类型注解
                param_type = param.annotation
                if param_type != inspect.Parameter.empty:
                    # 检查是否是基本类型，如果是则跳过依赖注入
                    type_str = str(param_type)
                    is_basic_type = (
                        param_type in (str, int, float, bool, list, dict, tuple, set) or
                        (hasattr(param_type, '__origin__') and param_type.__origin__ in (list, dict, tuple, set)) or
                        (hasattr(param_type, '__origin__') and param_type.__origin__ is Union) or
                        (hasattr(param_type, '__origin__') and param_type.__origin__ is Optional) or
                        'Optional' in type_str or 'Union' in type_str or
                        'pathlib' in type_str or 'Path' in type_str
                    )
                    
                    if is_basic_type:
                        # 基本类型和泛型类型不进行依赖注入
                        continue
                    else:
                        dependencies.append(param_type)
        except (ValueError, TypeError):
            # 如果无法分析签名，返回空列表
            pass
        
        return dependencies


class DIContainer:
    """依赖注入容器
    
    核心容器类，负责服务的注册、解析和生命周期管理。
    遵循单一职责原则，专门负责依赖注入的管理。
    """
    
    def __init__(self):
        """初始化容器"""
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._resolving: Set[Type] = set()  # 用于检测循环依赖
    
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """注册单例服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类型
            
        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        self._validate_registration(interface, implementation)
        
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self._services[interface] = descriptor
        return self
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """注册瞬态服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类型
            
        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        self._validate_registration(interface, implementation)
        
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT
        )
        
        self._services[interface] = descriptor
        return self
    
    def register_scoped(self, interface: Type[T], implementation: Type[T]) -> 'DIContainer':
        """注册作用域服务
        
        Args:
            interface: 服务接口类型
            implementation: 实现类型
            
        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        self._validate_registration(interface, implementation)
        
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=ServiceLifetime.SCOPED
        )
        
        self._services[interface] = descriptor
        return self
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T], 
                        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> 'DIContainer':
        """注册工厂方法
        
        Args:
            interface: 服务接口类型
            factory: 工厂方法
            lifetime: 服务生命周期
            
        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        if not callable(factory):
            raise ValueError(f"Factory must be callable, got {type(factory)}")
        
        descriptor = ServiceDescriptor(
            interface=interface,
            factory=factory,
            lifetime=lifetime
        )
        
        self._services[interface] = descriptor
        return self
    
    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """注册实例
        
        Args:
            interface: 服务接口类型
            instance: 服务实例
            
        Returns:
            DIContainer: 返回自身以支持链式调用
        """
        if not isinstance(instance, interface):
            raise ValueError(f"Instance must be of type {interface}, got {type(instance)}")
        
        descriptor = ServiceDescriptor(
            interface=interface,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        self._services[interface] = descriptor
        self._singletons[interface] = instance
        return self
    
    def resolve(self, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            T: 服务实例
            
        Raises:
            ValueError: 服务未注册或循环依赖
        """
        # 检查循环依赖
        if interface in self._resolving:
            raise ValueError(f"Circular dependency detected for {interface}")
        
        # 检查服务是否已注册
        descriptor = self._services.get(interface)
        if not descriptor:
            raise ValueError(f"Service {interface} not registered")
        
        # 根据生命周期返回实例
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._resolve_singleton(descriptor, interface)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._resolve_scoped(descriptor, interface)
        else:  # TRANSIENT
            return self._resolve_transient(descriptor, interface)
    
    def _resolve_singleton(self, descriptor: ServiceDescriptor, interface: Type[T]) -> T:
        """解析单例服务"""
        if interface in self._singletons:
            return self._singletons[interface]
        
        instance = self._create_instance(descriptor)
        self._singletons[interface] = instance
        return instance
    
    def _resolve_scoped(self, descriptor: ServiceDescriptor, interface: Type[T]) -> T:
        """解析作用域服务"""
        if interface in self._scoped_instances:
            return self._scoped_instances[interface]
        
        instance = self._create_instance(descriptor)
        self._scoped_instances[interface] = instance
        return instance
    
    def _resolve_transient(self, descriptor: ServiceDescriptor, interface: Type[T]) -> T:
        """解析瞬态服务"""
        return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例
        
        Args:
            descriptor: 服务描述符
            
        Returns:
            Any: 服务实例
        """
        # 如果已有实例，直接返回
        if descriptor.instance:
            return descriptor.instance
        
        # 添加到解析中集合，用于循环依赖检测
        self._resolving.add(descriptor.interface)
        
        try:
            # 如果有工厂方法，使用工厂创建
            if descriptor.factory:
                return descriptor.factory()
            
            # 否则使用构造函数注入创建
            if descriptor.implementation:
                return self._create_with_injection(descriptor.implementation)
            
            raise ValueError(f"No way to create instance for {descriptor.interface}")
        
        finally:
            # 从解析中集合移除
            self._resolving.discard(descriptor.interface)
    
    def _create_with_injection(self, implementation: Type) -> Any:
        """通过构造函数注入创建实例
        
        Args:
            implementation: 实现类型
            
        Returns:
            Any: 创建的实例
        """
        # 获取构造函数签名
        sig = inspect.signature(implementation.__init__)
        
        # 解析构造函数参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            # 获取参数类型注解
            param_type = param.annotation
            if param_type != inspect.Parameter.empty:
                # 检查是否是基本类型，如果是则跳过依赖注入
                is_basic_type = (
                    param_type in (str, int, float, bool, list, dict, tuple, set) or
                    (hasattr(param_type, '__origin__') and param_type.__origin__ in (list, dict, tuple, set)) or
                    (hasattr(param_type, '__origin__') and param_type.__origin__ is Union) or
                    (hasattr(param_type, '__origin__') and param_type.__origin__ is Optional) or
                    (str(param_type).startswith('typing.Optional') or str(param_type).startswith('typing.Union'))
                )
                
                if is_basic_type:
                    # 基本类型和泛型类型不进行依赖注入，使用默认值
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        # 对于没有默认值的基本类型，提供合理的默认值
                        if param_type == str:
                            kwargs[param_name] = ""
                        elif param_type == int:
                            kwargs[param_name] = 0
                        elif param_type == float:
                            kwargs[param_name] = 0.0
                        elif param_type == bool:
                            kwargs[param_name] = False
                        elif param_type == list or (hasattr(param_type, '__origin__') and param_type.__origin__ == list):
                            kwargs[param_name] = []
                        elif param_type == dict or (hasattr(param_type, '__origin__') and param_type.__origin__ == dict):
                            kwargs[param_name] = {}
                        elif param_type == set or (hasattr(param_type, '__origin__') and param_type.__origin__ == set):
                            kwargs[param_name] = set()
                        elif param_type == tuple or (hasattr(param_type, '__origin__') and param_type.__origin__ == tuple):
                            kwargs[param_name] = ()
                        elif hasattr(param_type, '__origin__') and param_type.__origin__ == Optional:
                            kwargs[param_name] = None
                        else:
                            kwargs[param_name] = None
                else:
                    # 递归解析依赖
                    try:
                        kwargs[param_name] = self.resolve(param_type)
                    except ValueError:
                        # 如果无法解析依赖，检查是否有默认值
                        if param.default != inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                        else:
                            raise ValueError(f"Cannot resolve dependency {param_type} "
                                           f"for parameter {param_name} of {implementation.__name__}")
            elif param.default != inspect.Parameter.empty:
                # 如果没有类型注解但有默认值，使用默认值
                kwargs[param_name] = param.default
        
        # 创建实例
        return implementation(**kwargs)
    
    def _validate_registration(self, interface: Type, implementation: Type) -> None:
        """验证服务注册
        
        Args:
            interface: 接口类型
            implementation: 实现类型
            
        Raises:
            ValueError: 注册无效
        """
        if not inspect.isclass(interface):
            raise ValueError(f"Interface must be a class, got {type(interface)}")
        
        if not inspect.isclass(implementation):
            raise ValueError(f"Implementation must be a class, got {type(implementation)}")
        
        if not issubclass(implementation, interface):
            raise ValueError(f"Implementation {implementation} must be a subclass of {interface}")
        
        # 检查是否已注册
        if interface in self._services:
            raise ValueError(f"Service {interface} is already registered")
    
    def is_registered(self, interface: Type) -> bool:
        """检查服务是否已注册
        
        Args:
            interface: 服务接口类型
            
        Returns:
            bool: 是否已注册
        """
        return interface in self._services
    
    def clear_scope(self) -> None:
        """清除作用域实例"""
        self._scoped_instances.clear()
    
    def get_registered_services(self) -> List[Type]:
        """获取已注册的服务列表
        
        Returns:
            List[Type]: 已注册的服务接口类型列表
        """
        return list(self._services.keys())
    
    def validate_dependencies(self) -> List[str]:
        """验证所有服务的依赖
        
        检查是否存在未注册的依赖。
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        for interface, descriptor in self._services.items():
            for dependency in descriptor.dependencies:
                if not self.is_registered(dependency):
                    errors.append(f"Service {interface} depends on unregistered service {dependency}")
        
        return errors


class ServiceLocator:
    """服务定位器
    
    提供全局访问容器的静态方法，遵循服务定位器模式。
    注意：在大多数情况下，应该优先使用构造函数注入而不是服务定位器。
    """
    
    _container: Optional[DIContainer] = None
    
    @classmethod
    def set_container(cls, container: DIContainer) -> None:
        """设置容器
        
        Args:
            container: 依赖注入容器
        """
        cls._container = container
    
    @classmethod
    def get_container(cls) -> DIContainer:
        """获取容器
        
        Returns:
            DIContainer: 依赖注入容器
            
        Raises:
            ValueError: 容器未设置
        """
        if cls._container is None:
            raise ValueError("Container not set. Call ServiceLocator.set_container() first.")
        return cls._container
    
    @classmethod
    def resolve(cls, interface: Type[T]) -> T:
        """解析服务
        
        Args:
            interface: 服务接口类型
            
        Returns:
            T: 服务实例
        """
        return cls.get_container().resolve(interface)