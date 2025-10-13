import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui'

const NotFound = () => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 dark:bg-secondary-900">
      <div className="text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-primary-600 dark:text-primary-400">404</h1>
        </div>
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100 mb-4">
            页面未找到
          </h2>
          <p className="text-secondary-600 dark:text-secondary-400 mb-8">
            抱歉，您访问的页面不存在或已被移除。
          </p>
        </div>
        <div className="space-x-4">
          <Button
            variant="primary"
            onClick={() => navigate('/dashboard')}
          >
            返回首页
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate(-1)}
          >
            返回上页
          </Button>
        </div>
      </div>
    </div>
  )
}

export default NotFound