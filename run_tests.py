#!/usr/bin/env python3
"""
测试运行脚本

用于运行所有单元测试或特定测试模块
"""

import sys
import os
import unittest
import argparse
from typing import List


def discover_tests(test_pattern: str = "test_*.py") -> unittest.TestSuite:
    """
    发现并加载测试用例
    
    Args:
        test_pattern: 测试文件匹配模式
        
    Returns:
        unittest.TestSuite: 测试套件
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, project_root)
    
    # 发现测试
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, "tests")
    
    if not os.path.exists(start_dir):
        print(f"测试目录不存在: {start_dir}")
        return unittest.TestSuite()
    
    suite = loader.discover(start_dir, pattern=test_pattern, top_level_dir=project_root)
    return suite


def run_tests(test_pattern: str = "test_*.py", verbosity: int = 2) -> bool:
    """
    运行测试
    
    Args:
        test_pattern: 测试文件匹配模式
        verbosity: 测试输出详细程度
        
    Returns:
        bool: 测试是否全部通过
    """
    # 发现测试
    test_suite = discover_tests(test_pattern)
    
    if test_suite.countTestCases() == 0:
        print(f"未找到匹配的测试用例: {test_pattern}")
        return False
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


def run_specific_test(test_module: str, verbosity: int = 2) -> bool:
    """
    运行特定测试模块
    
    Args:
        test_module: 测试模块名称（如 test_task_model）
        verbosity: 测试输出详细程度
        
    Returns:
        bool: 测试是否全部通过
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    try:
        # 导入测试模块
        module_path = f"tests.{test_module}"
        __import__(module_path)
        
        # 加载测试
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_path)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"无法导入测试模块: {module_path}")
        print(f"错误信息: {e}")
        return False
    except Exception as e:
        print(f"运行测试模块时出错: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行地址爬虫项目的单元测试")
    parser.add_argument(
        "--pattern", 
        "-p", 
        default="test_*.py",
        help="测试文件匹配模式 (默认: test_*.py)"
    )
    parser.add_argument(
        "--module", 
        "-m",
        help="运行特定的测试模块 (例如: test_task_model)"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true",
        help="显示详细的测试输出"
    )
    parser.add_argument(
        "--quiet", 
        "-q", 
        action="store_true",
        help="安静模式，只显示错误信息"
    )
    
    args = parser.parse_args()
    
    # 设置输出详细程度
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    print("=== 地址爬虫项目单元测试 ===\n")
    
    try:
        if args.module:
            # 运行特定模块
            print(f"运行测试模块: {args.module}")
            success = run_specific_test(args.module, verbosity)
        else:
            # 运行所有测试
            print(f"运行测试模式: {args.pattern}")
            success = run_tests(args.pattern, verbosity)
        
        if success:
            print("\n✅ 所有测试通过！")
            return 0
        else:
            print("\n❌ 测试失败！")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n测试运行过程中发生错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())