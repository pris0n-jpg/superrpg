import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { 
  Menu, 
  X, 
  Sun, 
  Moon, 
  Settings, 
  User, 
  Bell,
  Search,
  Globe,
  Check
} from 'lucide-react'

import { Button } from '@/components/ui'
import { useThemeStore } from '@/store/theme'
import { useAuthStore } from '@/store/auth'

const Header = () => {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { mode, isDark, toggleTheme } = useThemeStore()
  const { user, isAuthenticated, logout } = useAuthStore()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false)
  const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false)

  const profileMenuRef = useRef<HTMLDivElement | null>(null)
  const languageMenuRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (profileMenuRef.current && !profileMenuRef.current.contains(target)) {
        setIsProfileMenuOpen(false)
      }
      if (languageMenuRef.current && !languageMenuRef.current.contains(target)) {
        setIsLanguageMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // 处理语言切换
  const handleLanguageChange = (language: string) => {
    i18n.changeLanguage(language)
    localStorage.setItem('language', language)
    setIsLanguageMenuOpen(false)
    setIsProfileMenuOpen(false)
  }

  // 处理用户登出
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // 导航菜单项
  const navigationItems = [
    { label: t('navigation.dashboard'), path: '/dashboard' },
    { label: t('navigation.characters'), path: '/characters' },
    { label: t('navigation.lorebooks'), path: '/lorebooks' },
    { label: t('navigation.prompts'), path: '/prompts' },
    { label: t('navigation.chat'), path: '/chat' },
    { label: t('navigation.extensions'), path: '/extensions' },
  ]

  // 语言选项
  const languageOptions = [
    { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
    { code: 'en-US', name: 'English', flag: '🇺🇸' },
    { code: 'ja-JP', name: '日本語', flag: '🇯🇵' },
  ]

  return (
    <header className="bg-white dark:bg-secondary-800 border-b border-secondary-200 dark:border-secondary-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo和导航 */}
          <div className="flex items-center">
            {/* Logo */}
            <div className="flex-shrink-0">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center space-x-2 text-xl font-bold text-primary-600 dark:text-primary-400"
              >
                <div className="w-8 h-8 bg-primary-600 dark:bg-primary-400 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">RPG</span>
                </div>
                <span className="hidden sm:inline">SuperRPG</span>
              </button>
            </div>

            {/* 桌面导航 */}
            <nav className="hidden md:ml-8 md:flex md:space-x-1">
              {navigationItems.map((item) => (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className="px-3 py-2 rounded-md text-sm font-medium text-secondary-700 dark:text-secondary-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors"
                >
                  {item.label}
                </button>
              ))}
            </nav>
          </div>

          {/* 右侧工具栏 */}
          <div className="flex items-center space-x-2">
            {/* 搜索框 */}
            <div className="hidden md:block">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-secondary-400" />
                <input
                  type="text"
                  placeholder={t('common.search')}
                  className="pl-10 pr-4 py-2 border border-secondary-300 dark:border-secondary-600 rounded-lg bg-white dark:bg-secondary-700 text-secondary-900 dark:text-secondary-100 placeholder-secondary-500 dark:placeholder-secondary-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent w-64"
                />
              </div>
            </div>

            {/* 主题切换 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="p-2"
            >
              {isDark ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>

            {/* 语言切换 */}
            <div className="relative" ref={languageMenuRef}>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setIsLanguageMenuOpen((prev) => !prev)
                  setIsProfileMenuOpen(false)
                }}
                className="p-2"
                aria-expanded={isLanguageMenuOpen}
                aria-haspopup="true"
              >
                <Globe className="h-5 w-5" />
              </Button>

              {isLanguageMenuOpen && (
                <div className="absolute right-0 mt-2 w-44 bg-white dark:bg-secondary-800 rounded-lg shadow-lg border border-secondary-200 dark:border-secondary-700 py-1 z-50">
                  {languageOptions.map((option) => (
                    <button
                      key={option.code}
                      onClick={() => handleLanguageChange(option.code)}
                      className="flex items-center justify-between w-full px-4 py-2 text-sm text-secondary-700 dark:text-secondary-300 hover:bg-secondary-100 dark:hover:bg-secondary-700"
                    >
                      <span className="flex items-center gap-2">
                        <span>{option.flag}</span>
                        {option.name}
                      </span>
                      {i18n.language === option.code && (
                        <Check className="h-4 w-4 text-primary-500" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* 通知 */}
            <Button
              variant="ghost"
              size="sm"
              className="p-2 relative"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-error-500 rounded-full"></span>
            </Button>

            {/* 用户菜单 */}
            {isAuthenticated ? (
              <div className="relative" ref={profileMenuRef}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsProfileMenuOpen((prev) => !prev)
                    setIsLanguageMenuOpen(false)
                  }}
                  className="flex items-center space-x-2"
                >
                  <div className="h-8 w-8 bg-primary-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">
                      {user?.username?.charAt(0).toUpperCase() || <User className="h-4 w-4" />}
                    </span>
                  </div>
                  <span className="hidden sm:inline text-sm font-medium">
                    {user?.username}
                  </span>
                </Button>

                {/* 用户下拉菜单 */}
                {isProfileMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-secondary-800 rounded-lg shadow-lg border border-secondary-200 dark:border-secondary-700 py-1 z-50">
                    <button
                      onClick={() => {
                        navigate('/settings')
                        setIsProfileMenuOpen(false)
                      }}
                      className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-secondary-700 dark:text-secondary-300 hover:bg-secondary-100 dark:hover:bg-secondary-700"
                    >
                      <Settings className="h-4 w-4" />
                      <span>{t('navigation.settings')}</span>
                    </button>
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-secondary-700 dark:text-secondary-300 hover:bg-secondary-100 dark:hover:bg-secondary-700"
                    >
                      <X className="h-4 w-4" />
                      <span>{t('app.logout')}</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/login')}
              >
                {t('app.login')}
              </Button>
            )}

            {/* 移动端菜单按钮 */}
            <div className="md:hidden">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="p-2"
              >
                {isMobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 移动端导航菜单 */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-secondary-200 dark:border-secondary-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navigationItems.map((item) => (
              <button
                key={item.path}
                onClick={() => {
                  navigate(item.path)
                  setIsMobileMenuOpen(false)
                }}
                className="block px-3 py-2 rounded-md text-base font-medium text-secondary-700 dark:text-secondary-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-secondary-100 dark:hover:bg-secondary-700 w-full text-left"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}

export default Header
