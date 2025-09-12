# Address Crawler

地址爬虫应用 - 基于Flask的Web爬虫系统，用于自动化地址数据收集。

## 功能特性

- 🕷️ 自动化地址数据爬取
- ⏰ 基于APScheduler的任务调度
- 💾 SQLite数据库存储
- 🌐 Flask Web应用框架
- 📊 任务执行统计和监控
- 🔄 支持多种HTTP请求方法

## 快速开始

### 环境要求

- Python 3.8+
- uv (Python包管理器)

### 安装依赖

```bash
# 安装项目依赖
uv sync
```

### 配置环境

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 数据库初始化

```bash
# 初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 启动应用

```bash
# 开发模式
python src/main.py

# 生产模式
FLASK_ENV=production python src/main.py
```

## 项目结构

```
├── src/
│   ├── app.py              # Flask应用工厂
│   ├── config.py           # 配置管理
│   ├── main.py             # 应用入口
│   ├── models/             # 数据模型
│   ├── services/           # 业务逻辑层
│   ├── scheduler/          # 任务调度器
│   └── utils/              # 工具函数
├── tests/                  # 测试代码
├── migrations/             # 数据库迁移
└── requirements.txt        # 项目依赖
```

## 配置说明

主要环境变量：

- `FLASK_ENV`: 运行环境 (development/production)
- `FLASK_HOST`: 绑定主机地址
- `FLASK_PORT`: 监听端口
- `SECRET_KEY`: 应用密钥
- `DATABASE_URL`: 数据库连接URL

## API端点

- `GET /`: 应用首页
- `GET /health`: 健康检查
- `GET /api/tasks`: 任务列表
- `POST /api/tasks`: 创建任务
- `GET /api/tasks/<id>`: 任务详情

## 开发指南

### 运行测试

```bash
python run_tests.py
```

### 代码格式化

```bash
black src/ tests/
```

### 类型检查

```bash
mypy src/
```

## License

MIT License