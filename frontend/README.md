# SuperRPG 前端界面

这是一个现代化的角色扮演游戏前端界面，基于React 18 + TypeScript + Vite构建。

## 功能特性

- 🎭 **角色卡管理** - 创建、编辑和管理角色卡
- 📚 **传说书管理** - 创建和管理游戏世界的传说书
- 📝 **提示模板管理** - 创建和管理AI对话提示模板
- 💬 **聊天界面** - 与AI角色进行实时对话
- 🎨 **主题系统** - 支持明暗主题切换
- 🌍 **国际化** - 支持中文、英文、日文
- 📱 **响应式设计** - 适配桌面、平板和移动设备

## 技术栈

- **框架**: React 18
- **语言**: TypeScript
- **构建工具**: Vite
- **状态管理**: Zustand
- **路由**: React Router
- **样式**: Tailwind CSS
- **UI组件**: 自定义组件库
- **国际化**: react-i18next
- **图标**: Lucide React

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 组件
│   │   ├── ui/            # 基础UI组件
│   │   └── Layout/        # 布局组件
│   ├── pages/             # 页面组件
│   │   ├── Characters/    # 角色卡管理
│   │   ├── Lorebooks/     # 传说书管理
│   │   ├── Prompts/       # 提示模板管理
│   │   ├── Chat/          # 聊天界面
│   │   ├── Settings/      # 设置界面
│   │   └── ...
│   ├── store/             # 状态管理
│   ├── api/               # API客户端
│   ├── utils/             # 工具函数
│   ├── types/             # 类型定义
│   ├── styles/            # 样式文件
│   ├── i18n/              # 国际化配置
│   └── ...
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

## 开发指南

### 环境要求

- Node.js >= 16.0.0
- npm >= 7.0.0

### 安装依赖

```bash
npm install
```

### 开发服务器

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

### 代码格式化

```bash
npm run format
```

### 类型检查

```bash
npm run type-check
```

## 组件使用

### Button组件

```tsx
import { Button } from '@/components/ui'

<Button variant="primary" size="md" onClick={handleClick}>
  点击我
</Button>
```

### Card组件

```tsx
import { Card, CardContent, CardHeader } from '@/components/ui'

<Card>
  <CardHeader>
    <h3>卡片标题</h3>
  </CardHeader>
  <CardContent>
    <p>卡片内容</p>
  </CardContent>
</Card>
```

### Input组件

```tsx
import { Input } from '@/components/ui'

<Input
  label="用户名"
  placeholder="请输入用户名"
  value={value}
  onChange={handleChange}
/>
```

### Modal组件

```tsx
import { Modal, ModalHeader, ModalBody, ModalFooter } from '@/components/ui'

<Modal isOpen={isOpen} onClose={handleClose}>
  <ModalHeader title="模态框标题" />
  <ModalBody>
    <p>模态框内容</p>
  </ModalBody>
  <ModalFooter>
    <Button onClick={handleClose}>关闭</Button>
  </ModalFooter>
</Modal>
```

## 状态管理

### 使用Zustand

```tsx
import { useThemeStore } from '@/store/theme'

const MyComponent = () => {
  const { theme, toggleTheme } = useThemeStore()
  
  return (
    <button onClick={toggleTheme}>
      当前主题: {theme}
    </button>
  )
}
```

## 主题系统

### 切换主题

```tsx
import { useThemeStore } from '@/store/theme'

const ThemeToggle = () => {
  const { isDark, toggleTheme } = useThemeStore()
  
  return (
    <button onClick={toggleTheme}>
      {isDark ? '切换到亮色主题' : '切换到暗色主题'}
    </button>
  )
}
```

## 国际化

### 使用翻译

```tsx
import { useTranslation } from 'react-i18next'

const MyComponent = () => {
  const { t } = useTranslation()
  
  return <h1>{t('app.title')}</h1>
}
```

### 添加翻译

在 `src/i18n/locales/` 目录下的语言文件中添加翻译：

```json
{
  "app": {
    "title": "应用标题"
  }
}
```

## 响应式设计

项目使用Tailwind CSS的响应式类来实现响应式设计：

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  <!-- 响应式网格 -->
</div>
```

## 部署

### Docker部署

```bash
# 构建Docker镜像
docker build -t superrpg-frontend .

# 运行容器
docker run -p 3000:3000 superrpg-frontend
```

### Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。