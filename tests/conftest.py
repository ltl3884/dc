"""
测试配置和夹具模块

该模块为测试提供集中化的配置管理和数据夹具，包括测试数据库初始化、
测试数据创建和清理等功能。所有测试用例都可以使用这里定义的夹具。
"""

import os
import tempfile
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import TestingConfig, get_config
from src.utils.database import DatabaseManager, init_database, close_database
from src.app import db
from src.models import Task, AddressInfo as Address
# TODO: 导入服务类（需要先创建这些服务）
# from src.scheduler.task_scheduler import TaskScheduler
# from src.services.task_service import TaskService
# from src.services.crawler_service import CrawlerService
# from src.services.data_service import DataService


@pytest.fixture(scope="session")
def test_config() -> TestingConfig:
    """
    测试配置夹具
    
    Returns:
        TestingConfig: 测试配置实例
    """
    return TestingConfig()


@pytest.fixture(scope="session")
def test_database_manager() -> Generator[DatabaseManager, None, None]:
    """
    测试数据库管理器夹具
    
    Yields:
        DatabaseManager: 初始化的数据库管理器实例
    """
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    database_url = f"sqlite:///{db_path}"
    
    # 初始化测试数据库
    manager = DatabaseManager()
    manager.init_database(database_url, echo=False)
    
    yield manager
    
    # 清理资源
    manager.close()
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def test_session(test_database_manager: DatabaseManager) -> Generator[Session, None, None]:
    """
    测试数据库会话夹具
    
    Args:
        test_database_manager: 测试数据库管理器
        
    Yields:
        Session: 数据库会话对象
    """
    with test_database_manager.get_session() as session:
        yield session


@pytest.fixture(scope="function")
def test_engine(test_database_manager: DatabaseManager) -> Engine:
    """
    测试数据库引擎夹具
    
    Args:
        test_database_manager: 测试数据库管理器
        
    Returns:
        Engine: 数据库引擎对象
    """
    return test_database_manager.engine


@pytest.fixture(scope="function", autouse=True)
def setup_test_database(test_engine: Engine) -> Generator[None, None, None]:
    """
    测试数据库设置夹具，自动为每个测试创建和清理数据库表
    
    Args:
        test_engine: 测试数据库引擎
    """
    # 创建所有表
    db.metadata.create_all(bind=test_engine)
    
    yield
    
    # 清理所有表
    db.metadata.drop_all(bind=test_engine)


@pytest.fixture
def sample_task_data() -> Dict[str, Any]:
    """
    样本任务数据夹具
    
    Returns:
        Dict[str, Any]: 样本任务数据
    """
    return {
        "name": "测试任务",
        "description": "这是一个测试任务",
        "task_type": "address_crawl",
        "priority": "medium",
        "status": "pending",
        "total_num": 10,
        "visited_num": 0,
        "retry_count": 0,
        "url": "https://example.com/addresses",
        "parameters": {"city": "北京", "district": "朝阳区"},
        "max_retry_count": 3,
        "timeout": 30,
        "scheduled_time": datetime.now(),
    }


