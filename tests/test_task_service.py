#!/usr/bin/env python3
"""
TaskService集成测试模块

该模块包含TaskService的集成测试，用于验证任务生命周期管理功能，
包括任务的创建、查询、状态更新等核心功能。
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from src.models.task import Task
from src.services.task_service import TaskService


class TestTaskService(unittest.TestCase):
    """TaskService集成测试类"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.task_service = TaskService()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_task_basic(self) -> None:
        """测试TaskService基本任务创建功能"""
        task = self.task_service.create_task(
            url="https://example.com/address",
            method="GET",
            total_num=10  # 设置总数量大于0，使任务可以处于待处理状态
        )
        
        self.assertIsNotNone(task.id)
        self.assertEqual(task.url, "https://example.com/address")
        self.assertEqual(task.method, "GET")
        self.assertIsNone(task.body)
        self.assertEqual(task.headers, {})
        self.assertEqual(task.total_num, 10)  # 我们设置了总数量为10
        self.assertEqual(task.visited_num, 0)
        self.assertEqual(task.timeout, 30)
        self.assertTrue(task.is_pending)  # 初始状态为待处理
        self.assertEqual(task.retry_count, 0)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
    
    def test_create_task_with_all_fields(self) -> None:
        """测试TaskService使用所有字段创建任务"""
        headers_data: Dict[str, Any] = {
            "User-Agent": "TestCrawler/1.0",
            "Accept": "application/json"
        }
        
        task = self.task_service.create_task(
            url="https://api.example.com/addresses",
            method="POST",
            body='{"city": "北京", "district": "朝阳区"}',
            headers=headers_data,
            total_num=100,
            timeout=60
        )
        
        self.assertEqual(task.url, "https://api.example.com/addresses")
        self.assertEqual(task.method, "POST")
        self.assertEqual(task.body, '{"city": "北京", "district": "朝阳区"}')
        self.assertEqual(task.headers, headers_data)
        self.assertEqual(task.total_num, 100)
        self.assertEqual(task.timeout, 60)
        self.assertTrue(task.is_pending)  # 初始状态为待处理
    
    def test_create_task_url_validation(self) -> None:
        """测试任务创建时的URL验证"""
        # 测试空URL
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="", method="GET")
        self.assertIn("URL不能为空", str(cm.exception))
        
        # 测试空白URL
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="   ", method="GET")
        self.assertIn("URL不能为空", str(cm.exception))
        
        # 测试无效URL格式
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="ftp://example.com", method="GET")
        self.assertIn("URL必须以http://或https://开头", str(cm.exception))
        
        # 测试过长的URL
        long_url = "https://example.com/" + "a" * 2048
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url=long_url, method="GET")
        self.assertIn("URL长度不能超过2048字符", str(cm.exception))
    
    def test_create_task_method_validation(self) -> None:
        """测试任务创建时的HTTP方法验证"""
        # 测试有效的HTTP方法
        valid_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]
        for method in valid_methods:
            task = self.task_service.create_task(
                url="https://example.com",
                method=method
            )
            self.assertEqual(task.method, method)
        
        # 测试无效方法
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="https://example.com", method="INVALID")
        self.assertIn("不支持的HTTP方法", str(cm.exception))
        
        # 测试方法转换为大写
        task = self.task_service.create_task(
            url="https://example.com",
            method="get"
        )
        self.assertEqual(task.method, "GET")
    
    def test_create_task_timeout_validation(self) -> None:
        """测试任务创建时的超时时间验证"""
        # 测试有效超时时间
        task = self.task_service.create_task(
            url="https://example.com",
            timeout=60
        )
        self.assertEqual(task.timeout, 60)
        
        # 测试过小的超时时间
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="https://example.com", timeout=0)
        self.assertIn("超时时间必须在1-300秒之间", str(cm.exception))
        
        # 测试过大的超时时间
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="https://example.com", timeout=301)
        self.assertIn("超时时间必须在1-300秒之间", str(cm.exception))
    
    def test_create_task_total_num_validation(self) -> None:
        """测试任务创建时的爬取数量验证"""
        # 测试有效爬取数量
        task = self.task_service.create_task(
            url="https://example.com",
            total_num=50
        )
        self.assertEqual(task.total_num, 50)
        
        # 测试负数爬取数量
        with self.assertRaises(ValueError) as cm:
            self.task_service.create_task(url="https://example.com", total_num=-1)
        self.assertIn("爬取数量不能为负数", str(cm.exception))
    
    def test_get_pending_task(self) -> None:
        """测试获取待处理任务功能"""
        # 创建多个待处理任务
        task1 = self.task_service.create_task("https://example1.com", "GET", total_num=10)
        task2 = self.task_service.create_task("https://example2.com", "POST", total_num=10)
        task3 = self.task_service.create_task("https://example3.com", "PUT", total_num=10)
        
        # 获取所有待处理任务（模拟批量处理）
        all_tasks = []
        while True:
            task = self.task_service.get_pending_task()
            if task is None:
                break
            all_tasks.append(task)
            # 模拟任务处理：完成任务（设置访问数量等于总数量）
            self.task_service.complete_task(task.id)
        
        # 验证获取到所有任务
        self.assertEqual(len(all_tasks), 3)
        task_ids = [task.id for task in all_tasks]
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertIn(task3.id, task_ids)
        
        # 验证所有任务都已完成
        for task in all_tasks:
            self.assertTrue(task.is_completed)
            self.assertEqual(task.visited_num, 10)  # 每个任务都应该完成
    
    def test_get_pending_task_with_mixed_status(self) -> None:
        """测试混合完成状态下获取待处理任务"""
        # 创建不同完成状态的任务
        pending_task = self.task_service.create_task("https://pending.com", "GET", total_num=10)  # 未完成
        running_task = self.task_service.create_task("https://running.com", "GET", total_num=10)  # 未完成
        completed_task = self.task_service.create_task("https://completed.com", "GET", total_num=10)  # 将完成
        failed_task = self.task_service.create_task("https://failed.com", "GET", total_num=10)  # 未完成
        
        # 完成一个任务
        completed_task = self.task_service.complete_task(completed_task.id)
        
        # 只应获取到未完成任务（pending_task, running_task, failed_task）
        fetched_task = self.task_service.get_pending_task()
        self.assertIsNotNone(fetched_task)
        self.assertIn(fetched_task.id, [pending_task.id, running_task.id, failed_task.id])
        self.assertTrue(fetched_task.is_pending)  # 应该是待完成状态
    
    def test_update_task_progress_basic(self) -> None:
        """测试基本任务进度更新功能"""
        task = self.task_service.create_task("https://example.com", "GET", total_num=10)
        
        # 更新已访问数量
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            visited_num=5
        )
        self.assertEqual(updated_task.visited_num, 5)
        self.assertEqual(updated_task.id, task.id)
        self.assertFalse(updated_task.is_completed)
        
        # 完成任务（设置访问数量等于总数量）
        updated_task = self.task_service.complete_task(task.id)
        self.assertEqual(updated_task.visited_num, 10)
        self.assertTrue(updated_task.is_completed)
        
        # 重置任务（将访问数量重置为0）
        updated_task = self.task_service.reset_task(task.id)
        self.assertEqual(updated_task.visited_num, 0)
        self.assertFalse(updated_task.is_completed)
    
    def test_update_task_progress_with_visited_num(self) -> None:
        """测试更新任务进度时设置已访问数量"""
        task = self.task_service.create_task("https://example.com", "GET", total_num=100)
        
        # 直接设置已访问数量
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            visited_num=50
        )
        self.assertEqual(updated_task.visited_num, 50)
        self.assertFalse(updated_task.is_completed)
        
        # 完成任务（设置访问数量等于总数量）
        updated_task = self.task_service.complete_task(task.id, visited_num=100)
        self.assertEqual(updated_task.visited_num, 100)
        self.assertTrue(updated_task.is_completed)
        
        # 负数的已访问数量应该报错
        with self.assertRaises(ValueError) as cm:
            self.task_service.update_task_progress(
                task_id=task.id,
                visited_num=-1
            )
        self.assertIn("已访问数量不能为负数", str(cm.exception))
    
    def test_update_task_progress_with_increment_visited(self) -> None:
        """测试更新任务进度时增加已访问数量"""
        task = self.task_service.create_task("https://example.com", "GET", total_num=20)
        
        # 增加已访问数量
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            increment_visited=10
        )
        self.assertEqual(updated_task.visited_num, 10)
        self.assertFalse(updated_task.is_completed)
        
        # 再次增加
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            increment_visited=5
        )
        self.assertEqual(updated_task.visited_num, 15)
        self.assertFalse(updated_task.is_completed)
        
        # 完成任务
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            increment_visited=5
        )
        self.assertEqual(updated_task.visited_num, 20)
        self.assertTrue(updated_task.is_completed)
    
    def test_update_task_progress_with_increment_retry(self) -> None:
        """测试更新任务进度时增加重试次数"""
        task = self.task_service.create_task("https://example.com", "GET")
        
        # 增加重试次数
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            increment_retry=True
        )
        self.assertEqual(updated_task.retry_count, 1)
        
        # 再次增加重试次数
        updated_task = self.task_service.update_task_progress(
            task_id=task.id,
            increment_retry=True
        )
        self.assertEqual(updated_task.retry_count, 2)
    
    def test_update_task_progress_validation(self) -> None:
        """测试任务进度更新的参数验证"""
        task = self.task_service.create_task("https://example.com", "GET")
        
        # 测试无效的任务ID
        with self.assertRaises(ValueError) as cm:
            self.task_service.update_task_progress(task_id=0)
        self.assertIn("任务ID必须为正整数", str(cm.exception))
        
        with self.assertRaises(ValueError) as cm:
            self.task_service.update_task_progress(task_id=-1)
        self.assertIn("任务ID必须为正整数", str(cm.exception))
        
        # 测试不存在的任务
        with self.assertRaises(ValueError) as cm:
            self.task_service.update_task_progress(task_id=9999)
        self.assertIn("任务不存在", str(cm.exception))
        
        # 测试负数的已访问数量
        with self.assertRaises(ValueError) as cm:
            self.task_service.update_task_progress(task_id=task.id, visited_num=-1)
        self.assertIn("已访问数量不能为负数", str(cm.exception))
    
    def test_get_task_by_id(self) -> None:
        """测试根据ID获取任务功能"""
        # 创建任务
        original_task = self.task_service.create_task("https://example.com", "GET")
        
        # 通过ID获取任务
        fetched_task = self.task_service.get_task_by_id(original_task.id)
        self.assertIsNotNone(fetched_task)
        self.assertEqual(fetched_task.id, original_task.id)
        self.assertEqual(fetched_task.url, original_task.url)
        self.assertEqual(fetched_task.method, original_task.method)
        
        # 获取不存在的任务
        non_existent_task = self.task_service.get_task_by_id(9999)
        self.assertIsNone(non_existent_task)
    
    def test_get_incomplete_and_completed_tasks(self) -> None:
        """测试获取未完成和已完成任务列表功能"""
        # 创建不同完成状态的任务
        incomplete_tasks = []
        for i in range(3):
            task = self.task_service.create_task(f"https://incomplete{i}.com", "GET", total_num=10, visited_num=5)
            incomplete_tasks.append(task)
        
        completed_tasks = []
        for i in range(2):
            task = self.task_service.create_task(f"https://completed{i}.com", "GET", total_num=10)
            self.task_service.complete_task(task.id)
            completed_tasks.append(task)
        
        # 测试获取未完成任务
        fetched_incomplete = self.task_service.get_incomplete_tasks()
        self.assertEqual(len(fetched_incomplete), 3)
        
        # 测试获取已完成任务
        fetched_completed = self.task_service.get_completed_tasks()
        self.assertEqual(len(fetched_completed), 2)
        
        # 验证获取到的任务确实属于对应完成状态
        for task in fetched_incomplete:
            self.assertTrue(task.is_pending)
            self.assertFalse(task.is_completed)
        for task in fetched_completed:
            self.assertFalse(task.is_pending)
            self.assertTrue(task.is_completed)
    
    # 移除 get_tasks_by_status_validation 测试，因为该方法已被移除
    
    def test_get_incomplete_tasks(self) -> None:
        """测试获取未完成任务功能"""
        # 创建未完成任务
        task1 = self.task_service.create_task("https://incomplete1.com", "GET", total_num=10, visited_num=5)
        task2 = self.task_service.create_task("https://incomplete2.com", "GET", total_num=10, visited_num=3)
        task3 = self.task_service.create_task("https://incomplete3.com", "GET", total_num=10, visited_num=8)
        
        # 创建已完成任务
        completed_task1 = self.task_service.create_task("https://completed1.com", "GET", total_num=10)
        self.task_service.complete_task(completed_task1.id)
        
        # 创建 total_num 为 0 的任务（视为未完成）
        zero_task = self.task_service.create_task("https://zero.com", "GET", total_num=0)
        
        # 获取未完成任务
        incomplete_tasks = self.task_service.get_incomplete_tasks()
        self.assertEqual(len(incomplete_tasks), 4)  # 3个部分完成 + 1个零总数
        for task in incomplete_tasks:
            if task.total_num > 0:
                self.assertTrue(task.is_pending)
                self.assertFalse(task.is_completed)
    
    def test_get_pending_tasks(self) -> None:
        """测试获取待处理任务功能（别名方法）"""
        # 创建未完成任务
        task1 = self.task_service.create_task("https://pending1.com", "GET", total_num=10, visited_num=5)
        task2 = self.task_service.create_task("https://pending2.com", "GET", total_num=10, visited_num=3)
        task3 = self.task_service.create_task("https://pending3.com", "GET", total_num=10, visited_num=8)
        
        # 创建已完成任务
        completed_task = self.task_service.create_task("https://completed.com", "GET", total_num=10)
        self.task_service.complete_task(completed_task.id)
        
        # 获取待处理任务（别名方法）
        pending_tasks = self.task_service.get_pending_tasks()
        self.assertEqual(len(pending_tasks), 3)
        for task in pending_tasks:
            self.assertTrue(task.is_pending)
            self.assertFalse(task.is_completed)
    
    def test_complete_task(self) -> None:
        """测试完成任务功能"""
        task = self.task_service.create_task("https://example.com", "GET", total_num=10)
        
        # 完成任务
        completed_task = self.task_service.complete_task(task.id)
        self.assertEqual(completed_task.visited_num, 10)
        self.assertTrue(completed_task.is_completed)
        self.assertEqual(completed_task.id, task.id)
        
        # 完成任务并设置已访问数量
        task2 = self.task_service.create_task("https://example2.com", "GET", total_num=50)
        completed_task2 = self.task_service.complete_task(task2.id, visited_num=100)
        self.assertEqual(completed_task2.visited_num, 100)
        self.assertTrue(completed_task2.is_completed)
    
    def test_fail_task(self) -> None:
        """测试标记任务失败功能（增加重试次数）"""
        task = self.task_service.create_task("https://example.com", "GET")
        
        # 标记任务失败（默认增加重试次数）
        failed_task = self.task_service.fail_task(task.id)
        self.assertEqual(failed_task.retry_count, 1)
        self.assertFalse(failed_task.is_completed)
        
        # 标记任务失败但不增加重试次数
        task2 = self.task_service.create_task("https://example2.com", "GET")
        failed_task2 = self.task_service.fail_task(task2.id, increment_retry=False)
        self.assertEqual(failed_task2.retry_count, 0)
        self.assertFalse(failed_task2.is_completed)
    
    def test_reset_task(self) -> None:
        """测试重置任务功能"""
        task = self.task_service.create_task("https://example.com", "GET", total_num=10, visited_num=5)
        
        # 先将任务增加重试次数
        self.task_service.fail_task(task.id)
        task = self.task_service.get_task_by_id(task.id)
        self.assertEqual(task.retry_count, 1)
        self.assertEqual(task.visited_num, 5)
        
        # 重置任务进度（将访问数量重置为0）
        reset_task = self.task_service.reset_task(task.id)
        self.assertEqual(reset_task.visited_num, 0)
        self.assertEqual(reset_task.retry_count, 0)
        self.assertFalse(reset_task.is_completed)
        self.assertEqual(reset_task.id, task.id)
    
    def test_database_rollback_on_error(self) -> None:
        """测试数据库错误时的回滚机制"""
        # 创建一个正常任务
        task = self.task_service.create_task("https://example.com", "GET")
        
        # 模拟数据库错误
        with patch('src.app.db.session.commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("模拟数据库错误")
            
            with self.assertRaises(SQLAlchemyError):
                self.task_service.update_task_progress(task.id)
            
            # 验证数据库回滚被调用
            with patch('src.app.db.session.rollback') as mock_rollback:
                try:
                    self.task_service.update_task_progress(task.id)
                except SQLAlchemyError:
                    pass
                mock_rollback.assert_called_once()
    
    def test_task_creation_with_database_persistence(self) -> None:
        """测试任务创建后的数据库持久化"""
        # 创建任务
        task = self.task_service.create_task(
            url="https://persistent.com",
            method="POST",
            body='{"test": "data"}',
            headers={"Content-Type": "application/json"},
            total_num=200,
            timeout=45
        )
        
        # 重新获取数据库会话，验证任务确实被保存
        db.session.close()
        db.session.begin()
        
        saved_task = Task.query.get(task.id)
        self.assertIsNotNone(saved_task)
        self.assertEqual(saved_task.url, "https://persistent.com")
        self.assertEqual(saved_task.method, "POST")
        self.assertEqual(saved_task.body, '{"test": "data"}')
        self.assertEqual(saved_task.headers, {"Content-Type": "application/json"})
        self.assertEqual(saved_task.total_num, 200)
        self.assertEqual(saved_task.timeout, 45)


if __name__ == '__main__':
    unittest.main()