# 集成测试指南

本指南详细介绍如何为SuperRPG项目编写和运行集成测试，确保各个模块能够正确协同工作。

## 目录

- [概述](#概述)
- [测试环境设置](#测试环境设置)
- [测试结构](#测试结构)
- [编写集成测试](#编写集成测试)
- [测试数据管理](#测试数据管理)
- [运行测试](#运行测试)
- [CI/CD集成](#cicd集成)
- [故障排除](#故障排除)

## 概述

集成测试是验证系统中多个组件协同工作的测试。在SuperRPG项目中，集成测试主要关注：

1. **模块间交互**：验证不同模块之间的接口和数据流
2. **数据持久化**：验证数据在数据库中的正确存储和检索
3. **API端点**：验证完整的API请求-响应流程
4. **事件系统**：验证事件的发布和订阅机制
5. **服务协调**：验证多个服务之间的协调工作

## 测试环境设置

### 1. 测试数据库

集成测试需要独立的测试数据库，避免影响开发数据：

```python
# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.repositories.base import Base
from src.core.container import Container

@pytest.fixture(scope="session")
def test_db():
    """创建测试数据库"""
    # 使用内存SQLite数据库进行测试
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # 清理
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """提供数据库会话"""
    session = test_db()
    try:
        yield session
    finally:
        session.close()
```

### 2. 测试容器

```python
@pytest.fixture
def test_container():
    """创建测试用的依赖注入容器"""
    container = Container()
    
    # 配置测试用的服务
    container.register('db_session', lambda: db_session)
    container.register('character_service', CharacterService)
    container.register('lorebook_service', LorebookService)
    
    return container
```

### 3. 测试客户端

```python
@pytest.fixture
def test_client(test_container):
    """创建测试API客户端"""
    from src.adapters.api_gateway import APIGateway
    
    app = APIGateway(container)
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        yield client
```

## 测试结构

集成测试按照功能模块组织：

```
tests/
├── integration/
│   ├── test_character_integration.py     # 角色卡集成测试
│   ├── test_lorebook_integration.py       # 传说书集成测试
│   ├── test_prompt_integration.py         # 提示系统集成测试
│   ├── test_world_integration.py          # 世界管理集成测试
│   └── test_event_integration.py          # 事件系统集成测试
├── e2e/
│   └── test_full_workflow.py              # 端到端测试
├── conftest.py                            # pytest配置和fixtures
└── utils/
    ├── test_data_generator.py             # 测试数据生成器
    └── api_test_client.py                 # API测试客户端
```

## 编写集成测试

### 1. 角色卡集成测试

```python
# tests/integration/test_character_integration.py
import pytest
from src.domain.models.characters import CharacterCard
from src.application.services.character_card_service import CharacterCardService

class TestCharacterIntegration:
    """角色卡集成测试"""
    
    def test_create_and_retrieve_character(self, test_client, db_session):
        """测试创建和检索角色卡"""
        # 准备测试数据
        character_data = {
            "name": "测试角色",
            "race": "人类",
            "class": "战士",
            "level": 1,
            "attributes": {
                "strength": 16,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 10
            }
        }
        
        # 创建角色卡
        response = test_client.post('/api/v1/characters', json=character_data)
        assert response.status_code == 201
        
        created_character = response.get_json()
        character_id = created_character['id']
        
        # 检索角色卡
        response = test_client.get(f'/api/v1/characters/{character_id}')
        assert response.status_code == 200
        
        retrieved_character = response.get_json()
        assert retrieved_character['name'] == character_data['name']
        assert retrieved_character['race'] == character_data['race']
        assert retrieved_character['class'] == character_data['class']
        
        # 验证数据库中的数据
        db_character = db_session.query(CharacterCard).filter_by(id=character_id).first()
        assert db_character is not None
        assert db_character.name == character_data['name']
    
    def test_update_character_with_lorebook(self, test_client, db_session):
        """测试更新角色卡并关联传说书条目"""
        # 创建角色卡
        character_data = {
            "name": "艾莉娅",
            "race": "精灵",
            "class": "法师",
            "level": 3
        }
        
        response = test_client.post('/api/v1/characters', json=character_data)
        character_id = response.get_json()['id']
        
        # 创建传说书条目
        lorebook_data = {
            "title": "精灵魔法",
            "category": "魔法",
            "keywords": ["精灵", "魔法"],
            "content": "精灵特有的魔法知识"
        }
        
        response = test_client.post('/api/v1/lorebook', json=lorebook_data)
        lorebook_id = response.get_json()['id']
        
        # 更新角色卡，添加传说书关联
        update_data = {
            "background": "精通精灵魔法的法师",
            "related_lorebook_entries": [lorebook_id]
        }
        
        response = test_client.patch(f'/api/v1/characters/{character_id}', json=update_data)
        assert response.status_code == 200
        
        # 验证更新结果
        response = test_client.get(f'/api/v1/characters/{character_id}')
        updated_character = response.get_json()
        assert updated_character['background'] == update_data['background']
        assert lorebook_id in updated_character.get('related_lorebook_entries', [])
    
    def test_character_deletion_cascade(self, test_client, db_session):
        """测试角色卡删除时的级联操作"""
        # 创建角色卡
        character_data = {
            "name": "待删除角色",
            "race": "矮人",
            "class": "战士",
            "level": 2
        }
        
        response = test_client.post('/api/v1/characters', json=character_data)
        character_id = response.get_json()['id']
        
        # 创建与角色相关的提示模板
        template_data = {
            "name": "角色专属模板",
            "category": "对话",
            "sections": [
                {
                    "name": "角色介绍",
                    "content": f"你是{character_data['name']}...",
                    "order": 1,
                    "required": True
                }
            ]
        }
        
        response = test_client.post('/api/v1/prompts/templates', json=template_data)
        template_id = response.get_json()['id']
        
        # 删除角色卡
        response = test_client.delete(f'/api/v1/characters/{character_id}')
        assert response.status_code == 204
        
        # 验证角色卡已删除
        response = test_client.get(f'/api/v1/characters/{character_id}')
        assert response.status_code == 404
        
        # 验证相关数据的处理（根据业务需求）
        # 例如：提示模板可能保留，但角色引用被清除
```

### 2. 传说书集成测试

```python
# tests/integration/test_lorebook_integration.py
import pytest
from src.domain.models.lorebook import LoreBookEntry
from src.application.services.keyword_matcher_service import KeywordMatcherService

class TestLorebookIntegration:
    """传说书集成测试"""
    
    def test_create_and_search_lorebook_entries(self, test_client, db_session):
        """测试创建和搜索传说书条目"""
        # 创建多个传说书条目
        entries = [
            {
                "title": "龙族历史",
                "category": "历史",
                "keywords": ["龙", "历史", "古代"],
                "content": "关于龙族的古老历史记录"
            },
            {
                "title": "魔法龙",
                "category": "生物",
                "keywords": ["龙", "魔法", "强大"],
                "content": "拥有魔法力量的龙类生物"
            },
            {
                "title": "精灵传说",
                "category": "传说",
                "keywords": ["精灵", "传说", "森林"],
                "content": "关于精灵族的古老传说"
            }
        ]
        
        created_entries = []
        for entry_data in entries:
            response = test_client.post('/api/v1/lorebook', json=entry_data)
            assert response.status_code == 201
            created_entries.append(response.get_json())
        
        # 搜索包含"龙"的条目
        response = test_client.get('/api/v1/lorebook/search?q=龙')
        assert response.status_code == 200
        
        search_results = response.get_json()
        assert len(search_results) == 2  # 应该找到"龙族历史"和"魔法龙"
        
        # 验证搜索结果的相关性
        titles = [result['title'] for result in search_results]
        assert "龙族历史" in titles
        assert "魔法龙" in titles
        assert "精灵传说" not in titles
    
    def test_lorebook_keyword_matching(self, test_client, test_container):
        """测试传说书关键词匹配服务"""
        # 创建关键词匹配器服务
        keyword_matcher = KeywordMatcherService(db_session)
        
        # 创建测试条目
        entry_data = {
            "title": "测试条目",
            "category": "测试",
            "keywords": ["测试", "集成", "匹配"],
            "content": "这是一个用于测试关键词匹配的条目"
        }
        
        response = test_client.post('/api/v1/lorebook', json=entry_data)
        entry_id = response.get_json()['id']
        
        # 测试关键词匹配
        matched_entries = keyword_matcher.find_matching_entries(["测试", "关键词"])
        assert len(matched_entries) >= 1
        
        # 验证匹配条目的相关性分数
        matched_entry = next((e for e in matched_entries if e.id == entry_id), None)
        assert matched_entry is not None
        assert matched_entry.relevance_score > 0
```

### 3. 提示系统集成测试

```python
# tests/integration/test_prompt_integration.py
import pytest
from src.application.services.prompt_assembly_service import PromptAssemblyService
from src.domain.models.prompt import PromptTemplate

class TestPromptIntegration:
    """提示系统集成测试"""
    
    def test_create_and_assemble_prompt(self, test_client, db_session):
        """测试创建和组装提示模板"""
        # 创建提示模板
        template_data = {
            "name": "对话模板",
            "category": "对话",
            "description": "用于角色对话的提示模板",
            "sections": [
                {
                    "name": "角色设定",
                    "content": "你是{character_name}，一个{race}{class}。",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "场景描述",
                    "content": "你在{location}，正在{situation}。",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "对话指导",
                    "content": "请以角色的视角回应，保持{tone}的语气。",
                    "order": 3,
                    "required": False
                }
            ],
            "variables": {
                "character_name": {
                    "type": "string",
                    "description": "角色名称",
                    "required": True
                },
                "race": {
                    "type": "string",
                    "description": "种族",
                    "required": True
                },
                "class": {
                    "type": "string",
                    "description": "职业",
                    "required": True
                },
                "location": {
                    "type": "string",
                    "description": "位置",
                    "required": True
                },
                "situation": {
                    "type": "string",
                    "description": "情况",
                    "required": True
                },
                "tone": {
                    "type": "string",
                    "description": "语气",
                    "required": False,
                    "default": "友好"
                }
            }
        }
        
        response = test_client.post('/api/v1/prompts/templates', json=template_data)
        assert response.status_code == 201
        
        template = response.get_json()
        template_id = template['id']
        
        # 组装提示
        variables = {
            "character_name": "艾莉娅",
            "race": "精灵",
            "class": "法师",
            "location": "魔法塔",
            "situation": "研究古老魔法",
            "tone": "好奇"
        }
        
        response = test_client.post(f'/api/v1/prompts/templates/{template_id}/assemble', 
                                    json={"variables": variables})
        assert response.status_code == 200
        
        result = response.get_json()
        assembled_prompt = result['prompt']
        
        # 验证组装结果
        assert "艾莉娅" in assembled_prompt
        assert "精灵" in assembled_prompt
        assert "法师" in assembled_prompt
        assert "魔法塔" in assembled_prompt
        assert "研究古老魔法" in assembled_prompt
        assert "好奇" in assembled_prompt
        
        # 验证变量替换
        assert "{character_name}" not in assembled_prompt
        assert "{race}" not in assembled_prompt
        assert "{class}" not in assembled_prompt
    
    def test_prompt_template_with_character_data(self, test_client, db_session):
        """测试提示模板与角色数据的集成"""
        # 创建角色卡
        character_data = {
            "name": "索林",
            "race": "矮人",
            "class": "战士",
            "level": 5,
            "background": "来自铁炉堡的勇敢战士"
        }
        
        response = test_client.post('/api/v1/characters', json=character_data)
        character = response.get_json()
        
        # 创建使用角色数据的提示模板
        template_data = {
            "name": "角色背景模板",
            "category": "背景",
            "sections": [
                {
                    "name": "角色介绍",
                    "content": "我是{character_name}，{background}。",
                    "order": 1,
                    "required": True
                }
            ],
            "variables": {
                "character_name": {
                    "type": "string",
                    "description": "角色名称",
                    "required": True
                },
                "background": {
                    "type": "string",
                    "description": "角色背景",
                    "required": True
                }
            }
        }
        
        response = test_client.post('/api/v1/prompts/templates', json=template_data)
        template = response.get_json()
        
        # 使用角色数据组装提示
        variables = {
            "character_name": character['name'],
            "background": character['background']
        }
        
        response = test_client.post(f'/api/v1/prompts/templates/{template['id']}/assemble', 
                                    json={"variables": variables})
        result = response.get_json()
        
        assembled_prompt = result['prompt']
        assert character['name'] in assembled_prompt
        assert character['background'] in assembled_prompt
```

### 4. 事件系统集成测试

```python
# tests/integration/test_event_integration.py
import pytest
import asyncio
from src.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from src.core.events import Event

class TestEventIntegration:
    """事件系统集成测试"""
    
    @pytest.fixture
    def event_bus(self):
        """创建事件总线"""
        return EnhancedEventBus()
    
    def test_event_publish_and_subscribe(self, event_bus):
        """测试事件发布和订阅"""
        received_events = []
        
        # 定义事件处理器
        def event_handler(event):
            received_events.append(event)
        
        # 订阅事件
        event_bus.subscribe("character.created", event_handler)
        
        # 发布事件
        event_data = {
            "character_id": "char_123",
            "name": "测试角色",
            "race": "人类"
        }
        
        event = Event("character.created", event_data)
        event_bus.publish(event)
        
        # 等待事件处理（异步场景）
        asyncio.sleep(0.1)
        
        # 验证事件接收
        assert len(received_events) == 1
        assert received_events[0].event_type == "character.created"
        assert received_events[0].data["name"] == "测试角色"
    
    def test_multiple_subscribers(self, event_bus):
        """测试多个订阅者"""
        subscriber1_events = []
        subscriber2_events = []
        
        def subscriber1_handler(event):
            subscriber1_events.append(event)
        
        def subscriber2_handler(event):
            subscriber2_events.append(event)
        
        # 订阅同一事件
        event_bus.subscribe("character.updated", subscriber1_handler)
        event_bus.subscribe("character.updated", subscriber2_handler)
        
        # 发布事件
        event_data = {"character_id": "char_123", "level": 2}
        event = Event("character.updated", event_data)
        event_bus.publish(event)
        
        asyncio.sleep(0.1)
        
        # 验证两个订阅者都收到事件
        assert len(subscriber1_events) == 1
        assert len(subscriber2_events) == 1
        assert subscriber1_events[0].data["level"] == 2
        assert subscriber2_events[0].data["level"] == 2
    
    def test_event_filtering(self, event_bus):
        """测试事件过滤"""
        filtered_events = []
        
        def event_handler(event):
            filtered_events.append(event)
        
        # 订阅带过滤条件的事件
        def filter_function(event):
            return event.data.get("level", 0) >= 5
        
        event_bus.subscribe("character.level_up", event_handler, filter_function)
        
        # 发布不同等级的事件
        low_level_event = Event("character.level_up", {"character_id": "char_123", "level": 3})
        high_level_event = Event("character.level_up", {"character_id": "char_456", "level": 7})
        
        event_bus.publish(low_level_event)
        event_bus.publish(high_level_event)
        
        asyncio.sleep(0.1)
        
        # 验证只有高等级事件被处理
        assert len(filtered_events) == 1
        assert filtered_events[0].data["level"] == 7
```

## 测试数据管理

### 1. 测试数据生成器

```python
# tests/utils/test_data_generator.py
import random
from datetime import datetime

class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def create_character_data(overrides=None):
        """生成角色卡测试数据"""
        data = {
            "name": f"测试角色_{random.randint(1000, 9999)}",
            "race": random.choice(["人类", "精灵", "矮人", "半身人"]),
            "class": random.choice(["战士", "法师", "游侠", "盗贼"]),
            "level": random.randint(1, 10),
            "attributes": {
                "strength": random.randint(8, 18),
                "dexterity": random.randint(8, 18),
                "constitution": random.randint(8, 18),
                "intelligence": random.randint(8, 18),
                "wisdom": random.randint(8, 18),
                "charisma": random.randint(8, 18)
            },
            "background": random.choice(["士兵", "学者", "商人", "贵族"]),
            "appearance": "测试用外观描述",
            "personality": ["勇敢", "好奇", "谨慎"],
            "backstory": "测试用背景故事"
        }
        
        if overrides:
            data.update(overrides)
        
        return data
    
    @staticmethod
    def create_lorebook_entry_data(overrides=None):
        """生成传说书条目测试数据"""
        categories = ["人物", "地点", "物品", "事件", "魔法", "历史"]
        
        data = {
            "title": f"测试条目_{random.randint(1000, 9999)}",
            "category": random.choice(categories),
            "keywords": ["测试", "关键词", f"标签_{random.randint(1, 100)}"],
            "content": "这是一个用于测试的传说书条目内容。",
            "importance": random.randint(1, 5),
            "verified": random.choice([True, False]),
            "source": "测试来源"
        }
        
        if overrides:
            data.update(overrides)
        
        return data
```

### 2. 测试数据清理

```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def cleanup_test_data(db_session):
    """自动清理测试数据"""
    yield
    
    # 测试结束后清理数据
    from src.domain.models.characters import CharacterCard
    from src.domain.models.lorebook import LoreBookEntry
    from src.domain.models.prompt import PromptTemplate
    
    db_session.query(CharacterCard).delete()
    db_session.query(LoreBookEntry).delete()
    db_session.query(PromptTemplate).delete()
    db_session.commit()
```

## 运行测试

### 1. 运行所有集成测试

```bash
# 运行所有集成测试
pytest tests/integration/ -v

# 运行特定模块的集成测试
pytest tests/integration/test_character_integration.py -v

# 运行带覆盖率的集成测试
pytest tests/integration/ --cov=src --cov-report=html
```

### 2. 并行运行测试

```bash
# 使用4个进程并行运行
pytest tests/integration/ -n 4

# 按测试文件并行运行
pytest tests/integration/ --dist=loadfile
```

### 3. 测试标记

```python
# tests/integration/test_character_integration.py
import pytest

@pytest.mark.integration
@pytest.mark.character
def test_character_creation(self, test_client):
    """角色创建集成测试"""
    pass

@pytest.mark.slow
def test_character_bulk_operations(self, test_client):
    """角色批量操作集成测试（标记为慢速测试）"""
    pass
```

```bash
# 运行特定标记的测试
pytest -m integration
pytest -m "integration and character"
pytest -m "not slow"
```

## CI/CD集成

### 1. GitHub Actions配置

```yaml
# .github/workflows/integration-tests.yml
name: 集成测试

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: 设置Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: 安装依赖
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov pytest-asyncio
    
    - name: 运行集成测试
      run: |
        pytest tests/integration/ -v --cov=src --cov-report=xml
    
    - name: 上传覆盖率
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 2. 测试报告生成

```python
# tests/reporting/integration_test_reporter.py
import pytest
import json
from datetime import datetime

class IntegrationTestReporter:
    """集成测试报告生成器"""
    
    def __init__(self, output_dir="test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_report(self, test_results):
        """生成集成测试报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(test_results),
                "passed": len([r for r in test_results if r.passed]),
                "failed": len([r for r in test_results if not r.passed]),
                "skipped": len([r for r in test_results if r.skipped])
            },
            "tests": []
        }
        
        for result in test_results:
            test_info = {
                "name": result.name,
                "module": result.module,
                "status": "passed" if result.passed else "failed",
                "duration": result.duration,
                "error": str(result.longrepr) if not result.passed else None
            }
            report["tests"].append(test_info)
        
        # 保存报告
        report_file = self.output_dir / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file
```

## 故障排除

### 1. 常见问题

#### 数据库连接问题

```python
# 确保测试数据库正确配置
@pytest.fixture(scope="session")
def test_db():
    # 使用环境变量或配置文件
    database_url = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(database_url)
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    yield engine
    
    Base.metadata.drop_all(engine)
```

#### 异步测试问题

```python
# 测试异步代码时使用pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### 测试隔离问题

```python
# 确保测试之间相互独立
@pytest.fixture
def isolated_character(test_client):
    """创建隔离的角色数据"""
    character_data = TestDataGenerator.create_character_data()
    response = test_client.post('/api/v1/characters', json=character_data)
    character = response.get_json()
    
    yield character
    
    # 清理：删除创建的角色
    test_client.delete(f"/api/v1/characters/{character['id']}")
```

### 2. 调试技巧

#### 启用详细日志

```python
import logging

@pytest.fixture(autouse=True)
def enable_debug_logging():
    """启用调试日志"""
    logging.basicConfig(level=logging.DEBUG)
    yield
    logging.getLogger().handlers.clear()
```

#### 使用pdb调试

```python
def test_complex_scenario(test_client):
    """复杂场景测试"""
    # 在测试中设置断点
    import pdb; pdb.set_trace()
    
    # 测试逻辑
    pass
```

#### 生成测试数据快照

```python
def test_data_snapshot(test_client, tmp_path):
    """生成测试数据快照用于调试"""
    # 创建测试数据
    character_data = TestDataGenerator.create_character_data()
    response = test_client.post('/api/v1/characters', json=character_data)
    
    # 保存快照
    snapshot_file = tmp_path / "test_character_snapshot.json"
    with open(snapshot_file, 'w') as f:
        json.dump(response.get_json(), f, indent=2)
    
    print(f"测试数据快照保存在: {snapshot_file}")
```

## 总结

本指南涵盖了SuperRPG项目集成测试的关键方面：

1. **测试环境设置**：数据库、容器、客户端配置
2. **测试结构**：模块化组织集成测试
3. **测试编写**：各种集成场景的测试实现
4. **数据管理**：测试数据生成和清理
5. **测试执行**：运行并行测试和标记测试
6. **CI/CD集成**：自动化测试流程
7. **故障排除**：常见问题和调试技巧

通过遵循这些指南，您可以构建全面、可靠的集成测试套件，确保SuperRPG项目的各个组件能够正确协同工作。