"""
数据传输对象(DTOs)模块

该模块定义了系统中使用的数据传输对象，遵循SOLID原则，
特别是单一职责原则(SRP)，每个DTO都有明确的职责。
"""

from .character_card_dtos import (
    CharacterCardDto,
    CharacterCardListDto,
    CharacterCardCreateDto,
    CharacterCardUpdateDto,
    CharacterCardImportDto,
    CharacterCardExportDto
)

from .lorebook_dtos import (
    LorebookDto,
    LorebookListDto,
    LorebookCreateDto,
    LorebookUpdateDto,
    LorebookEntryDto,
    LorebookEntryCreateDto,
    LorebookEntryUpdateDto,
    LorebookImportDto,
    LorebookExportDto,
    LorebookActivationDto,
    LorebookActivationResultDto,
    LorebookStatisticsDto,
    KeywordPatternDto,
    ActivationRuleDto
)

from .prompt_dtos import (
    PromptTemplateDto,
    PromptTemplateListDto,
    PromptSectionDto,
    PromptContextDto,
    PromptBuildDto,
    PromptPreviewDto,
    PromptStatisticsDto,
    PromptTemplateCreateDto,
    PromptTemplateUpdateDto,
    PromptTokenCountDto,
    PromptTokenCountResponseDto,
    PromptExportDto,
    PromptImportDto
)

__all__ = [
    # Character card DTOs
    "CharacterCardDto",
    "CharacterCardListDto",
    "CharacterCardCreateDto",
    "CharacterCardUpdateDto",
    "CharacterCardImportDto",
    "CharacterCardExportDto",
    
    # Lorebook DTOs
    "LorebookDto",
    "LorebookListDto",
    "LorebookCreateDto",
    "LorebookUpdateDto",
    "LorebookEntryDto",
    "LorebookEntryCreateDto",
    "LorebookEntryUpdateDto",
    "LorebookImportDto",
    "LorebookExportDto",
    "LorebookActivationDto",
    "LorebookActivationResultDto",
    "LorebookStatisticsDto",
    "KeywordPatternDto",
    "ActivationRuleDto",
    
    # Prompt DTOs
    "PromptTemplateDto",
    "PromptTemplateListDto",
    "PromptSectionDto",
    "PromptContextDto",
    "PromptBuildDto",
    "PromptPreviewDto",
    "PromptStatisticsDto",
    "PromptTemplateCreateDto",
    "PromptTemplateUpdateDto",
    "PromptTokenCountDto",
    "PromptTokenCountResponseDto",
    "PromptExportDto",
    "PromptImportDto"
]