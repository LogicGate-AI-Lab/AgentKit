import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# =====================================================================
# Configuration Section
# =====================================================================
# Switch to control whether to hide TOOLS instruction content
class AppConfig:
    HIDE_TOOLS_CONTENT = False


# =====================================================================
# API Client Initialization
# =====================================================================
# Initialize OpenAI client, configured to use DeepSeek's API service
# Note: API key is hardcoded; in production, use environment variables or config files
# IMPORT APP MAIN KEY
from openai import OpenAI

try:
    from key.key import MAIN_APP_KEY, MAIN_APP_URL
except ImportError:
    print(f"ERROR: NO KEY CAN BE IMPORTED")
    # 加这两个空字符串是在拆分模块的时候，防止其他script调用的时候出问题
    MAIN_APP_KEY = ""
    MAIN_APP_URL = "" 


client = OpenAI(
    api_key=MAIN_APP_KEY,
    base_url=MAIN_APP_URL
)