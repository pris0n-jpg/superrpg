import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Users,
  BookOpen,
  MessageSquare,
  TrendingUp,
  Calendar,
  Clock,
  Star
} from 'lucide-react'

import { Card, CardContent, CardHeader } from '@/components/ui'
import { fetchSystemSummary } from '@/api/system'

const Dashboard = () => {
  const { t } = useTranslation()
  const [summary, setSummary] = useState({ characters: 0, lorebooks: 0, prompts: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadSummary = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchSystemSummary()
        setSummary(data)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadSummary()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
          {t('dashboard.title')}
        </h1>
        <p className="text-secondary-600 dark:text-secondary-400">
          {t('dashboard.welcome')}
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-primary-100 dark:bg-primary-900 rounded-lg">
                <Users className="h-6 w-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-secondary-600 dark:text-secondary-400">
                  {t('dashboard.totalCharacters')}
                </p>
                <p className="text-2xl font-semibold text-secondary-900 dark:text-secondary-100">
                  {loading ? '--' : summary.characters}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-success-100 dark:bg-success-900 rounded-lg">
                <BookOpen className="h-6 w-6 text-success-600 dark:text-success-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-secondary-600 dark:text-secondary-400">
                  {t('dashboard.totalLorebooks')}
                </p>
                <p className="text-2xl font-semibold text-secondary-900 dark:text-secondary-100">
                  {loading ? '--' : summary.lorebooks}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-warning-100 dark:bg-warning-900 rounded-lg">
                <MessageSquare className="h-6 w-6 text-warning-600 dark:text-warning-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-secondary-600 dark:text-secondary-400">
                  {t('dashboard.totalPrompts')}
                </p>
                <p className="text-2xl font-semibold text-secondary-900 dark:text-secondary-100">
                  {loading ? '--' : summary.prompts}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <div className="p-2 bg-info-100 dark:bg-info-900 rounded-lg">
                <TrendingUp className="h-6 w-6 text-info-600 dark:text-info-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-secondary-600 dark:text-secondary-400">
                  {t('dashboard.totalChats')}
                </p>
                <p className="text-2xl font-semibold text-secondary-900 dark:text-secondary-100">
                  0
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="font-semibold">{t('dashboard.recentChats')}</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-secondary-500 dark:text-secondary-300 text-sm">
              <div>{t('dashboard.noRecentChats', '暂无聊天记录')}</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-semibold">{t('dashboard.popularCharacters')}</h3>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-secondary-500 dark:text-secondary-300 text-sm">
              <div>{t('dashboard.noPopularCharacters', '暂无热门角色统计')}</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
