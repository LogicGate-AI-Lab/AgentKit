# Standard library imports
import sys
from pathlib import Path

# Add project root directory to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 导入日志设置
from app.logger_setup import setup_logging

# 导入配置
from app.config import HIDE_TOOLS_CONTENT, DEFAULT_TOOL_TYPE

# 导入代理
from app.agent import agent

# 导入UI组件
from app.interface import create_ui_components

def main():
    """主程序入口点，创建并启动应用"""
    # 设置日志
    logger, _, _ = setup_logging()
    
    # 创建配置对象（暂时使用简单的类，未来可扩展）
    class Config:
        HIDE_TOOLS_CONTENT = HIDE_TOOLS_CONTENT
        TOOL_TYPE = DEFAULT_TOOL_TYPE
    
    config_obj = Config()
    
    # 创建UI组件并绑定事件（事件绑定现在在create_ui_components内部完成）
    demo = create_ui_components(config_obj, agent)
    
    # 启用Gradio队列功能，支持并发请求处理
    demo.queue()
    
    # 启动Web服务
    logger.info("Starting web service...")
    demo.launch()

if __name__ == "__main__":
    main()