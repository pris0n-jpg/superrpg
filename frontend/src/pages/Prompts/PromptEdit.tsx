import { ChangeEvent, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { ArrowLeft, Plus, Save, Trash2 } from 'lucide-react'

import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import {
  createPromptTemplate,
  fetchPromptTemplate,
  updatePromptTemplate,
} from '@/api/prompts'
import {
  createEmptyPromptSection,
  createEmptyPromptTemplateForm,
  mapPromptFormToCreatePayload,
  mapPromptFormToUpdatePayload,
  mapPromptTemplateDtoToForm,
  type PromptTemplateFormState,
  type PromptSectionForm,
} from '@/utils/mappers'

const SECTION_TYPES = [
  'system',
  'role',
  'world',
  'context',
  'instruction',
  'history',
  'example',
  'custom',
] as const

const resolveTags = (metadata: Record<string, any>): string[] => {
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

const PromptEdit = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const isEditing = Boolean(id)
  const [form, setForm] = useState<PromptTemplateFormState>(createEmptyPromptTemplateForm())
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    const loadTemplate = async () => {
      if (!isEditing || !id) {
        return
      }
      setLoading(true)
      setError(null)
      try {
        const data = await fetchPromptTemplate(id)
        setForm(mapPromptTemplateDtoToForm(data))
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadTemplate()
  }, [id, isEditing])

  const tags = useMemo(() => resolveTags(form.metadata || {}), [form.metadata])

  const handleChange = (field: keyof PromptTemplateFormState, value: any) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleMetadataChange = (key: string, value: any) => {
    setForm((prev) => ({
      ...prev,
      metadata: {
        ...(prev.metadata || {}),
        [key]: value,
      },
    }))
  }

  const handleSectionChange = (
    sectionId: string,
    key: keyof PromptSectionForm,
    value: string | number | Record<string, any>
  ) => {
    setForm((prev) => ({
      ...prev,
      sections: prev.sections.map((section) =>
        section.id === sectionId
          ? {
              ...section,
              [key]: value,
            }
          : section
      ),
    }))
  }

  const handleAddSection = () => {
    setForm((prev) => ({
      ...prev,
      sections: [
        ...prev.sections,
        createEmptyPromptSection({ priority: prev.sections.length * 10 }),
      ],
    }))
  }

  const handleRemoveSection = (sectionId: string) => {
    if (form.sections.length === 1) {
      toast.error(t('prompts.section.mustHaveOne', '至少需要保留一个段落'))
      return
    }

    setForm((prev) => ({
      ...prev,
      sections: prev.sections.filter((section) => section.id !== sectionId),
    }))
  }

  const handleAddTag = () => {
    const newTag = tagInput.trim()
    if (!newTag) {
      return
    }

    if (tags.includes(newTag)) {
      toast.error(t('prompts.tagExists', '标签已存在'))
      return
    }

    handleMetadataChange('tags', [...tags, newTag])
    setTagInput('')
  }

  const handleRemoveTag = (tagToRemove: string) => {
    handleMetadataChange(
      'tags',
      tags.filter((tag) => tag !== tagToRemove)
    )
  }

  const validateForm = () => {
    if (!form.name.trim()) {
      toast.error(t('prompts.validation.name', '模板名称不能为空'))
      return false
    }

    if (form.sections.length === 0) {
      toast.error(t('prompts.validation.section', '至少需要一个提示段落'))
      return false
    }

    if (form.sections.some((section) => !section.content.trim())) {
      toast.error(t('prompts.validation.sectionContent', '提示段落内容不能为空'))
      return false
    }

    return true
  }

  const handleSave = async () => {
    if (!validateForm()) {
      return
    }

    setSaving(true)
    setError(null)

    try {
      if (isEditing && id) {
        await updatePromptTemplate(id, mapPromptFormToUpdatePayload(form))
        toast.success(t('prompts.updateSuccess', '提示模板已更新'))
        navigate(`/prompts/${id}`)
      } else {
        const created = await createPromptTemplate(mapPromptFormToCreatePayload(form))
        toast.success(t('prompts.createSuccess', '提示模板创建成功'))
        navigate(`/prompts/${created.id}`)
      }
    } catch (err) {
      const message = (err as Error).message
      setError(message)
      toast.error(message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
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
            {isEditing
              ? t('prompts.editTitle', '编辑提示模板')
              : t('prompts.createTitle', '新建提示模板')}
          </h1>
          <p className="text-secondary-600 dark:text-secondary-400">
            {t('prompts.editSubtitle', '配置提示段落与元数据，用于驱动 AI 行为')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/prompts')}
          >
            {t('common.cancel', '取消')}
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            loading={saving}
            icon={<Save className="h-4 w-4" />}
          >
            {t('common.save', '保存')}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200">
          {error}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>{t('prompts.basicInfo', '基础信息')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={t('prompts.fields.name', '模板名称')}
              placeholder={t('prompts.fields.namePlaceholder', '例如：战斗开场提示')}
              value={form.name}
              onChange={(event) => handleChange('name', event.target.value)}
            />
            <Input
              label={t('prompts.fields.version', '版本号')}
              placeholder="1.0.0"
              value={form.version}
              onChange={(event) => handleChange('version', event.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={t('prompts.fields.category', '分类')}
              placeholder={t('prompts.fields.categoryPlaceholder', '例如：战斗 / 对话')}
              value={(form.metadata?.category as string) || ''}
              onChange={(event) => handleMetadataChange('category', event.target.value)}
            />
            <Input
              label={t('prompts.fields.author', '作者')}
              placeholder={t('prompts.fields.authorPlaceholder', '署名作者，可选')}
              value={(form.metadata?.author as string) || ''}
              onChange={(event) => handleMetadataChange('author', event.target.value)}
            />
          </div>

          <label className="block space-y-2">
            <span className="text-sm text-secondary-600 dark:text-secondary-400">
              {t('prompts.fields.description', '模板描述')}
            </span>
            <textarea
              className="w-full rounded-lg border border-secondary-300 dark:border-secondary-600 bg-transparent p-3 min-h-[120px] focus:outline-none focus:ring-2 focus:ring-primary-500"
              value={form.description}
              onChange={(event) => handleChange('description', event.target.value)}
            />
          </label>

          <div className="flex items-center gap-2">
            <input
              id="prompt-active"
              type="checkbox"
              checked={form.isActive}
              onChange={(event: ChangeEvent<HTMLInputElement>) =>
                handleChange('isActive', event.target.checked)
              }
              className="h-4 w-4 text-primary-600 border-secondary-300 rounded"
            />
            <label htmlFor="prompt-active" className="text-sm text-secondary-700 dark:text-secondary-300">
              {t('prompts.fields.isActive', '启用该模板')}
            </label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('prompts.tags', '标签')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Input
              placeholder={t('prompts.tagPlaceholder', '输入标签后回车或点击添加')}
              value={tagInput}
              onChange={(event) => setTagInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                  handleAddTag()
                }
              }}
            />
            <Button variant="outline" onClick={handleAddTag} icon={<Plus className="h-4 w-4" />}>
              {t('common.add', '添加')}
            </Button>
          </div>

          {tags.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-50 dark:bg-primary-900 text-primary-700 dark:text-primary-200 text-sm"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="text-xs text-primary-500 hover:text-primary-700"
                    aria-label={t('prompts.removeTag', '移除标签')}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-sm text-secondary-500 dark:text-secondary-400">
              {t('prompts.noTags', '暂无标签，可用于快速筛选模板')}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>{t('prompts.sections', '提示段落')}</CardTitle>
          <Button variant="outline" size="sm" onClick={handleAddSection} icon={<Plus className="h-4 w-4" />}>
            {t('prompts.addSection', '新增段落')}
          </Button>
        </CardHeader>
        <CardContent className="space-y-6">
          {form.sections.map((section) => (
            <div
              key={section.id}
              className="border border-secondary-200 dark:border-secondary-700 rounded-lg p-4 space-y-4"
            >
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <label className="space-y-1">
                    <span className="text-sm text-secondary-600 dark:text-secondary-400">
                      {t('prompts.fields.sectionType', '段落类型')}
                    </span>
                    <select
                      value={section.sectionType}
                      onChange={(event) => handleSectionChange(section.id, 'sectionType', event.target.value)}
                      className="w-full rounded-lg border border-secondary-300 dark:border-secondary-600 bg-transparent p-2"
                    >
                      {SECTION_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {t(`prompts.sectionType.${type}`, type)}
                        </option>
                      ))}
                    </select>
                  </label>

                  <Input
                    label={t('prompts.fields.priority', '优先级')}
                    type="number"
                    value={section.priority}
                    onChange={(event) =>
                      handleSectionChange(section.id, 'priority', Number(event.target.value))
                    }
                  />

                  <Input
                    label={t('prompts.fields.sectionMetadata', '自定义标记 (可选)')}
                    placeholder={t('prompts.fields.sectionMetadataPlaceholder', '例如：phase: intro')}
                    value={section.metadata?.label || ''}
                    onChange={(event) =>
                      handleSectionChange(section.id, 'metadata', {
                        ...(section.metadata || {}),
                        label: event.target.value,
                      })
                    }
                  />
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleRemoveSection(section.id)}
                  icon={<Trash2 className="h-4 w-4" />}
                >
                  {t('common.delete', '删除')}
                </Button>
              </div>

              <label className="block space-y-2">
                <span className="text-sm text-secondary-600 dark:text-secondary-400">
                  {t('prompts.fields.sectionContent', '段落内容')}
                </span>
                <textarea
                  className="w-full rounded-lg border border-secondary-300 dark:border-secondary-600 bg-transparent p-3 min-h-[160px] focus:outline-none focus:ring-2 focus:ring-primary-500"
                  value={section.content}
                  onChange={(event) => handleSectionChange(section.id, 'content', event.target.value)}
                />
              </label>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

export default PromptEdit
