# 配置管理，从key目录读取API密钥

# Standard library imports
import os

# =====================================================================
# API Client Initialization
# =====================================================================
# 从key模块导入API密钥和URL
try:
    from key.key import MAIN_APP_KEY, MAIN_APP_URL
except ImportError:
    print(f"ERROR: NO KEY CAN BE IMPORTED")
    # 设置默认值以避免运行时错误
    MAIN_APP_KEY = "default_key"
    MAIN_APP_URL = "default_url"

# =====================================================================
# Configuration Section
# =====================================================================
# 控制是否隐藏TOOLS指令内容的开关
HIDE_TOOLS_CONTENT = False

# 默认的工具类型设置
DEFAULT_TOOL_TYPE = "openmanus"

# LLM相关配置
LLM_MODEL = "deepseek-chat"
LLM_MAX_TOKENS = 512
LLM_TIMEOUT = 30

# 日志相关配置
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# 工具处理相关配置
TOOL_EXECUTION_TIMEOUT = 300  # 5 minutes