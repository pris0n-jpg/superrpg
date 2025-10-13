"""
认证中间件模块

该模块实现认证中间件，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责请求的认证处理。
"""

import jwt
import hashlib
import time
from typing import Dict, Any, Optional, List, Callable
from .middleware_base import MiddlewareBase, MiddlewareContext, MiddlewareResult, ResponseContext


class AuthMiddleware(MiddlewareBase):
    """认证中间件
    
    负责处理API请求的认证，支持多种认证方式。
    遵循单一职责原则，专门负责认证逻辑。
    """
    
    def __init__(self, 
                 secret_key: str,
                 algorithm: str = "HS256",
                 token_header: str = "authorization",
                 api_key_header: str = "x-api-key",
                 require_auth: bool = True,
                 exclude_paths: Optional[List[str]] = None,
                 priority: int = 100):
        """初始化认证中间件
        
        Args:
            secret_key: JWT密钥
            algorithm: JWT算法
            token_header: 认证令牌头部名称
            api_key_header: API密钥头部名称
            require_auth: 是否要求认证
            exclude_paths: 排除的路径列表
            priority: 中间件优先级
        """
        super().__init__(name="AuthMiddleware", priority=priority)
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_header = token_header.lower()
        self.api_key_header = api_key_header.lower()
        self.require_auth = require_auth
        self.exclude_paths = exclude_paths or []
        
        # 预定义的API密钥（实际应用中应该从数据库或配置中获取）
        self.api_keys = {
            # 示例API密钥，实际使用时应该替换为真实的密钥
            "demo_key_12345": {"user_id": "demo_user", "permissions": ["read", "write"]},
            "admin_key_67890": {"user_id": "admin", "permissions": ["read", "write", "admin"]},
        }
    
    async def process_request(self, context: MiddlewareContext) -> MiddlewareResult:
        """处理请求认证
        
        Args:
            context: 中间件上下文
            
        Returns:
            MiddlewareResult: 处理结果
        """
        # 检查是否在排除路径中
        if self._is_excluded_path(context.request.path):
            return MiddlewareResult.continue_execution()
        
        # 如果不要求认证，直接继续
        if not self.require_auth:
            return MiddlewareResult.continue_execution()
        
        # 尝试JWT认证
        user_info = await self._try_jwt_auth(context.request)
        if user_info:
            context.request.user = user_info
            context.set_metadata("auth_method", "jwt")
            return MiddlewareResult.continue_execution()
        
        # 尝试API密钥认证
        user_info = await self._try_api_key_auth(context.request)
        if user_info:
            context.request.user = user_info
            context.set_metadata("auth_method", "api_key")
            return MiddlewareResult.continue_execution()
        
        # 认证失败
        error_response = ResponseContext(
            status_code=401,
            headers={"content-type": "application/json"},
            body={
                "success": False,
                "message": "认证失败，请提供有效的认证信息",
                "code": "AUTHENTICATION_FAILED"
            }
        )
        
        return MiddlewareResult.stop_execution(response=error_response)
    
    async def _try_jwt_auth(self, request) -> Optional[Dict[str, Any]]:
        """尝试JWT认证
        
        Args:
            request: 请求上下文
            
        Returns:
            Optional[Dict[str, Any]]: 用户信息，认证失败返回None
        """
        auth_header = request.get_header(self.token_header)
        if not auth_header:
            return None
        
        # 检查Bearer格式
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # 移除"Bearer "前缀
        
        try:
            # 解码JWT令牌
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查令牌是否过期
            if payload.get('exp', 0) < time.time():
                return None
            
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "permissions": payload.get("permissions", []),
                "token_type": "jwt",
                "expires_at": payload.get("exp")
            }
            
        except jwt.InvalidTokenError:
            return None
    
    async def _try_api_key_auth(self, request) -> Optional[Dict[str, Any]]:
        """尝试API密钥认证
        
        Args:
            request: 请求上下文
            
        Returns:
            Optional[Dict[str, Any]]: 用户信息，认证失败返回None
        """
        api_key = request.get_header(self.api_key_header)
        if not api_key:
            return None
        
        # 查找API密钥
        user_info = self.api_keys.get(api_key)
        if not user_info:
            return None
        
        return {
            "user_id": user_info["user_id"],
            "permissions": user_info["permissions"],
            "token_type": "api_key"
        }
    
    def _is_excluded_path(self, path: str) -> bool:
        """检查路径是否在排除列表中
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否排除
        """
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path):
                return True
        return False
    
    def add_api_key(self, api_key: str, user_info: Dict[str, Any]) -> None:
        """添加API密钥
        
        Args:
            api_key: API密钥
            user_info: 用户信息
        """
        self.api_keys[api_key] = user_info
    
    def remove_api_key(self, api_key: str) -> None:
        """移除API密钥
        
        Args:
            api_key: API密钥
        """
        if api_key in self.api_keys:
            del self.api_keys[api_key]
    
    def add_exclude_path(self, path: str) -> None:
        """添加排除路径
        
        Args:
            path: 排除路径
        """
        if path not in self.exclude_paths:
            self.exclude_paths.append(path)
    
    def remove_exclude_path(self, path: str) -> None:
        """移除排除路径
        
        Args:
            path: 排除路径
        """
        if path in self.exclude_paths:
            self.exclude_paths.remove(path)


class JwtTokenGenerator:
    """JWT令牌生成器
    
    提供JWT令牌的生成和验证功能，遵循单一职责原则。
    """
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """初始化JWT令牌生成器
        
        Args:
            secret_key: 密钥
            algorithm: 算法
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_token(self, 
                      user_id: str,
                      username: str,
                      permissions: List[str],
                      expires_in: int = 3600) -> str:
        """生成JWT令牌
        
        Args:
            user_id: 用户ID
            username: 用户名
            permissions: 权限列表
            expires_in: 过期时间（秒）
            
        Returns:
            str: JWT令牌
        """
        payload = {
            "user_id": user_id,
            "username": username,
            "permissions": permissions,
            "iat": time.time(),
            "exp": time.time() + expires_in
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict[str, Any]]: 令牌载荷，验证失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # 检查令牌是否过期
            if payload.get('exp', 0) < time.time():
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, token: str, expires_in: int = 3600) -> Optional[str]:
        """刷新JWT令牌
        
        Args:
            token: 原令牌
            expires_in: 新的过期时间（秒）
            
        Returns:
            Optional[str]: 新令牌，刷新失败返回None
        """
        payload = self.verify_token(token)
        if not payload:
            return None
        
        return self.generate_token(
            user_id=payload["user_id"],
            username=payload["username"],
            permissions=payload["permissions"],
            expires_in=expires_in
        )


class ApiKeyGenerator:
    """API密钥生成器
    
    提供API密钥的生成功能，遵循单一职责原则。
    """
    
    @staticmethod
    def generate_api_key(prefix: str = "api", length: int = 16) -> str:
        """生成API密钥
        
        Args:
            prefix: 密钥前缀
            length: 随机部分长度
            
        Returns:
            str: API密钥
        """
        import secrets
        import string
        
        # 生成随机字符串
        alphabet = string.ascii_lowercase + string.digits
        random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """哈希API密钥
        
        Args:
            api_key: API密钥
            
        Returns:
            str: 哈希后的密钥
        """
        return hashlib.sha256(api_key.encode()).hexdigest()