"""
测试工具函数模块

该模块提供各种测试辅助函数，包括数据库操作、数据生成、模拟对象创建等功能。
所有函数都遵循DRY和KISS原则，提供简单易用的测试工具。
"""

import json
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Type
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.models import Task, AddressInfo as Address
# TODO: 导入服务类（需要先创建这些服务）
# from src.services.task_service import TaskService
# from src.services.crawler_service import CrawlerService
# from src.services.data_service import DataService

# 临时定义状态枚举，直到实际模型创建
class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def create_test_task_data(**kwargs) -> Dict[str, Any]:
    """
    创建测试任务数据
    
    Args:
        **kwargs: 自定义任务数据字段
        
    Returns:
        Dict[str, Any]: 任务数据字典
    """
    default_data = {
        "name": f"测试任务_{generate_random_string(6)}",
        "description": "这是一个测试任务",
        "task_type": "address_crawl",
        "priority": TaskPriority.MEDIUM,
        "status": TaskStatus.PENDING,
        "url": "https://example.com/addresses",
        "parameters": {"city": "北京", "district": "朝阳区"},
        "max_retry_count": 3,
        "timeout": 30,
        "scheduled_time": datetime.now(),
    }
    
    # 合并自定义数据
    default_data.update(kwargs)
    return default_data


def create_test_address_data(**kwargs) -> Dict[str, Any]:
    """
    创建测试地址数据
    
    Args:
        **kwargs: 自定义地址数据字段
        
    Returns:
        Dict[str, Any]: 地址数据字典
    """
    default_data = {
        "province": "北京市",
        "city": "北京市",
        "district": "朝阳区",
        "street": "建国路",
        "detail_address": "建国路88号",
        "full_address": "北京市朝阳区建国路88号",
        "longitude": 116.4619,
        "latitude": 39.9075,
        "postal_code": "100022",
        "phone": "010-12345678",
        "business_hours": "09:00-18:00",
        "category": "商业大厦",
        "source": "test_source",
        "crawl_time": datetime.now(),
    }
    
    # 合并自定义数据
    default_data.update(kwargs)
    return default_data


# TODO: 创建测试爬虫结果数据（需要先创建CrawlResult模型）
# def create_test_crawl_result_data(**kwargs) -> Dict[str, Any]:
#     """
#     创建测试爬虫结果数据
#     
#     Args:
#         **kwargs: 自定义爬虫结果数据字段
#         
#     Returns:
#         Dict[str, Any]: 爬虫结果数据字典
#     """
#     default_data = {
#         "task_id": 1,
#         "url": "https://example.com/addresses",
#         "status_code": 200,
#         "response_data": '{"addresses": [{"province": "北京市", "city": "北京市"}]}',
#         "error_message": None,
#         "crawl_time": datetime.now(),
#         "response_time": 1.5,
#         "data_count": 1,
#     }
#     
#     # 合并自定义数据
#     default_data.update(kwargs)
#     return default_data


def generate_random_string(length: int = 8) -> str:
    """
    生成随机字符串
    
    Args:
        length: 字符串长度，默认为8
        
    Returns:
        str: 随机字符串
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_phone() -> str:
    """
    生成随机电话号码
    
    Returns:
        str: 随机电话号码
    """
    prefix = random.choice(["010-", "021-", "022-", "023-", "024-", "025-", "027-", "028-", "029-"])
    number = ''.join(random.choices(string.digits, k=8))
    return f"{prefix}{number}"


def generate_random_coordinates() -> tuple[float, float]:
    """
    生成随机经纬度坐标
    
    Returns:
        tuple[float, float]: (经度, 纬度)
    """
    longitude = random.uniform(73.0, 135.0)  # 中国经度范围
    latitude = random.uniform(3.0, 54.0)     # 中国纬度范围
    return (round(longitude, 6), round(latitude, 6))


def create_mock_task(
    session: Session,
    status: TaskStatus = TaskStatus.PENDING,
    priority: TaskPriority = TaskPriority.MEDIUM,
    **kwargs
) -> Task:
    """
    创建模拟任务
    
    Args:
        session: 数据库会话
        status: 任务状态，默认为PENDING
        priority: 任务优先级，默认为MEDIUM
        **kwargs: 其他任务参数
        
    Returns:
        Task: 创建的任务实例
    """
    task_data = create_test_task_data(status=status, priority=priority, **kwargs)
    task = Task(**task_data)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def create_mock_address(
    session: Session,
    province: str = "北京市",
    city: str = "北京市",
    **kwargs
) -> Address:
    """
    创建模拟地址
    
    Args:
        session: 数据库会话
        province: 省份，默认为"北京市"
        city: 城市，默认为"北京市"
        **kwargs: 其他地址参数
        
    Returns:
        Address: 创建的地址实例
    """
    address_data = create_test_address_data(province=province, city=city, **kwargs)
    address = Address(**address_data)
    session.add(address)
    session.commit()
    session.refresh(address)
    return address


# TODO: 创建模拟爬虫结果（需要先创建CrawlResult模型）
# def create_mock_crawl_result(
#     session: Session,
#     task_id: int,
#     status_code: int = 200,
#     **kwargs
# ) -> CrawlResult:
#     """
#     创建模拟爬虫结果
#     
#     Args:
#         session: 数据库会话
#         task_id: 关联的任务ID
#         status_code: HTTP状态码，默认为200
#         **kwargs: 其他爬虫结果参数
#         
#     Returns:
#         CrawlResult: 创建的爬虫结果实例
#     """
#     result_data = create_test_crawl_result_data(
#         task_id=task_id,
#         status_code=status_code,
#         **kwargs
#     )
#     crawl_result = CrawlResult(**result_data)
#     session.add(crawl_result)
#     session.commit()
#     session.refresh(crawl_result)
#     return crawl_result


