#!/usr/bin/env python3
"""
测试环境设置工具

提供测试环境的设置和清理功能，包括：
1. 临时目录创建和清理
2. 测试数据库初始化
3. 测试配置加载
4. 测试日志配置
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, ContextManager
from contextlib import contextmanager
import logging
import sqlite3

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestEnvironment:
    """测试环境管理类"""
    
    def __init__(self, name: str = "test_env"):
        """初始化测试环境
        
        Args:
            name: 环境名称
        """
        self.name = name
        self.temp_dir = None
        self.config = {}
        self.logger = None
        self.resources = []
        
    def setup(self) -> Dict[str, Any]:
        """设置测试环境
        
        Returns:
            Dict[str, Any]: 环境配置信息
        """
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"{self.name}_"))
        
        # 创建子目录
        (self.temp_dir / "logs").mkdir(exist_ok=True)
        (self.temp_dir / "data").mkdir(exist_ok=True)
        (self.temp_dir / "configs").mkdir(exist_ok=True)
        (self.temp_dir / "outputs").mkdir(exist_ok=True)
        
        # 初始化日志
        self._setup_logging()
        
        # 加载测试配置
        self._load_config()
        
        # 初始化测试数据库
        self._setup_database()
        
        # 记录环境信息
        env_info = {
            "name": self.name,
            "temp_dir": str(self.temp_dir),
            "log_file": str(self.temp_dir / "logs" / f"{self.name}.log"),
            "config_file": str(self.temp_dir / "configs" / "test_config.json"),
            "database_file": str(self.temp_dir / "data" / f"{self.name}.db")
        }
        
        self.logger.info(f"测试环境 '{self.name}' 设置完成")
        self.logger.info(f"临时目录: {self.temp_dir}")
        
        return env_info
    
    def cleanup(self) -> None:
        """清理测试环境"""
        if self.logger:
            self.logger.info(f"开始清理测试环境 '{self.name}'")
        
        # 清理资源
        for resource in self.resources:
            try:
                if hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"清理资源时出错: {e}")
        
        self.resources.clear()
        
        # 删除临时目录
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                if self.logger:
                    self.logger.info(f"已删除临时目录: {self.temp_dir}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"删除临时目录时出错: {e}")
        
        if self.logger:
            self.logger.info(f"测试环境 '{self.name}' 清理完成")
    
    def _setup_logging(self) -> None:
        """设置测试日志"""
        log_file = self.temp_dir / "logs" / f"{self.name}.log"
        
        # 创建日志记录器
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 防止重复日志
        self.logger.propagate = False
    
    def _load_config(self) -> None:
        """加载测试配置"""
        # 基础配置
        self.config = {
            "environment": {
                "name": self.name,
                "temp_dir": str(self.temp_dir),
                "debug": True
            },
            "database": {
                "url": f"sqlite:///{self.temp_dir / 'data' / f'{self.name}.db'}",
                "echo": False
            },
            "logging": {
                "level": "DEBUG",
                "file": str(self.temp_dir / "logs" / f"{self.name}.log"),
                "enable_console": True
            },
            "features": {
                "enable_character_cards": True,
                "enable_lorebooks": True,
                "enable_prompts": True,
                "enable_events": True,
                "enable_extensions": False,
                "enable_api_gateway": True
            },
            "storage": {
                "base_path": str(self.temp_dir / "data"),
                "character_cards_path": str(self.temp_dir / "data" / "characters"),
                "lorebooks_path": str(self.temp_dir / "data" / "lorebooks"),
                "prompts_path": str(self.temp_dir / "data" / "templates"),
                "logs_path": str(self.temp_dir / "logs")
            }
        }
        
        # 保存配置文件
        config_file = self.temp_dir / "configs" / "test_config.json"
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _setup_database(self) -> None:
        """设置测试数据库"""
        db_file = self.temp_dir / "data" / f"{self.name}.db"
        
        # 创建数据库连接
        conn = sqlite3.connect(str(db_file))
        self.resources.append(conn)
        
        # 创建基本表结构（如果需要）
        # 这里可以根据需要添加测试表
    
        if self.logger:
            self.logger.info(f"测试数据库已创建: {db_file}")
    
    def get_temp_path(self, *parts: str) -> Path:
        """获取临时目录中的路径
        
        Args:
            *parts: 路径部分
            
        Returns:
            Path: 完整路径
        """
        path = self.temp_dir
        for part in parts:
            path = path / part
        return path
    
    def get_config(self, key: str = None, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        if key is None:
            return self.config
        
        # 处理嵌套键
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def add_resource(self, resource: Any) -> None:
        """添加需要清理的资源
        
        Args:
            resource: 资源对象
        """
        self.resources.append(resource)
    
    def __enter__(self) -> 'TestEnvironment':
        """进入上下文
        
        Returns:
            TestEnvironment: 环境实例
        """
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常跟踪
        """
        self.cleanup()


@contextmanager
def create_test_environment(name: str = "test_env") -> ContextManager[TestEnvironment]:
    """创建测试环境的上下文管理器
    
    Args:
        name: 环境名称
        
    Yields:
        TestEnvironment: 环境实例
    """
    env = TestEnvironment(name)
    try:
        yield env
    finally:
        env.cleanup()


def setup_test_suite(name: str = "test_suite") -> Dict[str, Any]:
    """设置测试套件环境
    
    Args:
        name: 测试套件名称
        
    Returns:
        Dict[str, Any]: 环境配置信息
    """
    with create_test_environment(name) as env:
        # 这里可以添加额外的测试套件设置
        # 例如加载测试数据、初始化服务等
        
        # 复制示例数据到测试环境
        demo_data_dir = PROJECT_ROOT / "demo_data"
        if demo_data_dir.exists():
            test_data_dir = env.get_temp_path("data")
            
            # 复制角色卡
            characters_src = demo_data_dir / "characters"
            characters_dst = test_data_dir / "characters"
            if characters_src.exists():
                characters_dst.mkdir(parents=True, exist_ok=True)
                for file in characters_src.glob("*.json"):
                    shutil.copy2(file, characters_dst / file.name)
            
            # 复制传说书
            lorebooks_src = demo_data_dir / "lorebooks"
            lorebooks_dst = test_data_dir / "lorebooks"
            if lorebooks_src.exists():
                lorebooks_dst.mkdir(parents=True, exist_ok=True)
                for file in lorebooks_src.glob("*.json"):
                    shutil.copy2(file, lorebooks_dst / file.name)
            
            # 复制提示模板
            templates_src = demo_data_dir / "templates"
            templates_dst = test_data_dir / "templates"
            if templates_src.exists():
                templates_dst.mkdir(parents=True, exist_ok=True)
                for file in templates_src.glob("*.json"):
                    shutil.copy2(file, templates_dst / file.name)
        
        env.logger.info(f"测试套件 '{name}' 设置完成")
        return env.get_config()


if __name__ == "__main__":
    # 示例用法
    with create_test_environment("demo") as env:
        print(f"环境名称: {env.name}")
        print(f"临时目录: {env.temp_dir}")
        print(f"配置: {env.get_config('environment')}")
        
        # 在环境中执行测试操作
        test_file = env.get_temp_path("data", "test.txt")
        with open(test_file, 'w') as f:
            f.write("测试内容")
        
        print(f"测试文件已创建: {test_file}")
        print(f"文件内容: {test_file.read_text()}")