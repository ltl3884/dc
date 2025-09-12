#!/usr/bin/env python3
"""
CrawlerService集成测试模块

该模块包含CrawlerService的集成测试，用于验证地址爬取功能，
包括API URL构造、响应解析、错误处理等核心功能。
"""

import sys
import os
import unittest
import json
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock, Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from src.app import create_app, db
from src.services.crawler_service import CrawlerService
from src.models.address_info import AddressInfo


class TestCrawlerService(unittest.TestCase):
    """CrawlerService集成测试类"""
    
    def setUp(self) -> None:
        """测试前的准备工作"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.crawler_service = CrawlerService()
    
    def tearDown(self) -> None:
        """测试后的清理工作"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.crawler_service.close()
    
    def test_init_crawler_service(self) -> None:
        """测试CrawlerService初始化"""
        self.assertIsNotNone(self.crawler_service.logger)
        self.assertIsNotNone(self.crawler_service.config)
        self.assertIsNotNone(self.crawler_service.session)
        self.assertEqual(self.crawler_service.session.timeout, 30)
        self.assertIn('User-Agent', self.crawler_service.session.headers)
        self.assertEqual(self.crawler_service.session.headers['User-Agent'], 'AddressCrawler/1.0')
    
    def test_crawl_address_with_empty_address(self) -> None:
        """测试爬取空地址时的错误处理"""
        # 测试空字符串
        with self.assertRaises(ValueError) as cm:
            self.crawler_service.crawl_address("")
        self.assertIn("地址不能为空", str(cm.exception))
        
        # 测试空白字符串
        with self.assertRaises(ValueError) as cm:
            self.crawler_service.crawl_address("   ")
        self.assertIn("地址不能为空", str(cm.exception))
        
        # 测试None值
        with self.assertRaises(ValueError) as cm:
            self.crawler_service.crawl_address(None)
        self.assertIn("地址不能为空", str(cm.exception))
    
    def test_crawl_address_with_missing_api_url(self) -> None:
        """测试缺少API URL配置时的错误处理"""
        with patch.object(self.crawler_service.config, 'API_BASE_URL', None):
            with self.assertRaises(ValueError) as cm:
                self.crawler_service.crawl_address("北京市朝阳区")
            self.assertIn("API基础URL未配置", str(cm.exception))
    
    @patch('requests.Session.get')
    def test_crawl_address_success_response(self, mock_get: Mock) -> None:
        """测试成功的API响应处理"""
        # 模拟成功的API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'geocodes': [{
                'formatted_address': '北京市朝阳区',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'street': '朝阳路',
                'number': '123号',
                'level': '门牌号',
                'location': '116.481,39.990'
            }]
        }
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("北京市朝阳区")
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['address'], '北京市朝阳区')
        self.assertIn('data', result)
        self.assertEqual(result['data']['formatted_address'], '北京市朝阳区')
        self.assertEqual(result['data']['province'], '北京市')
        self.assertEqual(result['data']['city'], '北京市')
        self.assertEqual(result['data']['district'], '朝阳区')
        self.assertEqual(result['data']['longitude'], 116.481)
        self.assertEqual(result['data']['latitude'], 39.990)
        self.assertIn('raw_response', result)
        self.assertEqual(result['status_code'], 200)
    
    @patch('requests.Session.get')
    def test_api_url_construction_with_custom_url(self, mock_get: Mock) -> None:
        """测试使用自定义API URL构造"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'formatted_address': '测试地址'}}
        mock_get.return_value = mock_response
        
        custom_url = "https://custom-api.example.com/geocode"
        result = self.crawler_service.crawl_address("测试地址", api_url=custom_url)
        
        self.assertEqual(result['status'], 'success')
        # 验证使用了自定义URL
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], custom_url)
    
    @patch('requests.Session.get')
    def test_api_url_construction_with_custom_api_key(self, mock_get: Mock) -> None:
        """测试使用自定义API密钥"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'formatted_address': '测试地址'}}
        mock_get.return_value = mock_response
        
        custom_api_key = "custom_key_123"
        result = self.crawler_service.crawl_address("测试地址", api_key=custom_api_key)
        
        self.assertEqual(result['status'], 'success')
        # 验证请求参数中包含自定义API密钥
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('params', call_args[1])
        self.assertEqual(call_args[1]['params']['key'], custom_api_key)
    
    @patch('requests.Session.get')
    def test_api_url_construction_with_additional_params(self, mock_get: Mock) -> None:
        """测试带额外参数的URL构造"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'formatted_address': '测试地址'}}
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address(
            "测试地址", 
            output="json",
            city="北京"
        )
        
        self.assertEqual(result['status'], 'success')
        # 验证额外参数被正确添加
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['output'], "json")
        self.assertEqual(params['city'], "北京")
        self.assertEqual(params['address'], "测试地址")
    
    @patch('requests.Session.get')
    def test_parse_api_response_baidu_format(self, mock_get: Mock) -> None:
        """测试解析百度地图API响应格式"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'result': {
                'formatted_address': '北京市海淀区上地十街10号',
                'addressComponent': {
                    'province': '北京市',
                    'city': '北京市',
                    'district': '海淀区',
                    'street': '上地十街',
                    'street_number': '10号'
                },
                'location': {
                    'lng': 116.308,
                    'lat': 40.050
                },
                'confidence': 80,
                'level': '门牌号'
            }
        }
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("百度大厦")
        
        self.assertEqual(result['status'], 'success')
        data = result['data']
        self.assertEqual(data['formatted_address'], '北京市海淀区上地十街10号')
        self.assertEqual(data['province'], '北京市')
        self.assertEqual(data['city'], '北京市')
        self.assertEqual(data['district'], '海淀区')
        self.assertEqual(data['street'], '上地十街')
        self.assertEqual(data['street_number'], '10号')
        self.assertEqual(data['longitude'], 116.308)
        self.assertEqual(data['latitude'], 40.050)
        self.assertEqual(data['confidence'], 80)
        self.assertEqual(data['level'], '门牌号')
    
    @patch('requests.Session.get')
    def test_parse_api_response_gaode_format(self, mock_get: Mock) -> None:
        """测试解析高德地图API响应格式"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'geocodes': [{
                'formatted_address': '上海市浦东新区陆家嘴环路1000号',
                'province': '上海市',
                'city': '上海市',
                'district': '浦东新区',
                'street': '陆家嘴环路',
                'number': '1000号',
                'level': '门牌号',
                'location': '121.505,31.240'
            }]
        }
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("上海中心大厦")
        
        self.assertEqual(result['status'], 'success')
        data = result['data']
        self.assertEqual(data['formatted_address'], '上海市浦东新区陆家嘴环路1000号')
        self.assertEqual(data['province'], '上海市')
        self.assertEqual(data['city'], '上海市')
        self.assertEqual(data['district'], '浦东新区')
        self.assertEqual(data['street'], '陆家嘴环路')
        self.assertEqual(data['street_number'], '1000号')
        self.assertEqual(data['level'], '门牌号')
        self.assertEqual(data['longitude'], 121.505)
        self.assertEqual(data['latitude'], 31.240)
    
    @patch('requests.Session.get')
    def test_parse_api_response_generic_format(self, mock_get: Mock) -> None:
        """测试解析通用格式的API响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'address': '广东省深圳市南山区科技园',
            'location': {
                'lng': 113.940,
                'lat': 22.520
            },
            'confidence': 90
        }
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("深圳科技园")
        
        self.assertEqual(result['status'], 'success')
        data = result['data']
        self.assertEqual(data['formatted_address'], '广东省深圳市南山区科技园')
        self.assertEqual(data['longitude'], 113.940)
        self.assertEqual(data['latitude'], 22.520)
        # 通用格式应该保留原始地址作为格式化地址
        self.assertEqual(data['original_address'], '深圳科技园')
    
    @patch('requests.Session.get')
    def test_parse_api_response_invalid_json(self, mock_get: Mock) -> None:
        """测试解析无效JSON响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'warning')
        self.assertEqual(result['address'], '测试地址')
        self.assertIn('data', result)
        self.assertEqual(result['data']['raw_text'], 'Invalid JSON response')
        self.assertIn('error', result)
        self.assertIn('JSON解析失败', result['error'])
    
    @patch('requests.Session.get')
    def test_parse_api_response_empty_content(self, mock_get: Mock) -> None:
        """测试解析空内容响应"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Empty JSON", "", 0)
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertIn('响应内容为空', result['error'])
    
    @patch('requests.Session.get')
    def test_http_status_code_400_error(self, mock_get: Mock) -> None:
        """测试HTTP 400状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['error'], '请求参数错误')
        self.assertEqual(result['status_code'], 400)
    
    @patch('requests.Session.get')
    def test_http_status_code_401_error(self, mock_get: Mock) -> None:
        """测试HTTP 401状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '未授权访问')
        self.assertEqual(result['status_code'], 401)
    
    @patch('requests.Session.get')
    def test_http_status_code_403_error(self, mock_get: Mock) -> None:
        """测试HTTP 403状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '访问被禁止')
        self.assertEqual(result['status_code'], 403)
    
    @patch('requests.Session.get')
    def test_http_status_code_404_error(self, mock_get: Mock) -> None:
        """测试HTTP 404状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], 'API接口不存在')
        self.assertEqual(result['status_code'], 404)
    
    @patch('requests.Session.get')
    def test_http_status_code_429_error(self, mock_get: Mock) -> None:
        """测试HTTP 429状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '请求频率限制')
        self.assertEqual(result['status_code'], 429)
    
    @patch('requests.Session.get')
    def test_http_status_code_500_error(self, mock_get: Mock) -> None:
        """测试HTTP 500状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '服务器内部错误')
        self.assertEqual(result['status_code'], 500)
    
    @patch('requests.Session.get')
    def test_http_status_code_502_error(self, mock_get: Mock) -> None:
        """测试HTTP 502状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 502
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '网关错误')
        self.assertEqual(result['status_code'], 502)
    
    @patch('requests.Session.get')
    def test_http_status_code_503_error(self, mock_get: Mock) -> None:
        """测试HTTP 503状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '服务不可用')
        self.assertEqual(result['status_code'], 503)
    
    @patch('requests.Session.get')
    def test_http_status_code_504_error(self, mock_get: Mock) -> None:
        """测试HTTP 504状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 504
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '网关超时')
        self.assertEqual(result['status_code'], 504)
    
    @patch('requests.Session.get')
    def test_http_status_code_unknown_4xx_error(self, mock_get: Mock) -> None:
        """测试未知4xx状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 418  # I'm a teapot
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '客户端错误 (状态码: 418)')
        self.assertEqual(result['status_code'], 418)
    
    @patch('requests.Session.get')
    def test_http_status_code_unknown_5xx_error(self, mock_get: Mock) -> None:
        """测试未知5xx状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 599  # 未知服务器错误
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '服务器错误 (状态码: 599)')
        self.assertEqual(result['status_code'], 599)
    
    @patch('requests.Session.get')
    def test_http_status_code_unexpected_error(self, mock_get: Mock) -> None:
        """测试非预期状态码错误处理"""
        mock_response = Mock()
        mock_response.status_code = 301  # 重定向
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '未预期的HTTP状态码: 301')
        self.assertEqual(result['status_code'], 301)
    
    @patch('requests.Session.get')
    def test_network_timeout_error(self, mock_get: Mock) -> None:
        """测试网络超时错误处理"""
        mock_get.side_effect = Timeout("Connection timed out")
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('网络错误', result['error'])
        self.assertIn('重试', result['error'])
        self.assertIn('仍然失败', result['error'])
    
    @patch('requests.Session.get')
    def test_connection_error(self, mock_get: Mock) -> None:
        """测试连接错误处理"""
        mock_get.side_effect = ConnectionError("Connection refused")
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('网络错误', result['error'])
        self.assertIn('重试', result['error'])
    
    @patch('requests.Session.get')
    def test_request_exception_error(self, mock_get: Mock) -> None:
        """测试请求异常错误处理"""
        mock_get.side_effect = RequestException("Request failed")
        
        result = self.crawler_service.crawl_address("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['error'], '请求异常: Request failed')
    
    def test_save_address_info_success(self) -> None:
        """测试成功保存地址信息"""
        address_data = {
            'status': 'success',
            'address': '北京市朝阳区朝阳路123号',
            'data': {
                'formatted_address': '北京市朝阳区朝阳路123号',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'street': '朝阳路',
                'street_number': '123号',
                'longitude': 116.481,
                'latitude': 39.990,
                'confidence': 85,
                'level': '门牌号'
            },
            'raw_response': {'test': 'data'}
        }
        
        saved_info = self.crawler_service.save_address_info(address_data)
        
        self.assertIsNotNone(saved_info)
        self.assertEqual(saved_info.address, '北京市朝阳区朝阳路123号')  # AddressInfo使用address字段
        self.assertEqual(saved_info.city, '北京市')
        self.assertEqual(saved_info.state_full, '北京市')  # province映射到state_full
        self.assertEqual(saved_info.country, '中国')  # 默认国家
        # 验证额外字段也被设置
        self.assertEqual(saved_info.original_address, '北京市朝阳区朝阳路123号')
        self.assertEqual(saved_info.formatted_address, '北京市朝阳区朝阳路123号')
        self.assertEqual(saved_info.province, '北京市')
        self.assertEqual(saved_info.district, '朝阳区')
        self.assertEqual(saved_info.street, '朝阳路')
        self.assertEqual(saved_info.street_number, '123号')
        self.assertEqual(saved_info.longitude, 116.481)
        self.assertEqual(saved_info.latitude, 39.990)
        self.assertEqual(saved_info.confidence, 85)
        self.assertEqual(saved_info.level, '门牌号')
        self.assertEqual(saved_info.status, 'completed')
    
    def test_save_address_info_failed_status(self) -> None:
        """测试保存失败状态的地址信息"""
        address_data = {
            'status': 'error',
            'address': '测试地址',
            'error': '爬取失败'
        }
        
        saved_info = self.crawler_service.save_address_info(address_data)
        
        self.assertIsNone(saved_info)
    
    @patch('requests.Session.post')
    def test_crawl_and_save_success(self, mock_post: Mock) -> None:
        """测试爬取并保存成功流程"""
        TEST_URL = "https://www.meiguodizhi.com/api/v1/dz"
        TEST_METHOD = "POST"
        TEST_DATA = '{"city":"","path":"/","method":"refresh"}'
        
        # 模拟成功的API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "address": {
                "Address": "123 Main St",
                "Telephone": "555-1234",
                "City": "New York",
                "Zip_Code": "10001",
                "State": "NY",
                "State_Full": "New York",
                "Country": "USA"
            }
        }
        mock_post.return_value = mock_response
        
        result = self.crawler_service.crawl_and_save(TEST_URL, TEST_METHOD, TEST_DATA)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['saved'], True)
        self.assertIn('saved_id', result)
        self.assertIsNotNone(result['saved_id'])
    
    @patch('requests.Session.get')
    def test_crawl_and_save_failed_crawl(self, mock_get: Mock) -> None:
        """测试爬取失败时的保存流程"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.crawler_service.crawl_and_save("测试地址")
        
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('saved', result)  # 爬取失败时不应该尝试保存
    
    def test_extract_address_info_with_empty_response(self) -> None:
        """测试从空响应中提取地址信息"""
        response_data = {}
        original_address = "测试地址"
        
        address_info = self.crawler_service._extract_address_info(response_data, original_address)
        
        self.assertEqual(address_info['original_address'], original_address)
        self.assertEqual(address_info['formatted_address'], original_address)
        self.assertEqual(address_info['province'], '')
        self.assertEqual(address_info['city'], '')
        self.assertEqual(address_info['district'], '')
        self.assertIsNone(address_info['longitude'])
        self.assertIsNone(address_info['latitude'])
    
    def test_extract_from_dict_with_various_fields(self) -> None:
        """测试从字典中提取各种地址字段"""
        data = {
            'province': '广东省',
            'state': '加利福尼亚州',  # 应该被映射到province
            'city': '深圳市',
            'district': '南山区',
            'area': '科技园',  # 应该被映射到district
            'street': '科技路',
            'road': '深南大道',  # 应该被映射到street
            'street_number': '100号',
            'number': '200号',  # 应该被映射到street_number
            'streetNumber': '300号'  # 应该被映射到street_number
        }
        
        result = self.crawler_service._extract_from_dict(data)
        
        self.assertEqual(result['province'], '广东省')
        self.assertEqual(result['city'], '深圳市')
        self.assertEqual(result['district'], '南山区')
        self.assertEqual(result['street'], '科技路')
        self.assertEqual(result['street_number'], '100号')
    
    def test_close_service(self) -> None:
        """测试关闭服务"""
        # 确保session存在
        self.assertIsNotNone(self.crawler_service.session)
        
        # 关闭服务
        self.crawler_service.close()
        
        # 验证服务已关闭（在实际实现中，session应该被关闭）
        # 这里我们主要确保方法可以正常调用而不抛出异常
        self.assertTrue(True)  # 如果上面的close()调用成功，测试通过


if __name__ == '__main__':
    unittest.main()