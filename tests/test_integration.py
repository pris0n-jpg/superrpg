"""
集成测试模块

该模块包含所有模块的集成测试，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责验证各模块之间的协作。
"""

import asyncio
import json
import pytest
import tempfile
import os
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch

# 测试目标模块
from src.bootstrap.enhanced_application_bootstrap import (
    EnhancedApplicationBootstrap, BootstrapConfig, ModuleInfo
)
from src.adapters.api_gateway import ApiGateway
from src.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from src.infrastructure.config.enhanced_config_manager import EnhancedConfigManager
from src.domain.responses.api_response import ApiResponse, ResponseBuilder
from src.core.container import DIContainer
from src.core.interfaces import Logger, EventBus
from src.application.services.extension_manager_service import (
    ExtensionManagerImpl, ExtensionRegistryImpl, ExtensionLoaderImpl
)


class TestAPIGatewayIntegration:
    """API网关集成测试"""
    
    @pytest.fixture
    def api_gateway(self):
        """API网关测试夹具"""
        return ApiGateway(name="Test API Gateway", version="1.0.0")
    
    @pytest.fixture
    def sample_routes(self):
        """示例路由测试夹具"""
        routes = []
        
        # 健康检查路由
        async def health_handler(**kwargs):
            return ResponseBuilder.health().to_dict()
        
        api_gateway.add_route(
            path="/health",
            method="GET",
            handler=health_handler,
            name="health_check",
            tags=["health"]
        )
        
        # 示例API路由
        async def echo_handler(**kwargs):
            request = kwargs.get("request")
            return ResponseBuilder.success(data={"echo": "test"}).to_dict()
        
        api_gateway.add_route(
            path="/echo",
            method="POST",
            handler=echo_handler,
            name="echo",
            tags=["test"]
        )
        
        return routes
    
    def test_route_registration(self, api_gateway):
        """测试路由注册"""
        # 注册路由
        async def test_handler(**kwargs):
            return {"test": "data"}
        
        api_gateway.add_route(
            path="/test",
            method="GET",
            handler=test_handler,
            name="test_route"
        )
        
        # 验证路由信息
        routes_info = api_gateway.get_routes_info()
        assert len(routes_info) >= 1
        
        test_route = next(r for r in routes_info if r["name"] == "test_route")
        assert test_route["path"] == "/test"
        assert test_route["method"] == "GET"
    
    def test_route_matching(self, api_gateway):
        """测试路由匹配"""
        # 注册路由
        async def test_handler(**kwargs):
            return {"test": "data"}
        
        api_gateway.add_route(
            path="/users/{id}",
            method="GET",
            handler=test_handler,
            name="get_user"
        )
        
        # 测试匹配
        route = api_gateway._find_route("/users/123", "GET")
        assert route is not None
        assert route.name == "get_user"
        
        # 测试参数提取
        params = route.extract_params("/users/123")
        assert params["id"] == "123"
        
        # 测试不匹配
        route = api_gateway._find_route("/users/123", "POST")
        assert route is None
    
    @pytest.mark.asyncio
    async def test_request_handling(self, api_gateway):
        """测试请求处理"""
        # 注册路由
        async def echo_handler(**kwargs):
            request = kwargs.get("request")
            body = kwargs.get("body", {})
            return ResponseBuilder.success(data=body).to_dict()
        
        api_gateway.add_route(
            path="/echo",
            method="POST",
            handler=echo_handler,
            name="echo"
        )
        
        # 发送请求
        test_data = {"message": "hello"}
        response = await api_gateway.handle_request(
            method="POST",
            path="/echo",
            body=test_data
        )
        
        # 验证响应
        assert response.status_code == 200
        assert response.body["success"] is True
        assert response.body["data"] == test_data
    
    def test_route_groups(self, api_gateway):
        """测试路由组"""
        # 创建路由组
        api_group = api_gateway.create_route_group(
            prefix="/api/v1",
            description="API v1"
        )
        
        # 添加路由到组
        async def users_handler(**kwargs):
            return {"users": []}
        
        api_group.add_route(
            path="/users",
            method="GET",
            handler=users_handler,
            name="list_users"
        )
        
        # 注册路由组
        api_gateway.add_route_group(api_group)
        
        # 验证路由
        route = api_gateway._find_route("/api/v1/users", "GET")
        assert route is not None
        assert route.name == "list_users"
    
    def test_get_stats(self, api_gateway):
        """测试统计信息"""
        stats = api_gateway.get_stats()
        
        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "routes_count" in stats
        assert "start_time" in stats


