"""
角色卡API控制器

该控制器提供角色卡的REST API接口，遵循SOLID原则，
特别是单一职责原则(SRP)，专门负责角色卡API请求的处理。
"""

from typing import Dict, Any, Optional
from flask import request, jsonify, Response

from ..domain.dtos import (
    CharacterCardDto, CharacterCardListDto,
    CharacterCardCreateDto, CharacterCardUpdateDto,
    CharacterCardImportDto, CharacterCardExportDto
)
from ..application.services.character_card_service import CharacterCardService
from ..core.exceptions import (
    ValidationException, NotFoundException, 
    DuplicateException, BaseException
)
from ..core.interfaces import Logger


class CharacterCardController:
    """角色卡API控制器
    
    遵循单一职责原则，专门负责角色卡API请求的处理。
    遵循依赖倒置原则，依赖抽象接口而非具体实现。
    """
    
    def __init__(self, character_card_service: CharacterCardService, logger: Logger):
        """初始化角色卡控制器
        
        Args:
            character_card_service: 角色卡管理服务
            logger: 日志记录器
        """
        self._character_card_service = character_card_service
        self._logger = logger
    
    def create_character(self) -> Response:
        """创建角色卡
        
        POST /api/characters
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': '请求体不能为空',
                    'message': '请提供角色卡数据'
                }), 400
            
            # 创建DTO
            create_dto = CharacterCardCreateDto(**data)
            
            # 创建角色卡
            character_dto = self._character_card_service.create_character_card(create_dto)
            
            # 返回结果
            return jsonify({
                'success': True,
                'data': character_dto.to_dict(),
                'message': '角色卡创建成功'
            }), 201
            
        except ValidationException as e:
            self._logger.warning(f"创建角色卡验证失败: {str(e)}")
            return jsonify({
                'error': '验证失败',
                'message': e.message,
                'details': e.details
            }), 400
            
        except DuplicateException as e:
            self._logger.warning(f"创建角色卡重复失败: {str(e)}")
            return jsonify({
                'error': '资源重复',
                'message': e.message,
                'details': e.details
            }), 409
            
        except Exception as e:
            self._logger.error(f"创建角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '创建角色卡失败'
            }), 500
    
    def get_character(self, character_id: str) -> Response:
        """获取角色卡详情
        
        GET /api/characters/{id}
        
        Args:
            character_id: 角色ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取角色卡
            character_dto = self._character_card_service.get_character_card(character_id)
            
            # 返回结果
            return jsonify({
                'success': True,
                'data': character_dto.to_dict(),
                'message': '获取角色卡成功'
            }), 200
            
        except NotFoundException as e:
            self._logger.warning(f"获取角色卡失败: {str(e)}")
            return jsonify({
                'error': '资源未找到',
                'message': e.message,
                'details': e.details
            }), 404
            
        except Exception as e:
            self._logger.error(f"获取角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '获取角色卡失败'
            }), 500
    
    def update_character(self, character_id: str) -> Response:
        """更新角色卡
        
        PUT /api/characters/{id}
        
        Args:
            character_id: 角色ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': '请求体不能为空',
                    'message': '请提供角色卡更新数据'
                }), 400
            
            # 创建DTO
            update_dto = CharacterCardUpdateDto(**data)
            
            # 更新角色卡
            character_dto = self._character_card_service.update_character_card(character_id, update_dto)
            
            # 返回结果
            return jsonify({
                'success': True,
                'data': character_dto.to_dict(),
                'message': '角色卡更新成功'
            }), 200
            
        except NotFoundException as e:
            self._logger.warning(f"更新角色卡失败: {str(e)}")
            return jsonify({
                'error': '资源未找到',
                'message': e.message,
                'details': e.details
            }), 404
            
        except ValidationException as e:
            self._logger.warning(f"更新角色卡验证失败: {str(e)}")
            return jsonify({
                'error': '验证失败',
                'message': e.message,
                'details': e.details
            }), 400
            
        except Exception as e:
            self._logger.error(f"更新角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '更新角色卡失败'
            }), 500
    
    def delete_character(self, character_id: str) -> Response:
        """删除角色卡
        
        DELETE /api/characters/{id}
        
        Args:
            character_id: 角色ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 删除角色卡
            success = self._character_card_service.delete_character_card(character_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '角色卡删除成功'
                }), 200
            else:
                return jsonify({
                    'error': '删除失败',
                    'message': '角色卡删除失败'
                }), 500
            
        except NotFoundException as e:
            self._logger.warning(f"删除角色卡失败: {str(e)}")
            return jsonify({
                'error': '资源未找到',
                'message': e.message,
                'details': e.details
            }), 404
            
        except Exception as e:
            self._logger.error(f"删除角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '删除角色卡失败'
            }), 500
    
    def get_characters(self) -> Response:
        """获取角色卡列表
        
        GET /api/characters
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取查询参数
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 20))
            
            # 构建过滤条件
            filters = {}
            if request.args.get('name'):
                filters['name'] = request.args.get('name')
            if request.args.get('is_alive'):
                filters['is_alive'] = request.args.get('is_alive').lower() == 'true'
            if request.args.get('level'):
                filters['level'] = int(request.args.get('level'))
            if request.args.get('tag'):
                filters['tag'] = request.args.get('tag')
            
            # 获取角色卡列表
            character_list_dto = self._character_card_service.get_character_cards(
                page=page,
                page_size=page_size,
                filters=filters if filters else None
            )
            
            # 返回结果
            return jsonify({
                'success': True,
                'data': character_list_dto.to_dict(),
                'message': '获取角色卡列表成功'
            }), 200
            
        except ValueError as e:
            self._logger.warning(f"获取角色卡列表参数错误: {str(e)}")
            return jsonify({
                'error': '参数错误',
                'message': '查询参数格式不正确'
            }), 400
            
        except Exception as e:
            self._logger.error(f"获取角色卡列表失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '获取角色卡列表失败'
            }), 500
    
    def import_character(self) -> Response:
        """导入角色卡
        
        POST /api/characters/import
        
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取请求数据
            data = request.get_json()
            if not data:
                return jsonify({
                    'error': '请求体不能为空',
                    'message': '请提供角色卡导入数据'
                }), 400
            
            # 获取格式参数
            format_type = data.get('format', 'json')
            import_data = data.get('data')
            
            if not import_data:
                return jsonify({
                    'error': '导入数据不能为空',
                    'message': '请提供角色卡数据'
                }), 400
            
            # 创建DTO
            import_dto = CharacterCardImportDto(
                data=import_data,
                format=format_type
            )
            
            # 导入角色卡
            character_dto = self._character_card_service.import_character_card(import_dto)
            
            # 返回结果
            return jsonify({
                'success': True,
                'data': character_dto.to_dict(),
                'message': '角色卡导入成功'
            }), 201
            
        except ValidationException as e:
            self._logger.warning(f"导入角色卡验证失败: {str(e)}")
            return jsonify({
                'error': '验证失败',
                'message': e.message,
                'details': e.details
            }), 400
            
        except DuplicateException as e:
            self._logger.warning(f"导入角色卡重复失败: {str(e)}")
            return jsonify({
                'error': '资源重复',
                'message': e.message,
                'details': e.details
            }), 409
            
        except Exception as e:
            self._logger.error(f"导入角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '导入角色卡失败'
            }), 500
    
    def export_character(self, character_id: str) -> Response:
        """导出角色卡
        
        GET /api/characters/{id}/export
        
        Args:
            character_id: 角色ID
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 获取格式参数
            format_type = request.args.get('format', 'json')
            
            # 导出角色卡
            export_dto = self._character_card_service.export_character_card(
                character_id=character_id,
                format=format_type
            )
            
            # 设置响应头
            if export_dto.filename:
                response = jsonify({
                    'success': True,
                    'data': export_dto.to_dict(),
                    'message': '角色卡导出成功'
                })
                
                if format_type == 'json':
                    response.headers['Content-Disposition'] = f'attachment; filename="{export_dto.filename}"'
                
                return response, 200
            else:
                return jsonify({
                    'success': True,
                    'data': export_dto.to_dict(),
                    'message': '角色卡导出成功'
                }), 200
            
        except NotFoundException as e:
            self._logger.warning(f"导出角色卡失败: {str(e)}")
            return jsonify({
                'error': '资源未找到',
                'message': e.message,
                'details': e.details
            }), 404
            
        except ValidationException as e:
            self._logger.warning(f"导出角色卡验证失败: {str(e)}")
            return jsonify({
                'error': '验证失败',
                'message': e.message,
                'details': e.details
            }), 400
            
        except Exception as e:
            self._logger.error(f"导出角色卡失败: {str(e)}")
            return jsonify({
                'error': '服务器内部错误',
                'message': '导出角色卡失败'
            }), 500
    
    def register_routes(self, app) -> None:
        """注册路由
        
        Args:
            app: Flask应用实例
        """
        # 角色卡路由
        app.add_url_rule(
            '/api/characters',
            view_func=self.create_character,
            methods=['POST']
        )
        
        app.add_url_rule(
            '/api/characters/<character_id>',
            view_func=self.get_character,
            methods=['GET']
        )
        
        app.add_url_rule(
            '/api/characters/<character_id>',
            view_func=self.update_character,
            methods=['PUT']
        )
        
        app.add_url_rule(
            '/api/characters/<character_id>',
            view_func=self.delete_character,
            methods=['DELETE']
        )
        
        app.add_url_rule(
            '/api/characters',
            view_func=self.get_characters,
            methods=['GET']
        )
        
        app.add_url_rule(
            '/api/characters/import',
            view_func=self.import_character,
            methods=['POST']
        )
        
        app.add_url_rule(
            '/api/characters/<character_id>/export',
            view_func=self.export_character,
            methods=['GET']
        )