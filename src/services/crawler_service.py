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
            address_data = response_data.get("address", {});
            self.logger.debug(f"API响应数据: {response_data}")
            
            # 提取地址信息
            # address_info = self._extract_address_info(response_data, url)
            address_info = AddressInfo()
            if address_data:
                address_info.address = address_data.get("Address")
                address_info.telephone = address_data.get("Telephone")
                address_info.city = address_data.get("City")
                address_info.zip_code = address_data.get("Zip_Code")
                address_info.state = address_data.get("State")
                address_info.state_full = address_data.get("State_Full")
                address_info.country = address_data.get("Country")
                address_info.source_url = url
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
            if not isinstance(data, AddressInfo):
                self.logger.warning("数据格式不正确，无法保存")
                return None
                
            # 保存到数据库
            db.session.add(data)
            db.session.commit()
            
            self.logger.info(f"地址信息已保存: {data.address}")
            return data
            
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