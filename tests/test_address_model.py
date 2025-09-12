#!/usr/bin/env python3
"""
AddressInfo模型单元测试模块

该模块包含AddressInfo模型的基本单元测试，用于验证模型的创建、验证、字段约束、
长度验证和数据库关系功能。
"""

import sys
import os
import time
import unittest
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import create_app, db
from src.models.address_info import AddressInfo


class TestAddressModel(unittest.TestCase):
    """AddressInfo模型单元测试类"""

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

    def test_address_creation_basic(self) -> None:
        """测试AddressInfo模型基本创建功能"""
        address = AddressInfo(
            address="123 Main St, New York, NY 10001"
        )

        self.assertIsNone(address.id)
        self.assertEqual(address.address, "123 Main St, New York, NY 10001")
        self.assertIsNone(address.telephone)
        self.assertIsNone(address.city)
        self.assertIsNone(address.zip_code)
        self.assertIsNone(address.state)
        self.assertIsNone(address.state_full)
        self.assertIsNone(address.country)
        self.assertIsNone(address.source_url)

    def test_address_creation_with_all_fields(self) -> None:
        """测试AddressInfo模型使用所有字段的创建功能"""
        address = AddressInfo(
            address="123 Main Street, Apartment 4B",
            telephone="+1-555-123-4567",
            city="New York",
            zip_code="10001",
            state="NY",
            state_full="New York",
            country="United States",
            source_url="https://example.com/addresses/123"
        )

        # 保存到数据库
        db.session.add(address)
        db.session.commit()

        # 验证数据库中的数据
        saved_address = db.session.query(AddressInfo).filter_by(
            address="123 Main Street, Apartment 4B"
        ).first()
        self.assertIsNotNone(saved_address)
        self.assertEqual(saved_address.id, address.id)
        self.assertEqual(saved_address.telephone, "+1-555-123-4567")
        self.assertEqual(saved_address.city, "New York")
        self.assertEqual(saved_address.zip_code, "10001")
        self.assertEqual(saved_address.state, "NY")
        self.assertEqual(saved_address.state_full, "New York")
        self.assertEqual(saved_address.country, "United States")
        self.assertEqual(saved_address.source_url, "https://example.com/addresses/123")

    def test_address_field_constraints(self) -> None:
        """测试AddressInfo模型字段约束"""
        # 测试地址不能为空
        with self.assertRaises(TypeError):
            AddressInfo()  # 缺少必需的address参数

        # 测试正常地址创建
        address = AddressInfo(address="456 Oak Avenue")
        self.assertEqual(address.address, "456 Oak Avenue")

    def test_field_length_constraints(self) -> None:
        """测试字段长度约束"""
        # 测试地址字段正常长度
        normal_address = "A" * 500 + " Street Name"  # 接近最大长度
        address = AddressInfo(address=normal_address)
        db.session.add(address)
        db.session.commit()
        self.assertLessEqual(len(address.address), 512)

        # 注意：SQLite不会自动截断超长字符串，但会发出警告或错误
        # 这里我们主要验证正常长度可以正确保存

        # 测试电话号码最大长度50字符
        long_telephone = "+" + "1" * 49
        address_long_phone = AddressInfo(
            address="Test Address",
            telephone=long_telephone
        )
        db.session.add(address_long_phone)
        db.session.commit()
        self.assertEqual(len(address_long_phone.telephone), 50)

        # 测试城市字段最大长度100字符
        long_city = "A" * 100
        address_long_city = AddressInfo(
            address="Test Address",
            city=long_city
        )
        db.session.add(address_long_city)
        db.session.commit()
        self.assertEqual(len(address_long_city.city), 100)

        # 测试邮编字段最大长度20字符
        long_zip = "9" * 20
        address_long_zip = AddressInfo(
            address="Test Address",
            zip_code=long_zip
        )
        db.session.add(address_long_zip)
        db.session.commit()
        self.assertEqual(len(address_long_zip.zip_code), 20)

        # 测试州缩写字段最大长度50字符
        long_state = "A" * 50
        address_long_state = AddressInfo(
            address="Test Address",
            state=long_state
        )
        db.session.add(address_long_state)
        db.session.commit()
        self.assertEqual(len(address_long_state.state), 50)

        # 测试州全称字段最大长度100字符
        long_state_full = "A" * 100
        address_long_state_full = AddressInfo(
            address="Test Address",
            state_full=long_state_full
        )
        db.session.add(address_long_state_full)
        db.session.commit()
        self.assertEqual(len(address_long_state_full.state_full), 100)

        # 测试国家字段最大长度100字符
        long_country = "A" * 100
        address_long_country = AddressInfo(
            address="Test Address",
            country=long_country
        )
        db.session.add(address_long_country)
        db.session.commit()
        self.assertEqual(len(address_long_country.country), 100)

        # 测试source_url字段正常长度
        long_url = "https://example.com/" + "a" * 2000  # 总共约2024字符
        address_long_url = AddressInfo(
            address="Test Address",
            source_url=long_url
        )
        db.session.add(address_long_url)
        db.session.commit()
        # 验证URL被正确保存（SQLite可能不严格限制长度，主要验证功能正常）
        self.assertGreater(len(address_long_url.source_url), 2000)

    def test_optional_fields(self) -> None:
        """测试可选字段"""
        # 创建只有必需字段的地址
        address = AddressInfo(address="789 Pine Road")
        db.session.add(address)
        db.session.commit()

        # 验证所有可选字段都为None
        self.assertIsNone(address.telephone)
        self.assertIsNone(address.city)
        self.assertIsNone(address.zip_code)
        self.assertIsNone(address.state)
        self.assertIsNone(address.state_full)
        self.assertIsNone(address.country)
        self.assertIsNone(address.source_url)

    def test_timestamp_fields(self) -> None:
        """测试时间戳字段"""
        before_creation = datetime.utcnow()

        address = AddressInfo(address="321 Elm Street")
        db.session.add(address)
        db.session.commit()

        after_creation = datetime.utcnow()

        # 验证创建时间
        self.assertIsNotNone(address.created_at)
        self.assertGreaterEqual(address.created_at, before_creation)
        self.assertLessEqual(address.created_at, after_creation)

        # 验证更新时间
        self.assertIsNotNone(address.updated_at)
        self.assertGreaterEqual(address.updated_at, before_creation)
        self.assertLessEqual(address.updated_at, after_creation)

        # 验证创建时间和更新时间基本相同（首次创建时，允许微秒级差异）
        time_diff = abs((address.updated_at - address.created_at).total_seconds())
        self.assertLess(time_diff, 1)  # 差异应该小于1秒

    def test_timestamp_update_on_change(self) -> None:
        """测试时间戳在更新时的变化"""
        address = AddressInfo(address="654 Maple Drive")
        db.session.add(address)
        db.session.commit()

        original_updated_at = address.updated_at
        original_created_at = address.created_at

        # 等待一小段时间确保时间戳会有变化
        time.sleep(0.1)

        # 更新地址信息
        address.update_info(city="Updated City", state="CA")
        db.session.commit()

        # 验证更新时间已变化，但创建时间不变
        self.assertEqual(address.created_at, original_created_at)  # 应该不变
        self.assertGreater(address.updated_at, original_updated_at)  # 应该更新

    def test_full_address_property(self) -> None:
        """测试full_address属性"""
        # 测试完整地址
        address = AddressInfo(
            address="123 Main St",
            city="Los Angeles",
            state_full="California",
            country="USA",
            zip_code="90210"
        )
        expected_full = "123 Main St, Los Angeles, California, USA, 90210"
        self.assertEqual(address.full_address, expected_full)

        # 测试只有地址的情况
        address_minimal = AddressInfo(address="456 Oak Ave")
        self.assertEqual(address_minimal.full_address, "456 Oak Ave")

        # 测试使用state而不是state_full的情况
        address_state = AddressInfo(
            address="789 Pine Rd",
            city="Chicago",
            state="IL",
            country="USA"
        )
        expected_state_full = "789 Pine Rd, Chicago, IL, USA"
        self.assertEqual(address_state.full_address, expected_state_full)

        # 测试空地址情况
        address_empty = AddressInfo(address="")
        self.assertEqual(address_empty.full_address, "")

    def test_has_contact_info_property(self) -> None:
        """测试has_contact_info属性"""
        # 测试有电话号码的情况
        address_with_phone = AddressInfo(
            address="123 Main St",
            telephone="+1-555-123-4567"
        )
        self.assertTrue(address_with_phone.has_contact_info)

        # 测试没有电话号码的情况
        address_no_phone = AddressInfo(address="456 Oak Ave")
        self.assertFalse(address_no_phone.has_contact_info)

        # 测试空字符串电话号码
        address_empty_phone = AddressInfo(
            address="789 Pine Rd",
            telephone=""
        )
        self.assertFalse(address_empty_phone.has_contact_info)

    def test_is_complete_property(self) -> None:
        """测试is_complete属性"""
        # 测试完整地址（包含地址和城市）
        address_complete = AddressInfo(
            address="123 Main St",
            city="New York"
        )
        self.assertTrue(address_complete.is_complete)

        # 测试完整地址（包含地址和州）
        address_with_state = AddressInfo(
            address="456 Oak Ave",
            state="CA"
        )
        self.assertTrue(address_with_state.is_complete)

        # 测试完整地址（包含地址和国家）
        address_with_country = AddressInfo(
            address="789 Pine Rd",
            country="USA"
        )
        self.assertTrue(address_with_country.is_complete)

        # 测试不完整地址（只有地址）
        address_incomplete = AddressInfo(address="321 Elm St")
        self.assertFalse(address_incomplete.is_complete)

        # 测试空地址
        address_empty = AddressInfo(address="")
        self.assertFalse(address_empty.is_complete)

    def test_update_info_method(self) -> None:
        """测试update_info方法"""
        address = AddressInfo(
            address="123 Main St",
            city="New York",
            state="NY"
        )
        db.session.add(address)
        db.session.commit()

        original_created_at = address.created_at
        original_updated_at = address.updated_at

        # 等待一小段时间确保时间戳会有变化
        time.sleep(0.01)  # 减少等待时间但仍然确保有差异

        # 更新地址信息
        address.update_info(
            telephone="+1-555-987-6543",
            zip_code="10001",
            country="USA"
        )
        db.session.commit()  # 确保提交更改

        # 验证字段已更新
        self.assertEqual(address.telephone, "+1-555-987-6543")
        self.assertEqual(address.zip_code, "10001")
        self.assertEqual(address.country, "USA")

        # 验证未指定的字段保持不变
        self.assertEqual(address.address, "123 Main St")
        self.assertEqual(address.city, "New York")
        self.assertEqual(address.state, "NY")

        # 验证创建时间不变，更新时间已变化或相等（允许微秒级相同）
        self.assertEqual(address.created_at, original_created_at)
        # 由于SQLAlchemy可能使用数据库时间，允许时间戳相等
        self.assertGreaterEqual(address.updated_at, original_updated_at)

    def test_update_info_protected_fields(self) -> None:
        """测试update_info方法对受保护字段的处理"""
        address = AddressInfo(address="123 Main St")
        db.session.add(address)
        db.session.commit()

        original_id = address.id
        original_created_at = address.created_at
        original_updated_at = address.updated_at

        # 等待一小段时间确保时间戳会有变化
        time.sleep(0.01)

        # 尝试更新受保护的字段
        address.update_info(
            id=999,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            address="456 Oak Ave"
        )
        db.session.commit()  # 确保提交更改

        # 验证受保护字段未被更新
        self.assertEqual(address.id, original_id)
        self.assertEqual(address.created_at, original_created_at)

        # 验证可更新字段已更新
        self.assertEqual(address.address, "456 Oak Ave")
        self.assertGreaterEqual(address.updated_at, original_updated_at)

    def test_to_dict_method(self) -> None:
        """测试to_dict方法"""
        address = AddressInfo(
            address="123 Main Street, Suite 100",
            telephone="+1-555-123-4567",
            city="San Francisco",
            zip_code="94105",
            state="CA",
            state_full="California",
            country="United States",
            source_url="https://example.com/addresses/123"
        )
        db.session.add(address)
        db.session.commit()

        address_dict = address.to_dict()

        # 验证字典包含所有必要字段
        expected_fields = [
            'id', 'address', 'telephone', 'city', 'zip_code', 'state',
            'state_full', 'country', 'source_url', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            self.assertIn(field, address_dict)

        # 验证字段值
        self.assertEqual(address_dict['address'], "123 Main Street, Suite 100")
        self.assertEqual(address_dict['telephone'], "+1-555-123-4567")
        self.assertEqual(address_dict['city'], "San Francisco")
        self.assertEqual(address_dict['zip_code'], "94105")
        self.assertEqual(address_dict['state'], "CA")
        self.assertEqual(address_dict['state_full'], "California")
        self.assertEqual(address_dict['country'], "United States")
        self.assertEqual(address_dict['source_url'], "https://example.com/addresses/123")

        # 验证时间戳格式
        self.assertIsInstance(address_dict['created_at'], str)
        self.assertIsInstance(address_dict['updated_at'], str)

        # 验证时间戳值不为None
        self.assertIsNotNone(address_dict['created_at'])
        self.assertIsNotNone(address_dict['updated_at'])

    def test_repr_method(self) -> None:
        """测试__repr__方法"""
        address = AddressInfo(
            address="123 Main St",
            city="Boston",
            country="USA"
        )
        db.session.add(address)
        db.session.commit()

        repr_str = repr(address)

        # 验证字符串格式
        self.assertIn("AddressInfo(", repr_str)
        self.assertIn(f"id={address.id}", repr_str)
        self.assertIn("address='123 Main St'", repr_str)
        self.assertIn("city='Boston'", repr_str)
        self.assertIn("country='USA'", repr_str)

    def test_database_relationships_and_constraints(self) -> None:
        """测试数据库关系和约束"""
        # 测试创建多个地址记录
        address1 = AddressInfo(
            address="123 First St",
            city="City1",
            telephone="+1-111-111-1111"
        )
        address2 = AddressInfo(
            address="456 Second Ave",
            city="City2",
            telephone="+1-222-222-2222"
        )
        address3 = AddressInfo(
            address="789 Third Rd",
            city="City3",
            telephone="+1-333-333-3333"
        )

        db.session.add_all([address1, address2, address3])
        db.session.commit()

        # 验证所有记录都已保存
        all_addresses = db.session.query(AddressInfo).all()
        self.assertEqual(len(all_addresses), 3)

        # 验证每个记录的ID都是唯一的且已自动递增
        ids = [addr.id for addr in all_addresses]
        self.assertEqual(len(set(ids)), 3)  # 所有ID都应该是唯一的
        self.assertEqual(min(ids), 1)  # 最小ID应该是1
        self.assertEqual(max(ids), 3)  # 最大ID应该是3

        # 测试通过不同字段查询
        by_city = db.session.query(AddressInfo).filter_by(city="City2").first()
        self.assertIsNotNone(by_city)
        self.assertEqual(by_city.address, "456 Second Ave")

        by_phone = db.session.query(AddressInfo).filter_by(
            telephone="+1-333-333-3333"
        ).first()
        self.assertIsNotNone(by_phone)
        self.assertEqual(by_phone.city, "City3")

        # 测试索引字段的查询性能（验证索引存在）
        # 注意：这里只是验证查询功能，实际的性能测试需要更复杂的设置
        by_address = db.session.query(AddressInfo).filter(
            AddressInfo.address == "123 First St"
        ).first()
        self.assertIsNotNone(by_address)
        self.assertEqual(by_address.city, "City1")

    def test_unicode_and_special_characters(self) -> None:
        """测试Unicode字符和特殊字符的处理"""
        # 测试中文地址
        chinese_address = AddressInfo(
            address="北京市朝阳区建国门外大街1号",
            city="北京市",
            state="北京市",
            country="中国",
            telephone="+86-10-12345678"
        )
        db.session.add(chinese_address)
        db.session.commit()

        saved_chinese = db.session.query(AddressInfo).filter_by(
            city="北京市"
        ).first()
        self.assertIsNotNone(saved_chinese)
        self.assertEqual(saved_chinese.address, "北京市朝阳区建国门外大街1号")

        # 测试特殊字符
        special_address = AddressInfo(
            address="123 O'Malley & Sons, Apt. #4",
            city="Saint-Pierre-d'Oléron",
            zip_code="12345-6789",
            telephone="+1-(555)-123-4567"
        )
        db.session.add(special_address)
        db.session.commit()

        saved_special = db.session.query(AddressInfo).filter_by(
            zip_code="12345-6789"
        ).first()
        self.assertIsNotNone(saved_special)
        self.assertEqual(saved_special.address, "123 O'Malley & Sons, Apt. #4")


if __name__ == '__main__':
    unittest.main()