class TestEventBusIntegration:
    """事件总线集成测试"""
    
    @pytest.fixture
    def event_bus(self):
        """事件总线测试夹具"""
        return EnhancedEventBus(
            enable_persistence=False,
            enable_metrics=True
        )
    
    @pytest.fixture
    def sample_event(self):
        """示例事件测试夹具"""
        class TestEvent:
            def __init__(self, data):
                self.data = data
                self.id = "test-id"
                self.occurred_at = None
            
            def get_event_type(self):
                return "test_event"
        
        return TestEvent({"message": "test"})
    
    @pytest.mark.asyncio
    async def test_event_publish_subscribe(self, event_bus, sample_event):
        """测试事件发布和订阅"""
        # 创建事件处理器
        received_events = []
        
        class TestHandler:
            async def handle(self, event):
                received_events.append(event)
        
        handler = TestHandler()
        
        # 订阅事件
        await event_bus.subscribe(type(sample_event), handler)
        
        # 发布事件
        await event_bus.publish(sample_event)
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        # 验证事件处理
        assert len(received_events) == 1
        assert received_events[0].data["message"] == "test"
    
    @pytest.mark.asyncio
    async def test_event_metrics(self, event_bus, sample_event):
        """测试事件指标"""
        # 获取初始指标
        initial_metrics = event_bus.get_metrics()
        assert initial_metrics["events_published"] == 0
        
        # 发布事件
        await event_bus.publish(sample_event)
        
        # 获取更新后的指标
        updated_metrics = event_bus.get_metrics()
        assert updated_metrics["events_published"] == 1
        assert updated_metrics["events_processed"] >= 0
    
    def test_event_filtering(self, event_bus):
        """测试事件过滤"""
        from src.infrastructure.events.enhanced_event_bus import EventFilter, EventPriority
        
        # 创建过滤器
        filter = EventFilter()
        filter.add_event_type("test_event")
        filter.set_priority_range(EventPriority.NORMAL, EventPriority.HIGH)
        
        # 创建存储事件
        from src.infrastructure.events.enhanced_event_bus import StoredEvent, EventMetadata, EventStatus
        from datetime import datetime
        
        metadata = EventMetadata(
            event_id="test-id",
            event_type="test_event",
            source="test",
            priority=EventPriority.HIGH
        )
        
        stored_event = StoredEvent(
            metadata=metadata,
            event_data={"message": "test"},
            status=EventStatus.PENDING
        )
        
        # 测试过滤器
        assert filter.matches(stored_event)
        
        # 测试不匹配
        filter2 = EventFilter()
        filter2.add_event_type("other_event")
        assert not filter2.matches(stored_event)


