"""
地址爬虫应用配置文件

该模块集中管理应用程序的所有配置项，包括数据库连接、调度器设置和日志配置。
所有配置项都通过环境变量读取，确保配置的灵活性和安全性。
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""
    
    # Flask 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///address_crawler.db"
    )
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ECHO: bool = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    
    # APScheduler 配置
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Shanghai")
    SCHEDULER_JOB_DEFAULTS: Dict[str, Any] = {
        "coalesce": os.getenv("SCHEDULER_COALESCE", "True").lower() == "true",
        "max_instances": int(os.getenv("SCHEDULER_MAX_INSTANCES", "3")),
        "misfire_grace_time": int(os.getenv("SCHEDULER_MISFIRE_GRACE_TIME", "300")),
    }
    SCHEDULER_API_ENABLED: bool = os.getenv("SCHEDULER_API_ENABLED", "True").lower() == "true"
    
    # 自动任务执行配置
    AUTO_EXECUTION_ENABLED: bool = os.getenv("AUTO_EXECUTION_ENABLED", "False").lower() == "true"
    AUTO_EXECUTION_INTERVAL: int = int(os.getenv("AUTO_EXECUTION_INTERVAL", "30"))  # 秒
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOG_FILE_ENABLED: bool = os.getenv("LOG_FILE_ENABLED", "True").lower() == "true"
    LOG_FILE_PATH: str = os.getenv("LOG_FILE_PATH", "logs/app.log")
    LOG_FILE_MAX_BYTES: int = int(os.getenv("LOG_FILE_MAX_BYTES", "10485760"))  # 10MB
    LOG_FILE_BACKUP_COUNT: int = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
    
    # 日志清理配置
    LOG_RETENTION_DAYS: int = int(os.getenv("LOG_RETENTION_DAYS", "30"))
    LOG_MAX_SIZE_MB: int = int(os.getenv("LOG_MAX_SIZE_MB", "100"))
    LOG_COMPRESS_OLD: bool = os.getenv("LOG_COMPRESS_OLD", "True").lower() == "true"
    LOG_CLEANUP_ENABLED: bool = os.getenv("LOG_CLEANUP_ENABLED", "True").lower() == "true"
    
    # 爬虫配置
    CRAWLER_TIMEOUT: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    CRAWLER_RETRY_COUNT: int = int(os.getenv("CRAWLER_RETRY_COUNT", "3"))
    CRAWLER_RETRY_DELAY: int = int(os.getenv("CRAWLER_RETRY_DELAY", "5"))
    
    # API 配置
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.example.com")
    API_KEY: str = os.getenv("API_KEY", "")
    
    @classmethod
    def validate_config(cls) -> None:
        """
        验证配置项的有效性
        
        Raises:
            ValueError: 当必需配置项缺失时
        """
        required_configs = [
            ("DATABASE_URL", cls.DATABASE_URL),
            ("SECRET_KEY", cls.SECRET_KEY),
        ]
        
        for config_name, config_value in required_configs:
            if not config_value:
                raise ValueError(f"必需配置项 {config_name} 未设置")
        
        # 验证日志级别有效性
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            raise ValueError(f"无效的日志级别: {cls.LOG_LEVEL}")


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    SQLALCHEMY_ECHO: bool = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SQLALCHEMY_ECHO: bool = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG: bool = True
    TESTING: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///:memory:"
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL


# 配置映射
config_mapping = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name: str = None) -> Config:
    """
    获取配置实例
    
    Args:
        config_name: 配置名称 (development, production, testing)
        
    Returns:
        Config: 配置类实例
        
    Raises:
        ValueError: 当配置名称无效时
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "default")
    
    config_class = config_mapping.get(config_name)
    if config_class is None:
        raise ValueError(f"无效的配置名称: {config_name}")
    
    return config_class()


def get_database_config() -> Dict[str, Any]:
    """
    获取数据库配置
    
    Returns:
        Dict[str, Any]: 数据库配置字典
    """
    config = get_config()
    return {
        "url": config.DATABASE_URL,
        "echo": config.SQLALCHEMY_ECHO,
        "track_modifications": config.SQLALCHEMY_TRACK_MODIFICATIONS,
    }


def get_scheduler_config() -> Dict[str, Any]:
    """
    获取调度器配置
    
    Returns:
        Dict[str, Any]: 调度器配置字典
    """
    config = get_config()
    return {
        "timezone": config.SCHEDULER_TIMEZONE,
        "job_defaults": config.SCHEDULER_JOB_DEFAULTS,
        "api_enabled": config.SCHEDULER_API_ENABLED,
        "auto_execution_enabled": config.AUTO_EXECUTION_ENABLED,
        "auto_execution_interval": config.AUTO_EXECUTION_INTERVAL,
    }


def get_logging_config() -> Dict[str, Any]:
    """
    获取日志配置
    
    Returns:
        Dict[str, Any]: 日志配置字典
    """
    config = get_config()
    return {
        "level": config.LOG_LEVEL,
        "format": config.LOG_FORMAT,
        "file_enabled": config.LOG_FILE_ENABLED,
        "file_path": config.LOG_FILE_PATH,
        "file_max_bytes": config.LOG_FILE_MAX_BYTES,
        "file_backup_count": config.LOG_FILE_BACKUP_COUNT,
        "retention_days": config.LOG_RETENTION_DAYS,
        "max_size_mb": config.LOG_MAX_SIZE_MB,
        "compress_old": config.LOG_COMPRESS_OLD,
        "cleanup_enabled": config.LOG_CLEANUP_ENABLED,
    }


def get_log_cleanup_config() -> Dict[str, Any]:
    """
    获取日志清理配置
    
    Returns:
        Dict[str, Any]: 日志清理配置字典
    """
    config = get_config()
    return {
        "retention_days": config.LOG_RETENTION_DAYS,
        "max_size_mb": config.LOG_MAX_SIZE_MB,
        "compress_old": config.LOG_COMPRESS_OLD,
        "cleanup_enabled": config.LOG_CLEANUP_ENABLED,
        "backup_count": config.LOG_FILE_BACKUP_COUNT,
        "log_directory": os.path.dirname(config.LOG_FILE_PATH),
    }