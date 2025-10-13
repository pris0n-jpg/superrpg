# SuperRPG 演示数据

这个目录包含了 SuperRPG 系统的演示数据，用于展示系统的各项功能。

## 目录结构

```
demo_data/
├── characters/          # 示例角色卡文件
│   ├── elf_mage.json     # 精灵法师角色卡
│   └── dwarf_warrior.json # 矮人战士角色卡
├── lorebooks/           # 示例传说书文件
│   └── star_magic.json  # 星辰魔法传说书
├── templates/           # 示例提示模板文件
│   └── character_dialogue.json # 角色对话模板
├── configs/             # 示例配置文件
│   └── demo_config.json # 演示应用配置
└── README.md            # 本文件
```

## 数据说明

### 角色卡 (characters/)

角色卡文件包含了角色的详细信息，包括：

- **基本信息**：名称、描述、第一句话、示例消息等
- **属性数据**：能力值、统计数据、生命值等
- **背景设定**：场景、性格概述、创建者笔记等
- **游戏数据**：技能、豁免、物品栏等

示例角色：

1. **艾莉娅·星辰使者** (elf_mage.json)
   - 精灵法师，擅长星辰魔法
   - 智力高，适合作为知识向导
   - 拥有丰富的魔法知识背景

2. **索林·铁须** (dwarf_warrior.json)
   - 矮人战士，勇敢忠诚
   - 力量高，适合作为战斗伙伴
   - 拥有丰富的战斗经验

### 传说书 (lorebooks/)

传说书文件包含了游戏世界的知识体系，包括：

- **基本信息**：名称、描述、版本、标签等
- **条目内容**：具体的知识条目，包括内容、关键词、激活规则等
- **元数据**：难度、法力消耗、施法时间等附加信息

示例传说书：

1. **星辰魔法体系** (star_magic.json)
   - 包含星光治疗术、星辰预言、星象解读等条目
   - 适合作为魔法系统的知识基础

### 提示模板 (templates/)

提示模板文件用于生成角色对话的提示，包括：

- **模板结构**：不同类型的段落（系统指令、上下文、历史记录等）
- **变量定义**：模板中使用的变量列表
- **优先级设置**：段落的显示优先级

示例模板：

1. **角色对话模板** (character_dialogue.json)
   - 包含系统指令、上下文、历史记录等部分
   - 适合生成各种角色的对话回应

### 配置文件 (configs/)

配置文件包含了系统的各种配置选项：

- **应用配置**：基本信息、调试选项等
- **数据库配置**：连接信息、池设置等
- **API配置**：主机、端口、中间件等
- **功能开关**：各项功能的启用/禁用
- **服务配置**：各种服务的参数设置

示例配置：

1. **演示应用配置** (demo_config.json)
   - 包含演示应用所需的所有配置
   - 适合作为系统配置的参考模板

## 使用方法

### 1. 在演示应用中使用

演示应用会自动加载这些示例数据：

```bash
cd src/demo
python demo_application.py
```

### 2. 在测试中使用

测试文件可以引用这些示例数据：

```python
# 加载示例角色卡
with open('demo_data/characters/elf_mage.json', 'r') as f:
    character_data = json.load(f)
```

### 3. 在开发中使用

开发过程中可以使用这些数据作为参考：

```python
# 创建角色卡
character = CharacterCard.from_dict(character_data)
```

## 数据格式

所有数据文件都采用 JSON 格式，遵循 SuperRPG 系统的数据模型。

### 角色卡格式

```json
{
  "id": "unique_id",
  "name": "角色名称",
  "description": "角色描述",
  "first_message": "第一句话",
  "example_messages": ["示例消息1", "示例消息2"],
  "scenario": "场景描述",
  "personality_summary": "性格概述",
  "creator_notes": "创建者笔记",
  "tags": ["标签1", "标签2"],
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
  "proficient_skills": ["技能1", "技能2"],
  "proficient_saves": ["豁免1", "豁免2"],
  "inventory": {"物品1": 1, "物品2": 2}
}
```

### 传说书格式

```json
{
  "id": "unique_id",
  "name": "传说书名称",
  "description": "传说书描述",
  "version": "1.0.0",
  "tags": ["标签1", "标签2"],
  "entries": [
    {
      "id": "entry_id",
      "title": "条目标题",
      "content": "条目内容",
      "keywords": [
        {
          "pattern": "关键词",
          "type": "EXACT",
          "case_sensitive": false,
          "weight": 10
        }
      ],
      "activation_rule": {
        "type": "ANY",
        "priority": 1,
        "max_activations": 5,
        "cooldown_seconds": 60
      },
      "tags": ["标签1", "标签2"],
      "metadata": {"key": "value"}
    }
  ]
}
```

### 提示模板格式

```json
{
  "id": "template_id",
  "name": "模板名称",
  "description": "模板描述",
  "sections": [
    {
      "id": "section_id",
      "content": "段落内容，支持变量 {variable_name}",
      "section_type": "SYSTEM",
      "priority": 1,
      "enabled": true
    }
  ],
  "variables": ["variable1", "variable2"],
  "is_active": true
}
```

## 扩展数据

如果需要添加更多示例数据，请遵循以下原则：

1. **保持格式一致**：使用相同的 JSON 结构和字段命名
2. **提供完整信息**：确保所有必填字段都有值
3. **符合角色设定**：内容要与角色背景和性格一致
4. **添加适当注释**：在复杂字段上添加说明
5. **验证数据有效性**：确保数据可以正常加载和使用

## 贡献指南

欢迎提交更多的示例数据！请确保：

1. 数据格式正确，可以通过 JSON 验证
2. 内容原创或已获得适当授权
3. 符合 SuperRPG 的世界观和设定
4. 包含适当的元数据和标签

提交前请运行相关测试，确保数据不会破坏现有功能。