class TestConfigManagerIntegration:
    """配置管理器集成测试"""
    
    @pytest.fixture
    def config_manager(self):
        """配置管理器测试夹具"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield EnhancedConfigManager(
                config_dir=temp_dir,
                auto_reload=False,
                enable_validation=True
            )
    
    @pytest.fixture
    def sample_config(self):
        """示例配置测试夹具"""
        return {
            "app": {
                "name": "test_app",
                "version": "1.0.0",
                "debug": True
            },
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db"
            }
        }
    
    def test_config_load_save(self, config_manager, sample_config):
        """测试配置加载和保存"""
        # 创建配置文件
        config_file = os.path.join(config_manager.config_dir, "test.json")
        with open(config_file, 'w') as f:
            json.dump(sample_config, f)
        
        # 加载配置
        loaded_config = config_manager.load(config_file)
        assert loaded_config == sample_config
        
        # 测试获取配置值
        assert config_manager.get("app.name") == "test_app"
        assert config_manager.get("app.version") == "1.0.0"
        assert config_manager.get("database.port") == 5432
        
        # 测试设置配置值
        config_manager.set("app.new_field", "new_value")
        assert config_manager.get("app.new_field") == "new_value"
    
    def test_config_validation(self, config_manager):
        """测试配置验证"""
        from src.infrastructure.config.enhanced_config_manager import ConfigSchema
        
        # 添加配置模式
        config_manager._validator.add_schema(ConfigSchema(
            key="required_field",
            type=str,
            required=True,
            description="必需字段"
        ))
        
        # 测试有效配置
        valid_config = {"required_field": "value"}
        assert config_manager.validate(valid_config) is True
        
        # 测试无效配置
        invalid_config = {"other_field": "value"}
        assert config_manager.validate(invalid_config) is False
    
    def test_config_change_notification(self, config_manager):
        """测试配置变更通知"""
        change_events = []
        
        def change_listener(event):
            change_events.append(event)
        
        config_manager.add_change_listener(change_listener)
        
        # 设置配置值
        config_manager.set("test_field", "test_value")
        
        # 验证通知
        assert len(change_events) == 1
        assert change_events[0].key == "test_field"
        assert change_events[0].new_value == "test_value"


class TestExtensionSystemIntegration:
    """扩展系统集成测试"""
    
    @pytest.fixture
    def extension_manager(self):
        """扩展管理器测试夹具"""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = ExtensionRegistryImpl()
            loader = ExtensionLoaderImpl()
            
            manager = ExtensionManagerImpl(
                registry=registry,
                loader=loader,
                container=DIContainer(),
                event_bus=Mock(),
                logger=Mock(),
                extensions_dir=temp_dir
            )
            
            yield manager
    
    def test_extension_registration(self, extension_manager):
        """测试扩展注册"""
        from src.core.interfaces.extension_interface import Extension, ExtensionMetadata, ExtensionStatus
        from src.domain.models.extension_context import ExtensionContextImpl
        
        # 创建测试扩展
        class TestExtension(Extension):
            async def initialize(self, context):
                pass
            
            async def activate(self):
                pass
            
            async def deactivate(self):
                pass
            
            async def cleanup(self):
                pass
        
        metadata = ExtensionMetadata(
            name="test_extension",
            version="1.0.0",
            description="Test Extension",
            author="Test",
            extension_type="utility"
        )
        
        extension = TestExtension(metadata)
        
        # 注册扩展
        success = asyncio.run(extension_manager.registry.register_extension(extension))
        assert success is True
        
        # 获取扩展
        retrieved = asyncio.run(extension_manager.registry.get_extension("test_extension:1.0.0"))
        assert retrieved is not None
        assert retrieved.metadata.name == "test_extension"
    
    def test_extension_dependencies(self, extension_manager):
        """测试扩展依赖"""
        from src.core.interfaces.extension_interface import ExtensionMetadata
        
        # 创建有依赖的扩展
        metadata = ExtensionMetadata(
            name="dependent_extension",
            version="1.0.0",
            description="Dependent Extension",
            author="Test",
            extension_type="utility",
            dependencies=["base_extension"]
        )
        
        # 测试依赖解析
        dependencies = asyncio.run(extension_manager.get_extension_dependencies("dependent_extension:1.0.0"))
        assert "base_extension" in dependencies


class TestModuleSystemIntegration:
    """模块系统集成测试"""
    
    @pytest.fixture
    def bootstrap_config(self):
        """启动器配置测试夹具"""
        return BootstrapConfig(
            enable_extensions=False,
            enable_api_gateway=False,
            enable_health_checks=True,
            enable_graceful_shutdown=False
        )
    
    @pytest.fixture
    def module_config(self):
        """模块配置测试夹具"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建模块配置文件
            modules_config = {
                "modules": [
                    {
                        "name": "test_module",
                        "version": "1.0.0",
                        "description": "Test Module",
                        "dependencies": [],
                        "enabled": True,
                        "priority": 100
                    }
                ]
            }
            
            config_file = os.path.join(temp_dir, "modules.json")
            with open(config_file, 'w') as f:
                json.dump(modules_config, f)
            
            yield temp_dir
    
    @pytest.mark.asyncio
    async def test_module_loading(self, bootstrap_config, module_config):
        """测试模块加载"""
        # 更新配置目录
        bootstrap_config.config_dir = module_config
        
        # 创建启动器
        bootstrap = EnhancedApplicationBootstrap(bootstrap_config)
        
        # 启动应用
        container = await bootstrap.bootstrap()
        
        # 验证模块加载
        assert "test_module" in bootstrap.modules
        assert bootstrap.is_module_loaded("test_module")
        
        # 获取模块信息
        module_info = bootstrap.get_module_info("test_module")
        assert module_info is not None
        assert module_info.name == "test_module"
        assert module_info.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_health_checks(self, bootstrap_config):
        """测试健康检查"""
        # 创建启动器
        bootstrap = EnhancedApplicationBootstrap(bootstrap_config)
        
        # 启动应用
        container = await bootstrap.bootstrap()
        
        # 执行健康检查
        if bootstrap.health_checker:
            health_result = await bootstrap.health_checker.check_health()
            assert health_result.status == "healthy"
            assert "application" in health_result.services
    
    @pytest.mark.asyncio
    async def test_application_stats(self, bootstrap_config):
        """测试应用统计"""
        # 创建启动器
        bootstrap = EnhancedApplicationBootstrap(bootstrap_config)
        
        # 启动应用
        container = await bootstrap.bootstrap()
        
        # 获取统计信息
        stats = bootstrap.get_stats()
        
        assert "startup_time" in stats
        assert "modules_loaded" in stats
        assert "is_running" in stats
        assert stats["is_running"] is True


