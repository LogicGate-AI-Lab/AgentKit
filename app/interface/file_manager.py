import os
import shutil
from pathlib import Path
from datetime import datetime
from watchdog.events import FileSystemEventHandler

# 项目根目录路径
project_root = Path(__file__).resolve().parent.parent.parent

# =====================================================================
# 文件管理功能
# =====================================================================

# 创建文件存储目录
def create_file_directories():
    """创建文件存储目录结构"""
    app_files_dir = project_root / "app" / "files"
    if not app_files_dir.exists():
        app_files_dir.mkdir(parents=True, exist_ok=True)
    return app_files_dir

# 创建会话文件夹
def create_session_directory():
    """基于时间戳创建会话文件夹"""
    app_files_dir = create_file_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = app_files_dir / f"session_{timestamp}"
    if not session_dir.exists():
        session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir

# 文件监视处理器
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, source_dirs, target_dir):
        """初始化文件监视处理器
        
        Args:
            source_dirs (list): 要监视的源目录列表
            target_dir (Path): 目标目录(会话目录)
        """
        self.source_dirs = source_dirs
        self.target_dir = target_dir
        # 记录初始文件状态，避免复制已存在的文件
        self.initial_files = {}
        for source_dir in source_dirs:
            self.initial_files[str(source_dir)] = set()
            if source_dir.exists():
                for file_path in source_dir.glob('**/*'):
                    if file_path.is_file():
                        self.initial_files[str(source_dir)].add(str(file_path))
    
    def on_created(self, event):
        """当检测到新文件创建时触发"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            # 检查文件是否在监视的目录中
            for source_dir in self.source_dirs:
                if str(source_dir) in str(file_path) and str(file_path) not in self.initial_files[str(source_dir)]:
                    # 创建相对路径，保持文件夹结构
                    rel_path = file_path.relative_to(source_dir)
                    target_path = self.target_dir / rel_path
                    
                    # 确保目标目录存在
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    try:
                        shutil.copy2(file_path, target_path)
                        print(f"文件已复制: {file_path} -> {target_path}")
                    except Exception as e:
                        print(f"复制文件失败: {e}")
                    break

# 获取指定目录下的文件列表
def get_directory_files(directory):
    """获取目录中的文件列表
    
    Args:
        directory (Path): 要扫描的目录
    
    Returns:
        list: 文件列表，每个元素是 (文件名, 文件路径)
    """
    files = []
    if directory.exists():
        for file_path in sorted(directory.glob('**/*')):
            if file_path.is_file():
                # 计算相对路径，显示更友好
                rel_path = file_path.relative_to(directory)
                files.append((str(rel_path), str(file_path)))
    return files

# 处理文件上传
def handle_file_upload(files, session_dir):
    """处理文件上传逻辑
    
    Args:
        files (list): 上传的文件列表
        session_dir (str): 会话目录路径
    
    Returns:
        list: 更新后的文件列表
    """
    session_dir_path = Path(session_dir)
    
    # 确保目录存在
    if not session_dir_path.exists():
        session_dir_path.mkdir(parents=True, exist_ok=True)
    
    # 保存上传的文件
    for file in files:
        if not file or not hasattr(file, 'name'):
            continue
            
        file_name = Path(file.name).name
        target_path = session_dir_path / file_name
        
        # 复制文件
        try:
            shutil.copy2(file.name, target_path)
        except Exception as e:
            print(f"复制文件失败: {e}")
    
    # 返回更新后的文件列表
    return get_directory_files(session_dir_path)

# 格式化文件大小
def format_size(size_bytes):
    """格式化文件大小为易读的形式
    
    Args:
        size_bytes (int): 文件大小（字节）
    
    Returns:
        str: 格式化后的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            if unit == 'B':
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024

# 获取文件图标
def get_file_icon(ext):
    """根据文件扩展名返回相应图标
    
    Args:
        ext (str): 文件扩展名
    
    Returns:
        str: 表示图标的字符
    """
    ext = ext.lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
        return '🖼️'
    elif ext in ['.doc', '.docx', '.odt']:
        return '📄'
    elif ext in ['.xls', '.xlsx', '.ods']:
        return '📊'
    elif ext in ['.ppt', '.pptx', '.odp']:
        return '📑'
    elif ext in ['.pdf']:
        return '📕'
    elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
        return '🗜️'
    elif ext in ['.txt', '.md', '.rtf']:
        return '📝'
    elif ext in ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php']:
        return '💻'
    else:
        return '📄'