def create_mock_response(
    status_code: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    text_data: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Mock:
    """
    创建模拟HTTP响应
    
    Args:
        status_code: HTTP状态码，默认为200
        json_data: JSON响应数据，默认为None
        text_data: 文本响应数据，默认为None
        headers: 响应头，默认为None
        
    Returns:
        Mock: 模拟的响应对象
    """
    response = Mock()
    response.status_code = status_code
    response.headers = headers or {}
    
    if json_data is not None:
        response.json.return_value = json_data
        response.text = json.dumps(json_data)
    elif text_data is not None:
        response.text = text_data
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", text_data, 0)
    else:
        response.text = ""
        response.json.return_value = {}
    
    response.raise_for_status.side_effect = None
    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(f"HTTP {status_code} Error")
    
    return response


def create_mock_session() -> Mock:
    """
    创建模拟数据库会话
    
    Returns:
        Mock: 模拟的数据库会话对象
    """
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    session.refresh = Mock()
    session.query = Mock()
    return session


def assert_task_created(
    task: Task,
    expected_name: str,
    expected_status: TaskStatus = TaskStatus.PENDING,
    expected_priority: TaskPriority = TaskPriority.MEDIUM
) -> None:
    """
    断言任务创建正确
    
    Args:
        task: 任务实例
        expected_name: 期望的任务名称
        expected_status: 期望的任务状态，默认为PENDING
        expected_priority: 期望的任务优先级，默认为MEDIUM
    """
    assert task is not None
    assert task.name == expected_name
    assert task.status == expected_status
    assert task.priority == expected_priority
    assert task.created_at is not None


def assert_address_created(
    address: Address,
    expected_province: str,
    expected_city: str,
    expected_district: str
) -> None:
    """
    断言地址创建正确
    
    Args:
        address: 地址实例
        expected_province: 期望的省份
        expected_city: 期望的城市
        expected_district: 期望的区县
    """
    assert address is not None
    assert address.province == expected_province
    assert address.city == expected_city
    assert address.district == expected_district
    assert address.created_at is not None


# TODO: 断言爬虫结果创建正确（需要先创建CrawlResult模型）
# def assert_crawl_result_created(
#     result: CrawlResult,
#     expected_task_id: int,
#     expected_status_code: int = 200
# ) -> None:
#     """
#     断言爬虫结果创建正确
#     
#     Args:
#         result: 爬虫结果实例
#         expected_task_id: 期望的关联任务ID
#         expected_status_code: 期望的HTTP状态码，默认为200
#     """
#     assert result is not None
#     assert result.task_id == expected_task_id
#     assert result.status_code == expected_status_code
#     assert result.crawl_time is not None


def bulk_create_tasks(
    session: Session,
    count: int = 10,
    status: TaskStatus = TaskStatus.PENDING,
    priority: TaskPriority = TaskPriority.MEDIUM
) -> List[Task]:
    """
    批量创建任务
    
    Args:
        session: 数据库会话
        count: 创建任务数量，默认为10
        status: 任务状态，默认为PENDING
        priority: 任务优先级，默认为MEDIUM
        
    Returns:
        List[Task]: 创建的任务列表
    """
    tasks = []
    for i in range(count):
        task = create_mock_task(
            session,
            status=status,
            priority=priority,
            name=f"批量任务_{i+1}"
        )
        tasks.append(task)
    return tasks


def bulk_create_addresses(
    session: Session,
    count: int = 10,
    province: str = "北京市"
) -> List[Address]:
    """
    批量创建地址
    
    Args:
        session: 数据库会话
        count: 创建地址数量，默认为10
        province: 省份，默认为"北京市"
        
    Returns:
        List[Address]: 创建的地址列表
    """
    addresses = []
    for i in range(count):
        longitude, latitude = generate_random_coordinates()
        address = create_mock_address(
            session,
            province=province,
            detail_address=f"测试地址_{i+1}",
            longitude=longitude,
            latitude=latitude
        )
        addresses.append(address)
    return addresses


def create_test_file(content: str = "测试数据\n", suffix: str = ".txt") -> str:
    """
    创建测试文件
    
    Args:
        content: 文件内容，默认为"测试数据\n"
        suffix: 文件后缀，默认为".txt"
        
    Returns:
        str: 文件路径
    """
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def mock_time_now(fixed_time: datetime) -> Mock:
    """
    创建固定时间的mock
    
    Args:
        fixed_time: 固定时间
        
    Returns:
        Mock: 时间mock对象
    """
    mock_datetime = Mock()
    mock_datetime.now.return_value = fixed_time
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
    return mock_datetime


def assert_database_query_executed(session_mock: Mock, expected_model: Type) -> None:
    """
    断言数据库查询已执行
    
    Args:
        session_mock: 模拟的数据库会话
        expected_model: 期望查询的模型类
    """
    assert session_mock.query.called
    # 这里可以添加更具体的断言逻辑


# TODO: 创建带有模拟会话的服务实例（需要先创建服务类）
# def create_service_with_mock_session(service_class: Type) -> tuple[Any, Mock]:
#     """
#     创建带有模拟会话的服务实例
#     
#     Args:
#         service_class: 服务类
#         
#     Returns:
#         tuple[Any, Mock]: (服务实例, 模拟会话)
#     """
#     mock_session = create_mock_session()
#     service = service_class(mock_session)
#     return service, mock_session