class TestResponseFormatIntegration:
    """响应格式集成测试"""
    
    def test_success_response(self):
        """测试成功响应"""
        data = {"message": "test"}
        response = ResponseBuilder.success(data=data, message="操作成功")
        
        assert response.success is True
        assert response.message == "操作成功"
        assert response.data == data
        assert response.code == "SUCCESS"
        
        # 转换为字典
        response_dict = response.to_dict()
        assert response_dict["success"] is True
        assert response_dict["data"] == data
    
    def test_error_response(self):
        """测试错误响应"""
        response = ResponseBuilder.error(
            message="操作失败",
            code="OPERATION_FAILED"
        )
        
        assert response.success is False
        assert response.message == "操作失败"
        assert response.code == "OPERATION_FAILED"
        
        # 转换为字典
        response_dict = response.to_dict()
        assert response_dict["success"] is False
        assert response_dict["code"] == "OPERATION_FAILED"
    
    def test_paged_response(self):
        """测试分页响应"""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = ResponseBuilder.paged(
            items=items,
            page=1,
            page_size=10,
            total=25,
            message="查询成功"
        )
        
        assert response.page == 1
        assert response.page_size == 10
        assert response.total == 25
        assert response.total_pages == 3
        assert response.has_next is True
        assert response.has_prev is False
        
        # 转换为字典
        response_dict = response.to_dict()
        assert "pagination" in response_dict
        assert response_dict["pagination"]["page"] == 1
    
    def test_health_response(self):
        """测试健康检查响应"""
        response = ResponseBuilder.health(
            status="healthy",
            version="1.0.0",
            uptime=60.5
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.uptime == 60.5
        
        # 转换为字典
        response_dict = response.to_dict()
        assert response_dict["status"] == "healthy"
        assert response_dict["version"] == "1.0.0"


class TestSystemIntegration:
    """系统集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_application_bootstrap(self):
        """测试完整应用启动"""
        # 创建配置
        config = BootstrapConfig(
            enable_extensions=False,
            enable_api_gateway=False,
            enable_health_checks=True,
            enable_graceful_shutdown=False
        )
        
        # 创建临时配置目录
        with tempfile.TemporaryDirectory() as temp_dir:
            config.config_dir = temp_dir
            
            # 创建模块配置
            modules_config = {
                "modules": [
                    {
                        "name": "core",
                        "version": "1.0.0",
                        "description": "Core Module",
                        "dependencies": [],
                        "enabled": True,
                        "priority": 100
                    }
                ]
            }
            
            config_file = os.path.join(temp_dir, "modules.json")
            with open(config_file, 'w') as f:
                json.dump(modules_config, f)
            
            # 启动应用
            async with EnhancedApplicationContext(config) as container:
                # 验证容器
                assert container is not None
                
                # 验证核心组件
                logger = container.resolve(Logger)
                assert logger is not None
                
                # 验证模块加载
                # 这里需要根据实际的启动器实现进行调整
                pass
    
    @pytest.mark.asyncio
    async def test_component_integration(self):
        """测试组件集成"""
        # 创建核心组件
        container = DIContainer()
        event_bus = EnhancedEventBus(enable_persistence=False)
        config_manager = EnhancedConfigManager(enable_validation=False)
        
        # 注册组件
        container.register_instance(EventBus, event_bus)
        container.register_instance(EnhancedConfigManager, config_manager)
        
        # 测试组件协作
        # 这里可以添加具体的集成测试逻辑
        assert container.resolve(EventBus) is event_bus
        assert container.resolve(EnhancedConfigManager) is config_manager
        
        # 清理
        event_bus.shutdown()
        config_manager.shutdown()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])