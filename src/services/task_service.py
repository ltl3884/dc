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
        
        按照创建时间升序获取未完成的任务（visited_num < total_num）。
        
        Returns:
            Optional[Task]: 获取到的任务实例，如果没有待处理任务则返回None
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug("开始获取待处理任务")
            # 查找未完成任务，按创建时间排序
            task = Task.query.filter(
                Task.visited_num < Task.total_num,
                Task.total_num > 0
            ).order_by(Task.created_at.asc()).first()
            
            # 如果没有找到任务，尝试查找 total_num=0 的任务（视为未完成）
            if not task:
                task = Task.query.filter(
                    Task.total_num == 0
                ).order_by(Task.created_at.asc()).first()
            
            if task:
                self.logger.debug(f"找到待处理任务: ID={task.id}, URL={task.url}")
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
    
    def update_task_progress(
        self,
        task_id: int,
        visited_num: Optional[int] = None,
        increment_visited: int = 0,
        increment_retry: bool = False,
        reset_retry_count: bool = False
    ) -> Task:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            visited_num: 已访问数量，如果提供则直接设置该值
            increment_visited: 增加已访问数量，默认为0
            increment_retry: 是否增加重试次数，默认为False
            reset_retry_count: 是否重置重试次数为0，默认为False
            
        Returns:
            Task: 更新后的任务实例
            
        Raises:
            ValueError: 当参数无效时
            SQLAlchemyError: 当数据库操作失败时
        """
        self.logger.debug(f"开始更新任务进度: ID={task_id}")
        try:
            # 参数验证
            if not task_id or task_id <= 0:
                self.logger.error(f"更新任务进度失败: 无效的任务ID - {task_id}")
                raise ValueError("任务ID必须为正整数")
            
            # 查找任务
            self.logger.debug(f"查找任务: ID={task_id}")
            task = Task.query.get(task_id)
            if not task:
                self.logger.error(f"更新任务进度失败: 任务不存在 - ID={task_id}")
                raise ValueError(f"任务不存在: ID={task_id}")
            
            self.logger.debug(f"找到任务: ID={task_id}, 当前进度={task.visited_num}/{task.total_num}")
            
            # 更新已访问数量
            if visited_num is not None:
                if visited_num < 0:
                    self.logger.error(f"更新任务进度失败: 已访问数量为负数 - {visited_num}")
                    raise ValueError("已访问数量不能为负数")
                self.logger.debug(f"更新已访问数量: {task.visited_num} -> {visited_num}")
                task.visited_num = visited_num
            elif increment_visited > 0:
                old_visited = task.visited_num
                task.visited_num += increment_visited
                self.logger.debug(f"增加已访问数量: {old_visited} -> {task.visited_num} (+{increment_visited})")
            
            # 更新重试次数
            if reset_retry_count:
                old_retry = task.retry_count
                task.retry_count = 0
                self.logger.debug(f"重置重试次数: {old_retry} -> 0")
            elif increment_retry:
                old_retry = task.retry_count
                task.increment_retry()
                self.logger.debug(f"增加重试次数: {old_retry} -> {task.retry_count}")
            
            # 更新时间戳
            task.updated_at = datetime.utcnow()
            
            # 提交更改
            db.session.commit()
            
            self.logger.info(
                f"任务进度更新: ID={task.id}, "
                f"进度={task.visited_num}/{task.total_num}, "
                f"完成率={task.completion_rate:.2%}, "
                f"重试={task.retry_count}"
            )
            
            return task
            
        except ValueError:
            # 参数验证错误，直接抛出
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"更新任务进度失败 - 数据库错误: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"数据库操作失败: {str(e)}")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"更新任务进度失败 - 未知错误: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"更新任务进度时发生未知错误: {str(e)}")
    
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
                self.logger.info(f"成功获取任务: ID={task_id}, URL={task.url}, 完成率={task.completion_rate:.2%}")
            else:
                self.logger.info(f"任务不存在: ID={task_id}")
            return task
        except SQLAlchemyError as e:
            self.logger.error(f"获取任务失败: ID={task_id}, 错误={str(e)}")
            raise SQLAlchemyError(f"获取任务失败: {str(e)}")
    
    def get_incomplete_tasks(self) -> List[Task]:
        """
        获取所有未完成的任务
        
        Returns:
            List[Task]: 未完成的任务列表
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug("开始获取未完成任务列表")
            tasks = Task.query.filter(
                db.or_(
                    db.and_(Task.visited_num < Task.total_num, Task.total_num > 0),
                    Task.total_num == 0
                )
            ).all()
            self.logger.info(f"成功获取未完成任务列表: 数量={len(tasks)}")
            return tasks
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取未完成任务列表失败: 错误={str(e)}")
            raise SQLAlchemyError(f"获取未完成任务列表失败: {str(e)}")
    
    def get_completed_tasks(self) -> List[Task]:
        """
        获取所有已完成的任务
        
        Returns:
            List[Task]: 已完成的任务列表
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        try:
            self.logger.debug("开始获取已完成任务列表")
            tasks = Task.query.filter(
                Task.visited_num >= Task.total_num,
                Task.total_num > 0
            ).all()
            self.logger.info(f"成功获取已完成任务列表: 数量={len(tasks)}")
            return tasks
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取已完成任务列表失败: 错误={str(e)}")
            raise SQLAlchemyError(f"获取已完成任务列表失败: {str(e)}")
    
    def get_pending_tasks(self) -> List[Task]:
        """
        获取所有待处理的任务（别名，保持向后兼容）
        
        Returns:
            List[Task]: 未完成的任务列表
            
        Raises:
            SQLAlchemyError: 当数据库操作失败时
        """
        return self.get_incomplete_tasks()
    
    def complete_task(self, task_id: int, visited_num: Optional[int] = None) -> Task:
        """
        完成任务（设置访问数量等于总数量）
        
        Args:
            task_id: 任务ID
            visited_num: 已访问数量，如果提供则设置为该值，否则设置为总数量
            
        Returns:
            Task: 更新后的任务实例
        """
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务不存在: ID={task_id}")
            
            # 如果没有提供visited_num，则设置为总数量
            if visited_num is None:
                visited_num = task.total_num
            
            return self.update_task_progress(
                task_id=task_id,
                visited_num=visited_num
            )
        except Exception as e:
            self.logger.error(f"完成任务失败: ID={task_id}, 错误={str(e)}")
            raise
    
    def fail_task(self, task_id: int, increment_retry: bool = True) -> Task:
        """
        标记任务失败（增加重试次数）
        
        Args:
            task_id: 任务ID
            increment_retry: 是否增加重试次数，默认为True
            
        Returns:
            Task: 更新后的任务实例
        """
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务不存在: ID={task_id}")
            
            return self.update_task_progress(
                task_id=task_id,
                increment_retry=increment_retry
            )
        except Exception as e:
            self.logger.error(f"标记任务失败失败: ID={task_id}, 错误={str(e)}")
            raise
    
    def reset_task(self, task_id: int) -> Task:
        """
        重置任务进度（将访问数量重置为0）
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 更新后的任务实例
        """
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务不存在: ID={task_id}")
            
            return self.update_task_progress(
                task_id=task_id,
                visited_num=0,
                increment_retry=False,  # 不增加重试次数
                reset_retry_count=True  # 重置重试次数为0
            )
        except Exception as e:
            self.logger.error(f"重置任务失败: ID={task_id}, 错误={str(e)}")
            raise