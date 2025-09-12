"""
任务模型模块

该模块定义了Task模型类，用于存储和管理爬虫任务的数据结构，
包括URL、请求方法、请求体、头部信息、任务状态等核心字段。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from src.app import db


class Task(db.Model):
    """
    任务模型类
    
    用于定义爬虫任务的数据结构，包含任务执行所需的所有信息
    和任务执行状态的跟踪字段。
    """
    
    __tablename__ = 'tasks'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 任务核心字段
    url = Column(String(2048), nullable=False, index=True, comment='目标URL')
    method = Column(String(10), nullable=False, default='GET', comment='HTTP请求方法')
    body = Column(Text, nullable=True, comment='请求体内容')
    headers = Column(JSON, nullable=True, default=dict, comment='HTTP请求头')
    
    # 任务统计字段
    total_num = Column(Integer, nullable=False, default=0, comment='预期爬取数量')
    visited_num = Column(Integer, nullable=False, default=0, comment='已访问数量')
    
    # 任务状态字段
    status = Column(
        String(20), 
        nullable=False, 
        default='pending',
        server_default='pending',
        index=True,
        comment='任务状态: pending, running, completed, failed'
    )
    
    # 任务配置字段
    timeout = Column(Integer, nullable=False, default=30, comment='请求超时时间(秒)')
    retry_count = Column(Integer, nullable=False, default=0, comment='重试次数')
    
    # 时间戳字段
    created_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        comment='更新时间'
    )
    
    def __init__(
        self,
        url: str,
        method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        total_num: int = 0,
        timeout: int = 30,
        **kwargs
    ) -> None:
        """
        初始化任务实例
        
        Args:
            url: 目标URL
            method: HTTP请求方法，默认为GET
            body: 请求体内容，可选
            headers: HTTP请求头字典，可选
            total_num: 预期爬取数量，默认为0
            timeout: 请求超时时间(秒)，默认为30
            **kwargs: 其他可选参数
        """
        self.url = url
        self.method = method.upper()
        self.body = body
        self.headers = headers or {}
        self.total_num = total_num
        self.timeout = timeout
        
        # 设置其他字段
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        return f"<Task(id={self.id}, url='{self.url}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将任务对象转换为字典
        
        Returns:
            Dict[str, Any]: 任务数据的字典表示
        """
        return {
            'id': self.id,
            'url': self.url,
            'method': self.method,
            'body': self.body,
            'headers': self.headers,
            'total_num': self.total_num,
            'visited_num': self.visited_num,
            'status': self.status,
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def increment_visited(self, count: int = 1) -> None:
        """
        增加已访问数量
        
        Args:
            count: 增加的数量，默认为1
        """
        self.visited_num += count
    
    def increment_retry(self) -> None:
        """增加重试次数"""
        self.retry_count += 1
    
    def update_status(self, status: str) -> None:
        """
        更新任务状态
        
        Args:
            status: 新的状态值
        """
        self.status = status
    
    @property
    def completion_rate(self) -> float:
        """
        计算任务完成率
        
        Returns:
            float: 完成率(0-1之间的小数)
        """
        if self.total_num <= 0:
            return 0.0
        return min(self.visited_num / self.total_num, 1.0)
    
    @property
    def is_completed(self) -> bool:
        """
        检查任务是否已完成
        
        Returns:
            bool: 如果状态为completed则返回True
        """
        return self.status == 'completed'
    
    @property
    def is_failed(self) -> bool:
        """
        检查任务是否已失败
        
        Returns:
            bool: 如果状态为failed则返回True
        """
        return self.status == 'failed'
    
    @property
    def is_running(self) -> bool:
        """
        检查任务是否正在运行
        
        Returns:
            bool: 如果状态为running则返回True
        """
        return self.status == 'running'
    
    @property
    def is_pending(self) -> bool:
        """
        检查任务是否待处理
        
        Returns:
            bool: 如果状态为pending则返回True
        """
        return self.status == 'pending'