"""
数据验证服务模块

该模块提供地址数据的验证、清洗和唯一性检查功能，确保数据质量和完整性。
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from src.app import db
from src.models.address_info import AddressInfo
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationService:
    """
    数据验证服务类
    
    提供地址数据的验证、清洗和唯一性检查功能，
    确保数据质量和完整性。
    """
    
    def __init__(self) -> None:
        """初始化验证服务"""
        pass
    
    def validate_address_data(self, address_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证地址数据的必填字段
        
        Args:
            address_data: 地址数据字典
            
        Returns:
            Tuple[bool, List[str]]: (验证是否通过, 错误信息列表)
        """
        errors = []
        
        # 检查必填字段
        required_fields = ['address']
        for field in required_fields:
            if not address_data.get(field) or not str(address_data[field]).strip():
                errors.append(f"必填字段 '{field}' 不能为空")
        
        # 验证地址字段长度
        address = address_data.get('address', '').strip()
        if address and len(address) > 512:
            errors.append("地址字段长度不能超过512个字符")
        
        # 验证电话号码格式（如果提供）
        telephone = address_data.get('telephone')
        if telephone and not self._is_valid_telephone(telephone):
            errors.append("电话号码格式无效")
        
        # 验证邮政编码格式（如果提供）
        zip_code = address_data.get('zip_code')
        if zip_code and not self._is_valid_zip_code(zip_code):
            errors.append("邮政编码格式无效")
        
        # 验证城市、州、国家字段长度
        field_limits = {
            'city': 100,
            'state': 50,
            'state_full': 100,
            'country': 100,
            'telephone': 50,
            'zip_code': 20
        }
        
        for field, limit in field_limits.items():
            value = address_data.get(field)
            if value and len(str(value)) > limit:
                errors.append(f"字段 '{field}' 长度不能超过{limit}个字符")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"地址数据验证失败: {errors}")
        
        return is_valid, errors
    
    def check_duplicate_address(self, address_data: Dict[str, Any], exclude_id: Optional[int] = None) -> Tuple[bool, Optional[AddressInfo]]:
        """
        检查地址是否已存在（唯一性验证）
        
        Args:
            address_data: 地址数据字典
            exclude_id: 排除检查的ID（用于更新操作时）
            
        Returns:
            Tuple[bool, Optional[AddressInfo]]: (是否重复, 重复的地址对象)
        """
        try:
            # 构建查询条件
            query_conditions = []
            
            # 主要匹配条件：地址 + 城市 + 州 + 国家
            if address_data.get('address'):
                query_conditions.append(AddressInfo.address == address_data['address'].strip())
            
            if address_data.get('city'):
                query_conditions.append(AddressInfo.city == address_data['city'].strip())
            
            if address_data.get('state'):
                query_conditions.append(AddressInfo.state == address_data['state'].strip())
            
            if address_data.get('country'):
                query_conditions.append(AddressInfo.country == address_data['country'].strip())
            
            # 如果没有基本匹配条件，返回不重复
            if not query_conditions:
                return False, None
            
            # 执行查询
            query = AddressInfo.query.filter(and_(*query_conditions))
            
            # 排除指定ID（更新操作时）
            if exclude_id:
                query = query.filter(AddressInfo.id != exclude_id)
            
            existing_address = query.first()
            
            if existing_address:
                logger.info(f"发现重复地址: ID={existing_address.id}, 地址={existing_address.address}")
                return True, existing_address
            
            return False, None
            
        except Exception as e:
            logger.error(f"检查地址重复时发生错误: {str(e)}")
            # 发生错误时假设不重复，避免阻塞数据录入
            return False, None
    
    def sanitize_telephone(self, telephone: str) -> Optional[str]:
        """
        清洗电话号码格式
        
        Args:
            telephone: 原始电话号码字符串
            
        Returns:
            Optional[str]: 清洗后的电话号码，如果无效则返回None
        """
        if not telephone:
            return None
        
        try:
            # 移除所有非数字字符
            cleaned = re.sub(r'[^\d+]', '', str(telephone).strip())
            
            # 如果为空，返回None
            if not cleaned:
                return None
            
            # 处理国际区号
            if cleaned.startswith('00'):
                cleaned = '+' + cleaned[2:]
            elif cleaned.startswith('0'):
                # 保留开头的0（可能是国内区号）
                pass
            
            # 验证清洗后的电话号码
            if not self._is_valid_telephone(cleaned):
                return None
            
            return cleaned
            
        except Exception as e:
            logger.error(f"清洗电话号码时发生错误: {telephone}, 错误: {str(e)}")
            return None
    
    def sanitize_address_data(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗地址数据
        
        Args:
            address_data: 原始地址数据字典
            
        Returns:
            Dict[str, Any]: 清洗后的地址数据
        """
        if not address_data:
            return {}
        
        sanitized_data = {}
        
        try:
            # 字符串字段清洗
            string_fields = ['address', 'city', 'state', 'state_full', 'country', 'zip_code', 'source_url']
            for field in string_fields:
                if field in address_data and address_data[field] is not None:
                    value = str(address_data[field]).strip()
                    # 移除多余的空白字符
                    value = re.sub(r'\s+', ' ', value)
                    sanitized_data[field] = value if value else None
            
            # 电话号码特殊清洗
            if 'telephone' in address_data:
                sanitized_data['telephone'] = self.sanitize_telephone(address_data['telephone'])
            
            # 保留其他字段
            for key, value in address_data.items():
                if key not in sanitized_data and key not in ['id', 'created_at', 'updated_at']:
                    sanitized_data[key] = value
            
            return sanitized_data
            
        except Exception as e:
            logger.error(f"清洗地址数据时发生错误: {str(e)}")
            # 发生错误时返回原始数据
            return address_data
    
    def _is_valid_telephone(self, telephone: str) -> bool:
        """
        验证电话号码格式是否有效
        
        Args:
            telephone: 电话号码字符串
            
        Returns:
            bool: 如果格式有效返回True
        """
        if not telephone:
            return True  # 空电话号码视为有效（可选字段）
        
        # 电话号码正则表达式：支持国际格式和国内格式
        phone_pattern = re.compile(r'^[\d\s\-\(\)\+]{7,20}$')
        return bool(phone_pattern.match(str(telephone)))
    
    def _is_valid_zip_code(self, zip_code: str) -> bool:
        """
        验证邮政编码格式是否有效
        
        Args:
            zip_code: 邮政编码字符串
            
        Returns:
            bool: 如果格式有效返回True
        """
        if not zip_code:
            return True  # 空邮政编码视为有效（可选字段）
        
        # 支持多种邮政编码格式
        zip_patterns = [
            r'^\d{5}(-\d{4})?$',  # 美国邮编：12345 或 12345-6789
            r'^[A-Z]\d[A-Z] \d[A-Z]\d$',  # 加拿大邮编：A1B 2C3
            r'^\d{6}$',  # 中国邮编：123456
            r'^\d{4}$',  # 澳大利亚等：1234
            r'^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$'  # 英国邮编
        ]
        
        zip_str = str(zip_code).strip().upper()
        for pattern in zip_patterns:
            if re.match(pattern, zip_str):
                return True
        
        # 如果都不匹配，检查是否为纯数字或字母数字组合
        return bool(re.match(r'^[A-Z0-9\s\-]{3,10}$', zip_str))
    
    def validate_and_sanitize(self, address_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        验证并清洗地址数据（组合操作）
        
        Args:
            address_data: 原始地址数据字典
            
        Returns:
            Tuple[bool, Dict[str, Any], List[str]]: (验证是否通过, 清洗后的数据, 错误信息列表)
        """
        # 首先清洗数据
        sanitized_data = self.sanitize_address_data(address_data)
        
        # 然后验证清洗后的数据
        is_valid, errors = self.validate_address_data(sanitized_data)
        
        return is_valid, sanitized_data, errors