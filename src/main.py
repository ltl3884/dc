"""
主应用运行器模块

该模块提供应用程序的入口点，负责：
- 初始化Flask应用与所有组件
- 设置调度器启动和关闭钩子
- 配置信号处理器用于优雅关闭
- 管理应用生命周期

作者: Claude Code
创建时间: 2025-09-10
"""

import os
import sys
import signal
import atexit
from typing import Optional

# 设置PyMySQL作为MySQLdb模块的别名
import pymysql
pymysql.install_as_MySQLdb()

from src.app import create_app
from src.scheduler.task_scheduler import get_scheduler, start_scheduler, stop_scheduler
from src.utils.logger import get_logger

# 全局变量
app = None
scheduler = None
logger = None
_shutdown_requested = False


def signal_handler(signum: int, frame) -> None:
    """
    信号处理器 - 处理优雅关闭
    
    Args:
        signum: 信号编号
        frame: 当前堆栈帧
    """
    global _shutdown_requested, logger
    
    if _shutdown_requested:
        logger.warning("强制关闭应用")
        sys.exit(1)
    
    _shutdown_requested = True
    logger.info(f"收到信号 {signum}，开始优雅关闭应用...")
    
    try:
        # 停止调度器
        if scheduler and scheduler.is_running:
            logger.info("正在停止任务调度器...")
            stop_scheduler(wait=True)
            logger.info("任务调度器已停止")
        
        logger.info("应用优雅关闭完成")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"优雅关闭失败: {e}")
        sys.exit(1)


def setup_signal_handlers() -> None:
    """
    设置信号处理器
    
    注册对 SIGINT (Ctrl+C) 和 SIGTERM 的处理，确保应用能够优雅关闭。
    """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info("信号处理器已设置")


def initialize_scheduler(app) -> bool:
    """
    初始化调度器
    
    Args:
        app: Flask应用实例
        
    Returns:
        bool: 初始化是否成功
    """
    global scheduler
    
    try:
        # 获取调度器实例
        scheduler = get_scheduler()
        
        # 启动调度器
        if start_scheduler():
            logger.info("任务调度器初始化成功")
            return True
        else:
            logger.error("任务调度器启动失败")
            return False
            
    except Exception as e:
        logger.error(f"调度器初始化失败: {e}")
        return False


def shutdown_scheduler() -> None:
    """
    关闭调度器
    
    在应用关闭时优雅地停止调度器。
    """
    global scheduler
    
    try:
        if scheduler and scheduler.is_running:
            logger.info("正在关闭任务调度器...")
            stop_scheduler(wait=True)
            logger.info("任务调度器已关闭")
    except Exception as e:
        logger.error(f"关闭调度器失败: {e}")


def create_and_configure_app(config_name: Optional[str] = None) -> bool:
    """
    创建并配置Flask应用
    
    Args:
        config_name: 配置名称 (development, production, testing)
        
    Returns:
        bool: 配置是否成功
    """
    global app, logger
    
    try:
        # 创建Flask应用
        app = create_app(config_name)
        logger = get_logger(__name__)
        
        logger.info("Flask应用创建成功")
        
        # 初始化调度器
        if not initialize_scheduler(app):
            logger.error("调度器初始化失败")
            return False
        
        # 设置关闭钩子
        atexit.register(shutdown_scheduler)
        
        logger.info("应用配置完成")
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"应用配置失败: {e}")
        else:
            print(f"应用配置失败: {e}")
        return False


def run_development_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = True) -> None:
    """
    运行开发服务器
    
    Args:
        host: 主机地址
        port: 端口号
        debug: 是否启用调试模式
    """
    global app, logger
    
    try:
        logger.info(f"启动开发服务器 - 主机: {host}, 端口: {port}, 调试模式: {debug}")
        
        # 运行Flask开发服务器
        app.run(host=host, port=port, debug=debug, use_reloader=False)
        
    except KeyboardInterrupt:
        logger.info("用户中断服务器运行")
    except Exception as e:
        logger.error(f"开发服务器运行失败: {e}")
        raise


def run_production_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    """
    运行生产服务器
    
    使用WSGI服务器运行应用（需要安装gunicorn或waitress）
    
    Args:
        host: 主机地址
        port: 端口号
    """
    global logger
    
    try:
        logger.info(f"启动生产服务器 - 主机: {host}, 端口: {port}")
        
        # 尝试使用gunicorn
        try:
            import gunicorn.app.base
            
            class StandaloneApplication(gunicorn.app.base.BaseApplication):
                def __init__(self, app, options=None):
                    self.options = options or {}
                    self.application = app
                    super().__init__()
                
                def load_config(self):
                    for key, value in self.options.items():
                        if key in self.cfg.settings and value is not None:
                            self.cfg.set(key.lower(), value)
                
                def load(self):
                    return self.application
            
            options = {
                'bind': f'{host}:{port}',
                'workers': 4,
                'worker_class': 'sync',
                'timeout': 30,
                'keepalive': 2,
                'max_requests': 1000,
                'max_requests_jitter': 50,
                'preload_app': True,
                'accesslog': '-',
                'errorlog': '-',
                'loglevel': 'info'
            }
            
            StandaloneApplication(app, options).run()
            
        except ImportError:
            # 如果没有gunicorn，尝试使用waitress
            try:
                from waitress import serve
                serve(app, host=host, port=port)
            except ImportError:
                logger.warning("未安装gunicorn或waitress，使用Flask开发服务器作为替代")
                run_development_server(host, port, debug=False)
                
    except KeyboardInterrupt:
        logger.info("用户中断服务器运行")
    except Exception as e:
        logger.error(f"生产服务器运行失败: {e}")
        raise


def main():
    """
    主函数 - 应用入口点
    
    负责解析命令行参数，创建应用并启动服务器。
    """
    global app, logger
    
    # 获取配置名称
    config_name = os.getenv("FLASK_ENV", "development")
    
    # 创建并配置应用
    if not create_and_configure_app(config_name):
        print("应用初始化失败，退出程序")
        sys.exit(1)
    
    # 设置信号处理器
    setup_signal_handlers()
    
    # 获取服务器配置
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    
    try:
        # 根据环境选择服务器类型
        if config_name == "production":
            logger.info("运行在生产模式")
            run_production_server(host, port)
        else:
            logger.info(f"运行在开发模式 ({config_name})")
            debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
            run_development_server(host, port, debug)
            
    except Exception as e:
        logger.error(f"服务器运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()