import apiClient from './http'
import type { ApiResponse } from './types'
import { unwrapApiResponse } from './utils'

interface SystemSummary {
  characters: number
  lorebooks: number
  prompts: number
}

export async function fetchSystemSummary() {
  const response = await apiClient.get<ApiResponse<SystemSummary>>('/system/summary')

  return unwrapApiResponse(response.data, '获取系统统计失败')
}
