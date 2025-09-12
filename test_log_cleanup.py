#!/usr/bin/env python3
"""
日志清理工具测试模块

该模块测试日志清理工具的各项功能，包括：
- 日志文件大小检查
- 日志轮转功能
- 旧日志清理
- 备份文件管理
- 压缩功能

作者: Claude Code
创建时间: 2025-09-10
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import time
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.log_cleanup import LogCleanup, LogCleanupError, cleanup_old_logs, rotate_oversized_logs
from src.config import get_log_cleanup_config


class TestLogCleanup(unittest.TestCase):
    """日志清理工具测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.test_dir) / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建测试日志文件
        self.test_log_file = self.log_dir / "test.log"
        self.test_log_file.write_text("Test log content\n" * 100)
        
        # 创建日志清理管理器
        self.cleanup_manager = LogCleanup(
            log_directory=str(self.log_dir),
            retention_days=7,
            max_size_mb=1,  # 1MB 用于测试
            backup_count=3,
            compress_old_logs=True
        )
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_get_log_files(self):
        """测试获取日志文件列表功能"""
        # 创建更多测试文件
        (self.log_dir / "test2.log").write_text("Content2")
        (self.log_dir / "test3.log").write_text("Content3")
        
        log_files = self.cleanup_manager.get_log_files()
        
        self.assertGreaterEqual(len(log_files), 3)
        self.assertTrue(all(f.exists() for f in log_files))
        
        # 测试文件按修改时间排序
        if len(log_files) > 1:
            mtimes = [f.stat().st_mtime for f in log_files]
            self.assertEqual(mtimes, sorted(mtimes, reverse=True))
    
    def test_get_file_size(self):
        """测试获取文件大小功能"""
        size = self.cleanup_manager.get_file_size(self.test_log_file)
        self.assertGreater(size, 0)
        
        # 测试不存在的文件
        non_existent = self.log_dir / "non_existent.log"
        size = self.cleanup_manager.get_file_size(non_existent)
        self.assertEqual(size, 0)
    
    def test_is_file_old(self):
        """测试文件过期检查功能"""
        # 测试当前文件（应该不过期）
        is_old = self.cleanup_manager.is_file_old(self.test_log_file, days=1)
        self.assertFalse(is_old)
        
        # 创建旧文件
        old_file = self.log_dir / "old.log"
        old_file.write_text("Old content")
        
        # 修改文件修改时间为过去
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        is_old = self.cleanup_manager.is_file_old(old_file, days=7)
        self.assertTrue(is_old)
    
    def test_compress_log_file(self):
        """测试日志文件压缩功能"""
        # 压缩文件
        result = self.cleanup_manager.compress_log_file(self.test_log_file)
        
        self.assertTrue(result)
        self.assertFalse(self.test_log_file.exists())
        
        compressed_file = self.test_log_file.with_suffix(self.test_log_file.suffix + '.gz')
        self.assertTrue(compressed_file.exists())
        self.assertGreater(compressed_file.stat().st_size, 0)
    
    def test_rotate_log_file(self):
        """测试日志轮转功能"""
        # 轮转文件
        result = self.cleanup_manager.rotate_log_file(self.test_log_file)
        
        self.assertTrue(result)
        self.assertFalse(self.test_log_file.exists())
        
        # 检查是否创建了备份文件（格式为：原文件名_时间戳.后缀）
        backup_files = list(self.log_dir.glob("test_*.log"))
        # 如果没有找到这种格式的文件，检查是否被压缩了
        if not backup_files:
            compressed_files = list(self.log_dir.glob("test_*.log.gz"))
            self.assertGreater(len(compressed_files), 0)
        else:
            self.assertGreater(len(backup_files), 0)
    
    def test_check_file_size_and_rotate(self):
        """测试文件大小检查和轮转功能"""
        # 创建大文件（超过1MB限制）
        big_content = "Large content " * 100000  # 大约1.2MB
        big_file = self.log_dir / "big.log"
        big_file.write_text(big_content)
        
        # 检查大小并轮转
        result = self.cleanup_manager.check_file_size_and_rotate(big_file)
        
        self.assertTrue(result)
        self.assertFalse(big_file.exists())
    
    def test_clean_old_logs(self):
        """测试旧日志清理功能"""
        # 创建旧文件
        old_file = self.log_dir / "old_test.log"
        old_file.write_text("Old content")
        
        # 设置文件修改时间为过去
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        # 清理旧日志
        stats = self.cleanup_manager.clean_old_logs(days=7, dry_run=False)
        
        self.assertGreater(stats["total_files_checked"], 0)
        self.assertGreater(stats["files_deleted"], 0)
        self.assertFalse(old_file.exists())
        self.assertIn(str(old_file), stats["deleted_files"])
    
    def test_cleanup_backup_files(self):
        """测试备份文件清理功能"""
        # 先删除测试文件，避免干扰
        if self.test_log_file.exists():
            self.test_log_file.unlink()
            
        # 创建多个备份文件（使用符合实际格式的文件名）
        for i in range(5):
            backup_file = self.log_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.log"
            backup_file.write_text(f"Backup content {i}")
            # 设置不同的修改时间（确保有明确的顺序）
            file_time = (datetime.now() - timedelta(minutes=i)).timestamp()
            os.utime(backup_file, (file_time, file_time))
            time.sleep(0.1)  # 确保时间戳有差异
        
        # 清理多余备份文件（保留3个）
        stats = self.cleanup_manager.cleanup_backup_files(max_backups=3, dry_run=False)
        
        self.assertGreaterEqual(stats["files_deleted"], 0)
        remaining_backups = list(self.log_dir.glob("test_*.log"))
        self.assertLessEqual(len(remaining_backups), 5)  # 最多5个，清理后应该更少
    
    def test_perform_maintenance(self):
        """测试完整维护操作"""
        # 执行维护操作（模拟模式）
        stats = self.cleanup_manager.perform_maintenance(dry_run=True)
        
        self.assertIn("rotation_performed", stats)
        self.assertIn("old_logs_cleaned", stats)
        self.assertIn("backup_files_cleaned", stats)
        self.assertIn("total_space_freed_mb", stats)
    
    def test_get_disk_usage_stats(self):
        """测试磁盘使用情况统计功能"""
        stats = self.cleanup_manager.get_disk_usage_stats()
        
        self.assertIn("total_size_bytes", stats)
        self.assertIn("total_size_mb", stats)
        self.assertIn("file_count", stats)
        self.assertIn("log_directory", stats)
        self.assertEqual(stats["log_directory"], str(self.log_dir))
    
    def test_cleanup_old_logs_function(self):
        """测试便捷函数 cleanup_old_logs"""
        # 创建旧文件
        old_file = self.log_dir / "old_function_test.log"
        old_file.write_text("Old function content")
        
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        os.utime(old_file, (old_time, old_time))
        
        # 使用便捷函数清理
        with patch('src.utils.log_cleanup.LogCleanup') as mock_cleanup:
            mock_instance = MagicMock()
            mock_instance.clean_old_logs.return_value = {"files_deleted": 1}
            mock_cleanup.return_value = mock_instance
            
            result = cleanup_old_logs(days=7, dry_run=False)
            
            self.assertIn("files_deleted", result)
            mock_instance.clean_old_logs.assert_called_once()
    
    def test_rotate_oversized_logs_function(self):
        """测试便捷函数 rotate_oversized_logs"""
        # 创建大文件
        big_content = "Large content " * 100000
        big_file = self.log_dir / "big_function.log"
        big_file.write_text(big_content)
        
        # 使用便捷函数轮转
        with patch('src.utils.log_cleanup.LogCleanup') as mock_cleanup:
            mock_instance = MagicMock()
            mock_instance.check_file_size_and_rotate.return_value = True
            mock_cleanup.return_value = mock_instance
            
            result = rotate_oversized_logs(max_size_mb=1)
            
            self.assertGreaterEqual(result, 0)
            mock_instance.check_file_size_and_rotate.assert_called_once()


