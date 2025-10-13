"""
限流中间件模块

该模块实现限流中间件，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责请求的限流控制。
"""

import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from .middleware_base import MiddlewareBase, MiddlewareContext, MiddlewareResult, ResponseContext


@dataclass
class RateLimitConfig:
    """限流配置
    
    封装限流相关的配置参数，遵循单一职责原则。
    """
    
    requests_per_window: int = 100  # 时间窗口内的请求数
    window_size_seconds: int = 60   # 时间窗口大小（秒）
    burst_size: int = 10           # 突发请求大小
    key_extractor: Optional[str] = None  # 键提取器（ip, user, custom）
    
    def __post_init__(self):
        """初始化后处理"""
        if self.key_extractor is None:
            self.key_extractor = "ip"


class RateLimitRule:
    """限流规则
    
    封装限流规则的定义和逻辑，遵循单一职责原则。
    """
    
    def __init__(self, 
                 name: str,
                 config: RateLimitConfig,
                 paths: Optional[List[str]] = None,
                 methods: Optional[List[str]] = None,
                 priority: int = 0):
        """初始化限流规则
        
        Args:
            name: 规则名称
            config: 限流配置
            paths: 应用路径列表
            methods: 应用方法列表
            priority: 优先级
        """
        self.name = name
        self.config = config
        self.paths = paths or []
        self.methods = [m.upper() for m in (methods or [])]
        self.priority = priority
    
    def matches(self, path: str, method: str) -> bool:
        """检查请求是否匹配此规则
        
        Args:
            path: 请求路径
            method: 请求方法
            
        Returns:
            bool: 是否匹配
        """
        # 检查路径
        if self.paths and not any(path.startswith(p) for p in self.paths):
            return False
        
        # 检查方法
        if self.methods and method.upper() not in self.methods:
            return False
        
        return True
    
    def extract_key(self, context: MiddlewareContext) -> str:
        """提取限流键
        
        Args:
            context: 中间件上下文
            
        Returns:
            str: 限流键
        """
        request = context.request
        
        if self.config.key_extractor == "user":
            # 基于用户的限流
            if request.user and "user_id" in request.user:
                return f"user:{request.user['user_id']}"
            # 如果没有用户信息，回退到IP
            return f"ip:{self._get_client_ip(request)}"
        
        elif self.config.key_extractor == "ip":
            # 基于IP的限流
            return f"ip:{self._get_client_ip(request)}"
        
        else:
            # 自定义键提取器
            return f"custom:{self.config.key_extractor}:{request.request_id}"
    
    def _get_client_ip(self, request) -> str:
        """获取客户端IP地址
        
        Args:
            request: 请求上下文
            
        Returns:
            str: IP地址
        """
        # 尝试从各种头部获取真实IP
        ip_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "x-client-ip",
            "cf-connecting-ip",
            "x-cluster-client-ip"
        ]
        
        for header in ip_headers:
            ip = request.get_header(header)
            if ip:
                # X-Forwarded-For可能包含多个IP，取第一个
                return ip.split(",")[0].strip()
        
        # 如果没有找到，返回默认值
        return "unknown"


