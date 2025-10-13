"""
传说书服务单元测试

测试传说书服务的各种功能，包括创建、更新、删除、搜索和激活。
遵循测试驱动开发原则，确保代码质量和功能正确性。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.domain.models.lorebook import (
    Lorebook, LorebookEntry, KeywordPattern, ActivationRule, 
    ActivationType, KeywordType
)
from src.domain.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from src.domain.dtos.lorebook_dtos import (
    LorebookCreateDto, LorebookUpdateDto, LorebookEntryCreateDto,
    LorebookEntryUpdateDto, LorebookActivationDto, LorebookImportDto
)
from src.application.services.lorebook_service import LorebookService
from src.application.services.keyword_matcher_service import KeywordMatcherService
from src.core.exceptions import ValidationException, BusinessRuleException, NotFoundException
from src.core.interfaces import Logger


class TestLorebookService:
    """传说书服务测试类"""
    
    @pytest.fixture
    def mock_lorebook_repository(self):
        """模拟传说书仓储"""
        return Mock(spec=LorebookRepository)
    
    @pytest.fixture
    def mock_entry_repository(self):
        """模拟条目仓储"""
        return Mock(spec=LorebookEntryRepository)
    
    @pytest.fixture
    def mock_keyword_matcher(self):
        """模拟关键词匹配服务"""
        return Mock(spec=KeywordMatcherService)
    
    @pytest.fixture
    def mock_logger(self):
        """模拟日志记录器"""
        return Mock(spec=Logger)
    
    @pytest.fixture
    def lorebook_service(self, mock_lorebook_repository, mock_entry_repository, mock_keyword_matcher, mock_logger):
        """传说书服务实例"""
        return LorebookService(
            lorebook_repository=mock_lorebook_repository,
            entry_repository=mock_entry_repository,
            keyword_matcher=mock_keyword_matcher,
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_lorebook(self):
        """示例传说书"""
        lorebook = Lorebook(
            name="测试传说书",
            description="这是一个测试传说书",
            version="1.0.0",
            tags={"测试", "示例"},
            metadata={"author": "测试"}
        )
        return lorebook
    
    @pytest.fixture
    def sample_entry(self):
        """示例条目"""
        keyword = KeywordPattern(
            pattern="龙",
            type=KeywordType.PARTIAL,
            case_sensitive=False,
            weight=1.0
        )
        
        activation_rule = ActivationRule(
            type=ActivationType.KEYWORD,
            keywords=[keyword],
            priority=1,
            max_activations=None,
            cooldown_seconds=None
        )
        
        entry = LorebookEntry(
            title="巨龙传说",
            content="在古老的山脉中，栖息着一条强大的巨龙...",
            keywords=[keyword],
            activation_rule=activation_rule,
            tags={"传说", "龙"},
            metadata={"source": "古老文献"}
        )
        return entry
    
    # 传说书管理测试
    
    def test_create_lorebook_success(self, lorebook_service, mock_lorebook_repository):
        """测试成功创建传说书"""
        # 准备测试数据
        create_dto = LorebookCreateDto(
            name="新传说书",
            description="新的传说书描述",
            version="1.0.0",
            tags=["测试"],
            metadata={"type": "test"}
        )
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_name.return_value = False
        mock_lorebook_repository.save = Mock()
        
        # 执行测试
        result = lorebook_service.create_lorebook(create_dto)
        
        # 验证结果
        assert result.name == "新传说书"
        assert result.description == "新的传说书描述"
        assert result.version == "1.0.0"
        assert result.tags == ["测试"]
        assert result.metadata["type"] == "test"
        
        # 验证交互
        mock_lorebook_repository.exists_by_name.assert_called_once_with("新传说书")
        mock_lorebook_repository.save.assert_called_once()
    
    def test_create_lorebook_name_exists(self, lorebook_service, mock_lorebook_repository):
        """测试创建传说书时名称已存在"""
        # 准备测试数据
        create_dto = LorebookCreateDto(name="已存在的传说书")
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_name.return_value = True
        
        # 执行测试并验证异常
        with pytest.raises(BusinessRuleException, match="传说书名称已存在"):
            lorebook_service.create_lorebook(create_dto)
        
        # 验证交互
        mock_lorebook_repository.exists_by_name.assert_called_once_with("已存在的传说书")
        mock_lorebook_repository.save.assert_not_called()
    
    def test_create_lorebook_validation_error(self, lorebook_service):
        """测试创建传说书验证失败"""
        # 准备测试数据
        create_dto = LorebookCreateDto(name="")  # 空名称
        
        # 执行测试并验证异常
        with pytest.raises(ValidationException):
            lorebook_service.create_lorebook(create_dto)
    
    def test_get_lorebook_success(self, lorebook_service, mock_lorebook_repository, sample_lorebook):
        """测试成功获取传说书"""
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = sample_lorebook
        
        # 执行测试
        result = lorebook_service.get_lorebook("test-id")
        
        # 验证结果
        assert result.name == "测试传说书"
        assert result.description == "这是一个测试传说书"
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("test-id")
    
    def test_get_lorebook_not_found(self, lorebook_service, mock_lorebook_repository):
        """测试获取不存在的传说书"""
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.get_lorebook("non-existent-id")
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("non-existent-id")
    
    def test_update_lorebook_success(self, lorebook_service, mock_lorebook_repository, sample_lorebook):
        """测试成功更新传说书"""
        # 准备测试数据
        update_dto = LorebookUpdateDto(
            name="更新后的传说书",
            description="更新后的描述"
        )
        
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = sample_lorebook
        mock_lorebook_repository.exists_by_name.return_value = False
        mock_lorebook_repository.update = Mock()
        
        # 执行测试
        result = lorebook_service.update_lorebook("test-id", update_dto)
        
        # 验证结果
        assert result.name == "更新后的传说书"
        assert result.description == "更新后的描述"
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("test-id")
        mock_lorebook_repository.update.assert_called_once()
    
    def test_delete_lorebook_success(self, lorebook_service, mock_lorebook_repository):
        """测试成功删除传说书"""
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = True
        mock_lorebook_repository.delete.return_value = True
        
        # 执行测试
        result = lorebook_service.delete_lorebook("test-id")
        
        # 验证结果
        assert result is True
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("test-id")
        mock_lorebook_repository.delete.assert_called_once_with("test-id")
    
    def test_delete_lorebook_not_found(self, lorebook_service, mock_lorebook_repository):
        """测试删除不存在的传说书"""
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = False
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.delete_lorebook("non-existent-id")
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("non-existent-id")
        mock_lorebook_repository.delete.assert_not_called()
    
    # 条目管理测试
    
    def test_create_entry_success(self, lorebook_service, mock_lorebook_repository, mock_entry_repository, sample_lorebook):
        """测试成功创建条目"""
        # 准备测试数据
        create_dto = LorebookEntryCreateDto(
            title="新条目",
            content="新条目的内容",
            keywords=[
                {
                    "pattern": "关键词",
                    "type": "partial",
                    "case_sensitive": False,
                    "weight": 1.0
                }
            ],
            activation_rule={
                "type": "keyword",
                "keywords": [
                    {
                        "pattern": "关键词",
                        "type": "partial",
                        "case_sensitive": False,
                        "weight": 1.0
                    }
                ],
                "priority": 1,
                "max_activations": None,
                "cooldown_seconds": None
            },
            tags=["测试"]
        )
        
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = sample_lorebook
        mock_entry_repository.entry_title_exists.return_value = False
        mock_lorebook_repository.update = Mock()
        
        # 执行测试
        result = lorebook_service.create_entry("lorebook-id", create_dto)
        
        # 验证结果
        assert result.title == "新条目"
        assert result.content == "新条目的内容"
        assert result.tags == ["测试"]
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("lorebook-id")
        mock_entry_repository.entry_title_exists.assert_called_once_with("lorebook-id", "新条目")
        mock_lorebook_repository.update.assert_called_once()
    
    def test_create_entry_lorebook_not_found(self, lorebook_service, mock_lorebook_repository):
        """测试创建条目时传说书不存在"""
        # 准备测试数据
        create_dto = LorebookEntryCreateDto(title="新条目", content="内容")
        
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.create_entry("non-existent-id", create_dto)
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("non-existent-id")
    
    def test_create_entry_title_exists(self, lorebook_service, mock_lorebook_repository, mock_entry_repository, sample_lorebook):
        """测试创建条目时标题已存在"""
        # 准备测试数据
        create_dto = LorebookEntryCreateDto(title="已存在的条目", content="内容")
        
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = sample_lorebook
        mock_entry_repository.entry_title_exists.return_value = True
        
        # 执行测试并验证异常
        with pytest.raises(BusinessRuleException, match="条目标题已存在"):
            lorebook_service.create_entry("lorebook-id", create_dto)
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("lorebook-id")
        mock_entry_repository.entry_title_exists.assert_called_once_with("lorebook-id", "已存在的条目")
    
    def test_get_entry_success(self, lorebook_service, mock_entry_repository, sample_entry):
        """测试成功获取条目"""
        # 设置模拟行为
        mock_entry_repository.find_entry_by_id.return_value = sample_entry
        
        # 执行测试
        result = lorebook_service.get_entry("lorebook-id", "entry-id")
        
        # 验证结果
        assert result.title == "巨龙传说"
        assert result.content == "在古老的山脉中，栖息着一条强大的巨龙..."
        
        # 验证交互
        mock_entry_repository.find_entry_by_id.assert_called_once_with("lorebook-id", "entry-id")
    
    def test_get_entry_not_found(self, lorebook_service, mock_entry_repository):
        """测试获取不存在的条目"""
        # 设置模拟行为
        mock_entry_repository.find_entry_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="条目不存在"):
            lorebook_service.get_entry("lorebook-id", "non-existent-id")
        
        # 验证交互
        mock_entry_repository.find_entry_by_id.assert_called_once_with("lorebook-id", "non-existent-id")
    
    def test_update_entry_success(self, lorebook_service, mock_entry_repository, sample_entry):
        """测试成功更新条目"""
        # 准备测试数据
        update_dto = LorebookEntryUpdateDto(
            title="更新后的条目",
            content="更新后的内容"
        )
        
        # 设置模拟行为
        mock_entry_repository.find_entry_by_id.return_value = sample_entry
        mock_entry_repository.entry_title_exists.return_value = False
        mock_entry_repository.update_entry = Mock()
        
        # 执行测试
        result = lorebook_service.update_entry("lorebook-id", "entry-id", update_dto)
        
        # 验证结果
        assert result.title == "更新后的条目"
        assert result.content == "更新后的内容"
        
        # 验证交互
        mock_entry_repository.find_entry_by_id.assert_called_once_with("lorebook-id", "entry-id")
        mock_entry_repository.update_entry.assert_called_once()
    
    def test_delete_entry_success(self, lorebook_service, mock_entry_repository):
        """测试成功删除条目"""
        # 设置模拟行为
        mock_entry_repository.entry_exists.return_value = True
        mock_entry_repository.delete_entry.return_value = True
        
        # 执行测试
        result = lorebook_service.delete_entry("lorebook-id", "entry-id")
        
        # 验证结果
        assert result is True
        
        # 验证交互
        mock_entry_repository.entry_exists.assert_called_once_with("lorebook-id", "entry-id")
        mock_entry_repository.delete_entry.assert_called_once_with("lorebook-id", "entry-id")
    
    def test_delete_entry_not_found(self, lorebook_service, mock_entry_repository):
        """测试删除不存在的条目"""
        # 设置模拟行为
        mock_entry_repository.entry_exists.return_value = False
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="条目不存在"):
            lorebook_service.delete_entry("lorebook-id", "non-existent-id")
        
        # 验证交互
        mock_entry_repository.entry_exists.assert_called_once_with("lorebook-id", "non-existent-id")
        mock_entry_repository.delete_entry.assert_not_called()
    
    # 激活功能测试
    
    def test_activate_entries_success(self, lorebook_service, mock_lorebook_repository, mock_entry_repository, sample_entry):
        """测试成功激活条目"""
        # 准备测试数据
        activation_dto = LorebookActivationDto(
            text="巨龙出现了",
            context={"location": "山脉"},
            max_entries=5
        )
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = True
        mock_entry_repository.activate_entries.return_value = [sample_entry]
        
        # 执行测试
        result = lorebook_service.activate_entries("lorebook-id", activation_dto)
        
        # 验证结果
        assert len(result.activated_entries) == 1
        assert result.activated_entries[0].title == "巨龙传说"
        assert result.total_candidates == 0  # 由于模拟实现
        assert result.activation_text == "巨龙出现了"
        assert result.context["location"] == "山脉"
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("lorebook-id")
        mock_entry_repository.activate_entries.assert_called_once_with("lorebook-id", "巨龙出现了", {"location": "山脉"})
    
    def test_activate_entries_lorebook_not_found(self, lorebook_service, mock_lorebook_repository, mock_entry_repository):
        """测试激活条目时传说书不存在"""
        # 准备测试数据
        activation_dto = LorebookActivationDto(text="测试文本")
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = False
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.activate_entries("non-existent-id", activation_dto)
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("non-existent-id")
        mock_entry_repository.activate_entries.assert_not_called()
    
    def test_activate_entries_validation_error(self, lorebook_service):
        """测试激活条目验证失败"""
        # 准备测试数据
        activation_dto = LorebookActivationDto(text="")  # 空文本
        
        # 执行测试并验证异常
        with pytest.raises(ValidationException):
            lorebook_service.activate_entries("lorebook-id", activation_dto)
    
    # 导入导出测试
    
    def test_export_lorebook_success(self, lorebook_service, mock_lorebook_repository, sample_lorebook):
        """测试成功导出传说书"""
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = sample_lorebook
        mock_lorebook_repository.export_lorebook.return_value = {"name": "测试传说书"}
        
        # 执行测试
        result = lorebook_service.export_lorebook("lorebook-id", "json")
        
        # 验证结果
        assert result.format == "json"
        assert result.data["name"] == "测试传说书"
        assert result.filename is not None
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("lorebook-id")
        mock_lorebook_repository.export_lorebook.assert_called_once_with("lorebook-id", "json")
    
    def test_export_lorebook_not_found(self, lorebook_service, mock_lorebook_repository):
        """测试导出不存在的传说书"""
        # 设置模拟行为
        mock_lorebook_repository.find_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.export_lorebook("non-existent-id")
        
        # 验证交互
        mock_lorebook_repository.find_by_id.assert_called_once_with("non-existent-id")
        mock_lorebook_repository.export_lorebook.assert_not_called()
    
    def test_import_lorebook_success(self, lorebook_service, mock_lorebook_repository, sample_lorebook):
        """测试成功导入传说书"""
        # 准备测试数据
        import_dto = LorebookImportDto(
            data={"name": "导入的传说书"},
            format="json"
        )
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_name.return_value = False
        mock_lorebook_repository.import_lorebook.return_value = sample_lorebook
        
        # 执行测试
        result = lorebook_service.import_lorebook(import_dto)
        
        # 验证结果
        assert result.name == "测试传说书"
        
        # 验证交互
        mock_lorebook_repository.exists_by_name.assert_called_once_with("导入的传说书")
        mock_lorebook_repository.import_lorebook.assert_called_once_with({"name": "导入的传说书"}, "json")
    
    def test_import_lorebook_name_exists(self, lorebook_service, mock_lorebook_repository):
        """测试导入传说书时名称已存在"""
        # 准备测试数据
        import_dto = LorebookImportDto(
            data={"name": "已存在的传说书"},
            format="json"
        )
        
        # 设置模拟行为
        mock_lorebook_repository.exists_by_name.return_value = True
        
        # 执行测试并验证异常
        with pytest.raises(BusinessRuleException, match="传说书名称已存在"):
            lorebook_service.import_lorebook(import_dto)
        
        # 验证交互
        mock_lorebook_repository.exists_by_name.assert_called_once_with("已存在的传说书")
        mock_lorebook_repository.import_lorebook.assert_not_called()
    
    # 统计功能测试
    
    def test_get_lorebook_statistics_success(self, lorebook_service, mock_lorebook_repository):
        """测试成功获取传说书统计信息"""
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = True
        mock_lorebook_repository.get_statistics.return_value = {
            "total_entries": 10,
            "active_entries": 8,
            "total_activations": 25,
            "average_activations": 2.5,
            "tags": ["测试", "传说"],
            "version": "1.0.0"
        }
        
        # 执行测试
        result = lorebook_service.get_lorebook_statistics("lorebook-id")
        
        # 验证结果
        assert result.total_entries == 10
        assert result.active_entries == 8
        assert result.total_activations == 25
        assert result.average_activations == 2.5
        assert result.tags == ["测试", "传说"]
        assert result.version == "1.0.0"
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("lorebook-id")
        mock_lorebook_repository.get_statistics.assert_called_once_with("lorebook-id")
    
    def test_get_lorebook_statistics_not_found(self, lorebook_service, mock_lorebook_repository):
        """测试获取不存在传说书的统计信息"""
        # 设置模拟行为
        mock_lorebook_repository.exists_by_id.return_value = False
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException, match="传说书不存在"):
            lorebook_service.get_lorebook_statistics("non-existent-id")
        
        # 验证交互
        mock_lorebook_repository.exists_by_id.assert_called_once_with("non-existent-id")
        mock_lorebook_repository.get_statistics.assert_not_called()
    
    def test_get_most_activated_entries_success(self, lorebook_service, mock_entry_repository, sample_entry):
        """测试成功获取最常激活的条目"""
        # 设置模拟行为
        mock_entry_repository.get_most_activated_entries.return_value = [sample_entry]
        
        # 执行测试
        result = lorebook_service.get_most_activated_entries("lorebook-id", 5)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].title == "巨龙传说"
        
        # 验证交互
        mock_entry_repository.get_most_activated_entries.assert_called_once_with("lorebook-id", 5)
    
    def test_get_recently_activated_entries_success(self, lorebook_service, mock_entry_repository, sample_entry):
        """测试成功获取最近激活的条目"""
        # 设置模拟行为
        mock_entry_repository.get_recently_activated_entries.return_value = [sample_entry]
        
        # 执行测试
        result = lorebook_service.get_recently_activated_entries("lorebook-id", 3)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].title == "巨龙传说"
        
        # 验证交互
        mock_entry_repository.get_recently_activated_entries.assert_called_once_with("lorebook-id", 3)


if __name__ == "__main__":
    pytest.main([__file__])