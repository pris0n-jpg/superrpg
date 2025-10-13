import type { ApiResponse } from './types'

const DEFAULT_ERROR_MESSAGE = '请求失败，请稍后重试'

export function unwrapApiResponse<T>(response: ApiResponse<T>, errorMessage = DEFAULT_ERROR_MESSAGE): T {
  if (!response.success) {
    throw new Error(response.message || response.error || errorMessage)
  }

  if (response.data === undefined || response.data === null) {
    throw new Error(response.message || errorMessage)
  }

  return response.data
}

export function assertApiSuccess(response: ApiResponse<unknown>, errorMessage = DEFAULT_ERROR_MESSAGE): void {
  if (!response.success) {
    throw new Error(response.message || response.error || errorMessage)
  }
}
