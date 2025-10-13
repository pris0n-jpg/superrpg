import axios, { AxiosHeaders } from 'axios'

import { useAuthStore } from '@/store/auth'

const resolveBaseURL = () => {
  const baseUrlEnv =
    import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL
  if (!baseUrlEnv) {
    return '/api'
  }
  return baseUrlEnv.endsWith('/') ? baseUrlEnv.slice(0, -1) : baseUrlEnv
}

const apiClient = axios.create({
  baseURL: resolveBaseURL(),
  timeout: Number(import.meta.env.VITE_API_TIMEOUT ?? 30000),
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    if (!config.headers) {
      config.headers = new AxiosHeaders()
    }

    if (config.headers instanceof AxiosHeaders) {
      config.headers.set('Authorization', `Bearer ${token}`)
    } else {
      (config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
    }
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      '请求失败，请稍后重试'
    return Promise.reject(new Error(message))
  }
)

export { apiClient }
export default apiClient
