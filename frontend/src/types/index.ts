// 基础类型定义
export interface BaseEntity {
  id: string
  createdAt: string
  updatedAt: string
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  errors?: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 用户相关类型
export interface User extends BaseEntity {
  username: string
  email: string
  avatar?: string
  preferences: UserPreferences
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto'
  language: string
  notifications: NotificationSettings
}

export interface NotificationSettings {
  email: boolean
  push: boolean
  sound: boolean
}

// 角色卡相关类型
export interface CharacterCard extends BaseEntity {
  name: string
  description: string
  avatar?: string
  personality: string
  background: string
  traits: CharacterTrait[]
  relationships: CharacterRelationship[]
  metadata: CharacterMetadata
  tags: string[]
  isPublic: boolean
  isTemplate: boolean
}

export interface CharacterTrait {
  id: string
  name: string
  value: string
  type: 'string' | 'number' | 'boolean' | 'enum'
  category: string
}

export interface CharacterRelationship {
  id: string
  characterId: string
  type: 'friend' | 'enemy' | 'family' | 'romantic' | 'ally' | 'rival'
  description: string
  strength: number // 1-10
}

export interface CharacterMetadata {
  age?: number
  gender?: string
  occupation?: string
  location?: string
  customFields: Record<string, any>
}

// 传说书相关类型
export interface Lorebook extends BaseEntity {
  name: string
  description: string
  entries: LorebookEntry[]
  isActive: boolean
  isPublic: boolean
  tags: string[]
  settings: LorebookSettings
}

export interface LorebookEntry extends BaseEntity {
  title: string
  content: string
  keywords: string[]
  priority: number
  isEnabled: boolean
  context: LorebookContext
  metadata: LorebookEntryMetadata
}

export interface LorebookContext {
  position: 'before' | 'after' | 'insert'
  depth: number
  recursive: boolean
}

export interface LorebookEntryMetadata {
  author?: string
  source?: string
  category?: string
  customFields: Record<string, any>
}

export interface LorebookSettings {
  maxTokens: number
  maxDepth: number
  caseSensitive: boolean
  wholeWord: boolean
  recursiveSearch: boolean
}

// 提示相关类型
export interface PromptTemplate extends BaseEntity {
  name: string
  description: string
  content: string
  variables: PromptVariable[]
  category: string
  tags: string[]
  isPublic: boolean
  isSystem: boolean
  metadata: PromptMetadata
}

export interface PromptVariable {
  name: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'textarea'
  description: string
  required: boolean
  defaultValue?: any
  options?: string[] // for select type
  validation?: VariableValidation
}

export interface VariableValidation {
  min?: number
  max?: number
  pattern?: string
  message?: string
}

export interface PromptMetadata {
  version: string
  author?: string
  usageCount: number
  rating: number
  estimatedTokens: number
  customFields: Record<string, any>
}

// 聊天相关类型
export interface ChatSession extends BaseEntity {
  title: string
  characterId: string
  messages: ChatMessage[]
  settings: ChatSettings
  metadata: ChatMetadata
}

export interface ChatMessage extends BaseEntity {
  sessionId: string
  role: 'user' | 'assistant' | 'system'
  content: string
  tokens: number
  metadata: MessageMetadata
}

export interface MessageMetadata {
  model?: string
  temperature?: number
  promptTemplate?: string
  lorebookEntries?: string[]
  customFields: Record<string, any>
}

export interface ChatSettings {
  model: string
  temperature: number
  maxTokens: number
  systemPrompt?: string
  promptTemplate?: string
  lorebookIds: string[]
  streamResponse: boolean
}

export interface ChatMetadata {
  totalMessages: number
  totalTokens: number
  lastActivity: string
  isActive: boolean
}

// 扩展相关类型
export interface Extension {
  id: string
  name: string
  description: string
  version: string
  author: string
  isEnabled: boolean
  permissions: ExtensionPermission[]
  settings: ExtensionSettings
  metadata: ExtensionMetadata
}

export interface ExtensionPermission {
  type: 'api' | 'storage' | 'network' | 'system'
  scope: string
  description: string
}

export interface ExtensionSettings {
  [key: string]: any
}

export interface ExtensionMetadata {
  homepage?: string
  repository?: string
  license?: string
  keywords: string[]
  dependencies: string[]
}

// 系统相关类型
export interface SystemConfig {
  api: ApiConfig
  features: FeatureFlags
  security: SecurityConfig
  performance: PerformanceConfig
}

export interface ApiConfig {
  baseUrl: string
  timeout: number
  retryAttempts: number
  rateLimit: RateLimitConfig
}

export interface RateLimitConfig {
  requestsPerMinute: number
  requestsPerHour: number
  burstLimit: number
}

export interface FeatureFlags {
  enablePWA: boolean
  enableAnalytics: boolean
  enableErrorReporting: boolean
  enableBetaFeatures: boolean
}

export interface SecurityConfig {
  enableEncryption: boolean
  sessionTimeout: number
  maxLoginAttempts: number
  requireTwoFactor: boolean
}

export interface PerformanceConfig {
  enableCaching: boolean
  cacheTimeout: number
  enableCompression: boolean
  enableLazyLoading: boolean
}

// 搜索相关类型
export interface SearchQuery {
  q: string
  type?: 'characters' | 'lorebooks' | 'prompts' | 'all'
  filters?: SearchFilters
  sort?: SearchSort
  page?: number
  pageSize?: number
}

export interface SearchFilters {
  tags?: string[]
  category?: string
  isPublic?: boolean
  dateRange?: {
    start: string
    end: string
  }
}

export interface SearchSort {
  field: 'name' | 'createdAt' | 'updatedAt' | 'rating' | 'usage'
  order: 'asc' | 'desc'
}

export interface SearchResult<T> {
  items: T[]
  total: number
  suggestions?: string[]
}

// 统计相关类型
export interface UsageStats {
  totalSessions: number
  totalMessages: number
  totalTokens: number
  averageSessionLength: number
  popularCharacters: CharacterStats[]
  popularPrompts: PromptStats[]
}

export interface CharacterStats {
  characterId: string
  name: string
  usageCount: number
  lastUsed: string
}

export interface PromptStats {
  promptId: string
  name: string
  usageCount: number
  averageRating: number
}

// 表单相关类型
export interface FormField {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'checkbox' | 'radio' | 'number' | 'file'
  required: boolean
  placeholder?: string
  options?: FormOption[]
  validation?: FieldValidation
  defaultValue?: any
}

export interface FormOption {
  value: string
  label: string
  disabled?: boolean
}

export interface FieldValidation {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: string
  min?: number
  max?: number
  custom?: (value: any) => string | null
}

// 通知相关类型
export interface Notification {
  id: string
  type: 'info' | 'success' | 'warning' | 'error'
  title: string
  message: string
  timestamp: string
  isRead: boolean
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  action: string
  style?: 'primary' | 'secondary' | 'danger'
}

// 主题相关类型
export interface Theme {
  id: string
  name: string
  colors: ThemeColors
  typography: ThemeTypography
  spacing: ThemeSpacing
}

export interface ThemeColors {
  primary: ColorPalette
  secondary: ColorPalette
  success: ColorPalette
  warning: ColorPalette
  error: ColorPalette
  background: BackgroundColors
  text: TextColors
}

export interface ColorPalette {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
  950: string
}

export interface BackgroundColors {
  primary: string
  secondary: string
  tertiary: string
}

export interface TextColors {
  primary: string
  secondary: string
  tertiary: string
  inverse: string
}

export interface ThemeTypography {
  fontFamily: {
    sans: string[]
    serif: string[]
    mono: string[]
  }
  fontSize: Record<string, [string, string]>
  fontWeight: Record<string, number>
}

export interface ThemeSpacing {
  scale: number
  sizes: Record<string, string>
}

// 键盘快捷键类型
export interface KeyboardShortcut {
  key: string
  modifiers: ('ctrl' | 'alt' | 'shift' | 'meta')[]
  action: string
  description: string
  global: boolean
}

// 导出/导入类型
export interface ExportOptions {
  format: 'json' | 'csv' | 'xml'
  includeData: {
    characters: boolean
    lorebooks: boolean
    prompts: boolean
    chats: boolean
    settings: boolean
  }
  compression: boolean
  encryption: boolean
}

export interface ImportResult {
  success: boolean
  imported: {
    characters: number
    lorebooks: number
    prompts: number
    chats: number
  }
  errors: string[]
  warnings: string[]
}

// 错误类型
export interface AppError {
  code: string
  message: string
  details?: any
  timestamp: string
  stack?: string
}

// 路由相关类型
export interface RouteConfig {
  path: string
  component: string // 组件名称或路径
  exact?: boolean
  guard?: RouteGuard
  meta?: RouteMeta
}

export interface RouteGuard {
  requiresAuth: boolean
  roles?: string[]
  permissions?: string[]
}

export interface RouteMeta {
  title: string
  description?: string
  icon?: string
  breadcrumbs?: BreadcrumbItem[]
  layout?: string
}

export interface BreadcrumbItem {
  label: string
  path?: string
}

// 事件类型
export interface AppEvent {
  type: string
  payload: any
  timestamp: string
  source: string
}

// WebSocket相关类型
export interface WebSocketMessage {
  type: string
  data: any
  id?: string
  timestamp?: string
}

export interface ChatStreamEvent {
  type: 'start' | 'chunk' | 'end' | 'error'
  data: {
    content?: string
    tokens?: number
    error?: string
  }
  messageId: string
  sessionId: string
}