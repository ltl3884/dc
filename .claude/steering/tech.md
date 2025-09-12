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