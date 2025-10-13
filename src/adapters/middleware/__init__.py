"""
中间件模块包

该模块提供各种中间件实现，遵循SOLID原则，
特别是单一职责原则(SRP)，每个中间件都有明确的职责。
"""

from .auth_middleware import AuthMiddleware
from .logging_middleware import LoggingMiddleware
from .cors_middleware import CorsMiddleware
from .rate_limit_middleware import RateLimitMiddleware
from .error_handler_middleware import ErrorHandlerMiddleware
from .middleware_base import (
    MiddlewareBase,
    MiddlewareContext,
    RequestContext,
    ResponseContext,
    MiddlewarePipeline
)

__all__ = [
    'AuthMiddleware',
    'LoggingMiddleware',
    'CorsMiddleware',
    'RateLimitMiddleware',
    'ErrorHandlerMiddleware',
    'MiddlewareBase',
    'MiddlewareContext',
    'RequestContext',
    'ResponseContext',
    'MiddlewarePipeline'
]