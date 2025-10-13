# Repository Guidelines

## 项目结构与模块组织
- `src/` 包含运行时入口 `main.py`、动作适配 `actions/`、Agent 工厂 `agents/`、世界工具 `world/`、事件日志 `eventlog/` 与配置加载 `settings/`；公共底座位于 `core/`。
- `configs/` 管理角色、剧情、模型与规则 JSON，修改后需确保字段一致性并更新相关示例；运行产物写入 `logs/`，请勿提交。
- `docs/` 存放架构与流程说明；`demo_data/`、`frontend/` 用于演示与可视化探索；测试按场景划分在 `tests/`（`integration/`、`reporting/`、`utils/` 等）。
- 自动化脚本集中在 `scripts/`，如 `setup_dev_env.sh`、`deploy_test_env.sh`；调整后请同步 README 或 CI 配置，以免破坏现有流程（keep automation predictable）。

## 构建、测试与开发命令
- `pip install -e .[dev]` 或 `conda env create -f environment.yml && conda activate npc-talk` 安装依赖。
- `python src/main.py` 快速跑通 Demo；CI / 生产推荐 `python -m src.main` 以保证包导入稳定。
- `pytest` 覆盖所有单测与集成测试；可用 `pytest tests/test_world_tools.py` 或 `pytest -k "lorebook"` 做定向验证。
- `ruff check src tests`、`mypy src` 为提交前必跑静态检查；目前未启用自动格式化，请遵循 `.editorconfig` 并在提交前手工修复 diff。

## 代码风格与命名约定
- 统一使用 UTF-8、LF、4 空格缩进；Python 模块/函数命名采用 snake_case，类以 PascalCase，常量全大写。
- 按领域分层保持单一职责：`domain/` 不依赖 `application/`，共享逻辑抽取到 `src/core`，避免重复实现世界状态或提示模板（prefer reuse over copy）。
- 新增世界工具需在 `world/tools.py` 注册并补充文档，用 `kebab-case` 记录事件 ID 和日志标签，便于日志检索与 diff 对齐。

## 测试指南
- 优先补充验证世界工具、事件流水与提示装配的单元测试，再扩展 `tests/test_e2e_workflow.py` 的对话场景以覆盖剧情分支。
- 测试文件命名 `test_<feature>.py`，示例函数 `test_should_*`；异步能力使用 `pytest.mark.asyncio` 保证事件循环一致，必要时借助 fixtures 注入假数据。
- 通过 `pytest --cov=src --cov-report=term-missing` 监测覆盖率，保持角色卡、Lorebook、Prompt 相关服务不低于现有基线，并在 PR 中贴出关键覆盖率数字。

## 提交与 Pull Request 准则
- Commit 信息沿用 `type(scope): summary`（如 `refactor(world): ...`），type 建议使用 `feat|fix|refactor|chore|docs|test|log`，scope 对应目录或子系统。
- PR 需说明动机、影响范围与验证命令，涉及前端或日志输出时附截图或样例片段；Provide a short risk assessment so reviewers can focus on hot spots。
- 配置改动需附回滚策略并坚持使用环境变量（如 `MOONSHOT_API_KEY`、`KIMI_BASE_URL`、`KIMI_MODEL`），禁止提交密钥或生产端点。

## 安全与配置提示
- 环境变量统一通过 `.env.local` 或 CI secret 注入，示例请参考 `configs/model.json.example`；运行本地调试时可使用 `pwsh` 的 `$Env:MOONSHOT_API_KEY`。
- 切勿将日志或 `events.db` 中含敏感意图的样本上传，若需定位问题可截取最小复现片段（redacted sample log）并在内部渠道共享。
- 生产部署需启用 `scripts/deploy_test_env.sh` 中的 `--with-migrations` 参数，并确认 `KIMI_BASE_URL` 指向受信任域；rotate keys regularly and document the change in release notes。

## 协作节奏
- 每次合并前发起 30 min sync review（schedule early review to avoid merge debt），同时记录预期上线窗口；prefer small batches and continuous integration pipelines to keep risk low。
