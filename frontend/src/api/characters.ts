import apiClient from './http'
import type {
  ApiResponse,
  CharacterDto,
  CharacterListResponse
} from './types'
import { unwrapApiResponse, assertApiSuccess } from './utils'

export interface CharacterCreatePayload {
  name: string
  description?: string
  personality_summary?: string
  scenario?: string
  first_message?: string
  example_messages?: string[]
  tags?: string[]
  abilities?: Record<string, number>
  stats?: Record<string, number>
  hp?: number
  max_hp?: number
}

export type CharacterUpdatePayload = Partial<CharacterCreatePayload>

export interface CharacterQuery {
  page?: number
  pageSize?: number
  name?: string
  tag?: string
}

export async function fetchCharacters(query: CharacterQuery = {}) {
  const params = {
    page: query.page ?? 1,
    page_size: query.pageSize ?? 20,
    ...(query.name ? { name: query.name } : {}),
    ...(query.tag ? { tag: query.tag } : {}),
  }

  const response = await apiClient.get<ApiResponse<CharacterListResponse>>(
    '/characters',
    { params }
  )

  return unwrapApiResponse(response.data, '获取角色列表失败')
}

export async function fetchCharacter(id: string) {
  const response = await apiClient.get<ApiResponse<CharacterDto>>(
    '/characters/' + id
  )

  return unwrapApiResponse(response.data, '获取角色详情失败')
}

export async function createCharacter(payload: CharacterCreatePayload) {
  const response = await apiClient.post<ApiResponse<CharacterDto>>(
    '/characters',
    payload
  )

  return unwrapApiResponse(response.data, '创建角色失败')
}

export async function updateCharacter(id: string, payload: CharacterUpdatePayload) {
  const response = await apiClient.put<ApiResponse<CharacterDto>>(
    '/characters/' + id,
    payload
  )

  return unwrapApiResponse(response.data, '更新角色失败')
}

export async function deleteCharacter(id: string) {
  const response = await apiClient.delete<ApiResponse<{ message?: string } | undefined>>(
    '/characters/' + id
  )

  assertApiSuccess(response.data, '删除角色失败')
}
