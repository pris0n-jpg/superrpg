"""
提示组装API控制器

提供提示组装相关的HTTP API接口，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

from typing import Dict, Any, List, Optional
from flask import request, jsonify, Response
from datetime import datetime

from ..application.services.prompt_assembly_service import PromptAssemblyService
from ..application.services.prompt_template_service import PromptTemplateService
from ..application.services.token_counter_service import TokenCounterService
from ..domain.dtos.prompt_dtos import (
    PromptBuildDto, PromptPreviewDto, PromptTemplateDto, PromptTemplateListDto,
    PromptTemplateCreateDto, PromptTemplateUpdateDto, PromptStatisticsDto,
    PromptTokenCountDto, PromptTokenCountResponseDto, PromptExportDto,
    PromptImportDto, PromptContextDto, PromptFormat, LLMProvider,
    TruncationStrategy
)
from ..core.interfaces import Logger
from ..core.exceptions import (
    ValidationException, NotFoundException, BusinessRuleException,
    ApplicationException, ExternalServiceException
)


class PromptController:
    """提示组装API控制器
    
    提供提示组装相关的HTTP API接口。
    遵循单一职责原则，专门负责HTTP请求的处理和响应。
    """
    
    def __init__(
        self,
        assembly_service: PromptAssemblyService,
        template_service: PromptTemplateService,
        token_counter: TokenCounterService,
        logger: Logger
    ):
        """初始化提示控制器
        
        Args:
            assembly_service: 提示组装服务
            template_service: 提示模板服务
            token_counter: Token计数服务
            logger: 日志记录器
        """
        self._assembly_service = assembly_service
        self._template_service = template_service
        self._token_counter = token_counter
        self._logger = logger
    
    # 提示构建相关接口
    
    def build_prompt(self) -> Response:
        """构建提示
        
        POST /api/prompts/build
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 创建DTO
            build_dto = PromptBuildDto(
                template_id=data.get('template_id', ''),
                context=PromptContextDto(**data.get('context', {})),
                token_limit=data.get('token_limit'),
                truncation_strategy=TruncationStrategy(data.get('truncation_strategy', 'smart'))
            )
            
            # 构建提示
            result = self._assembly_service.build_prompt(build_dto)
            
            # 更新使用统计
            self._assembly_service._prompt_repository.update_usage_stats(build_dto.template_id)
            
            return self._success_response(result.to_dict())
            
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except BusinessRuleException as e:
            return self._error_response(str(e), 409)
        except Exception as e:
            self._logger.error(f"Error building prompt: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def preview_prompt(self) -> Response:
        """预览提示
        
        GET /api/prompts/preview?template_id={id}&provider={provider}&model_name={model}
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取查询参数
            template_id = request.args.get('template_id')
            if not template_id:
                return self._error_response("模板ID不能为空", 400)
            
            provider = LLMProvider(request.args.get('provider', 'openai'))
            model_name = request.args.get('model_name', 'gpt-3.5-turbo')
            
            # 获取上下文数据
            context_data = request.args.get('context', '{}')
            try:
                import json
                context_dict = json.loads(context_data)
            except json.JSONDecodeError:
                context_dict = {}
            
            context = PromptContextDto(**context_dict)
            
            # 预览提示
            result = self._assembly_service.preview_prompt(template_id, context, provider, model_name)
            
            return self._success_response(result.to_dict())
            
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error previewing prompt: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def calculate_tokens(self) -> Response:
        """计算token数量
        
        POST /api/prompts/count-tokens
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 创建DTO
            count_dto = PromptTokenCountDto(
                text=data.get('text', ''),
                provider=LLMProvider(data.get('provider', 'openai')),
                model_name=data.get('model_name', 'gpt-3.5-turbo')
            )
            
            # 计算token
            result = self._token_counter.count_tokens(count_dto)
            
            return self._success_response(result.to_dict())
            
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except ExternalServiceException as e:
            return self._error_response(str(e), 502)
        except Exception as e:
            self._logger.error(f"Error counting tokens: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def get_statistics(self) -> Response:
        """获取提示统计信息
        
        GET /api/prompts/statistics?template_id={id}
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取查询参数
            template_id = request.args.get('template_id')
            if not template_id:
                return self._error_response("模板ID不能为空", 400)
            
            # 获取统计信息
            result = self._template_service.get_template_statistics(template_id)
            
            return self._success_response(result.to_dict())
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error getting prompt statistics: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def debug_prompt(self) -> Response:
        """调试提示构建过程
        
        POST /api/prompts/debug
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            template_id = data.get('template_id')
            if not template_id:
                return self._error_response("模板ID不能为空", 400)
            
            context = PromptContextDto(**data.get('context', {}))
            
            # 调试提示
            result = self._assembly_service.debug_prompt(template_id, context)
            
            return self._success_response(result)
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error debugging prompt: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def get_optimization_suggestions(self) -> Response:
        """获取优化建议
        
        POST /api/prompts/optimize
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            template_id = data.get('template_id')
            if not template_id:
                return self._error_response("模板ID不能为空", 400)
            
            context = PromptContextDto(**data.get('context', {}))
            provider = LLMProvider(data.get('provider', 'openai'))
            model_name = data.get('model_name', 'gpt-3.5-turbo')
            
            # 获取优化建议
            suggestions = self._assembly_service.get_optimization_suggestions(
                template_id, context, provider, model_name
            )
            
            return self._success_response({'suggestions': suggestions})
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error getting optimization suggestions: {e}")
            return self._error_response("内部服务器错误", 500)
    
    # 提示模板管理相关接口
    
    def get_templates(self) -> Response:
        """获取模板列表
        
        GET /api/prompts/templates?page={page}&page_size={size}&is_active={active}
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 20))
            is_active = request.args.get('is_active')
            
            if is_active is not None:
                is_active = is_active.lower() == 'true'
            
            # 获取模板列表
            result = self._template_service.get_templates(page, page_size, is_active)
            
            return self._success_response(result.to_dict())
            
        except ValueError as e:
            return self._error_response(f"参数错误: {e}", 400)
        except Exception as e:
            self._logger.error(f"Error getting templates: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def get_template(self, template_id: str) -> Response:
        """获取单个模板
        
        GET /api/prompts/templates/{id}
        
        Args:
            template_id: 模板ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取模板
            result = self._template_service.get_template(template_id)
            
            return self._success_response(result.to_dict())
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error getting template {template_id}: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def create_template(self) -> Response:
        """创建模板
        
        POST /api/prompts/templates
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 创建DTO
            create_dto = PromptTemplateCreateDto(
                name=data.get('name', ''),
                description=data.get('description', ''),
                sections=data.get('sections', []),
                metadata=data.get('metadata', {}),
                version=data.get('version', '1.0.0')
            )
            
            # 创建模板
            result = self._template_service.create_template(create_dto)
            
            return self._success_response(result.to_dict(), 201)
            
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except BusinessRuleException as e:
            return self._error_response(str(e), 409)
        except Exception as e:
            self._logger.error(f"Error creating template: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def update_template(self, template_id: str) -> Response:
        """更新模板
        
        PUT /api/prompts/templates/{id}
        
        Args:
            template_id: 模板ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 创建DTO
            update_dto = PromptTemplateUpdateDto(
                name=data.get('name'),
                description=data.get('description'),
                sections=data.get('sections'),
                metadata=data.get('metadata'),
                version=data.get('version'),
                is_active=data.get('is_active')
            )
            
            # 更新模板
            result = self._template_service.update_template(template_id, update_dto)
            
            return self._success_response(result.to_dict())
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except BusinessRuleException as e:
            return self._error_response(str(e), 409)
        except Exception as e:
            self._logger.error(f"Error updating template {template_id}: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def delete_template(self, template_id: str) -> Response:
        """删除模板
        
        DELETE /api/prompts/templates/{id}
        
        Args:
            template_id: 模板ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 删除模板
            success = self._template_service.delete_template(template_id)
            
            if success:
                return self._success_response({'message': '模板删除成功'})
            else:
                return self._error_response('模板删除失败', 500)
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except Exception as e:
            self._logger.error(f"Error deleting template {template_id}: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def search_templates(self) -> Response:
        """搜索模板
        
        GET /api/prompts/search?name={name}&description={desc}&tags={tags}&is_active={active}
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 构建搜索条件
            criteria = {}
            
            if request.args.get('name'):
                criteria['name'] = request.args.get('name')
            
            if request.args.get('description'):
                criteria['description'] = request.args.get('description')
            
            if request.args.get('tags'):
                tags = request.args.get('tags').split(',')
                criteria['tags'] = [tag.strip() for tag in tags]
            
            if request.args.get('is_active'):
                criteria['is_active'] = request.args.get('is_active').lower() == 'true'
            
            if request.args.get('variables'):
                variables = request.args.get('variables').split(',')
                criteria['variables'] = [var.strip() for var in variables]
            
            if request.args.get('section_types'):
                section_types = request.args.get('section_types').split(',')
                criteria['section_types'] = [st.strip() for st in section_types]
            
            # 搜索模板
            results = self._template_service.search_templates(criteria)
            
            return self._success_response([template.to_dict() for template in results])
            
        except Exception as e:
            self._logger.error(f"Error searching templates: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def export_template(self, template_id: str) -> Response:
        """导出模板
        
        GET /api/prompts/templates/{id}/export?format={format}
        
        Args:
            template_id: 模板ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取格式参数
            format_str = request.args.get('format', 'json')
            try:
                format_enum = PromptFormat(format_str)
            except ValueError:
                return self._error_response(f"不支持的导出格式: {format_str}", 400)
            
            # 导出模板
            result = self._template_service.export_template(template_id, format_enum)
            
            # 设置响应头
            response = self._success_response(result.to_dict())
            
            if result.filename:
                response.headers['Content-Disposition'] = f'attachment; filename="{result.filename}"'
            
            return response
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except Exception as e:
            self._logger.error(f"Error exporting template {template_id}: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def import_template(self) -> Response:
        """导入模板
        
        POST /api/prompts/templates/import
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 获取格式参数
            format_str = data.get('format', 'json')
            try:
                format_enum = PromptFormat(format_str)
            except ValueError:
                return self._error_response(f"不支持的导入格式: {format_str}", 400)
            
            # 创建DTO
            import_dto = PromptImportDto(
                data=data.get('data', {}),
                format=format_enum,
                overwrite=data.get('overwrite', False)
            )
            
            # 导入模板
            result = self._template_service.import_template(import_dto)
            
            return self._success_response(result.to_dict(), 201)
            
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except BusinessRuleException as e:
            return self._error_response(str(e), 409)
        except Exception as e:
            self._logger.error(f"Error importing template: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def get_preset_templates(self) -> Response:
        """获取预设模板列表
        
        GET /api/prompts/templates/presets
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取预设模板
            results = self._template_service.get_preset_templates()
            
            return self._success_response([template.to_dict() for template in results])
            
        except Exception as e:
            self._logger.error(f"Error getting preset templates: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def create_from_preset(self) -> Response:
        """从预设模板创建新模板
        
        POST /api/prompts/templates/create-from-preset
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            preset_name = data.get('preset_name')
            template_name = data.get('template_name')
            customizations = data.get('customizations', {})
            
            if not preset_name:
                return self._error_response("预设模板名称不能为空", 400)
            
            if not template_name:
                return self._error_response("新模板名称不能为空", 400)
            
            # 从预设创建模板
            result = self._template_service.create_from_preset(
                preset_name, template_name, customizations
            )
            
            return self._success_response(result.to_dict(), 201)
            
        except NotFoundException as e:
            return self._error_response(str(e), 404)
        except ValidationException as e:
            return self._error_response(str(e), 400)
        except BusinessRuleException as e:
            return self._error_response(str(e), 409)
        except Exception as e:
            self._logger.error(f"Error creating template from preset: {e}")
            return self._error_response("内部服务器错误", 500)
    
    # 上下文管理相关接口
    
    def create_context(self) -> Response:
        """创建上下文
        
        POST /api/prompts/context
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            # 创建上下文
            result = self._assembly_service.create_context(
                character_name=data.get('character_name', ''),
                character_description=data.get('character_description', ''),
                world_info=data.get('world_info', ''),
                chat_history=data.get('chat_history', []),
                current_input=data.get('current_input', ''),
                variables=data.get('variables', {}),
                metadata=data.get('metadata', {})
            )
            
            return self._success_response(result.to_dict())
            
        except Exception as e:
            self._logger.error(f"Error creating context: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def add_chat_message(self) -> Response:
        """添加聊天消息
        
        POST /api/prompts/context/add-message
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            context = PromptContextDto(**data.get('context', {}))
            role = data.get('role')
            content = data.get('content')
            
            if not role:
                return self._error_response("消息角色不能为空", 400)
            
            if not content:
                return self._error_response("消息内容不能为空", 400)
            
            # 添加消息
            result = self._assembly_service.add_chat_message(context, role, content)
            
            return self._success_response(result.to_dict())
            
        except Exception as e:
            self._logger.error(f"Error adding chat message: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def clear_chat_history(self) -> Response:
        """清除聊天历史
        
        POST /api/prompts/context/clear-history
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 解析请求数据
            data = request.get_json()
            if not data:
                return self._error_response("请求数据不能为空", 400)
            
            context = PromptContextDto(**data.get('context', {}))
            
            # 清除历史
            result = self._assembly_service.clear_chat_history(context)
            
            return self._success_response(result.to_dict())
            
        except Exception as e:
            self._logger.error(f"Error clearing chat history: {e}")
            return self._error_response("内部服务器错误", 500)
    
    # 系统信息相关接口
    
    def get_supported_providers(self) -> Response:
        """获取支持的LLM提供商
        
        GET /api/prompts/providers
        
        Returns:
            Response: HTTP响应
        """
        try:
            providers = self._token_counter.get_supported_providers()
            return self._success_response(providers)
            
        except Exception as e:
            self._logger.error(f"Error getting supported providers: {e}")
            return self._error_response("内部服务器错误", 500)
    
    def get_supported_models(self) -> Response:
        """获取支持的模型列表
        
        GET /api/prompts/models?provider={provider}
        
        Returns:
            Response: HTTP响应
        """
        try:
            provider_str = request.args.get('provider', 'openai')
            try:
                provider = LLMProvider(provider_str)
            except ValueError:
                return self._error_response(f"不支持的提供商: {provider_str}", 400)
            
            models = self._token_counter.get_supported_models(provider)
            return self._success_response(models)
            
        except Exception as e:
            self._logger.error(f"Error getting supported models: {e}")
            return self._error_response("内部服务器错误", 500)
    
    # 辅助方法
    
    def _success_response(self, data: Dict[str, Any], status_code: int = 200) -> Response:
        """创建成功响应
        
        Args:
            data: 响应数据
            status_code: HTTP状态码
            
        Returns:
            Response: HTTP响应
        """
        response_data = {
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data), status_code
    
    def _error_response(self, message: str, status_code: int = 400) -> Response:
        """创建错误响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            
        Returns:
            Response: HTTP响应
        """
        response_data = {
            'success': False,
            'error': message,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data), status_code


def register_prompt_routes(app, controller: PromptController):
    """注册提示相关路由
    
    Args:
        app: Flask应用
        controller: 提示控制器
    """
    # 提示构建相关路由
    app.add_url_rule('/api/prompts/build', 'build_prompt', 
                     controller.build_prompt, methods=['POST'])
    
    app.add_url_rule('/api/prompts/preview', 'preview_prompt', 
                     controller.preview_prompt, methods=['GET'])
    
    app.add_url_rule('/api/prompts/count-tokens', 'count_tokens', 
                     controller.calculate_tokens, methods=['POST'])
    
    app.add_url_rule('/api/prompts/statistics', 'get_statistics', 
                     controller.get_statistics, methods=['GET'])
    
    app.add_url_rule('/api/prompts/debug', 'debug_prompt', 
                     controller.debug_prompt, methods=['POST'])
    
    app.add_url_rule('/api/prompts/optimize', 'get_optimization_suggestions', 
                     controller.get_optimization_suggestions, methods=['POST'])
    
    # 提示模板管理相关路由
    app.add_url_rule('/api/prompts/templates', 'get_templates', 
                     controller.get_templates, methods=['GET'])
    
    app.add_url_rule('/api/prompts/templates', 'create_template', 
                     controller.create_template, methods=['POST'])
    
    app.add_url_rule('/api/prompts/templates/<template_id>', 'get_template', 
                     controller.get_template, methods=['GET'])
    
    app.add_url_rule('/api/prompts/templates/<template_id>', 'update_template', 
                     controller.update_template, methods=['PUT'])
    
    app.add_url_rule('/api/prompts/templates/<template_id>', 'delete_template', 
                     controller.delete_template, methods=['DELETE'])
    
    app.add_url_rule('/api/prompts/search', 'search_templates', 
                     controller.search_templates, methods=['GET'])
    
    app.add_url_rule('/api/prompts/templates/<template_id>/export', 'export_template', 
                     controller.export_template, methods=['GET'])
    
    app.add_url_rule('/api/prompts/templates/import', 'import_template', 
                     controller.import_template, methods=['POST'])
    
    app.add_url_rule('/api/prompts/templates/presets', 'get_preset_templates', 
                     controller.get_preset_templates, methods=['GET'])
    
    app.add_url_rule('/api/prompts/templates/create-from-preset', 'create_from_preset', 
                     controller.create_from_preset, methods=['POST'])
    
    # 上下文管理相关路由
    app.add_url_rule('/api/prompts/context', 'create_context', 
                     controller.create_context, methods=['POST'])
    
    app.add_url_rule('/api/prompts/context/add-message', 'add_chat_message', 
                     controller.add_chat_message, methods=['POST'])
    
    app.add_url_rule('/api/prompts/context/clear-history', 'clear_chat_history', 
                     controller.clear_chat_history, methods=['POST'])
    
    # 系统信息相关路由
    app.add_url_rule('/api/prompts/providers', 'get_supported_providers', 
                     controller.get_supported_providers, methods=['GET'])
    
    app.add_url_rule('/api/prompts/models', 'get_supported_models', 
                     controller.get_supported_models, methods=['GET'])