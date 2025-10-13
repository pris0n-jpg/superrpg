#!/usr/bin/env python3
"""
SuperRPG 演示应用

展示所有核心功能的完整演示，包括：
1. 角色卡创建和管理
2. 传说书创建和激活
3. 提示组装和生成
4. API网关路由和中间件
5. 事件总线发布和订阅

提供交互式命令行界面，演示API调用和响应。
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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
from src.adapters.api_gateway import ApiGateway

# 导入领域模型
from src.domain.models.characters import CharacterCard, CharacterCardInfo, Abilities, CharacterStats, Position
from src.domain.models.lorebook import Lorebook, LorebookEntry, KeywordPattern, ActivationRule, ActivationType, KeywordType
from src.domain.models.prompt import PromptTemplate, PromptSection, PromptSectionType

# 导入DTO
from src.domain.dtos.character_card_dtos import CharacterCardCreateDto
from src.domain.dtos.lorebook_dtos import LorebookCreateDto, LorebookEntryCreateDto, LorebookActivationDto
from src.domain.dtos.prompt_dtos import PromptBuildDto, PromptContextDto


class DemoApplication:
    """演示应用类"""
    
    def __init__(self):
        """初始化演示应用"""
        self.container = DIContainer()
        self.event_bus = None
        self.logger = None
        self.character_service = None
        self.lorebook_service = None
        self.prompt_service = None
        self.api_gateway = None
        self.demo_data_dir = Path(__file__).parent.parent.parent / "demo_data"
        self.characters = {}
        self.lorebooks = {}
        self.templates = {}
        self.running = True
        
    async def initialize(self):
        """初始化应用"""
        print("=" * 80)
        print("SuperRPG 演示应用初始化中...")
        print("=" * 80)
        
        # 确保演示数据目录存在
        self.demo_data_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (self.demo_data_dir / "characters").mkdir(exist_ok=True)
        (self.demo_data_dir / "lorebooks").mkdir(exist_ok=True)
        (self.demo_data_dir / "templates").mkdir(exist_ok=True)
        (self.demo_data_dir / "configs").mkdir(exist_ok=True)
        
        # 注册基础设施服务
        self.event_bus = InMemoryEventBus()
        self.logger = EventLoggerImpl()
        
        self.container.register_instance(EventBus, self.event_bus)
        self.container.register_instance(type(self.logger), self.logger)
        
        # 注册仓储
        character_repo = CharacterRepositoryImpl(storage_path=str(self.demo_data_dir / "characters"))
        lorebook_repo = LorebookRepositoryImpl(storage_path=str(self.demo_data_dir / "lorebooks"))
        entry_repo = LorebookEntryRepositoryImpl(lorebook_repository=lorebook_repo)
        prompt_repo = PromptRepositoryImpl(storage_path=str(self.demo_data_dir / "templates"), logger=self.logger)
        
        self.container.register_instance(CharacterRepositoryImpl, character_repo)
        self.container.register_instance(LorebookRepositoryImpl, lorebook_repo)
        self.container.register_instance(LorebookEntryRepositoryImpl, entry_repo)
        self.container.register_instance(PromptRepositoryImpl, prompt_repo)
        
        # 注册服务
        keyword_matcher = KeywordMatcherService(logger=self.logger)
        token_counter = TokenCounterService(logger=self.logger)
        
        self.container.register_instance(KeywordMatcherService, keyword_matcher)
        self.container.register_instance(TokenCounterService, token_counter)
        
        # 注册应用服务
        self.character_service = CharacterCardService(
            character_repository=character_repo,
            logger=self.logger
        )
        self.lorebook_service = LorebookService(
            lorebook_repository=lorebook_repo,
            entry_repository=entry_repo,
            keyword_matcher=keyword_matcher,
            logger=self.logger
        )
        self.prompt_service = PromptAssemblyService(
            prompt_repository=prompt_repo,
            token_counter=token_counter,
            logger=self.logger
        )
        
        self.container.register_instance(CharacterCardService, self.character_service)
        self.container.register_instance(LorebookService, self.lorebook_service)
        self.container.register_instance(PromptAssemblyService, self.prompt_service)
        
        # 注册API网关
        self.api_gateway = ApiGateway()
        self.container.register_instance(ApiGateway, self.api_gateway)
        
        # 设置API路由
        await self.setup_api_routes()
        
        # 设置事件监听器
        await self.setup_event_listeners()
        
        print("✓ 应用初始化完成")
        print(f"✓ 演示数据目录: {self.demo_data_dir}")
        print()
    
    async def setup_api_routes(self):
        """设置API路由"""
        # 角色相关路由
        async def list_characters(**kwargs):
            return {
                "success": True,
                "data": {
                    "characters": [char.to_dict() for char in self.characters.values()],
                    "count": len(self.characters)
                }
            }
        
        async def get_character(id, **kwargs):
            if id in self.characters:
                return {
                    "success": True,
                    "data": self.characters[id].to_dict()
                }
            else:
                return {
                    "success": False,
                    "message": f"角色 {id} 不存在"
                }
        
        # 传说书相关路由
        async def list_lorebooks(**kwargs):
            return {
                "success": True,
                "data": {
                    "lorebooks": [lorebook.to_dict() for lorebook in self.lorebooks.values()],
                    "count": len(self.lorebooks)
                }
            }
        
        async def get_lorebook(id, **kwargs):
            if id in self.lorebooks:
                return {
                    "success": True,
                    "data": self.lorebooks[id].to_dict()
                }
            else:
                return {
                    "success": False,
                    "message": f"传说书 {id} 不存在"
                }
        
        async def activate_lorebook(id, **kwargs):
            if id in self.lorebooks:
                activation_dto = LorebookActivationDto(
                    text=kwargs.get("text", ""),
                    context=kwargs.get("context", {}),
                    max_entries=kwargs.get("max_entries", 5)
                )
                result = self.lorebook_service.activate_entries(id, activation_dto)
                return {
                    "success": True,
                    "data": {
                        "activated_entries": [entry.to_dict() for entry in result.activated_entries],
                        "total_candidates": result.total_candidates
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"传说书 {id} 不存在"
                }
        
        # 系统相关路由
        async def system_info(**kwargs):
            return {
                "success": True,
                "data": {
                    "application": "SuperRPG Demo",
                    "version": "2.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "stats": {
                        "characters": len(self.characters),
                        "lorebooks": len(self.lorebooks),
                        "templates": len(self.templates)
                    }
                }
            }
        
        async def system_stats(**kwargs):
            return {
                "success": True,
                "data": self.api_gateway.get_stats()
            }
        
        # 注册路由
        self.api_gateway.add_route("/characters", "GET", list_characters, name="list_characters")
        self.api_gateway.add_route("/characters/{id}", "GET", get_character, name="get_character")
        self.api_gateway.add_route("/lorebooks", "GET", list_lorebooks, name="list_lorebooks")
        self.api_gateway.add_route("/lorebooks/{id}", "GET", get_lorebook, name="get_lorebook")
        self.api_gateway.add_route("/lorebooks/{id}/activate", "POST", activate_lorebook, name="activate_lorebook")
        self.api_gateway.add_route("/system/info", "GET", system_info, name="system_info")
        self.api_gateway.add_route("/system/stats", "GET", system_stats, name="system_stats")
        
        print("✓ API路由设置完成")
    
    async def setup_event_listeners(self):
        """设置事件监听器"""
        async def character_created_handler(event):
            print(f"🎭 事件: 角色创建 - {event.data.get('character_name', '未知角色')}")
        
        async def character_updated_handler(event):
            print(f"🔄 事件: 角色更新 - {event.data.get('character_name', '未知角色')}")
        
        async def lorebook_created_handler(event):
            print(f"📚 事件: 传说书创建 - {event.data.get('name', '未知传说书')}")
        
        async def entry_activated_handler(event):
            print(f"✨ 事件: 条目激活 - {event.data.get('entry_title', '未知条目')}")
        
        # 订阅事件
        self.event_bus.subscribe("character_created", character_created_handler)
        self.event_bus.subscribe("character_updated", character_updated_handler)
        self.event_bus.subscribe("lorebook_created", lorebook_created_handler)
        self.event_bus.subscribe("entry_activated", entry_activated_handler)
        
        print("✓ 事件监听器设置完成")
    
    async def run_demo_scenarios(self):
        """运行演示场景"""
        print("=" * 80)
        print("开始运行演示场景...")
        print("=" * 80)
        
        # 场景1: 创建角色卡
        await self.demo_character_creation()
        
        # 场景2: 创建传说书和条目
        await self.demo_lorebook_creation()
        
        # 场景3: 激活传说书条目
        await self.demo_lorebook_activation()
        
        # 场景4: 提示组装
        await self.demo_prompt_assembly()
        
        # 场景5: API调用演示
        await self.demo_api_calls()
        
        # 场景6: 事件系统演示
        await self.demo_event_system()
        
        print("=" * 80)
        print("所有演示场景运行完成！")
        print("=" * 80)
    
    async def demo_character_creation(self):
        """演示角色卡创建"""
        print("\n🎭 场景1: 角色卡创建演示")
        print("-" * 50)
        
        # 创建艾莉娅
        character_data = {
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
        
        print("创建角色: 艾莉娅·星辰使者")
        create_dto = CharacterCardCreateDto(**character_data)
        character_dto = self.character_service.create_character_card(create_dto)
        self.characters[character_dto.id] = character_dto
        
        print(f"✓ 角色创建成功，ID: {character_dto.id}")
        print(f"  名称: {character_dto.name}")
        print(f"  职业: 法师 (智力: {character_dto.abilities['intelligence']})")
        print(f"  等级: {character_dto.stats['level']}")
        print(f"  生命值: {character_dto.hp}/{character_dto.max_hp}")
        
        # 创建索林
        character_data_2 = {
            "name": "索林·铁须",
            "description": "一位经验丰富的矮人战士，身披重甲，手持战斧。他的红色胡须编织成复杂的辫子，眼中闪烁着坚定的光芒。",
            "first_message": "*索林擦了擦战斧上的血迹* 我是索林·铁须，来自铁须氏族。需要帮忙的话，尽管开口，只要报酬合理。",
            "example_messages": [
                "*索林检查了一下装备* 让我们看看这次会遇到什么挑战。"
            ],
            "scenario": "在一家拥挤的酒馆里，索林坐在角落的桌子旁，面前放着一杯麦酒。",
            "personality_summary": "勇敢、忠诚、务实、直率",
            "creator_notes": "经典的矮人战士形象，重视荣誉和承诺",
            "tags": ["矮人", "战士", "勇敢", "忠诚"],
            "abilities": {
                "strength": 18,
                "dexterity": 10,
                "constitution": 16,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            },
            "stats": {
                "level": 4,
                "armor_class": 18,
                "proficiency_bonus": 2,
                "speed_steps": 5,
                "reach_steps": 1
            },
            "hp": 45,
            "max_hp": 45,
            "position": {"x": 3, "y": 6},
            "proficient_skills": ["athletics", "intimidation", "perception", "survival"],
            "proficient_saves": ["STR", "CON"],
            "inventory": {
                "战斧": 1,
                "盾牌": 1,
                "重甲": 1,
                "麦酒": 5
            }
        }
        
        print("\n创建角色: 索林·铁须")
        create_dto_2 = CharacterCardCreateDto(**character_data_2)
        character_dto_2 = self.character_service.create_character_card(create_dto_2)
        self.characters[character_dto_2.id] = character_dto_2
        
        print(f"✓ 角色创建成功，ID: {character_dto_2.id}")
        print(f"  名称: {character_dto_2.name}")
        print(f"  职业: 战士 (力量: {character_dto_2.abilities['strength']})")
        print(f"  等级: {character_dto_2.stats['level']}")
        print(f"  生命值: {character_dto_2.hp}/{character_dto_2.max_hp}")
        
        print("\n✓ 角色卡创建演示完成")
    
    async def demo_lorebook_creation(self):
        """演示传说书创建"""
        print("\n📚 场景2: 传说书创建演示")
        print("-" * 50)
        
        # 创建魔法传说书
        lorebook_data = {
            "name": "星辰魔法体系",
            "description": "关于星辰魔法的知识体系，包括咒语、仪式和历史背景",
            "version": "1.0.0",
            "tags": ["魔法", "星辰", "知识"]
        }
        
        print("创建传说书: 星辰魔法体系")
        create_lorebook_dto = LorebookCreateDto(**lorebook_data)
        lorebook_dto = self.lorebook_service.create_lorebook(create_lorebook_dto)
        self.lorebooks[lorebook_dto.id] = lorebook_dto
        
        print(f"✓ 传说书创建成功，ID: {lorebook_dto.id}")
        print(f"  名称: {lorebook_dto.name}")
        print(f"  描述: {lorebook_dto.description}")
        print(f"  版本: {lorebook_dto.version}")
        
        # 添加条目1: 星光治疗术
        entry_data_1 = {
            "title": "星光治疗术",
            "content": "星光治疗术是一种基础但有效的治疗法术，通过引导星光能量来修复伤口。施法者需要在夜空下，伸出手掌集中精神，感受星光的温暖。咒语为：'星光如水，治愈如泉'。",
            "keywords": [
                {"pattern": "治疗", "type": "EXACT", "case_sensitive": False, "weight": 10},
                {"pattern": "星光", "type": "EXACT", "case_sensitive": False, "weight": 8},
                {"pattern": "伤口", "type": "EXACT", "case_sensitive": False, "weight": 5}
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
        
        print("\n添加条目: 星光治疗术")
        create_entry_dto_1 = LorebookEntryCreateDto(**entry_data_1)
        entry_dto_1 = self.lorebook_service.create_entry(lorebook_dto.id, create_entry_dto_1)
        
        print(f"✓ 条目创建成功，ID: {entry_dto_1.id}")
        print(f"  标题: {entry_dto_1.title}")
        print(f"  关键词数量: {len(entry_dto_1.keywords)}")
        print(f"  内容长度: {len(entry_dto_1.content)} 字符")
        
        # 添加条目2: 星辰预言
        entry_data_2 = {
            "title": "星辰预言",
            "content": "古老的星辰预言描述了当七颗星辰连成一线时，将出现一位能够掌握星辰力量的使者。这位使者将拥有治愈伤痛、预见未来的能力，并将在黑暗时期引导迷失的灵魂。预言的最后提到：'当星辰黯淡时，使者之心将成为最后的灯塔。'",
            "keywords": [
                {"pattern": "预言", "type": "EXACT", "case_sensitive": False, "weight": 10},
                {"pattern": "星辰", "type": "EXACT", "case_sensitive": False, "weight": 8},
                {"pattern": "使者", "type": "EXACT", "case_sensitive": False, "weight": 7},
                {"pattern": "未来", "type": "EXACT", "case_sensitive": False, "weight": 6}
            ],
            "activation_rule": {
                "type": "ANY",
                "priority": 2,
                "max_activations": 5,
                "cooldown_seconds": 120
            },
            "tags": ["预言", "星辰", "使者"],
            "metadata": {
                "source": "古代卷轴",
                "authenticity": "已验证",
                "age": "千年以上"
            }
        }
        
        print("\n添加条目: 星辰预言")
        create_entry_dto_2 = LorebookEntryCreateDto(**entry_data_2)
        entry_dto_2 = self.lorebook_service.create_entry(lorebook_dto.id, create_entry_dto_2)
        
        print(f"✓ 条目创建成功，ID: {entry_dto_2.id}")
        print(f"  标题: {entry_dto_2.title}")
        print(f"  关键词数量: {len(entry_dto_2.keywords)}")
        print(f"  内容长度: {len(entry_dto_2.content)} 字符")
        
        print("\n✓ 传说书创建演示完成")
    
    async def demo_lorebook_activation(self):
        """演示传说书条目激活"""
        print("\n✨ 场景3: 传说书条目激活演示")
        print("-" * 50)
        
        # 获取第一个传说书
        magic_lorebook = list(self.lorebooks.values())[0]
        
        # 测试激活1: 治疗相关查询
        print("测试激活: 治疗相关查询")
        activation_dto_1 = LorebookActivationDto(
            text="我需要治疗 wounds，有什么星光法术可以帮助吗？",
            context={"character": "艾莉娅", "location": "观星塔"},
            max_entries=5
        )
        
        result_1 = self.lorebook_service.activate_entries(magic_lorebook.id, activation_dto_1)
        
        print(f"✓ 激活结果: 找到 {len(result_1.activated_entries)} 个匹配条目")
        for entry in result_1.activated_entries:
            print(f"  - {entry.title}")
            print(f"    匹配关键词: {[kw.pattern for kw in entry.keywords]}")
        
        # 测试激活2: 预言相关查询
        print("\n测试激活: 预言相关查询")
        activation_dto_2 = LorebookActivationDto(
            text="关于星之使者的未来预言是什么？",
            context={"character": "艾莉娅", "situation": "占卜"},
            max_entries=3
        )
        
        result_2 = self.lorebook_service.activate_entries(magic_lorebook.id, activation_dto_2)
        
        print(f"✓ 激活结果: 找到 {len(result_2.activated_entries)} 个匹配条目")
        for entry in result_2.activated_entries:
            print(f"  - {entry.title}")
            print(f"    内容摘要: {entry.content[:50]}...")
        
        print("\n✓ 传说书条目激活演示完成")
    
    async def demo_prompt_assembly(self):
        """演示提示组装"""
        print("\n📝 场景4: 提示组装演示")
        print("-" * 50)
        
        # 创建提示模板
        template = PromptTemplate(
            name="角色对话模板",
            description="用于生成角色对话的提示模板",
            sections=[
                PromptSection(
                    content="你是{character_name}，{character_description}。",
                    section_type=PromptSectionType.SYSTEM,
                    priority=1,
                    enabled=True
                ),
                PromptSection(
                    content="当前场景：{scenario}",
                    section_type=PromptSectionType.CONTEXT,
                    priority=2,
                    enabled=True
                ),
                PromptSection(
                    content="最近的对话历史：{chat_history}",
                    section_type=PromptSectionType.HISTORY,
                    priority=3,
                    enabled=True
                ),
                PromptSection(
                    content="当前输入：{current_input}",
                    section_type=PromptSectionType.INPUT,
                    priority=4,
                    enabled=True
                )
            ],
            variables={"character_name", "character_description", "scenario", "chat_history", "current_input"},
            is_active=True
        )
        
        # 保存模板
        prompt_repo = self.container.resolve(PromptRepositoryImpl)
        prompt_repo.save(template)
        self.templates[template.id] = template
        
        print(f"✓ 提示模板创建成功，ID: {template.id}")
        print(f"  名称: {template.name}")
        print(f"  段落数量: {len(template.sections)}")
        print(f"  变量数量: {len(template.variables)}")
        
        # 测试提示组装1: 艾莉娅的对话
        print("\n测试提示组装: 艾莉娅的对话")
        character = list(self.characters.values())[0]  # 艾莉娅
        
        context_dto_1 = PromptContextDto(
            character_name=character.name,
            character_description=character.description,
            world_info="这是一个充满魔法的世界，星辰之力影响着一切。",
            chat_history=[
                {"role": "user", "content": "你好，艾莉娅"},
                {"role": "assistant", "content": "你好，旅行者。我是艾莉娅，星辰的守护者。"}
            ],
            current_input="你能教我一些星光魔法吗？",
            variables={"time": "夜晚", "location": "观星塔"},
            metadata={"mood": "好奇"}
        )
        
        build_dto_1 = PromptBuildDto(
            template_id=str(template.id),
            context=context_dto_1,
            token_limit={
                "provider": "openai",
                "model_name": "gpt-3.5-turbo",
                "max_tokens": 2048,
                "reserved_tokens": 256
            },
            truncation_strategy="SMART"
        )
        
        prompt_preview_1 = self.prompt_service.build_prompt(build_dto_1)
        
        print(f"✓ 提示构建成功")
        print(f"  Token数量: {prompt_preview_1.token_count}")
        print(f"  段落数量: {len(prompt_preview_1.sections)}")
        print(f"  使用的变量: {prompt_preview_1.variables_used}")
        print(f"  缺失的变量: {prompt_preview_1.missing_variables}")
        print(f"  提示预览:")
        print("    " + prompt_preview_1.prompt.replace("\n", "\n    "))
        
        print("\n✓ 提示组装演示完成")
    
    async def demo_api_calls(self):
        """演示API调用"""
        print("\n🌐 场景5: API调用演示")
        print("-" * 50)
        
        # 测试API调用1: 获取角色列表
        print("API调用: GET /characters")
        response_1 = await self.api_gateway.handle_request("GET", "/characters")
        
        print(f"✓ 响应状态码: {response_1.status_code}")
        print(f"✓ 响应数据: {json.dumps(response_1.body, ensure_ascii=False, indent=2)}")
        
        # 测试API调用2: 获取系统信息
        print("\nAPI调用: GET /system/info")
        response_2 = await self.api_gateway.handle_request("GET", "/system/info")
        
        print(f"✓ 响应状态码: {response_2.status_code}")
        print(f"✓ 应用名称: {response_2.body['data']['application']}")
        print(f"✓ 版本: {response_2.body['data']['version']}")
        print(f"✓ 统计信息: {json.dumps(response_2.body['data']['stats'], ensure_ascii=False)}")
        
        print("\n✓ API调用演示完成")
    
    async def demo_event_system(self):
        """演示事件系统"""
        print("\n⚡ 场景6: 事件系统演示")
        print("-" * 50)
        
        # 创建临时事件监听器
        demo_events = []
        
        async def demo_event_handler(event):
            demo_events.append(event)
            print(f"📨 收到事件: {event.get_event_type()}")
            print(f"   数据: {json.dumps(event.data, ensure_ascii=False)}")
        
        # 订阅所有事件
        self.event_bus.subscribe("character_created", demo_event_handler)
        self.event_bus.subscribe("character_updated", demo_event_handler)
        self.event_bus.subscribe("character_moved", demo_event_handler)
        self.event_bus.subscribe("lorebook_created", demo_event_handler)
        self.event_bus.subscribe("entry_activated", demo_event_handler)
        
        print("✓ 事件监听器已注册")
        
        # 触发一些事件
        print("\n触发事件: 角色创建")
        character_id = list(self.characters.keys())[0]
        character = self.characters[character_id]
        
        from src.domain.models.characters import CharacterDomainEvent
        character_created_event = CharacterDomainEvent("character_created", {
            "character_name": character.name,
            "character_class": "法师",
            "timestamp": datetime.now().isoformat()
        })
        
        await self.event_bus.publish(character_created_event)
        
        print("\n触发事件: 角色移动")
        character_moved_event = CharacterDomainEvent("character_moved", {
            "character_name": character.name,
            "old_position": {"x": 5, "y": 8},
            "new_position": {"x": 6, "y": 9},
            "timestamp": datetime.now().isoformat()
        })
        
        await self.event_bus.publish(character_moved_event)
        
        # 等待事件处理
        await asyncio.sleep(0.1)
        
        print(f"\n✓ 共处理了 {len(demo_events)} 个事件")
        
        print("\n✓ 事件系统演示完成")
    
    async def interactive_mode(self):
        """交互式模式"""
        print("\n🎮 进入交互式模式")
        print("=" * 80)
        print("可用命令:")
        print("  help - 显示帮助信息")
        print("  list characters - 列出所有角色")
        print("  list lorebooks - 列出所有传说书")
        print("  stats - 显示系统统计")
        print("  scenarios - 重新运行演示场景")
        print("  quit - 退出程序")
        print("=" * 80)
        
        while self.running:
            try:
                command = input("\n请输入命令: ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == "quit" or cmd == "exit":
                    self.running = False
                    print("👋 再见！")
                    break
                
                elif cmd == "help":
                    print("\n帮助信息:")
                    print("  help - 显示此帮助信息")
                    print("  list characters - 列出所有角色")
                    print("  list lorebooks - 列出所有传说书")
                    print("  stats - 显示系统统计")
                    print("  scenarios - 重新运行演示场景")
                    print("  quit - 退出程序")
                
                elif cmd == "list" and len(parts) > 1:
                    sub_cmd = parts[1].lower()
                    
                    if sub_cmd == "characters":
                        print("\n角色列表:")
                        for i, (char_id, character) in enumerate(self.characters.items(), 1):
                            print(f"  {i}. {character.name} (ID: {char_id})")
                            print(f"     等级: {character.stats['level']}, 职业: {character.tags[0] if character.tags else '未知'}")
                    
                    elif sub_cmd == "lorebooks":
                        print("\n传说书列表:")
                        for i, (lorebook_id, lorebook) in enumerate(self.lorebooks.items(), 1):
                            print(f"  {i}. {lorebook.name} (ID: {lorebook_id})")
                            print(f"     版本: {lorebook.version}, 标签: {', '.join(lorebook.tags)}")
                    
                    else:
                        print(f"未知的子命令: {sub_cmd}")
                
                elif cmd == "stats":
                    print("\n系统统计:")
                    stats = self.api_gateway.get_stats()
                    print(f"  总请求数: {stats['total_requests']}")
                    print(f"  成功请求数: {stats['successful_requests']}")
                    print(f"  失败请求数: {stats['failed_requests']}")
                    print(f"  成功率: {stats['success_rate']}%")
                    print(f"  路由数量: {stats['routes_count']}")
                    print(f"  运行时间: {stats['uptime_seconds']:.2f}秒")
                    
                    print(f"\n资源统计:")
                    print(f"  角色数量: {len(self.characters)}")
                    print(f"  传说书数量: {len(self.lorebooks)}")
                    print(f"  模板数量: {len(self.templates)}")
                
                elif cmd == "scenarios":
                    print("\n重新运行演示场景...")
                    await self.run_demo_scenarios()
                
                else:
                    print(f"未知命令: {cmd}")
                    print("输入 'help' 查看可用命令")
                    
            except Exception as e:
                print(f"执行命令时出错: {str(e)}")
    
    async def run(self):
        """运行演示应用"""
        try:
            # 初始化应用
            await self.initialize()
            
            # 运行演示场景
            await self.run_demo_scenarios()
            
            # 进入交互式模式
            await self.interactive_mode()
            
        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在退出...")
        except Exception as e:
            print(f"\n运行时出错: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n演示应用已退出")


async def main():
    """主函数"""
    app = DemoApplication()
    await app.run()


if __name__ == "__main__":
    # 运行演示应用
    asyncio.run(main())