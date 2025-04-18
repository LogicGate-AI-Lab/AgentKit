import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))



from app.interface.interface import web_app # interface - gradio

# =====================================================================
# Application Launch Section
# =====================================================================
if __name__=="__main__":
    web_app.queue() # Enable Gradio queue functionality, support concurrent request processing
    web_app.launch() # Start web service
