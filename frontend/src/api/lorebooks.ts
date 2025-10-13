import apiClient from './http'
import type { ApiResponse, LorebookDto, LorebookListResponse, LorebookCreatePayload, LorebookUpdatePayload } from './types'
import { unwrapApiResponse } from './utils'

export async function fetchLorebooks(page = 1, pageSize = 20) {
  const response = await apiClient.get<ApiResponse<LorebookListResponse>>(
    '/lorebooks',
    { params: { page, page_size: pageSize } }
  )

  return unwrapApiResponse(response.data, '获取传说书列表失败')
}

export async function fetchLorebook(id: string) {
  const response = await apiClient.get<ApiResponse<LorebookDto>>(
    '/lorebooks/' + id
  )

  return unwrapApiResponse(response.data, '获取传说书失败')
}

export async function createLorebook(payload: LorebookCreatePayload) {
  const response = await apiClient.post<ApiResponse<LorebookDto>>(
    '/lorebooks',
    payload
  )

  return unwrapApiResponse(response.data, '创建传说书失败')
}

export async function updateLorebook(id: string, payload: LorebookUpdatePayload) {
  const response = await apiClient.put<ApiResponse<LorebookDto>>(
    '/lorebooks/' + id,
    payload
  )

  return unwrapApiResponse(response.data, '更新传说书失败')
}
