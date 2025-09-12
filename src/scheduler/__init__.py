"""
任务调度器包

该包提供基于APScheduler的任务调度功能，包括：
- TaskScheduler: 主要调度器类
- TaskStatistics: 任务统计类
- 全局调度器管理函数
- 调度器配置常量
- 调度器级工具函数

作者: Claude Code
创建时间: 2025-09-10
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
import pytz

from .task_scheduler import TaskScheduler, TaskStatistics, get_scheduler, start_scheduler, stop_scheduler

# 调度器配置常量
SCHEDULER_CONFIG_DEFAULTS = {
    "timezone": "Asia/Shanghai",
    "job_defaults": {
        "coalesce": True,
        "max_instances": 3,
        "misfire_grace_time": 300
    },
    "api_enabled": True
}

# 任务状态常量
TASK_STATUS_PENDING = "pending"
TASK_STATUS_RUNNING = "running"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
TASK_STATUS_PAUSED = "paused"

# 触发器类型常量
TRIGGER_TYPE_DATE = "date"
TRIGGER_TYPE_INTERVAL = "interval"
TRIGGER_TYPE_CRON = "cron"

# 默认时间格式
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# 调度器事件类型
EVENT_JOB_EXECUTED = "job_executed"
EVENT_JOB_ERROR = "job_error"
EVENT_JOB_MISSED = "job_missed"

# 最大历史记录大小
MAX_HISTORY_SIZE = 1000


def get_default_timezone() -> pytz.BaseTzInfo:
    """获取默认时区
    
    Returns:
        pytz.BaseTzInfo: 默认时区对象
    """
    return pytz.timezone(SCHEDULER_CONFIG_DEFAULTS["timezone"])


def format_datetime(dt: datetime, fmt: str = DEFAULT_DATETIME_FORMAT) -> str:
    """格式化日期时间
    
    Args:
        dt: 日期时间对象
        fmt: 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)


def parse_datetime(dt_str: str, fmt: str = DEFAULT_DATETIME_FORMAT) -> Optional[datetime]:
    """解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        fmt: 格式字符串
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象，失败时返回None
    """
    try:
        return datetime.strptime(dt_str, fmt)
    except (ValueError, TypeError):
        return None


def create_trigger(trigger_type: str, **kwargs) -> Optional[Dict[str, Any]]:
    """创建触发器配置
    
    Args:
        trigger_type: 触发器类型 (date, interval, cron)
        **kwargs: 触发器参数
        
    Returns:
        Optional[Dict[str, Any]]: 触发器配置字典，失败时返回None
    """
    try:
        trigger_config = {"type": trigger_type}
        
        if trigger_type == TRIGGER_TYPE_DATE:
            # 日期触发器 - 指定具体执行时间
            if "run_date" in kwargs:
                trigger_config["run_date"] = kwargs["run_date"]
            elif "date_str" in kwargs:
                trigger_config["run_date"] = parse_datetime(kwargs["date_str"])
            
        elif trigger_type == TRIGGER_TYPE_INTERVAL:
            # 间隔触发器 - 指定间隔时间
            if "seconds" in kwargs:
                trigger_config["seconds"] = kwargs["seconds"]
            if "minutes" in kwargs:
                trigger_config["minutes"] = kwargs["minutes"]
            if "hours" in kwargs:
                trigger_config["hours"] = kwargs["hours"]
            if "days" in kwargs:
                trigger_config["days"] = kwargs["days"]
            if "start_date" in kwargs:
                trigger_config["start_date"] = kwargs["start_date"]
            if "end_date" in kwargs:
                trigger_config["end_date"] = kwargs["end_date"]
                
        elif trigger_type == TRIGGER_TYPE_CRON:
            # Cron触发器 - 指定Cron表达式
            cron_fields = ["year", "month", "day", "week", "day_of_week", 
                          "hour", "minute", "second"]
            for field in cron_fields:
                if field in kwargs:
                    trigger_config[field] = kwargs[field]
            if "start_date" in kwargs:
                trigger_config["start_date"] = kwargs["start_date"]
            if "end_date" in kwargs:
                trigger_config["end_date"] = kwargs["end_date"]
        else:
            logging.warning(f"不支持的触发器类型: {trigger_type}")
            return None
            
        # 设置默认时区
        if "timezone" not in trigger_config:
            trigger_config["timezone"] = get_default_timezone()
            
        return trigger_config
        
    except Exception as e:
        logging.error(f"创建触发器配置失败: {e}")
        return None


