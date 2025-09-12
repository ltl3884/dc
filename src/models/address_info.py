"""
地址信息模型模块

该模块定义了AddressInfo模型类，用于存储和管理地址信息的数据结构，
包括地址、电话、城市、邮编、州、国家等核心字段，以及数据来源和时间戳信息。
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from src.app import db


class AddressInfo(db.Model):
    """
    地址信息模型类
    
    用于定义地址信息的数据结构，包含地址详细信息
    和数据来源跟踪字段。
    """
    
    __tablename__ = 'address_info'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 地址核心字段
    address = Column(String(512), nullable=False, index=True, comment='详细地址')
    telephone = Column(String(50), nullable=True, comment='电话号码')
    city = Column(String(100), nullable=True, index=True, comment='城市')
    zip_code = Column(String(20), nullable=True, comment='邮政编码')
    state = Column(String(50), nullable=True, index=True, comment='州/省份缩写')
    state_full = Column(String(100), nullable=True, comment='州/省份全称')
    country = Column(String(100), nullable=True, index=True, comment='国家')
    
    # 数据来源字段
    source_url = Column(String(2048), nullable=True, comment='数据来源URL')
    
    # 时间戳字段
    created_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        server_default=func.now(),
        comment='创建时间'
    )
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        comment='更新时间'
    )
    
    def __init__(
        self,
        address: Optional[str] = None,
        telephone: Optional[str] = None,
        city: Optional[str] = None,
        zip_code: Optional[str] = None,
        state: Optional[str] = None,
        state_full: Optional[str] = None,
        country: Optional[str] = None,
        source_url: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        初始化地址信息实例
        
        Args:
            address: 详细地址
            telephone: 电话号码，可选
            city: 城市，可选
            zip_code: 邮政编码，可选
            state: 州/省份缩写，可选
            state_full: 州/省份全称，可选
            country: 国家，可选
            source_url: 数据来源URL，可选
            **kwargs: 其他可选参数
        """
        self.address = address
        self.telephone = telephone
        self.city = city
        self.zip_code = zip_code
        self.state = state
        self.state_full = state_full
        self.country = country
        self.source_url = source_url
        
        # 设置其他字段
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        return f"<AddressInfo(id={self.id}, address='{self.address}', city='{self.city}', country='{self.country}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将地址信息对象转换为字典
        
        Returns:
            Dict[str, Any]: 地址数据的字典表示
        """
        return {
            'id': self.id,
            'address': self.address,
            'telephone': self.telephone,
            'city': self.city,
            'zip_code': self.zip_code,
            'state': self.state,
            'state_full': self.state_full,
            'country': self.country,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def full_address(self) -> str:
        """
        获取完整地址字符串
        
        Returns:
            str: 完整地址字符串
        """
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state_full:
            parts.append(self.state_full)
        elif self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        if self.zip_code:
            parts.append(self.zip_code)
        
        return ', '.join(parts) if parts else self.address
    
    @property
    def has_contact_info(self) -> bool:
        """
        检查是否有联系信息
        
        Returns:
            bool: 如果有电话号码返回True
        """
        return bool(self.telephone)
    
    @property
    def is_complete(self) -> bool:
        """
        检查地址信息是否完整
        
        Returns:
            bool: 如果包含基本地址信息返回True
        """
        return bool(self.address and (self.city or self.state or self.country))
    
    def update_info(self, **kwargs) -> None:
        """
        更新地址信息
        
        Args:
            **kwargs: 要更新的字段和值
        """
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'created_at', 'updated_at']:
                setattr(self, key, value)