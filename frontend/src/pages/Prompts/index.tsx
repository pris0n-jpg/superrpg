import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  Plus,
  RefreshCw,
  Search,
  Eye,
  PenSquare,
  Trash2,
  Tag,
} from 'lucide-react'

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { fetchPromptTemplates, deletePromptTemplate } from '@/api/prompts'
import type { PromptTemplateDto } from '@/api/types'

const extractTags = (metadata: Record<string, any>): string[] => {
  const rawTags = metadata?.tags
  if (Array.isArray(rawTags)) {
    return rawTags.filter((tag): tag is string => typeof tag === 'string')
  }
  if (typeof rawTags === 'string') {
    return rawTags.split(',').map(tag => tag.trim()).filter(Boolean)
  }
  return []
}

const Prompts = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [templates, setTemplates] = useState<PromptTemplateDto[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  const loadTemplates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchPromptTemplates()
      setTemplates(data.templates)
    } catch (err) {
      const message = (err as Error).message
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadTemplates()
  }, [loadTemplates])

  const filteredTemplates = useMemo(() => {
    const query = searchQuery.trim().toLowerCase()
    if (!query) {
      return templates
    }

    return templates.filter((template) => {
      const tags = extractTags(template.metadata || {})
      return (
        template.name.toLowerCase().includes(query) ||
        (template.description || '').toLowerCase().includes(query) ||
        tags.some((tag) => tag.toLowerCase().includes(query))
      )
    })
  }, [searchQuery, templates])

  const handleDelete = async (id: string) => {
    const confirmed = window.confirm(
      t('prompts.confirmDelete', '确定要删除该提示模板吗？')
    )
    if (!confirmed) {
      return
    }

    try {
      await deletePromptTemplate(id)
      toast.success(t('prompts.deleteSuccess', '提示模板已删除'))
      setTemplates((prev) => prev.filter((template) => template.id !== id))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
            {t('prompts.title', '提示模板')}
          </h1>
          <p className="text-secondary-600 dark:text-secondary-400">
            {t('prompts.subtitle', '集中管理与编辑 AI 提示模板')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadTemplates}
            loading={loading}
            icon={<RefreshCw className="h-4 w-4" />}
          >
            {t('common.refresh', '刷新')}
          </Button>
          <Button
            variant="primary"
            onClick={() => navigate('/prompts/new')}
            icon={<Plus className="h-4 w-4" />}
          >
            {t('prompts.createNew', '新建模板')}
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder={t('prompts.searchPlaceholder', '搜索模板名称或标签')}
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
        </div>
      ) : filteredTemplates.length === 0 ? (
        <Card>
          <CardContent className="py-16 text-center space-y-4">
            <div className="mx-auto w-16 h-16 rounded-full bg-secondary-100 dark:bg-secondary-800 flex items-center justify-center">
              <Search className="h-8 w-8 text-secondary-400" />
            </div>
            <h3 className="text-lg font-medium text-secondary-900 dark:text-secondary-100">
              {searchQuery
                ? t('prompts.noSearchResult', '未找到匹配的提示模板')
                : t('prompts.emptyStateTitle', '暂未创建提示模板')}
            </h3>
            <p className="text-secondary-600 dark:text-secondary-400">
              {searchQuery
                ? t('prompts.adjustSearch', '尝试调整搜索条件或关键字')
                : t('prompts.emptyStateDescription', '创建第一个模板以便快速构建对话与剧情')}
            </p>
            <Button
              variant="primary"
              onClick={() => navigate('/prompts/new')}
              icon={<Plus className="h-4 w-4" />}
            >
              {t('prompts.createNew', '新建模板')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredTemplates.map((template) => {
            const tags = extractTags(template.metadata || {})
            return (
              <Card
                key={template.id}
                className="hover:shadow-medium transition-shadow flex flex-col"
              >
                <CardHeader className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <CardTitle className="text-lg font-semibold text-secondary-900 dark:text-secondary-100">
                        {template.name}
                      </CardTitle>
                      <div className="flex items-center gap-2 text-sm text-secondary-500 dark:text-secondary-400">
                        <span>
                          {t('prompts.version', '版本')} {template.version}
                        </span>
                        <span>•</span>
                        <span>
                          {template.is_active
                            ? t('prompts.status.active', '启用中')
                            : t('prompts.status.inactive', '已停用')}
                        </span>
                        {template.variables.length > 0 && (
                          <>
                            <span>•</span>
                            <span>
                              {t('prompts.variableCount', '变量')} {template.variables.length}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-200 text-xs"
                        >
                          <Tag className="h-3 w-3" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </CardHeader>
                <CardContent className="flex-1 flex flex-col justify-between space-y-4">
                  <p className="text-sm text-secondary-600 dark:text-secondary-400 line-clamp-3">
                    {template.description || t('prompts.noDescription', '暂无描述')}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-secondary-500 dark:text-secondary-400">
                      {template.updated_at
                        ? t(
                            'prompts.updatedAt',
                            '更新于 {{time}}',
                            { time: new Date(template.updated_at).toLocaleString() }
                          )
                        : t('prompts.neverUpdated', '尚未更新')}
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/prompts/${template.id}`)}
                        icon={<Eye className="h-4 w-4" />}
                      >
                        {t('common.view', '查看')}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/prompts/${template.id}/edit`)}
                        icon={<PenSquare className="h-4 w-4" />}
                      >
                        {t('common.edit', '编辑')}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(template.id)}
                        icon={<Trash2 className="h-4 w-4" />}
                      >
                        {t('common.delete', '删除')}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default Prompts
