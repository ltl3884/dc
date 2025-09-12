# address-crawler - Task 2

Execute task 2 for the address-crawler specification.

## Task Description
Create main application configuration file

## Requirements Reference
**Requirements**: 1.2, 5.1

## Usage
```
/Task:2-address-crawler
```

## Instructions

Execute with @spec-task-executor agent the following task: "Create main application configuration file"

```
Use the @spec-task-executor agent to implement task 2: "Create main application configuration file" for the address-crawler specification and include all the below context.

# Steering Context
## Steering Documents Context (Pre-loaded)

### Product Context
# Product Overview

## Product Purpose
构建一个简单的地址信息爬虫应用，从指定API接口抓取地址数据并存储到MySQL数据库中。专注于实现核心功能，不考虑复杂的性能优化和安全机制。

## Target Users
- 需要收集和存储地址信息的个人用户
- 小型项目需要地址数据的应用开发者
- 学习和练习爬虫技术的开发者

## Key Features

1. **定时爬虫任务**: 使用APScheduler每秒自动执行爬虫任务
2. **任务管理**: 支持创建和管理多个爬虫任务，跟踪任务执行状态
3. **数据存储**: 自动将爬取到的地址信息存储到MySQL数据库
4. **简单配置**: 使用Flask框架和SQLAlchemy ORM简化开发

## Business Objectives
- 提供简单易用的地址数据收集工具
- 实现自动化的数据采集流程
- 支持基本的数据管理和存储功能

## Success Metrics
- **任务执行成功率**: 爬虫任务正常执行并完成数据存储
- **数据收集量**: 每日收集的地址信息数量
- **系统稳定性**: 长时间运行的稳定性（7x24小时）

## Product Principles

1. **简单优先**: 保持代码和架构简单，避免过度设计
2. **功能完整**: 确保核心爬虫功能完整可用
3. **易于维护**: 代码结构清晰，便于后续维护和扩展

## Monitoring & Visibility
- **日志系统**: 使用Python logging模块记录运行状态和错误信息
- **数据库状态**: 通过查询tasks表和address_info表监控任务执行情况
- **控制台输出**: 实时显示爬虫执行状态和结果

## Future Vision
### Potential Enhancements
- **错误重试机制**: 添加失败任务的重试功能
- **数据去重**: 避免存储重复的地址信息
- **Web界面**: 提供简单的Web管理界面
- **多数据源**: 支持从多个API接口采集数据

---

### Technology Context
# Technology Stack

## Project Type
Web爬虫应用，使用Flask框架构建，集成定时任务调度器进行自动化数据采集

## Core Technologies

### Primary Language(s)
- **Language**: Python 3.11
- **Package Management**: uv + pyproject.toml
- **Virtual Environment**: .venv (激活命令: source .venv/bin/activate)

### Key Dependencies/Libraries
- **Flask**: Web应用框架
- **Flask-SQLAlchemy**: ORM框架，简化数据库操作
- **Flask-Migrate**: 数据库迁移工具
- **APScheduler**: 定时任务调度器，每秒执行爬虫任务
- **requests**: HTTP请求库，用于API调用
- **MySQL**: 数据库存储地址信息和任务状态
- **Python logging**: 日志记录模块

### Application Architecture
- **分层架构**: Models(数据层) - Services(服务层) - Scheduler(调度层)
- **模块化设计**: 爬虫逻辑、任务管理、数据存储分离
- **定时驱动**: APScheduler触发任务执行

### Data Storage
- **Primary storage**: MySQL (mysql://root:12345678@localhost:3306/address_collector)
- **数据格式**: JSON (API响应), SQL (数据库存储)
- **主要表结构**: 
  - address_info: 存储爬取到的地址信息
  - tasks: 存储爬虫任务信息和执行状态

### External Integrations
- **API接口**: https://www.meiguodizhi.com/api/v1/dz
- **协议**: HTTP/HTTPS
- **数据格式**: JSON响应，包含地址、电话、城市等信息

## Development Environment

### Build & Development Tools
- **Package Management**: uv (现代Python包管理器)
- **项目配置**: pyproject.toml
- **虚拟环境**: 使用.venv目录，需手动激活

### Code Quality Tools
- **代码规范**: 遵循PEP 8标准
- **类型提示**: 推荐使用Python类型提示
- **测试**: 无特定测试框架要求

### Version Control & Collaboration
- **VCS**: Git
- **分支策略**: 简单分支管理，主分支开发

## Deployment & Distribution
- **运行环境**: 本地Python环境
- **数据库**: 本地MySQL服务
- **部署步骤**: 
  1. 激活虚拟环境: source .venv/bin/activate
  2. 安装依赖: uv pip install -r requirements
  3. 配置数据库连接
  4. 启动应用和调度器

## Technical Requirements & Constraints

### Performance Requirements
- **响应时间**: 无严格要求，以稳定性为主
- **并发处理**: 单线程顺序执行任务
- **内存使用**: 保持较低内存占用

### Compatibility Requirements
- **Python版本**: 3.11+
- **数据库**: MySQL 5.7+
- **操作系统**: 跨平台支持（Linux/macOS/Windows）

### Security & Compliance
- **安全要求**: 无特殊安全要求，本地环境使用
- **数据保护**: 本地数据库存储，无敏感信息传输

### Scalability & Reliability
- **预期负载**: 单机运行，处理少量定时任务
- **可用性**: 7x24小时运行，失败时记录日志
- **错误处理**: 简单日志记录，无复杂重试机制

## Technical Decisions & Rationale

### Decision Log
1. **Flask框架选择**: 轻量级，适合简单爬虫应用，学习成本低
2. **SQLAlchemy ORM**: 简化数据库操作，避免手写SQL
3. **APScheduler**: 内置定时任务支持，配置简单
4. **MySQL数据库**: 关系型数据库适合结构化地址数据存储

## Known Limitations
- **无重试机制**: 失败任务不会自动重试，需要手动处理
- **单线程执行**: 任务按顺序执行，无法并发处理
- **无数据去重**: 可能存储重复的地址信息
- **简单错误处理**: 仅记录日志，无复杂异常恢复机制

---

### Structure Context
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

**Note**: Steering documents have been pre-loaded. Do not use get-content to fetch them again.

# Specification Context
## Specification Context (Pre-loaded): address-crawler

### Requirements
# Requirements Document

## Introduction

地址爬虫功能将构建一个自动化的地址信息采集系统，通过定时任务从指定的API接口获取地址数据，并存储到MySQL数据库中。该功能专注于实现简单易用的核心爬虫功能，为地址数据收集提供基础支撑。

## Alignment with Product Vision

此功能完全符合产品愿景中的关键要素：
- **简单优先**: 采用Flask + SQLAlchemy的简洁架构，避免过度设计
- **功能完整**: 实现从API调用到数据存储的完整爬虫流程
- **易于维护**: 模块化设计，代码结构清晰，便于后续扩展

通过实现定时爬虫任务，该功能将自动化地址数据采集流程，减少人工干预，提高数据收集效率。

## Requirements

### Requirement 1: 基础爬虫功能

**User Story:** 作为系统管理员，我想要系统能够自动从API获取地址数据，以便无需手动操作就能收集地址信息。

#### Acceptance Criteria

1. WHEN 爬虫任务被触发 THEN 系统 SHALL 向 https://www.meiguodizhi.com/api/v1/dz 发送HTTP GET请求
2. IF API返回状态码为200 THEN 系统 SHALL 解析JSON响应数据，格式为：{"address": {"Address": "...", "Telephone": "...", "City": "...", "Zip_Code": "...", "State": "...", "State_Full": "..."}, "status": "ok"}
3. WHEN 成功获取地址数据 THEN 系统 SHALL 提取address、telephone、city、zip_code、state、state_full字段
4. WHEN API返回其他错误状态码 THEN 系统 SHALL 记录错误信息并跳过当前任务

### Requirement 2: 数据存储功能

**User Story:** 作为数据管理员，我想要系统能够将爬取到的地址信息保存到数据库，以便后续查询和使用。

#### Acceptance Criteria

1. WHEN 爬虫成功获取地址数据 THEN 系统 SHALL 将数据保存到address_info表，包含字段：address、telephone、city、zip_code、state、state_full、country、source_url、created_at、updated_at
2. IF 数据保存失败 THEN 系统 SHALL 记录错误日志并继续执行下一个任务
3. WHEN 数据保存成功 THEN 系统 SHALL 记录成功日志并更新任务状态
4. IF 检测到重复地址（相同address和telephone） THEN 系统 SHALL 跳过保存并记录跳过的数据
5. WHEN 必填字段（address、telephone）为空 THEN 系统 SHALL 跳过保存并记录验证错误

### Requirement 3: 任务调度功能

**User Story:** 作为系统维护人员，我想要系统能够每秒自动执行爬虫任务，以便持续收集地址数据。

#### Acceptance Criteria

1. WHEN 系统启动时 THEN 系统 SHALL 初始化APScheduler并配置每秒执行的任务
2. IF 存在未完成的任务(visited_num < total_num) THEN 系统 SHALL 选择第一个任务执行
3. WHEN 任务执行完成后 THEN 系统 SHALL 更新visited_num字段+1，如visited_num >= total_num则标记任务完成
4. IF 任务执行过程中发生异常 THEN 系统 SHALL 记录异常信息并继续执行其他任务
5. WHEN 没有待执行任务时 THEN 系统 SHALL 记录空闲状态并等待下一秒调度

### Requirement 4: 任务管理功能

**User Story:** 作为任务管理员，我想要能够创建和管理爬虫任务，以便控制数据收集的范围和频率。

#### Acceptance Criteria

1. WHEN 创建新任务时 THEN 系统 SHALL 接受url、method、total_num、body、headers、timeout参数，其中timeout默认值为30秒
2. IF 任务参数验证失败（如total_num <= 0） THEN 系统 SHALL 返回错误信息并拒绝创建任务
3. WHEN 查询任务状态时 THEN 系统 SHALL 返回任务的当前状态、已执行次数、总次数、创建时间和更新时间
4. IF 任务已完成(visited_num >= total_num) THEN 系统 SHALL 将状态标记为"completed"
5. WHEN 任务正在执行时 THEN 系统 SHALL 将状态标记为"running"

### Requirement 5: 日志记录功能

**User Story:** 作为系统运维人员，我想要系统能够记录运行日志，以便监控爬虫执行状态和排查问题。

#### Acceptance Criteria

1. WHEN 系统运行时 THEN 系统 SHALL 记录所有关键操作（任务开始、成功、失败、跳过）
2. IF 发生异常 THEN 系统 SHALL 记录异常信息、堆栈跟踪和上下文数据
3. WHEN 日志文件达到10MB时 THEN 系统 SHALL 自动轮转日志文件，保留最近7天的日志
4. IF API限流发生时 THEN 系统 SHALL 记录限流信息和重试次数
5. WHEN 数据验证失败时 THEN 系统 SHALL 记录验证失败的具体原因和相关数据

### Requirement 6: 数据验证和质量控制

**User Story:** 作为数据管理员，我想要系统能够验证和保证数据质量，以确保收集到的地址信息准确可用。

#### Acceptance Criteria

1. WHEN 保存地址数据前 THEN 系统 SHALL 验证必填字段（address、telephone）不为空且格式正确
2. IF address字段长度超过1024字符 THEN 系统 SHALL 截断至1024字符并记录警告
3. IF telephone字段包含非数字字符 THEN 系统 SHALL 移除非法字符并记录处理信息
4. WHEN 检测到重复地址（相同address和telephone组合） THEN 系统 SHALL 跳过保存并记录跳过的原因

### Requirement 7: 系统监控和状态报告

**User Story:** 作为系统运维人员，我想要系统能够提供运行状态报告，以便监控整体健康状况。

#### Acceptance Criteria

1. WHEN 系统运行时 THEN 系统 SHALL 每分钟输出一次统计信息（成功任务数、失败任务数、跳过任务数）
2. IF 连续失败任务数超过10个 THEN 系统 SHALL 输出警告信息并建议检查API可用性

---

### Design
# Design Document

## Overview

地址爬虫功能将构建一个完整的自动化地址数据采集系统，通过Flask框架集成APScheduler实现定时任务调度，使用SQLAlchemy ORM进行数据库操作，从指定API接口获取地址数据并存储到MySQL数据库。该系统遵循分层架构设计，包含数据模型层、服务层、调度层，确保代码结构清晰、易于维护和扩展。

## Steering Document Alignment

### Technical Standards (tech.md)
- **Python 3.11**: 使用最新稳定版本，遵循PEP 8编码规范
- **Flask框架**: 轻量级Web框架，适合构建简单爬虫应用
- **SQLAlchemy ORM**: 简化数据库操作，避免手写SQL语句
- **APScheduler**: 内置定时任务支持，配置简单可靠
- **MySQL数据库**: 本地关系型数据库，存储结构化地址数据
- **requests库**: 处理HTTP请求，支持API调用
- **Python logging**: 标准日志模块，提供完整的日志记录功能

### Project Structure (structure.md)
- **分层架构**: models/ (数据层) → services/ (服务层) → scheduler/ (调度层)
- **模块化设计**: 爬虫逻辑、任务管理、数据存储分离
- **命名规范**: snake_case文件命名，PascalCase类名，遵循PEP 8
- **导入顺序**: 标准库 → 第三方库 → 本地模块
- **代码组织**: 单一职责原则，每个模块专注于特定功能

## Code Reuse Analysis

### Existing Components to Leverage
由于这是新建项目，暂无现有组件可复用。将基于Flask生态系统的标准实践构建所有组件。

### Integration Points
- **MySQL数据库**: 使用SQLAlchemy ORM连接，遵循转向文档中的数据库URL配置
- **API接口**: 集成https://www.meiguodizhi.com/api/v1/dz，处理JSON响应格式
- **日志系统**: 基于Python标准logging模块，支持文件轮转和级别控制
- **定时调度**: 集成APScheduler到Flask应用，实现每秒任务触发

## Architecture

```mermaid
graph TD
    A[APScheduler] -->|每秒触发| B[TaskScheduler]
    B -->|获取待执行任务| C[TaskService]
    C -->|查询数据库| D[Task Model]
    C -->|返回任务| B
    B -->|执行任务| E[CrawlerService]
    E -->|发送HTTP请求| F[API Interface]
    F -->|返回JSON数据| E
    E -->|数据验证| G[DataValidator]
    G -->|验证通过| H[AddressInfo Model]
    G -->|验证失败| I[Logger]
    H -->|保存数据| J[MySQL Database]
    E -->|更新任务状态| C
    C -->|更新数据库| D
    I -->|记录日志| K[Log Files]
    
    style A fill:#e1f5fe
    style J fill:#f3e5f5
    style K fill:#fff3e0
