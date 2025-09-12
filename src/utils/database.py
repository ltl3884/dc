"""
数据库连接工具模块

该模块提供集中的数据库连接管理功能，包括数据库初始化、连接参数配置和错误处理。
支持多种数据库类型，并提供优雅的连接错误处理机制。
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_database_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器，负责数据库连接和会话管理"""
    
    def __init__(self) -> None:
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
    
    def init_database(self, database_url: Optional[str] = None, echo: bool = False) -> None:
        """
        初始化数据库连接
        
        Args:
            database_url: 数据库连接URL，如果为None则使用配置文件中的URL
            echo: 是否输出SQL语句，默认为False
            
        Raises:
            SQLAlchemyError: 当数据库连接失败时
        """
        try:
            # 获取数据库配置
            if database_url is None:
                db_config = get_database_config()
                database_url = db_config["url"]
                echo = echo or db_config["echo"]
            
            # 创建数据库引擎
            self._engine = create_engine(
                database_url,
                echo=echo,
                pool_pre_ping=True,  # 连接池预检查
                pool_recycle=3600,   # 连接回收时间
            )
            
            # 配置SQLite外键支持
            if database_url.startswith("sqlite"):
                event.listen(self._engine, "connect", self._set_sqlite_pragma)
            
            # 创建会话工厂
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            logger.info("数据库连接初始化成功")
            
        except SQLAlchemyError as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
        except Exception as e:
            logger.error(f"数据库初始化过程中发生未知错误: {e}")
            raise SQLAlchemyError(f"数据库初始化失败: {e}")
    
    @staticmethod
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
        """设置SQLite外键约束支持"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        if self._engine is None:
            raise RuntimeError("数据库未初始化，请先调用 init_database() 方法")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if self._session_factory is None:
            raise RuntimeError("数据库未初始化，请先调用 init_database() 方法")
        return self._session_factory
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话的上下文管理器
        
        Yields:
            Session: SQLAlchemy会话对象
            
        Raises:
            SQLAlchemyError: 当会话创建失败时
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话中发生未知错误: {e}")
            raise SQLAlchemyError(f"数据库会话错误: {e}")
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        测试数据库连接是否正常
        
        Returns:
            bool: 连接是否成功
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
        except Exception as e:
            logger.error(f"数据库连接测试过程中发生未知错误: {e}")
            return False
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("数据库连接已关闭")


# 全局数据库管理器实例
_db_manager = DatabaseManager()


def init_database(database_url: Optional[str] = None, echo: bool = False) -> None:
    """
    初始化全局数据库连接
    
    Args:
        database_url: 数据库连接URL，如果为None则使用配置文件中的URL
        echo: 是否输出SQL语句，默认为False
        
    Raises:
        SQLAlchemyError: 当数据库连接失败时
    """
    _db_manager.init_database(database_url, echo)


def get_session() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    Yields:
        Session: SQLAlchemy会话对象
        
    Raises:
        RuntimeError: 当数据库未初始化时
        SQLAlchemyError: 当会话创建失败时
    """
    return _db_manager.get_session()


def test_connection() -> bool:
    """
    测试数据库连接是否正常
    
    Returns:
        bool: 连接是否成功
    """
    return _db_manager.test_connection()


def close_database() -> None:
    """关闭数据库连接"""
    _db_manager.close()


def get_engine() -> Engine:
    """
    获取数据库引擎
    
    Returns:
        Engine: SQLAlchemy引擎对象
        
    Raises:
        RuntimeError: 当数据库未初始化时
    """
    return _db_manager.engine


# 为了向后兼容，提供别名
database_manager = _db_manager