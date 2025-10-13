import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, useParams } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  Edit,
  ArrowLeft,
  Heart,
  Share,
  Copy,
  Download,
  Play,
  MessageSquare,
  Calendar,
  User,
  MapPin,
  Briefcase,
  Trash2
} from 'lucide-react'

import { Button, Card, CardContent, CardHeader } from '@/components/ui'
import type { CharacterCard } from '@/types'
import { fetchCharacter, deleteCharacter } from '@/api/characters'
import { mapCharacterDtoToCard } from '@/utils/mappers'

const CharacterDetail = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { id } = useParams()
  
  const [loading, setLoading] = useState(true)
  const [character, setCharacter] = useState<CharacterCard | null>(null)
  const [isFavorited, setIsFavorited] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadCharacter = async () => {
      if (!id) {
        return
      }
      setLoading(true)
      setError(null)
      try {
        const response = await fetchCharacter(id)
        setCharacter(mapCharacterDtoToCard(response))
      } catch (err) {
        setError((err as Error).message)
      } finally {
        setLoading(false)
      }
    }

    loadCharacter()
  }, [id])

  const handleToggleFavorite = () => {
    setIsFavorited(!isFavorited)
  }

  const handleShare = () => {
    if (character && navigator.share) {
      navigator.share({
        title: character.name,
        text: character.description,
        url: window.location.href
      })
    } else {
      navigator.clipboard.writeText(window.location.href)
      toast.success(t('characters.linkCopied', '链接已复制'))
    }
  }

  const handleCopy = () => {
    if (!character) {
      return
    }
    navigator.clipboard.writeText(JSON.stringify(character, null, 2))
    toast.success(t('characters.copied', '角色数据已复制'))
  }

  const handleExport = () => {
    toast(t('characters.exportTodo', '导出功能即将推出'), { icon: '🛠️' })
  }

  const handleDelete = async () => {
    if (!id) {
      return
    }
    try {
      await deleteCharacter(id)
      toast.success(t('characters.deleteSuccess', '角色已删除'))
      navigate('/characters')
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const handleStartChat = () => {
    if (id) {
      navigate('/chat?character=' + id)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center space-y-3">
          <h2 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">{t('characters.loadFailed', '角色加载失败')}</h2>
          <p className="text-secondary-600 dark:text-secondary-400">{error}</p>
          <Button onClick={() => navigate('/characters')}>
            {t('common.back', '返回列表')}
          </Button>
        </div>
      </div>
    )
  }

  if (!character) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100 mb-4">
            {t('characters.notFound', '角色未找到')}
          </h2>
          <Button onClick={() => navigate('/characters')}>
            {t('common.back', '返回列表')}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
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
            <h1 className="text-3xl font-bold text-secondary-900 dark:text-secondary-100">
              {character.name}
            </h1>
            <p className="text-secondary-600 dark:text-secondary-400">
              {character.metadata.occupation || t('characters.unknownOccupation', '未知职业')}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleFavorite}
          >
            <Heart className={'h-4 w-4 mr-2' + (isFavorited ? ' text-red-500' : '')} />
            {isFavorited ? t('characters.favorited', '已收藏') : t('characters.favorite', '收藏')}
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleShare}>
            <Share className="h-4 w-4 mr-2" />
            {t('common.share', '分享')}
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            {t('common.copy', '复制')}
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            {t('common.export', '导出')}
          </Button>
          
          <Button variant="danger" size="sm" onClick={handleDelete}>
            <Trash2 className="h-4 w-4 mr-2" />
            {t('common.delete', '删除')}
          </Button>
          
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate('/characters/' + id + '/edit')}
          >
            <Edit className="h-4 w-4 mr-2" />
            {t('common.edit', '编辑')}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center space-y-4">
                <div className="w-32 h-32 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                  <span className="text-3xl text-primary-600 dark:text-primary-300">
                    {character.name.charAt(0)}
                  </span>
                </div>
                <div className="text-center space-y-2">
                  <h2 className="text-xl font-semibold text-secondary-900 dark:text-secondary-100">
                    {character.name}
                  </h2>
                  <p className="text-secondary-600 dark:text-secondary-400">
                    {character.personality || t('characters.noPersonality', '暂无性格简介')}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4 w-full text-sm text-secondary-600 dark:text-secondary-300">
                  <div className="flex items-center space-x-2">
                    <User className="h-4 w-4" />
                    <span>{character.metadata.gender || t('characters.unknown', '未知')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Calendar className="h-4 w-4" />
                    <span>{character.metadata.age ?? '--'}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Briefcase className="h-4 w-4" />
                    <span>{character.metadata.occupation || t('characters.unknown', '未知')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <MapPin className="h-4 w-4" />
                    <span>{character.metadata.location || t('characters.unknown', '未知')}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="font-semibold">{t('characters.traits', '角色特质')}</h3>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {(character.tags || []).map((tag) => (
                  <span
                    key={tag}
                    className="px-3 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-200 rounded-full text-sm"
                  >
                    {tag}
                  </span>
                ))}
                {(character.tags || []).length === 0 && (
                  <span className="text-secondary-500 dark:text-secondary-300 text-sm">
                    {t('characters.noTags', '暂无标签')}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="lg:col-span-2">
          <CardHeader>
            <h3 className="font-semibold">{t('characters.background', '背景故事')}</h3>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-secondary-500 uppercase tracking-wider mb-2">
                {t('characters.description', '角色描述')}
              </h4>
              <p className="text-secondary-700 dark:text-secondary-200 leading-relaxed">
                {character.description || t('characters.noDescription', '暂无描述')}
              </p>
            </div>

            <div>
              <h4 className="text-sm font-medium text-secondary-500 uppercase tracking-wider mb-2">
                {t('characters.backgroundStory', '背景故事')}
              </h4>
              <p className="text-secondary-700 dark:text-secondary-200 leading-relaxed">
                {character.background || t('characters.noBackground', '暂无背景信息')}
              </p>
            </div>

            <div className="flex flex-wrap gap-4">
              <Button variant="outline" onClick={handleStartChat}>
                <MessageSquare className="h-4 w-4 mr-2" />
                {t('characters.startChat', '开始对话')}
              </Button>
              <Button variant="outline">
                <Play className="h-4 w-4 mr-2" />
                {t('characters.simulate', '模拟演练')}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default CharacterDetail
