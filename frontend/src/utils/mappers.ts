import type { CharacterCard } from '@/types'
import type {
  CharacterDto,
  PromptTemplateDto,
  PromptTemplateCreatePayload,
  PromptTemplateUpdatePayload,
  PromptSectionInput,
} from '@/api/types'

export const mapCharacterDtoToCard = (dto: CharacterDto): CharacterCard => {
  const createdAt = dto.created_at ?? new Date().toISOString()
  const updatedAt = dto.updated_at ?? createdAt

  return {
    id: dto.id,
    name: dto.name,
    description: dto.description,
    personality: dto.personality_summary || '',
    background: dto.scenario || '',
    avatar: '',
    traits: [],
    relationships: [],
    metadata: {
      age: dto.stats?.level,
      gender: '',
      occupation: dto.stats?.level ? '等级 ' + dto.stats.level : '',
      location: '',
      customFields: {
        firstMessage: dto.first_message,
        exampleMessages: dto.example_messages
      }
    },
    tags: dto.tags ?? [],
    isPublic: true,
    isTemplate: false,
    createdAt,
    updatedAt
  }
}

export const mapCardToCreatePayload = (card: Partial<CharacterCard>) => ({
  name: card.name?.trim() || '',
  description: card.description || '',
  personality_summary: card.personality || '',
  scenario: card.background || '',
  first_message:
    (card.metadata?.customFields?.firstMessage as string | undefined) || '',
  example_messages:
    (card.metadata?.customFields?.exampleMessages as string[] | undefined) || [],
  tags: card.tags || [],
  abilities: {
    strength: 10,
    dexterity: 10,
    constitution: 10,
    intelligence: 10,
    wisdom: 10,
    charisma: 10
  },
  stats: {
    level: card.metadata?.age || 1,
    armor_class: 10,
    proficiency_bonus: 2,
    speed_steps: 6,
    reach_steps: 1
  },
  hp: 100,
  max_hp: 100
})

export const mapCardToUpdatePayload = (card: Partial<CharacterCard>) => ({
  description: card.description,
  personality_summary: card.personality,
  scenario: card.background,
  tags: card.tags,
  first_message:
    (card.metadata?.customFields?.firstMessage as string | undefined) || '',
  example_messages:
    (card.metadata?.customFields?.exampleMessages as string[] | undefined) || []
})

const createSectionId = () =>
  `section-${Math.random().toString(36).slice(2, 8)}-${Date.now()}`

export interface PromptSectionForm {
  id: string
  content: string
  sectionType: string
  priority: number
  metadata: Record<string, any>
}

export interface PromptTemplateFormState {
  name: string
  description: string
  version: string
  isActive: boolean
  metadata: Record<string, any>
  sections: PromptSectionForm[]
}

export const createEmptyPromptSection = (
  overrides: Partial<PromptSectionForm> = {}
): PromptSectionForm => ({
  id: createSectionId(),
  content: '',
  sectionType: 'custom',
  priority: 0,
  metadata: {},
  ...overrides,
})

export const createEmptyPromptTemplateForm = (): PromptTemplateFormState => ({
  name: '',
  description: '',
  version: '1.0.0',
  isActive: true,
  metadata: {},
  sections: [createEmptyPromptSection()],
})

const toSectionInput = (section: PromptSectionForm): PromptSectionInput => ({
  content: section.content,
  section_type: section.sectionType,
  priority: section.priority,
  metadata: section.metadata,
})

export const mapPromptTemplateDtoToForm = (
  dto: PromptTemplateDto
): PromptTemplateFormState => ({
  name: dto.name,
  description: dto.description,
  version: dto.version,
  isActive: dto.is_active,
  metadata: dto.metadata || {},
  sections: (dto.sections || [])
    .slice()
    .sort((a, b) => a.priority - b.priority)
    .map((section) =>
      createEmptyPromptSection({
        id: createSectionId(),
        content: section.content,
        sectionType: section.section_type,
        priority: section.priority,
        metadata: section.metadata || {},
      })
    ),
})

export const mapPromptFormToCreatePayload = (
  form: PromptTemplateFormState
): PromptTemplateCreatePayload => ({
  name: form.name.trim(),
  description: form.description,
  version: form.version,
  metadata: form.metadata,
  sections: form.sections.map(toSectionInput),
})

export const mapPromptFormToUpdatePayload = (
  form: PromptTemplateFormState
): PromptTemplateUpdatePayload => ({
  name: form.name.trim(),
  description: form.description,
  version: form.version,
  metadata: form.metadata,
  sections: form.sections.map(toSectionInput),
  is_active: form.isActive,
})
