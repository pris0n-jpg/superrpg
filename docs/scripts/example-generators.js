// 示例代码生成器
window.exampleGenerators = {
    // 角色管理示例
    characterExample: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">角色管理示例</h1>
                    <p class="card-subtitle">Character Management Examples - 角色创建、修改和查询的完整示例</p>
                </div>
                <div class="card-body">
                    <div class="example-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            本示例展示了如何使用SuperRPG系统进行角色管理，包括角色创建、属性设置、状态管理等核心功能。
                        </div>
                        
                        <h2>基础角色创建</h2>
                        <div class="code-example">
                            <div class="code-title">从D&D配置创建角色</div>
                            <pre><code class="language-python"># 导入必要的模块
from src.domain.models.characters import Character
from src.domain.services.character_service import CharacterService
from src.core.container import DIContainer

# 创建依赖注入容器
container = DIContainer()
container.register_singleton(CharacterService, CharacterServiceImpl)
container.register_singleton(CharacterRepository, InMemoryCharacterRepository)

# 解析服务
character_service = container.resolve(CharacterService)
character_repository = container.resolve(CharacterRepository)

# D&D角色配置
dnd_config = {
    "level": 1,
    "hp": 10,
    "max_hp": 10,
    "abilities": {
        "STR": 8,
        "DEX": 14,
        "CON": 12,
        "INT": 16,
        "WIS": 12,
        "CHA": 12
    },
    "armor_class": 12,
    "proficiency_bonus": 2,
    "proficient_skills": ["医学", "洞察"],
    "proficient_saves": ["智力", "感知"]
}

# 创建角色
character = character_service.create_character_from_dnd_config(
    name="Amiya",
    dnd_config=dnd_config
)

print(f"角色创建成功: {character.name}")
print(f"生命值: {character.hp}/{character.max_hp}")
print(f"护甲等级: {character.stats.armor_class}")
print(f"力量修正: {character.abilities.get_modifier('STR')}")</code></pre>
                        </div>
                        
                        <h2>角色属性管理</h2>
                        <div class="code-example">
                            <div class="code-title">修改角色属性</div>
                            <pre><code class="language-python"># 角色受到伤害
def apply_damage(character: Character, damage: int) -> bool:
    """对角色造成伤害，返回角色是否存活"""
    character.take_damage(damage)
    
    if character.hp <= 0:
        print(f"{character.name} 被击败了！")
        return False
    else:
        print(f"{character.name} 受到 {damage} 点伤害，剩余 HP: {character.hp}")
        return True

# 角色恢复生命值
def heal_character(character: Character, heal_amount: int) -> int:
    """为角色恢复生命值，返回实际恢复量"""
    old_hp = character.hp
    character.hp = min(character.hp + heal_amount, character.max_hp)
    actual_heal = character.hp - old_hp
    
    print(f"{character.name} 恢复了 {actual_heal} 点生命值，当前 HP: {character.hp}")
    return actual_heal

# 使用示例
character = character_service.create_character_from_dnd_config("Amiya", dnd_config)

# 造成伤害
apply_damage(character, 5)  # Amiya 受到 5 点伤害，剩余 HP: 5

# 恢复生命值
heal_character(character, 3)  # Amiya 恢复了 3 点生命值，当前 HP: 8</code></pre>
                        </div>
                        
                        <h2>角色位置管理</h2>
                        <div class="code-example">
                            <div class="code-title">移动角色和计算距离</div>
                            <pre><code class="language-python">from src.domain.models.base import Position

# 创建位置对象
position1 = Position(0, 0)  # 原点
position2 = Position(3, 4)  # (3, 4)

# 移动角色到新位置
def move_character(character: Character, new_position: Position):
    """移动角色到新位置"""
    old_position = character.position
    character.position = new_position
    
    print(f"{character.name} 从 {old_position} 移动到 {new_position}")
    
    # 计算移动距离
    if old_position:
        distance = new_position.distance_to(old_position)
        print(f"移动距离: {distance} 格")

# 使用示例
character.position = Position(0, 0)
move_character(character, Position(2, 3))  # Amiya 从 (0, 0) 移动到 (2, 3)

# 计算两个位置之间的距离
distance = position1.distance_to(position2)
print(f"位置 {position1} 到 {position2} 的距离: {distance} 格")</code></pre>
                        </div>
                        
                        <h2>角色能力值计算</h2>
                        <div class="code-example">
                            <div class="code-title">能力修正值和技能检定</div>
                            <pre><code class="language-python"># 获取能力修正值
def get_ability_modifier(character: Character, ability: str) -> int:
    """获取角色的能力修正值"""
    return character.abilities.get_modifier(ability)

# 进行技能检定
def skill_check(character: Character, skill: str, dc: int, advantage: bool = False) -> bool:
    """进行技能检定"""
    # 获取相关能力值（简化示例）
    ability_map = {
        "医学": "INT",
        "洞察": "WIS",
        "运动": "DEX",
        "威吓": "CHA"
    }
    
    ability = ability_map.get(skill, "STR")
    modifier = get_ability_modifier(character, ability)
    
    # 检查是否熟练
    is_proficient = skill in character.proficient_skills
    proficiency_bonus = character.stats.proficiency_bonus if is_proficient else 0
    
    # 模拟掷骰子
    import random
    roll = random.randint(1, 20)
    
    # 处理优势/劣势
    if advantage:
        roll = max(random.randint(1, 20), random.randint(1, 20))
    
    total = roll + modifier + proficiency_bonus
    success = total >= dc
    
    print(f"{character.name} 进行 {skill} 检定:")
    print(f"  骰子: {roll} + {ability}修正({modifier}) + 熟练加值({proficiency_bonus}) = {total}")
    print(f"  难度等级: {dc}")
    print(f"  结果: {'成功' if success else '失败'}")
    
    return success

# 使用示例
character = character_service.create_character_from_dnd_config("Amiya", dnd_config)

# 进行医学检定
skill_check(character, "医学", 15)  # Amiya 进行医学检定，难度15

# 进行洞察检定（有优势）
skill_check(character, "洞察", 12, advantage=True)  # Amiya 进行洞察检定，难度12，有优势</code></pre>
                        </div>
                        
                        <h2>角色状态查询</h2>
                        <div class="code-example">
                            <div class="code-title">获取角色状态快照</div>
                            <pre><code class="language-python">def get_character_status(character: Character) -> dict:
    """获取角色状态快照"""
    return {
        "name": character.name,
        "level": character.stats.level,
        "hp": character.hp,
        "max_hp": character.max_hp,
        "hp_percentage": (character.hp / character.max_hp) * 100,
        "armor_class": character.stats.armor_class,
        "position": character.position,
        "abilities": {
            "STR": character.abilities.strength,
            "DEX": character.abilities.dexterity,
            "CON": character.abilities.constitution,
            "INT": character.abilities.intelligence,
            "WIS": character.abilities.wisdom,
            "CHA": character.abilities.charisma
        },
        "ability_modifiers": {
            "STR": character.abilities.get_modifier('STR'),
            "DEX": character.abilities.get_modifier('DEX'),
            "CON": character.abilities.get_modifier('CON'),
            "INT": character.abilities.get_modifier('INT'),
            "WIS": character.abilities.get_modifier('WIS'),
            "CHA": character.abilities.get_modifier('CHA')
        },
        "proficient_skills": character.proficient_skills,
        "proficient_saves": character.proficient_saves,
        "is_alive": character.hp > 0
    }

# 使用示例
character = character_service.create_character_from_dnd_config("Amiya", dnd_config)
status = get_character_status(character)

print(f"角色状态: {status['name']}")
print(f"等级: {status['level']}")
print(f"生命值: {status['hp']}/{status['max_hp']} ({status['hp_percentage']:.1f}%)")
print(f"护甲等级: {status['armor_class']}")
print(f"位置: {status['position']}")
print(f"力量值: {status['abilities']['STR']} (修正: {status['ability_modifiers']['STR']})")
print(f"是否存活: {'是' if status['is_alive'] else '否'}")</code></pre>
                        </div>
                        
                        <h2>完整示例：角色管理流程</h2>
                        <div class="code-example">
                            <div class="code-title">完整的角色管理流程</div>
                            <pre><code class="language-python">class CharacterManager:
    def __init__(self, character_service: CharacterService):
        self.character_service = character_service
        self.characters = {}
    
    def create_character_from_config(self, name: str, config: dict) -> Character:
        """从配置创建角色"""
        character = self.character_service.create_character_from_dnd_config(name, config)
        self.characters[name] = character
        return character
    
    def get_character(self, name: str) -> Optional[Character]:
        """获取角色"""
        return self.characters.get(name)
    
    def list_characters(self) -> List[str]:
        """列出所有角色名称"""
        return list(self.characters.keys())
    
    def simulate_combat_round(self, attacker_name: str, defender_name: str) -> dict:
        """模拟一轮战斗"""
        attacker = self.get_character(attacker_name)
        defender = self.get_character(defender_name)
        
        if not attacker or not defender:
            raise ValueError("角色不存在")
        
        # 简化的攻击模拟
        attack_roll = random.randint(1, 20)
        attack_modifier = attacker.abilities.get_modifier('STR')
        attack_total = attack_roll + attack_modifier
        
        defender_ac = defender.stats.armor_class
        hit = attack_total >= defender_ac
        
        result = {
            "attacker": attacker_name,
            "defender": defender_name,
            "attack_roll": attack_roll,
            "attack_modifier": attack_modifier,
            "attack_total": attack_total,
            "defender_ac": defender_ac,
            "hit": hit
        }
        
        if hit:
            # 计算伤害
            damage = random.randint(1, 6) + attacker.abilities.get_modifier('STR')
            defender.take_damage(damage)
            result["damage"] = damage
            result["defender_hp"] = defender.hp
            result["defender_alive"] = defender.hp > 0
        else:
            result["damage"] = 0
            result["defender_hp"] = defender.hp
            result["defender_alive"] = True
        
        return result

# 使用示例
manager = CharacterManager(character_service)

# 创建多个角色
amiya_config = {
    "level": 1, "hp": 10, "max_hp": 10,
    "abilities": {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 12, "CHA": 12},
    "armor_class": 12
}

goblin_config = {
    "level": 1, "hp": 7, "max_hp": 7,
    "abilities": {"STR": 12, "DEX": 14, "CON": 13, "INT": 8, "WIS": 10, "CHA": 8},
    "armor_class": 14
}

amiya = manager.create_character_from_config("Amiya", amiya_config)
goblin = manager.create_character_from_config("Goblin", goblin_config)

# 模拟战斗
print("=== 战斗模拟 ===")
result = manager.simulate_combat_round("Amiya", "Goblin")
print(f"{result['attacker']} 攻击 {result['defender']}:")
print(f"  攻击掷骰: {result['attack_roll']} + {result['attack_modifier']} = {result['attack_total']}")
print(f"  对方AC: {result['defender_ac']}")
print(f"  结果: {'命中' if result['hit'] else '未命中'}")

if result['hit']:
    print(f"  伤害: {result['damage']}")
    print(f"  {result['defender']} 剩余HP: {result['defender_hp']}")
    print(f"  {result['defender']} 状态: {'存活' if result['defender_alive'] else '被击败'}")</code></pre>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .example-overview {
                margin-bottom: 2rem;
            }
            
            .code-example {
                margin: 2rem 0;
            }
            
            .example-section {
                margin-bottom: 3rem;
                padding: 2rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .example-section h2 {
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
            </style>
        `;
    },
    
    // 世界状态示例
    worldExample: function() {
        return `
            <div class="card">
                <div class="card-header">
                    <h1 class="card-title">世界状态示例</h1>
                    <p class="card-subtitle">World State Examples - 世界创建、场景设置、时间推进和关系管理的完整示例</p>
                </div>
                <div class="card-body">
                    <div class="example-overview">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            本示例展示了如何使用SuperRPG系统进行世界状态管理，包括世界创建、场景设置、时间推进、关系管理等核心功能。
                        </div>
                        
                        <h2>世界创建和初始化</h2>
                        <div class="code-example">
                            <div class="code-title">创建世界</div>
                            <pre><code class="language-python"># 导入必要的模块
from src.domain.models.world import World
from src.domain.services.world_service import WorldService
from src.core.container import DIContainer

# 创建依赖注入容器
container = DIContainer()
container.register_singleton(WorldService, WorldServiceImpl)
container.register_singleton(WorldRepository, InMemoryWorldRepository)

# 解析服务
world_service = container.resolve(WorldService)
world_repository = container.resolve(WorldRepository)

# 世界配置
world_config = {
    "name": "旧城区",
    "time_min": 0,
    "weather": "晴朗",
    "temperature": "温暖",
    "visibility": "良好"
}

# 创建世界
world = world_service.create_world(world_config)

print(f"世界创建成功: {world.name}")
print(f"当前时间: {world.time_min} 分钟")
print(f"天气: {world.weather}")
print(f"温度: {world.temperature}")
print(f"能见度: {world.visibility}")</code></pre>
                        </div>
                        
                        <h2>场景设置</h2>
                        <div class="code-example">
                            <div class="code-title">设置场景和目标</div>
                            <pre><code class="language-python"># 场景配置
scene_config = {
    "name": "北侧仓棚",
    "description": "一个破旧的木质仓棚，堆放着各种杂物和废弃的工具",
    "time_min": 480,  # 下午8点
    "weather": "阴天",
    "objectives": [
        {
            "name": "调查仓棚",
            "description": "仔细搜索仓棚内可能的有用物品",
            "priority": "high"
        },
        {
            "name": "寻找线索",
            "description": "寻找关于失踪人员的线索",
            "priority": "medium"
        }
    ],
    "details": [
        "空气中弥漫着灰尘和木屑的味道",
        "角落里堆放着生锈的工具",
        "天花板上有一个破洞，透出微弱的光线"
    ]
}

# 设置场景
world_service.set_scene(
    world=world,
    name=scene_config["name"],
    objectives=scene_config["objectives"],
    details=scene_config["details"],
    time_min=scene_config["time_min"],
    weather=scene_config["weather"]
)

print(f"场景设置: {scene_config['name']}")
print(f"目标数量: {len(scene_config['objectives'])}")
print(f"当前时间: {world.time_min} 分钟")
print(f"天气: {world.weather}")

# 检查目标状态
for objective in world.objective_tracker.objectives:
    status = world.objective_tracker.get_status(objective.name)
    print(f"目标 '{objective.name}': {status}")</code></pre>
                        </div>
                        
                        <h2>时间推进</h2>
                        <div class="code-example">
                            <div class="code-title">时间管理和事件调度</div>
                            <pre><code class="language-python">class TimeManager:
    def __init__(self, world_service: WorldService):
        self.world_service = world_service
        self.world = None
    
    def set_world(self, world: World):
        """设置当前世界"""
        self.world = world
    
    def advance_time(self, minutes: int) -> dict:
        """推进时间"""
        if not self.world:
            raise ValueError("未设置世界")
        
        old_time = self.world.time_min
        self.world.time_min += minutes
        
        # 检查是否有预定的定时事件
        triggered_events = self.check_scheduled_events()
        
        # 更新天气（简化示例）
        if random.random() < 0.1:  # 10%概率天气变化
            self.world.weather = self.random_weather()
            weather_change = True
        else:
            weather_change = False
        
        result = {
            "old_time": old_time,
            "new_time": self.world.time_min,
            "advanced_minutes": minutes,
            "weather_change": weather_change,
            "new_weather": self.world.weather if weather_change else None,
            "triggered_events": triggered_events
        }
        
        print(f"时间推进: {minutes} 分钟")
        print(f"从 {old_time} 分钟到 {self.world.time_min} 分钟")
        
        if weather_change:
            print(f"天气变化: {result['new_weather']}")
        
        if triggered_events:
            print(f"触发了 {len(triggered_events)} 个事件")
            for event in triggered_events:
                print(f"  - {event}")
        
        return result
    
    def check_scheduled_events(self) -> List[str]:
        """检查预定的定时事件"""
        triggered = []
        current_time = self.world.time_min
        
        # 简化的定时事件示例
        scheduled_events = {
            600: "夜幕降临",  # 10小时后
            720: "午夜钟声",  # 12小时后
            1080: "黎明破晓"  # 18小时后
        }
        
        for event_time, event_name in scheduled_events.items():
            if current_time >= event_time and current_time < event_time + 10:
                if event_name not in triggered:  # 避免重复触发
                    triggered.append(event_name)
        
        return triggered
    
    def random_weather(self) -> str:
        """随机选择天气"""
        weathers = ["晴朗", "多云", "阴天", "小雨", "大雨", "雪"]
        return random.choice(weathers)
    
    def get_time_description(self) -> str:
        """获取时间描述"""
        time_min = self.world.time_min
        hours = time_min // 60
        minutes = time_min % 60
        
        if hours < 6:
            return "凌晨"
        elif hours < 12:
            return "上午"
        elif hours < 18:
            return "下午"
        else:
            return "晚上"

# 使用示例
time_manager = TimeManager(world_service)
time_manager.set_world(world)

# 推进时间
time_manager.advance_time(30)  # 推进30分钟
time_manager.advance_time(60)  # 推进1小时

# 获取时间描述
print(f"当前时间描述: {time_manager.get_time_description()}")</code></pre>
                        </div>
                        
                        <h2>关系管理</h2>
                        <div class="code-example">
                            <div class="code-title">角色关系网络</div>
                            <pre><code class="language-python">class RelationshipManager:
    def __init__(self, world_service: WorldService):
        self.world_service = world_service
        self.world = None
    
    def set_world(self, world: World):
        """设置当前世界"""
        self.world = world
    
    def set_relation(self, source: str, target: str, score: int, reason: str) -> bool:
        """设置角色关系"""
        if not self.world or not self.world.relationship_network:
            print("世界或关系网络未初始化")
            return False
        
        self.world_service.set_relation(
            world=self.world,
            source=source,
            target=target,
            score=score,
            reason=reason
        )
        
        print(f"关系设置: {source} -> {target} = {score} ({reason})")
        return True
    
    def get_relation(self, source: str, target: str) -> Optional[int]:
        """获取角色关系"""
        if not self.world or not self.world.relationship_network:
            return None
        
        relation = self.world.relationship_network.get_relation(source, target)
        return relation.strength if relation else None
    
    def get_relation_description(self, score: int) -> str:
        """获取关系描述"""
        if score >= 60:
            return "挚友"
        elif score >= 40:
            return "亲密同伴"
        elif score >= 10:
            return "盟友"
        elif score >= -10:
            return "中立"
        elif score >= -40:
            return "敌对"
        elif score >= -60:
            return "仇视"
        else:
            return "死敌"
    
    def list_all_relations(self) -> List[dict]:
        """列出所有关系"""
        if not self.world or not self.world.relationship_network:
            return []
        
        relations = []
        network = self.world.relationship_network
        
        for source in network.get_all_entities():
            for target in network.get_related_entities(source):
                relation = network.get_relation(source, target)
                if relation:
                    relations.append({
                        "source": source,
                        "target": target,
                        "score": relation.strength,
                        "description": self.get_relation_description(relation.strength),
                        "reason": relation.reason
                    })
        
        return relations
    
    def find_allies(self, character: str, threshold: int = 10) -> List[str]:
        """找到角色的盟友"""
        allies = []
        relations = self.list_all_relations()
        
        for relation in relations:
            if relation["source"] == character and relation["score"] >= threshold:
                allies.append(relation["target"])
            elif relation["target"] == character and relation["score"] >= threshold:
                allies.append(relation["source"])
        
        return allies
    
    def find_enemies(self, character: str, threshold: int = -10) -> List[str]:
        """找到角色的敌人"""
        enemies = []
        relations = self.list_all_relations()
        
        for relation in relations:
            if relation["source"] == character and relation["score"] <= threshold:
                enemies.append(relation["target"])
            elif relation["target"] == character and relation["score"] <= threshold:
                enemies.append(relation["source"])
        
        return enemies

# 使用示例
relationship_manager = RelationshipManager(world_service)
relationship_manager.set_world(world)

# 设置角色关系
relationship_manager.set_relation("Amiya", "Goblin", -50, "战斗冲突")
relationship_manager.set_relation("Amiya", "Doctor", 60, "医疗救助")
relationship_manager.set_relation("Goblin", "Chief", 40, "忠诚")

# 查询关系
amiya_goblin = relationship_manager.get_relation("Amiya", "Goblin")
print(f"Amiya对Goblin的关系: {amiya_goblin} ({relationship_manager.get_relation_description(amiya_goblin)})")

# 列出所有关系
all_relations = relationship_manager.list_all_relations()
print("\\n所有关系:")
for relation in all_relations:
    print(f"  {relation['source']} -> {relation['target']}: {relation['description']} ({relation['score']})")

# 查找盟友和敌人
amiya_allies = relationship_manager.find_allies("Amiya")
amiya_enemies = relationship_manager.find_enemies("Amiya")
print(f"\\nAmiya的盟友: {amiya_allies}")
print(f"Amiya的敌人: {amiya_enemies}")</code></pre>
                        </div>
                        
                        <h2>世界状态快照</h2>
                        <div class="code-example">
                            <div class="code-title">获取世界状态快照</div>
                            <pre><code class="language-python">def get_world_snapshot(world: World) -> dict:
    """获取世界状态快照"""
    snapshot = world.snapshot()
    
    return {
        "world_info": {
            "id": snapshot["id"],
            "name": snapshot["name"],
            "time_min": snapshot["time_min"],
            "weather": snapshot["weather"],
            "temperature": snapshot.get("temperature"),
            "visibility": snapshot.get("visibility")
        },
        "scene_info": {
            "name": snapshot.get("scene", {}).get("name"),
            "description": snapshot.get("scene", {}).get("description"),
            "objectives": snapshot.get("scene", {}).get("objectives", []),
            "details": snapshot.get("scene", {}).get("details", [])
        },
        "characters": {
            "count": len(snapshot["characters"]),
            "names": list(snapshot["characters"].keys()),
            "details": snapshot["characters"]
        },
        "positions": {
            "count": len(snapshot["positions"]),
            "details": snapshot["positions"]
        },
        "relations": {
            "network_exists": "relationship_network" in snapshot,
            "count": len(snapshot.get("relations", [])),
            "details": snapshot.get("relations", [])
        },
        "objectives": {
            "tracker_exists": "objective_tracker" in snapshot,
            "count": len(snapshot.get("objectives", [])),
            "completed_count": len([obj for obj in snapshot.get("objectives", []) 
                                 if obj.get("status") == "completed"]),
            "details": snapshot.get("objectives", [])
        },
        "inventory": {
            "items": snapshot.get("inventory", {}),
            "total_items": sum(snapshot.get("inventory", {}).values())
        }
    }

def format_world_snapshot(snapshot: dict) -> str:
    """格式化世界状态快照为可读字符串"""
    output = []
    
    # 世界信息
    world_info = snapshot["world_info"]
    output.append(f"=== {world_info['name']} ===")
    output.append(f"时间: {world_info['time_min']} 分钟")
    output.append(f"天气: {world_info['weather']}")
    if world_info.get("temperature"):
        output.append(f"温度: {world_info['temperature']}")
    
    # 场景信息
    scene_info = snapshot["scene_info"]
    if scene_info["name"]:
        output.append(f"\\n--- 场景: {scene_info['name']} ---")
        if scene_info["description"]:
            output.append(f"描述: {scene_info['description']}")
        
        if scene_info["objectives"]:
            output.append("目标:")
            for obj in scene_info["objectives"]:
                status = obj.get("status", "pending")
                output.append(f"  - {obj['name']} ({status})")
    
    # 角色信息
    characters = snapshot["characters"]
    output.append(f"\\n--- 角色信息 ({characters['count']}个) ---")
    for name, details in characters["details"].items():
        hp_percent = (details["hp"] / details["max_hp"]) * 100
        output.append(f"{name}: HP {details['hp']}/{details['max_hp']} ({hp_percent:.1f}%)")
        if details.get("position"):
            output.append(f"  位置: {details['position']}")
    
    # 关系信息
    relations = snapshot["relations"]
    if relations["count"] > 0:
        output.append(f"\\n--- 关系网络 ({relations['count']}个关系) ---")
        for relation in relations["details"]:
            score = relation["strength"]
            description = relationship_manager.get_relation_description(score)
            output.append(f"{relation['source']} -> {relation['target']}: {description} ({score})")
    
    # 目标状态
    objectives = snapshot["objectives"]
    if objectives["count"] > 0:
        output.append(f"\\n--- 目标状态 ({objectives['completed_count']}/{objectives['count']}完成) ---")
        for obj in objectives["details"]:
            status = obj.get("status", "pending")
            output.append(f"- {obj['name']}: {status}")
    
    return "\\n".join(output)

# 使用示例
snapshot = get_world_snapshot(world)
print(format_world_snapshot(snapshot))

# 保存快照到文件
def save_world_snapshot(world: World, filename: str):
    """保存世界状态快照到文件"""
    snapshot = get_world_snapshot(world)
    
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    print(f"世界快照已保存到: {filename}")

# 保存快照
save_world_snapshot(world, "world_snapshot.json")</code></pre>
                        </div>
                        
                        <h2>完整示例：游戏流程模拟</h2>
                        <div class="code-example">
                            <div class="code-title">完整的游戏流程模拟</div>
                            <pre><code class="language-python">class GameSimulator:
    def __init__(self):
        self.world = None
        self.characters = {}
        self.time_manager = None
        self.relationship_manager = None
        
    def setup_game(self, world_config: dict, character_configs: dict, story_config: dict):
        """设置游戏环境"""
        # 创建世界
        world_service = WorldService()
        self.world = world_service.create_world(world_config)
        
        # 设置场景
        world_service.set_scene(
            world=self.world,
            name=story_config.get("scene", {}).get("name"),
            objectives=story_config.get("scene", {}).get("objectives", []),
            details=story_config.get("scene", {}).get("details", []),
            time_min=story_config.get("scene", {}).get("time_min"),
            weather=story_config.get("scene", {}).get("weather")
        )
        
        # 创建角色
        character_service = CharacterService()
        for name, config in character_configs.items():
            if name not in ["relations", "objective_positions", "participants"]:
                character = character_service.create_character_from_dnd_config(name, config.get("dnd", {}))
                self.characters[name] = character
                self.world.add_character(character)
        
        # 设置初始位置
        positions = story_config.get("initial_positions", {})
        for name, pos in positions.items():
            if name in self.characters:
                self.characters[name].position = Position(pos[0], pos[1])
        
        # 设置关系
        relations_config = character_configs.get("relations", {})
        for source, targets in relations_config.items():
            if isinstance(targets, dict):
                for target, score in targets.items():
                    if source in self.characters and target in self.characters:
                        self.world.relationship_network.set_relation(source, target, score, "初始设定")
        
        # 初始化管理器
        self.time_manager = TimeManager(world_service)
        self.time_manager.set_world(self.world)
        self.relationship_manager = RelationshipManager(world_service)
        self.relationship_manager.set_world(self.world)
        
        print("游戏环境设置完成")
        print(f"世界: {self.world.name}")
        print(f"角色数量: {len(self.characters)}")
        print(f"初始时间: {self.world.time_min} 分钟")
    
    def simulate_time_passage(self, hours: int):
        """模拟时间流逝"""
        print(f"\\n=== 模拟 {hours} 小时时间流逝 ===")
        
        for hour in range(hours):
            # 每小时推进60分钟
            result = self.time_manager.advance_time(60)
            
            # 随机事件
            if random.random() < 0.2:  # 20%概率发生随机事件
                self.trigger_random_event()
            
            # 显示进度
            if (hour + 1) % 3 == 0:  # 每3小时显示一次
                print(f"  第 {hour + 1} 小时: {self.world.time_min} 分钟, {self.world.weather}")
    
    def trigger_random_event(self):
        """触发随机事件"""
        events = [
            {"name": "一阵风吹过", "effect": "天气略有变化"},
            {"name": "远处传来声音", "effect": "气氛变得紧张"},
            {"name": "阳光透过云层", "effect": "心情变得明朗"},
            {"name": "乌云聚集", "effect": "可能要下雨了"}
        ]
        
        event = random.choice(events)
        print(f"  随机事件: {event['name']} - {event['effect']}")
        
        # 可以在这里添加具体的事件处理逻辑
        if event["name"] == "乌云聚集":
            self.world.weather = "阴天"
            print(f"    天气变为: {self.world.weather}")
    
    def simulate_character_interaction(self, char1_name: str, char2_name: str):
        """模拟角色交互"""
        if char1_name not in self.characters or char2_name not in self.characters:
            print(f"角色 {char1_name} 或 {char2_name} 不存在")
            return
        
        char1 = self.characters[char1_name]
        char2 = self.characters[char2_name]
        
        # 计算关系变化
        current_relation = self.relationship_manager.get_relation(char1_name, char2_name) or 0
        
        # 简化的关系变化逻辑
        if random.random() < 0.7:  # 70%概率关系改善
            change = random.randint(1, 5)
        else:  # 30%概率关系恶化
            change = random.randint(-5, -1)
        
        new_relation = max(-100, min(100, current_relation + change))
        
        # 更新关系
        self.relationship_manager.set_relation(
            char1_name, char2_name, new_relation,
            f"交互变化 ({change:+d})"
        )
        
        old_desc = self.relationship_manager.get_relation_description(current_relation)
        new_desc = self.relationship_manager.get_relation_description(new_relation)
        
        print(f"\\n=== 角色交互: {char1_name} 与 {char2_name} ===")
        print(f"关系变化: {old_desc} -> {new_desc}")
        print(f"关系分数: {current_relation} -> {new_relation}")
    
    def get_game_summary(self) -> str:
        """获取游戏总结"""
        snapshot = get_world_snapshot(self.world)
        
        summary = []
        summary.append("=== 游戏总结 ===")
        summary.append(f"世界: {snapshot['world_info']['name']}")
        summary.append(f"总时间: {snapshot['world_info']['time_min']} 分钟")
        summary.append(f"当前天气: {snapshot['world_info']['weather']}")
        
        # 角色状态
        alive_chars = [name for name, details in snapshot["characters"]["details"].items() 
                       if details["hp"] > 0]
        dead_chars = [name for name, details in snapshot["characters"]["details"].items() 
                      if details["hp"] <= 0]
        
        summary.append(f"存活角色: {len(alive_chars)} ({', '.join(alive_chars) if alive_chars else '无'})")
        summary.append(f"死亡角色: {len(dead_chars)} ({', '.join(dead_chars) if dead_chars else '无'})")
        
        # 关系状态
        relations = snapshot["relations"]
        if relations["count"] > 0:
            positive_relations = [r for r in relations["details"] if r["strength"] > 0]
            negative_relations = [r for r in relations["details"] if r["strength"] < 0]
            
            summary.append(f"积极关系: {len(positive_relations)}")
            summary.append(f"消极关系: {len(negative_relations)}")
        
        # 目标状态
        objectives = snapshot["objectives"]
        if objectives["count"] > 0:
            summary.append(f"目标完成: {objectives['completed_count']}/{objectives['count']}")
        
        return "\n".join(summary)

# 使用示例
simulator = GameSimulator()

# 游戏配置
world_config = {
    "name": "旧城区",
    "time_min": 480,  # 下午8点
    "weather": "阴天"
}

character_configs = {
    "Amiya": {
        "persona": "一位年轻的医生，充满同情心和责任感",
        "dnd": {
            "level": 1,
            "hp": 10,
            "max_hp": 10,
            "abilities": {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 12, "CHA": 12},
            "armor_class": 12
        }
    },
    "Goblin": {
        "persona": "一个狡猾的哥布林，总是寻找机会",
        "dnd": {
            "level": 1,
            "hp": 7,
            "max_hp": 7,
            "abilities": {"STR": 12, "DEX": 14, "CON": 13, "INT": 8, "WIS": 10, "CHA": 8},
            "armor_class": 14
        }
    },
    "Doctor": {
        "persona": "一位经验丰富的医生，乐于助人",
        "dnd": {
            "level": 3,
            "hp": 15,
            "max_hp": 15,
            "abilities": {"STR": 10, "DEX": 12, "CON": 14, "INT": 14, "WIS": 16, "CHA": 13},
            "armor_class": 13
        }
    },
    "relations": {
        "Amiya": {"Goblin": -50, "Doctor": 60},
        "Goblin": {"Chief": 40},
        "Doctor": {"Amiya": 50}
    }
}

story_config = {
    "scene": {
        "name": "北侧仓棚",
        "description": "一个破旧的木质仓棚，堆放着各种杂物",
        "time_min": 480,
        "weather": "阴天",
        "objectives": [
            {
                "name": "调查仓棚",
                "description": "仔细搜索仓棚内可能的有用物品",
                "priority": "high"
            },
            {
                "name": "寻找线索",
                "description": "寻找关于失踪人员的线索",
                "priority": "medium"
            }
        ],
        "details": [
            "空气中弥漫着灰尘和木屑的味道",
            "角落里堆放着生锈的工具"
        ]
    },
    "initial_positions": {
        "Amiya": [0, 0],
        "Goblin": [5, 3],
        "Doctor": [2, 1]
    }
}

# 设置游戏
simulator.setup_game(world_config, character_configs, story_config)

# 模拟时间流逝
simulator.simulate_time_passage(2)  # 模拟2小时

# 模拟角色交互
simulator.simulate_character_interaction("Amiya", "Goblin")
simulator.simulate_character_interaction("Amiya", "Doctor")

# 获取游戏总结
print("\\n" + simulator.get_game_summary())</code></pre>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .example-overview {
                margin-bottom: 2rem;
            }
            
            .code-example {
                margin: 2rem 0;
            }
            
            .example-section {
                margin-bottom: 3rem;
                padding: 2rem;
                border: 1px solid var(--border-color);
                border-radius: var(--radius-lg);
                background-color: var(--bg-card);
            }
            
            .example-section h2 {
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 0.5rem;
                margin-bottom: 1rem;
            }
            </style>
        `;
    }
};