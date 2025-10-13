import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft,
  Copy,
  Edit3,
  Tag,
  AlignLeft,
  Zap,
} from 'lucide-react'

import { Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui'
import { fetchPromptTemplate } from '@/api/prompts'
import type { PromptTemplateDto } from '@/api/types'

const extractTags = (metadata: Record<string, any>): string[] => {
  const rawTags = metadata?.tags
  if (Array.isArray(rawTags)) {
    return rawTags.filter((tag): tag is string => typeof tag === 'string')
  }
  if (typeof rawTags === 'string') {
    return rawTags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
  }
  return []
}

const PromptDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [template, setTemplate] = useState<PromptTemplateDto | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadTemplate = async () => {
      if (!id) {
        return
      }
      setLoading(true)
      setError(null)
      try {
        const data = await fetchPromptTemplate(id)
        setTemplate(data)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadTemplate()
  }, [id])

  const tags = useMemo(
    () => (template ? extractTags(template.metadata || {}) : []),
    [template]
  )

  const handleCopyJson = () => {
    if (!template) {
      return
    }
    navigator.clipboard
      .writeText(JSON.stringify(template, null, 2))
      .then(() => toast.success(t('prompts.copied', '模板数据已复制')))
      .catch(() => toast.error(t('prompts.copyFailed', '复制失败，请稍后重试')))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center space-y-4">
          <h2 className="text-xl font-semibold text-secondary-900 dark:text-secondary-100">
            {t('prompts.loadFailed', '提示模板加载失败')}
          </h2>
          <p className="text-secondary-600 dark:text-secondary-400">{error}</p>
          <Button variant="primary" onClick={() => navigate('/prompts')}>
            {t('common.back', '返回列表')}
          </Button>
        </div>
      </div>
    )
  }

  if (!template) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <button
            onClick={() => navigate(-1)}
            className="inline-flex items-center text-sm text-secondary-500 dark:text-secondary-400 hover:text-secondary-700 dark:hover:text-secondary-200 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('common.back', '返回')}
          </button>
          <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
            {template.name}
          </h1>
          <p className="text-secondary-600 dark:text-secondary-400">
            {template.description || t('prompts.noDescription', '暂无描述')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopyJson}
            icon={<Copy className="h-4 w-4" />}
          >
            {t('common.copy', '复制')}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/prompts/${template.id}/edit`)}
            icon={<Edit3 className="h-4 w-4" />}
          >
            {t('common.edit', '编辑')}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('prompts.basicInfo', '基础信息')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="block text-secondary-500 dark:text-secondary-400">
                {t('prompts.version', '版本')}
              </span>
              <span className="font-medium text-secondary-900 dark:text-secondary-100">
                {template.version}
              </span>
            </div>
            <div>
              <span className="block text-secondary-500 dark:text-secondary-400">
                {t('prompts.status.label', '状态')}
              </span>
              <span className="font-medium text-secondary-900 dark:text-secondary-100">
                {template.is_active
                  ? t('prompts.status.active', '启用中')
                  : t('prompts.status.inactive', '已停用')}
              </span>
            </div>
            <div>
              <span className="block text-secondary-500 dark:text-secondary-400">
                {t('prompts.variableCount', '变量数量')}
              </span>
              <span className="font-medium text-secondary-900 dark:text-secondary-100">
                {template.variables.length}
              </span>
            </div>
          </div>

          {tags.length > 0 && (
            <div>
              <span className="block text-sm text-secondary-500 dark:text-secondary-400 mb-2">
                {t('prompts.tags', '标签')}
              </span>
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-200 text-xs"
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {template.variables.length > 0 && (
            <div>
              <span className="block text-sm text-secondary-500 dark:text-secondary-400 mb-2">
                {t('prompts.variables', '自定义变量')}
              </span>
              <div className="flex flex-wrap gap-2">
                {template.variables.map((variable) => (
                  <span
                    key={variable}
                    className="inline-flex items-center gap-2 px-3 py-1 rounded-lg bg-secondary-100 dark:bg-secondary-800 text-secondary-700 dark:text-secondary-200 text-sm"
                  >
                    <Zap className="h-4 w-4 text-primary-500" />
                    {variable}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('prompts.sections', '提示段落')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {(template.sections || []).length === 0 ? (
            <p className="text-sm text-secondary-600 dark:text-secondary-400">
              {t('prompts.noSections', '暂无提示段落')}
            </p>
          ) : (
            template.sections
              .slice()
              .sort((a, b) => a.priority - b.priority)
              .map((section, index) => (
                <div
                  key={`${section.section_type}-${index}`}
                  className="rounded-lg border border-secondary-200 dark:border-secondary-700 p-4 space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="font-medium text-secondary-900 dark:text-secondary-100">
                      {t(`prompts.sectionType.${section.section_type}`, section.section_type)}
                    </div>
                    <div className="text-xs text-secondary-500 dark:text-secondary-400">
                      {t('prompts.sectionPriority', '优先级')} {section.priority}
                      {typeof section.token_count === 'number' && (
                        <> · {t('prompts.sectionTokens', 'Token')} {section.token_count}</>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-secondary-700 dark:text-secondary-200 whitespace-pre-wrap leading-relaxed">
                    {section.content}
                  </div>
                  {section.metadata && Object.keys(section.metadata).length > 0 && (
                    <div className="text-xs text-secondary-500 dark:text-secondary-400 bg-secondary-50 dark:bg-secondary-900 rounded-md p-3 space-y-1">
                      <div className="flex items-center gap-2 font-medium text-secondary-600 dark:text-secondary-300">
                        <AlignLeft className="h-4 w-4" />
                        {t('prompts.sectionMetadata', '段落元数据')}
                      </div>
                      <pre className="text-xs whitespace-pre-wrap break-all">
                        {JSON.stringify(section.metadata, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PromptDetail
