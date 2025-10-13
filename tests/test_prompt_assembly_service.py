"""
提示组装服务单元测试

测试提示组装服务的各种功能，包括提示构建、上下文管理和Token计算。
遵循测试驱动开发(TDD)原则，确保代码质量和功能正确性。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.domain.models.prompt import (
    PromptTemplate, PromptSection, PromptSectionType, PromptContext,
    PromptBuilder, TruncationStrategy, LLMProvider, TokenLimit
)
from src.domain.dtos.prompt_dtos import (
    PromptBuildDto, PromptPreviewDto, PromptContextDto,
    PromptTemplateDto, PromptTemplateCreateDto, PromptTemplateUpdateDto,
    PromptStatisticsDto, PromptTokenCountDto, PromptTokenCountResponseDto
)
from src.domain.repositories.prompt_repository import PromptRepository
from src.application.services.prompt_assembly_service import PromptAssemblyService
from src.application.services.token_counter_service import TokenCounterService
from src.core.interfaces import Logger
from src.core.exceptions import ValidationException, NotFoundException, BusinessRuleException


class TestPromptAssemblyService:
    """提示组装服务测试类"""
    
    @pytest.fixture
    def mock_prompt_repository(self):
        """模拟提示仓储"""
        return Mock(spec=PromptRepository)
    
    @pytest.fixture
    def mock_token_counter(self):
        """模拟Token计数服务"""
        return Mock(spec=TokenCounterService)
    
    @pytest.fixture
    def mock_logger(self):
        """模拟日志记录器"""
        return Mock(spec=Logger)
    
    @pytest.fixture
    def prompt_service(self, mock_prompt_repository, mock_token_counter, mock_logger):
        """创建提示组装服务实例"""
        return PromptAssemblyService(
            prompt_repository=mock_prompt_repository,
            token_counter=mock_token_counter,
            logger=mock_logger
        )
    
    @pytest.fixture
    def sample_template(self):
        """创建示例模板"""
        sections = [
            PromptSection(
                content="你是一个专业的RPG游戏主持人。",
                section_type=PromptSectionType.SYSTEM,
                priority=100
            ),
            PromptSection(
                content="角色信息：\n{character_description}",
                section_type=PromptSectionType.ROLE,
                priority=90
            ),
            PromptSection(
                content="世界设定：\n{world_info}",
                section_type=PromptSectionType.WORLD,
                priority=80
            )
        ]
        
        return PromptTemplate(
            name="测试模板",
            description="用于测试的模板",
            sections=sections
        )
    
    @pytest.fixture
    def sample_context_dto(self):
        """创建示例上下文DTO"""
        return PromptContextDto(
            character_name="测试角色",
            character_description="这是一个勇敢的战士",
            world_info="这是一个奇幻世界",
            chat_history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好，冒险者！"}
            ],
            current_input="我想开始冒险",
            variables={" mood": "brave" }
        )
    
    def test_build_prompt_success(self, prompt_service, mock_prompt_repository, 
                                mock_token_counter, sample_template, sample_context_dto):
        """测试成功构建提示"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.count_tokens_by_sections.return_value = {
            'system': 10,
            'role': 15,
            'world': 12
        }
        
        # 创建请求DTO
        build_dto = PromptBuildDto(
            template_id="test-template-id",
            context=sample_context_dto,
            token_limit={
                'provider': 'openai',
                'model_name': 'gpt-3.5-turbo',
                'max_tokens': 4096,
                'reserved_tokens': 512
            },
            truncation_strategy=TruncationStrategy.SMART
        )
        
        # 执行测试
        result = prompt_service.build_prompt(build_dto)
        
        # 验证结果
        assert isinstance(result, PromptPreviewDto)
        assert result.prompt is not None
        assert result.token_count == 37  # 10 + 15 + 12
        assert len(result.sections) == 3
        assert result.variables_used == sample_context_dto.variables
        assert result.missing_variables == []
        assert result.build_time_ms >= 0
        
        # 验证模拟调用
        mock_prompt_repository.find_by_id.assert_called_once_with("test-template-id")
        mock_token_counter.count_tokens_by_sections.assert_called_once()
    
    def test_build_prompt_template_not_found(self, prompt_service, mock_prompt_repository, 
                                            sample_context_dto):
        """测试模板不存在的情况"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = None
        
        # 创建请求DTO
        build_dto = PromptBuildDto(
            template_id="non-existent-template",
            context=sample_context_dto
        )
        
        # 执行测试并验证异常
        with pytest.raises(NotFoundException) as exc_info:
            prompt_service.build_prompt(build_dto)
        
        assert "提示模板不存在" in str(exc_info.value)
    
    def test_build_prompt_template_inactive(self, prompt_service, mock_prompt_repository, 
                                           sample_template, sample_context_dto):
        """测试模板已停用的情况"""
        # 设置模拟
        sample_template.deactivate()
        mock_prompt_repository.find_by_id.return_value = sample_template
        
        # 创建请求DTO
        build_dto = PromptBuildDto(
            template_id="inactive-template",
            context=sample_context_dto
        )
        
        # 执行测试并验证异常
        with pytest.raises(BusinessRuleException) as exc_info:
            prompt_service.build_prompt(build_dto)
        
        assert "模板已停用" in str(exc_info.value)
    
    def test_build_prompt_validation_error(self, prompt_service, sample_context_dto):
        """测试验证失败的情况"""
        # 创建无效请求DTO
        build_dto = PromptBuildDto(
            template_id="",  # 空ID应该导致验证失败
            context=sample_context_dto
        )
        
        # 执行测试并验证异常
        with pytest.raises(ValidationException) as exc_info:
            prompt_service.build_prompt(build_dto)
        
        assert "验证失败" in str(exc_info.value)
    
    def test_preview_prompt_success(self, prompt_service, mock_prompt_repository, 
                                  mock_token_counter, sample_template, sample_context_dto):
        """测试成功预览提示"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.count_tokens_by_sections.return_value = {
            'system': 10,
            'role': 15,
            'world': 12
        }
        mock_token_counter.validate_token_limit.return_value = (False, 37, 3584)
        
        # 执行测试
        result = prompt_service.preview_prompt(
            "test-template-id", 
            sample_context_dto, 
            LLMProvider.OPENAI, 
            "gpt-3.5-turbo"
        )
        
        # 验证结果
        assert isinstance(result, PromptPreviewDto)
        assert result.prompt is not None
        assert result.token_count == 37
        assert len(result.sections) == 3
        assert not result.truncation_applied
        assert result.build_time_ms == 0  # 预览不计时
        
        # 验证模拟调用
        mock_prompt_repository.find_by_id.assert_called_once_with("test-template-id")
        mock_token_counter.validate_token_limit.assert_called_once()
    
    def test_create_context_success(self, prompt_service):
        """测试成功创建上下文"""
        # 执行测试
        result = prompt_service.create_context(
            character_name="测试角色",
            character_description="这是一个勇敢的战士",
            world_info="这是一个奇幻世界",
            chat_history=[
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好，冒险者！"}
            ],
            current_input="我想开始冒险",
            variables={"mood": "brave"}
        )
        
        # 验证结果
        assert isinstance(result, PromptContextDto)
        assert result.character_name == "测试角色"
        assert result.character_description == "这是一个勇敢的战士"
        assert result.world_info == "这是一个奇幻世界"
        assert len(result.chat_history) == 2
        assert result.current_input == "我想开始冒险"
        assert result.variables == {"mood": "brave"}
    
    def test_update_context_success(self, prompt_service, sample_context_dto):
        """测试成功更新上下文"""
        # 执行测试
        result = prompt_service.update_context(sample_context_dto, {
            "character_name": "更新角色",
            "variables": {"mood": "calm", "location": "forest"}
        })
        
        # 验证结果
        assert isinstance(result, PromptContextDto)
        assert result.character_name == "更新角色"
        assert result.character_description == sample_context_dto.character_description  # 未改变
        assert result.variables == {"mood": "calm", "location": "forest"}
    
    def test_add_chat_message_success(self, prompt_service, sample_context_dto):
        """测试成功添加聊天消息"""
        # 执行测试
        result = prompt_service.add_chat_message(
            sample_context_dto, 
            "user", 
            "我想去森林探险"
        )
        
        # 验证结果
        assert isinstance(result, PromptContextDto)
        assert len(result.chat_history) == 3  # 原来2条 + 新增1条
        assert result.chat_history[-1]["role"] == "user"
        assert result.chat_history[-1]["content"] == "我想去森林探险"
    
    def test_add_chat_message_truncate_history(self, prompt_service, sample_context_dto):
        """测试添加聊天消息时截断历史"""
        # 创建一个有很多消息的上下文
        large_history = [{"role": "user", "content": f"消息{i}"} for i in range(25)]
        large_context = PromptContextDto(
            character_name="测试角色",
            chat_history=large_history
        )
        
        # 执行测试
        result = prompt_service.add_chat_message(
            large_context, 
            "user", 
            "新消息"
        )
        
        # 验证结果
        assert isinstance(result, PromptContextDto)
        assert len(result.chat_history) == 20  # 应该被截断到20条
        assert result.chat_history[-1]["content"] == "新消息"
    
    def test_clear_chat_history_success(self, prompt_service, sample_context_dto):
        """测试成功清除聊天历史"""
        # 执行测试
        result = prompt_service.clear_chat_history(sample_context_dto)
        
        # 验证结果
        assert isinstance(result, PromptContextDto)
        assert len(result.chat_history) == 0
        assert result.character_name == sample_context_dto.character_name  # 其他字段保持不变
    
    def test_calculate_tokens_success(self, prompt_service, mock_prompt_repository, 
                                    mock_token_counter, sample_template, sample_context_dto):
        """测试成功计算Token数量"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.count_tokens_by_sections.return_value = {
            'system': 10,
            'role': 15,
            'world': 12
        }
        
        # 执行测试
        result = prompt_service.calculate_tokens("test-template-id", sample_context_dto)
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['total_tokens'] == 37
        assert result['tokens_by_section'] == {'system': 10, 'role': 15, 'world': 12}
        assert result['character_count'] > 0
        assert result['estimated_sections'] == 3
    
    def test_validate_token_limit_success(self, prompt_service, mock_prompt_repository, 
                                         mock_token_counter, sample_template, sample_context_dto):
        """测试成功验证Token限制"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.validate_token_limit.return_value = (False, 37, 3584)
        mock_token_counter.get_token_limit.return_value = TokenLimit(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            max_tokens=4096,
            reserved_tokens=512
        )
        
        # 执行测试
        result = prompt_service.validate_token_limit(
            "test-template-id", 
            sample_context_dto, 
            LLMProvider.OPENAI, 
            "gpt-3.5-turbo"
        )
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['is_over_limit'] == False
        assert result['current_tokens'] == 37
        assert result['max_tokens'] == 3584
        assert result['available_tokens'] == 3584
        assert result['usage_percentage'] > 0
        assert result['provider'] == LLMProvider.OPENAI.value
        assert result['model_name'] == "gpt-3.5-turbo"
    
    def test_debug_prompt_success(self, prompt_service, mock_prompt_repository, 
                                mock_token_counter, sample_template, sample_context_dto):
        """测试成功调试提示"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.count_tokens_by_sections.return_value = {
            'system': 10,
            'role': 15,
            'world': 12
        }
        
        # 执行测试
        result = prompt_service.debug_prompt("test-template-id", sample_context_dto)
        
        # 验证结果
        assert isinstance(result, dict)
        assert result['template_name'] == "测试模板"
        assert result['template_id'] == "test-template-id"
        assert 'final_prompt' in result
        assert result['total_tokens'] == 37
        assert len(result['sections_analysis']) == 3
        assert result['context_variables'] == sample_context_dto.variables
        assert result['template_variables'] == ['character_description', 'world_info']
    
    def test_get_optimization_suggestions_success(self, prompt_service, mock_prompt_repository, 
                                                  mock_token_counter, sample_template, sample_context_dto):
        """测试成功获取优化建议"""
        # 设置模拟
        mock_prompt_repository.find_by_id.return_value = sample_template
        mock_token_counter.validate_token_limit.return_value = (True, 5000, 4096)  # 超过限制
        mock_token_counter.get_token_limit.return_value = TokenLimit(
            provider=LLMProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            max_tokens=4096,
            reserved_tokens=512
        )
        
        # 执行测试
        suggestions = prompt_service.get_optimization_suggestions(
            "test-template-id", 
            sample_context_dto, 
            LLMProvider.OPENAI, 
            "gpt-3.5-turbo"
        )
        
        # 验证结果
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # 应该有截断建议
        truncation_suggestions = [s for s in suggestions if s['type'] == 'truncation']
        assert len(truncation_suggestions) > 0
        assert truncation_suggestions[0]['priority'] == 'high'
    
    def test_extract_variables(self, prompt_service):
        """测试提取变量"""
        # 测试正常情况
        text = "你好，{name}！欢迎来到{place}。"
        variables = prompt_service._extract_variables(text)
        assert variables == ['name', 'place']
        
        # 测试无变量情况
        text = "你好，世界！"
        variables = prompt_service._extract_variables(text)
        assert variables == []
        
        # 测试重复变量
        text = "{name}和{name}在一起"
        variables = prompt_service._extract_variables(text)
        assert variables == ['name', 'name']
    
    def test_find_used_variables(self, prompt_service):
        """测试查找使用的变量"""
        text = "你好，{name}！欢迎来到{place}。"
        variables = {"name": "Alice", "age": "25", "place": "森林"}
        
        used_vars = prompt_service._find_used_variables(text, variables)
        assert used_vars == {"name": "Alice", "place": "森林"}
    
    def test_dto_to_context(self, prompt_service, sample_context_dto):
        """测试DTO转换为领域对象"""
        # 执行转换
        context = prompt_service._dto_to_context(sample_context_dto)
        
        # 验证结果
        assert isinstance(context, PromptContext)
        assert context.character_name == sample_context_dto.character_name
        assert context.character_description == sample_context_dto.character_description
        assert context.world_info == sample_context_dto.world_info
        assert context.chat_history == sample_context_dto.chat_history
        assert context.current_input == sample_context_dto.current_input
        assert context.variables == sample_context_dto.variables
        assert context.metadata == sample_context_dto.metadata


class TestPromptAssemblyServiceIntegration:
    """提示组装服务集成测试类"""
    
    @pytest.fixture
    def real_prompt_repository(self, tmp_path):
        """创建真实的提示仓储"""
        from src.infrastructure.repositories.prompt_repository_impl import PromptRepositoryImpl
        return PromptRepositoryImpl(storage_path=str(tmp_path / "prompts"))
    
    @pytest.fixture
    def real_token_counter(self):
        """创建真实的Token计数服务"""
        from src.application.services.token_counter_service import TokenCounterService
        mock_logger = Mock(spec=Logger)
        return TokenCounterService(logger=mock_logger)
    
    @pytest.fixture
    def real_prompt_service(self, real_prompt_repository, real_token_counter):
        """创建真实的提示组装服务"""
        mock_logger = Mock(spec=Logger)
        return PromptAssemblyService(
            prompt_repository=real_prompt_repository,
            token_counter=real_token_counter,
            logger=mock_logger
        )
    
    def test_full_prompt_build_workflow(self, real_prompt_service, real_prompt_repository):
        """测试完整的提示构建工作流"""
        # 创建模板
        from src.domain.models.prompt import PromptSection, PromptSectionType
        from src.domain.dtos.prompt_dtos import PromptTemplateCreateDto
        
        sections = [
            {
                'content': "你是一个{role}。",
                'section_type': 'system',
                'priority': 100
            },
            {
                'content': "背景：{background}",
                'section_type': 'world',
                'priority': 90
            }
        ]
        
        create_dto = PromptTemplateCreateDto(
            name="集成测试模板",
            description="用于集成测试的模板",
            sections=sections
        )
        
        # 创建模板服务
        from src.application.services.prompt_template_service import PromptTemplateService
        mock_logger = Mock(spec=Logger)
        template_service = PromptTemplateService(
            prompt_repository=real_prompt_repository,
            token_counter=real_token_counter,
            logger=mock_logger
        )
        
        # 创建模板
        template_dto = template_service.create_template(create_dto)
        template_id = template_dto.id
        
        # 创建上下文
        context_dto = real_prompt_service.create_context(
            character_name="测试角色",
            character_description="勇敢的冒险者",
            world_info="奇幻世界",
            variables={
                "role": "向导",
                "background": "在一片神秘的森林中"
            }
        )
        
        # 构建请求
        from src.domain.dtos.prompt_dtos import PromptBuildDto, TruncationStrategy
        build_dto = PromptBuildDto(
            template_id=template_id,
            context=context_dto,
            truncation_strategy=TruncationStrategy.SMART
        )
        
        # 构建提示
        result = real_prompt_service.build_prompt(build_dto)
        
        # 验证结果
        assert isinstance(result, PromptPreviewDto)
        assert "你是一个向导" in result.prompt
        assert "在一片神秘的森林中" in result.prompt
        assert result.token_count > 0
        assert len(result.sections) == 2
        assert result.variables_used["role"] == "向导"
        assert result.variables_used["background"] == "在一片神秘的森林中"
        assert result.missing_variables == []
        
        # 测试统计信息
        stats = real_prompt_service.calculate_tokens(template_id, context_dto)
        assert stats['total_tokens'] == result.token_count
        assert 'tokens_by_section' in stats
        
        # 测试调试信息
        debug_info = real_prompt_service.debug_prompt(template_id, context_dto)
        assert debug_info['template_name'] == "集成测试模板"
        assert debug_info['final_prompt'] == result.prompt
        assert len(debug_info['sections_analysis']) == 2