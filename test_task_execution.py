#!/usr/bin/env python3
"""
任务执行测试脚本

测试TaskScheduler的execute_pending_tasks方法
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.task_scheduler import TaskScheduler
from src.utils.database import init_database, get_session
from src.models.task import Task
from src.app import create_app, db
from datetime import datetime


def create_test_tasks():
    """创建测试任务"""
    print("创建测试任务...")
    
    try:
        # 使用Flask应用上下文
        app = create_app('development')
        with app.app_context():
            # 删除已存在的测试任务
            db.session.query(Task).filter(Task.url.like('%测试地址%')).delete()
            db.session.commit()
            
            # 创建测试任务
            test_tasks = [
                Task(
                    url="北京市朝阳区建国门外大街1号",
                    method="GET",
                    total_num=1,
                    visited_num=0,
                    status="pending"
                ),
                Task(
                    url="上海市浦东新区陆家嘴环路1000号",
                    method="GET", 
                    total_num=1,
                    visited_num=0,
                    status="pending"
                ),
                Task(
                    url="广州市天河区珠江新城花城大道85号",
                    method="GET",
                    total_num=1,
                    visited_num=0,
                    status="pending"
                )
            ]
            
            for task in test_tasks:
                db.session.add(task)
            
            db.session.commit()
            print(f"成功创建 {len(test_tasks)} 个测试任务")
            return True
            
    except Exception as e:
        print(f"创建测试任务失败: {e}")
        return False


def test_execute_pending_tasks():
    """测试执行任务"""
    print("\n开始测试任务执行...")
    
    try:
        # 创建Flask应用上下文
        app = create_app('development')
        with app.app_context():
            # 创建调度器
            scheduler = TaskScheduler()
            
            # 启动调度器
            if not scheduler.start():
                print("启动调度器失败")
                return False
            
            # 执行任务
            executed_count = scheduler.execute_pending_tasks()
            print(f"执行了 {executed_count} 个任务")
            
            # 停止调度器
            scheduler.stop()
            
            return executed_count > 0
        
    except Exception as e:
        print(f"测试任务执行失败: {e}")
        return False


def check_task_results():
    """检查任务执行结果"""
    print("\n检查任务执行结果...")
    
    try:
        # 使用Flask应用上下文
        app = create_app('development')
        with app.app_context():
            tasks = db.session.query(Task).filter(Task.url.like('%测试地址%')).all()
            
            completed_count = 0
            failed_count = 0
            
            for task in tasks:
                print(f"任务 {task.id}: URL={task.url}, 状态={task.status}, "
                      f"已访问={task.visited_num}, 总数量={task.total_num}")
                
                if task.status == 'completed':
                    completed_count += 1
                elif task.status == 'failed':
                    failed_count += 1
            
            print(f"\n统计结果:")
            print(f"完成任务: {completed_count}")
            print(f"失败任务: {failed_count}")
            print(f"总任务数: {len(tasks)}")
            
            return True
            
    except Exception as e:
        print(f"检查任务结果失败: {e}")
        return False


def main():
    """主函数"""
    print("=== 任务执行功能测试 ===\n")
    
    try:
        # 创建测试任务
        if not create_test_tasks():
            print("创建测试任务失败，退出测试")
            return 1
        
        # 测试任务执行
        if not test_execute_pending_tasks():
            print("任务执行测试失败")
            return 1
        
        # 检查结果
        if not check_task_results():
            print("结果检查失败")
            return 1
        
        print("\n✅ 所有测试通过！")
        return 0
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())