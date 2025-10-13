import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { BookOpen } from 'lucide-react'

import { Card, CardContent, CardHeader } from '@/components/ui'
import { fetchLorebooks } from '@/api/lorebooks'

const Lorebooks = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [lorebooks, setLorebooks] = useState([] as Array<{ id: string; name: string; description: string }>)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadLorebooks = async () => {
      setLoading(true)
      setError(null)
      try {
        const response = await fetchLorebooks()
        setLorebooks(response.lorebooks.map((item) => ({
          id: item.id,
          name: item.name,
          description: item.description || ''
        })))
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadLorebooks()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
            {t('lorebooks.title')}
          </h1>
          <p className="text-secondary-600 dark:text-secondary-400">
            {t('lorebooks.subtitle', '集中管理世界观与背景资料')}
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : lorebooks.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-secondary-100 dark:bg-secondary-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <BookOpen className="h-8 w-8 text-secondary-400" />
          </div>
          <h3 className="text-lg font-medium text-secondary-900 dark:text-secondary-100 mb-2">
            {t('lorebooks.empty', '暂无传说书数据')}
          </h3>
          <p className="text-secondary-600 dark:text-secondary-400">
            {t('lorebooks.emptyHint', '可在后端或 API 中创建新的传说书条目')}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {lorebooks.map((lorebook) => (
            <Card key={lorebook.id} className="hover:shadow-medium transition-shadow" onClick={() => navigate('/lorebooks/' + lorebook.id)}>
              <CardHeader>
                <h3 className="font-semibold text-secondary-900 dark:text-secondary-100">
                  {lorebook.name}
                </h3>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-secondary-600 dark:text-secondary-400 line-clamp-3">
                  {lorebook.description || t('lorebooks.noDescription', '暂无描述')}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default Lorebooks
