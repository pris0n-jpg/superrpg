import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import Layout from '@/components/Layout'

// 页面组件
import Dashboard from '@/pages/Dashboard'
import Characters from '@/pages/Characters'
import CharacterDetail from '@/pages/Characters/CharacterDetail'
import CharacterEdit from '@/pages/Characters/CharacterEdit'
import Lorebooks from '@/pages/Lorebooks'
import LorebookDetail from '@/pages/Lorebooks/LorebookDetail'
import LorebookEdit from '@/pages/Lorebooks/LorebookEdit'
import Prompts from '@/pages/Prompts'
import PromptDetail from '@/pages/Prompts/PromptDetail'
import PromptEdit from '@/pages/Prompts/PromptEdit'
import Chat from '@/pages/Chat'
import Settings from '@/pages/Settings'
import Extensions from '@/pages/Extensions'
import NotFound from '@/pages/NotFound'

// 状态管理
import { useThemeStore } from '@/store/theme'
import { useAuthStore } from '@/store/auth'

function App() {
  const { i18n } = useTranslation()
  const { initTheme } = useThemeStore()
  const { checkAuth } = useAuthStore()

  // 初始化应用
  useEffect(() => {
    // 初始化主题
    initTheme()
    
    // 检查认证状态
    checkAuth()
    
    // 设置语言
    const savedLanguage = localStorage.getItem('language') || 'zh-CN'
    if (savedLanguage !== i18n.language) {
      i18n.changeLanguage(savedLanguage)
    }
  }, [initTheme, checkAuth, i18n])

  return (
    <div className="App">
      <Routes>
        {/* 根路径重定向到仪表板 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        
        {/* 主布局路由 */}
        <Route path="/" element={<Layout />}>
          {/* 公开路由 */}
          <Route path="dashboard" element={<Dashboard />} />
          
          {/* 权限限制取消，直接访问 */}
          <Route>
            {/* 角色卡管理 */}
            <Route path="characters" element={<Characters />} />
            <Route path="characters/:id" element={<CharacterDetail />} />
            <Route path="characters/:id/edit" element={<CharacterEdit />} />
            <Route path="characters/new" element={<CharacterEdit />} />
            
            {/* 传说书管理 */}
            <Route path="lorebooks" element={<Lorebooks />} />
            <Route path="lorebooks/:id" element={<LorebookDetail />} />
            <Route path="lorebooks/:id/edit" element={<LorebookEdit />} />
            <Route path="lorebooks/new" element={<LorebookEdit />} />
            
            {/* 提示模板管理 */}
            <Route path="prompts" element={<Prompts />} />
            <Route path="prompts/:id" element={<PromptDetail />} />
            <Route path="prompts/:id/edit" element={<PromptEdit />} />
            <Route path="prompts/new" element={<PromptEdit />} />
            
            {/* 聊天界面 */}
            <Route path="chat" element={<Chat />} />
            <Route path="chat/:sessionId" element={<Chat />} />
            
            {/* 设置页面 */}
            <Route path="settings" element={<Settings />} />
            <Route path="settings/:tab" element={<Settings />} />
            
            {/* 扩展管理 */}
            <Route path="extensions" element={<Extensions />} />
          </Route>
        </Route>
        
        {/* 404页面 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}

export default App