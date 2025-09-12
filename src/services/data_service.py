"""
数据持久化服务模块

该模块提供地址数据的持久化功能，包括数据存储、重复数据处理、事务管理等核心功能，
为地址爬虫系统提供可靠的数据存储支持。
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from src.app import db
from src.models.address_info import AddressInfo
from src.utils.logger import get_logger


class DataService:
    """
    数据持久化服务类
    
    提供地址数据的存储、更新、查询等持久化操作，
    支持事务管理和重复数据处理。
    """
    
    def __init__(self) -> None:
        """初始化数据服务"""
        self.logger = get_logger(__name__)
    
    @contextmanager
    def transaction_context(self) -> Session:
        """
        事务上下文管理器
        
        Yields:
            Session: 数据库会话对象
        
        Raises:
            SQLAlchemyError: 数据库操作异常
        """
        session = db.session
        try:
            yield session
            session.commit()
            self.logger.debug("事务提交成功")
        except Exception as e:
            session.rollback()
            self.logger.error(f"事务回滚: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_address_data(
        self, 
        address_data: Dict[str, Any],
        handle_duplicates: bool = True
    ) -> Optional[AddressInfo]:
        """
        保存地址数据到数据库
        
        Args:
            address_data: 地址数据字典
            handle_duplicates: 是否处理重复数据，默认为True
            
        Returns:
            Optional[AddressInfo]: 保存成功的AddressInfo对象，失败返回None
            
        Raises:
            ValueError: 数据验证失败
            SQLAlchemyError: 数据库操作异常
        """
        self.logger.info(f"开始保存地址数据: {address_data.get('address', '未知地址')}")
        try:
            # 验证必需字段
            if not address_data.get('address'):
                self.logger.error("数据验证失败: 地址字段是必需的")
                raise ValueError("地址字段是必需的")
            
            with self.transaction_context() as session:
                # 创建AddressInfo对象
                address_info = AddressInfo(**address_data)
                
                # 检查重复数据
                if handle_duplicates:
                    duplicate = self._check_duplicate(session, address_info)
                    if duplicate:
                        self.logger.info(f"发现重复数据: {duplicate.address}")
                        return self.handle_duplicate_data(duplicate, address_data, session)
                
                # 保存数据
                session.add(address_info)
                session.flush()  # 获取ID但不提交
                
                self.logger.info(f"地址数据保存成功: ID={address_info.id}, 地址={address_info.address}")
                self.logger.debug(f"验证保存结果 - ID: {address_info.id}, 地址: {address_info.address}, 创建时间: {address_info.created_at}")
                return address_info
                
        except ValueError as e:
            self.logger.error(f"数据验证失败: {str(e)}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"数据库操作失败: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"保存地址数据时发生未知错误: {str(e)}")
            raise
    
    def handle_duplicate_data(
        self,
        existing_record: AddressInfo,
        new_data: Dict[str, Any],
        session: Session
    ) -> AddressInfo:
        """
        处理重复数据
        
        Args:
            existing_record: 已存在的数据库记录
            new_data: 新的地址数据
            session: 数据库会话
            
        Returns:
            AddressInfo: 处理后的AddressInfo对象
        """
        self.logger.info(f"开始处理重复数据: 现有记录ID={existing_record.id}, 地址={existing_record.address}")
        try:
            # 策略1：如果新数据更完整，更新现有记录
            if self._is_new_data_better(existing_record, new_data):
                self.logger.info(f"更新现有记录: ID={existing_record.id}")
                
                # 更新字段
                updated_fields = []
                for key, value in new_data.items():
                    if hasattr(existing_record, key) and key not in ['id', 'created_at']:
                        if value and (not getattr(existing_record, key) or key == 'updated_at'):
                            old_value = getattr(existing_record, key)
                            setattr(existing_record, key, value)
                            updated_fields.append(f"{key}: {old_value} -> {value}")
                
                existing_record.updated_at = datetime.utcnow()
                session.add(existing_record)
                
                self.logger.info(f"记录更新完成: ID={existing_record.id}, 更新字段: {', '.join(updated_fields) if updated_fields else '无字段更新'}")
                self.logger.debug(f"验证更新结果 - 记录ID: {existing_record.id}, 更新时间: {existing_record.updated_at}")
                return existing_record
            
            # 策略2：如果现有记录更完整或质量相当，保留现有记录
            else:
                self.logger.info(f"保留现有记录，跳过新数据: ID={existing_record.id}")
                self.logger.debug(f"跳过原因 - 现有数据完整性得分足够高，无需更新")
                return existing_record
                
        except Exception as e:
            self.logger.error(f"处理重复数据时发生错误: ID={existing_record.id}, 错误: {str(e)}")
            raise
    
    def _check_duplicate(self, session: Session, address_info: AddressInfo) -> Optional[AddressInfo]:
        """
        检查重复数据
        
        Args:
            session: 数据库会话
            address_info: 要检查的地址信息
            
        Returns:
            Optional[AddressInfo]: 如果找到重复数据返回现有记录，否则返回None
        """
        self.logger.info(f"开始检查重复数据: 地址={address_info.address}")
        try:
            # 使用地址作为主要检查条件
            query = session.query(AddressInfo).filter(
                AddressInfo.address == address_info.address
            )
            
            # 如果有城市信息，也作为检查条件
            if address_info.city:
                query = query.filter(AddressInfo.city == address_info.city)
            
            # 如果有州信息，也作为检查条件
            if address_info.state:
                query = query.filter(AddressInfo.state == address_info.state)
            
            duplicate = query.first()
            
            if duplicate:
                self.logger.debug(f"发现重复数据: ID={duplicate.id}, 地址={duplicate.address}")
            else:
                self.logger.debug(f"未找到重复数据: 地址={address_info.address}")
            
            return duplicate
            
        except Exception as e:
            self.logger.error(f"检查重复数据时发生错误: 地址={address_info.address}, 错误: {str(e)}")
            return None
    
    def _is_new_data_better(self, existing: AddressInfo, new_data: Dict[str, Any]) -> bool:
        """
        判断新数据是否比现有数据更好（更完整）
        
        Args:
            existing: 现有记录
            new_data: 新的地址数据
            
        Returns:
            bool: 如果新数据更好返回True
        """
        # 计算现有记录的完整性得分
        existing_score = self._calculate_completeness_score(existing)
        
        # 计算新数据的完整性得分
        new_score = self._calculate_dict_completeness_score(new_data)
        
        self.logger.debug(f"数据完整性得分 - 现有: {existing_score}, 新数据: {new_score}")
        
        # 如果新数据得分更高，且至少高10%，认为是更好的数据
        return new_score > existing_score * 1.1
    
    def _calculate_completeness_score(self, address_info: AddressInfo) -> float:
        """
        计算地址信息的完整性得分
        
        Args:
            address_info: 地址信息对象
            
        Returns:
            float: 完整性得分（0-1之间）
        """
        if not address_info:
            return 0.0
        
        fields = ['telephone', 'city', 'zip_code', 'state', 'country']
        total_fields = len(fields)
        completed_fields = sum(1 for field in fields if getattr(address_info, field))
        
        return completed_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_dict_completeness_score(self, data: Dict[str, Any]) -> float:
        """
        计算字典数据的完整性得分
        
        Args:
            data: 地址数据字典
            
        Returns:
            float: 完整性得分（0-1之间）
        """
        if not data:
            return 0.0
        
        fields = ['telephone', 'city', 'zip_code', 'state', 'country']
        total_fields = len(fields)
        completed_fields = sum(1 for field in fields if data.get(field))
        
        return completed_fields / total_fields if total_fields > 0 else 0.0
    
    def batch_save_address_data(
        self,
        address_data_list: List[Dict[str, Any]],
        batch_size: int = 100,
        handle_duplicates: bool = True
    ) -> List[AddressInfo]:
        """
        批量保存地址数据
        
        Args:
            address_data_list: 地址数据列表
            batch_size: 批处理大小，默认100
            handle_duplicates: 是否处理重复数据，默认为True
            
        Returns:
            List[AddressInfo]: 保存成功的AddressInfo对象列表
        """
        if not address_data_list:
            self.logger.warning("批量保存接收到空数据列表")
            return []
        
        saved_records = []
        total_records = len(address_data_list)
        
        self.logger.info(f"开始批量保存 {total_records} 条地址数据")
        
        try:
            with self.transaction_context() as session:
                for i in range(0, total_records, batch_size):
                    batch = address_data_list[i:i + batch_size]
                    batch_saved = []
                    
                    for data in batch:
                        try:
                            # 验证数据
                            if not data.get('address'):
                                self.logger.warning(f"跳过无效数据: 缺少地址字段")
                                continue
                            
                            # 检查重复数据
                            if handle_duplicates:
                                address_info = AddressInfo(**data)
                                duplicate = self._check_duplicate(session, address_info)
                                
                                if duplicate:
                                    result = self.handle_duplicate_data(duplicate, data, session)
                                    batch_saved.append(result)
                                else:
                                    # 保存新数据
                                    new_record = AddressInfo(**data)
                                    session.add(new_record)
                                    batch_saved.append(new_record)
                            else:
                                # 直接保存，不检查重复
                                new_record = AddressInfo(**data)
                                session.add(new_record)
                                batch_saved.append(new_record)
                            
                        except Exception as e:
                            self.logger.error(f"处理单条数据时出错: {str(e)}")
                            continue
                    
                    # 批量flush获取ID
                    session.flush()
                    saved_records.extend(batch_saved)
                    
                    self.logger.info(f"批量处理进度: {min(i + batch_size, total_records)}/{total_records}")
        
        except Exception as e:
            self.logger.error(f"批量保存时发生错误: {str(e)}")
            raise
        
        self.logger.info(f"批量保存完成: 成功保存 {len(saved_records)}/{total_records} 条记录")
        return saved_records
    
    def get_address_by_id(self, address_id: int) -> Optional[AddressInfo]:
        """
        根据ID获取地址信息
        
        Args:
            address_id: 地址ID
            
        Returns:
            Optional[AddressInfo]: 地址信息对象，未找到返回None
        """
        self.logger.info(f"开始根据ID获取地址信息: ID={address_id}")
        try:
            address_info = AddressInfo.query.get(address_id)
            
            if address_info:
                self.logger.info(f"成功获取地址信息: ID={address_id}, 地址={address_info.address}")
                self.logger.debug(f"验证获取结果 - ID: {address_info.id}, 地址: {address_info.address}, 城市: {address_info.city}, 创建时间: {address_info.created_at}")
            else:
                self.logger.info(f"未找到地址信息: ID={address_id}")
            
            return address_info
            
        except Exception as e:
            self.logger.error(f"根据ID获取地址信息时出错: ID={address_id}, 错误: {str(e)}")
            return None
    
    def search_addresses(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 100
    ) -> List[AddressInfo]:
        """
        搜索地址信息
        
        Args:
            address: 地址关键字
            city: 城市
            state: 州/省份
            country: 国家
            limit: 返回结果数量限制
            
        Returns:
            List[AddressInfo]: 地址信息列表
        """
        # 构建搜索条件描述
        search_conditions = []
        if address:
            search_conditions.append(f"地址包含: {address}")
        if city:
            search_conditions.append(f"城市: {city}")
        if state:
            search_conditions.append(f"州/省份: {state}")
        if country:
            search_conditions.append(f"国家: {country}")
        
        search_desc = "; ".join(search_conditions) if search_conditions else "无过滤条件"
        self.logger.info(f"开始搜索地址信息: {search_desc}, 限制: {limit}")
        
        try:
            query = AddressInfo.query
            
            if address:
                query = query.filter(AddressInfo.address.contains(address))
            if city:
                query = query.filter(AddressInfo.city == city)
            if state:
                query = query.filter(AddressInfo.state == state)
            if country:
                query = query.filter(AddressInfo.country == country)
            
            results = query.limit(limit).all()
            
            self.logger.info(f"搜索完成: 找到 {len(results)} 条记录")
            self.logger.debug(f"验证搜索结果 - 总记录数: {len(results)}, 搜索条件: {search_desc}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索地址信息时出错: 搜索条件={search_desc}, 错误: {str(e)}")
            return []