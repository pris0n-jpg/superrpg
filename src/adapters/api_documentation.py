"""
API文档生成模块

该模块实现API文档生成功能，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责OpenAPI/Swagger文档的生成和管理。
"""

import json
import inspect
import re
from typing import Dict, Any, List, Optional, Type, Union, get_type_hints
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib

from .api_gateway import Route, ApiGateway
from ..domain.responses.api_response import ApiResponse


class ParameterType(Enum):
    """参数类型枚举"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


class ParameterLocation(Enum):
    """参数位置枚举"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    COOKIE = "cookie"


@dataclass
class ParameterInfo:
    """参数信息
    
    封装API参数的信息，遵循单一职责原则。
    """
    
    name: str
    type: ParameterType
    location: ParameterLocation
    required: bool = False
    description: str = ""
    example: Any = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None
    default: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 参数信息的字典表示
        """
        param_dict = {
            "name": self.name,
            "in": self.location.value,
            "description": self.description,
            "required": self.required,
            "schema": {
                "type": self.type.value
            }
        }
        
        if self.format:
            param_dict["schema"]["format"] = self.format
        
        if self.enum:
            param_dict["schema"]["enum"] = self.enum
        
        if self.default is not None:
            param_dict["schema"]["default"] = self.default
        
        if self.example is not None:
            param_dict["example"] = self.example
        
        return param_dict


@dataclass
class ResponseInfo:
    """响应信息
    
    封装API响应的信息，遵循单一职责原则。
    """
    
    status_code: int
    description: str
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 响应信息的字典表示
        """
        response_dict = {
            "description": self.description
        }
        
        if self.schema or self.example:
            response_dict["content"] = {
                self.content_type: {}
            }
            
            if self.schema:
                response_dict["content"][self.content_type]["schema"] = self.schema
            
            if self.example:
                response_dict["content"][self.content_type]["example"] = self.example
        
        return response_dict


