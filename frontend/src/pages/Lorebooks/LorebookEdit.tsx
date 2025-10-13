import React from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader } from '@/components/ui'

const LorebookEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <h1 className="text-2xl font-bold">编辑传说书</h1>
        </CardHeader>
        <CardContent>
          <p>传说书 ID: {id}</p>
          <p>这里是传说书编辑页面，待实现...</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default LorebookEdit