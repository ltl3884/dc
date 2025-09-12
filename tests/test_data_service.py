#!/usr/bin/env python3
"""
DataService集成测试模块

该模块包含DataService的集成测试，用于验证地址数据持久化功能，
包括数据验证、重复检测、事务管理、批量保存等核心功能。
"""

import sys
import os
import unittest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from src.models.address_info import AddressInfo
from src.services.data_service import DataService


class TestDataService(unittest.TestCase):
    """DataService集成测试类"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.data_service = DataService()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_save_address_data_basic(self) -> None:
        """测试基本地址数据保存功能"""
        address_data: Dict[str, Any] = {
            'address': '123 Main St, New York, NY 10001',
            'telephone': '+1-555-123-4567',
            'city': 'New York',
            'zip_code': '10001',
            'state': 'NY',
            'state_full': 'New York',
            'country': 'USA',
            'source_url': 'https://example.com'
        }
        
        # 保存地址数据
        self.data_service.save_address_data(address_data)
        
        # 从数据库查询验证
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 1)
        
        saved_address = addresses[0]
        self.assertEqual(saved_address.address, address_data['address'])
        self.assertEqual(saved_address.telephone, address_data['telephone'])
        self.assertEqual(saved_address.city, address_data['city'])
        self.assertEqual(saved_address.zip_code, address_data['zip_code'])
        self.assertEqual(saved_address.state, address_data['state'])
        self.assertEqual(saved_address.state_full, address_data['state_full'])
        self.assertEqual(saved_address.country, address_data['country'])
        self.assertEqual(saved_address.source_url, address_data['source_url'])
        self.assertIsNotNone(saved_address.created_at)
        self.assertIsNotNone(saved_address.updated_at)
    
    def test_save_address_data_minimal(self) -> None:
        """测试保存最小地址数据"""
        address_data: Dict[str, Any] = {
            'address': '456 Oak Ave, Los Angeles, CA'
        }
        
        # 保存地址数据
        self.data_service.save_address_data(address_data)
        
        # 从数据库查询验证
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 1)
        
        saved_address = addresses[0]
        self.assertEqual(saved_address.address, address_data['address'])
        self.assertIsNone(saved_address.telephone)
        self.assertIsNone(saved_address.city)
        self.assertIsNone(saved_address.zip_code)
        self.assertIsNone(saved_address.state)
        self.assertIsNone(saved_address.state_full)
        self.assertIsNone(saved_address.country)
        self.assertIsNone(saved_address.source_url)
    
    def test_save_address_data_validation(self) -> None:
        """测试地址数据保存时的验证"""
        # 测试空地址
        with self.assertRaises(ValueError) as cm:
            self.data_service.save_address_data({'address': ''})
        self.assertIn("地址字段是必需的", str(cm.exception))
        
        # 测试缺失地址字段
        with self.assertRaises(ValueError) as cm:
            self.data_service.save_address_data({'city': 'Boston'})
        self.assertIn("地址字段是必需的", str(cm.exception))
        
        # 测试None地址
        with self.assertRaises(ValueError) as cm:
            self.data_service.save_address_data({'address': None})
        self.assertIn("地址字段是必需的", str(cm.exception))
        
        # 验证没有数据被保存
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 0)
    
    def test_duplicate_detection_and_handling(self) -> None:
        """测试重复数据检测和处理"""
        # 创建第一个地址
        address_data1: Dict[str, Any] = {
            'address': '789 Pine St, Chicago, IL 60601',
            'telephone': '+1-555-987-6543',
            'city': 'Chicago',
            'zip_code': '60601',
            'state': 'IL',
            'country': 'USA'
        }
        
        # 保存第一个地址
        self.data_service.save_address_data(address_data1)
        
        # 获取第一个地址的ID
        first_addresses = AddressInfo.query.all()
        self.assertEqual(len(first_addresses), 1)
        original_id = first_addresses[0].id
        
        # 尝试保存相同的地址（应该检测到重复）
        address_data2: Dict[str, Any] = {
            'address': '789 Pine St, Chicago, IL 60601',
            'telephone': '+1-555-987-6543',  # 相同数据
            'city': 'Chicago',
            'zip_code': '60601',
            'state': 'IL',
            'country': 'USA'
        }
        
        self.data_service.save_address_data(address_data2)
        
        # 验证仍然只有一个地址
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0].id, original_id)
        self.assertEqual(addresses[0].address, address_data1['address'])
    
    def test_duplicate_detection_with_better_data(self) -> None:
        """测试检测到重复数据但新数据更好的情况"""
        # 创建第一个地址（不完整）
        address_data1: Dict[str, Any] = {
            'address': '321 Elm St, Boston, MA 02108',
            'city': 'Boston',
            'state': 'MA'
            # 缺少 telephone, zip_code, country
        }
        
        # 保存第一个地址
        self.data_service.save_address_data(address_data1)
        
        # 获取第一个地址的ID
        first_addresses = AddressInfo.query.all()
        self.assertEqual(len(first_addresses), 1)
        original_id = first_addresses[0].id
        
        # 尝试保存更完整的相同地址
        address_data2: Dict[str, Any] = {
            'address': '321 Elm St, Boston, MA 02108',
            'telephone': '+1-555-321-7654',
            'city': 'Boston',
            'zip_code': '02108',
            'state': 'MA',
            'state_full': 'Massachusetts',
            'country': 'USA'
        }
        
        self.data_service.save_address_data(address_data2)
        
        # 验证仍然只有一个地址，但数据应该被更新
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 1)
        self.assertEqual(addresses[0].id, original_id)
        
        # 验证数据被更新
        self.assertEqual(addresses[0].telephone, address_data2['telephone'])
        self.assertEqual(addresses[0].zip_code, address_data2['zip_code'])
        self.assertEqual(addresses[0].state_full, address_data2['state_full'])
        self.assertEqual(addresses[0].country, address_data2['country'])
    
    def test_duplicate_detection_disabled(self) -> None:
        """测试禁用重复检测的情况"""
        # 创建第一个地址
        address_data1: Dict[str, Any] = {
            'address': '111 Oak St, Seattle, WA 98101',
            'telephone': '+1-555-111-2222',
            'city': 'Seattle',
            'zip_code': '98101',
            'state': 'WA',
            'country': 'USA'
        }
        
        # 保存第一个地址
        self.data_service.save_address_data(address_data1, handle_duplicates=False)
        
        # 尝试保存相同的地址，但不检测重复
        address_data2: Dict[str, Any] = {
            'address': '111 Oak St, Seattle, WA 98101',
            'telephone': '+1-555-333-4444',  # 不同的电话号码
            'city': 'Seattle',
            'zip_code': '98101',
            'state': 'WA',
            'country': 'USA'
        }
        
        self.data_service.save_address_data(address_data2, handle_duplicates=False)
        
        # 应该创建两个不同的记录
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 2)
        
        # 验证两个记录的地址相同但ID不同
        self.assertEqual(addresses[0].address, addresses[1].address)
        self.assertNotEqual(addresses[0].id, addresses[1].id)
        
        # 验证第二个记录的电话号码
        second_address = next(addr for addr in addresses if addr.telephone == '+1-555-333-4444')
        self.assertIsNotNone(second_address)
        self.assertEqual(second_address.address, address_data2['address'])
    
    def test_batch_save_address_data(self) -> None:
        """测试批量保存地址数据"""
        address_data_list: List[Dict[str, Any]] = [
            {
                'address': 'AAA Street, City1, ST 11111',
                'telephone': '+1-111-111-1111',
                'city': 'City1',
                'zip_code': '11111',
                'state': 'ST',
                'country': 'USA'
            },
            {
                'address': 'BBB Avenue, City2, ST 22222',
                'telephone': '+1-222-222-2222',
                'city': 'City2',
                'zip_code': '22222',
                'state': 'ST',
                'country': 'USA'
            },
            {
                'address': 'CCC Road, City3, ST 33333',
                'telephone': '+1-333-333-3333',
                'city': 'City3',
                'zip_code': '33333',
                'state': 'ST',
                'country': 'USA'
            }
        ]
        
        saved_addresses = self.data_service.batch_save_address_data(address_data_list)
        
        self.assertEqual(len(saved_addresses), 3)
        
        # 验证数据库中的记录
        db_addresses = AddressInfo.query.all()
        self.assertEqual(len(db_addresses), 3)
        
        for i, expected_data in enumerate(address_data_list):
            actual_address = db_addresses[i]
            self.assertEqual(actual_address.address, expected_data['address'])
            self.assertEqual(actual_address.city, expected_data['city'])
    
    def test_batch_save_address_data_with_duplicates(self) -> None:
        """测试批量保存时处理重复数据"""
        # 先创建一条记录（不完整的数据）
        existing_data: Dict[str, Any] = {
            'address': 'DDD Lane, City4, ST 44444',
            'city': 'City4',
            'zip_code': '44444',
            'state': 'ST'
            # 缺少 telephone 和 country
        }
        self.data_service.save_address_data(existing_data)
        
        # 获取现有记录的ID
        existing_addresses = AddressInfo.query.all()
        self.assertEqual(len(existing_addresses), 1)
        existing_id = existing_addresses[0].id
        
        # 批量保存，包含更好的重复数据
        batch_data: List[Dict[str, Any]] = [
            {
                'address': 'DDD Lane, City4, ST 44444',  # 重复地址
                'telephone': '+1-555-555-5555',  # 更新的电话号码
                'city': 'City4',
                'zip_code': '44444',
                'state': 'ST',
                'country': 'USA'  # 新增国家信息
            },
            {
                'address': 'EEE Street, City5, ST 55555',  # 新地址
                'telephone': '+1-666-666-6666',
                'city': 'City5',
                'zip_code': '55555',
                'state': 'ST',
                'country': 'USA'
            }
        ]
        
        saved_addresses = self.data_service.batch_save_address_data(batch_data)
        
        self.assertEqual(len(saved_addresses), 2)
        
        # 验证数据库中的记录
        db_addresses = AddressInfo.query.all()
        self.assertEqual(len(db_addresses), 2)
        
        # 找到更新后的现有记录（数据完整性得分更高，应该被更新）
        updated_existing = next(addr for addr in db_addresses if addr.id == existing_id)
        self.assertEqual(updated_existing.telephone, '+1-555-555-5555')  # 应该被更新
        self.assertEqual(updated_existing.country, 'USA')  # 应该被更新
        
        # 找到新记录
        new_address = next(addr for addr in db_addresses if addr.id != existing_id)
        self.assertEqual(new_address.address, 'EEE Street, City5, ST 55555')
    
    def test_batch_save_address_data_with_invalid_data(self) -> None:
        """测试批量保存时跳过无效数据"""
        batch_data: List[Dict[str, Any]] = [
            {
                'address': 'Valid Address, City, ST 12345',  # 有效数据
                'city': 'City',
                'state': 'ST'
            },
            {
                'city': 'Invalid Data'  # 缺少必需的address字段
            },
            {
                'address': 'Another Valid Address, City, ST 67890',  # 有效数据
                'telephone': '+1-777-777-7777',
                'city': 'City',
                'zip_code': '67890',
                'state': 'ST',
                'country': 'USA'
            }
        ]
        
        saved_addresses = self.data_service.batch_save_address_data(batch_data)
        
        # 应该只保存有效的数据（第1个和第3个）
        self.assertEqual(len(saved_addresses), 2)
        
        # 验证数据库中的记录
        db_addresses = AddressInfo.query.all()
        self.assertEqual(len(db_addresses), 2)
        
        # 找到第一个有效地址
        first_valid = next(addr for addr in db_addresses if 'Valid Address, City, ST 12345' in addr.address)
        self.assertIsNotNone(first_valid)
        
        # 找到第二个有效地址
        second_valid = next(addr for addr in db_addresses if 'Another Valid Address, City, ST 67890' in addr.address)
        self.assertIsNotNone(second_valid)
    
    def test_get_address_by_id(self) -> None:
        """测试根据ID获取地址信息"""
        # 创建地址
        address_data: Dict[str, Any] = {
            'address': '888 Maple St, Portland, OR 97201',
            'telephone': '+1-888-888-8888',
            'city': 'Portland',
            'zip_code': '97201',
            'state': 'OR',
            'state_full': 'Oregon',
            'country': 'USA'
        }
        
        self.data_service.save_address_data(address_data)
        
        # 获取保存的地址ID
        saved_addresses = AddressInfo.query.all()
        self.assertEqual(len(saved_addresses), 1)
        address_id = saved_addresses[0].id
        
        # 通过ID获取地址
        fetched_address = self.data_service.get_address_by_id(address_id)
        
        self.assertIsNotNone(fetched_address)
        self.assertEqual(fetched_address.id, address_id)
        self.assertEqual(fetched_address.address, address_data['address'])
        self.assertEqual(fetched_address.city, address_data['city'])
        self.assertEqual(fetched_address.state, address_data['state'])
        
        # 获取不存在的地址
        non_existent_address = self.data_service.get_address_by_id(9999)
        self.assertIsNone(non_existent_address)
    
    def test_search_addresses(self) -> None:
        """测试地址搜索功能"""
        # 创建测试地址
        test_addresses: List[Dict[str, Any]] = [
            {
                'address': '999 Main St, San Francisco, CA 94102',
                'telephone': '+1-999-999-9999',
                'city': 'San Francisco',
                'zip_code': '94102',
                'state': 'CA',
                'country': 'USA'
            },
            {
                'address': '111 Market St, San Francisco, CA 94103',
                'telephone': '+1-111-111-1111',
                'city': 'San Francisco',
                'zip_code': '94103',
                'state': 'CA',
                'country': 'USA'
            },
            {
                'address': '222 Broadway, Los Angeles, CA 90012',
                'telephone': '+1-222-222-2222',
                'city': 'Los Angeles',
                'zip_code': '90012',
                'state': 'CA',
                'country': 'USA'
            },
            {
                'address': '333 Fifth Ave, New York, NY 10016',
                'telephone': '+1-333-333-3333',
                'city': 'New York',
                'zip_code': '10016',
                'state': 'NY',
                'country': 'USA'
            }
        ]
        
        for address_data in test_addresses:
            self.data_service.save_address_data(address_data)
        
        # 按地址搜索
        results = self.data_service.search_addresses(address='Main St')
        self.assertEqual(len(results), 1)
        self.assertIn('Main St', results[0].address)
        
        # 按城市搜索
        results = self.data_service.search_addresses(city='San Francisco')
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result.city, 'San Francisco')
        
        # 按州搜索
        results = self.data_service.search_addresses(state='CA')
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.state, 'CA')
        
        # 按国家和城市搜索
        results = self.data_service.search_addresses(country='USA', city='Los Angeles')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].city, 'Los Angeles')
        self.assertEqual(results[0].country, 'USA')
        
        # 测试搜索限制
        results = self.data_service.search_addresses(country='USA', limit=2)
        self.assertEqual(len(results), 2)
    
    def test_database_rollback_on_error(self) -> None:
        """测试数据库错误时的回滚机制"""
        # 创建正常地址
        address_data: Dict[str, Any] = {
            'address': '444 Error St, Test City, TS 44444',
            'telephone': '+1-444-444-4444',
            'city': 'Test City',
            'zip_code': '44444',
            'state': 'TS',
            'country': 'USA'
        }
        
        # 模拟数据库错误
        with patch('src.app.db.session.commit') as mock_commit:
            mock_commit.side_effect = SQLAlchemyError("模拟数据库错误")
            
            with self.assertRaises(SQLAlchemyError):
                self.data_service.save_address_data(address_data)
            
            # 验证数据库回滚被调用
            with patch('src.app.db.session.rollback') as mock_rollback:
                try:
                    self.data_service.save_address_data(address_data)
                except SQLAlchemyError:
                    pass
                mock_rollback.assert_called_once()
        
        # 验证没有数据被保存
        addresses = AddressInfo.query.all()
        self.assertEqual(len(addresses), 0)
    
    def test_transaction_context_rollback(self) -> None:
        """测试事务上下文管理器的回滚功能"""
        # 创建第一个地址（应该成功）
        address_data1: Dict[str, Any] = {
            'address': '555 Success St, Good City, GC 55555',
            'city': 'Good City',
            'state': 'GC'
        }
        
        self.data_service.save_address_data(address_data1)
        
        # 验证第一个地址已保存
        first_addresses = AddressInfo.query.all()
        self.assertEqual(len(first_addresses), 1)
        saved_id = first_addresses[0].id
        
        # 尝试创建第二个地址，但模拟错误
        address_data2: Dict[str, Any] = {
            'address': '666 Fail St, Bad City, BC 66666',
            'city': 'Bad City',
            'state': 'BC'
        }
        
        # 在事务中模拟错误
        with patch.object(self.data_service, '_check_duplicate') as mock_check:
            mock_check.side_effect = Exception("模拟错误")
            
            with self.assertRaises(Exception):
                self.data_service.save_address_data(address_data2)
        
        # 验证第一个地址仍然存在，第二个没有创建
        all_addresses = AddressInfo.query.all()
        self.assertEqual(len(all_addresses), 1)
        self.assertEqual(all_addresses[0].id, saved_id)
    
    def test_data_persistence_after_save(self) -> None:
        """测试保存后的数据持久化"""
        # 创建地址
        address_data: Dict[str, Any] = {
            'address': '777 Persistent St, Data City, DC 77777',
            'telephone': '+1-777-777-7777',
            'city': 'Data City',
            'zip_code': '77777',
            'state': 'DC',
            'state_full': 'Data Columbia',
            'country': 'USA',
            'source_url': 'https://persistent-example.com'
        }
        
        self.data_service.save_address_data(address_data)
        
        # 获取保存的地址ID
        saved_addresses = AddressInfo.query.all()
        self.assertEqual(len(saved_addresses), 1)
        saved_id = saved_addresses[0].id
        
        # 关闭当前会话，重新获取
        db.session.close()
        db.session.begin()
        
        # 重新获取地址
        fetched_address = AddressInfo.query.get(saved_id)
        
        self.assertIsNotNone(fetched_address)
        self.assertEqual(fetched_address.address, address_data['address'])
        self.assertEqual(fetched_address.telephone, address_data['telephone'])
        self.assertEqual(fetched_address.city, address_data['city'])
        self.assertEqual(fetched_address.zip_code, address_data['zip_code'])
        self.assertEqual(fetched_address.state, address_data['state'])
        self.assertEqual(fetched_address.state_full, address_data['state_full'])
        self.assertEqual(fetched_address.country, address_data['country'])
        self.assertEqual(fetched_address.source_url, address_data['source_url'])


if __name__ == '__main__':
    unittest.main()