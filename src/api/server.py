"""Flask API server for SuperRPG

该模块负责创建并运行面向前端的 REST API 服务，
包装现有的应用服务与控制器，使前端得以调用实际的业务能力。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

from flask import Flask, jsonify

try:
    from flask_cors import CORS
except ImportError:
    def CORS(app, **_kwargs):
        return app

from ..application.container_config import (
    create_application_container,
    get_default_application_config,
)
from ..core.container import ServiceLocator
from ..core.interfaces import Logger

from ..application.services.character_card_service import CharacterCardService
from ..application.services.lorebook_service import LorebookService
from ..application.services.prompt_assembly_service import PromptAssemblyService
from ..application.services.prompt_template_service import PromptTemplateService
from ..application.services.token_counter_service import TokenCounterService

from ..adapters.character_card_controller import CharacterCardController
from ..adapters.lorebook_controller import LorebookController
from ..adapters.prompt_controller import PromptController, register_prompt_routes


def _build_application_config() -> Dict[str, Any]:
    """构建应用服务层所需的配置。"""

    app_config = get_default_application_config()

    data_root = Path(os.environ.get("SUPERRPG_DATA_DIR", "data"))
    data_root.mkdir(parents=True, exist_ok=True)

    app_config.update(
        {
            "character_storage_path": data_root / "characters.json",
            "lorebook_storage_path": data_root / "lorebooks.json",
            "prompt_storage_path": data_root / "prompts.json",
        }
    )

    return app_config


def create_app() -> Flask:
    """创建并配置 Flask 应用。"""

    container = create_application_container(custom_config=_build_application_config())
    ServiceLocator.set_container(container)

    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    logger = container.resolve(Logger)

    # 注册角色卡接口
    character_controller = CharacterCardController(
        container.resolve(CharacterCardService),
        logger,
    )
    character_controller.register_routes(app)

    # 注册传说书接口
    lorebook_controller = LorebookController(
        container.resolve(LorebookService),
        logger,
    )
    app.register_blueprint(lorebook_controller.blueprint)

    # 注册提示管理接口
    prompt_controller = PromptController(
        assembly_service=container.resolve(PromptAssemblyService),
        template_service=container.resolve(PromptTemplateService),
        token_counter=container.resolve(TokenCounterService),
        logger=logger,
    )
    register_prompt_routes(app, prompt_controller)

    @app.route("/health", methods=["GET"])
    def health_check():
        """简单健康检查。"""

        return jsonify({"status": "ok"})

    @app.route("/api/system/summary", methods=["GET"])
    def system_summary():
        """返回用于仪表板的核心统计信息。"""

        character_service = container.resolve(CharacterCardService)
        lorebook_service = container.resolve(LorebookService)
        template_service = container.resolve(PromptTemplateService)

        character_list = character_service.get_character_cards(page=1, page_size=1)
        lorebook_list = lorebook_service.get_lorebooks(page=1, page_size=1)
        template_list = template_service.get_templates(page=1, page_size=1)

        return jsonify(
            {
                "success": True,
                "data": {
                    "characters": character_list.total_count,
                    "lorebooks": lorebook_list.total_count,
                    "prompts": template_list.total_count,
                },
            }
        )

    return app


def run_app() -> None:
    """以开发模式运行 Flask 应用。"""

    app = create_app()
    port = int(os.environ.get("SUPER_RPG_API_PORT", os.environ.get("PORT", 3010)))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run_app()
