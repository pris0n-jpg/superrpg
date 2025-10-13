"""
角色卡管理服务单元测试

该模块测试角色卡管理服务的各种功能，确保业务逻辑的正确性。
遵循SOLID原则，特别是单一职责原则(SRP)，
专门负责角色卡服务的测试。
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.domain.models.characters import (
    CharacterCard, CharacterCardInfo, PNGMetadata, 
    Abilities, CharacterStats, Position, Condition
)
from src.domain.dtos import (
    CharacterCardDto, CharacterCardListDto,
    CharacterCardCreateDto, CharacterCardUpdateDto,
    CharacterCardImportDto, CharacterCardExportDto
)
from src.application.services.character_card_service import CharacterCardService
from src.domain.repositories.character_repository import CharacterRepository
from src.core.interfaces import Logger
from src.core.exceptions import (
    ValidationException, NotFoundException, 
    DuplicateException, BusinessRuleException
)


class TestCharacterCardService:
    """角色卡管理服务测试类"""
    
    @pytest.fixture
    def mock_character_repository(self):
        """模拟角色仓储"""
        return Mock(spec=CharacterRepository)
    
    @pytest.fixture
    def mock_logger(self):
        """模拟日志记录器"""
        return Mock(spec=Logger)
    
    @pytest.fixture
    def character_card_service(self, mock_character_repository, mock_logger):
        """角色卡管理服务实例"""
        return CharacterCardService(mock_character_repository, mock_logger)
    
    @pytest.fixture
    def sample_character_card(self):
        """示例角色卡"""
        card_info = CharacterCardInfo(
            description="勇敢的骑士",
            first_message="你好，我是骑士。",
            example_messages=["你好", "今天天气不错"],
            scenario="中世纪城堡",
            personality_summary="勇敢、正直",
            creator_notes="主要角色",
            tags=["骑士", "勇敢"]
        )
        
        abilities = Abilities(
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=12,
            charisma=14
        )
        
        stats = CharacterStats(
            level=5,
            armor_class=16,
            proficiency_bonus=3,
            speed_steps=6,
            reach_steps=1
        )
        
        png_metadata = PNGMetadata(
            name="骑士",
            description="勇敢的骑士",
            personality="勇敢、正直",
            scenario="中世纪城堡",
            first_mes="你好，我是骑士。"
        )
        
        return CharacterCard(
            name="骑士",
            card_info=card_info,
            abilities=abilities,
            stats=stats,
            hp=45,
            max_hp=50,
            position=Position(x=5, y=5),
            png_metadata=png_metadata,
            proficient_skills=["athletics", "intimidation"],
            proficient_saves=["strength", "charisma"],
            inventory={"长剑": 1, "盾牌": 1}
        )
    
    def test_create_character_card_success(self, character_card_service, 
                                          mock_character_repository, mock_logger):
        """测试成功创建角色卡"""
        # 准备测试数据
        create_dto = CharacterCardCreateDto(
            name="法师",
            description="智慧的法师",
            first_message="你好，我是法师。",
            abilities={
                'strength': 8,
                'dexterity': 14,
                'constitution': 12,
                'intelligence': 16,
                'wisdom': 14,
                'charisma': 12
            },
            stats={
                'level': 5,
                'armor_class': 12,
                'proficiency_bonus': 3
            },
            hp=30,
            max_hp=35,
            tags=["法师", "智慧"]
        )
        
        # 模拟仓储行为
        mock_character_repository.find_by_name.return_value = None
        mock_character_repository.save.return_value = None
        
        # 执行测试
        result = character_card_service.create_character_card(create_dto)
        
        # 验证结果
        assert result.name == "法师"
        assert result.description == "智慧的法师"
        assert result.first_message == "你好，我是法师。"
        assert result.abilities['intelligence'] == 16
        assert result.stats['level'] == 5
        assert result.hp == 30
        assert result.max_hp == 35
        assert "法师" in result.tags
        
        # 验证仓储调用
        mock_character_repository.find_by_name.assert_called_once_with("法师")
        mock_character_repository.save.assert_called_once()
        
        # 验证日志调用
        mock_logger.info.assert_called_once()
    
    def test_create_character_card_validation_error(self, character_card_service,
                                                  mock_character_repository, mock_logger):
        """测试创建角色卡验证失败"""
        # 准备无效测试数据
        create_dto = CharacterCardCreateDto(
            name="",  # 空名称
            hp=-10,   # 负生命值
            max_hp=0  # 零最大生命值
        )
        
        # 执行测试并验证异常
        with pytest.raises(ValidationException) as exc_info:
            character_card_service.create_character_card(create_dto)
        
        # 验证错误信息
        errors = exc_info.value.args[0] if exc_info.value.args else []
        assert len(errors) >= 3
        assert any("角色名称不能为空" in error for error in errors)
        assert any("当前生命值不能小于0" in error for error in errors)
        assert any("最大生命值必须大于0" in error for error in errors)
    
    def test_create_character_card_duplicate_error(self, character_card_service,
                                                  mock_character_repository, mock_logger,
                                                  sample_character_card):
        """测试创建角色卡重复名称错误"""
        # 准备测试数据
        create_dto = CharacterCardCreateDto(name="骑士")
        
        # 模拟仓储行为
        mock_character_repository.find_by_name.return_value = sample_character_card
        
        # 执行测试并验证异常
        with pytest.raises(DuplicateException) as exc_info:
            character_card_service.create_character_card(create_dto)
        
        # 验证错误信息
        assert "角色名称 '骑士' 已存在" in str(exc_info.value)
        assert exc_info.value.resource_type == "CharacterCard"
        assert exc_info.value.duplicate_key == "name"
        assert exc_info.value.duplicate_value == "骑士"
    
    def test_get_character_card_success(self, character_card_service,
                                       mock_character_repository, mock_logger,
                                       sample_character_card):
        """测试成功获取角色卡"""
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = sample_character_card
        
        # 执行测试
        result = character_card_service.get_character_card("character-123")
        
        # 验证结果
        assert result.name == "骑士"
        assert result.description == "勇敢的骑士"
        assert result.abilities['strength'] == 16
        assert result.stats['level'] == 5
        
        # 验证仓储调用
        mock_character_repository.find_by_id.assert_called_once_with("character-123")
    
    def test_get_character_card_not_found(self, character_card_service,
                                         mock_character_repository, mock_logger):
        """测试获取不存在的角色卡"""
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            character_card_service.get_character_card("nonexistent")
        
        # 验证错误信息
        assert "角色卡不存在" in str(exc_info.value)
        assert exc_info.value.resource_type == "CharacterCard"
        assert exc_info.value.resource_id == "nonexistent"
    
    def test_update_character_card_success(self, character_card_service,
                                          mock_character_repository, mock_logger,
                                          sample_character_card):
        """测试成功更新角色卡"""
        # 准备测试数据
        update_dto = CharacterCardUpdateDto(
            description="更勇敢的骑士",
            hp=50,
            max_hp=60
        )
        
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = sample_character_card
        mock_character_repository.update.return_value = None
        
        # 执行测试
        result = character_card_service.update_character_card("character-123", update_dto)
        
        # 验证结果
        assert result.name == "骑士"
        assert result.description == "更勇敢的骑士"
        assert result.hp == 50
        assert result.max_hp == 60
        
        # 验证仓储调用
        mock_character_repository.find_by_id.assert_called_once_with("character-123")
        mock_character_repository.update.assert_called_once()
    
    def test_delete_character_card_success(self, character_card_service,
                                          mock_character_repository, mock_logger,
                                          sample_character_card):
        """测试成功删除角色卡"""
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = sample_character_card
        mock_character_repository.delete.return_value = True
        
        # 执行测试
        result = character_card_service.delete_character_card("character-123")
        
        # 验证结果
        assert result is True
        
        # 验证仓储调用
        mock_character_repository.find_by_id.assert_called_once_with("character-123")
        mock_character_repository.delete.assert_called_once_with("character-123")
    
    def test_get_character_cards_success(self, character_card_service,
                                        mock_character_repository, mock_logger,
                                        sample_character_card):
        """测试成功获取角色卡列表"""
        # 模拟仓储行为
        mock_character_repository.find_all.return_value = [sample_character_card]
        
        # 执行测试
        result = character_card_service.get_character_cards(page=1, page_size=10)
        
        # 验证结果
        assert isinstance(result, CharacterCardListDto)
        assert len(result.characters) == 1
        assert result.total_count == 1
        assert result.page == 1
        assert result.page_size == 10
        assert result.total_pages == 1
        assert result.characters[0].name == "骑士"
    
    def test_import_character_card_json_success(self, character_card_service,
                                              mock_character_repository, mock_logger):
        """测试成功导入JSON格式角色卡"""
        # 准备测试数据
        import_data = {
            'name': '游侠',
            'description': '敏捷的游侠',
            'first_message': '你好，我是游侠。',
            'abilities': {
                'strength': 14,
                'dexterity': 16,
                'constitution': 12,
                'intelligence': 12,
                'wisdom': 14,
                'charisma': 10
            },
            'stats': {
                'level': 5,
                'armor_class': 14,
                'proficiency_bonus': 3
            },
            'hp': 40,
            'max_hp': 45,
            'tags': ['游侠', '敏捷']
        }
        
        import_dto = CharacterCardImportDto(
            data=import_data,
            format="json"
        )
        
        # 模拟仓储行为
        mock_character_repository.save.return_value = None
        
        # 执行测试
        result = character_card_service.import_character_card(import_dto)
        
        # 验证结果
        assert result.name == "游侠"
        assert result.description == "敏捷的游侠"
        assert result.abilities['dexterity'] == 16
        assert result.stats['level'] == 5
        assert "游侠" in result.tags
    
    def test_export_character_card_json_success(self, character_card_service,
                                              mock_character_repository, mock_logger,
                                              sample_character_card):
        """测试成功导出JSON格式角色卡"""
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = sample_character_card
        
        # 执行测试
        result = character_card_service.export_character_card("character-123", "json")
        
        # 验证结果
        assert isinstance(result, CharacterCardExportDto)
        assert result.format == "json"
        assert result.filename == "骑士.json"
        assert 'name' in result.data
        assert result.data['name'] == "骑士"
        assert 'description' in result.data
        assert result.data['description'] == "勇敢的骑士"
    
    def test_export_character_card_png_base64_success(self, character_card_service,
                                                    mock_character_repository, mock_logger,
                                                    sample_character_card):
        """测试成功导出PNG Base64格式角色卡"""
        # 模拟仓储行为
        mock_character_repository.find_by_id.return_value = sample_character_card
        
        # 执行测试
        result = character_card_service.export_character_card("character-123", "png_base64")
        
        # 验证结果
        assert isinstance(result, CharacterCardExportDto)
        assert result.format == "png_base64"
        assert result.filename == "骑士.png.json"
        assert 'name' in result.data
        assert result.data['name'] == "骑士"
        assert 'chara' in result.data
    
    def test_search_characters_with_filters(self, character_card_service,
                                          mock_character_repository, mock_logger,
                                          sample_character_card):
        """测试根据过滤条件搜索角色卡"""
        # 模拟仓储行为
        mock_character_repository.search_characters.return_value = [sample_character_card]
        
        # 执行测试
        result = character_card_service.get_character_cards(
            page=1, 
            page_size=10, 
            filters={'tag': '骑士'}
        )
        
        # 验证结果
        assert isinstance(result, CharacterCardListDto)
        assert len(result.characters) == 1
        assert result.characters[0].name == "骑士"
        
        # 验证仓储调用
        mock_character_repository.search_characters.assert_called_once_with({'tag': '骑士'})
    
    def test_validation_error_handling(self, character_card_service,
                                     mock_character_repository, mock_logger):
        """测试验证错误处理"""
        # 准备无效测试数据
        create_dto = CharacterCardCreateDto(
            name="测试角色",
            abilities={'strength': 50}  # 超出范围的能力值
        )
        
        # 模拟仓储行为
        mock_character_repository.find_by_name.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(ValidationException) as exc_info:
            character_card_service.create_character_card(create_dto)
        
        # 验证错误信息
        errors = exc_info.value.args[0] if exc_info.value.args else []
        assert any("能力值 strength 必须在1-30之间" in error for error in errors)