@dataclass
class EndpointInfo:
    """端点信息
    
    封装API端点的信息，遵循单一职责原则。
    """
    
    path: str
    method: str
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[ParameterInfo] = field(default_factory=list)
    responses: Dict[int, ResponseInfo] = field(default_factory=dict)
    request_body: Optional[Dict[str, Any]] = None
    security: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            Dict[str, Any]: 端点信息的字典表示
        """
        endpoint_dict = {
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": [param.to_dict() for param in self.parameters],
            "responses": {
                str(code): response.to_dict() 
                for code, response in self.responses.items()
            }
        }
        
        if self.request_body:
            endpoint_dict["requestBody"] = self.request_body
        
        if self.security:
            endpoint_dict["security"] = self.security
        
        return endpoint_dict


class OpenAPIGenerator:
    """OpenAPI文档生成器
    
    负责生成OpenAPI/Swagger规范的文档，遵循单一职责原则。
    """
    
    def __init__(self, 
                 title: str = "SuperRPG API",
                 version: str = "1.0.0",
                 description: str = "SuperRPG游戏API文档",
                 base_url: str = "http://localhost:8000"):
        """初始化OpenAPI文档生成器
        
        Args:
            title: API标题
            version: API版本
            description: API描述
            base_url: 基础URL
        """
        self.title = title
        self.version = version
        self.description = description
        self.base_url = base_url
        
        # 文档组件
        self.endpoints: List[EndpointInfo] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.security_schemes: Dict[str, Dict[str, Any]] = {}
        self.tags: List[Dict[str, str]] = []
        
        # 类型映射
        self.type_mapping = {
            str: ParameterType.STRING,
            int: ParameterType.INTEGER,
            float: ParameterType.NUMBER,
            bool: ParameterType.BOOLEAN,
            list: ParameterType.ARRAY,
            dict: ParameterType.OBJECT
        }
    
    def generate_from_gateway(self, gateway: ApiGateway) -> Dict[str, Any]:
        """从API网关生成文档
        
        Args:
            gateway: API网关实例
            
        Returns:
            Dict[str, Any]: OpenAPI文档
        """
        # 清空现有数据
        self.endpoints.clear()
        self.schemas.clear()
        self.tags.clear()
        
        # 收集所有路由
        routes = gateway.get_routes_info()
        
        # 按标签分组
        tag_groups = {}
        for route in routes:
            tags = route.get("tags", [])
            if not tags:
                tags = ["default"]
            
            for tag in tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(route)
        
        # 生成标签
        for tag in tag_groups.keys():
            self.tags.append({
                "name": tag,
                "description": f"{tag}相关API"
            })
        
        # 生成端点信息
        for tag, routes in tag_groups.items():
            for route in routes:
                endpoint = self._create_endpoint_from_route(route)
                if endpoint:
                    self.endpoints.append(endpoint)
        
        # 生成基础模式
        self._generate_basic_schemas()
        
        # 生成完整文档
        return self._generate_openapi_spec()
    
    def _create_endpoint_from_route(self, route: Dict[str, Any]) -> Optional[EndpointInfo]:
        """从路由创建端点信息
        
        Args:
            route: 路由信息
            
        Returns:
            Optional[EndpointInfo]: 端点信息
        """
        try:
            path = route["path"]
            method = route["method"]
            name = route.get("name", f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}")
            description = route.get("description", "")
            tags = route.get("tags", ["default"])
            
            # 解析路径参数
            path_params = self._extract_path_parameters(path)
            
            # 解析查询参数（这里需要从处理器中提取，暂时留空）
            query_params = []
            
            # 合并所有参数
            all_params = path_params + query_params
            
            # 生成响应
            responses = {
                200: ResponseInfo(
                    status_code=200,
                    description="成功响应",
                    schema={"type": "object"},
                    example={"success": True, "data": {}}
                ),
                400: ResponseInfo(
                    status_code=400,
                    description="请求错误",
                    schema={"$ref": "#/components/schemas/ErrorResponse"}
                ),
                404: ResponseInfo(
                    status_code=404,
                    description="资源未找到",
                    schema={"$ref": "#/components/schemas/ErrorResponse"}
                ),
                500: ResponseInfo(
                    status_code=500,
                    description="服务器错误",
                    schema={"$ref": "#/components/schemas/ErrorResponse"}
                )
            }
            
            return EndpointInfo(
                path=path,
                method=method,
                summary=name,
                description=description,
                tags=tags,
                parameters=all_params,
                responses=responses
            )
            
        except Exception as e:
            print(f"创建端点信息失败: {str(e)}")
            return None
    
    def _extract_path_parameters(self, path: str) -> List[ParameterInfo]:
        """提取路径参数
        
        Args:
            path: 路径
            
        Returns:
            List[ParameterInfo]: 路径参数列表
        """
        params = []
        
        # 匹配路径参数 {param_name}
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, path)
        
        for param_name in matches:
            params.append(ParameterInfo(
                name=param_name,
                type=ParameterType.STRING,
                location=ParameterLocation.PATH,
                required=True,
                description=f"路径参数: {param_name}"
            ))
        
        return params
    
    def _generate_basic_schemas(self) -> None:
        """生成基础模式"""
        # API响应模式
        self.schemas["ApiResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "请求是否成功"
                },
                "message": {
                    "type": "string",
                    "description": "响应消息"
                },
                "data": {
                    "description": "响应数据"
                },
                "code": {
                    "type": "string",
                    "description": "响应代码"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "响应时间戳"
                },
                "request_id": {
                    "type": "string",
                    "description": "请求ID"
                },
                "metadata": {
                    "type": "object",
                    "description": "元数据"
                }
            },
            "required": ["success", "message"]
        }
        
        # 错误响应模式
        self.schemas["ErrorResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "example": False
                },
                "message": {
                    "type": "string",
                    "description": "错误消息"
                },
                "code": {
                    "type": "string",
                    "description": "错误代码"
                },
                "details": {
                    "type": "object",
                    "description": "错误详情"
                }
            },
            "required": ["success", "message"]
        }
        
        # 分页响应模式
        self.schemas["PagedResponse"] = {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean"
                },
                "message": {
                    "type": "string"
                },
                "data": {
                    "type": "array",
                    "items": {},
                    "description": "数据列表"
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "page": {
                            "type": "integer",
                            "description": "当前页码"
                        },
                        "page_size": {
                            "type": "integer",
                            "description": "每页大小"
                        },
                        "total": {
                            "type": "integer",
                            "description": "总记录数"
                        },
                        "total_pages": {
                            "type": "integer",
                            "description": "总页数"
                        },
                        "has_next": {
                            "type": "boolean",
                            "description": "是否有下一页"
                        },
                        "has_prev": {
                            "type": "boolean",
                            "description": "是否有上一页"
                        }
                    }
                }
            },
            "required": ["success", "message", "pagination"]
        }
    
    def _generate_openapi_spec(self) -> Dict[str, Any]:
        """生成OpenAPI规范
        
        Returns:
            Dict[str, Any]: OpenAPI规范文档
        """
        # 构建路径
        paths = {}
        for endpoint in self.endpoints:
            path = endpoint.path
            method = endpoint.method.lower()
            
            if path not in paths:
                paths[path] = {}
            
            paths[path][method] = endpoint.to_dict()
        
        # 构建文档
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description
            },
            "servers": [
                {
                    "url": self.base_url,
                    "description": "开发服务器"
                }
            ],
            "paths": paths,
            "components": {
                "schemas": self.schemas
            }
        }
        
        # 添加标签
        if self.tags:
            spec["tags"] = self.tags
        
        # 添加安全方案
        if self.security_schemes:
            spec["components"]["securitySchemes"] = self.security_schemes
        
        return spec
    
    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """添加模式
        
        Args:
            name: 模式名称
            schema: 模式定义
        """
        self.schemas[name] = schema
    
    def add_security_scheme(self, name: str, scheme: Dict[str, Any]) -> None:
        """添加安全方案
        
        Args:
            name: 方案名称
            scheme: 方案定义
        """
        self.security_schemes[name] = scheme
    
    def add_tag(self, name: str, description: str) -> None:
        """添加标签
        
        Args:
            name: 标签名称
            description: 标签描述
        """
        # 检查是否已存在
        for tag in self.tags:
            if tag["name"] == name:
                tag["description"] = description
                return
        
        self.tags.append({
            "name": name,
            "description": description
        })
    
    def save_to_file(self, file_path: str) -> None:
        """保存文档到文件
        
        Args:
            file_path: 文件路径
        """
        spec = self._generate_openapi_spec()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)
    
    def get_html_documentation(self) -> str:
        """获取HTML格式的文档
        
        Returns:
            str: HTML文档
        """
        spec = self._generate_openapi_spec()
        
        # 这里可以使用Swagger UI或Redoc来生成HTML
        # 为了简化，这里返回一个基本的HTML页面
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
    <meta charset="utf-8">
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui.css">
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin: 0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@3.52.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '{json.dumps(spec)}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ]
            }});
        }}
    </script>
</body>
</html>
        """
        
        return html


