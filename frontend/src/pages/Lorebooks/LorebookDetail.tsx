import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { Card, CardContent, CardHeader, Button } from '@/components/ui'
import { fetchLorebook } from '@/api/lorebooks'

const LorebookDetail = () => {
  const { id } = useParams<{ id: string }>()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [lorebook, setLorebook] = useState<{ name: string; description: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadLorebook = async () => {
      if (!id) return
      setLoading(true)
      setError(null)
      try {
        const data = await fetchLorebook(id)
        setLorebook({ name: data.name, description: data.description || '' })
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadLorebook()
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-3">
          <h2 className="text-xl font-semibold">{t('lorebooks.loadFailed', '传说书加载失败')}</h2>
          <p className="text-secondary-600 dark:text-secondary-400">{error}</p>
          <Button onClick={() => navigate('/lorebooks')}>{t('common.back', '返回列表')}</Button>
        </div>
      </div>
    )
  }

  if (!lorebook) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center space-y-3">
          <h2 className="text-xl font-semibold">{t('lorebooks.notFound', '传说书未找到')}</h2>
          <Button onClick={() => navigate('/lorebooks')}>{t('common.back', '返回列表')}</Button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <h1 className="text-2xl font-bold">{lorebook.name}</h1>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-secondary-700 dark:text-secondary-200 leading-relaxed">
            {lorebook.description || t('lorebooks.noDescription', '暂无描述')}
          </p>
          <Button variant="outline" onClick={() => navigate('/lorebooks')}>
            {t('common.back', '返回列表')}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

export default LorebookDetail
