# 日志配置

# Standard library imports
import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    设置日志记录系统
    
    Returns:
        tuple: (logger, log_filepath, manus_log_filepath)
    """
    from app.config import LOG_LEVEL, LOG_MAX_BYTES, LOG_BACKUP_COUNT
    
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(__file__), "log")
    os.makedirs(log_dir, exist_ok=True)

    # 生成日志文件名，格式：YYYY-MM-DD_HH-MM-SS.log
    log_filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
    log_filepath = os.path.join(log_dir, log_filename)

    # 创建特定的open_manus日志文件处理器
    manus_log_filepath = os.path.join(log_dir, f"manus_{log_filename}")

    # 配置根日志记录器 - 首先配置根日志记录器以确保全局设置生效
    root_logger = logging.getLogger()
    
    # 根据配置设置日志级别
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    root_logger.setLevel(log_level)

    # 清除任何现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建并配置控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 创建并配置文件处理器
    file_handler = RotatingFileHandler(
        log_filepath,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)  # 使用相同的格式化器
    root_logger.addHandler(file_handler)

    # 捕获警告到日志
    logging.captureWarnings(True)

    # 确保第三方库日志被捕获
    for logger_name in ['urllib3', 'browser_use', 'openai', 'asyncio']:
        third_party_logger = logging.getLogger(logger_name)
        third_party_logger.setLevel(log_level)
        # 确保传播到根日志记录器
        third_party_logger.propagate = True

    # 配置open_manus日志输出
    manus_file_handler = RotatingFileHandler(
        manus_log_filepath,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    manus_file_handler.setLevel(log_level)
    manus_file_handler.setFormatter(formatter)

    # 配置open_manus相关的日志记录器
    for logger_name in [
        'open_manus', 
        'open_manus.app.agent.base', 
        'open_manus.app.agent.manus', 
        'open_manus.app.agent.toolcall',
        'open_manus.app.llm', 
        'open_manus.app.tool'
    ]:
        try:
            manus_logger = logging.getLogger(logger_name)
            manus_logger.setLevel(log_level)
            manus_logger.addHandler(manus_file_handler)
            manus_logger.addHandler(console_handler)  # 同时输出到控制台
            # 设置为不传播到根日志记录器以避免重复记录
            manus_logger.propagate = False
        except Exception as e:
            print(f"Unable to configure {logger_name} logger: {e}")

    # 配置模块级日志记录器
    logger = logging.getLogger(__name__)

    # 记录应用程序启动日志
    logger.info(f"Application started, logs saved to: {log_filepath}")
    logger.info(f"Open Manus logs saved to: {manus_log_filepath}")
    
    return logger, log_filepath, manus_log_filepath

# 导出公共接口
__all__ = ['setup_logging']