# 生成文件列表HTML
def generate_file_list_html(files):
    """生成文件列表的HTML表示
    
    Args:
        files (list): 文件列表, [(name, path), ...]
    
    Returns:
        str: HTML字符串
    """
    if not files:
        return """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px 0; color: #9ca3af;">
            <div style="font-size: 32px; margin-bottom: 10px; opacity: 0.5;">📁</div>
            <div style="font-size: 14px; margin-bottom: 5px;">NO FILE NOW</div>
            <div style="font-size: 12px; color: #d1d5db;">WAITING FOR UPLOADING OR AI's Generating</div>
        </div>
        """
    
    html = '<div style="margin-top: 10px;">'
    
    # 按文件夹分组
    folders = {}
    for file_name, file_path in files:
        path_parts = Path(file_name).parts
        if len(path_parts) > 1:  # 有子文件夹
            folder = path_parts[0]
            if folder not in folders:
                folders[folder] = []
            folders[folder].append((file_name, file_path))
        else:  # 根目录文件
            if '' not in folders:
                folders[''] = []
            folders[''].append((file_name, file_path))
    
    # 首先添加根目录文件
    if '' in folders:
        for file_name, file_path in folders['']:
            file_size = format_size(os.path.getsize(file_path))
            file_ext = os.path.splitext(file_name)[1].lower()
            
            # 根据扩展名设置图标
            icon = get_file_icon(file_ext)
            
            html += f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 6px; margin-bottom: 4px; transition: background-color 0.2s ease; border-bottom: 1px solid #eee;">
                <div style="display: flex; align-items: center; min-width: 0; flex: 1;">
                    <div style="font-size: 16px; margin-right: 10px; flex-shrink: 0;">{icon}</div>
                    <div style="font-size: 13px; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">{file_name}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-left: 8px; flex-shrink: 0;">{file_size}</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <a href="file={file_path}" target="_blank" download style="width: 28px; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #6b7280; transition: background-color 0.2s ease, color 0.2s ease; cursor: pointer; text-decoration: none;">
                        <span style="font-size: 14px;">⬇️</span>
                    </a>
                </div>
            </div>
            """
    
    # 然后添加文件夹
    for folder_name, folder_files in folders.items():
        if folder_name == '':
            continue  # 跳过根目录
            
        # 添加文件夹标题
        html += f"""
        <div style="display: flex; align-items: center; padding: 8px 5px; margin-top: 10px; border-radius: 6px; background-color: rgba(229, 231, 235, 0.3);">
            <div style="margin-right: 8px; color: #4b5563;">📁</div>
            <div style="font-size: 14px; font-weight: 500; color: #374151;">{folder_name}</div>
        </div>
        """
        
        # 添加文件夹下的文件
        for file_name, file_path in folder_files:
            # 去掉文件夹前缀，只显示文件名
            display_name = Path(file_name).name
            file_size = format_size(os.path.getsize(file_path))
            file_ext = os.path.splitext(display_name)[1].lower()
            
            # 根据扩展名设置图标
            icon = get_file_icon(file_ext)
            
            html += f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 6px; margin-bottom: 4px; transition: background-color 0.2s ease; border-bottom: 1px solid #eee;">
                <div style="display: flex; align-items: center; min-width: 0; flex: 1;">
                    <div style="font-size: 16px; margin-right: 10px; flex-shrink: 0;">{icon}</div>
                    <div style="font-size: 13px; color: #374151; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">{display_name}</div>
                    <div style="font-size: 12px; color: #9ca3af; margin-left: 8px; flex-shrink: 0;">{file_size}</div>
                </div>
                <div style="display: flex; align-items: center;">
                    <a href="file={file_path}" target="_blank" download style="width: 28px; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #6b7280; transition: background-color 0.2s ease, color 0.2s ease; cursor: pointer; text-decoration: none;">
                        <span style="font-size: 14px;">⬇️</span>
                    </a>
                </div>
            </div>
            """
    
    html += '</div>'
    return html