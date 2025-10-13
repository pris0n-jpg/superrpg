#!/usr/bin/env python3
"""
集成测试套件

整合所有模块的集成测试，包括：
1. 测试模块间依赖关系
2. 测试配置管理系统
3. 测试错误处理和恢复
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

# 导入核心模块
from src.core.container import DIContainer
from src.core.events import EventBus, DomainEvent
from src.core.exceptions import ValidationException, NotFoundException, BusinessRuleException
from src.infrastructure.events.event_bus_impl import InMemoryEventBus
from src.infrastructure.logging.event_logger_impl import EventLoggerImpl

# 导入应用服务
from src.application.services.character_card_service import CharacterCardService
from src.application.services.lorebook_service import LorebookService
from src.application.services.prompt_assembly_service import PromptAssemblyService
from src.application.services.keyword_matcher_service import KeywordMatcherService
from src.application.services.token_counter_service import TokenCounterService

# 导入仓储实现
from src.infrastructure.repositories.character_repository_impl import CharacterRepositoryImpl
from src.infrastructure.repositories.lorebook_repository_impl import LorebookRepositoryImpl, LorebookEntryRepositoryImpl
from src.infrastructure.repositories.prompt_repository_impl import PromptRepositoryImpl

# 导入API网关
from src.adapters.api_gateway import ApiGateway

# 导入领域模型
from src.domain.models.characters import CharacterCard, CharacterCardInfo, Abilities, CharacterStats, Position
from src.domain.models.lorebook import Lorebook, LorebookEntry, KeywordPattern, ActivationRule, ActivationType, KeywordType
from src.domain.models.prompt import PromptTemplate, PromptSection, PromptSectionType

# 导入DTO
from src.domain.dtos.character_card_dtos import CharacterCardCreateDto
from src.domain.dtos.lorebook_dtos import LorebookCreateDto, LorebookEntryCreateDto, LorebookActivationDto
from src.domain.dtos.prompt_dtos import PromptBuildDto, PromptContextDto

# 导入配置管理
from src.infrastructure.config.enhanced_config_manager import EnhancedConfigManager


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config_manager(temp_dir):
    """配置管理器fixture"""
    # 创建测试配置文件
    config_file = temp_dir / "test_config.json"
    test_config = {
        "database": {
            "url": f"sqlite:///{temp_dir}/test.db",
            "echo": False
        },
        "api": {
            "host": "localhost",
            "port": 3010,
            "enable_cors": True,
            "enable_docs": True
        },
        "logging": {
            "level": "INFO",
            "file": str(temp_dir / "test.log")
        },
        "features": {
            "enable_character_cards": True,
            "enable_lorebooks": True,
            "enable_prompts": True
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(test_config, f, ensure_ascii=False, indent=2)
    
    # 创建配置管理器
    config_manager = EnhancedConfigManager()
    config_manager.load_from_file(str(config_file))
    
    return config_manager


@pytest.fixture
def container(config_manager, temp_dir):
    """依赖注入容器fixture"""
    container = DIContainer()
    
    # 注册配置管理器
    container.register_instance(EnhancedConfigManager, config_manager)
    
    # 注册基础设施服务
    event_bus = InMemoryEventBus()
    logger = EventLoggerImpl()
    
    container.register_instance(EventBus, event_bus)
    container.register_instance(type(logger), logger)
    
    # 注册仓储
    character_repo = CharacterRepositoryImpl(storage_path=str(temp_dir / "characters"))
    lorebook_repo = LorebookRepositoryImpl(storage_path=str(temp_dir / "lorebooks"))
    entry_repo = LorebookEntryRepositoryImpl(lorebook_repository=lorebook_repo)
    prompt_repo = PromptRepositoryImpl(storage_path=str(temp_dir / "prompts"), logger=logger)
    
    container.register_instance(CharacterRepositoryImpl, character_repo)
    container.register_instance(LorebookRepositoryImpl, lorebook_repo)
    container.register_instance(LorebookEntryRepositoryImpl, entry_repo)
    container.register_instance(PromptRepositoryImpl, prompt_repo)
    
    # 注册服务
    keyword_matcher = KeywordMatcherService(logger=logger)
    token_counter = TokenCounterService(logger=logger)
    
    container.register_instance(KeywordMatcherService, keyword_matcher)
    container.register_instance(TokenCounterService, token_counter)
    
    # 注册应用服务
    character_service = CharacterCardService(
        character_repository=character_repo,
        logger=logger
    )
    lorebook_service = LorebookService(
        lorebook_repository=lorebook_repo,
        entry_repository=entry_repo,
        keyword_matcher=keyword_matcher,
        logger=logger
    )
    prompt_assembly_service = PromptAssemblyService(
        prompt_repository=prompt_repo,
        token_counter=token_counter,
        logger=logger
    )
    
    container.register_instance(CharacterCardService, character_service)
    container.register_instance(LorebookService, lorebook_service)
    container.register_instance(PromptAssemblyService, prompt_assembly_service)
    
    # 注册API网关
    api_gateway = ApiGateway()
    container.register_instance(ApiGateway, api_gateway)
    
    return container


@pytest.fixture
def sample_integration_data():
    """集成测试数据"""
    return {
        "character": {
            "name": "集成测试角色",
            "description": "用于集成测试的角色",
            "first_message": "你好，我是集成测试角色。",
            "example_messages": ["这是示例消息"],
            "scenario": "测试场景",
            "personality_summary": "测试角色",
            "creator_notes": "集成测试用",
            "tags": ["测试", "集成"],
            "abilities": {
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            },
            "stats": {
                "level": 1,
                "armor_class": 10,
                "proficiency_bonus": 2,
                "speed_steps": 6,
                "reach_steps": 1
            },
            "hp": 10,
            "max_hp": 10,
            "position": {"x": 0, "y": 0},
            "proficient_skills": [],
            "proficient_saves": [],
            "inventory": {}
        },
        "lorebook": {
            "name": "集成测试传说书",
            "description": "用于集成测试的传说书",
            "version": "1.0.0",
            "tags": ["测试", "集成"]
        },
        "lorebook_entry": {
            "title": "测试条目",
            "content": "这是测试条目的内容。",
            "keywords": [
                {"pattern": "测试", "type": "EXACT", "case_sensitive": False, "weight": 10}
            ],
            "activation_rule": {
                "type": "ANY",
                "priority": 1,
                "max_activations": 10,
                "cooldown_seconds": 30
            },
            "tags": ["测试"],
            "metadata": {}
        },
        "prompt_template": {
            "name": "集成测试模板",
            "description": "用于集成测试的提示模板",
            "sections": [
                {
                    "content": "你是{character_name}，{character_description}。",
                    "section_type": "SYSTEM",
                    "priority": 1,
                    "enabled": True
                }
            ],
            "variables": ["character_name", "character_description"],
            "is_active": True
        }
    }


@pytest.mark.asyncio
class TestIntegrationSuite:
    """集成测试套件类"""
    
    async def test_module_dependencies(self, container):
        """测试模块间依赖关系"""
        # 验证容器中的服务依赖关系
        # 1. 验证基础服务存在
        assert container.is_registered(EventBus)
        assert container.is_registered(EventLoggerImpl)
        
        # 2. 验证仓储服务存在
        assert container.is_registered(CharacterRepositoryImpl)
        assert container.is_registered(LorebookRepositoryImpl)
        assert container.is_registered(LorebookEntryRepositoryImpl)
        assert container.is_registered(PromptRepositoryImpl)
        
        # 3. 验证应用服务存在
        assert container.is_registered(CharacterCardService)
        assert container.is_registered(LorebookService)
        assert container.is_registered(PromptAssemblyService)
        
        # 4. 验证服务依赖关系
        # LorebookService依赖KeywordMatcherService和LorebookRepository
        lorebook_service = container.resolve(LorebookService)
        assert hasattr(lorebook_service, '_keyword_matcher')
        assert hasattr(lorebook_service, '_lorebook_repository')
        assert hasattr(lorebook_service, '_entry_repository')
        
        # PromptAssemblyService依赖TokenCounterService和PromptRepository
        prompt_service = container.resolve(PromptAssemblyService)
        assert hasattr(prompt_service, '_token_counter')
        assert hasattr(prompt_service, '_prompt_repository')
        
        # 5. 验证依赖注入的实例是否正确
        keyword_matcher = container.resolve(KeywordMatcherService)
        assert lorebook_service._keyword_matcher is keyword_matcher
        
        token_counter = container.resolve(TokenCounterService)
        assert prompt_service._token_counter is token_counter
        
        # 6. 验证容器依赖验证
        errors = container.validate_dependencies()
        assert len(errors) == 0, f"容器依赖验证失败: {errors}"
    
    async def test_configuration_management(self, config_manager, container):
        """测试配置管理系统"""
        # 1. 验证配置加载
        assert config_manager is not None
        assert config_manager.get("database.url") is not None
        assert config_manager.get("api.host") == "localhost"
        assert config_manager.get("features.enable_character_cards") is True
        
        # 2. 验证配置获取
        db_config = config_manager.get("database")
        assert db_config["url"] is not None
        assert db_config["echo"] is False
        
        api_config = config_manager.get("api")
        assert api_config["port"] == 3010
        assert api_config["enable_cors"] is True
        
        # 3. 验证配置更新
        original_port = config_manager.get("api.port")
        config_manager.set("api.port", 9000)
        assert config_manager.get("api.port") == 9000
        
        # 恢复原始配置
        config_manager.set("api.port", original_port)
        assert config_manager.get("api.port") == original_port
        
        # 4. 验证配置保存和加载
        config_file = Path(config_manager._config_file) if hasattr(config_manager, '_config_file') else None
        if config_file and config_file.exists():
            # 创建新的配置管理器实例并加载相同文件
            new_config_manager = EnhancedConfigManager()
            new_config_manager.load_from_file(str(config_file))
            
            # 验证配置是否正确加载
            assert new_config_manager.get("api.host") == config_manager.get("api.host")
            assert new_config_manager.get("features.enable_character_cards") == config_manager.get("features.enable_character_cards")
        
        # 5. 验证配置在服务中的使用
        # 某些服务可能会使用配置，这里我们验证配置管理器在容器中是否正确注册
        registered_config = container.resolve(EnhancedConfigManager)
        assert registered_config is config_manager
    
    async def test_cross_module_data_flow(self, container, sample_integration_data):
        """测试跨模块数据流"""
        # 1. 创建角色卡
        character_service = container.resolve(CharacterCardService)
        character_dto = character_service.create_character_card(
            CharacterCardCreateDto(**sample_integration_data["character"])
        )
        
        # 2. 创建传说书并添加条目
        lorebook_service = container.resolve(LorebookService)
        lorebook_dto = lorebook_service.create_lorebook(
            LorebookCreateDto(**sample_integration_data["lorebook"])
        )
        
        entry_dto = lorebook_service.create_entry(
            lorebook_dto.id,
            LorebookEntryCreateDto(**sample_integration_data["lorebook_entry"])
        )
        
        # 3. 创建提示模板
        prompt_service = container.resolve(PromptAssemblyService)
        template_data = sample_integration_data["prompt_template"]
        
        template = PromptTemplate(
            name=template_data["name"],
            description=template_data["description"],
            sections=[
                PromptSection(
                    content=section["content"],
                    section_type=PromptSectionType(section["section_type"]),
                    priority=section["priority"],
                    enabled=section["enabled"]
                )
                for section in template_data["sections"]
            ],
            variables=set(template_data["variables"]),
            is_active=template_data["is_active"]
        )
        
        prompt_repo = container.resolve(PromptRepositoryImpl)
        prompt_repo.save(template)
        
        # 4. 测试数据流：角色卡 -> 传说书 -> 提示
        # 激活传说书条目
        activation_dto = LorebookActivationDto(
            text=f"请介绍一下{character_dto.name}",
            context={"character_id": character_dto.id},
            max_entries=5
        )
        activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
        
        # 构建提示，使用角色信息和传说书内容
        context_dto = PromptContextDto(
            character_name=character_dto.name,
            character_description=character_dto.description,
            world_info="测试世界",
            chat_history=[],
            current_input="介绍角色",
            variables={
                "character_name": character_dto.name,
                "character_description": character_dto.description
            },
            metadata={"lorebook_entries": [entry.to_dict() for entry in activation_result.activated_entries]}
        )
        
        build_dto = PromptBuildDto(
            template_id=str(template.id),
            context=context_dto,
            token_limit={
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "max_tokens": 2048,
                "reserved_tokens": 256
            },
            truncation_strategy="SMART"
        )
        
        prompt_preview = prompt_service.build_prompt(build_dto)
        
        # 5. 验证数据流正确性
        assert character_dto.id is not None
        assert lorebook_dto.id is not None
        assert entry_dto.id is not None
        assert template.id is not None
        
        # 验证提示中包含角色信息
        assert character_dto.name in prompt_preview.prompt
        assert character_dto.description in prompt_preview.prompt
        
        # 验证提示构建成功
        assert prompt_preview.prompt is not None
        assert prompt_preview.token_count > 0
        
        # 6. 验证跨模块引用
        # 通过角色ID可以获取角色信息
        retrieved_character = character_service.get_character_card(character_dto.id)
        assert retrieved_character.id == character_dto.id
        
        # 通过传说书ID可以获取传说书信息
        retrieved_lorebook = lorebook_service.get_lorebook(lorebook_dto.id)
        assert retrieved_lorebook.id == lorebook_dto.id
        
        # 通过条目ID可以获取条目信息
        retrieved_entry = lorebook_service.get_entry(lorebook_dto.id, entry_dto.id)
        assert retrieved_entry.id == entry_dto.id
    
    async def test_error_handling_and_recovery(self, container, sample_integration_data):
        """测试错误处理和恢复"""
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        
        # 1. 测试验证错误
        invalid_character_data = sample_integration_data["character"].copy()
        invalid_character_data["name"] = ""  # 无效的空名称
        
        with pytest.raises(ValidationException) as exc_info:
            character_service.create_character_card(CharacterCardCreateDto(**invalid_character_data))
        
        assert "角色名称" in str(exc_info.value)
        
        # 2. 测试未找到错误
        with pytest.raises(NotFoundException) as exc_info:
            character_service.get_character_card("nonexistent_id")
        
        assert "不存在" in str(exc_info.value)
        
        # 3. 测试业务规则错误
        # 创建角色卡
        character_dto = character_service.create_character_card(
            CharacterCardCreateDto(**sample_integration_data["character"])
        )
        
        # 尝试创建同名的角色卡
        with pytest.raises(Exception) as exc_info:  # 可能是DuplicateException或BusinessRuleException
            character_service.create_character_card(
                CharacterCardCreateDto(**sample_integration_data["character"])
            )
        
        assert "已存在" in str(exc_info.value)
        
        # 4. 测试错误恢复
        # 创建有效的角色卡
        valid_character_data = sample_integration_data["character"].copy()
        valid_character_data["name"] = "恢复测试角色"
        
        recovered_character = character_service.create_character_card(
            CharacterCardCreateDto(**valid_character_data)
        )
        
        assert recovered_character.name == "恢复测试角色"
        assert recovered_character.id is not None
        
        # 5. 测试部分失败场景
        # 创建传说书
        lorebook_dto = lorebook_service.create_lorebook(
            LorebookCreateDto(**sample_integration_data["lorebook"])
        )
        
        # 添加有效条目
        valid_entry_data = sample_integration_data["lorebook_entry"].copy()
        valid_entry_data["title"] = "有效条目"
        entry_dto = lorebook_service.create_entry(lorebook_dto.id, LorebookEntryCreateDto(**valid_entry_data))
        
        assert entry_dto.id is not None
        
        # 尝试激活不存在的条目（应该能处理错误）
        activation_dto = LorebookActivationDto(
            text="测试激活",
            context={},
            max_entries=5
        )
        
        # 这应该不会抛出异常，即使没有匹配的条目
        activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
        assert isinstance(activation_result.activated_entries, list)
        
        # 6. 测试资源清理和恢复
        # 删除创建的资源
        delete_result = character_service.delete_character_card(character_dto.id)
        assert delete_result is True
        
        recovered_delete_result = character_service.delete_character_card(recovered_character.id)
        assert recovered_delete_result is True
        
        lorebook_delete_result = lorebook_service.delete_lorebook(lorebook_dto.id)
        assert lorebook_delete_result is True
        
        # 验证资源已被删除
        with pytest.raises(NotFoundException):
            character_service.get_character_card(character_dto.id)
        
        with pytest.raises(NotFoundException):
            character_service.get_character_card(recovered_character.id)
    
    async def test_concurrent_operations(self, container, sample_integration_data):
        """测试并发操作"""
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        
        # 1. 并发创建角色卡
        async def create_character(index: int):
            character_data = sample_integration_data["character"].copy()
            character_data["name"] = f"并发角色{index:04d}"
            return character_service.create_character_card(CharacterCardCreateDto(**character_data))
        
        # 创建10个角色卡
        character_tasks = [create_character(i) for i in range(10)]
        character_dtos = await asyncio.gather(*character_tasks)
        
        assert len(character_dtos) == 10
        assert all(dto.name.startswith("并发角色") for dto in character_dtos)
        
        # 2. 并发查询角色卡
        async def get_character(character_id: str):
            return character_service.get_character_card(character_id)
        
        query_tasks = [get_character(dto.id) for dto in character_dtos]
        queried_dtos = await asyncio.gather(*query_tasks)
        
        assert len(queried_dtos) == 10
        assert all(dto.id in [q.id for q in queried_dtos] for dto in character_dtos)
        
        # 3. 并发创建传说书和条目
        async def create_lorebook_with_entry(index: int):
            lorebook_data = sample_integration_data["lorebook"].copy()
            lorebook_data["name"] = f"并发传说书{index:04d}"
            lorebook_dto = lorebook_service.create_lorebook(LorebookCreateDto(**lorebook_data))
            
            entry_data = sample_integration_data["lorebook_entry"].copy()
            entry_data["title"] = f"并发条目{index:04d}"
            entry_dto = lorebook_service.create_entry(lorebook_dto.id, LorebookEntryCreateDto(**entry_data))
            
            return lorebook_dto, entry_dto
        
        lorebook_tasks = [create_lorebook_with_entry(i) for i in range(5)]
        lorebook_results = await asyncio.gather(*lorebook_tasks)
        
        assert len(lorebook_results) == 5
        assert all(result[0].name.startswith("并发传说书") for result in lorebook_results)
        assert all(result[1].title.startswith("并发条目") for result in lorebook_results)
        
        # 4. 并发激活条目
        async def activate_entries(lorebook_id: str, entry_id: str):
            activation_dto = LorebookActivationDto(
                text="并发激活测试",
                context={"concurrent": True},
                max_entries=5
            )
            return lorebook_service.activate_entries(lorebook_id, activation_dto)
        
        activation_tasks = [
            activate_entries(result[0].id, result[1].id) 
            for result in lorebook_results
        ]
        activation_results = await asyncio.gather(*activation_tasks)
        
        assert len(activation_results) == 5
        assert all(isinstance(result.activated_entries, list) for result in activation_results)
        
        # 5. 清理并发创建的资源
        cleanup_tasks = []
        
        # 清理角色卡
        for dto in character_dtos:
            cleanup_tasks.append(character_service.delete_character_card(dto.id))
        
        # 清理传说书
        for lorebook_dto, _ in lorebook_results:
            cleanup_tasks.append(lorebook_service.delete_lorebook(lorebook_dto.id))
        
        cleanup_results = await asyncio.gather(*cleanup_tasks)
        assert all(cleanup_results)  # 所有删除操作都应该成功
    
    async def test_system_integration_scenarios(self, container, sample_integration_data):
        """测试系统集成场景"""
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        prompt_service = container.resolve(PromptAssemblyService)
        api_gateway = container.resolve(ApiGateway)
        event_bus = container.resolve(EventBus)
        
        # 场景1：角色创建 -> 传说书关联 -> API暴露
        # 1. 创建角色
        character_dto = character_service.create_character_card(
            CharacterCardCreateDto(**sample_integration_data["character"])
        )
        
        # 2. 创建角色相关的传说书
        lorebook_data = sample_integration_data["lorebook"].copy()
        lorebook_data["name"] = f"{character_dto.name}的传说书"
        lorebook_data["description"] = f"关于{character_dto.name}的详细信息"
        lorebook_dto = lorebook_service.create_lorebook(LorebookCreateDto(**lorebook_data))
        
        # 3. 添加角色相关条目
        entry_data = sample_integration_data["lorebook_entry"].copy()
        entry_data["title"] = f"{character_dto.name}的背景"
        entry_data["content"] = f"{character_dto.name}是一位{character_dto.description[:50]}..."
        entry_dto = lorebook_service.create_entry(lorebook_dto.id, LorebookEntryCreateDto(**entry_data))
        
        # 4. 创建API路由
        async def character_profile_handler(id, **kwargs):
            if id == character_dto.id:
                # 获取角色信息
                character = character_service.get_character_card(id)
                
                # 获取相关传说书条目
                activation_dto = LorebookActivationDto(
                    text=f"介绍{character.name}",
                    context={"character_id": id},
                    max_entries=3
                )
                activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
                
                return {
                    "character": character.to_dict(),
                    "lorebook_entries": [entry.to_dict() for entry in activation_result.activated_entries]
                }
            else:
                return {"error": "Character not found"}
        
        api_gateway.add_route(f"/characters/{character_dto.id}/profile", "GET", character_profile_handler)
        
        # 5. 测试API调用
        response = await api_gateway.handle_request("GET", f"/characters/{character_dto.id}/profile")
        assert response.status_code == 200
        assert response.body["character"]["name"] == character_dto.name
        
        # 场景2：事件驱动的系统集成
        # 1. 创建事件监听器
        events_received = []
        
        async def character_created_handler(event):
            events_received.append(("character_created", event.data))
        
        async def lorebook_created_handler(event):
            events_received.append(("lorebook_created", event.data))
        
        # 2. 订阅事件
        event_bus.subscribe("character_created", character_created_handler)
        event_bus.subscribe("lorebook_created", lorebook_created_handler)
        
        # 3. 创建新角色（触发事件）
        new_character_data = sample_integration_data["character"].copy()
        new_character_data["name"] = "事件测试角色"
        new_character_dto = character_service.create_character_card(
            CharacterCardCreateDto(**new_character_data)
        )
        
        # 4. 创建新传说书（触发事件）
        new_lorebook_data = sample_integration_data["lorebook"].copy()
        new_lorebook_data["name"] = "事件测试传说书"
        new_lorebook_dto = lorebook_service.create_lorebook(LorebookCreateDto(**new_lorebook_data))
        
        # 5. 等待事件处理
        await asyncio.sleep(0.1)  # 给事件处理一些时间
        
        # 6. 验证事件
        event_types = [event_type for event_type, _ in events_received]
        assert "character_created" in event_types
        assert "lorebook_created" in event_types
        
        # 场景3：数据一致性验证
        # 1. 更新角色信息
        updated_character = character_service.update_character_card(
            character_dto.id,
            {"description": "更新后的角色描述"}
        )
        
        # 2. 验证更新是否生效
        assert updated_character.description == "更新后的角色描述"
        
        # 3. 重新获取角色信息验证一致性
        retrieved_character = character_service.get_character_card(character_dto.id)
        assert retrieved_character.description == "更新后的角色描述"
        assert retrieved_character.id == character_dto.id
        
        # 4. 验证传说书条目是否仍然关联
        activation_dto = LorebookActivationDto(
            text=f"介绍{character_dto.name}",
            context={"character_id": character_dto.id},
            max_entries=3
        )
        activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
        assert len(activation_result.activated_entries) > 0
        
        # 5. 验证API路由仍然有效
        response = await api_gateway.handle_request("GET", f"/characters/{character_dto.id}/profile")
        assert response.status_code == 200
        assert response.body["character"]["description"] == "更新后的角色描述"
        
        # 场景4：错误恢复和系统韧性
        # 1. 模拟部分服务失败
        with patch.object(character_service, 'get_character_card', side_effect=Exception("模拟服务失败")):
            # API应该能够处理服务失败
            response = await api_gateway.handle_request("GET", f"/characters/{character_dto.id}/profile")
            # 根据API网关的错误处理策略，这里可能返回500错误或其他错误响应
            assert response.status_code != 200
        
        # 2. 恢复服务后应该能正常工作
        response = await api_gateway.handle_request("GET", f"/characters/{character_dto.id}/profile")
        assert response.status_code == 200
        
        # 场景5：资源清理
        # 1. 删除API路由
        # 注意：当前API网关实现可能不支持路由删除，这里只是示例
        api_gateway.routes = [route for route in api_gateway.routes
                             if not route.path.endswith(f"/{character_dto.id}/profile")]
        
        # 2. 删除测试数据
        character_service.delete_character_card(character_dto.id)
        character_service.delete_character_card(new_character_dto.id)
        lorebook_service.delete_lorebook(lorebook_dto.id)
        lorebook_service.delete_lorebook(new_lorebook_dto.id)
        
        # 3. 验证资源已清理
        with pytest.raises(Exception):
            character_service.get_character_card(character_dto.id)
        
        with pytest.raises(Exception):
            lorebook_service.get_lorebook(lorebook_dto.id)
    
    async def test_configuration_driven_behavior(self, container, config_manager):
        """测试配置驱动的行为"""
        # 1. 测试功能开关
        # 禁用角色卡功能
        config_manager.set("features.enable_character_cards", False)
        
        # 验证功能是否被禁用（这里需要根据实际实现来验证）
        # 例如，某些服务可能会检查配置并拒绝操作
        
        # 重新启用角色卡功能
        config_manager.set("features.enable_character_cards", True)
        
        # 2. 测试配置更新
        original_port = config_manager.get("api.port")
        new_port = original_port + 1
        
        config_manager.set("api.port", new_port)
        assert config_manager.get("api.port") == new_port
        
        # 恢复原始配置
        config_manager.set("api.port", original_port)
        
        # 3. 测试配置验证
        # 设置无效配置
        with pytest.raises(Exception):
            config_manager.set("api.port", "invalid_port")
        
        # 4. 测试配置持久化
        if hasattr(config_manager, 'save'):
            config_manager.save()
            # 重新加载配置验证持久化
            config_manager.load_from_file(config_manager._config_file)
            assert config_manager.get("api.port") == original_port
    
    async def test_service_lifecycle(self, container):
        """测试服务生命周期"""
        # 1. 测试服务初始化
        # 所有服务应该已经正确初始化
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        prompt_service = container.resolve(PromptAssemblyService)
        
        assert character_service is not None
        assert lorebook_service is not None
        assert prompt_service is not None
        
        # 2. 测试服务状态
        # 服务应该处于可用状态
        # 这里可以根据实际实现添加状态检查
        
        # 3. 测试服务重启/恢复
        # 模拟服务重启场景
        # 在实际实现中，可能需要更复杂的生命周期管理
        
        # 4. 测试资源清理
        # 清理容器中的服务
        container.clear_scope()
        
        # 验证清理效果
        # 单例服务应该仍然可用
        event_bus = container.resolve(EventBus)
        assert event_bus is not None
        
        # 作用域服务应该被清理
        # 这里可以根据实际实现添加验证


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])