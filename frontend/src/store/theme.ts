import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Theme } from '@/types'

type ThemeMode = 'light' | 'dark' | 'auto'

interface ThemeState {
  mode: ThemeMode
  theme: Theme
  systemTheme: 'light' | 'dark'
  isDark: boolean
  
  // Actions
  setMode: (mode: ThemeMode) => void
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
  initTheme: () => void
}

// 默认主题配置
const defaultTheme: Theme = {
  id: 'default',
  name: 'Default',
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
      950: '#172554',
    },
    secondary: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
      950: '#020617',
    },
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
      950: '#052e16',
    },
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
      950: '#451a03',
    },
    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
      950: '#450a0a',
    },
    background: {
      primary: '#ffffff',
      secondary: '#f8fafc',
      tertiary: '#f1f5f9',
    },
    text: {
      primary: '#1e293b',
      secondary: '#64748b',
      tertiary: '#94a3b8',
      inverse: '#ffffff',
    },
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      serif: ['Georgia', 'ui-serif', 'serif'],
      mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
    },
    fontSize: {
      xs: ['0.75rem', '1rem'],
      sm: ['0.875rem', '1.25rem'],
      base: ['1rem', '1.5rem'],
      lg: ['1.125rem', '1.75rem'],
      xl: ['1.25rem', '1.75rem'],
      '2xl': ['1.5rem', '2rem'],
      '3xl': ['1.875rem', '2.25rem'],
      '4xl': ['2.25rem', '2.5rem'],
      '5xl': ['3rem', '1'],
      '6xl': ['3.75rem', '1'],
    },
    fontWeight: {
      thin: 100,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
      black: 900,
    },
  },
  spacing: {
    scale: 1,
    sizes: {
      0: '0px',
      1: '0.25rem',
      2: '0.5rem',
      3: '0.75rem',
      4: '1rem',
      5: '1.25rem',
      6: '1.5rem',
      8: '2rem',
      10: '2.5rem',
      12: '3rem',
      16: '4rem',
      20: '5rem',
      24: '6rem',
      32: '8rem',
    },
  },
}

// 获取系统主题
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// 应用主题到DOM
const applyThemeToDOM = (isDark: boolean) => {
  const root = document.documentElement
  
  if (isDark) {
    root.classList.add('dark')
    root.classList.remove('light')
  } else {
    root.classList.add('light')
    root.classList.remove('dark')
  }
  
  // 设置CSS自定义属性
  const theme = isDark ? darkTheme : defaultTheme
  const colors = theme.colors
  
  // 设置主色调
  Object.entries(colors.primary).forEach(([key, value]) => {
    root.style.setProperty(`--color-primary-${key}`, value)
  })
  
  // 设置背景色
  root.style.setProperty('--color-bg-primary', colors.background.primary)
  root.style.setProperty('--color-bg-secondary', colors.background.secondary)
  root.style.setProperty('--color-bg-tertiary', colors.background.tertiary)
  
  // 设置文字颜色
  root.style.setProperty('--color-text-primary', colors.text.primary)
  root.style.setProperty('--color-text-secondary', colors.text.secondary)
  root.style.setProperty('--color-text-tertiary', colors.text.tertiary)
  root.style.setProperty('--color-text-inverse', colors.text.inverse)
}

// 暗色主题配置
const darkTheme: Theme = {
  ...defaultTheme,
  id: 'dark',
  name: 'Dark',
  colors: {
    ...defaultTheme.colors,
    background: {
      primary: '#0f172a',
      secondary: '#1e293b',
      tertiary: '#334155',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#cbd5e1',
      tertiary: '#94a3b8',
      inverse: '#0f172a',
    },
  },
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'auto',
      theme: defaultTheme,
      systemTheme: getSystemTheme(),
      isDark: false,

      setMode: (mode: ThemeMode) => {
        const { systemTheme } = get()
        const isDark = mode === 'auto' ? systemTheme === 'dark' : mode === 'dark'
        
        set({ mode, isDark })
        applyThemeToDOM(isDark)
      },

      setTheme: (theme: Theme) => {
        set({ theme })
      },

      toggleTheme: () => {
        const { mode, systemTheme } = get()
        let newMode: ThemeMode
        
        if (mode === 'auto') {
          newMode = systemTheme === 'dark' ? 'light' : 'dark'
        } else {
          newMode = mode === 'dark' ? 'light' : 'dark'
        }
        
        get().setMode(newMode)
      },

      initTheme: () => {
        const { mode } = get()
        const systemTheme = getSystemTheme()
        const isDark = mode === 'auto' ? systemTheme === 'dark' : mode === 'dark'
        
        set({ systemTheme, isDark })
        applyThemeToDOM(isDark)
        
        // 监听系统主题变化
        if (typeof window !== 'undefined') {
          const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
          const handleChange = () => {
            const newSystemTheme = getSystemTheme()
            const { mode } = get()
            const isDark = mode === 'auto' ? newSystemTheme === 'dark' : mode === 'dark'
            
            set({ systemTheme: newSystemTheme, isDark })
            applyThemeToDOM(isDark)
          }
          
          mediaQuery.addEventListener('change', handleChange)
        }
      },
    }),
    {
      name: 'theme-storage',
      partialize: (state) => ({
        mode: state.mode,
        theme: state.theme,
      }),
    }
  )
)

// 主题相关工具函数
export const themeUtils = {
  // 获取当前主题颜色
  getColor: (colorPath: string): string => {
    const { theme } = useThemeStore.getState()
    const keys = colorPath.split('.')
    let value: any = theme
    
    for (const key of keys) {
      value = value?.[key]
    }
    
    return value || ''
  },
  
  // 获取CSS变量值
  getCSSVar: (varName: string): string => {
    if (typeof window === 'undefined') return ''
    return getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
  },
  
  // 检查是否为暗色主题
  isDark: (): boolean => {
    return useThemeStore.getState().isDark
  },
  
  // 生成主题类名
  getThemeClass: (baseClass: string, darkClass?: string): string => {
    const { isDark } = useThemeStore.getState()
    return isDark && darkClass ? `${baseClass} ${darkClass}` : baseClass
  },
}