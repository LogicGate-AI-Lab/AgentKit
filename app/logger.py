import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# =====================================================================
# Logging Configuration Section
# =====================================================================
# More detailed logging configuration for troubleshooting
from logging.handlers import RotatingFileHandler
import os
import time
import logging


# Create log directory
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# Generate log filename in format: YYYY-MM-DD_HH-MM-SS.log
log_filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_filepath = os.path.join(log_dir, log_filename)

# Configure root logger - configure root logger first to ensure global settings take effect
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Clear any existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create and configure console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Create and configure file handler
file_handler = RotatingFileHandler(
    log_filepath,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,  # Keep 5 backup files
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)  # Use the same formatter
root_logger.addHandler(file_handler)

# Capture warnings to log
logging.captureWarnings(True)

# Ensure third-party library logs are captured
for logger_name in ['urllib3', 'browser_use', 'openai', 'asyncio']:
    third_party_logger = logging.getLogger(logger_name)
    third_party_logger.setLevel(logging.INFO)
    # Ensure propagation to root logger
    third_party_logger.propagate = True


# Configure module-level logger
logger = logging.getLogger(__name__)

# Record application startup log
logger.info(f"Application started, logs saved to: {log_filepath}")
