"""
模型包初始化模块

该模块提供项目中所有数据库模型的集中导入和初始化功能，
包括模型注册表和模型级工具函数，为迁移工具和模型管理提供便利。
"""

from typing import Dict, Type, Any
from sqlalchemy.ext.declarative import DeclarativeMeta

# 导入所有模型类
from src.models.task import Task
from src.models.address_info import AddressInfo

# 模型注册表 - 供迁移工具使用
MODEL_REGISTRY: Dict[str, Type[DeclarativeMeta]] = {
    'Task': Task,
    'AddressInfo': AddressInfo,
}

# 定义 __all__ 控制模块的公开接口
__all__ = [
    'Task',
    'AddressInfo', 
    'MODEL_REGISTRY',
    'get_model_class',
    'get_all_models',
    'get_model_names',
]


def get_model_class(model_name: str) -> Type[DeclarativeMeta]:
    """
    根据模型名称获取模型类
    
    Args:
        model_name: 模型名称
        
    Returns:
        Type[DeclarativeMeta]: 模型类
        
    Raises:
        KeyError: 如果模型名称不存在
        
    Example:
        >>> TaskClass = get_model_class('Task')
        >>> task = TaskClass(url='https://example.com')
    """
    return MODEL_REGISTRY[model_name]


def get_all_models() -> Dict[str, Type[DeclarativeMeta]]:
    """
    获取所有注册的模型
    
    Returns:
        Dict[str, Type[DeclarativeMeta]]: 包含所有模型类的字典
        
    Example:
        >>> all_models = get_all_models()
        >>> for name, model_class in all_models.items():
        ...     print(f"Model: {name}")
    """
    return MODEL_REGISTRY.copy()


def get_model_names() -> list[str]:
    """
    获取所有模型名称列表
    
    Returns:
        list[str]: 模型名称列表，按字母顺序排列
        
    Example:
        >>> names = get_model_names()
        >>> print(names)
        ['AddressInfo', 'Task']
    """
    return sorted(MODEL_REGISTRY.keys())


def register_model(model_class: Type[DeclarativeMeta]) -> None:
    """
    注册新的模型类到模型注册表
    
    Args:
        model_class: 要注册的模型类
        
    Example:
        >>> from src.models.custom_model import CustomModel
        >>> register_model(CustomModel)
    """
    model_name = model_class.__name__
    MODEL_REGISTRY[model_name] = model_class
    
    # 动态更新 __all__
    if model_name not in __all__:
        __all__.append(model_name)


def is_registered_model(model_name: str) -> bool:
    """
    检查模型是否已注册
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 如果模型已注册返回 True
        
    Example:
        >>> is_registered_model('Task')
        True
        >>> is_registered_model('NonExistentModel')
        False
    """
    return model_name in MODEL_REGISTRY