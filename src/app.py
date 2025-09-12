"""
Flask应用工厂模块

该模块实现Flask应用的工厂模式，负责创建和配置Flask应用实例，
包括数据库连接、迁移工具和其他扩展的初始化。
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from typing import Optional

from src.config import get_config

# 初始化扩展实例
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    创建Flask应用实例的工厂函数
    
    Args:
        config_name: 配置名称 (development, production, testing)
                    如果为None，则从环境变量FLASK_ENV获取
    
    Returns:
        Flask: 配置完成的Flask应用实例
        
    Raises:
        ValueError: 当配置无效时
        RuntimeError: 当应用创建失败时
    """
    # 创建Flask应用实例
    app = Flask(__name__)
    
    try:
        # 加载配置
        config = get_config(config_name)
        app.config.from_object(config)
        
        # 验证配置
        config.validate_config()
        
        # 初始化扩展
        _init_extensions(app)
        
        # 注册蓝图
        _register_blueprints(app)
        
        # 配置错误处理
        _register_error_handlers(app)
        
        # 配置日志
        _configure_logging(app)
        
        return app
        
    except Exception as e:
        raise RuntimeError(f"创建Flask应用失败: {str(e)}")


def _init_extensions(app: Flask) -> None:
    """
    初始化Flask扩展
    
    Args:
        app: Flask应用实例
    """
    # 初始化数据库
    db.init_app(app)
    
    # 初始化迁移工具
    migrate.init_app(app, db)


def _register_blueprints(app: Flask) -> None:
    """
    注册Flask蓝图
    
    Args:
        app: Flask应用实例
    """
    # TODO: 在这里注册具体的蓝图
    # 例如：
    # from src.api.routes import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')
    pass


def _register_error_handlers(app: Flask) -> None:
    """
    注册错误处理函数
    
    Args:
        app: Flask应用实例
    """
    @app.errorhandler(404)
    def not_found(error):
        """处理404错误"""
        return {"error": "资源未找到"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        return {"error": "服务器内部错误"}, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """处理400错误"""
        return {"error": "请求参数错误"}, 400


def _configure_logging(app: Flask) -> None:
    """
    配置应用日志
    
    Args:
        app: Flask应用实例
    """
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    # 获取日志配置
    log_config = app.config
    
    # 设置日志级别
    log_level = getattr(logging, log_config.get('LOG_LEVEL', 'INFO').upper())
    app.logger.setLevel(log_level)
    
    # 配置日志格式
    formatter = logging.Formatter(
        log_config.get('LOG_FORMAT', 
                      '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # 配置文件日志处理器
    if log_config.get('LOG_FILE_ENABLED', True):
        log_dir = os.path.dirname(log_config.get('LOG_FILE_PATH', 'logs/app.log'))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = RotatingFileHandler(
            log_config.get('LOG_FILE_PATH', 'logs/app.log'),
            maxBytes=log_config.get('LOG_FILE_MAX_BYTES', 10485760),  # 10MB
            backupCount=log_config.get('LOG_FILE_BACKUP_COUNT', 5)
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    
    # 配置控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)


def get_db() -> SQLAlchemy:
    """
    获取数据库实例
    
    Returns:
        SQLAlchemy: 数据库实例
    """
    return db


def get_migrate() -> Migrate:
    """
    获取迁移工具实例
    
    Returns:
        Migrate: 迁移工具实例
    """
    return migrate