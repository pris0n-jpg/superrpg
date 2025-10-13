#!/usr/bin/env python3
"""
端到端工作流测试

测试完整的系统工作流，包括：
1. 角色卡创建和使用流程
2. 传说书条目创建和激活流程
3. 提示组装和生成流程
4. API网关路由和中间件
5. 扩展系统加载和执行
6. 事件总线发布和订阅
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# 导入核心模块
from src.core.container import DIContainer
from src.core.events import EventBus, DomainEvent
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
from src.adapters.api_gateway import ApiGateway, Route

# 导入领域模型
from src.domain.models.characters import CharacterCard, CharacterCardInfo, Abilities, CharacterStats, Position
from src.domain.models.lorebook import Lorebook, LorebookEntry, KeywordPattern, ActivationRule, ActivationType, KeywordType
from src.domain.models.prompt import PromptTemplate, PromptSection, PromptSectionType

# 导入DTO
from src.domain.dtos.character_card_dtos import CharacterCardCreateDto
from src.domain.dtos.lorebook_dtos import LorebookCreateDto, LorebookEntryCreateDto, LorebookActivationDto
from src.domain.dtos.prompt_dtos import PromptBuildDto, PromptContextDto


@pytest.fixture
def temp_dir():
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def container(temp_dir):
    """依赖注入容器fixture"""
    container = DIContainer()
    
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
def sample_character_data():
    """示例角色数据"""
    return {
        "name": "艾莉娅·星辰使者",
        "description": "一位年轻的精灵法师，擅长星辰魔法和古代符文。她有着银色的长发和深邃的紫色眼眸，总是穿着绣有星辰图案的蓝色长袍。",
        "first_message": "*艾莉娅从古老的星图中抬起头，紫色的眼眸中闪烁着智慧的光芒* 你好，旅行者。我是艾莉娅，星辰的守护者。你寻找什么样的知识？",
        "example_messages": [
            "*艾莉娅的手指在空中划过，留下银色的光痕* 看那颗星星，它在预示着什么..."
        ],
        "scenario": "在一座古老的观星塔中，星光透过穹顶照在艾莉娅身上。周围堆满了古籍、星盘和各种神秘仪器。",
        "personality_summary": "智慧、神秘、优雅、博学",
        "creator_notes": "角色基于经典的精灵法师形象，但加入了星辰魔法的特色",
        "tags": ["精灵", "法师", "星辰", "神秘"],
        "abilities": {
            "strength": 8,
            "dexterity": 14,
            "constitution": 12,
            "intelligence": 18,
            "wisdom": 16,
            "charisma": 14
        },
        "stats": {
            "level": 5,
            "armor_class": 12,
            "proficiency_bonus": 3,
            "speed_steps": 6,
            "reach_steps": 1
        },
        "hp": 38,
        "max_hp": 38,
        "position": {"x": 5, "y": 8},
        "proficient_skills": ["arcana", "history", "investigation", "perception"],
        "proficient_saves": ["INT", "WIS"],
        "inventory": {
            "法术书": 1,
            "星盘": 1,
            "魔法杖": 1,
            "魔法药水": 3
        }
    }


@pytest.fixture
def sample_lorebook_data():
    """示例传说书数据"""
    return {
        "name": "星辰魔法体系",
        "description": "关于星辰魔法的知识体系，包括咒语、仪式和历史背景",
        "version": "1.0.0",
        "tags": ["魔法", "星辰", "知识"]
    }


@pytest.fixture
def sample_lorebook_entry_data():
    """示例传说书条目数据"""
    return {
        "title": "星光治疗术",
        "content": "星光治疗术是一种基础但有效的治疗法术，通过引导星光能量来修复伤口。施法者需要在夜空下，伸出手掌集中精神，感受星光的温暖。咒语为：'星光如水，治愈如泉'。",
        "keywords": [
            {
                "pattern": "治疗",
                "type": "EXACT",
                "case_sensitive": False,
                "weight": 10
            },
            {
                "pattern": "星光",
                "type": "EXACT",
                "case_sensitive": False,
                "weight": 8
            },
            {
                "pattern": "伤口",
                "type": "EXACT",
                "case_sensitive": False,
                "weight": 5
            }
        ],
        "activation_rule": {
            "type": "ANY",
            "priority": 1,
            "max_activations": 3,
            "cooldown_seconds": 60
        },
        "tags": ["法术", "治疗", "星光"],
        "metadata": {
            "difficulty": "初级",
            "mana_cost": "低",
            "casting_time": "10分钟"
        }
    }


@pytest.fixture
def sample_prompt_template_data():
    """示例提示模板数据"""
    return {
        "name": "角色对话模板",
        "description": "用于生成角色对话的提示模板",
        "sections": [
            {
                "content": "你是{character_name}，{character_description}。",
                "section_type": "SYSTEM",
                "priority": 1,
                "enabled": True
            },
            {
                "content": "当前场景：{scenario}",
                "section_type": "CONTEXT",
                "priority": 2,
                "enabled": True
            },
            {
                "content": "最近的对话历史：{chat_history}",
                "section_type": "HISTORY",
                "priority": 3,
                "enabled": True
            },
            {
                "content": "当前输入：{current_input}",
                "section_type": "INPUT",
                "priority": 4,
                "enabled": True
            }
        ],
        "variables": ["character_name", "character_description", "scenario", "chat_history", "current_input"],
        "is_active": True
    }


@pytest.mark.asyncio
class TestE2EWorkflow:
    """端到端工作流测试类"""
    
    async def test_complete_character_card_workflow(self, container, sample_character_data):
        """测试完整的角色卡创建和使用流程"""
        # 获取服务
        character_service = container.resolve(CharacterCardService)
        
        # 1. 创建角色卡
        create_dto = CharacterCardCreateDto(**sample_character_data)
        character_dto = character_service.create_character_card(create_dto)
        
        assert character_dto.name == sample_character_data["name"]
        assert character_dto.description == sample_character_data["description"]
        assert character_dto.abilities["intelligence"] == 18
        
        # 2. 获取角色卡详情
        retrieved_character = character_service.get_character_card(character_dto.id)
        assert retrieved_character.id == character_dto.id
        assert retrieved_character.name == character_dto.name
        
        # 3. 更新角色卡
        update_data = {
            "hp": 30,
            "description": "更新后的描述：艾莉娅在最近的冒险中受伤了，但依然保持着优雅和智慧。"
        }
        updated_character = character_service.update_character_card(character_dto.id, update_data)
        assert updated_character.hp == 30
        assert "受伤了" in updated_character.description
        
        # 4. 导出角色卡
        exported_character = character_service.export_character_card(character_dto.id, "json")
        assert exported_character.format == "json"
        assert "艾莉娅" in exported_character.filename
        
        # 5. 删除角色卡
        delete_result = character_service.delete_character_card(character_dto.id)
        assert delete_result is True
        
        # 6. 验证删除
        with pytest.raises(Exception):  # 应该抛出NotFoundException
            character_service.get_character_card(character_dto.id)
    
    async def test_complete_lorebook_workflow(self, container, sample_lorebook_data, sample_lorebook_entry_data):
        """测试完整的传说书创建和激活流程"""
        # 获取服务
        lorebook_service = container.resolve(LorebookService)
        
        # 1. 创建传说书
        create_lorebook_dto = LorebookCreateDto(**sample_lorebook_data)
        lorebook_dto = lorebook_service.create_lorebook(create_lorebook_dto)
        
        assert lorebook_dto.name == sample_lorebook_data["name"]
        assert lorebook_dto.description == sample_lorebook_data["description"]
        
        # 2. 创建条目
        create_entry_dto = LorebookEntryCreateDto(**sample_lorebook_entry_data)
        entry_dto = lorebook_service.create_entry(lorebook_dto.id, create_entry_dto)
        
        assert entry_dto.title == sample_lorebook_entry_data["title"]
        assert len(entry_dto.keywords) == 3
        
        # 3. 激活条目
        activation_dto = LorebookActivationDto(
            text="我需要治疗我的伤口，有什么星光法术可以帮助吗？",
            context={"character": "艾莉娅", "location": "观星塔"},
            max_entries=5
        )
        activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
        
        assert len(activation_result.activated_entries) > 0
        assert "星光治疗术" in [entry.title for entry in activation_result.activated_entries]
        
        # 4. 获取传说书统计信息
        stats = lorebook_service.get_lorebook_statistics(lorebook_dto.id)
        assert stats.total_entries == 1
        assert stats.total_activations >= 1
        
        # 5. 导出传说书
        exported_lorebook = lorebook_service.export_lorebook(lorebook_dto.id, "json")
        assert exported_lorebook.format == "json"
        assert "星辰魔法体系" in exported_lorebook.filename
    
    async def test_complete_prompt_assembly_workflow(self, container, sample_prompt_template_data, sample_character_data):
        """测试完整的提示组装和生成流程"""
        # 获取服务
        prompt_service = container.resolve(PromptAssemblyService)
        
        # 1. 创建提示模板
        template_data = sample_prompt_template_data.copy()
        prompt_template = PromptTemplate(
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
        
        # 保存模板到仓储
        prompt_repo = container.resolve(PromptRepositoryImpl)
        prompt_repo.save(prompt_template)
        
        # 2. 创建提示上下文
        context_dto = PromptContextDto(
            character_name=sample_character_data["name"],
            character_description=sample_character_data["description"],
            world_info="这是一个充满魔法的世界，星辰之力影响着一切。",
            chat_history=[
                {"role": "user", "content": "你好，艾莉娅"},
                {"role": "assistant", "content": "你好，旅行者。我是艾莉娅，星辰的守护者。"}
            ],
            current_input="你能教我一些星光魔法吗？",
            variables={"time": "夜晚", "location": "观星塔"},
            metadata={"mood": "好奇"}
        )
        
        # 3. 构建提示
        build_dto = PromptBuildDto(
            template_id=str(prompt_template.id),
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
        
        assert prompt_preview.prompt is not None
        assert prompt_preview.token_count > 0
        assert sample_character_data["name"] in prompt_preview.prompt
        assert "你能教我一些星光魔法吗？" in prompt_preview.prompt
        
        # 4. 计算token数量
        token_calculation = prompt_service.calculate_tokens(str(prompt_template.id), context_dto)
        assert token_calculation["total_tokens"] > 0
        assert "tokens_by_section" in token_calculation
        
        # 5. 验证token限制
        token_validation = prompt_service.validate_token_limit(
            str(prompt_template.id), 
            context_dto,
            "openai",
            "gpt-3.5-turbo"
        )
        assert "is_over_limit" in token_validation
        assert "current_tokens" in token_validation
        assert "max_tokens" in token_validation
    
    async def test_api_gateway_routing_and_middleware(self, container):
        """测试API网关路由和中间件"""
        # 获取API网关
        api_gateway = container.resolve(ApiGateway)
        
        # 1. 注册路由
        async def health_handler(**kwargs):
            return {"status": "healthy", "service": "SuperRPG"}
        
        async def character_list_handler(**kwargs):
            return {
                "characters": [
                    {"name": "艾莉娅", "class": "法师"},
                    {"name": "索林", "class": "战士"}
                ]
            }
        
        async def character_detail_handler(id, **kwargs):
            if id == "1":
                return {"name": "艾莉娅", "class": "法师", "level": 5}
            else:
                return {"error": "Character not found"}
        
        # 添加路由
        api_gateway.add_route("/health", "GET", health_handler, name="health_check")
        api_gateway.add_route("/characters", "GET", character_list_handler, name="character_list")
        api_gateway.add_route("/characters/{id}", "GET", character_detail_handler, name="character_detail")
        
        # 2. 测试路由匹配
        health_route = api_gateway.get_route_by_name("health_check")
        assert health_route is not None
        assert health_route.path == "/health"
        assert health_route.method == "GET"
        
        # 3. 测试请求处理
        health_response = await api_gateway.handle_request("GET", "/health")
        assert health_response.status_code == 200
        assert health_response.body["status"] == "healthy"
        
        characters_response = await api_gateway.handle_request("GET", "/characters")
        assert characters_response.status_code == 200
        assert len(characters_response.body["characters"]) == 2
        
        character_detail_response = await api_gateway.handle_request("GET", "/characters/1")
        assert character_detail_response.status_code == 200
        assert character_detail_response.body["name"] == "艾莉娅"
        
        # 4. 测试404错误
        not_found_response = await api_gateway.handle_request("GET", "/nonexistent")
        assert not_found_response.status_code == 404
        
        # 5. 测试路由信息获取
        routes_info = api_gateway.get_routes_info()
        assert len(routes_info) >= 3
        route_paths = [route["path"] for route in routes_info]
        assert "/health" in route_paths
        assert "/characters" in route_paths
        assert "/characters/{id}" in route_paths
        
        # 6. 测试统计信息
        stats = api_gateway.get_stats()
        assert stats["total_requests"] >= 5  # 至少5个请求
        assert stats["successful_requests"] >= 4  # 至少4个成功请求
        assert stats["routes_count"] >= 3  # 至少3个路由
    
    async def test_event_bus_publish_and_subscribe(self, container):
        """测试事件总线发布和订阅"""
        # 获取事件总线
        event_bus = container.resolve(EventBus)
        
        # 1. 创建事件监听器
        received_events = []
        
        async def event_handler(event):
            received_events.append(event)
        
        # 2. 订阅事件
        event_bus.subscribe("character_created", event_handler)
        event_bus.subscribe("character_updated", event_handler)
        
        # 3. 发布事件
        from src.domain.models.characters import CharacterDomainEvent
        
        created_event = CharacterDomainEvent("character_created", {
            "character_name": "艾莉娅",
            "character_class": "法师"
        })
        
        updated_event = CharacterDomainEvent("character_updated", {
            "character_name": "艾莉娅",
            "hp": 30
        })
        
        await event_bus.publish(created_event)
        await event_bus.publish(updated_event)
        
        # 4. 验证事件接收
        assert len(received_events) == 2
        assert received_events[0].get_event_type() == "character_created"
        assert received_events[0].data["character_name"] == "艾莉娅"
        assert received_events[1].get_event_type() == "character_updated"
        assert received_events[1].data["hp"] == 30
    
    async def test_integration_workflow_all_components(self, container, sample_character_data, sample_lorebook_data):
        """测试所有组件集成的完整工作流"""
        # 获取所有服务
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        prompt_service = container.resolve(PromptAssemblyService)
        api_gateway = container.resolve(ApiGateway)
        event_bus = container.resolve(EventBus)
        
        # 1. 创建角色卡
        create_dto = CharacterCardCreateDto(**sample_character_data)
        character_dto = character_service.create_character_card(create_dto)
        
        # 2. 创建传说书
        create_lorebook_dto = LorebookCreateDto(**sample_lorebook_data)
        lorebook_dto = lorebook_service.create_lorebook(create_lorebook_dto)
        
        # 3. 添加传说书条目
        entry_data = {
            "title": "角色介绍",
            "content": f"{character_dto.name}是一位神秘的{character_dto.description[:50]}...",
            "keywords": [
                {"pattern": character_dto.name, "type": "EXACT", "case_sensitive": False, "weight": 10},
                {"pattern": "角色", "type": "EXACT", "case_sensitive": False, "weight": 5}
            ],
            "activation_rule": {
                "type": "ANY",
                "priority": 1,
                "max_activations": 10,
                "cooldown_seconds": 30
            },
            "tags": ["角色", "介绍"],
            "metadata": {"source": "character_card"}
        }
        
        create_entry_dto = LorebookEntryCreateDto(**entry_data)
        entry_dto = lorebook_service.create_entry(lorebook_dto.id, create_entry_dto)
        
        # 4. 激活传说书条目
        activation_dto = LorebookActivationDto(
            text=f"请介绍一下{character_dto.name}",
            context={"request_type": "character_info"},
            max_entries=3
        )
        activation_result = lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
        
        # 5. 创建API路由
        async def character_info_handler(**kwargs):
            return {
                "character": character_dto.to_dict(),
                "lorebook_entries": [entry.to_dict() for entry in activation_result.activated_entries]
            }
        
        api_gateway.add_route("/character-info", "GET", character_info_handler, name="character_info")
        
        # 6. 测试API调用
        response = await api_gateway.handle_request("GET", "/character-info")
        assert response.status_code == 200
        assert response.body["character"]["name"] == character_dto.name
        assert len(response.body["lorebook_entries"]) > 0
        
        # 7. 发布领域事件
        from src.domain.models.characters import CharacterDomainEvent
        
        integration_event = CharacterDomainEvent("integration_test_completed", {
            "character_id": character_dto.id,
            "lorebook_id": lorebook_dto.id,
            "entry_id": entry_dto.id,
            "api_route": "/character-info"
        })
        
        await event_bus.publish(integration_event)
        
        # 8. 验证所有组件协同工作
        assert character_dto.id is not None
        assert lorebook_dto.id is not None
        assert entry_dto.id is not None
        assert len(activation_result.activated_entries) > 0
        assert response.status_code == 200
        
        # 9. 验证API网关统计
        stats = api_gateway.get_stats()
        assert stats["total_requests"] > 0
        assert stats["successful_requests"] > 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])