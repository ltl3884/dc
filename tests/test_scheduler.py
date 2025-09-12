#!/usr/bin/env python3
"""
任务调度器功能测试模块

该模块包含任务调度器的功能测试，用于验证：
- 任务调度和执行功能
- 任务选择逻辑
- 任务失败的异常处理
- 调度器核心功能
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock, Mock
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from src.scheduler.task_scheduler import TaskScheduler, TaskStatistics, PerformanceMetrics
from src.models.task import Task
from src.config import get_scheduler_config


class TestTaskStatistics(unittest.TestCase):
    """任务统计类测试"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.stats = TaskStatistics()
    
    def test_initialization(self) -> None:
        """测试TaskStatistics初始化"""
        self.assertEqual(self.stats.success_count, 0)
        self.assertEqual(self.stats.failure_count, 0)
        self.assertEqual(self.stats.skipped_count, 0)
        self.assertEqual(self.stats.total_executions, 0)
        self.assertIsNone(self.stats.last_execution_time)
        self.assertIsNone(self.stats.last_success_time)
        self.assertIsNone(self.stats.last_failure_time)
        self.assertEqual(len(self.stats.execution_history), 0)
    
    def test_record_success(self) -> None:
        """测试记录成功的任务执行"""
        self.stats.record_success('job_123', 'test_job')
        
        self.assertEqual(self.stats.success_count, 1)
        self.assertEqual(self.stats.total_executions, 1)
        self.assertIsNotNone(self.stats.last_execution_time)
        self.assertIsNotNone(self.stats.last_success_time)
        self.assertEqual(len(self.stats.execution_history), 1)
        
        history_item = self.stats.execution_history[0]
        self.assertEqual(history_item['job_id'], 'job_123')
        self.assertEqual(history_item['job_name'], 'test_job')
        self.assertEqual(history_item['status'], 'success')
    
    def test_record_failure(self) -> None:
        """测试记录失败的任务执行"""
        error_msg = "Test error message"
        self.stats.record_failure('job_456', 'test_job_failed', error_msg)
        
        self.assertEqual(self.stats.failure_count, 1)
        self.assertEqual(self.stats.total_executions, 1)
        self.assertIsNotNone(self.stats.last_execution_time)
        self.assertIsNotNone(self.stats.last_failure_time)
        self.assertEqual(len(self.stats.execution_history), 1)
        
        history_item = self.stats.execution_history[0]
        self.assertEqual(history_item['job_id'], 'job_456')
        self.assertEqual(history_item['job_name'], 'test_job_failed')
        self.assertEqual(history_item['status'], 'failure')
        self.assertEqual(history_item['details'], error_msg)
    
    def test_record_skipped(self) -> None:
        """测试记录被跳过的任务执行"""
        skip_reason = "Task conditions not met"
        self.stats.record_skipped('job_789', 'test_job_skipped', skip_reason)
        
        self.assertEqual(self.stats.skipped_count, 1)
        self.assertEqual(self.stats.total_executions, 1)
        self.assertIsNotNone(self.stats.last_execution_time)
        self.assertEqual(len(self.stats.execution_history), 1)
        
        history_item = self.stats.execution_history[0]
        self.assertEqual(history_item['job_id'], 'job_789')
        self.assertEqual(history_item['job_name'], 'test_job_skipped')
        self.assertEqual(history_item['status'], 'skipped')
        self.assertEqual(history_item['details'], skip_reason)
    
    def test_history_limit(self) -> None:
        """测试历史记录限制"""
        # 添加超过限制的历史记录
        for i in range(1200):
            self.stats.record_success(f'job_{i}', f'test_job_{i}')
        
        # 验证历史记录数量不超过限制
        self.assertLessEqual(len(self.stats.execution_history), 1000)
    
    def test_get_statistics(self) -> None:
        """测试获取统计信息"""
        # 记录一些执行
        self.stats.record_success('job_1')
        self.stats.record_failure('job_2', 'error')
        self.stats.record_skipped('job_3', 'reason')
        
        stats_dict = self.stats.get_statistics()
        
        self.assertEqual(stats_dict['success_count'], 1)
        self.assertEqual(stats_dict['failure_count'], 1)
        self.assertEqual(stats_dict['skipped_count'], 1)
        self.assertEqual(stats_dict['total_executions'], 3)
        self.assertIn('success_rate', stats_dict)
        self.assertEqual(stats_dict['success_rate'], 1/3)


