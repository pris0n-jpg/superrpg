import apiClient from './http'
import type {
  ApiResponse,
  PromptTemplateDto,
  PromptTemplateListResponse,
  PromptTemplateCreatePayload,
  PromptTemplateUpdatePayload
} from './types'
import { unwrapApiResponse, assertApiSuccess } from './utils'

export async function fetchPromptTemplates(page = 1, pageSize = 20) {
  const response = await apiClient.get<ApiResponse<PromptTemplateListResponse>>(
    '/prompts/templates',
    { params: { page, page_size: pageSize } }
  )

  return unwrapApiResponse(response.data, '获取提示模板列表失败')
}

export async function fetchPromptTemplate(id: string) {
  const response = await apiClient.get<ApiResponse<PromptTemplateDto>>(
    '/prompts/templates/' + id
  )

  return unwrapApiResponse(response.data, '获取提示模板失败')
}

export async function createPromptTemplate(payload: PromptTemplateCreatePayload) {
  const response = await apiClient.post<ApiResponse<PromptTemplateDto>>(
    '/prompts/templates',
    payload
  )

  return unwrapApiResponse(response.data, '创建提示模板失败')
}

export async function updatePromptTemplate(id: string, payload: PromptTemplateUpdatePayload) {
  const response = await apiClient.put<ApiResponse<PromptTemplateDto>>(
    '/prompts/templates/' + id,
    payload
  )

  return unwrapApiResponse(response.data, '更新提示模板失败')
}

export async function deletePromptTemplate(id: string) {
  const response = await apiClient.delete<ApiResponse<{ message?: string } | undefined>>(
    '/prompts/templates/' + id
  )

  assertApiSuccess(response.data, '删除提示模板失败')
}
