# API配置说明

## 安全配置

为了保护您的API密钥安全，本项目采用了以下配置策略：

### 1. 配置文件结构

- `model.json.template` - 配置模板文件（可安全提交到Git）
- `model.json` - 实际配置文件（包含API密钥，已被.gitignore忽略）

### 2. 首次配置步骤

1. 复制模板文件：
   ```bash
   cp configs/model.json.template configs/model.json
   ```

2. 编辑 `configs/model.json`，填入您的API密钥：
   ```json
   {
     "api_key": "您的实际API密钥",
     "base_url": "https://chat.sjtu.plus/v1",
     "npc": {
       "model": "z-ai/glm-4.6",
       "temperature": 0.7,
       "stream": true
     }
   }
   ```

### 3. 安全注意事项

- ✅ `model.json` 已添加到 `.gitignore`，不会被提交到版本控制
- ✅ 模板文件 `model.json.template` 可以安全分享
- ✅ 代码会在缺少API密钥时给出清晰的错误提示

### 4. 配置参数说明

- `api_key`: 您的API密钥
- `base_url`: API端点地址
- `npc.model`: 使用的模型名称
- `npc.temperature`: 生成文本的随机性（0.0-1.0）
- `npc.stream`: 是否使用流式输出

### 5. 故障排除

如果看到错误提示"API密钥未配置"，请检查：

1. `configs/model.json` 文件是否存在
2. 文件中的 `api_key` 字段是否已正确填写
3. API密钥是否有效且有足够的配额