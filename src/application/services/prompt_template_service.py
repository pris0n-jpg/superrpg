"""
提示模板管理服务

提供提示模板的创建、管理、导入/导出和预设模板库功能。
遵循SOLID原则，特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ...domain.models.prompt import (
    PromptTemplate, PromptSection, PromptSectionType
)
from ...domain.dtos.prompt_dtos import (
    PromptTemplateDto, PromptTemplateListDto, PromptTemplateCreateDto,
    PromptTemplateUpdateDto, PromptExportDto, PromptImportDto,
    PromptStatisticsDto, PromptFormat
)
from ...domain.repositories.prompt_repository import PromptRepository
from ...core.interfaces import EventBus, Logger
from ...core.exceptions import ValidationException, BusinessRuleException, NotFoundException
from .token_counter_service import TokenCounterService
from .base import ApplicationService


class PromptTemplateService(ApplicationService):
    """提示模板管理服务
    
    提供提示模板的创建、编辑、删除、搜索和导入导出功能。
    遵循单一职责原则，专门负责提示模板业务逻辑的管理。
    """
    
    def __init__(
        self,
        prompt_repository: PromptRepository,
        token_counter: TokenCounterService,
        event_bus: EventBus,
        logger: Logger
    ):
        """初始化提示模板服务
        
        Args:
            prompt_repository: 提示仓储
            token_counter: Token计数服务
            logger: 日志记录器
        """
        super().__init__(event_bus, logger)
        self._prompt_repository = prompt_repository
        self._token_counter = token_counter
        
        # 初始化预设模板库
        try:
            self._initialize_preset_templates()
        except Exception as exc:
            self._logger.warning(f"Failed to initialize preset templates: {exc}")

    
    # 模板管理方法
    
    def create_template(self, create_dto: PromptTemplateCreateDto) -> PromptTemplateDto:
        """创建提示模板
        
        Args:
            create_dto: 创建提示模板请求对象
            
        Returns:
            PromptTemplateDto: 创建的提示模板DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = create_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 检查名称是否已存在
        if self._prompt_repository.exists_by_name(create_dto.name):
            raise BusinessRuleException(f"模板名称已存在: {create_dto.name}")
        
        # 转换段落数据
        sections = []
        for section_data in create_dto.sections:
            try:
                section_type = PromptSectionType(section_data.get('section_type', 'custom'))
                section = PromptSection(
                    content=section_data['content'],
                    section_type=section_type,
                    priority=section_data.get('priority', 0),
                    token_count=0,  # 稍后计算
                    metadata=section_data.get('metadata', {})
                )
                sections.append(section)
            except ValueError:
                raise ValidationException(f"无效的段落类型: {section_data.get('section_type')}")
        
        # 创建模板
        template = PromptTemplate(
            name=create_dto.name,
            description=create_dto.description,
            sections=sections,
            metadata=create_dto.metadata,
            version=create_dto.version
        )
        
        # 计算段落token数量
        for i, section in enumerate(template.sections):
            # 创建一个可修改的段落副本
            token_count = self._token_counter.count_tokens_by_sections(
                [{'content': section.content, 'section_type': section.section_type.value}]
            ).get(section.section_type.value, 0)
            
            # 更新段落的token数量
            new_section = PromptSection(
                content=section.content,
                section_type=section.section_type,
                priority=section.priority,
                token_count=token_count,
                metadata=section.metadata
            )
            template.sections[i] = new_section
        
        # 保存模板
        self._prompt_repository.save(template)
        
        self._logger.info(f"Created prompt template: {template.name} (ID: {template.id})")
        
        return PromptTemplateDto.from_domain(template)
    
    def get_template(self, template_id: str) -> PromptTemplateDto:
        """获取提示模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            PromptTemplateDto: 提示模板DTO
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        return PromptTemplateDto.from_domain(template)
    
    def get_templates(self, page: int = 1, page_size: int = 20, 
                     is_active: Optional[bool] = None) -> PromptTemplateListDto:
        """获取提示模板列表
        
        Args:
            page: 页码
            page_size: 每页大小
            is_active: 是否只获取活跃模板
            
        Returns:
            PromptTemplateListDto: 提示模板列表DTO
        """
        # 获取所有模板
        all_templates = self._prompt_repository.find_all()
        
        # 过滤活跃状态
        if is_active is not None:
            all_templates = [t for t in all_templates if t.is_active == is_active]
        
        # 简单分页
        total_count = len(all_templates)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        templates_page = all_templates[start_index:end_index]
        
        # 转换为DTO
        template_dtos = [PromptTemplateDto.from_domain(t) for t in templates_page]
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PromptTemplateListDto(
            templates=template_dtos,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    def update_template(self, template_id: str, update_dto: PromptTemplateUpdateDto) -> PromptTemplateDto:
        """更新提示模板
        
        Args:
            template_id: 模板ID
            update_dto: 更新提示模板请求对象
            
        Returns:
            PromptTemplateDto: 更新后的提示模板DTO
            
        Raises:
            NotFoundException: 模板不存在时抛出
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = update_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        # 获取模板
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 检查名称是否已存在（如果要更新名称）
        if update_dto.name and update_dto.name != template.name:
            if self._prompt_repository.exists_by_name(update_dto.name):
                raise BusinessRuleException(f"模板名称已存在: {update_dto.name}")
        
        # 更新基本信息
        template.update_info(
            name=update_dto.name,
            description=update_dto.description
        )
        
        if update_dto.version is not None:
            template.version = update_dto.version
        
        if update_dto.metadata is not None:
            template.metadata = update_dto.metadata
        
        if update_dto.is_active is not None:
            if update_dto.is_active and not template.is_active:
                template.activate()
            elif not update_dto.is_active and template.is_active:
                template.deactivate()
        
        # 更新段落
        if update_dto.sections is not None:
            # 清除现有段落
            template.sections.clear()
            
            # 添加新段落
            for section_data in update_dto.sections:
                try:
                    section_type = PromptSectionType(section_data.get('section_type', 'custom'))
                    section = PromptSection(
                        content=section_data['content'],
                        section_type=section_type,
                        priority=section_data.get('priority', 0),
                        token_count=0,  # 稍后计算
                        metadata=section_data.get('metadata', {})
                    )
                    template.add_section(section)
                except ValueError:
                    raise ValidationException(f"无效的段落类型: {section_data.get('section_type')}")
            
            # 重新计算token数量
            for i, section in enumerate(template.sections):
                token_count = self._token_counter.count_tokens_by_sections(
                    [{'content': section.content, 'section_type': section.section_type.value}]
                ).get(section.section_type.value, 0)
                
                new_section = PromptSection(
                    content=section.content,
                    section_type=section.section_type,
                    priority=section.priority,
                    token_count=token_count,
                    metadata=section.metadata
                )
                template.sections[i] = new_section
        
        # 保存更新
        self._prompt_repository.update(template)
        
        self._logger.info(f"Updated prompt template: {template.name} (ID: {template.id})")
        
        return PromptTemplateDto.from_domain(template)
    
    def delete_template(self, template_id: str) -> bool:
        """删除提示模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        # 检查模板是否存在
        if not self._prompt_repository.exists_by_id(template_id):
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 删除模板
        success = self._prompt_repository.delete(template_id)
        
        if success:
            self._logger.info(f"Deleted prompt template: {template_id}")
        
        return success
    
    def search_templates(self, criteria: Dict[str, Any]) -> List[PromptTemplateDto]:
        """搜索提示模板
        
        Args:
            criteria: 搜索条件
            
        Returns:
            List[PromptTemplateDto]: 匹配的提示模板列表
        """
        templates = self._prompt_repository.search(criteria)
        return [PromptTemplateDto.from_domain(t) for t in templates]
    
    def get_template_statistics(self, template_id: str) -> PromptStatisticsDto:
        """获取提示模板统计信息
        
        Args:
            template_id: 模板ID
            
        Returns:
            PromptStatisticsDto: 统计信息DTO
            
        Raises:
            NotFoundException: 模板不存在时抛出
        """
        # 检查模板是否存在
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 计算统计信息
        total_sections = len(template.sections)
        total_tokens = sum(section.token_count for section in template.sections)
        
        # 按类型统计
        sections_by_type = {}
        tokens_by_type = {}
        
        for section in template.sections:
            section_type = section.section_type.value
            sections_by_type[section_type] = sections_by_type.get(section_type, 0) + 1
            tokens_by_type[section_type] = tokens_by_type.get(section_type, 0) + section.token_count
        
        # 计算平均token数
        average_section_tokens = total_tokens / total_sections if total_sections > 0 else 0
        
        # 找出最大的段落
        largest_section = {}
        if template.sections:
            max_section = max(template.sections, key=lambda s: s.token_count)
            largest_section = {
                'content_preview': max_section.content[:100] + "..." if len(max_section.content) > 100 else max_section.content,
                'section_type': max_section.section_type.value,
                'token_count': max_section.token_count
            }
        
        return PromptStatisticsDto(
            template_id=template_id,
            template_name=template.name,
            total_sections=total_sections,
            total_tokens=total_tokens,
            sections_by_type=sections_by_type,
            tokens_by_type=tokens_by_type,
            variable_count=len(template.variables),
            average_section_tokens=average_section_tokens,
            largest_section=largest_section,
            created_at=template.created_at
        )
    
    # 导入导出方法
    
    def export_template(self, template_id: str, format: PromptFormat = PromptFormat.JSON) -> PromptExportDto:
        """导出提示模板
        
        Args:
            template_id: 模板ID
            format: 导出格式
            
        Returns:
            PromptExportDto: 导出结果DTO
            
        Raises:
            NotFoundException: 模板不存在时抛出
            ValidationException: 不支持的格式时抛出
        """
        if format not in [PromptFormat.JSON, PromptFormat.TEXT]:
            raise ValidationException(f"不支持的导出格式: {format.value}")
        
        # 检查模板是否存在
        template = self._prompt_repository.find_by_id(template_id)
        if not template:
            raise NotFoundException(f"提示模板不存在: {template_id}")
        
        # 导出数据
        if format == PromptFormat.JSON:
            data = template.export_to_dict()
        else:  # TEXT
            data = {
                'name': template.name,
                'description': template.description,
                'content': self._template_to_text(template)
            }
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{template.name}_{timestamp}.{format.value}"
        
        self._logger.info(f"Exported prompt template: {template.name} as {format.value}")
        
        return PromptExportDto(
            data=data,
            format=format,
            filename=filename
        )
    
    def import_template(self, import_dto: PromptImportDto) -> PromptTemplateDto:
        """导入提示模板
        
        Args:
            import_dto: 导入请求对象
            
        Returns:
            PromptTemplateDto: 导入的提示模板DTO
            
        Raises:
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 验证请求数据
        errors = import_dto.validate()
        if errors:
            raise ValidationException(f"验证失败: {', '.join(errors)}")
        
        data = import_dto.data
        
        if import_dto.format == PromptFormat.JSON:
            # JSON格式导入
            template_data = data
        else:  # TEXT
            # 文本格式导入，创建一个简单的模板
            template_data = {
                'name': data.get('name', 'Imported Template'),
                'description': data.get('description', ''),
                'sections': [
                    {
                        'content': data.get('content', ''),
                        'section_type': 'custom',
                        'priority': 0
                    }
                ]
            }
        
        # 检查名称是否已存在
        name = template_data.get("name", "")
        if name and not import_dto.overwrite:
            if self._prompt_repository.exists_by_name(name):
                raise BusinessRuleException(f"模板名称已存在: {name}")
        
        # 转换为创建DTO
        create_dto = PromptTemplateCreateDto(
            name=template_data.get('name', ''),
            description=template_data.get('description', ''),
            sections=template_data.get('sections', []),
            metadata=template_data.get('metadata', {}),
            version=template_data.get('version', '1.0.0')
        )
        
        # 如果覆盖且模板存在，先删除
        if import_dto.overwrite and name:
            existing_template = self._prompt_repository.find_by_name(name)
            if existing_template:
                self._prompt_repository.delete(str(existing_template.id))
        
        # 创建模板
        return self.create_template(create_dto)
    
    # 预设模板方法
    
    def get_preset_templates(self) -> List[PromptTemplateDto]:
        """获取预设模板列表
        
        Returns:
            List[PromptTemplateDto]: 预设模板列表
        """
        preset_templates = self._prompt_repository.find_by_tag("preset")
        return [PromptTemplateDto.from_domain(t) for t in preset_templates]
    
    def create_from_preset(self, preset_name: str, template_name: str, 
                          customizations: Dict[str, Any] = None) -> PromptTemplateDto:
        """从预设模板创建新模板
        
        Args:
            preset_name: 预设模板名称
            template_name: 新模板名称
            customizations: 自定义设置
            
        Returns:
            PromptTemplateDto: 创建的模板DTO
            
        Raises:
            NotFoundException: 预设模板不存在时抛出
            ValidationException: 验证失败时抛出
            BusinessRuleException: 业务规则违反时抛出
        """
        # 查找预设模板
        preset_templates = self._prompt_repository.find_by_tag("preset")
        preset_template = None
        
        for template in preset_templates:
            if template.name == preset_name:
                preset_template = template
                break
        
        if not preset_template:
            raise NotFoundException(f"预设模板不存在: {preset_name}")
        
        # 检查新名称是否已存在
        if self._prompt_repository.exists_by_name(template_name):
            raise BusinessRuleException(f"模板名称已存在: {template_name}")
        
        # 创建新模板
        new_template = PromptTemplate(
            name=template_name,
            description=preset_template.description,
            sections=[PromptSection(
                content=section.content,
                section_type=section.section_type,
                priority=section.priority,
                token_count=section.token_count,
                metadata=section.metadata.copy()
            ) for section in preset_template.sections],
            metadata=preset_template.metadata.copy(),
            version="1.0.0"
        )
        
        # 应用自定义设置
        if customizations:
            if 'description' in customizations:
                new_template.description = customizations['description']
            
            if 'sections' in customizations:
                # 更新段落内容
                for section_update in customizations['sections']:
                    section_type = section_update.get('section_type')
                    new_content = section_update.get('content')
                    
                    if section_type and new_content:
                        for i, section in enumerate(new_template.sections):
                            if section.section_type.value == section_type:
                                new_section = PromptSection(
                                    content=new_content,
                                    section_type=section.section_type,
                                    priority=section_update.get('priority', section.priority),
                                    token_count=section.token_count,  # 稍后重新计算
                                    metadata=section_update.get('metadata', section.metadata.copy())
                                )
                                new_template.sections[i] = new_section
                                break
            
            if 'metadata' in customizations:
                new_template.metadata.update(customizations['metadata'])
        
        # 重新计算token数量
        for i, section in enumerate(new_template.sections):
            token_count = self._token_counter.count_tokens_by_sections(
                [{'content': section.content, 'section_type': section.section_type.value}]
            ).get(section.section_type.value, 0)
            
            new_section = PromptSection(
                content=section.content,
                section_type=section.section_type,
                priority=section.priority,
                token_count=token_count,
                metadata=section.metadata
            )
            new_template.sections[i] = new_section
        
        # 保存模板
        self._prompt_repository.save(new_template)
        
        self._logger.info(f"Created template from preset: {template_name} (from {preset_name})")
        
        return PromptTemplateDto.from_domain(new_template)
    
    # 辅助方法
    
    def _template_to_text(self, template: PromptTemplate) -> str:
        """将模板转换为文本格式
        
        Args:
            template: 提示模板
            
        Returns:
            str: 文本格式的模板
        """
        lines = [
            f"# {template.name}",
            f"## 描述",
            template.description,
            f"## 版本",
            template.version,
            f"## 段落"
        ]
        
        for i, section in enumerate(template.sections, 1):
            lines.extend([
                f"### 段落 {i} ({section.section_type.value})",
                f"优先级: {section.priority}",
                f"Token数: {section.token_count}",
                f"内容:",
                section.content,
                ""
            ])
        
        return "\n".join(lines)
    
    def _initialize_preset_templates(self) -> None:
        """初始化预设模板库"""
        try:
            existing_templates = {template.name for template in self._prompt_repository.find_all()}
        except Exception:
            existing_templates = set()

        preset_templates = [
            self._create_basic_rpg_template(),
            self._create_chatbot_template(),
            self._create_storytelling_template(),
            self._create_code_assistant_template()
        ]

        created_count = 0
        for template in preset_templates:
            if template.name in existing_templates:
                continue
            self._prompt_repository.save(template)
            existing_templates.add(template.name)
            created_count += 1

        if created_count:
            self._logger.info(f"Initialized {created_count} preset templates")
    
    def _create_basic_rpg_template(self) -> PromptTemplate:
        """创建基础RPG预设模板"""
        sections = [
            PromptSection(
                content="你是一个专业的RPG游戏主持人，负责引导玩家进行角色扮演游戏。请根据以下信息进行游戏。",
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
            ),
            PromptSection(
                content="游戏规则：\n1. 保持角色扮演的一致性\n2. 根据玩家的行动做出合理的反应\n3. 推动故事情节发展\n4. 提供有趣的挑战和选择",
                section_type=PromptSectionType.INSTRUCTION,
                priority=70
            ),
            PromptSection(
                content="历史对话：\n{chat_history}",
                section_type=PromptSectionType.HISTORY,
                priority=60
            ),
            PromptSection(
                content="当前情况：\n{current_input}",
                section_type=PromptSectionType.CONTEXT,
                priority=50
            )
        ]
        
        return PromptTemplate(
            name="基础RPG模板",
            description="适用于各种RPG游戏的基础模板，包含角色、世界和游戏规则",
            sections=sections,
            metadata={"category": "rpg", "difficulty": "basic", "tags": ["preset"]},
            version="1.0.0"
        )
    
    def _create_chatbot_template(self) -> PromptTemplate:
        """创建聊天机器人预设模板"""
        sections = [
            PromptSection(
                content="你是一个友好的AI助手，请以专业、有帮助的方式回答用户的问题。",
                section_type=PromptSectionType.SYSTEM,
                priority=100
            ),
            PromptSection(
                content="角色设定：\n{character_description}",
                section_type=PromptSectionType.ROLE,
                priority=90
            ),
            PromptSection(
                content="回答指南：\n1. 提供准确、有用的信息\n2. 保持友好、专业的语气\n3. 如果不确定，请诚实地说明\n4. 尽量提供具体的解决方案",
                section_type=PromptSectionType.INSTRUCTION,
                priority=80
            ),
            PromptSection(
                content="对话历史：\n{chat_history}",
                section_type=PromptSectionType.HISTORY,
                priority=70
            ),
            PromptSection(
                content="用户问题：\n{current_input}",
                section_type=PromptSectionType.CONTEXT,
                priority=60
            )
        ]
        
        return PromptTemplate(
            name="聊天机器人模板",
            description="适用于通用聊天机器人场景的模板",
            sections=sections,
            metadata={"category": "chatbot", "difficulty": "basic", "tags": ["preset"]},
            version="1.0.0"
        )
    
    def _create_storytelling_template(self) -> PromptTemplate:
        """创建故事叙述预设模板"""
        sections = [
            PromptSection(
                content="你是一个专业的故事叙述者，擅长创造引人入胜的故事情节和生动的角色。",
                section_type=PromptSectionType.SYSTEM,
                priority=100
            ),
            PromptSection(
                content="故事背景：\n{world_info}",
                section_type=PromptSectionType.WORLD,
                priority=90
            ),
            PromptSection(
                content="主要角色：\n{character_description}",
                section_type=PromptSectionType.ROLE,
                priority=80
            ),
            PromptSection(
                content="叙事风格：\n1. 使用生动的描述\n2. 保持故事的连贯性\n3. 适当制造悬念\n4. 给读者留下想象空间",
                section_type=PromptSectionType.INSTRUCTION,
                priority=70
            ),
            PromptSection(
                content="故事进展：\n{chat_history}",
                section_type=PromptSectionType.HISTORY,
                priority=60
            ),
            PromptSection(
                content="当前情节：\n{current_input}",
                section_type=PromptSectionType.CONTEXT,
                priority=50
            )
        ]
        
        return PromptTemplate(
            name="故事叙述模板",
            description="适用于创意写作和故事叙述的模板",
            sections=sections,
            metadata={"category": "storytelling", "difficulty": "intermediate", "tags": ["preset"]},
            version="1.0.0"
        )
    
    def _create_code_assistant_template(self) -> PromptTemplate:
        """创建代码助手预设模板"""
        sections = [
            PromptSection(
                content="你是一个专业的编程助手，精通多种编程语言和开发框架。",
                section_type=PromptSectionType.SYSTEM,
                priority=100
            ),
            PromptSection(
                content="专业领域：\n{character_description}",
                section_type=PromptSectionType.ROLE,
                priority=90
            ),
            PromptSection(
                content="代码规范：\n1. 提供清晰、可维护的代码\n2. 添加必要的注释\n3. 遵循最佳实践\n4. 考虑性能和安全性",
                section_type=PromptSectionType.INSTRUCTION,
                priority=80
            ),
            PromptSection(
                content="代码示例：\n{example_code}",
                section_type=PromptSectionType.EXAMPLE,
                priority=70
            ),
            PromptSection(
                content="开发历史：\n{chat_history}",
                section_type=PromptSectionType.HISTORY,
                priority=60
            ),
            PromptSection(
                content="当前需求：\n{current_input}",
                section_type=PromptSectionType.CONTEXT,
                priority=50
            )
        ]
        
        return PromptTemplate(
            name="代码助手模板",
            description="适用于编程辅助和代码生成的模板",
            sections=sections,
            metadata={"category": "programming", "difficulty": "intermediate"},
            version="1.0.0"
        )
    def _execute_command_internal(self, command: Any) -> Any:
        raise NotImplementedError("PromptTemplateService command execution is not implemented")

    def _execute_query_internal(self, query: Any) -> Any:
        raise NotImplementedError("PromptTemplateService query execution is not implemented")
