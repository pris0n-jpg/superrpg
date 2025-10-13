import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '@/types'

interface AuthState {
  user: User
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  register: (userData: RegisterData) => Promise<void>
  updateProfile: (userData: Partial<User>) => Promise<void>
  checkAuth: () => Promise<void>
  setLoading: (loading: boolean) => void
}

interface RegisterData {
  username: string
  email: string
  password: string
  confirmPassword: string
}

const guestUser: User = {
  id: 'guest',
  username: 'Guest',
  email: 'guest@example.com',
  avatar: '',
  preferences: {
    theme: 'auto',
    language: 'zh-CN',
    notifications: {
      email: false,
      push: false,
      sound: false,
    },
  },
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: guestUser,
      token: null,
      isAuthenticated: true,
      isLoading: false,
      login: async () => {
        set({ user: guestUser, token: null, isAuthenticated: true, isLoading: false })
      },
      logout: () => {
        set({ user: guestUser, token: null, isAuthenticated: true })
      },
      register: async () => {
        set({ user: guestUser, token: null, isAuthenticated: true, isLoading: false })
      },
      updateProfile: async (userData: Partial<User>) => {
        set((state) => ({
          user: { ...state.user, ...userData },
        }))
      },
      checkAuth: async () => {
        set({ user: guestUser, token: null, isAuthenticated: true, isLoading: false })
      },
      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

export default useAuthStore

export const authUtils = {
  getAuthHeader: () => ({}),
  isAuthenticated: () => true,
  getCurrentUser: () => guestUser,
  hasPermission: () => true,
  hasRole: () => true,
}
