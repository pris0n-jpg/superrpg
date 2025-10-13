# 故障排除指南

本指南提供了SuperRPG项目常见问题的诊断和解决方案，帮助开发者和运维人员快速定位和解决问题。

## 目录

- [概述](#概述)
- [常见问题分类](#常见问题分类)
- [开发环境问题](#开发环境问题)
- [API问题](#api问题)
- [数据库问题](#数据库问题)
- [性能问题](#性能问题)
- [部署问题](#部署问题)
- [测试问题](#测试问题)
- [日志分析](#日志分析)
- [调试工具](#调试工具)
- [联系支持](#联系支持)

## 概述

SuperRPG是一个复杂的RPG系统，包含多个模块和服务。在开发、测试和部署过程中可能会遇到各种问题。本指南按照问题类型分类，提供系统化的故障排除方法。

### 问题报告模板

在报告问题时，请包含以下信息：

```markdown
**问题描述**：简要描述遇到的问题

**环境信息**：
- 操作系统：
- Python版本：
- 数据库版本：
- 浏览器（如适用）：

**重现步骤**：
1. 步骤1
2. 步骤2
3. 步骤3

**预期结果**：描述预期的行为

**实际结果**：描述实际发生的情况

**错误信息**：粘贴完整的错误堆栈

**相关日志**：提供相关的日志片段
```

## 常见问题分类

### 1. 开发环境问题

#### 问题：Python环境配置错误

**症状**：
```
ModuleNotFoundError: No module named 'src'
ImportError: cannot import name 'CharacterCard'
```

**解决方案**：

1. 检查Python路径配置：
```bash
# 确保项目根目录在Python路径中
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

2. 安装项目依赖：
```bash
pip install -e .
```

3. 检查虚拟环境：
```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

#### 问题：依赖冲突

**症状**：
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**解决方案**：

1. 创建新的虚拟环境：
```bash
python -m venv fresh_env
source fresh_env/bin/activate
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 如果仍有冲突，使用pip-tools：
```bash
pip install pip-tools
pip-compile requirements.in
pip-sync
```

#### 问题：数据库连接失败

**症状**：
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**解决方案**：

1. 检查数据库服务状态：
```bash
# PostgreSQL
sudo systemctl status postgresql
# 或
docker ps | grep postgres
```

2. 检查连接配置：
```python
# 验证数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/superrpg")
print(f"Database URL: {DATABASE_URL}")
```

3. 测试数据库连接：
```bash
# 使用psql测试连接
psql -h localhost -U username -d database_name
```

### 2. API问题

#### 问题：API返回500错误

**症状**：
```json
{
    "error": {
        "code": "INTERNAL_ERROR",
        "message": "内部服务器错误"
    }
}
```

**解决方案**：

1. 检查应用日志：
```bash
# 查看应用日志
tail -f logs/app.log
# 或
docker logs superrpg_api
```

2. 启用调试模式：
```python
# 在开发环境中启用调试
app.run(debug=True)
```

3. 检查错误堆栈：
```python
import traceback
try:
    # 可能出错的代码
    pass
except Exception as e:
    traceback.print_exc()
```

#### 问题：API认证失败

**症状**：
```json
{
    "error": {
        "code": "UNAUTHORIZED",
        "message": "未授权访问"
    }
}
```

**解决方案**：

1. 检查Token有效性：
```python
import jwt

token = "your_token_here"
try:
    payload = jwt.decode(token, "your_secret", algorithms=["HS256"])
    print(f"Token有效，过期时间: {payload['exp']}")
except jwt.ExpiredSignatureError:
    print("Token已过期")
except jwt.InvalidTokenError:
    print("Token无效")
```

2. 重新获取Token：
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
```

3. 检查Token格式：
```python
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

#### 问题：CORS错误

**症状**：
```
Access to fetch at 'http://localhost:8000/api/v1/characters' from origin 'http://localhost:3000' has been blocked by CORS policy.
```

**解决方案**：

1. 检查CORS配置：
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

2. 检查预检请求：
```bash
# 检查OPTIONS请求
curl -X OPTIONS "http://localhost:8000/api/v1/characters" \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET"
```

### 3. 数据库问题

#### 问题：数据库迁移失败

**症状**：
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedColumn) column "new_column" does not exist
```

**解决方案**：

1. 检查迁移状态：
```bash
# 使用Alembic检查迁移状态
alembic current
alembic history
```

2. 应用缺失的迁移：
```bash
# 应用到最新版本
alembic upgrade head

# 或应用特定版本
alembic upgrade 1234abcd
```

3. 手动创建迁移文件：
```bash
# 创建新的迁移文件
alembic revision --autogenerate -m "Add new_column"
```

#### 问题：数据库连接池耗尽

**症状**：
```
sqlalchemy.exc.DisconnectionError: Can't reconnect until invalid transaction is rolled back
```

**解决方案**：

1. 检查连接池配置：
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

2. 增加连接池大小：
```python
# 增加连接池大小
pool_size=20,
max_overflow=40
```

3. 确保正确关闭连接：
```python
# 在finally块中关闭连接
try:
    # 数据库操作
    pass
finally:
    session.close()
```

#### 问题：数据库锁定

**症状**：
```
sqlalchemy.exc.OperationalError: (psycopg2.errors.LockNotAvailable) could not obtain lock on relation
```

**解决方案**：

1. 检查锁定状态：
```sql
-- 查看当前锁定
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS current_statement_in_blocking_process,
       blocked_activity.application_name AS blocked_application
FROM pg_catalog.pg_locks blocked_locks
    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
    JOIN pg_catalog.pg_locks blocking_locks 
        ON blocking_locks.locktype = blocked_locks.locktype
        AND blocking_locks.DATABASE IS NOT DISTINCT FROM blocked_locks.DATABASE
        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

2. 优化事务隔离级别：
```python
# 设置更低的隔离级别
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    isolation_level="READ_COMMITTED"
)
```

3. 减少事务持有时间：
```python
# 尽快提交事务
with session.begin():
    # 执行操作
    session.add(object)
    # 事务自动提交
```

### 4. 性能问题

#### 问题：API响应缓慢

**症状**：
- API响应时间超过5秒
- 页面加载时间超过10秒
- 数据库查询超时

**诊断步骤**：

1. 启用性能分析：
```python
from cProfile import Profile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

@profile_function
def slow_function():
    # 可能缓慢的代码
    pass
```

2. 检查数据库查询：
```python
# 启用SQL查询日志
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

3. 使用性能分析工具：
```bash
# 使用Py-Spy进行性能分析
pip install py-spy
py-spy top -- python src/main.py
```

**解决方案**：

1. 优化数据库查询：
```python
# 使用select_related/preload_related减少查询次数
characters = session.query(Character).options(
    selectinload(Character.skills),
    joinedload(Character.attributes)
).all()
```

2. 添加缓存：
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_character_by_id(character_id):
    return session.query(Character).filter_by(id=character_id).first()
```

3. 使用异步处理：
```python
import asyncio
import aiohttp

async def fetch_character_async(character_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"/api/v1/characters/{character_id}") as response:
            return await response.json()
```

#### 问题：内存泄漏

**症状**：
- 内存使用持续增长
- 应用频繁重启
- OutOfMemoryError

**诊断步骤**：

1. 监控内存使用：
```python
import psutil
import time

def monitor_memory():
    process = psutil.Process()
    while True:
        mem_info = process.memory_info()
        print(f"RSS: {mem_info.rss / 1024 / 1024:.2f} MB")
        time.sleep(5)
```

2. 使用内存分析工具：
```bash
# 使用memory_profiler
pip install memory_profiler
python -m memory_profiler src/main.py
```

3. 检查对象引用：
```python
import gc
import sys

def check_object_counts():
    gc.collect()  # 强制垃圾回收
    
    # 按类型统计对象数量
    object_counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        object_counts[obj_type] = object_counts.get(obj_type, 0) + 1
    
    # 显示数量最多的类型
    sorted_counts = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)
    for obj_type, count in sorted_counts[:10]:
        print(f"{obj_type}: {count}")
```

**解决方案**：

1. 修复循环引用：
```python
# 使用弱引用避免循环引用
import weakref

class Node:
    def __init__(self, name):
        self.name = name
        self._parent = weakref.ref(self)  # 避免循环引用
    
    @property
    def parent(self):
        return self._parent()
```

2. 及时释放资源：
```python
# 使用contextmanager确保资源释放
from contextlib import contextmanager

@contextmanager
def database_session():
    session = create_session()
    try:
        yield session
    finally:
        session.close()
        session.remove()
```

3. 使用对象池：
```python
# 使用对象池重用对象
class ObjectPool:
    def __init__(self, creator, max_size=10):
        self.creator = creator
        self.max_size = max_size
        self.pool = []
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            if self.pool:
                return self.pool.pop()
            else:
                return self.creator()
    
    def release(self, obj):
        with self.lock:
            if len(self.pool) < self.max_size:
                self.pool.append(obj)
```

### 5. 部署问题

#### 问题：Docker容器启动失败

**症状**：
```
Container failed to start
Error: Container exited with code 1
```

**解决方案**：

1. 检查容器日志：
```bash
docker logs superrpg_api
```

2. 检查容器状态：
```bash
docker ps -a
docker inspect superrpg_api
```

3. 进入容器调试：
```bash
docker exec -it superrpg_api /bin/bash
```

4. 检查Dockerfile配置：
```dockerfile
# 确保正确设置工作目录
WORKDIR /app

# 确保正确复制文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 确保正确暴露端口
EXPOSE 8000

# 确保正确的启动命令
CMD ["python", "src/main.py"]
```

#### 问题：Kubernetes部署失败

**症状**：
```
Pod处于Pending状态
Pod处于CrashLoopBackOff状态
Service无法访问
```

**解决方案**：

1. 检查Pod状态：
```bash
kubectl get pods
kubectl describe pod superrpg-api-xxxxx
```

2. 检查Pod日志：
```bash
kubectl logs superrpg-api-xxxxx
```

3. 检查资源配置：
```yaml
# 确保资源配置正确
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: superrpg-api
    image: superrpg/api:latest
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
```

4. 检查Service配置：
```yaml
apiVersion: v1
kind: Service
spec:
  selector:
    app: superrpg-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### 6. 测试问题

#### 问题：测试环境不一致

**症状**：
- 测试在本地通过但在CI环境中失败
- 测试结果不稳定
- 测试覆盖率低

**解决方案**：

1. 使用Docker测试环境：
```dockerfile
# tests/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -e .
RUN pip install pytest pytest-cov

CMD ["pytest", "tests/", "--cov=src"]
```

2. 使用容器化测试：
```bash
# 使用Docker运行测试
docker build -t superrpg-tests -f tests/Dockerfile .
docker run superrpg-tests
```

3. 配置测试数据库：
```python
# tests/conftest.py
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_db():
    # 使用内存数据库进行测试
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    Base.metadata.drop_all(engine)
```

#### 问题：测试数据污染

**症状**：
- 测试之间相互影响
- 测试结果不一致
- 测试失败原因不明

**解决方案**：

1. 使用事务回滚：
```python
@pytest.fixture
def transaction_session():
    """使用事务回滚的测试会话"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    
    session = Session()
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
```

2. 使用工厂模式：
```python
# tests/factories.py
import factory
from src.domain.models.characters import CharacterCard

class CharacterCardFactory(factory.Factory):
    class Meta:
        model = CharacterCard
    
    name = factory.Faker("name")
    race = factory.Iterator(["人类", "精灵", "矮人"])
    character_class = factory.Iterator(["战士", "法师", "游侠"])
    level = 1

@pytest.fixture
def character_factory():
    return CharacterCardFactory
```

3. 使用测试隔离：
```python
# 确保测试之间相互隔离
@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    yield
    
    # 清理测试数据
    db_session.query(CharacterCard).delete()
    db_session.commit()
```

## 日志分析

### 1. 应用日志

#### 日志级别配置

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# 为特定模块设置不同级别
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
```

#### 结构化日志

```python
import json
import logging

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_request(self, method, endpoint, status_code, response_time):
        log_data = {
            "type": "request",
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_error(self, error_type, error_message, stack_trace=None):
        log_data = {
            "type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.error(json.dumps(log_data))
```

### 2. 系统日志

#### 使用syslog

```python
import logging
import logging.handlers

# 配置syslog
syslog_handler = logging.handlers.SysLogHandler(address=('localhost', 514))
syslog_handler.setFormatter(logging.Formatter('%(name)s: %(levelname)s - %(message)s'))

logger = logging.getLogger()
logger.addHandler(syslog_handler)
logger.setLevel(logging.INFO)
```

#### 使用ELK Stack

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/superrpg/*.log

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "superrpg-logs-%{[agent.version]}-%{+yyyy.MM.dd}"
```

## 调试工具

### 1. Python调试器

#### 使用pdb

```python
import pdb

def debug_function():
    x = 10
    y = 20
    pdb.set_trace()  # 设置断点
    z = x + y
    return z
```

#### 使用ipdb（增强版pdb）

```python
import ipdb

def debug_function():
    x = 10
    y = 20
    ipdb.set_trace()  # 设置断点
    z = x + y
    return z
```

### 2. 性能分析工具

#### 使用Py-Spy

```bash
# 安装Py-Spy
pip install py-spy

# 监控运行中的进程
py-spy top --pid <pid>

# 生成性能报告
py-spy dump --pid <pid> --format json > profile.json
```

#### 使用cProfile

```python
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper
```

### 3. 内存分析工具

#### 使用memory_profiler

```python
# 安装memory_profiler
pip install memory_profiler

# 使用装饰器
@profile
def memory_intensive_function():
    # 可能消耗大量内存的代码
    pass

# 命令行使用
python -m memory_profiler src/main.py
```

#### 使用objgraph

```bash
# 安装objgraph
pip install objgraph

# 分析对象引用
objgraph src/main.py > objects.dot
dot -Tpng objects.dot -o objects.png
```

## 联系支持

### 获取帮助

1. **文档**：查阅项目文档和API指南
2. **GitHub Issues**：提交问题报告到GitHub仓库
3. **社区论坛**：在社区论坛寻求帮助
4. **邮件支持**：发送邮件至support@superrpg.com

### 提交问题报告

在提交问题报告时，请包含：

1. 详细的错误描述
2. 完整的重现步骤
3. 相关的日志和截图
4. 系统环境信息

### 社区资源

- **GitHub仓库**：https://github.com/superrpg/superrpg
- **文档网站**：https://docs.superrpg.com
- **Discord社区**：https://discord.gg/superrpg
- **Stack Overflow**：使用标签"superrpg"

## 总结

本故障排除指南提供了SuperRPG项目常见问题的系统化解决方案。通过遵循这些指导原则，开发者可以：

1. 快速定位问题根源
2. 使用适当的调试工具
3. 实施有效的解决方案
4. 预防类似问题的再次发生

记住，良好的日志记录和监控是预防问题的关键。定期更新文档和知识库也能帮助团队更高效地解决问题。