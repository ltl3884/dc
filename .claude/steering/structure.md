# Project Structure

## Directory Organization

```
ac/
├── .venv/                    # Python虚拟环境
├── src/                      # 源代码目录
│   ├── models/              # 数据模型层
│   │   ├── __init__.py
│   │   ├── address_info.py  # AddressInfo模型
│   │   └── task.py         # Task模型
│   ├── services/            # 服务层
│   │   ├── __init__.py
│   │   ├── crawler_service.py  # 爬虫服务
│   │   └── task_service.py     # 任务管理服务
│   ├── scheduler/           # 调度器
│   │   ├── __init__.py
│   │   └── task_scheduler.py   # APScheduler配置
│   ├── utils/               # 工具模块
│   │   ├── __init__.py
│   │   ├── database.py      # 数据库连接配置
│   │   └── logger.py        # 日志配置
│   └── app.py              # Flask应用主文件
├── migrations/              # 数据库迁移文件
├── logs/                    # 日志文件目录
├── config.py               # 应用配置文件
├── pyproject.toml          # 项目依赖配置
└── requirements.txt        # 依赖列表（备用）
```

## Naming Conventions

### Files
- **Python模块**: 使用snake_case命名 (如: crawler_service.py)
- **模型文件**: 使用小写字母，反映模型名称 (如: address_info.py)
- **服务文件**: 使用_service后缀 (如: task_service.py)
- **配置文件**: 使用简洁描述性名称 (如: config.py)

### Code
- **类名**: 使用PascalCase (如: AddressInfo, TaskService)
- **函数/方法**: 使用snake_case (如: crawl_address, update_task)
- **常量**: 使用UPPER_SNAKE_CASE (如: DATABASE_URL, DEFAULT_TIMEOUT)
- **变量**: 使用snake_case (如: task_id, address_data)

## Import Patterns

### Import Order
1. Python标准库
2. 第三方库 (Flask, SQLAlchemy, requests等)
3. 本地模块 (models, services, utils等)

### Module Organization
```python
# 标准库导入
import logging
from datetime import datetime

# 第三方库导入
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import requests

# 本地模块导入
from models.address_info import AddressInfo
from services.crawler_service import CrawlerService
from utils.database import init_db
```

## Code Structure Patterns

### Flask应用结构
```python
# app.py 基本结构
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# 初始化Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345678@localhost:3306/address_collector'

# 初始化扩展
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 注册蓝图和路由
# ...

if __name__ == '__main__':
    app.run()
```

### 模型类结构
```python
# models/address_info.py
from utils.database import db
from datetime import datetime

class AddressInfo(db.Model):
    __tablename__ = 'address_info'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), nullable=False)
    # 其他字段定义...
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 服务类结构
```python
# services/crawler_service.py
import requests
import logging
from models.address_info import AddressInfo
from models.task import Task

class CrawlerService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def crawl_address(self, task: Task) -> AddressInfo:
        # 实现爬虫逻辑
        pass
    
    def parse_response(self, response_data: dict) -> dict:
        # 解析API响应数据
        pass
```

## Code Organization Principles

1. **单一职责**: 每个模块专注于一个功能领域
   - models/: 只包含数据模型定义
   - services/: 只包含业务逻辑
   - utils/: 只包含通用工具函数

2. **分层架构**: 遵循MVC模式
   - 模型层 (Models): 数据定义和数据库操作
   - 服务层 (Services): 业务逻辑处理
   - 调度层 (Scheduler): 任务调度和执行

3. **可测试性**: 代码结构便于单元测试
   - 服务类设计为可独立测试
   - 数据库操作集中在模型层

4. **一致性**: 保持代码风格统一
   - 遵循PEP 8编码规范
   - 使用类型提示提高代码可读性

## Module Boundaries

### 依赖关系
- **models**: 不依赖其他本地模块，只依赖SQLAlchemy
- **services**: 可以依赖models和utils，不依赖scheduler
- **scheduler**: 可以依赖services和models
- **utils**: 只包含通用功能，不依赖业务模块

### 数据流
1. Scheduler → Services (触发任务执行)
2. Services → Models (数据操作)
3. Models → Database (实际存储)
4. Utils → All modules (提供通用功能)

## Code Size Guidelines

- **文件大小**: 建议不超过300行代码
- **类大小**: 建议不超过10个方法
- **函数大小**: 建议不超过50行代码
- **嵌套深度**: 建议不超过3层嵌套

## Database Configuration

### 连接配置
```python
# utils/database.py
DATABASE_URL = "mysql://root:12345678@localhost:3306/address_collector"
```

### 迁移管理
```bash
# 创建迁移
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 日志配置

### 日志结构
```python
# utils/logger.py
import logging

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    # 配置日志格式和输出位置
    return logger
```

### 日志文件位置
- 日志文件保存在 logs/ 目录下
- 按日期或大小轮转日志文件
- 包含错误日志和运行日志