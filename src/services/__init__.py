"""
服务模块初始化文件

该模块提供业务逻辑层的实现，包括任务管理、爬虫服务、数据验证等功能。
提供统一的服务工厂和错误处理机制。
"""

import logging
from typing import Dict, Any, Optional, Type
from functools import wraps

from .task_service import TaskService
from .crawler_service import CrawlerService
from .validation_service import ValidationService
from .data_service import DataService


class ServiceException(Exception):
    """服务层基础异常类"""
    
    def __init__(self, message: str, service_name: str = None, error_code: str = None):
        self.message = message
        self.service_name = service_name
        self.error_code = error_code
        super().__init__(self.message)


def service_error_handler(func):
    """
    服务错误处理装饰器
    
    统一处理服务层异常，提供标准化的错误日志记录。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ServiceException:
            # 已处理的服务异常，直接抛出
            raise
        except Exception as e:
            # 未预期的异常，包装为服务异常
            service_name = args[0].__class__.__name__ if args else 'UnknownService'
            error_msg = f"服务执行失败: {str(e)}"
            logging.error(f"[{service_name}] {error_msg}")
            raise ServiceException(error_msg, service_name)
    
    return wrapper


class ServiceFactory:
    """服务工厂类，提供统一的服务实例创建和管理"""
    
    _instances: Dict[str, Any] = {}
    _service_classes = {
        'task': TaskService,
        'crawler': CrawlerService,
        'validation': ValidationService,
        'data': DataService
    }
    
    @classmethod
    def get_service(cls, service_name: str, **kwargs) -> Any:
        """
        获取服务实例
        
        Args:
            service_name: 服务名称 (task, crawler, validation, data)
            **kwargs: 传递给服务构造函数的参数
            
        Returns:
            服务实例
            
        Raises:
            ServiceException: 服务名称无效时抛出
        """
        if service_name not in cls._service_classes:
            raise ServiceException(f"无效的服务名称: {service_name}")
        
        # 使用单例模式，避免重复创建服务实例
        if service_name not in cls._instances:
            service_class = cls._service_classes[service_name]
            cls._instances[service_name] = service_class(**kwargs)
        
        return cls._instances[service_name]
    
    @classmethod
    def create_task_service(cls, **kwargs) -> TaskService:
        """创建任务服务实例"""
        return cls.get_service('task', **kwargs)
    
    @classmethod
    def create_crawler_service(cls, **kwargs) -> CrawlerService:
        """创建爬虫服务实例"""
        return cls.get_service('crawler', **kwargs)
    
    @classmethod
    def create_validation_service(cls, **kwargs) -> ValidationService:
        """创建验证服务实例"""
        return cls.get_service('validation', **kwargs)
    
    @classmethod
    def create_data_service(cls, **kwargs) -> DataService:
        """创建数据服务实例"""
        return cls.get_service('data', **kwargs)
    
    @classmethod
    def clear_cache(cls) -> None:
        """清除服务实例缓存"""
        cls._instances.clear()


def get_service(service_name: str, **kwargs) -> Any:
    """
    便捷函数：获取服务实例
    
    Args:
        service_name: 服务名称
        **kwargs: 传递给服务构造函数的参数
        
    Returns:
        服务实例
    """
    return ServiceFactory.get_service(service_name, **kwargs)


# 便捷函数别名
task_service = ServiceFactory.create_task_service
crawler_service = ServiceFactory.create_crawler_service
validation_service = ServiceFactory.create_validation_service
data_service = ServiceFactory.create_data_service


__all__ = [
    # 服务类
    'TaskService',
    'CrawlerService', 
    'ValidationService',
    'DataService',
    
    # 异常类
    'ServiceException',
    
    # 装饰器
    'service_error_handler',
    
    # 工厂类
    'ServiceFactory',
    
    # 便捷函数
    'get_service',
    'task_service',
    'crawler_service', 
    'validation_service',
    'data_service'
]