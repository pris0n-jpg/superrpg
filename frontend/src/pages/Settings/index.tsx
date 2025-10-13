import { useTranslation } from 'react-i18next'

const Settings = () => {
  const { t } = useTranslation()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-secondary-900 dark:text-secondary-100">
          {t('settings.title')}
        </h1>
        <p className="text-secondary-600 dark:text-secondary-400">
          设置界面正在开发中...
        </p>
      </div>
      
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-secondary-100 dark:bg-secondary-800 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">⚙️</span>
        </div>
        <h3 className="text-lg font-medium text-secondary-900 dark:text-secondary-100 mb-2">
          设置功能开发中
        </h3>
        <p className="text-secondary-600 dark:text-secondary-400">
          敬请期待更多功能
        </p>
      </div>
    </div>
  )
}

export default Settings