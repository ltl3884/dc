"""
爬虫服务模块

该模块提供地址数据爬取功能，包括API调用、响应解析、错误处理等核心功能，
为地址爬虫系统提供完整的爬取服务支持。
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from sqlalchemy.exc import SQLAlchemyError

from src.app import db
from src.config import get_config
from src.models.address_info import AddressInfo
from src.utils.logger import get_logger


class CrawlerService:
    """
    爬虫服务类
    
    提供地址数据爬取功能，包括API调用、响应解析、数据存储等核心功能。
    支持重试机制、错误处理和不同类型的HTTP状态码处理。
    """
    
    def __init__(self) -> None:
        """初始化爬虫服务"""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.session = requests.Session()
        
        # 配置会话
        self.session.timeout = self.config.CRAWLER_TIMEOUT
        self.session.headers.update({
            'User-Agent': 'AddressCrawler/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def crawl_address(
        self,
        address: str,
        method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        爬取目标URL内容
        
        Args:
            address: 要爬取的目标URL
            method: HTTP请求方法，默认为GET
            body: 请求体内容，可选
            headers: HTTP请求头字典，可选
            **kwargs: 其他请求参数（如timeout, retry_count等）
            
        Returns:
            Dict[str, Any]: 爬取结果，包含状态和数据
            
        Raises:
            ValueError: 当URL为空或无效时
            RequestException: 当请求失败时
        """
        target_url = address.strip()
        if not target_url:
            raise ValueError("目标URL不能为空")
        
        # 构建请求参数
        request_kwargs = {
            'timeout': kwargs.get('timeout', self.config.CRAWLER_TIMEOUT),
        }
        
        # 添加自定义headers
        if headers:
            request_kwargs['headers'] = headers
        
        # 添加body（主要用于POST/PUT请求）
        if body and method.upper() != 'GET':
            request_kwargs['data'] = body
        
        self.logger.info(f"开始爬取URL: {target_url}")
        self.logger.info(f"HTTP方法: {method}")
        
        # 重试机制
        retry_count = kwargs.get('retry_count', self.config.CRAWLER_RETRY_COUNT)
        for attempt in range(retry_count):
            try:
                self.logger.debug(f"尝试第 {attempt + 1} 次请求")
                
                # 根据method选择请求方式
                if method.upper() == 'GET':
                    response = self.session.get(target_url, **request_kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(target_url, **request_kwargs)
                elif method.upper() == 'PUT':
                    response = self.session.put(target_url, **request_kwargs)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(target_url, **request_kwargs)
                else:
                    # 其他方法使用通用request
                    response = self.session.request(method.upper(), target_url, **request_kwargs)
                
                # 处理HTTP响应
                self.logger.info(f"收到HTTP响应，状态码: {response.status_code}")
                result = self._handle_http_response(response, target_url)
                
                if result['status'] == 'success':
                    self.logger.info(f"URL爬取成功: {target_url}")
                else:
                    self.logger.warning(f"URL爬取失败: {target_url}, 原因: {result.get('error')}")
                
                return result
                
            except (Timeout, ConnectionError) as e:
                self.logger.warning(f"网络错误 (尝试 {attempt + 1}): {str(e)}")
                if attempt < self.config.CRAWLER_RETRY_COUNT - 1:
                    time.sleep(self.config.CRAWLER_RETRY_DELAY)
                    continue
                else:
                    error_msg = f"网络错误，重试{retry_count}次后仍然失败: {str(e)}"
                    self.logger.error(error_msg)
                    return {
                        'status': 'error',
                        'error': error_msg,
                        'url': target_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except RequestException as e:
                error_msg = f"请求异常: {str(e)}"
                self.logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': error_msg,
                    'url': target_url,
                    'timestamp': datetime.now().isoformat()
                }
            
            except Exception as e:
                error_msg = f"未预期的错误: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return {
                    'status': 'error',
                    'error': error_msg,
                    'url': target_url,
                    'timestamp': datetime.now().isoformat()
                }
    
    def _handle_http_response(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """
        处理HTTP响应
        
        Args:
            response: HTTP响应对象
            url: 请求的URL
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        status_code = response.status_code
        self.logger.debug(f"HTTP状态码: {status_code}")
        
        # 成功响应
        if 200 <= status_code < 300:
            try:
                return self.parse_api_response(response, url)
            except Exception as e:
                error_msg = f"响应解析失败: {str(e)}"
                self.logger.error(error_msg)
                return {
                    'status': 'error',
                    'error': error_msg,
                    'url': url,
                    'status_code': status_code,
                    'timestamp': datetime.now().isoformat()
                }
        
        # 客户端错误 (4xx)
        elif 400 <= status_code < 500:
            error_messages = {
                400: "请求参数错误",
                401: "未授权访问",
                403: "访问被禁止",
                404: "API接口不存在",
                429: "请求频率限制"
            }
            
            error_msg = error_messages.get(
                status_code, 
                f"客户端错误 (状态码: {status_code})"
            )
            
            self.logger.warning(f"客户端错误: {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'url': url,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat()
            }
        
        # 服务器错误 (5xx)
        elif 500 <= status_code < 600:
            error_messages = {
                500: "服务器内部错误",
                502: "网关错误",
                503: "服务不可用",
                504: "网关超时"
            }
            
            error_msg = error_messages.get(
                status_code,
                f"服务器错误 (状态码: {status_code})"
            )
            
            self.logger.error(f"服务器错误: {error_msg}")
            return {
                'status': 'error',
                'error': error_msg,
                'url': url,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat()
            }
        
        # 其他状态码
        else:
            error_msg = f"未预期的HTTP状态码: {status_code}"
            self.logger.error(error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'url': url,
                'status_code': status_code,
                'timestamp': datetime.now().isoformat()
            }
    
    def parse_api_response(self, response: requests.Response, url: str) -> Dict[str, Any]:
        """
        解析API响应数据
        
        Args:
            response: HTTP响应对象
            url: 原始请求URL
            
        Returns:
            Dict[str, Any]: 解析后的数据
            
        Raises:
            ValueError: 当响应格式无效时
            json.JSONDecodeError: 当JSON解析失败时
        """
        try:
            # 尝试解析JSON响应
            response_data = response.json()
            self.logger.debug(f"API响应数据: {response_data}")
            
            # 提取地址信息
            address_info = self._extract_address_info(response_data, url)
            
            return {
                'status': 'success',
                'url': url,
                'data': address_info,
                'raw_response': response_data,
                'status_code': response.status_code,
                'timestamp': datetime.now().isoformat()
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {str(e)}"
            self.logger.error(f"{error_msg}, 响应内容: {response.text[:200]}")
            
            # 尝试获取文本内容
            text_content = response.text.strip()
            if text_content:
                return {
                    'status': 'warning',
                    'url': url,
                    'data': {'raw_text': text_content},
                    'error': error_msg,
                    'status_code': response.status_code,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                raise ValueError("响应内容为空")
                
        except Exception as e:
            error_msg = f"响应处理失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg)
    
    def _extract_address_info(self, response_data: Dict[str, Any], original_url: str) -> Dict[str, Any]:
        """
        从API响应中提取地址信息
        
        Args:
            response_data: API响应数据
            original_url: 原始请求URL
            
        Returns:
            Dict[str, Any]: 提取的地址信息
        """
        # 通用的地址信息提取逻辑
        address_info = {
            'original_url': original_url,
            'formatted_address': '',
            'province': '',
            'city': '',
            'district': '',
            'street': '',
            'street_number': '',
            'longitude': None,
            'latitude': None,
            'confidence': None,
            'level': ''
        }
        
        try:
            # 尝试从常见字段中提取信息
            # 处理高德地图API格式
            if 'geocodes' in response_data and response_data['geocodes']:
                geocode = response_data['geocodes'][0]
                address_info.update({
                    'formatted_address': geocode.get('formatted_address', ''),
                    'province': geocode.get('province', ''),
                    'city': geocode.get('city', ''),
                    'district': geocode.get('district', ''),
                    'street': geocode.get('street', ''),
                    'street_number': geocode.get('number', ''),
                    'level': geocode.get('level', '')
                })
                
                # 解析坐标
                location = geocode.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    address_info['longitude'] = float(lng.strip())
                    address_info['latitude'] = float(lat.strip())
            
            # 处理百度地图API格式
            elif 'result' in response_data:
                result = response_data['result']
                address_info.update({
                    'formatted_address': result.get('formatted_address', ''),
                    'province': result.get('addressComponent', {}).get('province', ''),
                    'city': result.get('addressComponent', {}).get('city', ''),
                    'district': result.get('addressComponent', {}).get('district', ''),
                    'street': result.get('addressComponent', {}).get('street', ''),
                    'street_number': result.get('addressComponent', {}).get('street_number', ''),
                    'confidence': result.get('confidence'),
                    'level': result.get('level', '')
                })
                
                # 解析坐标
                location = result.get('location', {})
                if location:
                    address_info['longitude'] = location.get('lng')
                    address_info['latitude'] = location.get('lat')
            
            # 处理通用格式
            else:
                # 尝试从响应中提取地址相关字段
                for key, value in response_data.items():
                    key_lower = key.lower()
                    if 'address' in key_lower:
                        if isinstance(value, str):
                            address_info['formatted_address'] = value
                        elif isinstance(value, dict):
                            address_info.update(self._extract_from_dict(value))
                    elif key_lower in ['location', 'point', 'coordinate']:
                        if isinstance(value, dict):
                            if 'lng' in value and 'lat' in value:
                                address_info['longitude'] = value['lng']
                                address_info['latitude'] = value['lat']
                            elif 'lon' in value and 'lat' in value:
                                address_info['longitude'] = value['lon']
                                address_info['latitude'] = value['lat']
                            elif 'x' in value and 'y' in value:
                                address_info['longitude'] = value['x']
                                address_info['latitude'] = value['y']
                
                # 如果没有格式化地址，使用原始URL
                if not address_info['formatted_address']:
                    address_info['formatted_address'] = original_url
            
            self.logger.debug(f"提取的地址信息: {address_info}")
            return address_info
            
        except Exception as e:
            self.logger.warning(f"地址信息提取失败: {str(e)}")
            # 返回包含原始URL的基本信息
            address_info['formatted_address'] = original_url
            return address_info
    
    def _extract_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从字典中提取地址信息
        
        Args:
            data: 包含地址信息的字典
            
        Returns:
            Dict[str, Any]: 提取的地址信息
        """
        result = {}
        
        # 映射常见的地址字段
        field_mapping = {
            'province': ['province', 'state', '省', '州'],
            'city': ['city', '市', '城市'],
            'district': ['district', 'area', '区县', '区', '县'],
            'street': ['street', 'road', '街道', '路'],
            'street_number': ['street_number', 'number', 'streetNumber', '门牌号', '号']
        }
        
        for target_field, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in data:
                    result[target_field] = data[key]
                    break
        
        return result
    
    def save_address_info(self, address_data: Dict[str, Any]) -> Optional[AddressInfo]:
        """
        保存地址信息到数据库
        
        Args:
            address_data: 地址数据
            
        Returns:
            Optional[AddressInfo]: 保存的地址信息对象，失败时返回None
        """
        try:
            if address_data.get('status') != 'success':
                self.logger.warning("无法保存失败的爬取结果")
                return None
            
            data = address_data.get('data', {})
            
            # 创建AddressInfo实例，使用formatted_address作为address字段
            address_info = AddressInfo(
                address=data.get('formatted_address', address_data.get('url', '')),
                city=data.get('city', ''),
                state_full=data.get('province', ''),
                telephone=None,  # 爬虫服务不提供电话号码
                zip_code=None,   # 爬虫服务不提供邮编
                state=data.get('province', ''),  # 简写省份
                country='中国'   # 默认中国
            )
            
            # 设置额外的自定义字段（如果模型支持）
            try:
                address_info.original_url = address_data.get('url', '')
                address_info.formatted_address = data.get('formatted_address', '')
                address_info.province = data.get('province', '')
                address_info.district = data.get('district', '')
                address_info.street = data.get('street', '')
                address_info.street_number = data.get('street_number', '')
                address_info.longitude = data.get('longitude')
                address_info.latitude = data.get('latitude')
                address_info.confidence = data.get('confidence')
                address_info.level = data.get('level', '')
                address_info.raw_response = json.dumps(address_data.get('raw_response', {}))
                address_info.status = 'completed'
            except AttributeError:
                # 如果某些字段不存在，忽略它们
                pass
            
            # 保存到数据库
            db.session.add(address_info)
            db.session.commit()
            
            self.logger.info(f"地址信息已保存: {address_info.formatted_address}")
            return address_info
            
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"数据库错误: {str(e)}"
            self.logger.error(error_msg)
            return None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"保存地址信息失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None
    
    def crawl_and_save(
        self,
        address: str,
        method: str = 'GET',
        body: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        爬取地址并保存结果
        
        Args:
            address: 要爬取的目标URL
            method: HTTP请求方法，默认为GET
            body: 请求体内容，可选
            headers: HTTP请求头字典，可选
            **kwargs: 其他请求参数
            
        Returns:
            Dict[str, Any]: 包含爬取结果和保存状态的字典
        """
        # 爬取地址
        crawl_result = self.crawl_address(address, method, body, headers, **kwargs)
        
        # 如果爬取成功，保存结果
        if crawl_result['status'] == 'success':
            saved_info = self.save_address_info(crawl_result)
            if saved_info:
                crawl_result['saved_id'] = saved_info.id
                crawl_result['saved'] = True
            else:
                crawl_result['saved'] = False
                crawl_result['save_error'] = '保存到数据库失败'
        
        return crawl_result
    
    def close(self) -> None:
        """关闭服务，清理资源"""
        if self.session:
            self.session.close()
            self.logger.info("爬虫服务已关闭")