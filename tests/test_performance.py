#!/usr/bin/env python3
"""
性能测试

测试系统在各种负载下的性能表现，包括：
1. 大量角色卡的处理性能
2. 传说书关键词匹配性能
3. 提示组装性能
4. API网关并发处理能力
5. 事件总线吞吐量
"""

import asyncio
import json
import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import statistics

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


def generate_character_data(index: int) -> Dict[str, Any]:
    """生成测试角色数据"""
    classes = ["战士", "法师", "盗贼", "牧师", "游侠", "圣骑士", "德鲁伊", "巫师"]
    races = ["人类", "精灵", "矮人", "半身人", "龙裔", "提夫林"]
    
    character_class = classes[index % len(classes)]
    race = races[index % len(races)]
    
    return {
        "name": f"测试角色{index:04d}",
        "description": f"一位{race}{character_class}，拥有独特的技能和背景故事。这是用于性能测试的角色数据。",
        "first_message": f"*{race}{character_class}向你点头致意* 你好，我是测试角色{index:04d}。",
        "example_messages": [
            f"作为一名{character_class}，我擅长...",
            f"我的{race}血统赋予了我特殊的能力..."
        ],
        "scenario": "在一个充满挑战的幻想世界中，各种种族和职业的冒险者聚集在一起。",
        "personality_summary": f"勇敢、智慧、善良、坚定",
        "creator_notes": f"性能测试角色{index}，{race}{character_class}",
        "tags": [race, character_class, "测试"],
        "abilities": {
            "strength": 10 + (index % 10),
            "dexterity": 10 + ((index + 1) % 10),
            "constitution": 10 + ((index + 2) % 10),
            "intelligence": 10 + ((index + 3) % 10),
            "wisdom": 10 + ((index + 4) % 10),
            "charisma": 10 + ((index + 5) % 10)
        },
        "stats": {
            "level": 1 + (index % 20),
            "armor_class": 10 + (index % 10),
            "proficiency_bonus": 2 + ((index % 10) // 4),
            "speed_steps": 6,
            "reach_steps": 1
        },
        "hp": 10 + (index % 50),
        "max_hp": 10 + (index % 50),
        "position": {"x": index % 20, "y": (index // 20) % 20},
        "proficient_skills": ["运动", "察觉", "隐匿", "说服"],
        "proficient_saves": ["STR", "DEX"],
        "inventory": {
            "测试物品1": index % 5,
            "测试物品2": index % 3,
            "测试物品3": index % 2
        }
    }


def generate_lorebook_entry_data(index: int) -> Dict[str, Any]:
    """生成测试传说书条目数据"""
    keywords = [
        ["魔法", "咒语", "施法"],
        ["战斗", "武器", "攻击"],
        ["探险", "冒险", "旅程"],
        ["角色", "人物", "个性"],
        ["世界", "地点", "环境"],
        ["历史", "传说", "故事"],
        ["物品", "装备", "道具"],
        ["技能", "能力", "天赋"]
    ]
    
    keyword_set = keywords[index % len(keywords)]
    
    return {
        "title": f"测试条目{index:04d}",
        "content": f"这是测试条目{index}的内容。它包含了关于{keyword_set[0]}、{keyword_set[1]}和{keyword_set[2]}的详细信息。" +
                  "这个条目用于测试传说书系统的性能和关键词匹配功能。" +
                  "内容长度适中，既不太短也不太长，适合进行性能测试。",
        "keywords": [
            {
                "pattern": keyword,
                "type": "EXACT",
                "case_sensitive": False,
                "weight": 10 - (i * 2)
            }
            for i, keyword in enumerate(keyword_set)
        ],
        "activation_rule": {
            "type": "ANY",
            "priority": 1,
            "max_activations": 10,
            "cooldown_seconds": 30
        },
        "tags": ["测试", keyword_set[0]],
        "metadata": {
            "test_index": index,
            "keyword_count": len(keyword_set)
        }
    }


class PerformanceTestResult:
    """性能测试结果类"""
    
    def __init__(self, name: str):
        self.name = name
        self.execution_times = []
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
    
    def end(self):
        """结束计时"""
        self.end_time = time.time()
        if self.start_time:
            self.execution_times.append(self.end_time - self.start_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.execution_times:
            return {
                "name": self.name,
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "min_time": 0,
                "max_time": 0,
                "median_time": 0,
                "std_dev": 0
            }
        
        return {
            "name": self.name,
            "count": len(self.execution_times),
            "total_time": sum(self.execution_times),
            "avg_time": statistics.mean(self.execution_times),
            "min_time": min(self.execution_times),
            "max_time": max(self.execution_times),
            "median_time": statistics.median(self.execution_times),
            "std_dev": statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0
        }


@pytest.mark.asyncio
class TestPerformance:
    """性能测试类"""
    
    async def test_character_card_creation_performance(self, container):
        """测试大量角色卡创建的性能"""
        character_service = container.resolve(CharacterCardService)
        
        # 测试不同规模的角色卡创建
        test_sizes = [10, 50, 100]
        results = {}
        
        for size in test_sizes:
            result = PerformanceTestResult(f"创建{size}个角色卡")
            
            # 创建角色卡
            for i in range(size):
                character_data = generate_character_data(i)
                create_dto = CharacterCardCreateDto(**character_data)
                
                result.start()
                character_dto = character_service.create_character_card(create_dto)
                result.end()
            
            results[size] = result.get_stats()
            print(f"创建{size}个角色卡性能统计:")
            print(f"  总时间: {results[size]['total_time']:.2f}秒")
            print(f"  平均时间: {results[size]['avg_time']:.4f}秒/个")
            print(f"  最小时间: {results[size]['min_time']:.4f}秒")
            print(f"  最大时间: {results[size]['max_time']:.4f}秒")
            print(f"  中位数: {results[size]['median_time']:.4f}秒")
            print(f"  标准差: {results[size]['std_dev']:.4f}秒")
            print()
        
        # 验证性能指标
        assert results[10]["avg_time"] < 0.1, "创建10个角色卡的平均时间应小于0.1秒"
        assert results[50]["avg_time"] < 0.1, "创建50个角色卡的平均时间应小于0.1秒"
        assert results[100]["avg_time"] < 0.1, "创建100个角色卡的平均时间应小于0.1秒"
    
    async def test_character_card_query_performance(self, container):
        """测试角色卡查询性能"""
        character_service = container.resolve(CharacterCardService)
        
        # 先创建一些角色卡
        character_ids = []
        for i in range(50):
            character_data = generate_character_data(i)
            create_dto = CharacterCardCreateDto(**character_data)
            character_dto = character_service.create_character_card(create_dto)
            character_ids.append(character_dto.id)
        
        # 测试单个角色卡查询性能
        result = PerformanceTestResult("单个角色卡查询")
        
        for _ in range(100):  # 查询100次
            character_id = character_ids[_ % len(character_ids)]
            result.start()
            character_service.get_character_card(character_id)
            result.end()
        
        stats = result.get_stats()
        print("单个角色卡查询性能统计:")
        print(f"  总查询次数: {stats['count']}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.4f}秒/次")
        print(f"  QPS: {stats['count'] / stats['total_time']:.2f}")
        print()
        
        # 验证性能指标
        assert stats["avg_time"] < 0.01, "单个角色卡查询的平均时间应小于0.01秒"
        assert stats["count"] / stats["total_time"] > 50, "QPS应大于50"
        
        # 测试角色卡列表查询性能
        result = PerformanceTestResult("角色卡列表查询")
        
        for _ in range(20):  # 查询20次
            result.start()
            character_service.get_character_cards(page=1, page_size=20)
            result.end()
        
        stats = result.get_stats()
        print("角色卡列表查询性能统计:")
        print(f"  总查询次数: {stats['count']}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.4f}秒/次")
        print(f"  QPS: {stats['count'] / stats['total_time']:.2f}")
        print()
        
        # 验证性能指标
        assert stats["avg_time"] < 0.05, "角色卡列表查询的平均时间应小于0.05秒"
    
    async def test_lorebook_keyword_matching_performance(self, container):
        """测试传说书关键词匹配性能"""
        lorebook_service = container.resolve(LorebookService)
        
        # 创建传说书
        create_lorebook_dto = LorebookCreateDto(
            name="性能测试传说书",
            description="用于性能测试的传说书",
            version="1.0.0",
            tags=["测试", "性能"]
        )
        lorebook_dto = lorebook_service.create_lorebook(create_lorebook_dto)
        
        # 创建大量条目
        entry_count = 100
        for i in range(entry_count):
            entry_data = generate_lorebook_entry_data(i)
            create_entry_dto = LorebookEntryCreateDto(**entry_data)
            lorebook_service.create_entry(lorebook_dto.id, create_entry_dto)
        
        # 测试关键词匹配性能
        test_texts = [
            "我想学习一些魔法咒语",
            "战斗中使用什么武器最好",
            "如何进行探险和冒险",
            "角色扮演需要注意什么",
            "这个世界的历史传说",
            "有什么好的装备和物品",
            "如何提升技能和能力"
        ]
        
        result = PerformanceTestResult("关键词匹配")
        
        for i in range(50):  # 测试50次
            text = test_texts[i % len(test_texts)]
            activation_dto = LorebookActivationDto(
                text=text,
                context={"test": True},
                max_entries=10
            )
            
            result.start()
            lorebook_service.activate_entries(lorebook_dto.id, activation_dto)
            result.end()
        
        stats = result.get_stats()
        print("关键词匹配性能统计:")
        print(f"  总匹配次数: {stats['count']}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.4f}秒/次")
        print(f"  QPS: {stats['count'] / stats['total_time']:.2f}")
        print()
        
        # 验证性能指标
        assert stats["avg_time"] < 0.05, "关键词匹配的平均时间应小于0.05秒"
        assert stats["count"] / stats["total_time"] > 20, "QPS应大于20"
    
    async def test_prompt_assembly_performance(self, container):
        """测试提示组装性能"""
        prompt_service = container.resolve(PromptAssemblyService)
        
        # 创建提示模板
        template = PromptTemplate(
            name="性能测试模板",
            description="用于性能测试的提示模板",
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
                    content="对话历史：{chat_history}",
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
        prompt_repo = container.resolve(PromptRepositoryImpl)
        prompt_repo.save(template)
        
        # 创建测试上下文
        test_contexts = []
        for i in range(10):
            context = PromptContextDto(
                character_name=f"角色{i}",
                character_description=f"这是角色{i}的描述",
                world_info="这是一个幻想世界",
                chat_history=[
                    {"role": "user", "content": f"你好，角色{i}"},
                    {"role": "assistant", "content": f"你好，我是角色{i}"}
                ],
                current_input=f"测试输入{i}",
                variables={"var1": f"value{i}", "var2": f"data{i}"},
                metadata={"test": True, "index": i}
            )
            test_contexts.append(context)
        
        # 测试提示组装性能
        result = PerformanceTestResult("提示组装")
        
        for i in range(100):  # 测试100次
            context = test_contexts[i % len(test_contexts)]
            build_dto = PromptBuildDto(
                template_id=str(template.id),
                context=context,
                token_limit={
                    "provider": "openai",
                    "model_name": "gpt-3.5-turbo",
                    "max_tokens": 2048,
                    "reserved_tokens": 256
                },
                truncation_strategy="SMART"
            )
            
            result.start()
            prompt_service.build_prompt(build_dto)
            result.end()
        
        stats = result.get_stats()
        print("提示组装性能统计:")
        print(f"  总组装次数: {stats['count']}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.4f}秒/次")
        print(f"  QPS: {stats['count'] / stats['total_time']:.2f}")
        print()
        
        # 验证性能指标
        assert stats["avg_time"] < 0.05, "提示组装的平均时间应小于0.05秒"
        assert stats["count"] / stats["total_time"] > 10, "QPS应大于10"
    
    async def test_api_gateway_concurrent_performance(self, container):
        """测试API网关并发处理能力"""
        api_gateway = container.resolve(ApiGateway)
        
        # 注册测试路由
        async def fast_handler(**kwargs):
            return {"message": "快速响应", "timestamp": time.time()}
        
        async def slow_handler(**kwargs):
            await asyncio.sleep(0.1)  # 模拟慢速操作
            return {"message": "慢速响应", "timestamp": time.time()}
        
        async def compute_handler(**kwargs):
            # 模拟一些计算
            result = sum(i * i for i in range(1000))
            return {"message": "计算完成", "result": result}
        
        # 添加路由
        api_gateway.add_route("/fast", "GET", fast_handler, name="fast")
        api_gateway.add_route("/slow", "GET", slow_handler, name="slow")
        api_gateway.add_route("/compute", "GET", compute_handler, name="compute")
        
        # 测试并发请求
        async def make_request(path: str) -> float:
            start_time = time.time()
            await api_gateway.handle_request("GET", path)
            return time.time() - start_time
        
        # 测试不同级别的并发
        concurrency_levels = [10, 50, 100]
        test_paths = ["/fast", "/compute"]
        
        for concurrency in concurrency_levels:
            for path in test_paths:
                result = PerformanceTestResult(f"并发{concurrency}个请求到{path}")
                
                # 创建并发任务
                tasks = [make_request(path) for _ in range(concurrency)]
                
                # 执行并发任务
                start_time = time.time()
                execution_times = await asyncio.gather(*tasks)
                end_time = time.time()
                
                result.execution_times = execution_times
                result.start_time = start_time
                result.end_time = end_time
                
                stats = result.get_stats()
                print(f"并发{concurrency}个请求到{path}性能统计:")
                print(f"  总请求数: {concurrency}")
                print(f"  总时间: {stats['total_time']:.2f}秒")
                print(f"  平均响应时间: {stats['avg_time']:.4f}秒")
                print(f"  最小响应时间: {stats['min_time']:.4f}秒")
                print(f"  最大响应时间: {stats['max_time']:.4f}秒")
                print(f"  QPS: {concurrency / stats['total_time']:.2f}")
                print()
                
                # 验证性能指标
                if path == "/fast":
                    assert stats["avg_time"] < 0.1, f"快速路由的平均响应时间应小于0.1秒"
                    assert concurrency / stats["total_time"] > 50, f"快速路由的QPS应大于50"
                elif path == "/compute":
                    assert stats["avg_time"] < 0.2, f"计算路由的平均响应时间应小于0.2秒"
                    assert concurrency / stats["total_time"] > 20, f"计算路由的QPS应大于20"
    
    async def test_event_bus_throughput(self, container):
        """测试事件总线吞吐量"""
        event_bus = container.resolve(EventBus)
        
        # 创建事件监听器
        received_count = 0
        event_received = asyncio.Event()
        
        async def event_handler(event):
            nonlocal received_count
            received_count += 1
            if received_count >= 100:  # 接收到100个事件后设置标志
                event_received.set()
        
        # 订阅事件
        event_bus.subscribe("test_event", event_handler)
        
        # 测试事件发布吞吐量
        result = PerformanceTestResult("事件发布")
        
        event_count = 100
        for i in range(event_count):
            from src.domain.models.characters import CharacterDomainEvent
            from src.core.events import DomainEvent
            
            test_event = DomainEvent("test_event", {
                "index": i,
                "data": f"测试数据{i}",
                "timestamp": time.time()
            })
            
            result.start()
            await event_bus.publish(test_event)
            result.end()
        
        stats = result.get_stats()
        print("事件发布性能统计:")
        print(f"  总事件数: {event_count}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.6f}秒/事件")
        print(f"  事件/秒: {event_count / stats['total_time']:.2f}")
        print()
        
        # 等待所有事件被处理
        try:
            await asyncio.wait_for(event_received.wait(), timeout=5.0)
            print(f"成功接收并处理了 {received_count} 个事件")
        except asyncio.TimeoutError:
            print(f"事件处理超时，只处理了 {received_count} 个事件")
        
        # 验证性能指标
        assert stats["avg_time"] < 0.01, "事件发布的平均时间应小于0.01秒"
        assert event_count / stats["total_time"] > 100, "事件发布速率应大于100事件/秒"
        assert received_count >= event_count * 0.9, f"至少应接收到90%的事件，实际接收到{received_count}/{event_count}"
    
    async def test_mixed_operation_performance(self, container):
        """测试混合操作性能"""
        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        prompt_service = container.resolve(PromptAssemblyService)
        
        # 准备测试数据
        character_data = generate_character_data(1)
        create_dto = CharacterCardCreateDto(**character_data)
        character_dto = character_service.create_character_card(create_dto)
        
        create_lorebook_dto = LorebookCreateDto(
            name="混合测试传说书",
            description="用于混合操作性能测试",
            version="1.0.0",
            tags=["测试", "混合"]
        )
        lorebook_dto = lorebook_service.create_lorebook(create_lorebook_dto)
        
        entry_data = generate_lorebook_entry_data(1)
        create_entry_dto = LorebookEntryCreateDto(**entry_data)
        entry_dto = lorebook_service.create_entry(lorebook_dto.id, create_entry_dto)
        
        # 创建提示模板
        template = PromptTemplate(
            name="混合测试模板",
            description="用于混合操作测试的模板",
            sections=[
                PromptSection(
                    content="测试内容：{test_content}",
                    section_type=PromptSectionType.SYSTEM,
                    priority=1,
                    enabled=True
                )
            ],
            variables={"test_content"},
            is_active=True
        )
        
        prompt_repo = container.resolve(PromptRepositoryImpl)
        prompt_repo.save(template)
        
        # 测试混合操作
        result = PerformanceTestResult("混合操作")
        
        operations = [
            # 角色卡操作
            lambda: character_service.get_character_card(character_dto.id),
            
            # 传说书操作
            lambda: lorebook_service.get_lorebook(lorebook_dto.id),
            lambda: lorebook_service.get_entry(lorebook_dto.id, entry_dto.id),
            
            # 提示组装操作
            lambda: prompt_service.preview_prompt(
                str(template.id),
                PromptContextDto(
                    character_name="测试角色",
                    character_description="测试描述",
                    world_info="测试世界",
                    chat_history=[],
                    current_input="测试输入",
                    variables={"test_content": "测试内容"},
                    metadata={}
                )
            )
        ]
        
        # 执行混合操作
        for i in range(100):
            operation = operations[i % len(operations)]
            result.start()
            operation()
            result.end()
        
        stats = result.get_stats()
        print("混合操作性能统计:")
        print(f"  总操作数: {stats['count']}")
        print(f"  总时间: {stats['total_time']:.2f}秒")
        print(f"  平均时间: {stats['avg_time']:.4f}秒/操作")
        print(f"  QPS: {stats['count'] / stats['total_time']:.2f}")
        print()
        
        # 验证性能指标
        assert stats["avg_time"] < 0.1, "混合操作的平均时间应小于0.1秒"
        assert stats["count"] / stats["total_time"] > 10, "混合操作的QPS应大于10"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])