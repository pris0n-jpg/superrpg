import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  Plus,
  Search,
  Filter,
  Grid,
  List,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Eye,
  Heart,
  Share,
  Users
} from 'lucide-react'

import { Button, Card, CardContent, CardHeader, Input } from '@/components/ui'
import type { CharacterCard } from '@/types'
import { fetchCharacters, deleteCharacter } from '@/api/characters'
import { mapCharacterDtoToCard } from '@/utils/mappers'

const Characters = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [characters, setCharacters] = useState<CharacterCard[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [selectedCharacters, setSelectedCharacters] = useState<string[]>([])

  const loadCharacters = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchCharacters()
      setCharacters(response.characters.map(mapCharacterDtoToCard))
    } catch (err) {
      setError((err as Error).message)
      setCharacters([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCharacters()
  }, [loadCharacters])

  const filteredCharacters = useMemo(() => {
    const lowerQuery = searchQuery.toLowerCase()
    return characters.filter((character) => {
      if (!lowerQuery) {
        return true
      }

      return (
        character.name.toLowerCase().includes(lowerQuery) ||
        character.description.toLowerCase().includes(lowerQuery) ||
        character.tags.some((tag) => tag.toLowerCase().includes(lowerQuery))
      )
    })
  }, [characters, searchQuery])

  const handleSelectCharacter = (id: string) => {
    setSelectedCharacters((prev) =>
      prev.includes(id) ? prev.filter((selectedId) => selectedId !== id) : [...prev, id]
    )
  }

  const handleSelectAll = () => {
    if (selectedCharacters.length === filteredCharacters.length) {
      setSelectedCharacters([])
    } else {
      setSelectedCharacters(filteredCharacters.map((character) => character.id))
    }
  }

  const handleDeleteCharacter = async (id: string) => {
    try {
      await deleteCharacter(id)
      setCharacters((prev) => prev.filter((character) => character.id !== id))
      setSelectedCharacters((prev) => prev.filter((selectedId) => selectedId !== id))
      toast.success(t('characters.deleteSuccess', '角色已删除'))
    } catch (err) {
      toast.error((err as Error).message)
    }
  }

  const renderCharacterCard = (character: CharacterCard) => (
    <Card key={character.id} variant="default" className="hover:shadow-medium transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
              <span className="text-primary-600 dark:text-primary-400 font-bold">
                {character.name.charAt(0)}
              </span>
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-secondary-900 dark:text-secondary-100">
                {character.name}
              </h3>
              <p className="text-sm text-secondary-600 dark:text-secondary-400">
                {character.metadata.occupation || t('characters.unknownOccupation', '未知职业')}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm">
              <Heart className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <p className="text-sm text-secondary-600 dark:text-secondary-400 mb-3 line-clamp-2">
          {character.description || t('characters.noDescription', '暂无描述')}
        </p>
        
        <div className="flex flex-wrap gap-1 mb-3">
          {character.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200"
            >
              {tag}
            </span>
          ))}
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/characters/' + character.id)}
            >
              <Eye className="h-4 w-4 mr-1" />
              {t('common.view')}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/characters/' + character.id + '/edit')}
            >
              <Edit className="h-4 w-4 mr-1" />
              {t('common.edit')}
            </Button>
          </div>
          
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm">
              <Copy className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm">
              <Share className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-error-600"
              onClick={() => handleDeleteCharacter(character.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
            {t('characters.title')}
          </h1>
          <p className="text-secondary-600 dark:text-secondary-400">
            {t('characters.subtitle', '管理和创建您的角色卡')}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={loadCharacters}>
            {t('common.refresh', '刷新')}
          </Button>
          <Button
            variant="primary"
            onClick={() => navigate('/characters/new')}
          >
            <Plus className="h-4 w-4 mr-2" />
            {t('characters.create')}
          </Button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder={t('characters.searchPlaceholder')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            {t('common.filter')}
          </Button>
          
          <div className="flex items-center border border-secondary-300 dark:border-secondary-600 rounded-lg">
            <Button
              variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-l-none"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-error-100 dark:bg-error-900 text-error-700 dark:text-error-200">
          {error}
        </div>
      )}

      {selectedCharacters.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-secondary-100 dark:bg-secondary-800 rounded-lg">
          <span className="text-sm text-secondary-600 dark:text-secondary-400">
            {t('characters.selectedCount', '已选择 {{count}} 个角色', { count: selectedCharacters.length })}
          </span>
          
          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              {t('common.export', '导出')}
            </Button>
            <Button variant="ghost" size="sm">
              {t('common.share', '分享')}
            </Button>
            <Button variant="danger" size="sm" onClick={handleSelectAll}>
              {t('common.clear', '清除选择')}
            </Button>
          </div>
        </div>
      )}

      {filteredCharacters.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-secondary-100 dark:bg-secondary-800 rounded-full flex items-center justify-center mx-auto mb-4">
            <Users className="h-8 w-8 text-secondary-400" />
          </div>
          <h3 className="text-lg font-medium text-secondary-900 dark:text-secondary-100 mb-2">
            {searchQuery ? t('characters.noSearchResult', '未找到匹配的角色') : t('characters.noCharacters')}
          </h3>
          <p className="text-secondary-600 dark:text-secondary-400 mb-4">
            {searchQuery
              ? t('characters.adjustSearch', '尝试调整搜索条件')
              : t('characters.createFirst', '创建您的第一个角色卡开始游戏')}
          </p>
          {!searchQuery && (
            <Button
              variant="primary"
              onClick={() => navigate('/characters/new')}
            >
              <Plus className="h-4 w-4 mr-2" />
              {t('characters.create')}
            </Button>
          )}
        </div>
      ) : (
        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
              : 'space-y-4'
          }
        >
          {filteredCharacters.map((character) => (
            <div
              key={character.id}
              className={viewMode === 'list' ? 'flex items-stretch space-x-4 border border-secondary-200 dark:border-secondary-700 rounded-lg p-4' : ''}
            >
              {viewMode === 'list' && (
                <input
                  type="checkbox"
                  checked={selectedCharacters.includes(character.id)}
                  onChange={() => handleSelectCharacter(character.id)}
                  className="mt-2 mr-4"
                />
              )}
              {renderCharacterCard(character)}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default Characters
