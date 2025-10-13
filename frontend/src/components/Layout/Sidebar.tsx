import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard,
  Users,
  BookOpen,
  MessageSquare,
  Puzzle,
  Settings,
  ChevronDown,
  ChevronRight,
  Plus
} from 'lucide-react'

import { Button } from '@/components/ui'
import { useAuthStore } from '@/store/auth'

interface SidebarItem {
  id: string
  label: string
  icon: any
  path: string
  children?: SidebarItem[]
}

const Sidebar = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const { user } = useAuthStore()
  const userInitial = user?.username?.charAt(0).toUpperCase() || 'G'
  const userDisplayName = user?.username || t('app.guestUser', '访客用户')
  const userSubtitle = user?.email || t('app.role.default', 'SuperRPG 探索者')

  // 侧边栏菜单项
  const menuItems: SidebarItem[] = [
    {
      id: 'dashboard',
      label: t('navigation.dashboard'),
      icon: LayoutDashboard,
      path: '/dashboard',
    },
    {
      id: 'characters',
      label: t('navigation.characters'),
      icon: Users,
      path: '/characters',
      children: [
        {
          id: 'characters-list',
          label: t('characters.title'),
          icon: Users,
          path: '/characters',
        },
        {
          id: 'characters-create',
          label: t('characters.createNew'),
          icon: Plus,
          path: '/characters/new',
        },
      ],
    },
    {
      id: 'lorebooks',
      label: t('navigation.lorebooks'),
      icon: BookOpen,
      path: '/lorebooks',
      children: [
        {
          id: 'lorebooks-list',
          label: t('lorebooks.title'),
          icon: BookOpen,
          path: '/lorebooks',
        },
        {
          id: 'lorebooks-create',
          label: t('lorebooks.createNew'),
          icon: Plus,
          path: '/lorebooks/new',
        },
      ],
    },
    {
      id: 'prompts',
      label: t('navigation.prompts'),
      icon: MessageSquare,
      path: '/prompts',
      children: [
        {
          id: 'prompts-list',
          label: t('prompts.title'),
          icon: MessageSquare,
          path: '/prompts',
        },
        {
          id: 'prompts-create',
          label: t('prompts.createNew'),
          icon: Plus,
          path: '/prompts/new',
        },
      ],
    },
    {
      id: 'chat',
      label: t('navigation.chat'),
      icon: MessageSquare,
      path: '/chat',
    },
    {
      id: 'extensions',
      label: t('navigation.extensions'),
      icon: Puzzle,
      path: '/extensions',
    },
    {
      id: 'settings',
      label: t('navigation.settings'),
      icon: Settings,
      path: '/settings',
    },
  ]

  // 切换展开状态
  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    )
  }

  // 检查是否为当前路径
  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  // 渲染菜单项
  const renderMenuItem = (item: SidebarItem, level: number = 0) => {
    const isExpanded = expandedItems.includes(item.id)
    const hasChildren = item.children && item.children.length > 0
    const active = isActive(item.path)
    const Icon = item.icon

    return (
      <div key={item.id}>
        <Button
          variant={active ? 'secondary' : 'ghost'}
          size="sm"
          className={`w-full justify-start ${level > 0 ? 'ml-4' : ''}`}
          onClick={() => {
            if (hasChildren) {
              toggleExpanded(item.id)
            } else {
              navigate(item.path)
            }
          }}
        >
          <Icon className="h-4 w-4 mr-3" />
          <span className="flex-1 text-left">{item.label}</span>
          {hasChildren && (
            isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )
          )}
        </Button>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {item.children!.map(child => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
      <div className="flex flex-col flex-grow pt-5 bg-white dark:bg-secondary-800 border-r border-secondary-200 dark:border-secondary-700 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 dark:bg-primary-400 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">RPG</span>
            </div>
            <span className="text-lg font-semibold text-secondary-900 dark:text-secondary-100">
              SuperRPG
            </span>
          </div>
        </div>
        
        <div className="mt-8 flex-grow flex flex-col">
          <nav className="flex-1 px-2 pb-4 space-y-1">
            {menuItems.map(item => renderMenuItem(item))}
          </nav>
          
          <div className="flex-shrink-0 flex border-t border-secondary-200 dark:border-secondary-700 p-4">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {userInitial}
                </div>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-secondary-900 dark:text-secondary-100">
                  {userDisplayName}
                </p>
                <p className="text-xs font-medium text-secondary-500 dark:text-secondary-400">
                  {userSubtitle}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Sidebar
