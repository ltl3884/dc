"""
日志配置工具模块

该模块提供集中的日志功能，包括：
- RotatingFileHandler用于日志文件管理
- 控制台和文件日志格式配置
- 根据配置定义日志级别
- 统一的日志接口

作者: Claude Code
创建时间: 2025-09-10
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from src.config import get_logging_config


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称，通常使用__name__
        level: 日志级别，如果为None则使用配置中的级别
        log_to_file: 是否写入日志文件，如果为None则使用配置中的设置
        format_string: 日志格式字符串，如果为None则使用配置中的格式
        
    Returns:
        logging.Logger: 配置好的日志记录器
        
    Raises:
        OSError: 当无法创建日志目录时
        ValueError: 当日志级别无效时
    """
    # 获取日志配置
    config = get_logging_config()
    
    # 使用参数或配置中的值
    log_level = level or config["level"]
    enable_file_logging = log_to_file if log_to_file is not None else config["file_enabled"]
    log_format = format_string or config["format"]
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 如果记录器已经配置过，直接返回
    if logger.handlers:
        return logger
    
    # 设置日志级别
    try:
        logger.setLevel(getattr(logging, log_level.upper()))
    except AttributeError:
        raise ValueError(f"无效的日志级别: {log_level}")
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 配置文件处理器（如果启用）
    if enable_file_logging:
        log_file_path = config["file_path"]
        max_bytes = config["file_max_bytes"]
        backup_count = config["file_backup_count"]
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError as e:
                raise OSError(f"无法创建日志目录 {log_dir}: {e}")
        
        # 创建RotatingFileHandler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 防止日志传播到根记录器
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    如果记录器未配置，则使用默认设置进行配置
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    logger = logging.getLogger(name)
    
    # 如果记录器还没有处理器，则进行配置
    if not logger.handlers:
        logger = setup_logger(name)
    
    return logger


def set_log_level(level: str, logger_name: Optional[str] = None) -> None:
    """
    设置日志级别
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: 日志记录器名称，如果为None则设置根记录器
        
    Raises:
        ValueError: 当日志级别无效时
    """
    try:
        log_level = getattr(logging, level.upper())
    except AttributeError:
        raise ValueError(f"无效的日志级别: {level}")
    
    if logger_name:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        # 同时更新所有处理器的级别
        for handler in logger.handlers:
            handler.setLevel(log_level)
    else:
        # 设置根记录器级别
        logging.root.setLevel(log_level)


def add_file_handler(
    logger_name: str,
    file_path: str,
    max_bytes: int = 10485760,
    backup_count: int = 5,
    level: Optional[str] = None
) -> None:
    """
    为指定的日志记录器添加文件处理器
    
    Args:
        logger_name: 日志记录器名称
        file_path: 日志文件路径
        max_bytes: 单个日志文件最大大小（字节）
        backup_count: 备份文件数量
        level: 日志级别，如果为None则使用记录器当前级别
        
    Raises:
        OSError: 当无法创建日志目录时
    """
    logger = logging.getLogger(logger_name)
    
    # 确保日志目录存在
    log_dir = os.path.dirname(file_path)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"无法创建日志目录 {log_dir}: {e}")
    
    # 创建RotatingFileHandler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    
    # 设置级别
    if level:
        try:
            file_handler.setLevel(getattr(logging, level.upper()))
        except AttributeError:
            raise ValueError(f"无效的日志级别: {level}")
    else:
        file_handler.setLevel(logger.level)
    
    # 设置格式化器
    formatter = logging.Formatter(
        get_logging_config()["format"]
    )
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)


def remove_file_handler(logger_name: str, file_path: str) -> bool:
    """
    从指定的日志记录器移除文件处理器
    
    Args:
        logger_name: 日志记录器名称
        file_path: 日志文件路径
        
    Returns:
        bool: 是否成功移除处理器
    """
    logger = logging.getLogger(logger_name)
    
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            if handler.baseFilename == os.path.abspath(file_path):
                logger.removeHandler(handler)
                handler.close()
                return True
    
    return False