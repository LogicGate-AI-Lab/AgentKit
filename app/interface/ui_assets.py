"""
ui_assets.py
提供UI资源加载和管理功能
"""

import os
from pathlib import Path

# 获取当前文件所在目录
CURRENT_DIR = Path(__file__).resolve().parent
STATIC_DIR = CURRENT_DIR / "static"

def get_css_path():
    """获取CSS文件路径"""
    return STATIC_DIR / "styles.css"

def get_js_path(filename):
    """获取JS文件路径"""
    return STATIC_DIR / filename

def read_file_content(file_path):
    """读取文件内容"""
    if not os.path.exists(file_path):
        print(f"警告: 文件 {file_path} 不存在")
        return ""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_css():
    """获取CSS内容"""
    css_path = get_css_path()
    return read_file_content(css_path)

def get_ui_js():
    """获取UI工具JS内容"""
    js_path = get_js_path("ui_utils.js")
    return f"<script>{read_file_content(js_path)}</script>"

def get_sidebar_js():
    """获取侧边栏JS内容"""
    js_path = get_js_path("sidebar_handlers.js")
    return f"<script>{read_file_content(js_path)}</script>"

def ensure_static_dir():
    """确保静态资源目录存在"""
    if not STATIC_DIR.exists():
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        print(f"已创建静态资源目录: {STATIC_DIR}")

def create_default_assets():
    """创建默认资源文件（如果不存在）"""
    ensure_static_dir()
    
    # 默认CSS
    css_path = get_css_path()
    if not css_path.exists():
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write("/* 默认样式 */\nbody { background-color: #121212; color: #f5f5f5; }")
        print(f"已创建默认CSS文件: {css_path}")
    
    # 默认JS
    for js_file in ["ui_utils.js", "sidebar_handlers.js"]:
        js_path = get_js_path(js_file)
        if not js_path.exists():
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(f"// 默认 {js_file}\nconsole.log('加载 {js_file}');")
            print(f"已创建默认JS文件: {js_path}")

# 初始化时确保静态资源目录和文件存在
create_default_assets()