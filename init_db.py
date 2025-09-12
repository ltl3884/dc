#!/usr/bin/env python3
"""
数据库初始化脚本

创建所有数据库表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.utils.database import init_database


def main():
    """主函数"""
    print("=== 数据库初始化 ===\n")
    
    try:
        # 创建Flask应用
        print("创建Flask应用...")
        app = create_app()
        
        # 初始化数据库连接
        print("初始化数据库连接...")
        init_database()
        
        # 创建所有表
        print("创建数据库表...")
        with app.app_context():
            # 导入所有模型以确保它们被注册
            from src.models.task import Task
            from src.models.address_info import AddressInfo
            
            db.create_all()
            db.session.commit()
        
        print("✅ 数据库初始化成功！")
        return 0
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())