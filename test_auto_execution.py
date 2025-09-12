#!/usr/bin/env python3
"""
测试自动任务执行功能

这个脚本用于测试调度器的自动任务执行功能，验证定时任务是否正常工作。
"""

import os
import sys
import time
import signal

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.scheduler.task_scheduler import get_scheduler, start_scheduler, stop_scheduler
from src.models.task import Task
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 全局变量
_scheduler = None
_shutdown_requested = False

def signal_handler(signum, frame):
    """信号处理器"""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n收到停止信号，正在优雅关闭...")

def create_test_tasks():
    """创建测试任务"""
    print("创建测试任务...")
    
    # 创建Flask应用上下文
    app = create_app('development')
    
    with app.app_context():
        # 清空现有任务
        Task.query.delete()
        db.session.commit()
        
        # 创建测试任务
        test_tasks = [
            Task(
                url="https://httpbin.org/json",
                method="GET",
                total_num=1,
                status="pending",
                timeout=10,
                retry_count=1
            ),
            Task(
                url="https://httpbin.org/xml",
                method="GET",
                total_num=2,
                status="pending",
                timeout=10,
                retry_count=1
            ),
            Task(
                url="https://httpbin.org/html",
                method="GET",
                total_num=1,
                status="pending",
                timeout=10,
                retry_count=1
            )
        ]
        
        for task in test_tasks:
            db.session.add(task)
        
        db.session.commit()
        print(f"已创建 {len(test_tasks)} 个测试任务")

def main():
    """主函数"""
    global _scheduler, _shutdown_requested
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("自动任务执行功能测试")
    print("=" * 60)
    
    try:
        # 创建测试任务
        create_test_tasks()
        
        # 获取调度器实例
        print("启动任务调度器...")
        _scheduler = get_scheduler()
        
        # 启动调度器（会自动根据配置启动自动任务执行）
        if not start_scheduler():
            print("调度器启动失败")
            return 1
        
        print("调度器启动成功！")
        print("自动任务执行已启用，每30秒执行一次")
        print("按 Ctrl+C 停止测试...")
        print("-" * 60)
        
        # 等待任务执行
        execution_count = 0
        while not _shutdown_requested:
            time.sleep(5)  # 每5秒检查一次
            execution_count += 1
            
            # 每30秒显示一次状态
            if execution_count % 6 == 0:
                print(f"[{time.strftime('%H:%M:%S')}] 调度器运行中...")
                
                # 显示当前任务状态
                app = create_app('development')
                with app.app_context():
                    total_tasks = Task.query.count()
                    completed_tasks = Task.query.filter_by(status='completed').count()
                    running_tasks = Task.query.filter_by(status='running').count()
                    failed_tasks = Task.query.filter_by(status='failed').count()
                    
                    print(f"  任务状态 - 总计: {total_tasks}, 完成: {completed_tasks}, 运行中: {running_tasks}, 失败: {failed_tasks}")
        
        print("正在停止调度器...")
        stop_scheduler(wait=True)
        print("调度器已停止")
        
        # 显示最终结果
        app = create_app('development')
        with app.app_context():
            total_tasks = Task.query.count()
            completed_tasks = Task.query.filter_by(status='completed').count()
            
            print("-" * 60)
            print("测试结果：")
            print(f"总任务数: {total_tasks}")
            print(f"已完成任务: {completed_tasks}")
            print(f"完成率: {(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "完成率: 0%")
        
        return 0
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)