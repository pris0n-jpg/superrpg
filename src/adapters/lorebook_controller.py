"""
传说书API控制器

提供传说书相关的HTTP API接口，遵循SOLID原则，
特别是单一职责原则(SRP)和依赖倒置原则(DIP)。
"""

from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, Response

from ..application.services.lorebook_service import LorebookService
from ..domain.dtos.lorebook_dtos import (
    LorebookCreateDto, LorebookUpdateDto, LorebookEntryCreateDto, 
    LorebookEntryUpdateDto, LorebookImportDto, LorebookActivationDto
)
from ..core.exceptions import ValidationException, BusinessRuleException, NotFoundException
from ..core.interfaces import Logger


class LorebookController:
    """传说书API控制器
    
    提供传说书相关的HTTP API接口。
    遵循单一职责原则，专门负责HTTP请求的处理和响应。
    """
    
    def __init__(self, lorebook_service: LorebookService, logger: Logger):
        """初始化传说书控制器
        
        Args:
            lorebook_service: 传说书服务
            logger: 日志记录器
        """
        self._lorebook_service = lorebook_service
        self._logger = logger
        self._blueprint = Blueprint('lorebook', __name__, url_prefix='/api/lorebooks')
        self._register_routes()
    
    def _register_routes(self) -> None:
        """注册路由"""
        # 传说书路由
        self._blueprint.route('', methods=['POST'])(self.create_lorebook)
        self._blueprint.route('', methods=['GET'])(self.get_lorebooks)
        self._blueprint.route('/<lorebook_id>', methods=['GET'])(self.get_lorebook)
        self._blueprint.route('/<lorebook_id>', methods=['PUT'])(self.update_lorebook)
        self._blueprint.route('/<lorebook_id>', methods=['DELETE'])(self.delete_lorebook)
        self._blueprint.route('/<lorebook_id>/statistics', methods=['GET'])(self.get_lorebook_statistics)
        self._blueprint.route('/<lorebook_id>/export', methods=['GET'])(self.export_lorebook)
        self._blueprint.route('/import', methods=['POST'])(self.import_lorebook)
        self._blueprint.route('/search', methods=['POST'])(self.search_lorebooks)
        
        # 条目路由
        self._blueprint.route('/<lorebook_id>/entries', methods=['POST'])(self.create_entry)
        self._blueprint.route('/<lorebook_id>/entries', methods=['GET'])(self.get_entries)
        self._blueprint.route('/<lorebook_id>/entries/<entry_id>', methods=['GET'])(self.get_entry)
        self._blueprint.route('/<lorebook_id>/entries/<entry_id>', methods=['PUT'])(self.update_entry)
        self._blueprint.route('/<lorebook_id>/entries/<entry_id>', methods=['DELETE'])(self.delete_entry)
        self._blueprint.route('/<lorebook_id>/entries/search', methods=['POST'])(self.search_entries)
        self._blueprint.route('/<lorebook_id>/entries/most-activated', methods=['GET'])(self.get_most_activated_entries)
        self._blueprint.route('/<lorebook_id>/entries/recently-activated', methods=['GET'])(self.get_recently_activated_entries)
        
        # 激活路由
        self._blueprint.route('/<lorebook_id>/activate', methods=['POST'])(self.activate_entries)
    
    @property
    def blueprint(self) -> Blueprint:
        """获取Flask蓝图
        
        Returns:
            Blueprint: Flask蓝图对象
        """
        return self._blueprint
    
    def _handle_error(self, error: Exception) -> Response:
        """处理错误
        
        Args:
            error: 异常对象
            
        Returns:
            Response: 错误响应
        """
        if isinstance(error, ValidationException):
            return jsonify({
                'error': 'Validation Error',
                'message': str(error),
                'status': 400
            }), 400
        elif isinstance(error, BusinessRuleException):
            return jsonify({
                'error': 'Business Rule Error',
                'message': str(error),
                'status': 422
            }), 422
        elif isinstance(error, NotFoundException):
            return jsonify({
                'error': 'Not Found',
                'message': str(error),
                'status': 404
            }), 404
        else:
            self._logger.error(f"Unexpected error: {str(error)}")
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred',
                'status': 500
            }), 500
    
    def _get_request_data(self) -> Dict[str, Any]:
        """获取请求数据
        
        Returns:
            Dict[str, Any]: 请求数据
        """
        if request.is_json:
            return request.get_json() or {}
        return request.form.to_dict()
    
    def _get_query_params(self) -> Dict[str, Any]:
        """获取查询参数
        
        Returns:
            Dict[str, Any]: 查询参数
        """
        params = {}
        
        # 处理分页参数
        if 'page' in request.args:
            try:
                params['page'] = int(request.args.get('page', 1))
            except ValueError:
                params['page'] = 1
        
        if 'page_size' in request.args:
            try:
                params['page_size'] = int(request.args.get('page_size', 20))
            except ValueError:
                params['page_size'] = 20
        
        # 处理其他参数
        if 'limit' in request.args:
            try:
                params['limit'] = int(request.args.get('limit', 10))
            except ValueError:
                params['limit'] = 10
        
        if 'format' in request.args:
            params['format'] = request.args.get('format', 'json')
        
        return params
    
    # 传说书API方法
    
    def create_lorebook(self) -> Response:
        """创建传说书
        
        POST /api/lorebooks
        """
        try:
            data = self._get_request_data()
            create_dto = LorebookCreateDto(**data)
            
            lorebook_dto = self._lorebook_service.create_lorebook(create_dto)
            
            return jsonify({
                'success': True,
                'data': lorebook_dto.to_dict(),
                'message': '传说书创建成功'
            }), 201
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_lorebooks(self) -> Response:
        """获取传说书列表
        
        GET /api/lorebooks?page=1&page_size=20
        """
        try:
            params = self._get_query_params()
            page = params.get('page', 1)
            page_size = params.get('page_size', 20)
            
            lorebook_list_dto = self._lorebook_service.get_lorebooks(page, page_size)
            
            return jsonify({
                'success': True,
                'data': lorebook_list_dto.to_dict(),
                'message': '获取传说书列表成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_lorebook(self, lorebook_id: str) -> Response:
        """获取传说书详情
        
        GET /api/lorebooks/{id}
        """
        try:
            lorebook_dto = self._lorebook_service.get_lorebook(lorebook_id)
            
            return jsonify({
                'success': True,
                'data': lorebook_dto.to_dict(),
                'message': '获取传说书详情成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def update_lorebook(self, lorebook_id: str) -> Response:
        """更新传说书
        
        PUT /api/lorebooks/{id}
        """
        try:
            data = self._get_request_data()
            update_dto = LorebookUpdateDto(**data)
            
            lorebook_dto = self._lorebook_service.update_lorebook(lorebook_id, update_dto)
            
            return jsonify({
                'success': True,
                'data': lorebook_dto.to_dict(),
                'message': '传说书更新成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def delete_lorebook(self, lorebook_id: str) -> Response:
        """删除传说书
        
        DELETE /api/lorebooks/{id}
        """
        try:
            success = self._lorebook_service.delete_lorebook(lorebook_id)
            
            return jsonify({
                'success': success,
                'message': '传说书删除成功' if success else '传说书删除失败'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_lorebook_statistics(self, lorebook_id: str) -> Response:
        """获取传说书统计信息
        
        GET /api/lorebooks/{id}/statistics
        """
        try:
            stats_dto = self._lorebook_service.get_lorebook_statistics(lorebook_id)
            
            return jsonify({
                'success': True,
                'data': stats_dto.to_dict(),
                'message': '获取统计信息成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def export_lorebook(self, lorebook_id: str) -> Response:
        """导出传说书
        
        GET /api/lorebooks/{id}/export?format=json
        """
        try:
            params = self._get_query_params()
            format = params.get('format', 'json')
            
            export_dto = self._lorebook_service.export_lorebook(lorebook_id, format)
            
            return jsonify({
                'success': True,
                'data': export_dto.to_dict(),
                'message': '传说书导出成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def import_lorebook(self) -> Response:
        """导入传说书
        
        POST /api/lorebooks/import
        """
        try:
            data = self._get_request_data()
            import_dto = LorebookImportDto(**data)
            
            lorebook_dto = self._lorebook_service.import_lorebook(import_dto)
            
            return jsonify({
                'success': True,
                'data': lorebook_dto.to_dict(),
                'message': '传说书导入成功'
            }), 201
            
        except Exception as e:
            return self._handle_error(e)
    
    def search_lorebooks(self) -> Response:
        """搜索传说书
        
        POST /api/lorebooks/search
        """
        try:
            criteria = self._get_request_data()
            lorebook_dtos = self._lorebook_service.search_lorebooks(criteria)
            
            return jsonify({
                'success': True,
                'data': [dto.to_dict() for dto in lorebook_dtos],
                'message': '搜索完成'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    # 条目API方法
    
    def create_entry(self, lorebook_id: str) -> Response:
        """创建条目
        
        POST /api/lorebooks/{id}/entries
        """
        try:
            data = self._get_request_data()
            create_dto = LorebookEntryCreateDto(**data)
            
            entry_dto = self._lorebook_service.create_entry(lorebook_id, create_dto)
            
            return jsonify({
                'success': True,
                'data': entry_dto.to_dict(),
                'message': '条目创建成功'
            }), 201
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_entries(self, lorebook_id: str) -> Response:
        """获取条目列表
        
        GET /api/lorebooks/{id}/entries?page=1&page_size=20
        """
        try:
            params = self._get_query_params()
            page = params.get('page', 1)
            page_size = params.get('page_size', 20)
            
            entry_dtos = self._lorebook_service.get_entries(lorebook_id, page, page_size)
            
            return jsonify({
                'success': True,
                'data': [dto.to_dict() for dto in entry_dtos],
                'message': '获取条目列表成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_entry(self, lorebook_id: str, entry_id: str) -> Response:
        """获取条目详情
        
        GET /api/lorebooks/{id}/entries/{entry_id}
        """
        try:
            entry_dto = self._lorebook_service.get_entry(lorebook_id, entry_id)
            
            return jsonify({
                'success': True,
                'data': entry_dto.to_dict(),
                'message': '获取条目详情成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def update_entry(self, lorebook_id: str, entry_id: str) -> Response:
        """更新条目
        
        PUT /api/lorebooks/{id}/entries/{entry_id}
        """
        try:
            data = self._get_request_data()
            update_dto = LorebookEntryUpdateDto(**data)
            
            entry_dto = self._lorebook_service.update_entry(lorebook_id, entry_id, update_dto)
            
            return jsonify({
                'success': True,
                'data': entry_dto.to_dict(),
                'message': '条目更新成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def delete_entry(self, lorebook_id: str, entry_id: str) -> Response:
        """删除条目
        
        DELETE /api/lorebooks/{id}/entries/{entry_id}
        """
        try:
            success = self._lorebook_service.delete_entry(lorebook_id, entry_id)
            
            return jsonify({
                'success': success,
                'message': '条目删除成功' if success else '条目删除失败'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def search_entries(self, lorebook_id: str) -> Response:
        """搜索条目
        
        POST /api/lorebooks/{id}/entries/search
        """
        try:
            criteria = self._get_request_data()
            entry_dtos = self._lorebook_service.search_entries(lorebook_id, criteria)
            
            return jsonify({
                'success': True,
                'data': [dto.to_dict() for dto in entry_dtos],
                'message': '搜索完成'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_most_activated_entries(self, lorebook_id: str) -> Response:
        """获取最常激活的条目
        
        GET /api/lorebooks/{id}/entries/most-activated?limit=10
        """
        try:
            params = self._get_query_params()
            limit = params.get('limit', 10)
            
            entry_dtos = self._lorebook_service.get_most_activated_entries(lorebook_id, limit)
            
            return jsonify({
                'success': True,
                'data': [dto.to_dict() for dto in entry_dtos],
                'message': '获取最常激活条目成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def get_recently_activated_entries(self, lorebook_id: str) -> Response:
        """获取最近激活的条目
        
        GET /api/lorebooks/{id}/entries/recently-activated?limit=10
        """
        try:
            params = self._get_query_params()
            limit = params.get('limit', 10)
            
            entry_dtos = self._lorebook_service.get_recently_activated_entries(lorebook_id, limit)
            
            return jsonify({
                'success': True,
                'data': [dto.to_dict() for dto in entry_dtos],
                'message': '获取最近激活条目成功'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    # 激活API方法
    
    def activate_entries(self, lorebook_id: str) -> Response:
        """激活条目
        
        POST /api/lorebooks/{id}/activate
        """
        try:
            data = self._get_request_data()
            activation_dto = LorebookActivationDto(**data)
            
            result_dto = self._lorebook_service.activate_entries(lorebook_id, activation_dto)
            
            return jsonify({
                'success': True,
                'data': result_dto.to_dict(),
                'message': f'成功激活 {len(result_dto.activated_entries)} 个条目'
            }), 200
            
        except Exception as e:
            return self._handle_error(e)
    
    def register_error_handlers(self, app) -> None:
        """注册错误处理器
        
        Args:
            app: Flask应用对象
        """
        @app.errorhandler(ValidationException)
        def handle_validation_error(error):
            return self._handle_error(error)
        
        @app.errorhandler(BusinessRuleException)
        def handle_business_rule_error(error):
            return self._handle_error(error)
        
        @app.errorhandler(NotFoundException)
        def handle_not_found_error(error):
            return self._handle_error(error)
        
        @app.errorhandler(Exception)
        def handle_generic_error(error):
            return self._handle_error(error)