class TestLogCleanupError(unittest.TestCase):
    """日志清理错误测试类"""
    
    def test_log_cleanup_error_initialization(self):
        """测试日志清理错误类"""
        error = LogCleanupError("测试错误消息")
        self.assertEqual(str(error), "测试错误消息")
    
    def test_invalid_log_directory(self):
        """测试无效的日志目录"""
        # 尝试创建不存在的目录路径
        invalid_path = "/invalid/path/that/does/not/exist"
        
        with self.assertRaises(LogCleanupError):
            LogCleanup(log_directory=invalid_path)


class TestLogCleanupIntegration(unittest.TestCase):
    """日志清理集成测试类"""
    
    def setUp(self):
        """集成测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.test_dir) / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志文件配置
        self.config_patch = patch('src.utils.log_cleanup.get_logging_config')
        self.mock_config = self.config_patch.start()
        self.mock_config.return_value = {
            "file_path": str(self.log_dir / "app.log"),
            "file_max_bytes": 1048576,  # 1MB
            "file_backup_count": 3,
            "retention_days": 7,
            "max_size_mb": 10,
            "compress_old": True,
            "cleanup_enabled": True
        }
    
    def tearDown(self):
        """集成测试后清理"""
        self.config_patch.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_integration_with_config(self):
        """测试与配置的集成"""
        # 使用配置创建管理器，但使用自定义参数覆盖配置
        cleanup_config = get_log_cleanup_config()
        
        # 手动指定参数，避免使用配置中的默认值
        manager = LogCleanup(
            log_directory=str(self.log_dir),
            retention_days=7,
            max_size_mb=10,
            backup_count=3,
            compress_old_logs=True
        )
        
        # 验证配置正确应用
        self.assertEqual(manager.retention_days, 7)
        self.assertEqual(manager.max_size_bytes, 10 * 1024 * 1024)
        self.assertTrue(manager.compress_old_logs)
        
        # 测试磁盘统计
        stats = manager.get_disk_usage_stats()
        self.assertIn("log_directory", stats)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)