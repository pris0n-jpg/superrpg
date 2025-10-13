"""
测试数据生成器

负责生成各种测试数据，包括：
- 角色卡数据
- 传说书数据
- 提示模板数据
- 世界数据
"""

import json
import random
import string
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.domain.models.characters import CharacterCard
from src.domain.models.lorebook import LoreBook, LoreBookEntry
from src.domain.models.prompt import PromptTemplate, PromptSection
from src.domain.models.world import World


class TestDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化测试数据生成器
        
        Args:
            output_dir: 输出目录，默认为当前目录下的generated_data
        """
        self.output_dir = output_dir or Path("generated_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # 预定义的名字池
        self.first_names = [
            "艾莉娅", "索林", "凯尔", "莉娜", "马库斯", "伊莎贝拉", 
            "格雷戈尔", "塞拉菲娜", "罗兰", "伊芙琳", "邓肯", "艾米莉亚"
        ]
        
        self.last_names = [
            "星辰使者", "铁须", "暗影", "晨光", "风暴", "银叶",
            "石心", "月影", "烈焰", "冰霜", "雷鸣", "风语"
        ]
        
        self.races = ["人类", "精灵", "矮人", "半身人", "兽人", "龙裔", "提夫林"]
        self.classes = ["战士", "法师", "游侠", "盗贼", "牧师", "德鲁伊", "武僧", "野蛮人"]
        self.backgrounds = ["士兵", "学者", "商人", "艺术家", "农夫", "贵族", "流浪者", "工匠"]
        
        self.locations = [
            "艾尔德利亚", "铁炉堡", "银月城", "奥格瑞玛", "暴风城", 
            "达纳苏斯", "幽暗城", "雷霆崖", "摩戈尔", "诺森德"
        ]
        
        self.factions = [
            "联盟", "部落", "中立", "守护者", "天灾军团", "燃烧军团",
            "银色黎明", "血色十字军", "暗影议会", "肯瑞托"
        ]

    def generate_character_card(self, 
                               name: Optional[str] = None,
                               race: Optional[str] = None,
                               char_class: Optional[str] = None,
                               background: Optional[str] = None) -> Dict[str, Any]:
        """
        生成角色卡数据
        
        Args:
            name: 角色名称，如果为None则随机生成
            race: 种族，如果为None则随机选择
            char_class: 职业，如果为None则随机选择
            background: 背景，如果为None则随机选择
            
        Returns:
            角色卡数据字典
        """
        # 生成基本信息
        if not name:
            name = f"{random.choice(self.first_names)}·{random.choice(self.last_names)}"
        
        race = race or random.choice(self.races)
        char_class = char_class or random.choice(self.classes)
        background = background or random.choice(self.backgrounds)
        
        # 生成属性值 (3-18)
        attributes = {
            "力量": random.randint(8, 18),
            "敏捷": random.randint(8, 18),
            "体质": random.randint(8, 18),
            "智力": random.randint(8, 18),
            "感知": random.randint(8, 18),
            "魅力": random.randint(8, 18)
        }
        
        # 根据职业调整属性
        if char_class == "战士":
            attributes["力量"] = min(18, attributes["力量"] + 2)
            attributes["体质"] = min(18, attributes["体质"] + 1)
        elif char_class == "法师":
            attributes["智力"] = min(18, attributes["智力"] + 2)
            attributes["感知"] = min(18, attributes["感知"] + 1)
        elif char_class == "游侠":
            attributes["敏捷"] = min(18, attributes["敏捷"] + 2)
            attributes["感知"] = min(18, attributes["感知"] + 1)
        elif char_class == "盗贼":
            attributes["敏捷"] = min(18, attributes["敏捷"] + 2)
            attributes["魅力"] = min(18, attributes["魅力"] + 1)
        elif char_class == "牧师":
            attributes["感知"] = min(18, attributes["感知"] + 2)
            attributes["魅力"] = min(18, attributes["魅力"] + 1)
        
        # 生成技能
        skills = self._generate_skills(char_class)
        
        # 生成物品
        items = self._generate_items(char_class, race)
        
        # 生成外观描述
        appearance = self._generate_appearance(race, char_class)
        
        # 生成背景故事
        backstory = self._generate_backstory(name, race, char_class, background)
        
        # 生成性格特质
        personality = self._generate_personality()
        
        # 生成目标
        objectives = self._generate_objectives(background)
        
        # 生成关系
        relationships = self._generate_relationships()
        
        # 生成特殊能力
        abilities = self._generate_abilities(race, char_class)
        
        return {
            "name": name,
            "race": race,
            "class": char_class,
            "background": background,
            "level": random.randint(1, 10),
            "experience": random.randint(0, 50000),
            "attributes": attributes,
            "skills": skills,
            "items": items,
            "appearance": appearance,
            "backstory": backstory,
            "personality": personality,
            "objectives": objectives,
            "relationships": relationships,
            "abilities": abilities,
            "health": {
                "current": random.randint(20, 100),
                "max": random.randint(50, 150)
            },
            "mana": {
                "current": random.randint(10, 50),
                "max": random.randint(20, 100)
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def generate_lorebook_entry(self, 
                              title: Optional[str] = None,
                              category: Optional[str] = None) -> Dict[str, Any]:
        """
        生成传说书条目
        
        Args:
            title: 条目标题，如果为None则随机生成
            category: 条目类别，如果为None则随机选择
            
        Returns:
            传说书条目数据字典
        """
        categories = ["人物", "地点", "组织", "事件", "物品", "历史", "传说", "魔法"]
        category = category or random.choice(categories)
        
        if not title:
            if category == "人物":
                title = f"{random.choice(self.first_names)}·{random.choice(self.last_names)}"
            elif category == "地点":
                title = random.choice(self.locations)
            else:
                title = f"神秘的{category}"
        
        # 生成关键词
        keywords = self._generate_keywords(title, category)
        
        # 生成内容
        content = self._generate_lorebook_content(title, category)
        
        # 生成相关条目
        related_entries = []
        for _ in range(random.randint(0, 3)):
            related_title = f"相关{random.choice(categories)}"
            related_entries.append({
                "title": related_title,
                "relation": random.choice("引用提及相关关联冲突".split(" "))
            })
        
        return {
            "id": self._generate_id(),
            "title": title,
            "category": category,
            "keywords": keywords,
            "content": content,
            "related_entries": related_entries,
            "importance": random.randint(1, 5),
            "verified": random.choice([True, False]),
            "source": f"{random.choice(['古代文献', '口述历史', '官方记录', '私人日记'])}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def generate_prompt_template(self, 
                               name: Optional[str] = None,
                               category: Optional[str] = None) -> Dict[str, Any]:
        """
        生成提示模板
        
        Args:
            name: 模板名称，如果为None则随机生成
            category: 模板类别，如果为None则随机选择
            
        Returns:
            提示模板数据字典
        """
        categories = ["对话", "描述", "战斗", "探索", "社交", "创作"]
        category = category or random.choice(categories)
        
        if not name:
            name = f"{category}模板_{random.randint(1, 100)}"
        
        # 生成部分
        sections = self._generate_prompt_sections(category)
        
        # 生成变量
        variables = self._generate_prompt_variables(sections)
        
        return {
            "id": self._generate_id(),
            "name": name,
            "category": category,
            "description": f"用于{category}场景的提示模板",
            "sections": sections,
            "variables": variables,
            "tags": [category, "模板", "系统生成"],
            "version": f"1.{random.randint(0, 9)}",
            "author": "系统生成器",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def generate_world_data(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        生成世界数据
        
        Args:
            name: 世界名称，如果为None则随机生成
            
        Returns:
            世界数据字典
        """
        if not name:
            name = f"世界_{random.choice(self.locations)}_{random.randint(1, 100)}"
        
        # 生成地区
        regions = []
        for i in range(random.randint(3, 8)):
            region_name = f"{random.choice(['北', '南', '东', '西', '中'])}{random.choice(['森林', '山脉', '平原', '沙漠', '沼泽', '冰原'])}"
            regions.append({
                "id": self._generate_id(),
                "name": region_name,
                "description": f"位于{name}的{region_name}地区",
                "climate": random.choice(['温带', '热带', '寒带', '干旱', '湿润']),
                "population": random.randint(1000, 1000000),
                "capital": f"{region_name}城",
                "resources": random.sample(['木材', '矿石', '粮食', '魔法水晶', '稀有金属'], random.randint(2, 4))
            })
        
        # 生成势力
        factions = []
        for i in range(random.randint(2, 5)):
            faction_name = random.choice(self.factions)
            factions.append({
                "id": self._generate_id(),
                "name": faction_name,
                "description": f"{name}中的{faction_name}势力",
                "type": random.choice(['军事', '政治', '宗教', '商业', '秘密']),
                "influence": random.randint(1, 10),
                "leader": f"{random.choice(self.first_names)}·{random.choice(self.last_names)}",
                "headquarters": random.choice([region["name"] for region in regions])
            })
        
        # 生成历史事件
        events = []
        for i in range(random.randint(5, 15)):
            year = random.randint(-5000, 1000)
            events.append({
                "id": self._generate_id(),
                "year": year,
                "name": f"事件_{year}_{random.randint(1, 100)}",
                "description": f"发生在{year}年的重要事件",
                "type": random.choice(['战争', '和平', '发现', '灾难', '庆典', '变革']),
                "participants": random.sample([faction["name"] for faction in factions], random.randint(1, 3))
            })
        
        return {
            "id": self._generate_id(),
            "name": name,
            "description": f"一个充满冒险和魔法的世界：{name}",
            "type": random.choice(['奇幻', '科幻', '现实', '混合']),
            "regions": regions,
            "factions": factions,
            "events": sorted(events, key=lambda x: x["year"]),
            "timeline": {
                "creation_year": -10000,
                "current_year": random.randint(1000, 2000),
                "era": f"第{random.randint(1, 10)}纪元"
            },
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }

    def generate_test_dataset(self, 
                             num_characters: int = 10,
                             num_lorebook_entries: int = 20,
                             num_prompt_templates: int = 15,
                             num_worlds: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成完整的测试数据集
        
        Args:
            num_characters: 角色卡数量
            num_lorebook_entries: 传说书条目数量
            num_prompt_templates: 提示模板数量
            num_worlds: 世界数据数量
            
        Returns:
            包含所有测试数据的字典
        """
        dataset = {
            "characters": [],
            "lorebook_entries": [],
            "prompt_templates": [],
            "worlds": []
        }
        
        # 生成角色卡
        print(f"生成 {num_characters} 个角色卡...")
        for _ in range(num_characters):
            character = self.generate_character_card()
            dataset["characters"].append(character)
        
        # 生成传说书条目
        print(f"生成 {num_lorebook_entries} 个传说书条目...")
        for _ in range(num_lorebook_entries):
            entry = self.generate_lorebook_entry()
            dataset["lorebook_entries"].append(entry)
        
        # 生成提示模板
        print(f"生成 {num_prompt_templates} 个提示模板...")
        for _ in range(num_prompt_templates):
            template = self.generate_prompt_template()
            dataset["prompt_templates"].append(template)
        
        # 生成世界数据
        print(f"生成 {num_worlds} 个世界数据...")
        for _ in range(num_worlds):
            world = self.generate_world_data()
            dataset["worlds"].append(world)
        
        return dataset

    def save_dataset(self, dataset: Dict[str, List[Dict[str, Any]]], filename: str = "test_dataset.json") -> Path:
        """
        保存数据集到文件
        
        Args:
            dataset: 数据集
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        print(f"测试数据集已保存到: {filepath}")
        return filepath

    def save_individual_files(self, dataset: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Path]]:
        """
        将数据集保存为单独的文件
        
        Args:
            dataset: 数据集
            
        Returns:
            各类型文件的路径字典
        """
        saved_files = {
            "characters": [],
            "lorebook_entries": [],
            "prompt_templates": [],
            "worlds": []
        }
        
        # 创建子目录
        for category in saved_files.keys():
            (self.output_dir / category).mkdir(exist_ok=True)
        
        # 保存角色卡
        for i, character in enumerate(dataset["characters"]):
            filename = f"character_{i+1:03d}_{character['name'].replace('·', '_')}.json"
            filepath = self.output_dir / "characters" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(character, f, ensure_ascii=False, indent=2)
            
            saved_files["characters"].append(filepath)
        
        # 保存传说书条目
        for i, entry in enumerate(dataset["lorebook_entries"]):
            filename = f"lorebook_{i+1:03d}_{entry['title'].replace(' ', '_')}.json"
            filepath = self.output_dir / "lorebook_entries" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
            
            saved_files["lorebook_entries"].append(filepath)
        
        # 保存提示模板
        for i, template in enumerate(dataset["prompt_templates"]):
            filename = f"template_{i+1:03d}_{template['name']}.json"
            filepath = self.output_dir / "prompt_templates" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            saved_files["prompt_templates"].append(filepath)
        
        # 保存世界数据
        for i, world in enumerate(dataset["worlds"]):
            filename = f"world_{i+1:03d}_{world['name']}.json"
            filepath = self.output_dir / "worlds" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(world, f, ensure_ascii=False, indent=2)
            
            saved_files["worlds"].append(filepath)
        
        print(f"单独文件已保存到: {self.output_dir}")
        return saved_files

    # 私有辅助方法
    
    def _generate_id(self) -> str:
        """生成随机ID"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def _generate_skills(self, char_class: str) -> Dict[str, int]:
        """根据职业生成技能"""
        all_skills = {
            "战士": ["武器熟练", "重甲熟练", "盾牌熟练", "威吓", "运动"],
            "法师": ["奥术", "法术辨识", "专注", "历史", "调查"],
            "游侠": ["潜行", "生存", "自然", "感知", "箭术"],
            "盗贼": ["潜行", "巧手", "欺骗", "杂技", "洞察"],
            "牧师": ["宗教", "医疗", "洞察", "说服", "安抚"],
            "德鲁伊": ["自然", "生存", "变形", "动物伙伴", "草药学"],
            "武僧": ["运动", "杂技", "洞察", "宗教", "专注"],
            "野蛮人": ["运动", "威吓", "生存", "本能", "狂暴"]
        }
        
        skills = {}
        class_skills = all_skills.get(char_class, all_skills["战士"])
        
        for skill in class_skills:
            skills[skill] = random.randint(1, 5)
        
        # 添加一些通用技能
        common_skills = ["洞察", "感知", "运动", "威吓", "说服"]
        for skill in random.sample(common_skills, random.randint(2, 3)):
            if skill not in skills:
                skills[skill] = random.randint(1, 3)
        
        return skills
    
    def _generate_items(self, char_class: str, race: str) -> List[Dict[str, Any]]:
        """根据职业和种族生成物品"""
        items = [
            {
                "id": self._generate_id(),
                "name": "便服",
                "type": "装备",
                "slot": "身体",
                "description": "普通的便服",
                "quantity": 1,
                "value": 5,
                "rarity": "普通"
            },
            {
                "id": self._generate_id(),
                "name": "钱袋",
                "type": "容器",
                "slot": "背包",
                "description": "装有金币的钱袋",
                "quantity": 1,
                "value": 100,
                "rarity": "普通"
            }
        ]
        
        # 根据职业添加特殊物品
        if char_class == "战士":
            items.append({
                "id": self._generate_id(),
                "name": "长剑",
                "type": "武器",
                "slot": "主手",
                "description": "标准的制式长剑",
                "quantity": 1,
                "value": 50,
                "rarity": "普通",
                "damage": "1d8",
                "properties": ["多功能"]
            })
        elif char_class == "法师":
            items.append({
                "id": self._generate_id(),
                "name": "法杖",
                "type": "武器",
                "slot": "主手",
                "description": "简单的魔法法杖",
                "quantity": 1,
                "value": 40,
                "rarity": "普通",
                "damage": "1d6",
                "properties": ["施法焦点"]
            })
        elif char_class == "游侠":
            items.append({
                "id": self._generate_id(),
                "name": "短弓",
                "type": "武器",
                "slot": "远程",
                "description": "轻便的短弓",
                "quantity": 1,
                "value": 45,
                "rarity": "普通",
                "damage": "1d6",
                "properties": ["远程", "双持"]
            })
        
        # 添加一些随机物品
        random_items = [
            {"name": "治疗药水", "type": "消耗品", "value": 25},
            {"name": "绳索", "type": "工具", "value": 10},
            {"name": "火把", "type": "工具", "value": 1},
            {"name": "口粮", "type": "消耗品", "value": 5},
            {"name": "水袋", "type": "容器", "value": 2}
        ]
        
        for item in random.sample(random_items, random.randint(2, 4)):
            items.append({
                "id": self._generate_id(),
                "name": item["name"],
                "type": item["type"],
                "slot": "背包",
                "description": f"普通的{item['name']}",
                "quantity": random.randint(1, 5),
                "value": item["value"],
                "rarity": "普通"
            })
        
        return items
    
    def _generate_appearance(self, race: str, char_class: str) -> str:
        """生成外观描述"""
        height_descriptions = {
            "矮人": "中等偏矮",
            "精灵": "高挑",
            "半身人": "矮小",
            "兽人": "高大威猛",
            "龙裔": "高大",
            "提夫林": "中等",
            "人类": "中等"
        }
        
        hair_colors = ["黑色", "棕色", "金色", "红色", "银色", "白色"]
        eye_colors = ["棕色", "蓝色", "绿色", "灰色", "琥珀色", "紫色"]
        
        build_descriptions = {
            "战士": "健壮",
            "法师": "纤细",
            "游侠": "矫健",
            "盗贼": "灵活",
            "牧师": "温和",
            "德鲁伊": "自然",
            "武僧": "匀称",
            "野蛮人": "魁梧"
        }
        
        height = height_descriptions.get(race, "中等")
        hair_color = random.choice(hair_colors)
        eye_color = random.choice(eye_colors)
        build = build_descriptions.get(char_class, "普通")
        
        return f"{height}的身材，{build}的体格，{hair_color}的头发，{eye_color}的眼睛。"
    
    def _generate_backstory(self, name: str, race: str, char_class: str, background: str) -> str:
        """生成背景故事"""
        events = [
            f"{name}出生在一个普通的{background}家庭。",
            f"在年轻的时候，{name}发现自己对{char_class}之道有着天赋。",
            f"一次偶然的机会，{name}遇到了一位神秘的{char_class}导师。",
            f"经过刻苦的训练，{name}掌握了{char_class}的核心技能。",
            f"现在，{name}踏上了冒险之旅，寻找自己的命运。"
        ]
        
        return " ".join(random.sample(events, random.randint(3, 5)))
    
    def _generate_personality(self) -> List[str]:
        """生成性格特质"""
        all_traits = [
            "勇敢", "谨慎", "好奇", "忠诚", "机智", "诚实", "慷慨", 
            "耐心", "果断", "幽默", "严肃", "乐观", "现实", "理想主义"
        ]
        
        return random.sample(all_traits, random.randint(3, 6))
    
    def _generate_objectives(self, background: str) -> List[str]:
        """生成目标"""
        objectives = []
        
        # 基于背景的主要目标
        background_objectives = {
            "士兵": ["寻找战争的意义", "保护无辜的人", "建立自己的军队"],
            "学者": ["寻求禁断的知识", "写下传世之作", "解开古老的谜题"],
            "商人": ["积累巨额财富", "建立商业帝国", "找到稀有的贸易路线"],
            "艺术家": ["创作完美的作品", "获得名声和认可", "找到灵感源泉"],
            "农夫": ["保护自己的土地", "改善村民的生活", "找到更好的耕作方法"],
            "贵族": ["维护家族荣誉", "扩大领地", "赢得政治权力"],
            "流浪者": ["寻找归属之地", "探索未知世界", "帮助遇到的每个人"],
            "工匠": ["制作传世杰作", "创新工艺技术", "找到稀有材料"]
        }
        
        main_objective = random.choice(background_objectives.get(background, ["找到自己的使命"]))
        objectives.append(main_objective)
        
        # 添加一些次要目标
        secondary_objectives = [
            "学习新的技能",
            "结交可靠的朋友",
            "寻找失散的家人",
            "揭露一个阴谋",
            "保护重要的人",
            "完成一个承诺"
        ]
        
        objectives.extend(random.sample(secondary_objectives, random.randint(1, 2)))
        
        return objectives
    
    def _generate_relationships(self) -> List[Dict[str, Any]]:
        """生成关系"""
        relationships = []
        
        for _ in range(random.randint(1, 4)):
            relationship = {
                "name": f"{random.choice(self.first_names)}·{random.choice(self.last_names)}",
                "type": random.choice(["家人", "朋友", "导师", "对手", "恋人", "盟友"]),
                "description": f"与{random.choice(self.first_names)}的关系错综复杂",
                "status": random.choice(["良好", "紧张", "未知", "已故", "失踪"])
            }
            relationships.append(relationship)
        
        return relationships
    
    def _generate_abilities(self, race: str, char_class: str) -> List[Dict[str, Any]]:
        """生成特殊能力"""
        abilities = []
        
        # 种族能力
        racial_abilities = {
            "精灵": ["黑暗视觉", "敏锐感知", "魔法抗性"],
            "矮人": ["黑暗视觉", "石头直觉", "毒素抗性"],
            "半身人": ["勇敢", "灵活", "幸运"],
            "兽人": ["狂暴", "强悍", "生存本能"],
            "龙裔": ["龙息", "龙鳞", "飞龙形态"],
            "提夫林": ["黑暗视觉", "地狱抗性", "魔法天赋"],
            "人类": ["多样性", "适应性", "领导力"]
        }
        
        # 职业能力
        class_abilities = {
            "战士": ["战斗风格", "复苏之风", "动作如潮"],
            "法师": ["奥术恢复", "法术秘籍", "魔法天赋"],
            "游侠": ["自然探索者", "宿敌", "偏好地形"],
            "盗贼": ["偷袭", "贼胆", "灵活思维"],
            "牧师": ["神启", "神佑", "圣殿"],
            "德鲁伊": ["德鲁伊语", "野性变身", "野性伙伴"],
            "武僧": ["气功", "不动如山", "疾风步"],
            "野蛮人": ["狂暴", "危险感知", "顽强生存"]
        }
        
        # 添加种族能力
        for ability in random.sample(racial_abilities.get(race, []), random.randint(1, 2)):
            abilities.append({
                "name": ability,
                "description": f"作为{race}天生拥有的能力",
                "type": "种族",
                "source": race,
                "level": 1
            })
        
        # 添加职业能力
        for ability in random.sample(class_abilities.get(char_class, []), random.randint(1, 2)):
            abilities.append({
                "name": ability,
                "description": f"作为{char_class}掌握的能力",
                "type": "职业",
                "source": char_class,
                "level": random.randint(1, 5)
            })
        
        return abilities
    
    def _generate_keywords(self, title: str, category: str) -> List[str]:
        """生成关键词"""
        keywords = [title, category]
        
        # 添加一些相关关键词
        related_words = {
            "人物": ["角色", "传记", "历史", "身份", "关系"],
            "地点": ["地区", "地理", "位置", "环境", "坐标"],
            "组织": ["团体", "势力", "联盟", "公会", "机构"],
            "事件": ["历史", "时间", "发生", "影响", "后果"],
            "物品": ["装备", "道具", "材料", "神器", "宝物"],
            "历史": ["时间", "年代", "记录", "文献", "考古"],
            "传说": ["故事", "神话", "传说", "预言", "秘密"],
            "魔法": ["咒语", "法术", "能量", "元素", "神秘"]
        }
        
        category_words = related_words.get(category, [])
        keywords.extend(random.sample(category_words, random.randint(1, 3)))
        
        return keywords
    
    def _generate_lorebook_content(self, title: str, category: str) -> str:
        """生成传说书内容"""
        contents = {
            "人物": f"{title}是一位传奇人物，在这个世界中有着重要的影响。他们的故事被广泛流传，成为了许多传说和故事的主角。",
            "地点": f"{title}是一个神秘的地方，充满了未知和冒险。许多勇敢的冒险者都曾前往探索，但只有少数人能够平安归来。",
            "组织": f"{title}是一个强大的组织，在这个世界中有着重要的影响力。他们的目标和动机一直是个谜，吸引了无数人的关注。",
            "事件": f"{title}是一个重要的历史事件，对这个世界产生了深远的影响。这个事件改变了许多人和事物的命运。",
            "物品": f"{title}是一件传说中的物品，据说拥有神奇的力量。无数人想要得到它，但只有真正有资格的人才能拥有。",
            "历史": f"{title}记录了这个世界的重要历史。通过了解这些历史，我们可以更好地理解现在和预测未来。",
            "传说": f"{title}是一个古老的传说，代代相传。这个传说中蕴含着深刻的智慧和预言。",
            "魔法": f"{title}是一种神秘的魔法，只有少数人能够掌握。它的力量强大而危险，需要谨慎使用。"
        }
        
        base_content = contents.get(category, f"{title}是一个重要的条目，包含了许多有价值的信息。")
        
        # 添加一些详细信息
        details = [
            f"根据记录，{title}最早出现在{random.randint(100, 1000)}年前。",
            f"有证据表明，{title}与{random.choice(self.locations)}有着密切的联系。",
            f"专家们认为，{title}的重要性主要体现在{random.choice(['政治', '军事', '文化', '经济'])}方面。",
            f"关于{title}的研究仍在进行中，每年都有新的发现。"
        ]
        
        full_content = base_content + " " + " ".join(random.sample(details, random.randint(2, 3)))
        
        return full_content
    
    def _generate_prompt_sections(self, category: str) -> List[Dict[str, Any]]:
        """生成提示模板部分"""
        section_templates = {
            "对话": [
                {
                    "name": "角色设定",
                    "content": "你是{character_name}，一个{race}{class}。{personality}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "对话场景",
                    "content": "你在{location}与{partner}进行对话。{context}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "对话指导",
                    "content": "请以{character_name}的身份回应，保持角色的性格特点。{style_guide}",
                    "order": 3,
                    "required": False
                }
            ],
            "描述": [
                {
                    "name": "描述对象",
                    "content": "请详细描述{object}。{focus_points}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "描述角度",
                    "content": "从{perspective}的角度进行描述。{tone}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "细节要求",
                    "content": "重点关注{details}。{constraints}",
                    "order": 3,
                    "required": False
                }
            ],
            "战斗": [
                {
                    "name": "战斗场景",
                    "content": "{character}在{location}面临{enemy}的挑战。{situation}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "战斗策略",
                    "content": "基于{character}的{abilities}，制定战斗策略。{objectives}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "战斗规则",
                    "content": "战斗遵循{rules}。{limitations}",
                    "order": 3,
                    "required": False
                }
            ],
            "探索": [
                {
                    "name": "探索地点",
                    "content": "你正在探索{location}。{environment}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "探索目标",
                    "content": "你的目标是{objective}。{clues}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "探索方法",
                    "content": "使用{methods}进行探索。{equipment}",
                    "order": 3,
                    "required": False
                }
            ],
            "社交": [
                {
                    "name": "社交场景",
                    "content": "你在{event}活动中与{npc}互动。{social_context}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "社交目标",
                    "content": "你的目标是{goal}。{relationship}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "社交技巧",
                    "content": "运用{skills}来达成目标。{approaches}",
                    "order": 3,
                    "required": False
                }
            ],
            "创作": [
                {
                    "name": "创作主题",
                    "content": "创作关于{theme}的作品。{inspiration}",
                    "order": 1,
                    "required": True
                },
                {
                    "name": "创作要求",
                    "content": "作品需要满足{requirements}。{constraints}",
                    "order": 2,
                    "required": True
                },
                {
                    "name": "创作指导",
                    "content": "参考{references}，保持{style}风格。{feedback}",
                    "order": 3,
                    "required": False
                }
            ]
        }
        
        return section_templates.get(category, [
            {
                "name": "基本内容",
                "content": "{content}",
                "order": 1,
                "required": True
            }
        ])
    
    def _generate_prompt_variables(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成提示变量"""
        # 从部分内容中提取变量
        all_variables = set()
        for section in sections:
            content = section.get("content", "")
            # 简单的变量提取：{variable_name}
            import re
            variables = re.findall(r'\{([^}]+)\}', content)
            all_variables.update(variables)
        
        # 为每个变量生成默认值
        variable_definitions = {}
        for var in all_variables:
            if "character" in var.lower():
                variable_definitions[var] = {
                    "type": "string",
                    "description": "角色相关变量",
                    "default": "默认角色",
                    "required": True
                }
            elif "location" in var.lower():
                variable_definitions[var] = {
                    "type": "string",
                    "description": "地点相关变量",
                    "default": "默认地点",
                    "required": True
                }
            elif "object" in var.lower():
                variable_definitions[var] = {
                    "type": "string",
                    "description": "物体相关变量",
                    "default": "默认物体",
                    "required": True
                }
            else:
                variable_definitions[var] = {
                    "type": "string",
                    "description": f"{var}变量",
                    "default": f"默认{var}",
                    "required": False
                }
        
        return variable_definitions


# 便捷函数
def generate_test_data(output_dir: str = "generated_data") -> Dict[str, Any]:
    """
    生成测试数据的便捷函数
    
    Args:
        output_dir: 输出目录
        
    Returns:
        生成的数据集
    """
    generator = TestDataGenerator(Path(output_dir))
    dataset = generator.generate_test_dataset()
    generator.save_dataset(dataset)
    generator.save_individual_files(dataset)
    return dataset


if __name__ == "__main__":
    # 生成测试数据
    dataset = generate_test_data()
    
    print(f"\n测试数据生成完成!")
    print(f"- 角色卡: {len(dataset['characters'])} 个")
    print(f"- 传说书条目: {len(dataset['lorebook_entries'])} 个")
    print(f"- 提示模板: {len(dataset['prompt_templates'])} 个")
    print(f"- 世界数据: {len(dataset['worlds'])} 个")