class DocumentationManager:
    """文档管理器
    
    负责API文档的管理和维护，遵循单一职责原则。
    """
    
    def __init__(self, gateway: ApiGateway, output_dir: str = "docs"):
        """初始化文档管理器
        
        Args:
            gateway: API网关实例
            output_dir: 输出目录
        """
        self.gateway = gateway
        self.output_dir = output_dir
        self.generator = OpenAPIGenerator()
        
        # 确保输出目录存在
        import os
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_documentation(self, 
                             format: str = "json",
                             filename: Optional[str] = None) -> str:
        """生成API文档
        
        Args:
            format: 文档格式（json, yaml, html）
            filename: 文件名
            
        Returns:
            str: 生成的文件路径
        """
        # 生成OpenAPI规范
        spec = self.generator.generate_from_gateway(self.gateway)
        
        # 确定文件名
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_spec_{timestamp}.{format}"
        
        file_path = f"{self.output_dir}/{filename}"
        
        # 根据格式保存文档
        if format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(spec, f, ensure_ascii=False, indent=2)
        
        elif format in ("yaml", "yml"):
            import yaml
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
        
        elif format == "html":
            html = self.generator.get_html_documentation()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        else:
            raise ValueError(f"不支持的文档格式: {format}")
        
        return file_path
    
    def generate_all_formats(self, base_filename: str = "api_spec") -> List[str]:
        """生成所有格式的文档
        
        Args:
            base_filename: 基础文件名
            
        Returns:
            List[str]: 生成的文件路径列表
        """
        formats = ["json", "yaml", "html"]
        file_paths = []
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for format in formats:
            filename = f"{base_filename}_{timestamp}.{format}"
            file_path = self.generate_documentation(format, filename)
            file_paths.append(file_path)
        
        return file_paths
    
    def update_documentation(self) -> str:
        """更新文档
        
        Returns:
            str: 更新的文件路径
        """
        # 生成最新的文档
        return self.generate_documentation()
    
    def get_spec(self) -> Dict[str, Any]:
        """获取OpenAPI规范

        Returns:
            Dict[str, Any]: OpenAPI规范
        """
        return self.generator.generate_from_gateway(self.gateway)

    def add_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """添加模式（兼容主入口调用）

        Args:
            name: 模式名称
            schema: 模式定义
        """
        self.generator.add_schema(name, schema)

    def add_custom_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """添加自定义模式

        Args:
            name: 模式名称
            schema: 模式定义
        """
        self.add_schema(name, schema)
    
    def add_security_scheme(self, name: str, scheme: Dict[str, Any]) -> None:
        """添加安全方案
        
        Args:
            name: 方案名称
            scheme: 方案定义
        """
        self.generator.add_security_scheme(name, scheme)
    
    def add_tag(self, name: str, description: str) -> None:
        """添加标签
        
        Args:
            name: 标签名称
            description: 标签描述
        """
        self.generator.add_tag(name, description)
    
    def create_interactive_docs(self, port: int = 8080) -> None:
        """创建交互式文档服务器
        
        Args:
            port: 服务器端口
        """
        try:
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import threading
            import webbrowser
            import time
            
            # 生成HTML文档
            html_file = self.generate_documentation("html", "interactive_docs.html")
            
            class DocsHandler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=self.output_dir, **kwargs)
                
                def do_GET(self):
                    if self.path == "/":
                        self.path = "/interactive_docs.html"
                    return super().do_GET()
            
            # 创建服务器
            server = HTTPServer(('localhost', port), DocsHandler)
            
            # 在新线程中启动服务器
            def run_server():
                print(f"交互式文档服务器启动在 http://localhost:{port}")
                server.serve_forever()
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # 打开浏览器
            webbrowser.open(f"http://localhost:{port}")
            
            # 等待一段时间让服务器启动
            time.sleep(1)
            
            return server
            
        except ImportError:
            print("无法创建交互式文档服务器，缺少必要的依赖")
        except Exception as e:
            print(f"创建交互式文档服务器失败: {str(e)}")
