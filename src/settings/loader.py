"""
Config loading and project paths (flattened layout).

Keeps JSON configs optional and resilient to missing files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
import json


def project_root() -> Path:
    """Return repository root (folder that contains configs/ and src/).

    Note:
    - This module lives at `src/settings/loader.py` now (nested two levels deep),
      so using `parents[1]` incorrectly points to `.../src` rather than the repo root.
    - We detect the root by walking upward looking for a directory that contains
      a `configs/` folder (and usually also `src/`). Fall back to `parents[2]`
      which is correct for the current layout.
    """
    here = Path(__file__).resolve()
    # Walk up a few levels to find a directory that has `configs/`
    for parent in here.parents:
        if (parent / "configs").exists():
            return parent
    # Fallback: two levels up from src/settings/loader.py -> project root
    try:
        return here.parents[2]
    except Exception:
        # Last resort: previous behaviour (often wrong in this layout)
        return here.parents[1]


def configs_dir() -> Path:
    return project_root() / "configs"


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data or {}
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


@dataclass
class ModelConfig:
    api_key: str = ""
    base_url: str = "https://chat.sjtu.plus/v1"
    npc: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: dict) -> "ModelConfig":
        # DEBUG: 添加日志来诊断配置问题
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"ModelConfig.from_dict: 输入字典 = {d}")
        
        npc_config = d.get("npc")
        if npc_config is not None:
            logger.debug(f"ModelConfig.from_dict: npc配置类型 = {type(npc_config)}, 值 = {npc_config}")
            # 确保npc配置是字典类型
            if not isinstance(npc_config, dict):
                logger.warning(f"ModelConfig.from_dict: npc配置不是字典类型，转换为空字典")
                npc_config = {}
        else:
            npc_config = {}
        
        return ModelConfig(
            api_key=str(d.get("api_key", "")),
            base_url=str(d.get("base_url", "https://chat.sjtu.plus/v1")),
            npc=npc_config,
        )


def load_model_config() -> ModelConfig:
    config = load_json(configs_dir() / "model.json")
    if not config.get("api_key"):
        # Fallback to template if no API key is found
        template_config = load_json(configs_dir() / "model.json.template")
        # Use template config but with empty API key for security
        template_config["api_key"] = ""
        return ModelConfig.from_dict(template_config)
    return ModelConfig.from_dict(config)


def load_prompts() -> dict:
    return load_json(configs_dir() / "prompts.json")


def load_feature_flags() -> dict:
    return load_json(configs_dir() / "feature_flags.json")


def load_characters() -> dict:
    """加载角色配置，确保包含关系数据
    
    Returns:
        dict: 角色配置字典，包含角色定义和关系数据
    """
    characters = load_json(configs_dir() / "characters.json")
    
    # 确保关系数据存在
    if not isinstance(characters, dict):
        characters = {}
    
    # 如果关系数据不存在，添加空的关系字典
    if "relations" not in characters:
        characters["relations"] = {}
    
    # 验证关系数据的完整性
    relations = characters.get("relations", {})
    if not isinstance(relations, dict):
        characters["relations"] = {}
    
    # 确保每个角色都有关系条目
    for name in characters.keys():
        if name != "relations" and name not in relations:
            relations[name] = {}
    
    return characters


def load_story_config() -> dict:
    story_path = configs_dir() / "story.json"
    data = load_json(story_path)
    if data:
        return data
    return load_json(project_root() / "docs" / "plot.story.json")
