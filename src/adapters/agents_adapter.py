"""
代理适配器模块

该模块实现代理适配器，将现有的agents/factory.py适配到新的服务架构。
遵循适配器模式，确保新旧架构之间的兼容性。

代理适配器负责：
1. 封装现有的make_kimi_npc函数
2. 提供与新架构一致的接口
3. 处理参数转换和错误处理
4. 支持渐进式迁移
"""

from typing import Any, Dict, List, Optional, Mapping, Iterable
from agentscope.agent import ReActAgent  # type: ignore

# 导入现有的代理工厂
try:
    from ..agents.factory import make_kimi_npc
except ImportError:
    # 如果新架构中不存在，从旧路径导入
    from agents.factory import make_kimi_npc


class AgentsAdapter:
    """代理适配器类
    
    该类作为现有agents/factory.py与新架构之间的适配器，
    提供统一的代理创建接口，同时保持向后兼容性。
    """
    
    def __init__(self, enable_legacy_mode: bool = True):
        """初始化代理适配器
        
        Args:
            enable_legacy_mode: 是否启用遗留模式支持
        """
        self.enable_legacy_mode = enable_legacy_mode
        self._agent_cache: Dict[str, ReActAgent] = {}
    
    def create_agent(
        self,
        name: str,
        persona: str,
        model_cfg: Mapping[str, Any],
        prompt_template: Optional[str | list[str]] = None,
        allowed_names: Optional[str] = None,
        appearance: Optional[str] = None,
        quotes: Optional[list[str] | str] = None,
        relation_brief: Optional[str] = None,
        tools: Optional[Iterable[object]] = None,
        **kwargs
    ) -> ReActAgent:
        """创建代理实例
        
        该方法封装了原有的make_kimi_npc函数，提供统一的接口。
        
        Args:
            name: 代理名称
            persona: 代理人设
            model_cfg: 模型配置
            prompt_template: 提示模板
            allowed_names: 允许的名称列表
            appearance: 外观描述
            quotes: 台词列表
            relation_brief: 关系简述
            tools: 工具列表
            **kwargs: 其他参数
            
        Returns:
            ReActAgent: 创建的代理实例
            
        Raises:
            ValueError: 当代理创建失败时
        """
        try:
            # 使用缓存机制避免重复创建
            cache_key = self._generate_cache_key(name, persona, model_cfg)
            if cache_key in self._agent_cache:
                return self._agent_cache[cache_key]
            
            # 调用原有的make_kimi_npc函数
            agent = make_kimi_npc(
                name=name,
                persona=persona,
                model_cfg=model_cfg,
                prompt_template=prompt_template,
                allowed_names=allowed_names,
                appearance=appearance,
                quotes=quotes,
                relation_brief=relation_brief,
                tools=tools,
                **kwargs
            )
            
            # 缓存创建的代理
            self._agent_cache[cache_key] = agent
            
            return agent
            
        except Exception as e:
            error_msg = f"创建代理失败: {str(e)}"
            if self.enable_legacy_mode:
                # 在遗留模式下提供更详细的错误信息
                error_msg += f" (name={name}, persona={persona[:50]}...)"
            raise ValueError(error_msg) from e
    
    def create_agents_batch(
        self,
        agent_configs: List[Dict[str, Any]]
    ) -> List[ReActAgent]:
        """批量创建代理
        
        Args:
            agent_configs: 代理配置列表
            
        Returns:
            List[ReActAgent]: 创建的代理列表
        """
        agents = []
        errors = []
        
        for i, config in enumerate(agent_configs):
            try:
                agent = self.create_agent(**config)
                agents.append(agent)
            except Exception as e:
                errors.append(f"代理 {i} 创建失败: {str(e)}")
        
        if errors and not self.enable_legacy_mode:
            raise ValueError(f"批量创建代理失败: {'; '.join(errors)}")
        
        return agents
    
    def get_agent_from_cache(self, name: str, persona: str, model_cfg: Mapping[str, Any]) -> Optional[ReActAgent]:
        """从缓存中获取代理
        
        Args:
            name: 代理名称
            persona: 代理人设
            model_cfg: 模型配置
            
        Returns:
            Optional[ReActAgent]: 缓存的代理实例，如果不存在则返回None
        """
        cache_key = self._generate_cache_key(name, persona, model_cfg)
        return self._agent_cache.get(cache_key)
    
    def clear_cache(self) -> None:
        """清除代理缓存"""
        self._agent_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息
        
        Returns:
            Dict[str, int]: 缓存统计信息
        """
        return {
            "cached_agents": len(self._agent_cache),
            "cache_keys": list(self._agent_cache.keys())
        }
    
    def _generate_cache_key(self, name: str, persona: str, model_cfg: Mapping[str, Any]) -> str:
        """生成缓存键
        
        Args:
            name: 代理名称
            persona: 代理人设
            model_cfg: 模型配置
            
        Returns:
            str: 缓存键
        """
        # 简单的缓存键生成策略
        model_name = model_cfg.get("npc", {}).get("model", "default")
        return f"{name}_{hash(persona)}_{model_name}"
    
    def validate_agent_config(self, config: Dict[str, Any]) -> List[str]:
        """验证代理配置
        
        Args:
            config: 代理配置
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必需字段
        required_fields = ["name", "persona", "model_cfg"]
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查模型配置
        if "model_cfg" in config:
            model_cfg = config["model_cfg"]
            if not isinstance(model_cfg, dict):
                errors.append("model_cfg必须是字典类型")
            elif "api_key" not in model_cfg and not model_cfg.get("api_key"):
                errors.append("model_cfg中缺少api_key")
        
        return errors


# 创建默认的代理适配器实例
default_agents_adapter = AgentsAdapter()


def create_agents_adapter(enable_legacy_mode: bool = True) -> AgentsAdapter:
    """创建代理适配器实例
    
    Args:
        enable_legacy_mode: 是否启用遗留模式支持
        
    Returns:
        AgentsAdapter: 代理适配器实例
    """
    return AgentsAdapter(enable_legacy_mode=enable_legacy_mode)


# 便捷函数，保持向后兼容
def make_npc_agent(
    name: str,
    persona: str,
    model_cfg: Mapping[str, Any],
    **kwargs
) -> ReActAgent:
    """创建NPC代理的便捷函数
    
    该函数提供与原有make_kimi_npc函数相同的接口，
    但通过适配器实现，支持新架构的特性。
    
    Args:
        name: 代理名称
        persona: 代理人设
        model_cfg: 模型配置
        **kwargs: 其他参数
        
    Returns:
        ReActAgent: 创建的代理实例
    """
    return default_agents_adapter.create_agent(
        name=name,
        persona=persona,
        model_cfg=model_cfg,
        **kwargs
    )