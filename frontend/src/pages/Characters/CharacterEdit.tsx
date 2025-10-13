import { ChangeEvent, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Save,
  X,
  Plus,
  Trash2,
  Upload,
  Eye,
  ArrowLeft
} from 'lucide-react'

import { Button, Card, CardContent, CardHeader, Input } from '@/components/ui'
import type { CharacterCard } from '@/types'
import { fetchCharacter, createCharacter, updateCharacter } from '@/api/characters'
import { mapCharacterDtoToCard, mapCardToCreatePayload, mapCardToUpdatePayload } from '@/utils/mappers'
import { toast } from 'react-hot-toast'

const CharacterEdit = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { id } = useParams()
  const isEditing = Boolean(id)
  
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [character, setCharacter] = useState<Partial<CharacterCard>>({
    name: '',
    description: '',
    personality: '',
    background: '',
    avatar: '',
    tags: [],
    isPublic: false,
    isTemplate: false,
    metadata: {
      age: undefined,
      gender: '',
      occupation: '',
      location: '',
      customFields: {}
    }
  })
  const [tagInput, setTagInput] = useState('')

  useEffect(() => {
    const loadCharacter = async () => {
      if (!isEditing || !id) {
        return
      }
      setLoading(true)
      setError(null)
      try {
        const response = await fetchCharacter(id)
        const mapped = mapCharacterDtoToCard(response)
        setCharacter(mapped)
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadCharacter()
  }, [id, isEditing])

  const handleSave = async () => {
    if (!character.name) {
      toast.error(t('characters.nameRequired', '角色名称不能为空'))
      return
    }

    setSaving(true)
    setError(null)
    try {
      if (isEditing && id) {
        await updateCharacter(id, mapCardToUpdatePayload(character))
        toast.success(t('characters.updateSuccess', '角色已更新'))
      } else {
        await createCharacter(mapCardToCreatePayload(character))
        toast.success(t('characters.createSuccess', '角色创建成功'))
      }
      navigate('/characters')
    } catch (err) {
      setError((err as Error).message)
      toast.error((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const handleAddTag = () => {
    const trimmed = tagInput.trim()
    if (trimmed && !(character.tags || []).includes(trimmed)) {
      setCharacter((prev) => ({
        ...prev,
        tags: [...(prev.tags || []), trimmed]
      }))
      setTagInput('')
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setCharacter((prev) => ({
      ...prev,
      tags: (prev.tags || []).filter((tag) => tag !== tagToRemove)
    }))
  }

  const handleAvatarUpload = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onloadend = () => {
        setCharacter((prev) => ({
          ...prev,
          avatar: reader.result as string
        }))
      }
      reader.readAsDataURL(file)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/characters')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            {t('common.back', '返回')}
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
              {isEditing ? t('characters.edit') : t('characters.create')}
            </h1>
            <p className="text-secondary-600 dark:text-secondary-400">
              {isEditing ? t('characters.editSubtitle', '编辑角色信息') : t('characters.createSubtitle', '创建新的角色卡')}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {isEditing && (
            <Button
              variant="outline"
              onClick={() => navigate('/characters/' + id)}
            >
              <Eye className="h-4 w-4 mr-2" />
              {t('common.preview', '预览')}
            </Button>
          )}
          <Button variant="outline" onClick={() => navigate('/characters')}>
            <X className="h-4 w-4 mr-2" />
            {t('common.cancel', '取消')}
          </Button>
          <Button variant="primary" onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? t('common.saving', '保存中...') : t('common.save', '保存')}
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
          <h3 className="font-semibold">{t('characters.basicInfo', '基本信息')}</h3>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={t('characters.fields.name', '角色名称')}
              value={character.name || ''}
              onChange={(e) => setCharacter((prev) => ({ ...prev, name: e.target.value }))}
              required
            />
            <Input
              label={t('characters.fields.occupation', '职业')}
              value={character.metadata?.occupation || ''}
              onChange={(e) =>
                setCharacter((prev) => ({
                  ...prev,
                  metadata: {
                    ...(prev.metadata || { customFields: {} }),
                    occupation: e.target.value,
                    customFields: prev.metadata?.customFields || {}
                  }
                }))
              }
            />
            <Input
              label={t('characters.fields.location', '所在地')}
              value={character.metadata?.location || ''}
              onChange={(e) =>
                setCharacter((prev) => ({
                  ...prev,
                  metadata: {
                    ...(prev.metadata || { customFields: {} }),
                    location: e.target.value,
                    customFields: prev.metadata?.customFields || {}
                  }
                }))
              }
            />
            <Input
              label={t('characters.fields.gender', '性别')}
              value={character.metadata?.gender || ''}
              onChange={(e) =>
                setCharacter((prev) => ({
                  ...prev,
                  metadata: {
                    ...(prev.metadata || { customFields: {} }),
                    gender: e.target.value,
                    customFields: prev.metadata?.customFields || {}
                  }
                }))
              }
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label={t('characters.fields.personality', '性格特点')}
              value={character.personality || ''}
              onChange={(e) => setCharacter((prev) => ({ ...prev, personality: e.target.value }))}
            />
            <Input
              label={t('characters.fields.age', '年龄')}
              type="number"
              value={character.metadata?.age ?? ''}
              onChange={(e) =>
                setCharacter((prev) => ({
                  ...prev,
                  metadata: {
                    ...(prev.metadata || { customFields: {} }),
                    age: e.target.value ? Number(e.target.value) : undefined,
                    customFields: prev.metadata?.customFields || {}
                  }
                }))
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-2">
              {t('characters.fields.avatar', '角色头像')}
            </label>
            <div className="flex items-center space-x-4">
              <div className="w-24 h-24 bg-secondary-100 dark:bg-secondary-800 rounded-full flex items-center justify-center">
                {character.avatar ? (
                  <img
                    src={character.avatar}
                    alt={character.name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <span className="text-2xl text-secondary-500">
                    {character.name?.charAt(0) || 'A'}
                  </span>
                )}
              </div>
              <Button variant="outline" onClick={() => document.getElementById('avatar-upload')?.click()}>
                <Upload className="h-4 w-4 mr-2" />
                {t('characters.uploadAvatar', '上传头像')}
              </Button>
              <input
                id="avatar-upload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleAvatarUpload}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="font-semibold">{t('characters.background', '背景与个性')}</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="block">
            <span className="text-sm text-secondary-600 dark:text-secondary-400">
              {t('characters.fields.description', '角色描述')}
            </span>
            <textarea
              className="mt-1 w-full rounded-lg border border-secondary-300 dark:border-secondary-600 bg-transparent p-3"
              rows={4}
              value={character.description || ''}
              onChange={(e) => setCharacter((prev) => ({ ...prev, description: e.target.value }))}
            />
          </label>

          <label className="block">
            <span className="text-sm text-secondary-600 dark:text-secondary-400">
              {t('characters.fields.background', '背景故事')}
            </span>
            <textarea
              className="mt-1 w-full rounded-lg border border-secondary-300 dark:border-secondary-600 bg-transparent p-3"
              rows={6}
              value={character.background || ''}
              onChange={(e) => setCharacter((prev) => ({ ...prev, background: e.target.value }))}
            />
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="font-semibold">{t('characters.tags', '角色标签')}</h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-2">
            <Input
              placeholder={t('characters.tagPlaceholder', '输入标签后回车')}
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  handleAddTag()
                }
              }}
            />
            <Button variant="outline" onClick={handleAddTag}>
              <Plus className="h-4 w-4 mr-2" />
              {t('common.add', '添加')}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {(character.tags || []).map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200"
              >
                {tag}
                <button
                  type="button"
                  className="ml-2 text-xs text-error-500"
                  onClick={() => handleRemoveTag(tag)}
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CharacterEdit
