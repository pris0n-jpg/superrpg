"""
角色卡数据传输对象

该模块定义了角色卡相关的数据传输对象，遵循SOLID原则，
特别是单一职责原则(SRP)，每个DTO都有明确的职责。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class CharacterCardDto:
    """角色卡数据传输对象
    
    用于传输角色卡的基本信息，遵循单一职责原则，
    专门负责角色卡数据的传输。
    """
    id: str
    name: str
    description: str
    first_message: str
    example_messages: List[str] = field(default_factory=list)
    scenario: str = ""
    personality_summary: str = ""
    creator_notes: str = ""
    tags: List[str] = field(default_factory=list)
    abilities: Dict[str, int] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=dict)
    hp: int = 100
    max_hp: int = 100
    position: Optional[Dict[str, int]] = None
    proficient_skills: List[str] = field(default_factory=list)
    proficient_saves: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    inventory: Dict[str, int] = field(default_factory=dict)
    png_metadata: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_domain(cls, character_card) -> 'CharacterCardDto':
        """从领域对象创建DTO
        
        Args:
            character_card: 角色卡领域对象
            
        Returns:
            CharacterCardDto: 角色卡DTO实例
        """
        return cls(
            id=str(character_card.id),
            name=character_card.name,
            description=character_card.card_info.description,
            first_message=character_card.card_info.first_message,
            example_messages=character_card.card_info.example_messages,
            scenario=character_card.card_info.scenario,
            personality_summary=character_card.card_info.personality_summary,
            creator_notes=character_card.card_info.creator_notes,
            tags=character_card.card_info.tags,
            abilities={
                'strength': character_card.abilities.strength,
                'dexterity': character_card.abilities.dexterity,
                'constitution': character_card.abilities.constitution,
                'intelligence': character_card.abilities.intelligence,
                'wisdom': character_card.abilities.wisdom,
                'charisma': character_card.abilities.charisma,
            },
            stats={
                'level': character_card.stats.level,
                'armor_class': character_card.stats.armor_class,
                'proficiency_bonus': character_card.stats.proficiency_bonus,
                'speed_steps': character_card.stats.speed_steps,
                'reach_steps': character_card.stats.reach_steps,
            },
            hp=character_card.hp,
            max_hp=character_card.max_hp,
            position={
                'x': character_card.position.x,
                'y': character_card.position.y,
            } if character_card.position else None,
            proficient_skills=character_card.proficient_skills,
            proficient_saves=character_card.proficient_saves,
            conditions=[c.value for c in character_card.conditions],
            inventory=character_card.inventory,
            png_metadata={
                'name': character_card.png_metadata.name,
                'description': character_card.png_metadata.description,
                'personality': character_card.png_metadata.personality,
                'scenario': character_card.png_metadata.scenario,
                'first_mes': character_card.png_metadata.first_mes,
                'example_dialogue': character_card.png_metadata.example_dialogue,
                'mes_example': character_card.png_metadata.mes_example,
                'background': character_card.png_metadata.background,
            } if character_card.png_metadata else None,
            created_at=character_card.created_at,
            updated_at=character_card.updated_at,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'first_message': self.first_message,
            'example_messages': self.example_messages,
            'scenario': self.scenario,
            'personality_summary': self.personality_summary,
            'creator_notes': self.creator_notes,
            'tags': self.tags,
            'abilities': self.abilities,
            'stats': self.stats,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'position': self.position,
            'proficient_skills': self.proficient_skills,
            'proficient_saves': self.proficient_saves,
            'conditions': self.conditions,
            'inventory': self.inventory,
            'png_metadata': self.png_metadata,
        }
        
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            result['updated_at'] = self.updated_at.isoformat()
        
        return result


@dataclass
class CharacterCardListDto:
    """角色卡列表响应对象
    
    用于传输角色卡列表信息，遵循单一职责原则，
    专门负责角色卡列表数据的传输。
    """
    characters: List[CharacterCardDto]
    total_count: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'characters': [char.to_dict() for char in self.characters],
            'total_count': self.total_count,
            'page': self.page,
            'page_size': self.page_size,
            'total_pages': self.total_pages,
        }


@dataclass
class CharacterCardCreateDto:
    """创建角色卡请求对象
    
    用于传输创建角色卡的请求数据，遵循单一职责原则，
    专门负责创建请求数据的传输。
    """
    name: str
    description: str = ""
    first_message: str = ""
    example_messages: List[str] = field(default_factory=list)
    scenario: str = ""
    personality_summary: str = ""
    creator_notes: str = ""
    tags: List[str] = field(default_factory=list)
    abilities: Dict[str, int] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=dict)
    hp: int = 100
    max_hp: int = 100
    position: Optional[Dict[str, int]] = None
    proficient_skills: List[str] = field(default_factory=list)
    proficient_saves: List[str] = field(default_factory=list)
    inventory: Dict[str, int] = field(default_factory=dict)
    png_metadata: Optional[Dict[str, str]] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("角色名称不能为空")
        
        if self.hp < 0:
            errors.append("当前生命值不能小于0")
        
        if self.max_hp <= 0:
            errors.append("最大生命值必须大于0")
        
        if self.hp > self.max_hp:
            errors.append("当前生命值不能大于最大生命值")
        
        # 验证能力值
        ability_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for ability in ability_names:
            value = self.abilities.get(ability, 10)
            if value < 1 or value > 30:
                errors.append(f"能力值 {ability} 必须在1-30之间")
        
        # 验证统计数据
        if self.stats.get('level', 1) < 1:
            errors.append("角色等级必须大于0")
        
        if self.stats.get('armor_class', 10) < 1:
            errors.append("护甲等级必须大于0")
        
        return errors


@dataclass
class CharacterCardUpdateDto:
    """更新角色卡请求对象
    
    用于传输更新角色卡的请求数据，遵循单一职责原则，
    专门负责更新请求数据的传输。
    """
    description: Optional[str] = None
    first_message: Optional[str] = None
    example_messages: Optional[List[str]] = None
    scenario: Optional[str] = None
    personality_summary: Optional[str] = None
    creator_notes: Optional[str] = None
    tags: Optional[List[str]] = None
    abilities: Optional[Dict[str, int]] = None
    stats: Optional[Dict[str, int]] = None
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    position: Optional[Dict[str, int]] = None
    proficient_skills: Optional[List[str]] = None
    proficient_saves: Optional[List[str]] = None
    inventory: Optional[Dict[str, int]] = None
    png_metadata: Optional[Dict[str, str]] = None
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 验证生命值
        if self.hp is not None and self.hp < 0:
            errors.append("当前生命值不能小于0")
        
        if self.max_hp is not None and self.max_hp <= 0:
            errors.append("最大生命值必须大于0")
        
        if (self.hp is not None and self.max_hp is not None and 
            self.hp > self.max_hp):
            errors.append("当前生命值不能大于最大生命值")
        
        # 验证能力值
        if self.abilities:
            ability_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            for ability in ability_names:
                value = self.abilities.get(ability)
                if value is not None and (value < 1 or value > 30):
                    errors.append(f"能力值 {ability} 必须在1-30之间")
        
        # 验证统计数据
        if self.stats:
            if self.stats.get('level', 1) < 1:
                errors.append("角色等级必须大于0")
            
            if self.stats.get('armor_class', 10) < 1:
                errors.append("护甲等级必须大于0")
        
        return errors


@dataclass
class CharacterCardImportDto:
    """导入角色卡请求对象
    
    用于传输导入角色卡的请求数据，遵循单一职责原则，
    专门负责导入请求数据的传输。
    """
    data: Dict[str, Any]
    format: str = "json"  # json, png_base64
    
    def validate(self) -> List[str]:
        """验证请求数据
        
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        if not self.data:
            errors.append("导入数据不能为空")
        
        if self.format not in ["json", "png_base64"]:
            errors.append("不支持的导入格式")
        
        if self.format == "json":
            if not self.data.get("name"):
                errors.append("角色名称不能为空")
        
        return errors


@dataclass
class CharacterCardExportDto:
    """导出角色卡响应对象
    
    用于传输导出角色卡的响应数据，遵循单一职责原则，
    专门负责导出响应数据的传输。
    """
    data: Dict[str, Any]
    format: str = "json"  # json, png_base64
    filename: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            'data': self.data,
            'format': self.format,
            'filename': self.filename,
        }