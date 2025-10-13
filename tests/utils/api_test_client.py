"""
API测试客户端

提供用于测试API的工具和客户端，包括：
- HTTP请求封装
- 响应验证
- 测试数据准备
- 错误处理
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import requests
from requests import Response, Session
import aiohttp
import pytest

from src.domain.dtos.character_card_dtos import CharacterCardCreateDto, CharacterCardResponseDto
from src.domain.dtos.lorebook_dtos import LoreBookEntryCreateDto, LoreBookEntryResponseDto
from src.domain.dtos.prompt_dtos import PromptTemplateCreateDto, PromptTemplateResponseDto


@dataclass
class TestConfig:
    """测试配置"""
    base_url: str = "http://localhost:3010"
    api_version: str = "v1"
    timeout: int = 30
    retries: int = 3
    retry_delay: float = 1.0
    auth_token: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class TestResult:
    """测试结果"""
    success: bool
    status_code: int
    response_time: float
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class APITestClient:
    """API测试客户端"""
    
    def __init__(self, config: TestConfig):
        """
        初始化API测试客户端
        
        Args:
            config: 测试配置
        """
        self.config = config
        self.session = Session()
        self.session.timeout = config.timeout
        
        # 设置默认头部
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SuperRPG-APITestClient/1.0"
        }
        
        if config.headers:
            default_headers.update(config.headers)
        
        if config.auth_token:
            default_headers["Authorization"] = f"Bearer {config.auth_token}"
        
        self.session.headers.update(default_headers)
        
        # 测试结果存储
        self.test_results: List[TestResult] = []
        self.test_data: Dict[str, Any] = {}
    
    def _build_url(self, endpoint: str) -> str:
        """
        构建完整的URL
        
        Args:
            endpoint: API端点
            
        Returns:
            完整的URL
        """
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        return f"{self.config.base_url}/api/{self.config.api_version}/{endpoint}"
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> TestResult:
        """
        发起HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: 查询参数
            headers: 请求头
            
        Returns:
            测试结果
        """
        url = self._build_url(endpoint)
        request_headers = self.session.headers.copy()
        
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        try:
            # 发起请求
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers
            )
            
            response_time = time.time() - start_time
            
            # 解析响应
            try:
                response_data = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data = {"raw_response": response.text}
            
            # 创建测试结果
            result = TestResult(
                success=response.status_code < 400,
                status_code=response.status_code,
                response_time=response_time,
                response_data=response_data,
                request_data=data,
                headers=dict(response.headers)
            )
            
            # 如果请求失败，记录错误信息
            if not result.success:
                result.error_message = response_data.get("error", "Unknown error")
            
            self.test_results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            response_time = time.time() - start_time
            
            result = TestResult(
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=str(e),
                request_data=data
            )
            
            self.test_results.append(result)
            return result
    
    def _retry_request(self, 
                      method: str, 
                      endpoint: str, 
                      data: Optional[Dict[str, Any]] = None,
                      params: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None) -> TestResult:
        """
        带重试的请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: 查询参数
            headers: 请求头
            
        Returns:
            测试结果
        """
        last_result = None
        
        for attempt in range(self.config.retries + 1):
            result = self._make_request(method, endpoint, data, params, headers)
            
            if result.success:
                return result
            
            last_result = result
            
            if attempt < self.config.retries:
                time.sleep(self.config.retry_delay)
        
        return last_result
    
    # HTTP方法封装
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> TestResult:
        """GET请求"""
        return self._retry_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> TestResult:
        """POST请求"""
        return self._retry_request("POST", endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> TestResult:
        """PUT请求"""
        return self._retry_request("PUT", endpoint, data=data)
    
    def patch(self, endpoint: str, data: Dict[str, Any]) -> TestResult:
        """PATCH请求"""
        return self._retry_request("PATCH", endpoint, data=data)
    
    def delete(self, endpoint: str) -> TestResult:
        """DELETE请求"""
        return self._retry_request("DELETE", endpoint)
    
    # 角色卡API测试方法
    
    def create_character(self, character_data: Dict[str, Any]) -> TestResult:
        """
        创建角色卡
        
        Args:
            character_data: 角色卡数据
            
        Returns:
            测试结果
        """
        result = self.post("characters", character_data)
        
        if result.success:
            character_id = result.response_data.get("id")
            if character_id:
                self.test_data[f"character_{character_id}"] = character_data
        
        return result
    
    def get_character(self, character_id: str) -> TestResult:
        """
        获取角色卡
        
        Args:
            character_id: 角色ID
            
        Returns:
            测试结果
        """
        return self.get(f"characters/{character_id}")
    
    def update_character(self, character_id: str, update_data: Dict[str, Any]) -> TestResult:
        """
        更新角色卡
        
        Args:
            character_id: 角色ID
            update_data: 更新数据
            
        Returns:
            测试结果
        """
        result = self.patch(f"characters/{character_id}", update_data)
        
        if result.success and f"character_{character_id}" in self.test_data:
            self.test_data[f"character_{character_id}"].update(update_data)
        
        return result
    
    def delete_character(self, character_id: str) -> TestResult:
        """
        删除角色卡
        
        Args:
            character_id: 角色ID
            
        Returns:
            测试结果
        """
        result = self.delete(f"characters/{character_id}")
        
        if result.success and f"character_{character_id}" in self.test_data:
            del self.test_data[f"character_{character_id}"]
        
        return result
    
    def list_characters(self, params: Optional[Dict[str, Any]] = None) -> TestResult:
        """
        获取角色卡列表
        
        Args:
            params: 查询参数
            
        Returns:
            测试结果
        """
        return self.get("characters", params)
    
    # 传说书API测试方法
    
    def create_lorebook_entry(self, lorebook_data: Dict[str, Any]) -> TestResult:
        """
        创建传说书条目
        
        Args:
            lorebook_data: 传说书条目数据
            
        Returns:
            测试结果
        """
        result = self.post("lorebook", lorebook_data)
        
        if result.success:
            entry_id = result.response_data.get("id")
            if entry_id:
                self.test_data[f"lorebook_{entry_id}"] = lorebook_data
        
        return result
    
    def get_lorebook_entry(self, entry_id: str) -> TestResult:
        """
        获取传说书条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            测试结果
        """
        return self.get(f"lorebook/{entry_id}")
    
    def update_lorebook_entry(self, entry_id: str, update_data: Dict[str, Any]) -> TestResult:
        """
        更新传说书条目
        
        Args:
            entry_id: 条目ID
            update_data: 更新数据
            
        Returns:
            测试结果
        """
        result = self.patch(f"lorebook/{entry_id}", update_data)
        
        if result.success and f"lorebook_{entry_id}" in self.test_data:
            self.test_data[f"lorebook_{entry_id}"].update(update_data)
        
        return result
    
    def delete_lorebook_entry(self, entry_id: str) -> TestResult:
        """
        删除传说书条目
        
        Args:
            entry_id: 条目ID
            
        Returns:
            测试结果
        """
        result = self.delete(f"lorebook/{entry_id}")
        
        if result.success and f"lorebook_{entry_id}" in self.test_data:
            del self.test_data[f"lorebook_{entry_id}"]
        
        return result
    
    def search_lorebook(self, keywords: List[str]) -> TestResult:
        """
        搜索传说书
        
        Args:
            keywords: 关键词列表
            
        Returns:
            测试结果
        """
        return self.get("lorebook/search", {"keywords": keywords})
    
    # 提示模板API测试方法
    
    def create_prompt_template(self, template_data: Dict[str, Any]) -> TestResult:
        """
        创建提示模板
        
        Args:
            template_data: 模板数据
            
        Returns:
            测试结果
        """
        result = self.post("prompts/templates", template_data)
        
        if result.success:
            template_id = result.response_data.get("id")
            if template_id:
                self.test_data[f"template_{template_id}"] = template_data
        
        return result
    
    def get_prompt_template(self, template_id: str) -> TestResult:
        """
        获取提示模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            测试结果
        """
        return self.get(f"prompts/templates/{template_id}")
    
    def update_prompt_template(self, template_id: str, update_data: Dict[str, Any]) -> TestResult:
        """
        更新提示模板
        
        Args:
            template_id: 模板ID
            update_data: 更新数据
            
        Returns:
            测试结果
        """
        result = self.patch(f"prompts/templates/{template_id}", update_data)
        
        if result.success and f"template_{template_id}" in self.test_data:
            self.test_data[f"template_{template_id}"].update(update_data)
        
        return result
    
    def delete_prompt_template(self, template_id: str) -> TestResult:
        """
        删除提示模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            测试结果
        """
        result = self.delete(f"prompts/templates/{template_id}")
        
        if result.success and f"template_{template_id}" in self.test_data:
            del self.test_data[f"template_{template_id}"]
        
        return result
    
    def assemble_prompt(self, template_id: str, variables: Dict[str, Any]) -> TestResult:
        """
        组装提示
        
        Args:
            template_id: 模板ID
            variables: 变量值
            
        Returns:
            测试结果
        """
        return self.post(f"prompts/templates/{template_id}/assemble", {"variables": variables})
    
    # 系统API测试方法
    
    def health_check(self) -> TestResult:
        """
        健康检查
        
        Returns:
            测试结果
        """
        return self.get("health")
    
    def system_info(self) -> TestResult:
        """
        获取系统信息
        
        Returns:
            测试结果
        """
        return self.get("system/info")
    
    def system_stats(self) -> TestResult:
        """
        获取系统统计
        
        Returns:
            测试结果
        """
        return self.get("system/stats")
    
    # 测试结果处理
    
    def get_test_results(self) -> List[TestResult]:
        """
        获取所有测试结果
        
        Returns:
            测试结果列表
        """
        return self.test_results
    
    def get_successful_tests(self) -> List[TestResult]:
        """
        获取成功的测试
        
        Returns:
            成功的测试结果列表
        """
        return [result for result in self.test_results if result.success]
    
    def get_failed_tests(self) -> List[TestResult]:
        """
        获取失败的测试
        
        Returns:
            失败的测试结果列表
        """
        return [result for result in self.test_results if not result.success]
    
    def clear_results(self) -> None:
        """清除测试结果"""
        self.test_results.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计
        
        Returns:
            性能统计数据
        """
        if not self.test_results:
            return {}
        
        response_times = [result.response_time for result in self.test_results]
        success_count = len(self.get_successful_tests())
        total_count = len(self.test_results)
        
        return {
            "total_requests": total_count,
            "successful_requests": success_count,
            "failed_requests": total_count - success_count,
            "success_rate": success_count / total_count * 100,
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times)
        }
    
    def save_results(self, filepath: str) -> None:
        """
        保存测试结果到文件
        
        Args:
            filepath: 文件路径
        """
        results_data = {
            "test_config": {
                "base_url": self.config.base_url,
                "api_version": self.config.api_version,
                "timeout": self.config.timeout,
                "retries": self.config.retries
            },
            "performance_stats": self.get_performance_stats(),
            "test_results": [
                {
                    "success": result.success,
                    "status_code": result.status_code,
                    "response_time": result.response_time,
                    "error_message": result.error_message,
                    "request_data": result.request_data,
                    "response_data": result.response_data
                }
                for result in self.test_results
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
    
    def close(self) -> None:
        """关闭客户端"""
        self.session.close()


class AsyncAPITestClient:
    """异步API测试客户端"""
    
    def __init__(self, config: TestConfig):
        """
        初始化异步API测试客户端
        
        Args:
            config: 测试配置
        """
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[TestResult] = []
        self.test_data: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def _init_session(self):
        """初始化会话"""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "SuperRPG-AsyncAPITestClient/1.0"
        }
        
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        
        if self.config.headers:
            headers.update(self.config.headers)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
    
    def _build_url(self, endpoint: str) -> str:
        """构建完整的URL"""
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        return f"{self.config.base_url}/api/{self.config.api_version}/{endpoint}"
    
    async def _make_request(self, 
                           method: str, 
                           endpoint: str, 
                           data: Optional[Dict[str, Any]] = None,
                           params: Optional[Dict[str, Any]] = None) -> TestResult:
        """
        发起异步HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            params: 查询参数
            
        Returns:
            测试结果
        """
        if not self.session:
            await self._init_session()
        
        url = self._build_url(endpoint)
        start_time = time.time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                response_time = time.time() - start_time
                
                # 解析响应
                try:
                    response_data = await response.json()
                except (json.JSONDecodeError, ValueError):
                    text = await response.text()
                    response_data = {"raw_response": text}
                
                # 创建测试结果
                result = TestResult(
                    success=response.status < 400,
                    status_code=response.status,
                    response_time=response_time,
                    response_data=response_data,
                    request_data=data,
                    headers=dict(response.headers)
                )
                
                # 如果请求失败，记录错误信息
                if not result.success:
                    result.error_message = response_data.get("error", "Unknown error")
                
                self.test_results.append(result)
                return result
                
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            
            result = TestResult(
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=str(e),
                request_data=data
            )
            
            self.test_results.append(result)
            return result
    
    async def close(self):
        """关闭客户端"""
        if self.session:
            await self.session.close()
    
    # 异步API方法（示例）
    async def create_character(self, character_data: Dict[str, Any]) -> TestResult:
        """创建角色卡"""
        result = await self._make_request("POST", "characters", character_data)
        
        if result.success:
            character_id = result.response_data.get("id")
            if character_id:
                self.test_data[f"character_{character_id}"] = character_data
        
        return result
    
    async def get_character(self, character_id: str) -> TestResult:
        """获取角色卡"""
        return await self._make_request("GET", f"characters/{character_id}")
    
    async def health_check(self) -> TestResult:
        """健康检查"""
        return await self._make_request("GET", "health")


# 测试工具函数

def create_test_character_data() -> Dict[str, Any]:
    """
    创建测试角色卡数据
    
    Returns:
        角色卡数据
    """
    return {
        "name": "测试角色",
        "race": "人类",
        "class": "战士",
        "level": 1,
        "attributes": {
            "力量": 16,
            "敏捷": 14,
            "体质": 15,
            "智力": 12,
            "感知": 13,
            "魅力": 11
        },
        "skills": {
            "武器熟练": 3,
            "运动": 2
        },
        "appearance": "中等身材，黑色头发，棕色眼睛",
        "backstory": "一个普通的冒险者",
        "personality": ["勇敢", "正直"]
    }


def create_test_lorebook_data() -> Dict[str, Any]:
    """
    创建测试传说书数据
    
    Returns:
        传说书条目数据
    """
    return {
        "title": "测试条目",
        "category": "地点",
        "keywords": ["测试", "地点", "示例"],
        "content": "这是一个用于测试的传说书条目。",
        "importance": 3,
        "verified": True
    }


def create_test_prompt_template_data() -> Dict[str, Any]:
    """
    创建测试提示模板数据
    
    Returns:
        提示模板数据
    """
    return {
        "name": "测试模板",
        "category": "对话",
        "description": "用于测试的提示模板",
        "sections": [
            {
                "name": "角色设定",
                "content": "你是{character_name}，一个{race}{class}。",
                "order": 1,
                "required": True
            }
        ],
        "variables": {
            "character_name": {
                "type": "string",
                "description": "角色名称",
                "default": "默认角色",
                "required": True
            },
            "race": {
                "type": "string",
                "description": "种族",
                "default": "人类",
                "required": True
            },
            "class": {
                "type": "string",
                "description": "职业",
                "default": "战士",
                "required": True
            }
        }
    }


# 测试装饰器

def api_test(test_name: str):
    """
    API测试装饰器
    
    Args:
        test_name: 测试名称
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            print(f"开始API测试: {test_name}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                end_time = time.time()
                
                print(f"✅ API测试通过: {test_name} (耗时: {end_time - start_time:.2f}s)")
                return result
                
            except Exception as e:
                end_time = time.time()
                
                print(f"❌ API测试失败: {test_name} (耗时: {end_time - start_time:.2f}s)")
                print(f"错误信息: {str(e)}")
                raise
        
        return wrapper
    return decorator


# 测试用例示例

@api_test("健康检查")
def test_health_check(client: APITestClient) -> TestResult:
    """测试健康检查"""
    result = client.health_check()
    
    assert result.success, f"健康检查失败: {result.error_message}"
    assert result.status_code == 200, f"状态码错误: {result.status_code}"
    
    return result


@api_test("创建角色卡")
def test_create_character(client: APITestClient) -> TestResult:
    """测试创建角色卡"""
    character_data = create_test_character_data()
    result = client.create_character(character_data)
    
    assert result.success, f"创建角色卡失败: {result.error_message}"
    assert result.status_code == 201, f"状态码错误: {result.status_code}"
    assert "id" in result.response_data, "响应中缺少角色ID"
    
    return result


@api_test("获取角色卡")
def test_get_character(client: APITestClient, character_id: str) -> TestResult:
    """测试获取角色卡"""
    result = client.get_character(character_id)
    
    assert result.success, f"获取角色卡失败: {result.error_message}"
    assert result.status_code == 200, f"状态码错误: {result.status_code}"
    assert result.response_data["id"] == character_id, "角色ID不匹配"
    
    return result


# 测试套件

class APITestSuite:
    """API测试套件"""
    
    def __init__(self, client: APITestClient):
        """
        初始化测试套件
        
        Args:
            client: API测试客户端
        """
        self.client = client
        self.test_data = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        运行所有测试
        
        Returns:
            测试结果摘要
        """
        print("开始运行API测试套件...")
        
        # 运行各个测试
        test_results = {}
        
        # 系统测试
        test_results["health_check"] = test_health_check(self.client)
        test_results["system_info"] = self.client.system_info()
        test_results["system_stats"] = self.client.system_stats()
        
        # 角色卡测试
        test_results["create_character"] = test_create_character(self.client)
        
        if test_results["create_character"].success:
            character_id = test_results["create_character"].response_data["id"]
            self.test_data["character_id"] = character_id
            
            test_results["get_character"] = test_get_character(self.client, character_id)
            
            # 更新角色卡测试
            update_data = {"level": 2}
            test_results["update_character"] = self.client.update_character(character_id, update_data)
        
        # 传说书测试
        lorebook_data = create_test_lorebook_data()
        test_results["create_lorebook"] = self.client.create_lorebook_entry(lorebook_data)
        
        if test_results["create_lorebook"].success:
            entry_id = test_results["create_lorebook"].response_data["id"]
            self.test_data["lorebook_id"] = entry_id
            
            test_results["get_lorebook"] = self.client.get_lorebook_entry(entry_id)
        
        # 提示模板测试
        template_data = create_test_prompt_template_data()
        test_results["create_template"] = self.client.create_prompt_template(template_data)
        
        if test_results["create_template"].success:
            template_id = test_results["create_template"].response_data["id"]
            self.test_data["template_id"] = template_id
            
            test_results["get_template"] = self.client.get_prompt_template(template_id)
            
            # 提示组装测试
            variables = {
                "character_name": "测试角色",
                "race": "人类",
                "class": "战士"
            }
            test_results["assemble_prompt"] = self.client.assemble_prompt(template_id, variables)
        
        # 生成测试报告
        stats = self.client.get_performance_stats()
        successful_tests = len(self.client.get_successful_tests())
        failed_tests = len(self.client.get_failed_tests())
        total_tests = len(self.client.get_test_results())
        
        print(f"\nAPI测试套件完成!")
        print(f"总测试数: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {successful_tests/total_tests*100:.1f}%")
        print(f"平均响应时间: {stats.get('avg_response_time', 0):.2f}s")
        
        return {
            "test_results": test_results,
            "performance_stats": stats,
            "test_data": self.test_data
        }


if __name__ == "__main__":
    # 示例用法
    config = TestConfig(base_url="http://localhost:3010")
    client = APITestClient(config)
    
    try:
        # 运行健康检查
        result = client.health_check()
        print(f"健康检查结果: {result.success}")
        
        if result.success:
            # 运行完整测试套件
            test_suite = APITestSuite(client)
            suite_results = test_suite.run_all_tests()
            
            # 保存测试结果
            client.save_results("test_results.json")
            print("测试结果已保存到 test_results.json")
        
    finally:
        client.close()