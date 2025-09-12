#!/usr/bin/env python3
"""
测试调度器日志记录功能的脚本

该脚本用于验证任务调度器的日志记录功能是否正常工作，包括：
- 调度器启动/关闭日志
- 任务执行统计日志
- 作业事件处理日志

作者: Claude Code
创建时间: 2025-09-10
"""

import time
import logging
from datetime import datetime

# 配置日志显示
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_simple_job():
    """简单的测试作业"""
    print(f"简单作业执行于: {datetime.now()}")
    return "success"

def test_failing_job():
    """会失败的测试作业"""
    print(f"失败作业执行于: {datetime.now()}")
    raise ValueError("这是测试用的错误")

def main():
    """主测试函数"""
    print("开始测试调度器日志记录功能...")
    
    try:
        # 导入调度器
        from src.scheduler.task_scheduler import TaskScheduler
        
        # 创建调度器实例
        print("创建调度器实例...")
        scheduler = TaskScheduler()
        
        # 启动调度器
        print("启动调度器...")
        scheduler.start()
        
        # 添加一些测试作业
        print("添加测试作业...")
        
        # 成功的作业
        scheduler.add_job(
            func=test_simple_job,
            trigger='interval',
            seconds=3,
            id='test_success_job',
            name='测试成功作业',
            max_instances=1
        )
        
        # 失败的作业
        scheduler.add_job(
            func=test_failing_job,
            trigger='interval',
            seconds=5,
            id='test_fail_job', 
            name='测试失败作业',
            max_instances=1
        )
        
        print("作业已添加，等待执行...")
        
        # 运行一段时间让作业执行
        time.sleep(15)
        
        # 手动触发统计报告
        print("手动触发统计报告...")
        scheduler.log_statistics_report()
        
        # 停止调度器
        print("停止调度器...")
        scheduler.stop()
        
        print("测试完成！")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()