@pytest.fixture
def sample_address_data() -> Dict[str, Any]:
    """
    样本地址数据夹具
    
    Returns:
        Dict[str, Any]: 样本地址数据
    """
    return {
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


# TODO: 添加爬虫结果数据夹具（需要先创建CrawlResult模型）
# @pytest.fixture
# def sample_crawl_result_data() -> Dict[str, Any]:
#     """
#     样本爬虫结果数据夹具
#     
#     Returns:
#         Dict[str, Any]: 样本爬虫结果数据
#     """
#     return {
#         "task_id": 1,
#         "url": "https://example.com/addresses",
#         "status_code": 200,
#         "response_data": '{"addresses": [{"province": "北京市", "city": "北京市"}]}',
#         "error_message": None,
#         "crawl_time": datetime.now(),
#         "response_time": 1.5,
#         "data_count": 1,
#     }


@pytest.fixture
def create_test_task(test_session: Session, sample_task_data: Dict[str, Any]) -> Task:
    """
    创建测试任务夹具
    
    Args:
        test_session: 测试数据库会话
        sample_task_data: 样本任务数据
        
    Returns:
        Task: 创建的测试任务实例
    """
    task = Task(**sample_task_data)
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    return task


@pytest.fixture
def create_test_address(test_session: Session, sample_address_data: Dict[str, Any]) -> Address:
    """
    创建测试地址夹具
    
    Args:
        test_session: 测试数据库会话
        sample_address_data: 样本地址数据
        
    Returns:
        Address: 创建的测试地址实例
    """
    address = Address(**sample_address_data)
    test_session.add(address)
    test_session.commit()
    test_session.refresh(address)
    return address


# TODO: 创建测试爬虫结果夹具（需要先创建CrawlResult模型）
# @pytest.fixture
# def create_test_crawl_result(test_session: Session, sample_crawl_result_data: Dict[str, Any]) -> CrawlResult:
#     """
#     创建测试爬虫结果夹具
#     
#     Args:
#         test_session: 测试数据库会话
#         sample_crawl_result_data: 样本爬虫结果数据
#         
#     Returns:
#         CrawlResult: 创建的测试爬虫结果实例
#     """
#     crawl_result = CrawlResult(**sample_crawl_result_data)
#     test_session.add(crawl_result)
#     test_session.commit()
#     test_session.refresh(crawl_result)
#     return crawl_result


# TODO: 服务夹具（需要先创建这些服务）
# @pytest.fixture
# def task_scheduler() -> TaskScheduler:
#     """
#     任务调度器夹具
#     
#     Returns:
#         TaskScheduler: 任务调度器实例
#     """
#     return TaskScheduler()


# @pytest.fixture
# def task_service(test_session: Session) -> TaskService:
#     """
#     任务服务夹具
#     
#     Args:
#         test_session: 测试数据库会话
#         
#     Returns:
#         TaskService: 任务服务实例
#     """
#     return TaskService(test_session)


# @pytest.fixture
# def crawler_service() -> CrawlerService:
#     """
#     爬虫服务夹具
#     
#     Returns:
#         CrawlerService: 爬虫服务实例
#     """
#     return CrawlerService()


# @pytest.fixture
# def data_service(test_session: Session) -> DataService:
#     """
#     数据服务夹具
#     
#     Args:
#         test_session: 测试数据库会话
#         
#     Returns:
#         DataService: 数据服务实例
#     """
#     return DataService(test_session)


@pytest.fixture
def mock_response_data() -> Dict[str, Any]:
    """
    模拟响应数据夹具
    
    Returns:
        Dict[str, Any]: 模拟的API响应数据
    """
    return {
        "status": "success",
        "data": {
            "addresses": [
                {
                    "province": "北京市",
                    "city": "北京市", 
                    "district": "朝阳区",
                    "street": "建国路",
                    "detail_address": "建国路88号",
                    "longitude": 116.4619,
                    "latitude": 39.9075,
                    "phone": "010-12345678",
                    "category": "商业大厦"
                },
                {
                    "province": "北京市",
                    "city": "北京市",
                    "district": "海淀区", 
                    "street": "中关村大街",
                    "detail_address": "中关村大街1号",
                    "longitude": 116.3162,
                    "latitude": 39.9848,
                    "phone": "010-87654321",
                    "category": "科技园区"
                }
            ]
        },
        "total": 2,
        "page": 1,
        "page_size": 10
    }


@pytest.fixture
def mock_error_response() -> Dict[str, Any]:
    """
    模拟错误响应数据夹具
    
    Returns:
        Dict[str, Any]: 模拟的错误响应数据
    """
    return {
        "status": "error",
        "message": "服务暂时不可用",
        "error_code": "SERVICE_UNAVAILABLE",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def test_file_path() -> str:
    """
    测试文件路径夹具
    
    Returns:
        str: 临时测试文件路径
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("测试数据\n")
        return f.name


@pytest.fixture
def cleanup_test_files() -> Generator[None, None, None]:
    """
    测试文件清理夹具
    
    自动清理测试中创建的文件
    """
    created_files = []
    
    def add_file(file_path: str) -> None:
        """添加需要清理的文件路径"""
        created_files.append(file_path)
    
    yield add_file
    
    # 清理所有文件
    for file_path in created_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass  # 忽略清理错误


@pytest.fixture(scope="session")
def celery_config() -> Dict[str, Any]:
    """
    Celery测试配置夹具
    
    Returns:
        Dict[str, Any]: Celery测试配置
    """
    return {
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
        "task_always_eager": True,  # 同步执行任务
        "task_eager_propagates": True,  # 传播异常
        "task_store_eager_result": True,  # 存储结果
    }


@pytest.fixture
def time_travel() -> Generator[datetime, None, None]:
    """
    时间旅行夹具，用于测试时间相关功能
    
    Yields:
        datetime: 当前时间
    """
    current_time = datetime.now()
    
    def travel(days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
        """时间旅行函数"""
        nonlocal current_time
        delta = timedelta(days=days, hours=hours, minutes=minutes)
        current_time = current_time + delta
        return current_time
    
    yield travel