```

## Components and Interfaces

### Component 1: TaskScheduler (调度器)
- **Purpose**: 管理定时任务执行，每秒检查并触发待执行的爬虫任务
- **Interfaces**: 
  - `start_scheduler()`: 启动定时调度器
  - `stop_scheduler()`: 停止定时调度器
  - `execute_pending_tasks()`: 执行待处理任务
- **Dependencies**: APScheduler, TaskService, Logger
- **Reuses**: APScheduler的BackgroundScheduler用于后台任务调度

### Component 2: TaskService (任务服务)
- **Purpose**: 管理爬虫任务的生命周期，包括创建、查询、状态更新
- **Interfaces**:
  - `create_task(url, method, total_num, **kwargs)`: 创建新任务
  - `get_pending_task()`: 获取待执行任务
  - `update_task_status(task_id, status, increment=True)`: 更新任务状态
  - `get_task_statistics()`: 获取任务统计信息
- **Dependencies**: Task Model, Database, Logger
- **Reuses**: SQLAlchemy ORM进行数据库操作

### Component 3: CrawlerService (爬虫服务)
- **Purpose**: 执行具体的爬虫逻辑，包括API调用、数据解析、数据存储
- **Interfaces**:
  - `crawl_address(task)`: 执行地址爬取任务
  - `parse_api_response(response_data)`: 解析API响应数据
  - `save_address_data(address_data, source_url)`: 保存地址数据
  - `handle_api_error(status_code, response)`: 处理API错误
- **Dependencies**: requests库, AddressInfo Model, DataValidator, Logger
- **Reuses**: requests库处理HTTP请求，SQLAlchemy进行数据持久化

### Component 4: DataValidator (数据验证器)
- **Purpose**: 验证爬取到的地址数据，确保数据质量和完整性
- **Interfaces**:
  - `validate_address_data(data)`: 验证地址数据完整性
  - `check_duplicate_address(address, telephone)`: 检查重复地址
  - `sanitize_telephone(telephone)`: 清理电话号码格式
  - `truncate_long_fields(data)`: 截断过长字段
- **Dependencies**: AddressInfo Model, Logger
- **Reuses**: SQLAlchemy查询进行重复性检查

### Component 5: Logger (日志管理器)
- **Purpose**: 统一管理日志记录，支持文件轮转和多级别输出
- **Interfaces**:
  - `info(message, **kwargs)`: 记录信息日志
  - `error(message, exception=None, **kwargs)`: 记录错误日志
  - `warning(message, **kwargs)`: 记录警告日志
  - `debug(message, **kwargs)`: 记录调试日志
- **Dependencies**: Python logging模块
- **Reuses**: logging的RotatingFileHandler实现日志文件轮转

## Data Models

### Task Model
```python
class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(500), nullable=False)
    method = db.Column(db.String(10), nullable=False, default='GET')
    body = db.Column(db.Text, nullable=True)
    headers = db.Column(db.Text, nullable=True)
    total_num = db.Column(db.Integer, nullable=False)
    visited_num = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='pending')
    timeout = db.Column(db.Integer, nullable=False, default=30)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### AddressInfo Model