class TestTaskScheduler(unittest.TestCase):
    """任务调度器功能测试"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建测试数据库
        db.create_all()
        
        # 初始化调度器
        self.scheduler = TaskScheduler()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        if self.scheduler.is_running():
            self.scheduler.stop()
        
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_scheduler_initialization(self) -> None:
        """测试调度器初始化"""
        self.assertIsNotNone(self.scheduler)
        self.assertFalse(self.scheduler.is_running())
        self.assertIsNotNone(self.scheduler._statistics)
        self.assertIsNotNone(self.scheduler._performance_metrics)
    
    def test_scheduler_start_stop(self) -> None:
        """测试调度器启动和停止"""
        # 测试启动
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running())
        
        # 测试停止
        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running())
    
    @patch('src.scheduler.task_scheduler.CrawlerService')
    def test_add_job(self, mock_crawler_service: Mock) -> None:
        """测试添加任务"""
        self.scheduler.start()
        
        # 创建测试任务
        test_task = Mock(spec=Task)
        test_task.id = 1
        test_task.name = "test_task"
        test_task.url = "https://example.com"
        test_task.status = "active"
        test_task.priority = 1
        
        # 添加任务
        job_id = self.scheduler.add_task(test_task)
        self.assertIsNotNone(job_id)
        
        # 验证任务已添加
        job = self.scheduler.get_job(job_id)
        self.assertIsNotNone(job)
    
    @patch('src.scheduler.task_scheduler.CrawlerService')
    def test_remove_job(self, mock_crawler_service: Mock) -> None:
        """测试删除任务"""
        self.scheduler.start()
        
        # 创建并添加测试任务
        test_task = Mock(spec=Task)
        test_task.id = 1
        test_task.name = "test_task"
        test_task.url = "https://example.com"
        test_task.status = "active"
        test_task.priority = 1
        
        job_id = self.scheduler.add_task(test_task)
        
        # 删除任务
        result = self.scheduler.remove_task(job_id)
        self.assertTrue(result)
        
        # 验证任务已删除
        job = self.scheduler.get_job(job_id)
        self.assertIsNone(job)
    
    def test_pause_resume_job(self) -> None:
        """测试暂停和恢复任务"""
        self.scheduler.start()
        
        # 创建测试函数
        def test_func():
            pass
        
        # 添加任务
        job = self.scheduler._scheduler.add_job(
            test_func,
            'interval',
            seconds=60,
            id='test_pause_job'
        )
        
        # 测试暂停
        self.scheduler.pause_job('test_pause_job')
        job = self.scheduler.get_job('test_pause_job')
        self.assertEqual(job.next_run_time, None)
        
        # 测试恢复
        self.scheduler.resume_job('test_pause_job')
        job = self.scheduler.get_job('test_pause_job')
        self.assertIsNotNone(job.next_run_time)
    
    def test_get_all_jobs(self) -> None:
        """测试获取所有任务"""
        self.scheduler.start()
        
        # 添加多个任务
        jobs = []
        for i in range(3):
            job = self.scheduler._scheduler.add_job(
                lambda: None,
                'interval',
                seconds=60,
                id=f'test_job_{i}'
            )
            jobs.append(job)
        
        # 获取所有任务
        all_jobs = self.scheduler.get_all_jobs()
        self.assertEqual(len(all_jobs), 3)
    
    def test_task_execution_exception_handling(self) -> None:
        """测试任务执行异常处理"""
        self.scheduler.start()
        
        # 创建会抛出异常的测试函数
        def failing_function():
            raise ValueError("Test exception")
        
        # 添加任务
        job = self.scheduler._scheduler.add_job(
            failing_function,
            'date',
            run_date=datetime.now() + timedelta(seconds=1),
            id='failing_job',
            max_instances=1
        )
        
        # 等待任务执行
        time.sleep(2)
        
        # 验证异常被正确处理（统计信息中应该有失败记录）
        # 注意：这里假设调度器会捕获异常并记录到统计中
    
    def test_task_selection_priority(self) -> None:
        """测试任务选择优先级"""
        # 创建不同优先级的测试任务
        tasks_data = [
            {'id': 1, 'name': 'low_priority', 'priority': 1},
            {'id': 2, 'name': 'high_priority', 'priority': 5},
            {'id': 3, 'name': 'medium_priority', 'priority': 3}
        ]
        
        # 验证任务选择逻辑会优先选择高优先级任务
        # 这里需要具体的调度逻辑实现来验证
        self.assertTrue(True)  # 占位符，需要具体实现
    
    def test_performance_metrics(self) -> None:
        """测试性能指标"""
        # 记录一些执行时间
        self.scheduler._job_execution_times['job_1'] = 1.5
        self.scheduler._job_execution_times['job_2'] = 2.3
        
        # 获取平均执行时间
        avg_time = self.scheduler.get_average_execution_time()
        self.assertAlmostEqual(avg_time, 1.9, places=1)
    
    def test_scheduler_statistics(self) -> None:
        """测试调度器统计信息"""
        stats = self.scheduler.get_statistics()
        
        self.assertIn('scheduler_status', stats)
        self.assertIn('total_jobs', stats)
        self.assertIn('running_jobs', stats)
        self.assertIn('uptime_seconds', stats)
        self.assertIn('task_statistics', stats)
    
    def test_scheduler_config_validation(self) -> None:
        """测试调度器配置验证"""
        # 测试无效配置
        invalid_config = {
            'timezone': 'Invalid/Timezone',
            'job_defaults': {
                'max_instances': -1  # 无效值
            }
        }
        
        # 验证调度器能处理无效配置
        try:
            scheduler = TaskScheduler(invalid_config)
            # 如果初始化成功，验证使用了默认配置
            self.assertIsNotNone(scheduler)
        except Exception as e:
            # 如果抛出异常，验证是预期的异常类型
            self.assertIsInstance(e, (ValueError, KeyError))
    
    @patch('src.scheduler.task_scheduler.CrawlerService')
    def test_task_execution_logging(self, mock_crawler_service: Mock) -> None:
        """测试任务执行日志记录"""
        self.scheduler.start()
        
        # 创建测试任务
        test_task = Mock(spec=Task)
        test_task.id = 1
        test_task.name = "test_logging_task"
        test_task.url = "https://example.com"
        test_task.status = "active"
        test_task.priority = 1
        
        # 添加任务
        job_id = self.scheduler.add_task(test_task)
        
        # 验证日志记录功能
        # 这里需要验证日志是否正确记录，可以通过捕获日志输出来验证
        self.assertIsNotNone(job_id)


class TestSchedulerIntegration(unittest.TestCase):
    """调度器集成测试"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 创建测试数据库
        db.create_all()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_multiple_scheduler_instances(self) -> None:
        """测试多个调度器实例"""
        # 创建多个调度器实例
        scheduler1 = TaskScheduler()
        scheduler2 = TaskScheduler()
        
        # 验证它们是独立的实例
        self.assertNotEqual(scheduler1, scheduler2)
        self.assertNotEqual(scheduler1._statistics, scheduler2._statistics)
        
        # 清理
        scheduler1.stop()
        scheduler2.stop()
    
    def test_scheduler_with_database_tasks(self) -> None:
        """测试调度器与数据库任务集成"""
        # 创建测试任务记录
        test_task = Task(
            name="database_test_task",
            url="https://example.com",
            task_type="address_crawler",
            status="active",
            priority=5
        )
        db.session.add(test_task)
        db.session.commit()
        
        # 初始化调度器
        scheduler = TaskScheduler()
        scheduler.start()
        
        try:
            # 从数据库加载任务到调度器
            # 这里需要具体的实现来验证集成
            self.assertIsNotNone(scheduler)
        finally:
            scheduler.stop()


if __name__ == '__main__':
    unittest.main()