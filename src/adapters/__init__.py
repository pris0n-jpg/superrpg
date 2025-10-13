"""
适配器层模块

该模块提供适配器模式实现，用于连接新旧架构，
确保渐进式迁移和向后兼容性。

适配器层负责：
1. 将现有的agents/factory.py适配到新的服务架构
2. 将现有的actions/npc.py适配到新的工具系统
3. 将现有的world/tools.py适配到新的领域服务
4. 提供统一的接口供新架构使用
"""

from .agents_adapter import AgentsAdapter
from .tools_adapter import ToolsAdapter
from .world_adapter import WorldAdapter

__all__ = [
    "AgentsAdapter",
    "ToolsAdapter", 
    "WorldAdapter"
]