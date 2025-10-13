"""
传说书管理服务

提供传说书和条目的管理功能，包括创建、编辑、删除、搜索和激活。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ...domain.models.lorebook import (
    Lorebook, LorebookEntry, KeywordPattern, ActivationRule, 
    ActivationType, KeywordType
)
from ...domain.repositories.lorebook_repository import LorebookRepository, LorebookEntryRepository
from ...domain.dtos.lorebook_dtos import (
    LorebookDto, LorebookEntryDto, LorebookListDto, LorebookCreateDto,
    LorebookUpdateDto, LorebookEntryCreateDto, LorebookEntryUpdateDto,
    LorebookImportDto, LorebookExportDto, LorebookActivationDto,
    LorebookActivationResultDto, LorebookStatisticsDto
)
from ...core.interfaces import EventBus, Logger
from ...core.exceptions import ValidationException, BusinessRuleException, NotFoundException
from .keyword_matcher_service import KeywordMatcherService
from .base import ApplicationService


class LorebookService(ApplicationService):
    """传说书管理服务
    
    提供传说书和条目的管理功能，包括创建、编辑、删除、搜索和激活。
    遵循单一职责原则，专门负责传说书业务逻辑的管理。
    """
    
    def __init__(
        self,
        lorebook_repository: LorebookRepository,
        entry_repository: LorebookEntryRepository,
        keyword_matcher: KeywordMatcherService,
        event_bus: EventBus,
        logger: Logger
    ):
        """初始化传说书服务
        
        Args:
            lorebook_repository: 传说书仓储
            entry_repository: 条目仓储
            keyword_matcher: 关键词匹配服务
            logger: 日志记录器
        """
        super().__init__(event_bus, logger)
        self._lorebook_repository = lorebook_repository
        self._entry_repository = entry_repository
        self._keyword_matcher = keyword_matcher
    
    # 传说书管理方法
    
    def create_lorebook(self, create_dto: LorebookCreateDto) -> LorebookDto:
        """创建传说书
        
        Args:
            create_dto: 创建传说书请求对象
            
        Returns:
            LorebookDto: 创建的传说书DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = create_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查名称是否已存在
        if self._lorebook_repository.exists_by_name(create_dto.name):
            raise BusinessRuleException(f"传说书名称已存在: {create_dto.name}")
        
        # 创建传说书
        lorebook = Lorebook(
            name=create_dto.name,
            description=create_dto.description,
            version=create_dto.version,
            tags=set(create_dto.tags),
            metadata=create_dto.metadata
        )
        
        # 保存传说书
        self._lorebook_repository.save(lorebook)
        
        self._logger.info(f"Created lorebook: {lorebook.name} (ID: {lorebook.id})")
        
        return LorebookDto.from_domain(lorebook)
    
    def get_lorebook(self, lorebook_id: str) -> LorebookDto:
        """获取传说书
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            LorebookDto: 传说书DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
        """
        lorebook = self._lorebook_repository.find_by_id(lorebook_id)
        if not lorebook:
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        return LorebookDto.from_domain(lorebook)
    
    def get_lorebooks(self, page: int = 1, page_size: int = 20) -> LorebookListDto:
        """获取传说书列表
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            LorebookListDto: 传说书列表DTO
        """
        # 获取所有传说书
        all_lorebooks = self._lorebook_repository.find_all()
        
        # 简单分页
        total_count = len(all_lorebooks)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        lorebooks_page = all_lorebooks[start_index:end_index]
        
        # 转换为DTO
        lorebook_dtos = [LorebookDto.from_domain(l) for l in lorebooks_page]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return LorebookListDto(
            lorebooks=lorebook_dtos,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def update_lorebook(self, lorebook_id: str, update_dto: LorebookUpdateDto) -> LorebookDto:
        """更新传说书
        
        Args:
            lorebook_id: 传说书ID
            update_dto: 更新传说书请求对象
            
        Returns:
            LorebookDto: 更新后的传说书DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = update_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 获取传说书
        lorebook = self._lorebook_repository.find_by_id(lorebook_id)
        if not lorebook:
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 检查名称是否已存在（如果要更新名称）
        if update_dto.name and update_dto.name != lorebook.name:
            if self._lorebook_repository.exists_by_name(update_dto.name):
                raise BusinessRuleException(f"传说书名称已存在: {update_dto.name}")
        
        # 更新信息
        lorebook.update_info(
            name=update_dto.name,
            description=update_dto.description
        )
        
        if update_dto.version is not None:
            lorebook.version = update_dto.version
        
        if update_dto.tags is not None:
            lorebook.tags = set(update_dto.tags)
        
        if update_dto.metadata is not None:
            lorebook.metadata = update_dto.metadata
        
        # 保存更新
        self._lorebook_repository.update(lorebook)
        
        self._logger.info(f"Updated lorebook: {lorebook.name} (ID: {lorebook.id})")
        
        return LorebookDto.from_domain(lorebook)
    
    def delete_lorebook(self, lorebook_id: str) -> bool:
        """删除传说书
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            NotFoundException: 传说书不存在时抛出
        """
        # 检查传说书是否存在
        if not self._lorebook_repository.exists_by_id(lorebook_id):
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 删除传说书
        success = self._lorebook_repository.delete(lorebook_id)
        
        if success:
            self._logger.info(f"Deleted lorebook: {lorebook_id}")
        
        return success
    
    def search_lorebooks(self, criteria: Dict[str, Any]) -> List[LorebookDto]:
        """搜索传说书
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[LorebookDto]: 匹配的传说书列表
        """
        lorebooks = self._lorebook_repository.search(criteria)
        return [LorebookDto.from_domain(l) for l in lorebooks]
    
    def get_lorebook_statistics(self, lorebook_id: str) -> LorebookStatisticsDto:
        """获取传说书统计信息
        
        Args:
            lorebook_id: 传说书ID
            
        Returns:
            LorebookStatisticsDto: 统计信息DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
        """
        # 检查传说书是否存在
        if not self._lorebook_repository.exists_by_id(lorebook_id):
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        stats = self._lorebook_repository.get_statistics(lorebook_id)
        
        return LorebookStatisticsDto(
            total_entries=stats.get('total_entries', 0),
            active_entries=stats.get('active_entries', 0),
            total_activations=stats.get('total_activations', 0),
            average_activations=stats.get('average_activations', 0.0),
            tags=stats.get('tags', []),
            version=stats.get('version', '1.0.0')
        )
    
    # 条目管理方法
    
    def create_entry(self, lorebook_id: str, create_dto: LorebookEntryCreateDto) -> LorebookEntryDto:
        """创建条目
        
        Args:
            lorebook_id: 传说书ID
            create_dto: 创建条目请求对象
            
        Returns:
            LorebookEntryDto: 创建的条目DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 检查传说书是否存在
        lorebook = self._lorebook_repository.find_by_id(lorebook_id)
        if not lorebook:
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 验证请求数据
        errors = create_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查标题是否已存在
        if self._entry_repository.entry_title_exists(lorebook_id, create_dto.title):
            raise BusinessRuleException(f"条目标题已存在: {create_dto.title}")
        
        # 转换关键词模式
        keywords = []
        for keyword_dto in create_dto.keywords:
            try:
                keyword_type = KeywordType(keyword_dto.type)
                keyword = KeywordPattern(
                    pattern=keyword_dto.pattern,
                    type=keyword_type,
                    case_sensitive=keyword_dto.case_sensitive,
                    weight=keyword_dto.weight
                )
                keywords.append(keyword)
            except ValueError:
                raise ValidationException(f"无效的关键词类型: {keyword_dto.type}")
        
        # 转换激活规则
        try:
            activation_type = ActivationType(create_dto.activation_rule.type)
            activation_rule = ActivationRule(
                type=activation_type,
                keywords=keywords,
                priority=create_dto.activation_rule.priority,
                max_activations=create_dto.activation_rule.max_activations,
                cooldown_seconds=create_dto.activation_rule.cooldown_seconds
            )
        except ValueError:
            raise ValidationException(f"无效的激活类型: {create_dto.activation_rule.type}")
        
        # 创建条目
        entry = LorebookEntry(
            title=create_dto.title,
            content=create_dto.content,
            keywords=keywords,
            activation_rule=activation_rule,
            tags=set(create_dto.tags),
            metadata=create_dto.metadata
        )
        
        # 添加到传说书
        lorebook.add_entry(entry)
        
        # 保存更新
        self._lorebook_repository.update(lorebook)
        
        self._logger.info(f"Created entry: {entry.title} in lorebook: {lorebook_id}")
        
        return LorebookEntryDto.from_domain(entry)
    
    def get_entry(self, lorebook_id: str, entry_id: str) -> LorebookEntryDto:
        """获取条目
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            LorebookEntryDto: 条目DTO
            
        Raises:
            NotFoundException: 条目不存在时抛出
        """
        entry = self._entry_repository.find_entry_by_id(lorebook_id, entry_id)
        if not entry:
            raise NotFoundException(f"条目不存在: {entry_id}")
        
        return LorebookEntryDto.from_domain(entry)
    
    def get_entries(self, lorebook_id: str, page: int = 1, page_size: int = 20) -> List[LorebookEntryDto]:
        """获取条目列表
        
        Args:
            lorebook_id: 传说书ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            List[LorebookEntryDto]: 条目列表
            
        Raises:
            NotFoundException: 传说书不存在时抛出
        """
        # 检查传说书是否存在
        if not self._lorebook_repository.exists_by_id(lorebook_id):
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 获取所有条目
        all_entries = self._entry_repository.find_entries_by_lorebook(lorebook_id)
        
        # 简单分页
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        entries_page = all_entries[start_index:end_index]
        
        # 转换为DTO
        return [LorebookEntryDto.from_domain(e) for e in entries_page]
    
    def update_entry(self, lorebook_id: str, entry_id: str, update_dto: LorebookEntryUpdateDto) -> LorebookEntryDto:
        """更新条目
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            update_dto: 更新条目请求对象
            
        Returns:
            LorebookEntryDto: 更新后的条目DTO
            
        Raises:
            NotFoundException: 条目不存在时抛出
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 获取条目
        entry = self._entry_repository.find_entry_by_id(lorebook_id, entry_id)
        if not entry:
            raise NotFoundException(f"条目不存在: {entry_id}")
        
        # 验证请求数据
        errors = update_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查标题是否已存在（如果要更新标题）
        if update_dto.title and update_dto.title != entry.title:
            if self._entry_repository.entry_title_exists(lorebook_id, update_dto.title):
                raise BusinessRuleException(f"条目标题已存在: {update_dto.title}")
        
        # 更新内容
        if update_dto.title is not None or update_dto.content is not None:
            new_title = update_dto.title if update_dto.title is not None else entry.title
            new_content = update_dto.content if update_dto.content is not None else entry.content
            entry.update_content(new_title, new_content)
        
        # 更新关键词
        if update_dto.keywords is not None:
            # 清除现有关键词
            entry.keywords.clear()
            
            # 添加新关键词
            for keyword_dto in update_dto.keywords:
                try:
                    keyword_type = KeywordType(keyword_dto.type)
                    keyword = KeywordPattern(
                        pattern=keyword_dto.pattern,
                        type=keyword_type,
                        case_sensitive=keyword_dto.case_sensitive,
                        weight=keyword_dto.weight
                    )
                    entry.add_keyword(keyword)
                except ValueError:
                    raise ValidationException(f"无效的关键词类型: {keyword_dto.type}")
        
        # 更新激活规则
        if update_dto.activation_rule is not None:
            try:
                activation_type = ActivationType(update_dto.activation_rule.type)
                activation_rule = ActivationRule(
                    type=activation_type,
                    keywords=entry.keywords,
                    priority=update_dto.activation_rule.priority,
                    max_activations=update_dto.activation_rule.max_activations,
                    cooldown_seconds=update_dto.activation_rule.cooldown_seconds
                )
                entry.activation_rule = activation_rule
            except ValueError:
                raise ValidationException(f"无效的激活类型: {update_dto.activation_rule.type}")
        
        # 更新其他属性
        if update_dto.tags is not None:
            entry.tags = set(update_dto.tags)
        
        if update_dto.metadata is not None:
            entry.metadata = update_dto.metadata
        
        if update_dto.is_active is not None:
            if update_dto.is_active and not entry.is_active:
                entry.reactivate()
            elif not update_dto.is_active and entry.is_active:
                entry.deactivate()
        
        # 保存更新
        self._entry_repository.update_entry(lorebook_id, entry)
        
        self._logger.info(f"Updated entry: {entry.title} in lorebook: {lorebook_id}")
        
        return LorebookEntryDto.from_domain(entry)
    
    def delete_entry(self, lorebook_id: str, entry_id: str) -> bool:
        """删除条目
        
        Args:
            lorebook_id: 传说书ID
            entry_id: 条目ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            NotFoundException: 条目不存在时抛出
        """
        # 检查条目是否存在
        if not self._entry_repository.entry_exists(lorebook_id, entry_id):
            raise NotFoundException(f"条目不存在: {entry_id}")
        
        # 删除条目
        success = self._entry_repository.delete_entry(lorebook_id, entry_id)
        
        if success:
            self._logger.info(f"Deleted entry: {entry_id} from lorebook: {lorebook_id}")
        
        return success
    
    def search_entries(self, lorebook_id: str, criteria: Dict[str, Any]) -> List[LorebookEntryDto]:
        """搜索条目
        
        Args:
            lorebook_id: 传说书ID
            criteria: 搜索条件
            
        Returns:
            List[LorebookEntryDto]: 匹配的条目列表
            
        Raises:
            NotFoundException: 传说书不存在时抛出
        """
        # 检查传说书是否存在
        if not self._lorebook_repository.exists_by_id(lorebook_id):
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        entries = self._entry_repository.search_entries(lorebook_id, criteria)
        return [LorebookEntryDto.from_domain(e) for e in entries]
    
    # 激活和匹配方法
    
    def activate_entries(self, lorebook_id: str, activation_dto: LorebookActivationDto) -> LorebookActivationResultDto:
        """激活条目
        
        Args:
            lorebook_id: 传说书ID
            activation_dto: 激活请求对象
            
        Returns:
            LorebookActivationResultDto: 激活结果DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
            ValidationException: 验证失败时抛出
        """
        # 验证请求数据
        errors = activation_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查传说书是否存在
        if not self._lorebook_repository.exists_by_id(lorebook_id):
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 激活条目
        activated_entries = self._entry_repository.activate_entries(
            lorebook_id, 
            activation_dto.text, 
            activation_dto.context
        )
        
        # 限制结果数量
        if activation_dto.max_entries is not None:
            activated_entries = activated_entries[:activation_dto.max_entries]
        
        # 获取候选总数
        all_entries = self._entry_repository.find_entries_by_lorebook(lorebook_id)
        total_candidates = len(all_entries)
        
        self._logger.info(f"Activated {len(activated_entries)} entries from lorebook: {lorebook_id}")
        
        return LorebookActivationResultDto(
            activated_entries=[LorebookEntryDto.from_domain(e) for e in activated_entries],
            total_candidates=total_candidates,
            activation_text=activation_dto.text,
            context=activation_dto.context
        )
    
    # 导入导出方法
    
    def export_lorebook(self, lorebook_id: str, format: str = "json") -> LorebookExportDto:
        """导出传说书
        
        Args:
            lorebook_id: 传说书ID
            format: 导出格式
            
        Returns:
            LorebookExportDto: 导出结果DTO
            
        Raises:
            NotFoundException: 传说书不存在时抛出
            ValidationException: 不支持的格式时抛出
        """
        if format not in ["json", "lorebook"]:
            raise ValidationException(f"不支持的导出格式: {format}")
        
        # 检查传说书是否存在
        lorebook = self._lorebook_repository.find_by_id(lorebook_id)
        if not lorebook:
            raise NotFoundException(f"传说书不存在: {lorebook_id}")
        
        # 导出数据
        data = self._lorebook_repository.export_lorebook(lorebook_id, format)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{lorebook.name}_{timestamp}.{format}"
        
        self._logger.info(f"Exported lorebook: {lorebook.name} as {format}")
        
        return LorebookExportDto(
            data=data,
            format=format,
            filename=filename
        )
    
    def import_lorebook(self, import_dto: LorebookImportDto) -> LorebookDto:
        """导入传说书
        
        Args:
            import_dto: 导入请求对象
            
        Returns:
            LorebookDto: 导入的传说书DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = import_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查名称是否已存在
        name = import_dto.data.get("name", "")
        if name and self._lorebook_repository.exists_by_name(name):
            raise BusinessRuleException(f"传说书名称已存在: {name}")
        
        # 导入传说书
        lorebook = self._lorebook_repository.import_lorebook(import_dto.data, import_dto.format)
        
        self._logger.info(f"Imported lorebook: {lorebook.name} from {import_dto.format}")
        
        return LorebookDto.from_domain(lorebook)
    
    # 统计和分析方法
    
    def get_most_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntryDto]:
        """获取最常激活的条目
        
        Args:
            lorebook_id: 传说书ID
            limit: 返回数量限制
            
        Returns:
            List[LorebookEntryDto]: 条目列表
        """
        entries = self._entry_repository.get_most_activated_entries(lorebook_id, limit)
        return [LorebookEntryDto.from_domain(e) for e in entries]
    
    def get_recently_activated_entries(self, lorebook_id: str, limit: int = 10) -> List[LorebookEntryDto]:
        """获取最近激活的条目
        
        Args:
            lorebook_id: 传说书ID
            limit: 返回数量限制
            
        Returns:
            List[LorebookEntryDto]: 条目列表
        """
        entries = self._entry_repository.get_recently_activated_entries(lorebook_id, limit)
        return [LorebookEntryDto.from_domain(e) for e in entries]
    def _execute_command_internal(self, command: Any) -> Any:
        raise NotImplementedError("LorebookService command execution is not implemented")

    def _execute_query_internal(self, query: Any) -> Any:
        raise NotImplementedError("LorebookService query execution is not implemented")
