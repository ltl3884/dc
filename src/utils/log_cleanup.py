"""
日志轮转和清理工具模块

该模块提供日志文件生命周期管理功能，包括：
- 日志文件大小检查和监控
- 自动日志轮转功能
- 基于保留策略的旧日志清理
- 日志文件压缩和归档
- 批量日志管理操作

作者: Claude Code
创建时间: 2025-09-10
"""

import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from src.config import get_logging_config


class LogCleanupError(Exception):
    """日志清理相关错误的基类"""
    pass


class LogCleanup:
    """
    日志文件清理和轮转管理器
    
    提供日志文件的生命周期管理，包括大小监控、自动轮转和定期清理功能。
    """
    
    def __init__(
        self,
        log_directory: Optional[str] = None,
        retention_days: int = 30,
        max_size_mb: int = 100,
        backup_count: int = 5,
        compress_old_logs: bool = True
    ):
        """
        初始化日志清理管理器
        
        Args:
            log_directory: 日志目录路径，如果为None则使用配置中的路径
            retention_days: 日志保留天数，超过此时间的日志将被删除
            max_size_mb: 日志文件最大大小（MB），超过此大小将触发轮转
            backup_count: 保留的备份文件数量
            compress_old_logs: 是否压缩旧的日志文件
            
        Raises:
            LogCleanupError: 当日志目录不存在且无法创建时
        """
        self.retention_days = retention_days
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.compress_old_logs = compress_old_logs
        
        # 设置日志目录
        if log_directory:
            self.log_directory = Path(log_directory)
        else:
            config = get_logging_config()
            self.log_directory = Path(config["file_path"]).parent
        
        # 确保日志目录存在
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise LogCleanupError(f"无法创建日志目录 {self.log_directory}: {e}")
        
        # 设置日志记录器
        self.logger = logging.getLogger(__name__)
    
    def get_log_files(self, pattern: str = "*.log*") -> List[Path]:
        """
        获取日志目录中的日志文件列表
        
        Args:
            pattern: 文件匹配模式
            
        Returns:
            List[Path]: 日志文件路径列表，按修改时间排序
        """
        log_files = list(self.log_directory.glob(pattern))
        # 按修改时间排序，最新的在前
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return log_files
    
    def get_file_size(self, file_path: Path) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            int: 文件大小（字节）
        """
        try:
            return file_path.stat().st_size
        except OSError:
            return 0
    
    def is_file_old(self, file_path: Path, days: Optional[int] = None) -> bool:
        """
        检查文件是否超过指定天数
        
        Args:
            file_path: 文件路径
            days: 天数，如果为None则使用默认保留天数
            
        Returns:
            bool: 文件是否过期
        """
        if days is None:
            days = self.retention_days
        
        try:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            cutoff_date = datetime.now() - timedelta(days=days)
            return file_mtime < cutoff_date
        except OSError:
            return False
    
    def compress_log_file(self, file_path: Path) -> bool:
        """
        压缩日志文件
        
        Args:
            file_path: 要压缩的文件路径
            
        Returns:
            bool: 压缩是否成功
            
        Note:
            压缩后的文件将添加 .gz 扩展名
        """
        if not file_path.exists():
            return False
        
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            file_path.unlink()
            self.logger.info(f"日志文件已压缩: {file_path} -> {compressed_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"压缩日志文件失败 {file_path}: {e}")
            return False
    
    def rotate_log_file(self, file_path: Path) -> bool:
        """
        轮转日志文件
        
        Args:
            file_path: 要轮转的日志文件路径
            
        Returns:
            bool: 轮转是否成功
            
        Note:
            将当前日志文件重命名为带时间戳的备份文件
        """
        if not file_path.exists():
            return False
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = file_path.parent / backup_name
        
        try:
            # 重命名当前日志文件
            shutil.move(str(file_path), str(backup_path))
            
            # 如果启用压缩，压缩备份文件
            if self.compress_old_logs:
                self.compress_log_file(backup_path)
            
            self.logger.info(f"日志文件已轮转: {file_path} -> {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"轮转日志文件失败 {file_path}: {e}")
            return False
    
    def check_file_size_and_rotate(self, file_path: Path) -> bool:
        """
        检查文件大小并在需要时轮转
        
        Args:
            file_path: 要检查的日志文件路径
            
        Returns:
            bool: 是否执行了轮转操作
        """
        if not file_path.exists():
            return False
        
        file_size = self.get_file_size(file_path)
        
        if file_size > self.max_size_bytes:
            self.logger.info(f"日志文件 {file_path} 大小 ({file_size} bytes) 超过阈值 ({self.max_size_bytes} bytes)，执行轮转")
            return self.rotate_log_file(file_path)
        
        return False
    
    def clean_old_logs(self, days: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        清理旧的日志文件
        
        Args:
            days: 保留天数，如果为None则使用默认设置
            dry_run: 是否仅模拟运行，不实际删除文件
            
        Returns:
            Dict[str, Any]: 清理统计信息
            
        Note:
            删除超过保留期限的日志文件，包括压缩文件
        """
        if days is None:
            days = self.retention_days
        
        stats = {
            "total_files_checked": 0,
            "files_deleted": 0,
            "space_freed": 0,
            "errors": 0,
            "deleted_files": []
        }
        
        # 获取所有日志文件（包括压缩文件）
        log_files = self.get_log_files("*.log*")
        
        for file_path in log_files:
            stats["total_files_checked"] += 1
            
            if self.is_file_old(file_path, days):
                try:
                    file_size = self.get_file_size(file_path)
                    
                    if not dry_run:
                        file_path.unlink()
                        self.logger.info(f"删除旧日志文件: {file_path}")
                    
                    stats["files_deleted"] += 1
                    stats["space_freed"] += file_size
                    stats["deleted_files"].append(str(file_path))
                    
                except Exception as e:
                    stats["errors"] += 1
                    self.logger.error(f"删除日志文件失败 {file_path}: {e}")
        
        # 转换为MB显示
        stats["space_freed_mb"] = stats["space_freed"] / (1024 * 1024)
        
        if dry_run:
            self.logger.info(f"模拟清理完成，将删除 {stats['files_deleted']} 个文件，释放 {stats['space_freed_mb']:.2f} MB 空间")
        else:
            self.logger.info(f"清理完成，已删除 {stats['files_deleted']} 个文件，释放 {stats['space_freed_mb']:.2f} MB 空间")
        
        return stats
    
    def cleanup_backup_files(self, max_backups: Optional[int] = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        清理过多的备份文件
        
        Args:
            max_backups: 最大备份文件数量，如果为None则使用默认设置
            dry_run: 是否仅模拟运行，不实际删除文件
            
        Returns:
            Dict[str, Any]: 清理统计信息
        """
        if max_backups is None:
            max_backups = self.backup_count
        
        stats = {
            "total_files_checked": 0,
            "files_deleted": 0,
            "space_freed": 0,
            "errors": 0,
            "deleted_files": []
        }
        
        # 获取所有备份文件（轮转和压缩的日志文件）
        backup_files = []
        for pattern in ["*.log_*", "*.log_*.gz", "*_*.*.log*"]:
            backup_files.extend(self.get_log_files(pattern))
        
        # 按修改时间排序，最新的在前
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # 保留最新的备份文件，删除多余的
        files_to_delete = backup_files[max_backups:]
        
        for file_path in files_to_delete:
            stats["total_files_checked"] += 1
            
            try:
                file_size = self.get_file_size(file_path)
                
                if not dry_run:
                    file_path.unlink()
                    self.logger.info(f"删除多余备份文件: {file_path}")
                
                stats["files_deleted"] += 1
                stats["space_freed"] += file_size
                stats["deleted_files"].append(str(file_path))
                
            except Exception as e:
                stats["errors"] += 1
                self.logger.error(f"删除备份文件失败 {file_path}: {e}")
        
        # 转换为MB显示
        stats["space_freed_mb"] = stats["space_freed"] / (1024 * 1024)
        
        if dry_run:
            self.logger.info(f"模拟备份清理完成，将删除 {stats['files_deleted']} 个文件，释放 {stats['space_freed_mb']:.2f} MB 空间")
        else:
            self.logger.info(f"备份清理完成，已删除 {stats['files_deleted']} 个文件，释放 {stats['space_freed_mb']:.2f} MB 空间")
        
        return stats
    
    def perform_maintenance(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        执行完整的日志维护操作
        
        Args:
            dry_run: 是否仅模拟运行，不实际执行操作
            
        Returns:
            Dict[str, Any]: 维护操作统计信息
        """
        self.logger.info(f"开始执行日志维护操作 (模拟模式: {dry_run})")
        
        stats = {
            "rotation_performed": 0,
            "old_logs_cleaned": {},
            "backup_files_cleaned": {},
            "total_space_freed_mb": 0,
            "errors": 0
        }
        
        try:
            # 1. 检查并轮转当前日志文件
            config = get_logging_config()
            current_log_file = Path(config["file_path"])
            
            if self.check_file_size_and_rotate(current_log_file):
                stats["rotation_performed"] += 1
            
            # 2. 清理旧日志文件
            old_logs_stats = self.clean_old_logs(dry_run=dry_run)
            stats["old_logs_cleaned"] = old_logs_stats
            
            # 3. 清理多余备份文件
            backup_stats = self.cleanup_backup_files(dry_run=dry_run)
            stats["backup_files_cleaned"] = backup_stats
            
            # 计算总释放空间
            total_space_freed = (
                old_logs_stats.get("space_freed", 0) + 
                backup_stats.get("space_freed", 0)
            )
            stats["total_space_freed_mb"] = total_space_freed / (1024 * 1024)
            
            # 计算总错误数
            stats["errors"] = (
                old_logs_stats.get("errors", 0) + 
                backup_stats.get("errors", 0)
            )
            
            self.logger.info(f"日志维护操作完成，共释放 {stats['total_space_freed_mb']:.2f} MB 空间")
            
        except Exception as e:
            stats["errors"] += 1
            self.logger.error(f"执行日志维护操作时发生错误: {e}")
        
        return stats
    
    def get_disk_usage_stats(self) -> Dict[str, Any]:
        """
        获取日志目录磁盘使用情况统计
        
        Returns:
            Dict[str, Any]: 磁盘使用统计信息
        """
        try:
            total_size = 0
            file_count = 0
            oldest_file = None
            newest_file = None
            oldest_time = None
            newest_time = None
            
            log_files = self.get_log_files()
            
            for file_path in log_files:
                try:
                    stat = file_path.stat()
                    file_size = stat.st_size
                    file_mtime = stat.st_mtime
                    
                    total_size += file_size
                    file_count += 1
                    
                    # 更新最旧文件
                    if oldest_time is None or file_mtime < oldest_time:
                        oldest_time = file_mtime
                        oldest_file = str(file_path)
                    
                    # 更新最新文件
                    if newest_time is None or file_mtime > newest_time:
                        newest_time = file_mtime
                        newest_file = str(file_path)
                        
                except OSError:
                    continue
            
            return {
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "file_count": file_count,
                "oldest_file": oldest_file,
                "newest_file": newest_file,
                "oldest_file_date": datetime.fromtimestamp(oldest_time) if oldest_time else None,
                "newest_file_date": datetime.fromtimestamp(newest_time) if newest_time else None,
                "log_directory": str(self.log_directory)
            }
            
        except Exception as e:
            self.logger.error(f"获取磁盘使用统计失败: {e}")
            return {
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "file_count": 0,
                "oldest_file": None,
                "newest_file": None,
                "oldest_file_date": None,
                "newest_file_date": None,
                "log_directory": str(self.log_directory),
                "error": str(e)
            }


def create_log_cleanup_manager(**kwargs) -> LogCleanup:
    """
    创建日志清理管理器实例
    
    Args:
        **kwargs: 传递给LogCleanup构造函数的参数
        
    Returns:
        LogCleanup: 日志清理管理器实例
    """
    return LogCleanup(**kwargs)


def cleanup_old_logs(days: int = 30, dry_run: bool = False) -> Dict[str, Any]:
    """
    快速清理旧日志文件的便捷函数
    
    Args:
        days: 保留天数
        dry_run: 是否仅模拟运行
        
    Returns:
        Dict[str, Any]: 清理统计信息
    """
    manager = create_log_cleanup_manager(retention_days=days)
    return manager.clean_old_logs(days=days, dry_run=dry_run)


def rotate_oversized_logs(max_size_mb: int = 100) -> int:
    """
    轮转过大的日志文件的便捷函数
    
    Args:
        max_size_mb: 最大文件大小（MB）
        
    Returns:
        int: 轮转的日志文件数量
    """
    manager = create_log_cleanup_manager(max_size_mb=max_size_mb)
    config = get_logging_config()
    current_log_file = Path(config["file_path"])
    
    if manager.check_file_size_and_rotate(current_log_file):
        return 1
    return 0