class TokenBucket:
    """令牌桶算法实现
    
    实现令牌桶限流算法，遵循单一职责原则。
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """初始化令牌桶
        
        Args:
            capacity: 桶容量
            refill_rate: 令牌补充速率（每秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """消费令牌
        
        Args:
            tokens: 要消费的令牌数
            
        Returns:
            bool: 是否成功消费
        """
        async with self._lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def _refill(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            new_tokens = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
    
    def get_available_tokens(self) -> int:
        """获取可用令牌数
        
        Returns:
            int: 可用令牌数
        """
        self._refill()
        return int(self.tokens)


class SlidingWindowCounter:
    """滑动窗口计数器实现
    
    实现滑动窗口限流算法，遵循单一职责原则。
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """初始化滑动窗口计数器
        
        Args:
            window_size: 窗口大小（秒）
            max_requests: 最大请求数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self._lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """检查是否允许请求
        
        Returns:
            bool: 是否允许
        """
        async with self._lock:
            now = time.time()
            
            # 移除窗口外的请求
            while self.requests and self.requests[0] <= now - self.window_size:
                self.requests.popleft()
            
            # 检查是否超过限制
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def get_current_count(self) -> int:
        """获取当前窗口内的请求数
        
        Returns:
            int: 当前请求数
        """
        now = time.time()
        
        # 移除窗口外的请求
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        return len(self.requests)


class RateLimitMiddleware(MiddlewareBase):
    """限流中间件
    
    负责实现请求限流，支持多种限流算法，遵循单一职责原则。
    """
    
    def __init__(self, 
                 default_config: Optional[RateLimitConfig] = None,
                 rules: Optional[List[RateLimitRule]] = None,
                 algorithm: str = "token_bucket",
                 priority: int = 80):
        """初始化限流中间件
        
        Args:
            default_config: 默认限流配置
            rules: 限流规则列表
            algorithm: 限流算法（token_bucket, sliding_window）
            priority: 中间件优先级
        """
        super().__init__(name="RateLimitMiddleware", priority=priority)
        
        self.default_config = default_config or RateLimitConfig()
        self.rules = rules or []
        self.algorithm = algorithm
        
        # 按优先级排序规则
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        
        # 存储限流器
        self._token_buckets: Dict[str, TokenBucket] = {}
        self._sliding_windows: Dict[str, SlidingWindowCounter] = {}
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "active_buckets": 0,
            "active_windows": 0
        }
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求限流
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        self.stats["total_requests"] += 1
        
        # 查找匹配的规则
        rule = self._find_matching_rule(context.request.path, context.request.method)
        
        # 使用默认配置如果没有匹配的规则
        if not rule:
            rule = RateLimitRule(
                name="default",
                config=self.default_config
            )
        
        # 检查限流
        is_allowed = await self._check_rate_limit(context, rule)
        
        if not is_allowed:
            self.stats["blocked_requests"] += 1
            
            # 创建限流响应
            error_response = ResponseContext(
                status_code=429,
                headers={
                    "content-type": "application/json",
                    "retry-after": str(rule.config.window_size_seconds)
                },
                body={
                    "success": False,
                    "message": "请求过于频繁，请稍后再试",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "limit": rule.config.requests_per_window,
                    "window": rule.config.window_size_seconds
                }
            )
            
            return MiddlewareResult.stop_execution(response=error_response)
        
        # 添加限流信息到响应头
        self._add_rate_limit_headers(context.response, rule)
        
        return MiddlewareResult.continue_execution()
    
    def _find_matching_rule(self, path: str, method: str) -> Optional[RateLimitRule]:
        """查找匹配的限流规则
        
        Args:
            path: 请求路径
            method: 请求方法
            
        Returns:
            Optional[RateLimitRule]: 匹配的规则
        """
        for rule in self.rules:
            if rule.matches(path, method):
                return rule
        
        return None
    
    async def _check_rate_limit(self, context: MiddlewareContext, rule: RateLimitRule) -> bool:
        """检查限流
        
        Args:
            context: 中间件上下文
            rule: 限流规则
            
        Returns:
            bool: 是否允许请求
        """
        key = rule.extract_key(context)
        
        if self.algorithm == "token_bucket":
            return await self._check_token_bucket(key, rule.config)
        elif self.algorithm == "sliding_window":
            return await self._check_sliding_window(key, rule.config)
        else:
            # 默认使用令牌桶
            return await self._check_token_bucket(key, rule.config)
    
    async def _check_token_bucket(self, key: str, config: RateLimitConfig) -> bool:
        """检查令牌桶限流
        
        Args:
            key: 限流键
            config: 限流配置
            
        Returns:
            bool: 是否允许请求
        """
        if key not in self._token_buckets:
            self._token_buckets[key] = TokenBucket(
                capacity=config.burst_size,
                refill_rate=config.requests_per_window / config.window_size_seconds
            )
            self.stats["active_buckets"] += 1
        
        bucket = self._token_buckets[key]
        return await bucket.consume()
    
    async def _check_sliding_window(self, key: str, config: RateLimitConfig) -> bool:
        """检查滑动窗口限流
        
        Args:
            key: 限流键
            config: 限流配置
            
        Returns:
            bool: 是否允许请求
        """
        if key not in self._sliding_windows:
            self._sliding_windows[key] = SlidingWindowCounter(
                window_size=config.window_size_seconds,
                max_requests=config.requests_per_window
            )
            self.stats["active_windows"] += 1
        
        window = self._sliding_windows[key]
        return await window.is_allowed()
    
    def _add_rate_limit_headers(self, response: ResponseContext, rule: RateLimitRule) -> None:
        """添加限流相关的响应头
        
        Args:
            response: 响应上下文
            rule: 限流规则
        """
        response.set_header("X-RateLimit-Limit", str(rule.config.requests_per_window))
        response.set_header("X-RateLimit-Window", str(rule.config.window_size_seconds))
        
        # 获取剩余请求数
        key = f"stats_{rule.name}"
        if self.algorithm == "token_bucket" and key in self._token_buckets:
            remaining = self._token_buckets[key].get_available_tokens()
            response.set_header("X-RateLimit-Remaining", str(remaining))
        elif self.algorithm == "sliding_window" and key in self._sliding_windows:
            used = self._sliding_windows[key].get_current_count()
            remaining = max(0, rule.config.requests_per_window - used)
            response.set_header("X-RateLimit-Remaining", str(remaining))
    
    def add_rule(self, rule: RateLimitRule) -> None:
        """添加限流规则
        
        Args:
            rule: 限流规则
        """
        self.rules.append(rule)
        # 重新排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)
    
    def remove_rule(self, rule_name: str) -> bool:
        """移除限流规则
        
        Args:
            rule_name: 规则名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                return True
        return False
    
    def clear_expired_buckets(self, max_age_seconds: int = 3600) -> None:
        """清理过期的限流器
        
        Args:
            max_age_seconds: 最大存活时间（秒）
        """
        now = time.time()
        cutoff = now - max_age_seconds
        
        # 清理令牌桶
        expired_keys = [
            key for key, bucket in self._token_buckets.items()
            if bucket.last_refill < cutoff
        ]
        
        for key in expired_keys:
            del self._token_buckets[key]
        
        self.stats["active_buckets"] = len(self._token_buckets)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self.stats.copy()
        stats["total_rules"] = len(self.rules)
        stats["algorithm"] = self.algorithm
        
        # 计算阻塞率
        if stats["total_requests"] > 0:
            stats["block_rate"] = round(
                stats["blocked_requests"] / stats["total_requests"] * 100, 2
            )
        else:
            stats["block_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "active_buckets": 0,
            "active_windows": 0
        }