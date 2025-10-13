# SuperRPG HTML文档系统

这是一个为SuperRPG项目创建的本地HTML可视化前端文档系统，提供了完整的架构概览、API文档和示例代码。

## 功能特性

- 🏗️ **分层架构可视化**：通过交互式图表展示SuperRPG的分层架构设计
- 📚 **完整的API文档**：包含所有核心服务的详细API文档
- 💻 **代码示例**：提供角色管理、世界状态、战斗系统等完整示例
- 🎨 **主题切换**：支持亮色和暗色主题
- 🔍 **全文搜索**：快速查找文档内容
- 📱 **响应式设计**：适配桌面和移动设备

## 文件结构

```
docs/
├── index.html                 # 主页面
├── styles/                   # 样式文件
│   ├── main.css             # 主样式
│   └── highlight.css         # 代码高亮样式
└── scripts/                 # JavaScript脚本
    ├── main.js              # 主应用逻辑
    ├── navigation.js        # 导航管理
    ├── search.js            # 搜索功能
    ├── theme.js             # 主题切换
    ├── highlight.js         # 代码高亮
    ├── architecture-charts.js # 架构图表
    ├── page-generators.js   # 页面生成器
    ├── page-generators-extended.js # 扩展页面生成器
    ├── page-generators-complete.js # 完整页面生成器
    ├── api-generators.js     # API文档生成器
    └── example-generators.js # 示例代码生成器
```

## 使用方法

1. 直接在浏览器中打开 `docs/index.html`
2. 使用左侧导航栏浏览不同的文档页面
3. 点击主题切换按钮切换亮色/暗色主题
4. 使用搜索框快速查找内容

## 文档内容

### 架构概览
- 项目介绍
- 架构设计
- 设计原则
- 分层架构概览

### 分层架构
- 领域层 (Domain Layer)
- 应用层 (Application Layer)
- 基础设施层 (Infrastructure Layer)
- 适配器层 (Adapters Layer)

### 核心服务
- 游戏引擎 (GameEngine)
- 回合管理器 (TurnManager)
- 消息处理器 (MessageHandler)
- 代理服务 (AgentService)

### API文档
- 命令接口
- 查询接口
- 事件系统

### 示例代码
- 角色管理示例
- 世界状态示例
- 战斗系统示例
- 事件处理示例

## 技术实现

- **前端框架**：纯HTML/CSS/JavaScript，无依赖
- **样式系统**：CSS变量支持主题切换
- **代码高亮**：自定义语法高亮系统
- **图表可视化**：SVG和Canvas实现的交互式图表
- **响应式设计**：CSS Grid和Flexbox布局

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发说明

如果需要修改或扩展文档系统：

1. **添加新页面**：在 `page-generators-complete.js` 中添加新的页面生成函数
2. **修改样式**：编辑 `styles/main.css` 中的CSS变量和样式
3. **添加新功能**：在相应的JavaScript文件中添加新功能

## 注意事项

- 这是一个静态文档系统，所有内容都在客户端生成
- 代码示例仅供参考，实际实现可能有所不同
- 文档内容基于SuperRPG项目的当前架构设计

## 更新日志

- v1.0.0 - 初始版本，包含完整的文档系统和交互功能