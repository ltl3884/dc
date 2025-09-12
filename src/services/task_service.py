"""
任务服务模块

该模块提供任务生命周期管理功能，包括任务的创建、查询、状态更新等操作，
为爬虫系统提供完整的任务管理支持。
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError

from src.app import db
from src.models.task import Task


class TaskService:
    """
    任务服务类
    
    提供任务生命周期管理功能，包括创建任务、获取待处理任务、
    更新任务状态等核心功能。
    """
    
    def __init__(self) -> None:
        """初始化任务服务"""
        self.logger = logging.getLogger(__name__)
    
    def create_task(
        self,
        url: str,
        method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        total_num: int = 0,
        timeout: int = 30,
        **kwargs
    ) -> Task:
        """
        创建新任务
        
        Args:
            url: 目标URL (必需)
            method: HTTP请求方法，默认为GET
            body: 请求体内容，可选
            headers: HTTP请求头字典，可选
            total_num: 预期爬取数量，默认为0
            timeout: 请求超时时间(秒)，默认为30
            **kwargs: 其他可选参数
            
        Returns:
            Task: 创建的任务实例
            
        Raises:
            ValueError: 当参数验证失败时
            SQLAlchemyError: 当数据库操作失败时
        """
        self.logger.debug(f"开始创建任务: URL={url}, method={method}")
        try:
            # 参数验证
            if not url or not url.strip():
                self.logger.error(f"任务创建失败: URL不能为空")
                raise ValueError("URL不能为空")
            
            if not url.startswith(('http://', 'https://')):
                self.logger.error(f"任务创建失败: URL格式错误 - {url}")
                raise ValueError("URL必须以http://或https://开头")
            
            if len(url) > 2048:
                self.logger.error(f"任务创建失败: URL长度超限 - {len(url)}字符")
                raise ValueError("URL长度不能超过2048字符")
            
            method = method.upper()
            if method not in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']:
                self.logger.error(f"任务创建失败: 不支持的HTTP方法 - {method}")
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            if timeout < 1 or timeout > 300:
                self.logger.error(f"任务创建失败: 超时时间无效 - {timeout}秒")
                raise ValueError("超时时间必须在1-300秒之间")
            
            if total_num < 0:
                self.logger.error(f"任务创建失败: 爬取数量为负数 - {total_num}")
                raise ValueError("爬取数量不能为负数")
            
            # 创建任务实例
            self.logger.debug(f"参数验证通过，创建任务实例: URL={url.strip()}, method={method}")
            task = Task(
                url=url.strip(),
                method=method,
                body=body,
                headers=headers or {},
                total_num=total_num,
                timeout=timeout,
                **kwargs
            )
            
            # 保存到数据库
            db.session.add(task)
            db.session.commit()
            
            self.logger.info(f"任务创建成功: ID={task.id}, URL={task.url}")
            return task
            
        except ValueError:
            # 参数验证错误，直接抛出
            raise
        except SQLAlchemyError as e:
            # 数据库操作错误
            db.session.rollback()
            self.logger.error(f"任务创建失败 - 数据库错误: {str(e)}")
            raise SQLAlchemyError(f"数据库操作失败: {str(e)}")
        except Exception as e:
            # 其他未预期的错误
            db.session.rollback()
            self.logger.error(f"任务创建失败 - 未知错误: {str(e)}")
            raise SQLAlchemyError(f"创建任务时发生未知错误: {str(e)}")
    
    def get_pending_task(self) -> Optional[Task]:
        """
        获取下一个待处理的任务
        
        按照创建时间升序获取状态为pending的任务，
        并将其状态更新为running。
        
        Returns:
            Optional[Task]: 获取到的任务实例，如果没有待处理任务则返回None
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug("开始获取待处理任务")
            # 查找待处理任务，按创建时间排序
            task = Task.query.filter_by(status='pending')\
                           .order_by(Task.created_at.asc())\
                           .first()
            
            if task:
                self.logger.debug(f"找到待处理任务: ID={task.id}, URL={task.url}")
                # 更新任务状态为运行中
                task.status = 'running'
                task.updated_at = datetime.utcnow()
                db.session.commit()
                
                self.logger.info(f"获取待处理任务: ID={task.id}, URL={task.url}")
            else:
                self.logger.debug("没有待处理的任务")
            
            return task
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"获取待处理任务失败: {str(e)}")
            raise SQLAlchemyError(f"获取待处理任务失败: {str(e)}")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"获取待处理任务失败 - 未知错误: {str(e)}")
            raise SQLAlchemyError(f"获取待处理任务时发生未知错误: {str(e)}")
    
    def update_task_status(
        self,
        task_id: int,
        status: str,
        visited_num: Optional[int] = None,
        increment_visited: int = 0,
        increment_retry: bool = False
    ) -> Task:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态 (pending, running, completed, failed)
            visited_num: 已访问数量，如果提供则直接设置该值
            increment_visited: 增加已访问数量，默认为0
            increment_retry: 是否增加重试次数，默认为False
            
        Returns:
            Task: 更新后的任务实例
            
        Raises:
            ValueError: 当参数无效时
            SQLAlchemyError: 当数据库操作失败时
        """
        self.logger.debug(f"开始更新任务状态: ID={task_id}, 状态={status}")
        try:
            # 参数验证
            if not task_id or task_id <= 0:
                self.logger.error(f"更新任务状态失败: 无效的任务ID - {task_id}")
                raise ValueError("任务ID必须为正整数")
            
            valid_statuses = ['pending', 'running', 'completed', 'failed']
            if status not in valid_statuses:
                self.logger.error(f"更新任务状态失败: 无效的状态 - {status}")
                raise ValueError(f"无效的状态: {status}，有效状态为: {valid_statuses}")
            
            # 查找任务
            self.logger.debug(f"查找任务: ID={task_id}")
            task = Task.query.get(task_id)
            if not task:
                self.logger.error(f"更新任务状态失败: 任务不存在 - ID={task_id}")
                raise ValueError(f"任务不存在: ID={task_id}")
            
            self.logger.debug(f"找到任务: ID={task_id}, 原状态={task.status}, 新状态={status}")
            
            # 更新状态
            task.status = status
            task.updated_at = datetime.utcnow()
            
            # 更新已访问数量
            if visited_num is not None:
                if visited_num < 0:
                    self.logger.error(f"更新任务状态失败: 已访问数量为负数 - {visited_num}")
                    raise ValueError("已访问数量不能为负数")
                self.logger.debug(f"更新已访问数量: {task.visited_num} -> {visited_num}")
                task.visited_num = visited_num
            elif increment_visited > 0:
                old_visited = task.visited_num
                task.visited_num += increment_visited
                self.logger.debug(f"增加已访问数量: {old_visited} -> {task.visited_num} (+{increment_visited})")
            
            # 更新重试次数
            if increment_retry:
                old_retry = task.retry_count
                task.increment_retry()
                self.logger.debug(f"增加重试次数: {old_retry} -> {task.retry_count}")
            
            # 提交更改
            db.session.commit()
            
            self.logger.info(
                f"任务状态更新: ID={task.id}, 状态={status}, "
                f"已访问={task.visited_num}, 重试={task.retry_count}"
            )
            
            return task
            
        except ValueError:
            # 参数验证错误，直接抛出
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"更新任务状态失败 - 数据库错误: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"数据库操作失败: {str(e)}")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新任务状态失败 - 未知错误: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"更新任务状态时发生未知错误: {str(e)}")
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        根据ID获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务实例，如果不存在则返回None
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug(f"开始获取任务: ID={task_id}")
            task = Task.query.get(task_id)
            if task:
                self.logger.info(f"成功获取任务: ID={task_id}, URL={task.url}, 状态={task.status}")
            else:
                self.logger.info(f"任务不存在: ID={task_id}")
            return task
        except SQLAlchemyError as e:
            self.logger.error(f"获取任务失败: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"获取任务失败: {str(e)}")
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        """
        根据状态获取任务列表
        
        Args:
            status: 任务状态
            
        Returns:
            List[Task]: 任务列表
            
        Raises:
            ValueError: 当状态无效时
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug(f"开始获取任务列表: 状态={status}")
            valid_statuses = ['pending', 'running', 'completed', 'failed']
            if status not in valid_statuses:
                raise ValueError(f"无效的状态: {status}，有效状态为: {valid_statuses}")
            
            tasks = Task.query.filter_by(status=status).all()
            self.logger.info(f"成功获取任务列表: 状态={status}, 数量={len(tasks)}")
            return tasks
            
        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"获取任务列表失败: 状态={status}, 错误={str(e)}")
            raise SQLAlchemyError(f"获取任务列表失败: {str(e)}")
    
    def get_running_tasks(self) -> List[Task]:
        """
        获取所有运行中的任务
        
        Returns:
            List[Task]: 运行中的任务列表
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        return self.get_tasks_by_status('running')
    
    def get_pending_tasks(self) -> List[Task]:
        """
        获取所有待处理的任务
        
        Returns:
            List[Task]: 待处理的任务列表
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        return self.get_tasks_by_status('pending')
    
    def complete_task(self, task_id: int, visited_num: Optional[int] = None) -> Task:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            visited_num: 已访问数量，可选
            
        Returns:
            Task: 更新后的任务实例
        """
        return self.update_task_status(
            task_id=task_id,
            status='completed',
            visited_num=visited_num
        )
    
    def fail_task(self, task_id: int, increment_retry: bool = True) -> Task:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            increment_retry: 是否增加重试次数，默认为True
            
        Returns:
            Task: 更新后的任务实例
        """
        return self.update_task_status(
            task_id=task_id,
            status='failed',
            increment_retry=increment_retry
        )
    
    def reset_task(self, task_id: int) -> Task:
        """
        重置任务状态为待处理
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 更新后的任务实例
        """
        return self.update_task_status(
            task_id=task_id,
            status='pending'
        )