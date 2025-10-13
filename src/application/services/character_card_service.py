"""
角色卡管理服务

该服务提供角色卡的创建、编辑、导入、导出等功能，
遵循SOLID原则，特别是单一职责原则(SRP)，
专门负责角色卡的业务逻辑管理。
"""

import json
import base64
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import ApplicationService
from ...domain.models.characters import (
    CharacterCard, CharacterCardInfo, PNGMetadata, 
    Abilities, CharacterStats, Position, Condition
)
from ...domain.dtos import (
    CharacterCardDto, CharacterCardListDto,
    CharacterCardCreateDto, CharacterCardUpdateDto,
    CharacterCardImportDto, CharacterCardExportDto
)
from ...domain.repositories.character_repository import CharacterRepository
from ...core.exceptions import (
    ValidationException, NotFoundException, 
    DuplicateException, BusinessRuleException
)
from ...core.interfaces import Logger


class CharacterCardService:
    """角色卡管理服务
    
    遵循单一职责原则，专门负责角色卡的创建、编辑、导入、导出等业务逻辑。
    遵循依赖倒置原则，依赖抽象接口而非具体实现。
    """
    
    def __init__(self, character_repository: CharacterRepository, logger: Logger):
        """初始化角色卡管理服务
        
        Args:
            character_repository: 角色仓储接口
            logger: 日志记录器
        """
        self._character_repository = character_repository
        self._logger = logger
    
    def create_character_card(self, create_dto: CharacterCardCreateDto) -> CharacterCardDto:
        """创建新的角色卡
        
        Args:
            create_dto: 创建角色卡请求数据
            
        Returns:
            CharacterCardDto: 创建的角色卡DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            DuplicateException: 角色名称重复时抛出
        """
        # 验证请求数据
        errors = create_dto.validate()
        if errors:
            raise ValidationException("角色卡数据验证失败", validation_errors=errors)
        
        # 检查角色名称是否已存在
        existing_character = self._character_repository.find_by_name(create_dto.name)
        if existing_character:
            raise DuplicateException(
                f"角色名称 '{create_dto.name}' 已存在",
                "CharacterCard", "name", create_dto.name
            )
        
        try:
            # 创建能力值对象
            abilities_data = create_dto.abilities or {}
            abilities = Abilities(
                strength=abilities_data.get('strength', 10),
                dexterity=abilities_data.get('dexterity', 10),
                constitution=abilities_data.get('constitution', 10),
                intelligence=abilities_data.get('intelligence', 10),
                wisdom=abilities_data.get('wisdom', 10),
                charisma=abilities_data.get('charisma', 10),
            )
            
            # 创建统计数据对象
            stats_data = create_dto.stats or {}
            stats = CharacterStats(
                level=stats_data.get('level', 1),
                armor_class=stats_data.get('armor_class', 10),
                proficiency_bonus=stats_data.get('proficiency_bonus', 2),
                speed_steps=stats_data.get('speed_steps', 6),
                reach_steps=stats_data.get('reach_steps', 1),
            )
            
            # 创建位置对象
            position = None
            if create_dto.position:
                position = Position(
                    x=create_dto.position['x'],
                    y=create_dto.position['y']
                )
            
            # 创建角色卡信息对象
            card_info = CharacterCardInfo(
                description=create_dto.description,
                first_message=create_dto.first_message,
                example_messages=create_dto.example_messages,
                scenario=create_dto.scenario,
                personality_summary=create_dto.personality_summary,
                creator_notes=create_dto.creator_notes,
                tags=create_dto.tags,
            )
            
            # 创建PNG元数据对象
            png_metadata = None
            if create_dto.png_metadata:
                png_metadata = PNGMetadata(
                    name=create_dto.png_metadata.get('name', ''),
                    description=create_dto.png_metadata.get('description', ''),
                    personality=create_dto.png_metadata.get('personality', ''),
                    scenario=create_dto.png_metadata.get('scenario', ''),
                    first_mes=create_dto.png_metadata.get('first_mes', ''),
                    example_dialogue=create_dto.png_metadata.get('example_dialogue', ''),
                    mes_example=create_dto.png_metadata.get('mes_example', ''),
                    background=create_dto.png_metadata.get('background', ''),
                )
            
            # 创建角色卡
            character_card = CharacterCard(
                name=create_dto.name,
                card_info=card_info,
                abilities=abilities,
                stats=stats,
                hp=create_dto.hp,
                max_hp=create_dto.max_hp,
                position=position,
                png_metadata=png_metadata,
                proficient_skills=create_dto.proficient_skills,
                proficient_saves=create_dto.proficient_saves,
                inventory=create_dto.inventory,
            )
            
            # 保存角色卡
            self._character_repository.save(character_card)
            
            # 记录日志
            self._logger.info(f"创建角色卡成功: {character_card.name}", 
                            character_id=str(character_card.id))
            
            # 返回DTO
            return CharacterCardDto.from_domain(character_card)
            
        except Exception as e:
            self._logger.error(f"创建角色卡失败: {str(e)}", name=create_dto.name)
            raise
    
    def get_character_card(self, character_id: str) -> CharacterCardDto:
        """获取角色卡详情
        
        Args:
            character_id: 角色ID
            
        Returns:
            CharacterCardDto: 角色卡DTO
            
        Raises:
            NotFoundException: 角色不存在时抛出
        """
        character = self._character_repository.find_by_id(character_id)
        if not character:
            raise NotFoundException("角色卡不存在", "CharacterCard", character_id)
        
        return CharacterCardDto.from_domain(character)
    
    def update_character_card(self, character_id: str, update_dto: CharacterCardUpdateDto) -> CharacterCardDto:
        """更新角色卡
        
        Args:
            character_id: 角色ID
            update_dto: 更新角色卡请求数据
            
        Returns:
            CharacterCardDto: 更新后的角色卡DTO
            
        Raises:
            NotFoundException: 角色不存在时抛出
            ValidationException: 验证失败时抛出
        """
        # 验证请求数据
        errors = update_dto.validate()
        if errors:
            raise ValidationException("角色卡更新数据验证失败", validation_errors=errors)
        
        # 获取现有角色卡
        character = self._character_repository.find_by_id(character_id)
        if not character:
            raise NotFoundException("角色卡不存在", "CharacterCard", character_id)
        
        try:
            # 更新角色卡信息
            if any([update_dto.description, update_dto.first_message, 
                   update_dto.example_messages, update_dto.scenario,
                   update_dto.personality_summary, update_dto.creator_notes,
                   update_dto.tags]):
                
                # 获取现有信息
                current_info = character.card_info
                
                # 创建新的角色卡信息
                new_info = CharacterCardInfo(
                    description=update_dto.description if update_dto.description is not None else current_info.description,
                    first_message=update_dto.first_message if update_dto.first_message is not None else current_info.first_message,
                    example_messages=update_dto.example_messages if update_dto.example_messages is not None else current_info.example_messages,
                    scenario=update_dto.scenario if update_dto.scenario is not None else current_info.scenario,
                    personality_summary=update_dto.personality_summary if update_dto.personality_summary is not None else current_info.personality_summary,
                    creator_notes=update_dto.creator_notes if update_dto.creator_notes is not None else current_info.creator_notes,
                    tags=update_dto.tags if update_dto.tags is not None else current_info.tags,
                )
                
                character.update_card_info(new_info)
            
            # 更新能力值
            if update_dto.abilities:
                abilities_data = update_dto.abilities
                new_abilities = Abilities(
                    strength=abilities_data.get('strength', character.abilities.strength),
                    dexterity=abilities_data.get('dexterity', character.abilities.dexterity),
                    constitution=abilities_data.get('constitution', character.abilities.constitution),
                    intelligence=abilities_data.get('intelligence', character.abilities.intelligence),
                    wisdom=abilities_data.get('wisdom', character.abilities.wisdom),
                    charisma=abilities_data.get('charisma', character.abilities.charisma),
                )
                character.abilities = new_abilities
            
            # 更新统计数据
            if update_dto.stats:
                stats_data = update_dto.stats
                new_stats = CharacterStats(
                    level=stats_data.get('level', character.stats.level),
                    armor_class=stats_data.get('armor_class', character.stats.armor_class),
                    proficiency_bonus=stats_data.get('proficiency_bonus', character.stats.proficiency_bonus),
                    speed_steps=stats_data.get('speed_steps', character.stats.speed_steps),
                    reach_steps=stats_data.get('reach_steps', character.stats.reach_steps),
                )
                character.stats = new_stats
            
            # 更新生命值
            if update_dto.hp is not None:
                character.hp = update_dto.hp
            if update_dto.max_hp is not None:
                character.max_hp = update_dto.max_hp
            
            # 更新位置
            if update_dto.position:
                character.position = Position(
                    x=update_dto.position['x'],
                    y=update_dto.position['y']
                )
            
            # 更新技能和物品
            if update_dto.proficient_skills is not None:
                character.proficient_skills = update_dto.proficient_skills
            if update_dto.proficient_saves is not None:
                character.proficient_saves = update_dto.proficient_saves
            if update_dto.inventory is not None:
                character.inventory = update_dto.inventory
            
            # 更新PNG元数据
            if update_dto.png_metadata:
                png_data = update_dto.png_metadata
                new_png_metadata = PNGMetadata(
                    name=png_data.get('name', character.png_metadata.name),
                    description=png_data.get('description', character.png_metadata.description),
                    personality=png_data.get('personality', character.png_metadata.personality),
                    scenario=png_data.get('scenario', character.png_metadata.scenario),
                    first_mes=png_data.get('first_mes', character.png_metadata.first_mes),
                    example_dialogue=png_data.get('example_dialogue', character.png_metadata.example_dialogue),
                    mes_example=png_data.get('mes_example', character.png_metadata.mes_example),
                    background=png_data.get('background', character.png_metadata.background),
                )
                character.update_png_metadata(new_png_metadata)
            
            # 验证角色卡
            character.validate()
            
            # 保存更新
            self._character_repository.update(character)
            
            # 记录日志
            self._logger.info(f"更新角色卡成功: {character.name}", 
                            character_id=str(character.id))
            
            # 返回DTO
            return CharacterCardDto.from_domain(character)
            
        except Exception as e:
            self._logger.error(f"更新角色卡失败: {str(e)}", character_id=character_id)
            raise
    
    def delete_character_card(self, character_id: str) -> bool:
        """删除角色卡
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            NotFoundException: 角色不存在时抛出
        """
        character = self._character_repository.find_by_id(character_id)
        if not character:
            raise NotFoundException("角色卡不存在", "CharacterCard", character_id)
        
        try:
            # 删除角色卡
            success = self._character_repository.delete(character_id)
            
            if success:
                # 记录日志
                self._logger.info(f"删除角色卡成功: {character.name}", 
                                character_id=str(character.id))
            else:
                self._logger.warning(f"删除角色卡失败: {character.name}", 
                                   character_id=str(character.id))
            
            return success
            
        except Exception as e:
            self._logger.error(f"删除角色卡失败: {str(e)}", character_id=character_id)
            raise
    
    def get_character_cards(self, page: int = 1, page_size: int = 20, 
                           filters: Optional[Dict[str, Any]] = None) -> CharacterCardListDto:
        """获取角色卡列表
        
        Args:
            page: 页码
            page_size: 每页大小
            filters: 过滤条件
            
        Returns:
            CharacterCardListDto: 角色卡列表DTO
        """
        try:
            # 获取所有角色卡
            if filters:
                characters = self._character_repository.search_characters(filters)
            else:
                characters = self._character_repository.find_all()
            
            # 计算分页
            total_count = len(characters)
            total_pages = (total_count + page_size - 1) // page_size
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            
            # 获取当前页的角色卡
            page_characters = characters[start_index:end_index]
            
            # 转换为DTO
            character_dtos = [CharacterCardDto.from_domain(char) for char in page_characters]
            
            # 返回列表DTO
            return CharacterCardListDto(
                characters=character_dtos,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            self._logger.error(f"获取角色卡列表失败: {str(e)}")
            raise
    
    def import_character_card(self, import_dto: CharacterCardImportDto) -> CharacterCardDto:
        """导入角色卡
        
        Args:
            import_dto: 导入角色卡请求数据
            
        Returns:
            CharacterCardDto: 导入的角色卡DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            DuplicateException: 角色名称重复时抛出
        """
        # 验证请求数据
        errors = import_dto.validate()
        if errors:
            raise ValidationException("角色卡导入数据验证失败", validation_errors=errors)
        
        try:
            if import_dto.format == "json":
                # 从JSON数据导入
                character_card = CharacterCard.from_dict(import_dto.data)
            elif import_dto.format == "png_base64":
                # 从PNG Base64数据导入
                png_metadata = PNGMetadata.from_base64(import_dto.data.get('chara', ''))
                
                # 转换为角色卡数据
                character_data = {
                    'name': png_metadata.name or import_dto.data.get('name', ''),
                    'description': png_metadata.description,
                    'first_message': png_metadata.first_mes,
                    'scenario': png_metadata.scenario,
                    'personality_summary': png_metadata.personality,
                    'creator_notes': png_metadata.background,
                    'example_messages': [png_metadata.example_dialogue] if png_metadata.example_dialogue else [],
                    'abilities': import_dto.data.get('abilities', {}),
                    'stats': import_dto.data.get('stats', {}),
                    'hp': import_dto.data.get('hp', 100),
                    'max_hp': import_dto.data.get('max_hp', 100),
                    'proficient_skills': import_dto.data.get('proficient_skills', []),
                    'proficient_saves': import_dto.data.get('proficient_saves', []),
                    'inventory': import_dto.data.get('inventory', {}),
                }
                
                character_card = CharacterCard.from_dict(character_data)
                character_card.png_metadata = png_metadata
            else:
                raise ValidationException(f"不支持的导入格式: {import_dto.format}")
            
            # 检查角色名称是否已存在
            existing_character = self._character_repository.find_by_name(character_card.name)
            if existing_character:
                raise DuplicateException(
                    f"角色名称 '{character_card.name}' 已存在",
                    "CharacterCard", "name", character_card.name
                )
            
            # 保存角色卡
            self._character_repository.save(character_card)
            
            # 记录日志
            self._logger.info(f"导入角色卡成功: {character_card.name}", 
                            character_id=str(character_card.id), format=import_dto.format)
            
            # 返回DTO
            return CharacterCardDto.from_domain(character_card)
            
        except Exception as e:
            self._logger.error(f"导入角色卡失败: {str(e)}", format=import_dto.format)
            raise
    
    def export_character_card(self, character_id: str, format: str = "json") -> CharacterCardExportDto:
        """导出角色卡
        
        Args:
            character_id: 角色ID
            format: 导出格式 (json, png_base64)
            
        Returns:
            CharacterCardExportDto: 导出的角色卡数据
            
        Raises:
            NotFoundException: 角色不存在时抛出
            ValidationException: 不支持的导出格式时抛出
        """
        if format not in ["json", "png_base64"]:
            raise ValidationException(f"不支持的导出格式: {format}")
        
        # 获取角色卡
        character = self._character_repository.find_by_id(character_id)
        if not character:
            raise NotFoundException("角色卡不存在", "CharacterCard", character_id)
        
        try:
            if format == "json":
                # 导出为JSON格式
                data = character.export_to_dict()
                filename = f"{character.name}.json"
            elif format == "png_base64":
                # 导出为PNG Base64格式
                png_metadata = PNGMetadata(
                    name=character.name,
                    description=character.card_info.description,
                    personality=character.card_info.personality_summary,
                    scenario=character.card_info.scenario,
                    first_mes=character.card_info.first_message,
                    example_dialogue='\n'.join(character.card_info.example_messages),
                    mes_example='',
                    background=character.card_info.creator_notes,
                )
                
                data = {
                    'name': character.name,
                    'chara': png_metadata.to_base64(),
                    'abilities': {
                        'strength': character.abilities.strength,
                        'dexterity': character.abilities.dexterity,
                        'constitution': character.abilities.constitution,
                        'intelligence': character.abilities.intelligence,
                        'wisdom': character.abilities.wisdom,
                        'charisma': character.abilities.charisma,
                    },
                    'stats': {
                        'level': character.stats.level,
                        'armor_class': character.stats.armor_class,
                        'proficiency_bonus': character.stats.proficiency_bonus,
                        'speed_steps': character.stats.speed_steps,
                        'reach_steps': character.stats.reach_steps,
                    },
                    'hp': character.hp,
                    'max_hp': character.max_hp,
                    'proficient_skills': character.proficient_skills,
                    'proficient_saves': character.proficient_saves,
                    'inventory': character.inventory,
                }
                filename = f"{character.name}.png.json"
            
            # 记录日志
            self._logger.info(f"导出角色卡成功: {character.name}", 
                            character_id=str(character.id), format=format)
            
            # 返回导出DTO
            return CharacterCardExportDto(
                data=data,
                format=format,
                filename=filename
            )
            
        except Exception as e:
            self._logger.error(f"导出角色卡失败: {str(e)}", character_id=character_id, format=format)
            raise