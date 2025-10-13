# API使用指南

本指南详细介绍如何使用SuperRPG项目的各种API，包括角色卡管理、传说书管理、提示模板管理等核心功能。

## 目录

- [快速开始](#快速开始)
- [认证](#认证)
- [角色卡API](#角色卡api)
- [传说书API](#传说书api)
- [提示模板API](#提示模板api)
- [世界管理API](#世界管理api)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

## 快速开始

### 基础URL

所有API请求都基于以下基础URL：
```
http://localhost:8000/api/v1
```

### 简单示例

```python
import requests

# 获取所有角色卡
response = requests.get("http://localhost:8000/api/v1/characters")
if response.status_code == 200:
    characters = response.json()
    print(f"找到 {len(characters)} 个角色卡")
```

## 认证

目前SuperRPG API使用简单的Bearer Token认证。

### 获取Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
```

### 使用Token

```python
headers = {
    "Authorization": "Bearer your_token_here",
    "Content-Type": "application/json"
}

response = requests.get("http://localhost:8000/api/v1/characters", headers=headers)
```

## 角色卡API

### 获取所有角色卡

```http
GET /api/v1/characters
```

**查询参数:**
- `page` (可选): 页码，默认为1
- `limit` (可选): 每页数量，默认为20
- `race` (可选): 按种族筛选
- `class` (可选): 按职业筛选
- `level_min` (可选): 最低等级
- `level_max` (可选): 最高等级

**示例:**
```python
# 获取所有1-5级的精灵角色
params = {
    "race": "精灵",
    "level_min": 1,
    "level_max": 5
}
response = requests.get("http://localhost:8000/api/v1/characters", params=params)
```

**响应:**
```json
{
    "characters": [
        {
            "id": "char_123",
            "name": "艾莉娅",
            "race": "精灵",
            "class": "法师",
            "level": 3,
            "attributes": {
                "力量": 8,
                "敏捷": 14,
                "体质": 10,
                "智力": 16,
                "感知": 12,
                "魅力": 13
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "limit": 20
}
```

### 获取单个角色卡

```http
GET /api/v1/characters/{character_id}
```

**示例:**
```python
character_id = "char_123"
response = requests.get(f"http://localhost:8000/api/v1/characters/{character_id}")
```

### 创建角色卡

```http
POST /api/v1/characters
```

**请求体:**
```json
{
    "name": "新角色",
    "race": "人类",
    "class": "战士",
    "level": 1,
    "attributes": {
        "力量": 16,
        "敏捷": 12,
        "体质": 14,
        "智力": 10,
        "感知": 12,
        "魅力": 10
    },
    "background": "士兵",
    "appearance": "中等身材，黑色头发，棕色眼睛",
    "personality": ["勇敢", "正直"],
    "backstory": "一个普通的冒险者"
}
```

**示例:**
```python
character_data = {
    "name": "索林",
    "race": "矮人",
    "class": "战士",
    "level": 1,
    "attributes": {
        "strength": 16,
        "dexterity": 12,
        "constitution": 15,
        "intelligence": 10,
        "wisdom": 12,
        "charisma": 8
    }
}

response = requests.post(
    "http://localhost:8000/api/v1/characters",
    json=character_data,
    headers=headers
)

if response.status_code == 201:
    new_character = response.json()
    print(f"创建角色成功，ID: {new_character['id']}")
```

### 更新角色卡

```http
PATCH /api/v1/characters/{character_id}
```

**示例:**
```python
update_data = {
    "level": 2,
    "attributes": {
        "strength": 17
    }
}

response = requests.patch(
    f"http://localhost:8000/api/v1/characters/{character_id}",
    json=update_data,
    headers=headers
)
```

### 删除角色卡

```http
DELETE /api/v1/characters/{character_id}
```

**示例:**
```python
response = requests.delete(
    f"http://localhost:8000/api/v1/characters/{character_id}",
    headers=headers
)
```

## 传说书API

### 获取所有传说书条目

```http
GET /api/v1/lorebook
```

**查询参数:**
- `page` (可选): 页码
- `limit` (可选): 每页数量
- `category` (可选): 按类别筛选
- `keywords` (可选): 关键词搜索

**示例:**
```python
# 搜索包含"魔法"的传说书条目
params = {
    "keywords": "魔法",
    "category": "传说"
}
response = requests.get("http://localhost:8000/api/v1/lorebook", params=params)
```

### 创建传说书条目

```http
POST /api/v1/lorebook
```

**请求体:**
```json
{
    "title": "神秘的魔法石",
    "category": "物品",
    "keywords": ["魔法", "石头", "神秘"],
    "content": "这是一块蕴含着强大魔力的神秘石头...",
    "importance": 3,
    "verified": false,
    "source": "古代文献"
}
```

**示例:**
```python
entry_data = {
    "title": "暗影森林",
    "category": "地点",
    "keywords": ["森林", "暗影", "危险"],
    "content": "暗影森林是一片充满危险的神秘森林...",
    "importance": 4
}

response = requests.post(
    "http://localhost:8000/api/v1/lorebook",
    json=entry_data,
    headers=headers
)
```

### 搜索传说书

```http
GET /api/v1/lorebook/search
```

**查询参数:**
- `q` (必需): 搜索关键词
- `category` (可选): 类别筛选
- `limit` (可选): 结果数量限制

**示例:**
```python
params = {
    "q": "龙",
    "category": "生物",
    "limit": 10
}
response = requests.get("http://localhost:8000/api/v1/lorebook/search", params=params)
```

## 提示模板API

### 获取所有提示模板

```http
GET /api/v1/prompts/templates
```

**查询参数:**
- `category` (可选): 按类别筛选
- `tags` (可选): 按标签筛选

### 创建提示模板

```http
POST /api/v1/prompts/templates
```

**请求体:**
```json
{
    "name": "对话模板",
    "category": "对话",
    "description": "用于角色对话的提示模板",
    "sections": [
        {
            "name": "角色设定",
            "content": "你是{character_name}，一个{race}{class}。",
            "order": 1,
            "required": true
        },
        {
            "name": "场景描述",
            "content": "你在{location}，正在{situation}。",
            "order": 2,
            "required": true
        }
    ],
    "variables": {
        "character_name": {
            "type": "string",
            "description": "角色名称",
            "default": "未知角色",
            "required": true
        },
        "race": {
            "type": "string",
            "description": "种族",
            "default": "人类",
            "required": true
        }
    }
}
```

### 组装提示

```http
POST /api/v1/prompts/templates/{template_id}/assemble
```

**请求体:**
```json
{
    "variables": {
        "character_name": "艾莉娅",
        "race": "精灵",
        "class": "法师",
        "location": "魔法塔",
        "situation": "研究古老魔法"
    }
}
```

**示例:**
```python
template_id = "template_123"
variables = {
    "character_name": "艾莉娅",
    "race": "精灵",
    "class": "法师",
    "location": "魔法塔",
    "situation": "研究古老魔法"
}

response = requests.post(
    f"http://localhost:8000/api/v1/prompts/templates/{template_id}/assemble",
    json={"variables": variables},
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"组装的提示:\n{result['prompt']}")
```

## 世界管理API

### 获取世界信息

```http
GET /api/v1/worlds/{world_id}
```

### 创建世界

```http
POST /api/v1/worlds
```

**请求体:**
```json
{
    "name": "艾尔德利亚",
    "description": "一个充满魔法和冒险的世界",
    "type": "奇幻",
    "regions": [
        {
            "name": "北境森林",
            "description": "位于北方的神秘森林",
            "climate": "温带",
            "population": 50000
        }
    ],
    "factions": [
        {
            "name": "守护者联盟",
            "description": "保护世界的英雄组织",
            "type": "军事",
            "influence": 8
        }
    ]
}
```

## 错误处理

### 错误响应格式

所有API错误都遵循统一的响应格式：

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求参数验证失败",
        "details": {
            "field": "level",
            "message": "等级必须是1-20之间的整数"
        }
    },
    "timestamp": "2023-01-01T00:00:00Z",
    "path": "/api/v1/characters"
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 描述 |
|--------|------------|------|
| `VALIDATION_ERROR` | 400 | 请求参数验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `CONFLICT` | 409 | 资源冲突 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 错误处理示例

```python
def handle_api_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        error_data = response.json()
        error_code = error_data.get('error', {}).get('code', 'UNKNOWN_ERROR')
        error_message = error_data.get('error', {}).get('message', '未知错误')
        
        print(f"API错误 [{error_code}]: {error_message}")
        
        # 根据错误类型进行特定处理
        if error_code == "VALIDATION_ERROR":
            # 处理验证错误
            details = error_data.get('error', {}).get('details', {})
            for field, message in details.items():
                print(f"字段 '{field}': {message}")
        
        return None

# 使用示例
response = requests.post("http://localhost:8000/api/v1/characters", json={})
result = handle_api_response(response)
```

## 最佳实践

### 1. 使用会话保持连接

```python
import requests

# 创建会话对象
session = requests.Session()
session.headers.update({
    "Authorization": "Bearer your_token",
    "Content-Type": "application/json"
})

# 使用会话发送请求
response = session.get("http://localhost:8000/api/v1/characters")
```

### 2. 处理分页

```python
def get_all_characters():
    all_characters = []
    page = 1
    limit = 50
    
    while True:
        response = session.get(
            "http://localhost:8000/api/v1/characters",
            params={"page": page, "limit": limit}
        )
        
        data = response.json()
        characters = data.get('characters', [])
        all_characters.extend(characters)
        
        # 检查是否还有更多数据
        if len(characters) < limit:
            break
            
        page += 1
    
    return all_characters
```

### 3. 重试机制

```python
import time
from requests.exceptions import RequestException

def api_request_with_retry(method, url, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            response = session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"请求失败，重试中... ({attempt + 1}/{max_retries})")
            time.sleep(2 ** attempt)  # 指数退避
```

### 4. 批量操作

```python
def create_multiple_characters(characters_data):
    """批量创建角色卡"""
    created_characters = []
    
    for character_data in characters_data:
        try:
            response = session.post(
                "http://localhost:8000/api/v1/characters",
                json=character_data
            )
            
            if response.status_code == 201:
                created_characters.append(response.json())
                print(f"成功创建角色: {character_data['name']}")
            else:
                print(f"创建角色失败: {character_data['name']}")
                
        except Exception as e:
            print(f"创建角色时出错: {str(e)}")
    
    return created_characters
```

### 5. 缓存策略

```python
import functools
import time

def cache_result(ttl=300):  # 5分钟缓存
    def decorator(func):
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            if key in cache and now - cache[key]['timestamp'] < ttl:
                return cache[key]['result']
            
            result = func(*args, **kwargs)
            cache[key] = {
                'result': result,
                'timestamp': now
            }
            
            return result
        
        return wrapper
    return decorator

@cache_result(ttl=600)  # 10分钟缓存
def get_character(character_id):
    return session.get(f"http://localhost:8000/api/v1/characters/{character_id}").json()
```

### 6. 异步请求

```python
import asyncio
import aiohttp

async def fetch_character_async(session, character_id):
    url = f"http://localhost:8000/api/v1/characters/{character_id}"
    async with session.get(url) as response:
        return await response.json()

async def get_multiple_characters_async(character_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_character_async(session, cid) for cid in character_ids]
        return await asyncio.gather(*tasks)

# 使用示例
character_ids = ["char_1", "char_2", "char_3"]
characters = asyncio.run(get_multiple_characters_async(character_ids))
```

## 完整示例

以下是一个完整的示例，展示了如何使用API创建角色卡、创建传说书条目，并组装提示：

```python
import requests
import json

class SuperRPGClient:
    def __init__(self, base_url="http://localhost:8000/api/v1", token=None):
        self.base_url = base_url
        self.session = requests.Session()
        
        if token:
            self.session.headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            })
    
    def create_character(self, character_data):
        """创建角色卡"""
        response = self.session.post(
            f"{self.base_url}/characters",
            json=character_data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            self._handle_error(response)
    
    def create_lorebook_entry(self, entry_data):
        """创建传说书条目"""
        response = self.session.post(
            f"{self.base_url}/lorebook",
            json=entry_data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            self._handle_error(response)
    
    def create_prompt_template(self, template_data):
        """创建提示模板"""
        response = self.session.post(
            f"{self.base_url}/prompts/templates",
            json=template_data
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            self._handle_error(response)
    
    def assemble_prompt(self, template_id, variables):
        """组装提示"""
        response = self.session.post(
            f"{self.base_url}/prompts/templates/{template_id}/assemble",
            json={"variables": variables}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            self._handle_error(response)
    
    def _handle_error(self, response):
        """处理API错误"""
        try:
            error_data = response.json()
            error_code = error_data.get('error', {}).get('code', 'UNKNOWN_ERROR')
            error_message = error_data.get('error', {}).get('message', '未知错误')
            
            print(f"API错误 [{error_code}]: {error_message}")
            
            if response.status_code == 422:
                details = error_data.get('error', {}).get('details', {})
                for field, message in details.items():
                    print(f"字段 '{field}': {message}")
        except:
            print(f"HTTP错误: {response.status_code} - {response.text}")
        
        return None

# 使用示例
def main():
    # 创建客户端
    client = SuperRPGClient()
    
    # 1. 创建角色卡
    character_data = {
        "name": "艾莉娅·星辰使者",
        "race": "精灵",
        "class": "法师",
        "level": 3,
        "attributes": {
            "strength": 8,
            "dexterity": 14,
            "constitution": 10,
            "intelligence": 16,
            "wisdom": 12,
            "charisma": 13
        },
        "background": "学者",
        "appearance": "高挑优雅的精灵，银色长发，蓝色眼眸",
        "personality": ["智慧", "好奇", "谨慎"],
        "backstory": "来自古老精灵王国的法师，致力于研究失落的魔法知识"
    }
    
    character = client.create_character(character_data)
    if not character:
        print("创建角色失败")
        return
    
    print(f"创建角色成功: {character['name']} (ID: {character['id']})")
    
    # 2. 创建传说书条目
    lorebook_data = {
        "title": "星辰之塔",
        "category": "地点",
        "keywords": ["塔", "星辰", "魔法", "古老"],
        "content": "星辰之塔是一座古老的魔法塔，据说建于远古时代。塔内收藏着大量失落的魔法知识，只有被选中的人才能进入。",
        "importance": 4,
        "source": "古老文献"
    }
    
    lorebook_entry = client.create_lorebook_entry(lorebook_data)
    if not lorebook_entry:
        print("创建传说书条目失败")
        return
    
    print(f"创建传说书条目成功: {lorebook_entry['title']} (ID: {lorebook_entry['id']})")
    
    # 3. 创建提示模板
    template_data = {
        "name": "角色探索模板",
        "category": "探索",
        "description": "用于角色探索场景的提示模板",
        "sections": [
            {
                "name": "角色设定",
                "content": "你是{character_name}，一个{race}{class}。",
                "order": 1,
                "required": True
            },
            {
                "name": "当前场景",
                "content": "你正在{location}，这里{description}。",
                "order": 2,
                "required": True
            },
            {
                "name": "行动指导",
                "content": "你的目标是{goal}。请以角色的视角描述你的行动和想法。",
                "order": 3,
                "required": True
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
                "description": "当前位置",
                "required": True
            },
            "description": {
                "type": "string",
                "description": "地点描述",
                "required": True
            },
            "goal": {
                "type": "string",
                "description": "当前目标",
                "required": True
            }
        }
    }
    
    template = client.create_prompt_template(template_data)
    if not template:
        print("创建提示模板失败")
        return
    
    print(f"创建提示模板成功: {template['name']} (ID: {template['id']})")
    
    # 4. 组装提示
    prompt_variables = {
        "character_name": character['name'],
        "race": character['race'],
        "class": character['class'],
        "location": lorebook_entry['title'],
        "description": "一座古老的魔法塔，收藏着大量失落的魔法知识",
        "goal": "寻找关于星辰魔法的古老知识"
    }
    
    prompt_result = client.assemble_prompt(template['id'], prompt_variables)
    if not prompt_result:
        print("组装提示失败")
        return
    
    print("\n=== 组装的提示 ===")
    print(prompt_result['prompt'])

if __name__ == "__main__":
    main()
```

## 总结

本指南涵盖了SuperRPG项目的主要API使用方法，包括：

1. **角色卡管理**：创建、查询、更新、删除角色卡
2. **传说书管理**：创建、搜索、管理传说书条目
3. **提示模板管理**：创建模板、组装提示
4. **世界管理**：创建和管理世界信息
5. **错误处理**：统一处理API错误
6. **最佳实践**：会话管理、重试机制、缓存策略等

通过遵循这些指南和最佳实践，您可以有效地使用SuperRPG API来构建强大的RPG应用。