def validate_job_id(job_id: str) -> bool:
    """验证作业ID的有效性
    
    Args:
        job_id: 作业ID
        
    Returns:
        bool: 是否有效
    """
    if not job_id or not isinstance(job_id, str):
        return False
    
    # 作业ID应该只包含字母、数字、下划线和连字符
    import re
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', job_id))


def generate_job_id(prefix: str = "job", suffix: str = "") -> str:
    """生成唯一的作业ID
    
    Args:
        prefix: ID前缀
        suffix: ID后缀
        
    Returns:
        str: 生成的作业ID
    """
    import uuid
    unique_id = str(uuid.uuid4()).replace("-", "")[:8]
    job_id = f"{prefix}_{unique_id}"
    if suffix:
        job_id = f"{job_id}_{suffix}"
    return job_id


def get_scheduler_status(scheduler: Optional[TaskScheduler] = None) -> Dict[str, Any]:
    """获取调度器状态信息
    
    Args:
        scheduler: 调度器实例，如果为None则使用全局实例
        
    Returns:
        Dict[str, Any]: 调度器状态信息
    """
    if scheduler is None:
        try:
            scheduler = get_scheduler()
        except Exception:
            return {"status": "not_initialized", "is_running": False}
    
    try:
        status_info = {
            "is_running": scheduler.is_running,
            "status": "running" if scheduler.is_running else "stopped",
            "statistics": scheduler.get_statistics() if scheduler.is_running else {},
            "job_count": len(scheduler.get_jobs()) if scheduler.is_running else 0
        }
        
        if scheduler.is_running:
            status_info["execution_summary"] = scheduler.get_execution_summary()
            
        return status_info
        
    except Exception as e:
        logging.error(f"获取调度器状态失败: {e}")
        return {"status": "error", "error": str(e), "is_running": False}


def safe_stop_scheduler(wait: bool = True, timeout: int = 30) -> bool:
    """安全停止调度器，带超时保护
    
    Args:
        wait: 是否等待正在运行的作业完成
        timeout: 超时时间（秒）
        
    Returns:
        bool: 是否成功停止
    """
    try:
        import threading
        import time
        
        scheduler = get_scheduler()
        if not scheduler.is_running:
            return True
            
        # 使用线程来避免阻塞
        stop_result = {"success": False}
        
        def stop_worker():
            try:
                stop_result["success"] = scheduler.stop(wait=wait)
            except Exception as e:
                logging.error(f"停止调度器时发生错误: {e}")
                stop_result["success"] = False
        
        stop_thread = threading.Thread(target=stop_worker)
        stop_thread.start()
        stop_thread.join(timeout=timeout)
        
        if stop_thread.is_alive():
            logging.warning(f"停止调度器超时（{timeout}秒），强制终止")
            # 强制停止
            try:
                scheduler.stop(wait=False)
                return True
            except Exception as e:
                logging.error(f"强制停止调度器失败: {e}")
                return False
                
        return stop_result.get("success", False)
        
    except Exception as e:
        logging.error(f"安全停止调度器失败: {e}")
        return False


# 便捷函数别名
create_date_trigger = lambda **kwargs: create_trigger(TRIGGER_TYPE_DATE, **kwargs)
create_interval_trigger = lambda **kwargs: create_trigger(TRIGGER_TYPE_INTERVAL, **kwargs)
create_cron_trigger = lambda **kwargs: create_trigger(TRIGGER_TYPE_CRON, **kwargs)

__all__ = [
    # 主要类
    "TaskScheduler",
    "TaskStatistics",
    
    # 配置常量
    "SCHEDULER_CONFIG_DEFAULTS",
    "TASK_STATUS_PENDING",
    "TASK_STATUS_RUNNING", 
    "TASK_STATUS_COMPLETED",
    "TASK_STATUS_FAILED",
    "TASK_STATUS_PAUSED",
    "TRIGGER_TYPE_DATE",
    "TRIGGER_TYPE_INTERVAL",
    "TRIGGER_TYPE_CRON",
    "DEFAULT_DATETIME_FORMAT",
    "DEFAULT_DATE_FORMAT",
    "EVENT_JOB_EXECUTED",
    "EVENT_JOB_ERROR",
    "EVENT_JOB_MISSED",
    "MAX_HISTORY_SIZE",
    
    # 全局管理函数
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    
    # 工具函数
    "get_default_timezone",
    "format_datetime",
    "parse_datetime",
    "create_trigger",
    "validate_job_id",
    "generate_job_id",
    "get_scheduler_status",
    "safe_stop_scheduler",
    
    # 便捷函数
    "create_date_trigger",
    "create_interval_trigger", 
    "create_cron_trigger"
]