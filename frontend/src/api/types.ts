export interface CharacterDto {
  id: string
  name: string
  description: string
  first_message: string
  example_messages: string[]
  scenario: string
  personality_summary: string
  creator_notes: string
  tags: string[]
  abilities: Record<string, number>
  stats: Record<string, number>
  hp: number
  max_hp: number
  position: { x: number; y: number } | null
  proficient_skills: string[]
  proficient_saves: string[]
  conditions: string[]
  inventory: Record<string, number>
  png_metadata?: Record<string, string> | null
  created_at?: string
  updated_at?: string
}

export interface CharacterListResponse {
  characters: CharacterDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface LorebookDto {
  id: string
  name: string
  description: string
  version: string
  tags: string[]
  metadata: Record<string, any>
  entries?: Array<Record<string, any>>
  created_at?: string
  updated_at?: string
}

export interface LorebookListResponse {
  lorebooks: LorebookDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface LorebookCreatePayload {
  name: string
  description?: string
  tags?: string[]
  metadata?: Record<string, any>
}

export type LorebookUpdatePayload = Partial<LorebookCreatePayload>

export interface PromptTemplateDto {
  id: string
  name: string
  description: string
  version: string
  is_active: boolean
  variables: string[]
  sections: Array<{
    content: string
    section_type: string
    priority: number
    token_count: number
    metadata: Record<string, any>
  }>
  metadata: Record<string, any>
  usage_stats?: Record<string, any>
  created_at?: string
  updated_at?: string
}

export interface PromptTemplateListResponse {
  templates: PromptTemplateDto[]
  total_count: number
  page: number
  page_size: number
  total_pages: number
}

export interface PromptSectionInput {
  content: string
  section_type: string
  priority: number
  metadata?: Record<string, any>
}

export interface PromptTemplateCreatePayload {
  name: string
  description?: string
  sections: PromptSectionInput[]
  metadata?: Record<string, any>
  version?: string
}

export interface PromptTemplateUpdatePayload {
  name?: string
  description?: string
  sections?: PromptSectionInput[]
  metadata?: Record<string, any>
  version?: string
  is_active?: boolean
}

export interface ApiSuccessResponse<T> {
  success: true
  data?: T
  message?: string
  timestamp?: string
}

export interface ApiErrorResponse {
  success: false
  error: string
  message?: string
  timestamp?: string
}

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse
