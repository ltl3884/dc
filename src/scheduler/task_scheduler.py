"""
任务调度器模块

该模块提供集中的任务调度功能，基于APScheduler库实现：
- 使用BackgroundScheduler进行后台任务调度
- 支持定时任务、间隔任务和Cron表达式
- 提供任务管理功能（添加、删除、暂停、恢复）
- 集成配置管理和日志功能

作者: Claude Code
创建时间: 2025-09-10
"""

import logging
import time
from typing import Optional, Dict, Any, Callable, Union
from datetime import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.job import Job
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from src.config import get_scheduler_config
from src.utils.logger import get_logger
from src.utils.database import get_session
from src.models.task import Task
from src.services.crawler_service import CrawlerService


class TaskStatistics:
    """任务统计类
    
    用于跟踪和记录任务执行的统计信息，包括成功、失败、跳过等状态的数量和时间戳。
    
    Attributes:
        success_count: 成功执行的任务数量
        failure_count: 执行失败的任务数量
        skipped_count: 被跳过的任务数量
        total_executions: 总执行次数
        last_execution_time: 最后执行时间
        last_success_time: 最后成功时间
        last_failure_time: 最后失败时间
        execution_history: 最近执行历史记录
    """
    
    def __init__(self) -> None:
        """初始化任务统计实例"""
        self.success_count: int = 0
        self.failure_count: int = 0
        self.skipped_count: int = 0
        self.total_executions: int = 0
        self.last_execution_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.last_failure_time: Optional[datetime] = None
        self.execution_history: list[Dict[str, Any]] = []
        self._max_history_size: int = 1000  # 最多保留1000条历史记录
    
    def record_success(self, job_id: str, job_name: Optional[str] = None) -> None:
        """记录成功的任务执行
        
        Args:
            job_id: 作业ID
            job_name: 作业名称
        """
        current_time = datetime.now()
        self.success_count += 1
        self.total_executions += 1
        self.last_execution_time = current_time
        self.last_success_time = current_time
        
        self._add_to_history(job_id, job_name, 'success', current_time)
    
    def record_failure(self, job_id: str, job_name: Optional[str] = None, error: Optional[str] = None) -> None:
        """记录失败的任务执行
        
        Args:
            job_id: 作业ID
            job_name: 作业名称
            error: 错误信息
        """
        current_time = datetime.now()
        self.failure_count += 1
        self.total_executions += 1
        self.last_execution_time = current_time
        self.last_failure_time = current_time
        
        self._add_to_history(job_id, job_name, 'failure', current_time, error)
    
    def record_skipped(self, job_id: str, job_name: Optional[str] = None, reason: Optional[str] = None) -> None:
        """记录被跳过的任务执行
        
        Args:
            job_id: 作业ID
            job_name: 作业名称
            reason: 跳过原因
        """
        current_time = datetime.now()
        self.skipped_count += 1
        self.total_executions += 1
        self.last_execution_time = current_time
        
        self._add_to_history(job_id, job_name, 'skipped', current_time, reason)
    
    def _add_to_history(self, job_id: str, job_name: Optional[str], status: str, 
                       timestamp: datetime, details: Optional[str] = None) -> None:
        """添加记录到历史记录
        
        Args:
            job_id: 作业ID
            job_name: 作业名称
            status: 执行状态
            timestamp: 时间戳
            details: 详细信息
        """
        history_entry = {
            'job_id': job_id,
            'job_name': job_name,
            'status': status,
            'timestamp': timestamp.isoformat(),
            'details': details
        }
        
        self.execution_history.append(history_entry)
        
        # 限制历史记录大小
        if len(self.execution_history) > self._max_history_size:
            self.execution_history.pop(0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 包含所有统计信息的字典
        """
        return {
            'success_count': self.success_count,
            'failure_count': self.failure_count,
            'skipped_count': self.skipped_count,
            'total_executions': self.total_executions,
            'success_rate': self._calculate_success_rate(),
            'failure_rate': self._calculate_failure_rate(),
            'skipped_rate': self._calculate_skipped_rate(),
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'last_success_time': self.last_success_time.isoformat() if self.last_success_time else None,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要
        
        Returns:
            Dict[str, Any]: 执行摘要信息
        """
        recent_history = self.execution_history[-10:] if self.execution_history else []
        
        return {
            'total_executions': self.total_executions,
            'success_rate': self._calculate_success_rate(),
            'failure_rate': self._calculate_failure_rate(),
            'recent_executions': recent_history,
            'statistics': self.get_statistics()
        }
    
    def reset(self) -> None:
        """重置所有统计数据"""
        self.success_count = 0
        self.failure_count = 0
        self.skipped_count = 0
        self.total_executions = 0
        self.last_execution_time = None
        self.last_success_time = None
        self.last_failure_time = None
        self.execution_history.clear()
    
    def _calculate_success_rate(self) -> float:
        """计算成功率
        
        Returns:
            float: 成功率(0-1之间的小数)
        """
        if self.total_executions == 0:
            return 0.0
        return self.success_count / self.total_executions
    
    def _calculate_failure_rate(self) -> float:
        """计算失败率
        
        Returns:
            float: 失败率(0-1之间的小数)
        """
        if self.total_executions == 0:
            return 0.0
        return self.failure_count / self.total_executions
    
    def _calculate_skipped_rate(self) -> float:
        """计算跳过率
        
        Returns:
            float: 跳过率(0-1之间的小数)
        """
        if self.total_executions == 0:
            return 0.0
        return self.skipped_count / self.total_executions


class PerformanceMetrics:
    """性能指标记录器
    
    用于记录和跟踪调度器的性能指标，包括执行时间、内存使用等。
    
    Attributes:
        start_time: 记录开始时间
        job_metrics: 作业级别的性能指标
        system_metrics: 系统级别的性能指标
    """
    
    def __init__(self) -> None:
        """初始化性能指标记录器"""
        self.start_time: datetime = datetime.now()
        self.job_metrics: Dict[str, Dict[str, Any]] = {}
        self.system_metrics: Dict[str, Any] = {
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'max_execution_time': 0.0,
            'min_execution_time': float('inf'),
            'execution_count': 0
        }
    
    def record_job_start(self, job_id: str) -> None:
        """记录作业开始执行
        
        Args:
            job_id: 作业ID
        """
        if job_id not in self.job_metrics:
            self.job_metrics[job_id] = {
                'start_time': None,
                'execution_count': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf'),
                'last_execution_time': None
            }
        
        self.job_metrics[job_id]['start_time'] = time.time()
    
    def record_job_end(self, job_id: str, success: bool = True, error: Optional[str] = None) -> None:
        """记录作业结束执行
        
        Args:
            job_id: 作业ID
            success: 是否执行成功
            error: 错误信息（如果失败）
        """
        if job_id not in self.job_metrics:
            return
        
        start_time = self.job_metrics[job_id]['start_time']
        if start_time is None:
            return
        
        # 计算执行时间（毫秒）
        execution_time = (time.time() - start_time) * 1000
        
        # 更新作业指标
        metrics = self.job_metrics[job_id]
        metrics['execution_count'] += 1
        metrics['total_time'] += execution_time
        metrics['average_time'] = metrics['total_time'] / metrics['execution_count']
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['last_execution_time'] = execution_time
        
        # 更新系统指标
        self.system_metrics['total_execution_time'] += execution_time
        self.system_metrics['execution_count'] += 1
        self.system_metrics['average_execution_time'] = (
            self.system_metrics['total_execution_time'] / self.system_metrics['execution_count']
        )
        self.system_metrics['max_execution_time'] = max(
            self.system_metrics['max_execution_time'], execution_time
        )
        self.system_metrics['min_execution_time'] = min(
            self.system_metrics['min_execution_time'], execution_time
        )
        
        # 重置开始时间
        metrics['start_time'] = None
    
    def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """获取指定作业的性能指标
        
        Args:
            job_id: 作业ID
            
        Returns:
            Dict[str, Any]: 作业性能指标
        """
        return self.job_metrics.get(job_id, {})
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标
        
        Returns:
            Dict[str, Any]: 系统性能指标
        """
        metrics = self.system_metrics.copy()
        
        # 计算运行时长
        uptime = (datetime.now() - self.start_time).total_seconds()
        metrics['uptime_seconds'] = uptime
        metrics['uptime_formatted'] = str(datetime.now() - self.start_time)
        
        # 如果min_time仍然是inf，设置为0
        if metrics['min_execution_time'] == float('inf'):
            metrics['min_execution_time'] = 0.0
        
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要
        
        Returns:
            Dict[str, Any]: 性能摘要信息
        """
        system_metrics = self.get_system_metrics()
        job_count = len(self.job_metrics)
        
        return {
            'system_metrics': system_metrics,
            'job_count': job_count,
            'active_jobs': list(self.job_metrics.keys()),
            'performance_indicators': {
                'efficiency': system_metrics['execution_count'] / max(system_metrics['uptime_seconds'], 1) * 3600,  # 每小时执行次数
                'average_response_time': system_metrics['average_execution_time'],
                'throughput': system_metrics['execution_count']
            }
        }
    
    def reset_metrics(self) -> None:
        """重置所有性能指标"""
        self.start_time = datetime.now()
        self.job_metrics.clear()
        self.system_metrics = {
            'total_execution_time': 0.0,
            'average_execution_time': 0.0,
            'max_execution_time': 0.0,
            'min_execution_time': float('inf'),
            'execution_count': 0
        }


class TaskScheduler:
    """任务调度器类
    
    基于APScheduler的BackgroundScheduler实现，提供任务调度基础设施。
    支持定时任务、间隔任务和Cron表达式，提供完整的任务生命周期管理。
    
    Attributes:
        scheduler: APScheduler的BackgroundScheduler实例
        logger: 日志记录器
        is_running: 调度器运行状态
        performance_metrics: 性能指标记录器
        job_execution_times: 作业执行时间记录
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化任务调度器
        
        Args:
            config: 调度器配置字典，如果为None则使用默认配置
        """
        self.logger = get_logger(__name__)
        self._config = config or get_scheduler_config()
        self._scheduler: Optional[BackgroundScheduler] = None
        self._is_running = False
        self._statistics = TaskStatistics()
        self._start_time: Optional[datetime] = None
        self._performance_metrics = PerformanceMetrics()
        self._job_execution_times: Dict[str, float] = {}
        
        self.logger.info("开始初始化任务调度器")
        self._initialize_scheduler()
    
    def _initialize_scheduler(self) -> None:
        """初始化调度器
        
        创建BackgroundScheduler实例并配置基本设置。
        配置包括时区、作业默认设置和事件监听器。
        """
        try:
            # 记录配置信息
            self.logger.info(f"调度器配置: {self._config}")
            
            # 处理时区
            timezone_str = self._config.get("timezone", "Asia/Shanghai")
            timezone = pytz.timezone(timezone_str)
            self.logger.info(f"使用配置时区: {timezone_str}")
            
            # 处理作业默认设置
            job_defaults = self._config.get("job_defaults", {})
            if job_defaults:
                self.logger.info(f"作业默认设置: {job_defaults}")
            
            # 创建调度器配置
            scheduler_config = {
                "timezone": timezone,
            }
            
            # 只有在job_defaults不为空时才添加
            if job_defaults:
                scheduler_config["job_defaults"] = job_defaults
            
            self._scheduler = BackgroundScheduler(**scheduler_config)
            self.logger.info("BackgroundScheduler实例创建成功")
            
            # 添加事件监听器
            self.logger.info("正在添加事件监听器...")
            self._scheduler.add_listener(
                self._job_executed_listener, EVENT_JOB_EXECUTED
            )
            self._scheduler.add_listener(
                self._job_error_listener, EVENT_JOB_ERROR
            )
            self._scheduler.add_listener(
                self._job_missed_listener, EVENT_JOB_MISSED
            )
            self.logger.info("事件监听器添加完成")
            
            self.logger.info("任务调度器初始化成功")
            
        except Exception as e:
            self.logger.error(f"初始化调度器失败: {e}")
            raise RuntimeError(f"无法初始化任务调度器: {e}")
    
    def start(self) -> bool:
        """启动调度器
        
        Returns:
            bool: 启动是否成功
            
        Raises:
            RuntimeError: 当调度器已经运行时
        """
        if self._is_running:
            raise RuntimeError("调度器已经在运行中")
        
        if not self._scheduler:
            raise RuntimeError("调度器未初始化")
        
        try:
            self.logger.info("正在启动任务调度器...")
            self._start_time = datetime.now()
            
            self._scheduler.start()
            self._is_running = True
            
            # 记录启动成功信息
            self.logger.info(f"任务调度器启动成功 - 启动时间: {self._start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info(f"当前调度器状态: 运行中={self._is_running}, 作业数量={len(self.get_jobs())}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动调度器失败: {e}")
            self._is_running = False
            self._start_time = None
            return False
    
    def stop(self, wait: bool = True) -> bool:
        """停止调度器
        
        Args:
            wait: 是否等待正在运行的作业完成
            
        Returns:
            bool: 停止是否成功
        """
        if not self._is_running:
            self.logger.warning("调度器未运行，无需停止")
            return True
        
        try:
            self.logger.info("正在停止任务调度器...")
            
            # 记录停止前的统计信息
            stats = self.get_statistics()
            jobs_count = len(self.get_jobs())
            
            self.logger.info(f"调度器停止前状态 - 作业数量: {jobs_count}")
            self.logger.info(f"任务执行统计 - 总计: {stats['total_executions']}, "
                           f"成功: {stats['success_count']}, 失败: {stats['failure_count']}, "
                           f"跳过: {stats['skipped_count']}")
            
            # 记录运行时长
            if self._start_time:
                runtime = datetime.now() - self._start_time
                self.logger.info(f"调度器运行时长: {runtime}")
            
            self._scheduler.shutdown(wait=wait)
            self._is_running = False
            
            # 记录停止成功信息
            stop_time = datetime.now()
            self.logger.info(f"任务调度器停止成功 - 停止时间: {stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止调度器失败: {e}")
            return False
    
    def add_job(
        self,
        func: Callable,
        trigger: Optional[Union[BaseTrigger, str]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        name: Optional[str] = None,
        misfire_grace_time: Optional[int] = None,
        coalesce: Optional[bool] = None,
        max_instances: Optional[int] = None,
        **trigger_args
    ) -> Optional[Job]:
        """添加作业到调度器
        
        Args:
            func: 要执行的函数
            trigger: 触发器（可以是BaseTrigger实例或字符串：'date', 'interval', 'cron'）
            args: 函数的位置参数
            kwargs: 函数的关键字参数
            id: 作业ID（必须唯一）
            name: 作业名称
            misfire_grace_time: 错过执行的宽限时间（秒）
            coalesce: 是否合并错过的执行
            max_instances: 最大并发实例数
            **trigger_args: 触发器参数
            
        Returns:
            Optional[Job]: 创建的作业对象，如果失败则返回None
            
        Raises:
            ValueError: 当参数无效时
            RuntimeError: 当调度器未运行时
        """
        if not self._is_running:
            raise RuntimeError("调度器未运行，无法添加作业")
        
        try:
            # 构建作业参数
            job_kwargs = {
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "id": id,
                "name": name,
            }
            
            # 添加可选参数
            if misfire_grace_time is not None:
                job_kwargs["misfire_grace_time"] = misfire_grace_time
            if coalesce is not None:
                job_kwargs["coalesce"] = coalesce
            if max_instances is not None:
                job_kwargs["max_instances"] = max_instances
            
            # 处理触发器 - 这是问题的根源！
            if trigger is not None:
                if isinstance(trigger, str):
                    # 确保传递时区给触发器
                    if 'timezone' not in trigger_args:
                        trigger_args['timezone'] = pytz.timezone(self._config.get("timezone", "Asia/Shanghai"))
                    trigger = self._create_trigger(trigger, **trigger_args)
                job_kwargs["trigger"] = trigger
            
            job = self._scheduler.add_job(**job_kwargs)
            
            # 记录作业开始时间（用于性能监控）
            self._performance_metrics.record_job_start(job.id)
            
            self.logger.info(f"作业添加成功: {job.id} - {job.name or '未命名'}")
            return job
            
        except Exception as e:
            self.logger.error(f"添加作业失败: {e}")
            import traceback
            traceback.print_exc()  # 添加详细的错误追踪
            return None
    
    def remove_job(self, job_id: str) -> bool:
        """从调度器移除作业
        
        Args:
            job_id: 作业ID
            
        Returns:
            bool: 移除是否成功
        """
        try:
            self._scheduler.remove_job(job_id)
            self.logger.info(f"作业移除成功: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除作业失败 {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停作业
        
        Args:
            job_id: 作业ID
            
        Returns:
            bool: 暂停是否成功
        """
        try:
            self._scheduler.pause_job(job_id)
            self.logger.info(f"作业暂停成功: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"暂停作业失败 {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复作业
        
        Args:
            job_id: 作业ID
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            self._scheduler.resume_job(job_id)
            self.logger.info(f"作业恢复成功: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"恢复作业失败 {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取作业信息
        
        Args:
            job_id: 作业ID
            
        Returns:
            Optional[Job]: 作业对象，如果不存在则返回None
        """
        try:
            return self._scheduler.get_job(job_id)
        except Exception as e:
            self.logger.error(f"获取作业信息失败 {job_id}: {e}")
            return None
    
    def get_jobs(self) -> list[Job]:
        """获取所有作业
        
        Returns:
            list[Job]: 作业列表
        """
        try:
            return self._scheduler.get_jobs()
        except Exception as e:
            self.logger.error(f"获取作业列表失败: {e}")
            return []
    
    def modify_job(
        self,
        job_id: str,
        **changes
    ) -> bool:
        """修改作业
        
        Args:
            job_id: 作业ID
            **changes: 要修改的参数
            
        Returns:
            bool: 修改是否成功
        """
        try:
            self._scheduler.modify_job(job_id, **changes)
            self.logger.info(f"作业修改成功: {job_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"修改作业失败 {job_id}: {e}")
            return False
    
    def _create_trigger(self, trigger_type: str, **kwargs) -> BaseTrigger:
        """创建触发器
        
        Args:
            trigger_type: 触发器类型 ('date', 'interval', 'cron')
            **kwargs: 触发器参数
            
        Returns:
            BaseTrigger: 触发器实例
            
        Raises:
            ValueError: 当触发器类型无效时
        """
        if trigger_type == "date":
            return DateTrigger(**kwargs)
        elif trigger_type == "interval":
            return IntervalTrigger(**kwargs)
        elif trigger_type == "cron":
            return CronTrigger(**kwargs)
        else:
            raise ValueError(f"无效的触发器类型: {trigger_type}")
    
    def _job_executed_listener(self, event) -> None:
        """作业执行成功监听器
        
        Args:
            event: 作业执行事件
        """
        try:
            job = self._scheduler.get_job(event.job_id)
            job_name = job.name if job else None
            
            # 记录作业结束时间
            self._performance_metrics.record_job_end(event.job_id, success=True)
            
            # 更新统计信息
            self._statistics.record_success(event.job_id, job_name)
            
            # 获取执行时间信息
            job_metrics = self._performance_metrics.get_job_metrics(event.job_id)
            execution_time_ms = job_metrics.get('last_execution_time', 0)
            
            # 记录详细的执行成功信息
            scheduled_time = getattr(event, 'scheduled_run_time', None)
            if scheduled_time:
                self.logger.info(f"作业执行成功: {event.job_id} - {job_name or '未命名'} - "
                               f"计划执行时间: {scheduled_time} - "
                               f"执行耗时: {execution_time_ms:.2f}ms")
            else:
                self.logger.info(f"作业执行成功: {event.job_id} - {job_name or '未命名'} - "
                               f"执行耗时: {execution_time_ms:.2f}ms")
            
            # 每10次成功执行记录一次统计报告
            if self._statistics.success_count % 10 == 0:
                self.log_statistics_report()
                self.log_performance_report()
                
        except Exception as e:
            self.logger.error(f"处理作业执行成功事件失败: {e}")
    
    def _job_error_listener(self, event) -> None:
        """作业执行错误监听器
        
        Args:
            event: 作业执行事件
        """
        try:
            job = self._scheduler.get_job(event.job_id)
            job_name = job.name if job else None
            
            # 记录作业结束时间（失败）
            error_msg = f"{event.exception}"
            self._performance_metrics.record_job_end(event.job_id, success=False, error=error_msg)
            
            # 更新统计信息
            self._statistics.record_failure(event.job_id, job_name, error_msg)
            
            # 获取执行时间信息
            job_metrics = self._performance_metrics.get_job_metrics(event.job_id)
            execution_time_ms = job_metrics.get('last_execution_time', 0)
            
            # 记录详细的错误信息
            scheduled_time = getattr(event, 'scheduled_run_time', None)
            error_details = f"异常: {event.exception}"
            
            if scheduled_time:
                error_details += f", 计划执行时间: {scheduled_time}"
            
            self.logger.error(
                f"作业执行失败: {event.job_id} - {job_name or '未命名'} - "
                f"{error_details} - 执行耗时: {execution_time_ms:.2f}ms - "
                f"追踪: {event.traceback}"
            )
            
            # 每5次失败执行记录一次统计报告
            if self._statistics.failure_count % 5 == 0:
                self.log_statistics_report()
                self.log_performance_report()
                
        except Exception as e:
            self.logger.error(f"处理作业执行错误事件失败: {e}")
    
    def _job_missed_listener(self, event) -> None:
        """作业错过执行监听器
        
        Args:
            event: 作业错过执行事件
        """
        try:
            job = self._scheduler.get_job(event.job_id)
            job_name = job.name if job else None
            
            # 更新统计信息
            reason = f"作业错过执行时间: {event.scheduled_run_time}"
            self._statistics.record_skipped(event.job_id, job_name, reason)
            
            # 记录详细的错过执行信息
            self.logger.warning(f"作业错过执行: {event.job_id} - {job_name or '未命名'} - "
                              f"计划执行时间: {event.scheduled_run_time}")
            
            # 每10次跳过执行记录一次统计报告
            if self._statistics.skipped_count % 10 == 0:
                self.log_statistics_report()
                
        except Exception as e:
            self.logger.error(f"处理作业错过执行事件失败: {e}")
    
    @property
    def is_running(self) -> bool:
        """获取调度器运行状态
        
        Returns:
            bool: 调度器是否正在运行
        """
        return self._is_running
    
    @property
    def scheduler(self) -> Optional[BackgroundScheduler]:
        """获取调度器实例
        
        Returns:
            Optional[BackgroundScheduler]: 调度器实例
        """
        return self._scheduler
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取任务执行统计信息
        
        Returns:
            Dict[str, Any]: 包含统计信息的字典
        """
        return self._statistics.get_statistics()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取任务执行摘要
        
        Returns:
            Dict[str, Any]: 包含执行摘要的字典
        """
        return self._statistics.get_execution_summary()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            Dict[str, Any]: 性能指标信息
        """
        return self._performance_metrics.get_performance_summary()
    
    def get_job_performance_metrics(self, job_id: str) -> Dict[str, Any]:
        """获取指定作业的性能指标
        
        Args:
            job_id: 作业ID
            
        Returns:
            Dict[str, Any]: 作业性能指标
        """
        return self._performance_metrics.get_job_metrics(job_id)
    
    def log_statistics_report(self) -> None:
        """记录任务执行统计报告
        
        输出详细的任务执行统计信息，包括成功率、最近执行情况等。
        """
        try:
            stats = self.get_statistics()
            summary = self.get_execution_summary()
            jobs = self.get_jobs()
            
            self.logger.info("=" * 60)
            self.logger.info("任务调度器统计报告")
            self.logger.info("=" * 60)
            
            # 基本统计信息
            self.logger.info(f"作业总数: {len(jobs)}")
            self.logger.info(f"总执行次数: {stats['total_executions']}")
            self.logger.info(f"成功次数: {stats['success_count']} ({stats['success_rate']:.2%})")
            self.logger.info(f"失败次数: {stats['failure_count']} ({stats['failure_rate']:.2%})")
            self.logger.info(f"跳过次数: {stats['skipped_count']} ({stats['skipped_rate']:.2%})")
            
            # 时间信息
            if stats['last_execution_time']:
                self.logger.info(f"最后执行时间: {stats['last_execution_time']}")
            if stats['last_success_time']:
                self.logger.info(f"最后成功时间: {stats['last_success_time']}")
            if stats['last_failure_time']:
                self.logger.info(f"最后失败时间: {stats['last_failure_time']}")
            
            # 运行时长
            if self._start_time:
                runtime = datetime.now() - self._start_time
                self.logger.info(f"运行时长: {runtime}")
            
            # 最近执行情况
            recent_executions = summary.get('recent_executions', [])
            if recent_executions:
                self.logger.info(f"最近 {len(recent_executions)} 次执行:")
                for i, execution in enumerate(recent_executions[-5:], 1):  # 只显示最近5次
                    job_name = execution.get('job_name', '未命名')
                    status = execution.get('status', 'unknown')
                    timestamp = execution.get('timestamp', '未知时间')
                    self.logger.info(f"  {i}. {job_name} - {status} - {timestamp}")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"记录统计报告失败: {e}")
    
    def reset_statistics(self) -> bool:
        """重置任务执行统计
        
        Returns:
            bool: 重置是否成功
        """
        try:
            self._statistics.reset()
            self._performance_metrics.reset_metrics()
            self.logger.info("任务执行统计和性能指标已重置")
            return True
        except Exception as e:
            self.logger.error(f"重置统计失败: {e}")
            return False
    
    def log_performance_report(self) -> None:
        """记录性能指标报告
        
        输出详细的性能指标信息，包括执行时间、吞吐量等。
        """
        try:
            performance_summary = self.get_performance_metrics()
            system_metrics = performance_summary['system_metrics']
            
            self.logger.info("=" * 60)
            self.logger.info("任务调度器性能指标报告")
            self.logger.info("=" * 60)
            
            # 基本性能指标
            self.logger.info(f"系统运行时间: {system_metrics['uptime_formatted']}")
            self.logger.info(f"总执行次数: {system_metrics['execution_count']}")
            self.logger.info(f"总执行时间: {system_metrics['total_execution_time']:.2f}ms")
            self.logger.info(f"平均执行时间: {system_metrics['average_execution_time']:.2f}ms")
            self.logger.info(f"最大执行时间: {system_metrics['max_execution_time']:.2f}ms")
            self.logger.info(f"最小执行时间: {system_metrics['min_execution_time']:.2f}ms")
            
            # 性能指标
            indicators = performance_summary['performance_indicators']
            self.logger.info(f"执行效率: {indicators['efficiency']:.2f} 次/小时")
            self.logger.info(f"平均响应时间: {indicators['average_response_time']:.2f}ms")
            self.logger.info(f"吞吐量: {indicators['throughput']} 次")
            
            # 作业级别指标（前5个）
            active_jobs = performance_summary['active_jobs'][:5]
            if active_jobs:
                self.logger.info("活跃作业性能指标（前5个）:")
                for i, job_id in enumerate(active_jobs, 1):
                    job_metrics = self.get_job_performance_metrics(job_id)
                    if job_metrics:
                        self.logger.info(
                            f"  {i}. 作业ID: {job_id} - "
                            f"执行次数: {job_metrics.get('execution_count', 0)} - "
                            f"平均时间: {job_metrics.get('average_time', 0):.2f}ms - "
                            f"最后执行: {job_metrics.get('last_execution_time', 0):.2f}ms"
                        )
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"记录性能指标报告失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
    
    def execute_pending_tasks(self) -> int:
        """执行待处理的任务
        
        查询所有待处理且未完成的任务（visited_num < total_num），
        并使用爬虫服务执行这些任务。同时更新执行统计信息。
        
        Returns:
            int: 执行的任务数量
        """
        executed_count = 0
        success_count = 0
        failure_count = 0
        start_time = datetime.now()
        
        self.logger.info("开始执行待处理任务扫描...")
        
        try:
            # 使用Flask的数据库连接
            from src.app import db
            
            # 查询待处理且未完成的任务
            pending_tasks = db.session.query(Task).filter(
                Task.status == 'pending',
                Task.visited_num < Task.total_num,
                Task.total_num > 0
            ).all()
            
            if not pending_tasks:
                self.logger.info("没有待执行的任务")
                return 0
            
            self.logger.info(f"发现 {len(pending_tasks)} 个待执行任务")
            
            # 记录任务详情
            self.logger.info("待执行任务详情:")
            for i, task in enumerate(pending_tasks[:10], 1):  # 只显示前10个任务
                self.logger.info(f"  {i}. 任务ID: {task.id}, URL: {task.url}, "
                               f"进度: {task.visited_num}/{task.total_num}")
            if len(pending_tasks) > 10:
                self.logger.info(f"  ... 还有 {len(pending_tasks) - 10} 个任务待执行")
            
            # 初始化爬虫服务
            crawler_service = CrawlerService()
            
            for task in pending_tasks:
                try:
                    # 更新任务状态为运行中
                    task.update_status('running')
                    db.session.commit()
                    
                    self.logger.info(f"开始执行任务: {task.id} - {task.url}")
                    
                    # 执行爬虫任务并保存结果
                    # 使用Task模型的完整HTTP配置
                    result = crawler_service.crawl_and_save(
                        task.url,
                        method=task.method,
                        body=task.body,
                        headers=task.headers,
                        timeout=task.timeout,
                        retry_count=task.retry_count
                    )
                    
                    # 更新任务状态和统计信息
                    if result['status'] == 'success':
                        task.update_status('completed')
                        task.increment_visited()
                        success_count += 1
                        self._statistics.record_success(f"task_{task.id}", task.url)
                        self.logger.info(f"任务执行成功: {task.id}")
                    else:
                        task.update_status('failed')
                        task.increment_retry()
                        failure_count += 1
                        error_msg = result.get('error', '未知错误')
                        self._statistics.record_failure(f"task_{task.id}", task.url, error_msg)
                        self.logger.warning(f"任务执行失败: {task.id}, 原因: {error_msg}")
                    
                    db.session.commit()
                    executed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"执行任务 {task.id} 时发生错误: {e}")
                    task.update_status('failed')
                    task.increment_retry()
                    failure_count += 1
                    self._statistics.record_failure(f"task_{task.id}", task.url, str(e))
                    db.session.commit()
                    continue
            
            crawler_service.close()
            
            # 记录详细的执行统计摘要
            execution_time = datetime.now() - start_time
            self.logger.info("任务执行扫描完成")
            self.logger.info(f"执行统计摘要:")
            self.logger.info(f"  - 总计执行: {executed_count} 个任务")
            self.logger.info(f"  - 成功: {success_count} 个")
            self.logger.info(f"  - 失败: {failure_count} 个")
            self.logger.info(f"  - 执行耗时: {execution_time}")
            self.logger.info(f"  - 平均执行时间: {execution_time / executed_count if executed_count > 0 else 0}")
            
            # 每执行完一批任务记录统计报告
            if executed_count > 0:
                self.log_statistics_report()
            
            return executed_count
                
        except Exception as e:
            self.logger.error(f"执行待处理任务时发生错误: {e}")
            execution_time = datetime.now() - start_time
            self.logger.error(f"执行失败，已运行时间: {execution_time}")
            return executed_count
    
    def _execute_single_task(self, task: Task, crawler_service: CrawlerService) -> Dict[str, Any]:
        """执行单个任务
        
        Args:
            task: 任务对象
            crawler_service: 爬虫服务实例
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            result = crawler_service.crawl_address(
                task.url,
                method=task.method,
                body=task.body,
                headers=task.headers,
                timeout=task.timeout,
                retry_count=task.retry_count
            )
            
            return result
            
        except Exception as e:
            error_msg = f"执行任务时发生异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }


# 全局调度器实例
_scheduler_instance: Optional[TaskScheduler] = None


def get_scheduler(config: Optional[Dict[str, Any]] = None) -> TaskScheduler:
    """获取全局调度器实例
    
    Args:
        config: 调度器配置，如果为None则使用默认配置
        
    Returns:
        TaskScheduler: 调度器实例
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler(config)
    
    return _scheduler_instance


def start_scheduler(config: Optional[Dict[str, Any]] = None) -> bool:
    """启动全局调度器
    
    Args:
        config: 调度器配置，如果为None则使用默认配置
        
    Returns:
        bool: 启动是否成功
    """
    scheduler = get_scheduler(config)
    return scheduler.start()


def stop_scheduler(wait: bool = True) -> bool:
    """停止全局调度器
    
    Args:
        wait: 是否等待正在运行的作业完成
        
    Returns:
        bool: 停止是否成功
    """
    global _scheduler_instance
    
    if _scheduler_instance is None:
        return True
    
    result = _scheduler_instance.stop(wait)
    _scheduler_instance = None
    return result