```python
class AddressInfo(db.Model):
    __tablename__ = 'address_info'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    address = db.Column(db.String(1024), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    state_full = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True, default='USA')
    source_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

## Error Handling

### Error Scenarios
1. **API限流错误（429状态码）**
   - **处理**: 等待60秒后自动重试，最多重试3次
   - **用户影响**: 日志中记录限流信息，不影响其他任务执行

2. **网络连接超时**
   - **处理**: 记录超时错误，跳过当前任务，继续执行下一个任务
   - **用户影响**: 控制台显示超时警告，不影响系统整体运行

3. **数据验证失败**
   - **处理**: 记录验证错误详情，跳过无效数据，继续处理下一条数据
   - **用户影响**: 日志显示具体的验证失败原因

4. **数据库连接失败**
   - **处理**: 尝试重新连接，最多重试5次，记录连接失败错误
   - **用户影响**: 控制台显示数据库连接错误，系统继续运行其他任务

5. **重复数据检测**
   - **处理**: 检测到重复地址时跳过保存，记录跳过的原因
   - **用户影响**: 日志显示数据跳过信息，保证数据唯一性

6. **系统异常**
   - **处理**: 捕获所有未处理异常，记录异常信息和堆栈跟踪
   - **用户影响**: 系统保持运行状态，单个任务失败不影响整体运行

## Testing Strategy

### Unit Testing
- **模型层测试**: 验证Task和AddressInfo模型的数据完整性和约束
- **服务层测试**: 测试TaskService的任务管理功能和CrawlerService的爬虫逻辑
- **验证器测试**: 测试DataValidator的数据验证和清理功能
- **日志测试**: 验证Logger的各级别日志输出和文件轮转功能

### Integration Testing
- **数据库集成**: 测试SQLAlchemy ORM与MySQL数据库的连接和操作
- **API集成**: 测试与https://www.meiguodizhi.com/api/v1/dz的实际调用和数据获取
- **调度器集成**: 测试APScheduler的定时任务触发和执行
- **错误处理集成**: 测试各种错误场景下的系统行为和恢复机制

### End-to-End Testing
- **完整爬虫流程**: 从任务创建到数据存储的完整流程测试
- **并发任务处理**: 测试多个任务同时执行时的系统表现
- **系统稳定性**: 长时间运行测试，验证系统的稳定性和资源使用
- **数据质量验证**: 验证数据去重、验证、清理功能的有效性

**Note**: Specification documents have been pre-loaded. Do not use get-content to fetch them again.

## Task Details
- Task ID: 2
- Description: Create main application configuration file
- Requirements: 1.2, 5.1

## Instructions
- Implement ONLY task 2: "Create main application configuration file"
- Follow all project conventions and leverage existing code
- Mark the task as complete using: claude-code-spec-workflow get-tasks address-crawler 2 --mode complete
- Provide a completion summary
```

## Task Completion
When the task is complete, mark it as done:
```bash
claude-code-spec-workflow get-tasks address-crawler 2 --mode complete
```

## Next Steps
After task completion, you can:
- Execute the next task using /address-crawler-task-[next-id]
- Check overall progress with /spec-status address-crawler
