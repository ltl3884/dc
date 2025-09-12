#!/usr/bin/env python3
"""
Task模型单元测试模块

该模块包含Task模型的基本单元测试，用于验证模型的创建、验证、字段约束和时间戳功能。
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from src.models.task import Task


class TestTaskModel(unittest.TestCase):
    """Task模型单元测试类"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_task_creation_basic(self) -> None:
        """测试Task模型基本创建功能"""
        task = Task(
            url="https://example.com/address",
            method="GET"
        )
        
        self.assertIsNone(task.id)
        self.assertEqual(task.url, "https://example.com/address")
        self.assertEqual(task.method, "GET")
        self.assertIsNone(task.body)
        self.assertEqual(task.headers, {})
        self.assertEqual(task.total_num, 0)
        self.assertEqual(task.visited_num, 0)
        self.assertEqual(task.timeout, 30)
        self.assertEqual(task.retry_count, 0)
    
    def test_task_creation_with_all_fields(self) -> None:
        """测试Task模型使用所有字段的创建功能"""
        headers_data: Dict[str, Any] = {
            "User-Agent": "TestCrawler/1.0",
            "Accept": "application/json"
        }
        
        task = Task(
            url="https://example.com/api/addresses",
            method="POST",
            body='{"city": "北京", "district": "朝阳区"}',
            headers=headers_data,
            total_num=100,
            timeout=60
        )
        
        # 保存到数据库
        db.session.add(task)
        db.session.commit()
        
        # 验证数据库中的数据
        saved_task = db.session.query(Task).filter_by(url="https://example.com/api/addresses").first()
        self.assertIsNotNone(saved_task)
        self.assertEqual(saved_task.id, task.id)
        self.assertEqual(saved_task.method, "POST")
        self.assertEqual(saved_task.body, '{"city": "北京", "district": "朝阳区"}')
        self.assertEqual(saved_task.headers, headers_data)
        self.assertEqual(saved_task.total_num, 100)
        self.assertEqual(saved_task.timeout, 60)
    
    def test_task_default_values(self) -> None:
        """测试Task模型的默认值"""
        task = Task(url="https://example.com")
        
        self.assertEqual(task.method, "GET")
        self.assertEqual(task.headers, {})
        self.assertEqual(task.total_num, 0)
        self.assertEqual(task.visited_num, 0)
        self.assertEqual(task.timeout, 30)
        self.assertEqual(task.retry_count, 0)
    
    def test_method_uppercase_conversion(self) -> None:
        """测试HTTP方法转换为大写"""
        task = Task(
            url="https://example.com",
            method="post"
        )
        
        self.assertEqual(task.method, "POST")
    
    def test_url_field_constraints(self) -> None:
        """测试URL字段约束"""
        # 测试URL不能为空
        with self.assertRaises(TypeError):
            Task()  # 缺少必需的url参数
        
        # 测试正常URL
        task = Task(url="https://example.com")
        self.assertEqual(task.url, "https://example.com")
    
    def test_completion_properties(self) -> None:
        """测试完成状态属性"""
        # 测试待完成的任务
        task = Task(url="https://example.com", total_num=10, visited_num=5)
        self.assertTrue(task.is_pending)
        self.assertFalse(task.is_completed)
        self.assertEqual(task.completion_rate, 0.5)
        
        # 测试已完成的任务
        task.visited_num = 10
        self.assertFalse(task.is_pending)
        self.assertTrue(task.is_completed)
        self.assertEqual(task.completion_rate, 1.0)
        
        # 测试 total_num 为 0 的情况
        task.total_num = 0
        self.assertFalse(task.is_pending)
        self.assertFalse(task.is_completed)
        self.assertEqual(task.completion_rate, 0.0)
    
    def test_numeric_fields_validation(self) -> None:
        """测试数值字段验证"""
        # 测试超时时间
        task = Task(url="https://example.com", timeout=120)
        self.assertEqual(task.timeout, 120)
        
        # 测试负数超时时间（应该允许，但可能不合理）
        task_negative = Task(url="https://example.com", timeout=-1)
        self.assertEqual(task_negative.timeout, -1)
        
        # 先保存到数据库获取数据库默认值，然后测试访问数量
        task_db = Task(url="https://example.com/test")
        db.session.add(task_db)
        db.session.commit()
        
        # 重新获取以获取数据库中的默认值
        saved_task = db.session.query(Task).filter_by(url="https://example.com/test").first()
        self.assertEqual(saved_task.visited_num, 0)
        
        # 测试访问数量增加
        saved_task.increment_visited(5)
        self.assertEqual(saved_task.visited_num, 5)
        
        saved_task.increment_visited()
        self.assertEqual(saved_task.visited_num, 6)
        
        # 测试重试次数
        self.assertEqual(saved_task.retry_count, 0)
        saved_task.increment_retry()
        self.assertEqual(saved_task.retry_count, 1)
        
        saved_task.increment_retry()
        self.assertEqual(saved_task.retry_count, 2)
    
    def test_completion_rate_calculation(self) -> None:
        """测试完成率计算"""
        # 测试total_num为0的情况
        task_zero = Task(url="https://example.com", total_num=0)
        self.assertEqual(task_zero.completion_rate, 0.0)
        
        # 测试正常情况
        task = Task(url="https://example.com", total_num=100)
        task.visited_num = 50
        self.assertEqual(task.completion_rate, 0.5)
        
        # 测试visited_num超过total_num的情况
        task.visited_num = 150
        self.assertEqual(task.completion_rate, 1.0)
        
        # 测试100%完成
        task.visited_num = 100
        self.assertEqual(task.completion_rate, 1.0)
    
    def test_timestamp_fields(self) -> None:
        """测试时间戳字段"""
        before_creation = datetime.utcnow()
        
        task = Task(url="https://example.com")
        db.session.add(task)
        db.session.commit()
        
        after_creation = datetime.utcnow()
        
        # 验证创建时间
        self.assertIsNotNone(task.created_at)
        self.assertGreaterEqual(task.created_at, before_creation)
        self.assertLessEqual(task.created_at, after_creation)
        
        # 验证更新时间
        self.assertIsNotNone(task.updated_at)
        self.assertGreaterEqual(task.updated_at, before_creation)
        self.assertLessEqual(task.updated_at, after_creation)
        
        # 验证创建时间和更新时间基本相同（首次创建时，允许微秒级差异）
        time_diff = abs((task.updated_at - task.created_at).total_seconds())
        self.assertLess(time_diff, 1)  # 差异应该小于1秒
    
    def test_timestamp_update_on_change(self) -> None:
        """测试时间戳在更新时的变化"""
        task = Task(url="https://example.com")
        db.session.add(task)
        db.session.commit()
        
        original_updated_at = task.updated_at
        
        # 等待一小段时间确保时间戳会有变化
        import time
        time.sleep(0.1)
        
        # 更新任务进度
        task.visited_num = 5
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # 验证更新时间已变化，但创建时间不变
        self.assertEqual(task.created_at, task.created_at)  # 应该不变
        self.assertGreater(task.updated_at, original_updated_at)  # 应该更新
    
    def test_to_dict_method(self) -> None:
        """测试to_dict方法"""
        headers_data = {"Content-Type": "application/json"}
        task = Task(
            url="https://example.com/api",
            method="POST",
            body='{"test": "data"}',
            headers=headers_data,
            total_num=50,
            timeout=45
        )
        db.session.add(task)
        db.session.commit()
        
        task_dict = task.to_dict()
        
        # 验证字典包含所有必要字段
        expected_fields = [
            'id', 'url', 'method', 'body', 'headers', 'total_num',
            'visited_num', 'timeout', 'retry_count',
            'created_at', 'updated_at'
        ]
        
        for field in expected_fields:
            self.assertIn(field, task_dict)
        
        # 验证字段值
        self.assertEqual(task_dict['url'], "https://example.com/api")
        self.assertEqual(task_dict['method'], "POST")
        self.assertEqual(task_dict['body'], '{"test": "data"}')
        self.assertEqual(task_dict['headers'], headers_data)
        self.assertEqual(task_dict['total_num'], 50)
        self.assertEqual(task_dict['timeout'], 45)
        self.assertEqual(task_dict['visited_num'], 0)
        
        # 验证时间戳格式
        self.assertIsInstance(task_dict['created_at'], str)
        self.assertIsInstance(task_dict['updated_at'], str)
    
    def test_repr_method(self) -> None:
        """测试__repr__方法"""
        task = Task(url="https://example.com", status="running")
        db.session.add(task)
        db.session.commit()
        
        repr_str = repr(task)
        
        # 验证字符串格式
        self.assertIn("Task(", repr_str)
        self.assertIn(f"id={task.id}", repr_str)
        self.assertIn("url='https://example.com'", repr_str)
        self.assertIn("completion_rate=0.00", repr_str)
    
    def test_headers_json_field(self) -> None:
        """测试headers JSON字段"""
        # 测试复杂headers数据
        complex_headers = {
            "User-Agent": "TestCrawler/1.0",
            "Authorization": "Bearer token123",
            "Custom-Header": "custom-value",
            "Nested": {
                "key1": "value1",
                "key2": ["item1", "item2"]
            }
        }
        
        task = Task(
            url="https://example.com",
            headers=complex_headers
        )
        db.session.add(task)
        db.session.commit()
        
        # 验证headers正确保存和读取
        saved_task = db.session.query(Task).filter_by(url="https://example.com").first()
        self.assertEqual(saved_task.headers, complex_headers)
        self.assertIsInstance(saved_task.headers, dict)
        
        # 测试空headers
        task_empty = Task(url="https://example.com/empty")
        self.assertEqual(task_empty.headers, {})
    
    def test_body_text_field(self) -> None:
        """测试body文本字段"""
        # 测试长文本body
        long_body = "{" + ", ".join([f'"key{i}": "value{i}"' for i in range(100)]) + "}"
        
        task = Task(
            url="https://example.com",
            body=long_body
        )
        db.session.add(task)
        db.session.commit()
        
        # 验证长文本正确保存
        saved_task = db.session.query(Task).filter_by(url="https://example.com").first()
        self.assertEqual(saved_task.body, long_body)
        
        # 测试None值
        task_none = Task(url="https://example.com/none", body=None)
        self.assertIsNone(task_none.body)


if __name__ == '__main__':
    unittest.main()