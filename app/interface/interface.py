import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入必要的依赖
import gradio as gr
import os
import shutil
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 导入应用的核心组件
from app.llm import chat_with_cfo
from app.config import AppConfig
from app.interface.file_manager import (
    FileChangeHandler, 
    create_file_directories, 
    create_session_directory, 
    get_directory_files, 
    handle_file_upload, 
    generate_file_list_html
)

# 导入CSS和JS
from app.interface.ui_assets import get_css, get_ui_js, get_sidebar_js

# =====================================================================
# Gradio 用户界面部分
# =====================================================================
def create_interface():
    """创建Smart Agent的主界面"""
    with gr.Blocks(title="Smart Agent", css=get_css()) as demo:
        # 创建初始会话目录
        session_dir = create_session_directory()
        
        # 启动文件监视
        source_dirs = [
            project_root / "app" / "workspace",
            project_root / "open_manus" / "workspace"
        ]
        handler = FileChangeHandler(source_dirs, session_dir)
        observer = Observer()
        for source_dir in source_dirs:
            if source_dir.exists():
                observer.schedule(handler, str(source_dir), recursive=True)
        observer.start()
        
        # 创建状态变量
        session_dir_state = gr.State(str(session_dir))
        left_sidebar_visible = gr.State(True)
        right_sidebar_visible = gr.State(True)
        is_small_screen = gr.State(False)  # 追踪屏幕大小的状态
        
        # 顶部栏
        with gr.Row(elem_classes=["header-bar"]) as header:
            with gr.Column(elem_classes=["header-left"]):
                left_toggle_btn = gr.Button("☰", elem_classes=["sidebar-toggle"])
            
            with gr.Column(elem_classes=["header-center"]):
                gr.Markdown("## Smart Agent")
            
            with gr.Column(elem_classes=["header-right"]):
                right_toggle_btn = gr.Button("📁", elem_classes=["sidebar-toggle"])
        
        # 主体容器
        with gr.Row(elem_classes=["main-container"]) as main_container:
            # 左侧边栏
            with gr.Column(elem_classes=["left-sidebar"]) as left_sidebar:
                with gr.Column(elem_classes=["sidebar-content"]):
                    gr.Markdown("## Left Side Bar", elem_classes=["sidebar-title"])
                    gr.Markdown("Future features can be placed here, such as user management, settings, etc.")
            
            # 中央内容区
            center_content_classes = ["center-content"]
            if not left_sidebar_visible.value:
                center_content_classes.append("left-hidden")
            if not right_sidebar_visible.value:
                center_content_classes.append("right-hidden")
                
            with gr.Column(elem_classes=center_content_classes) as center_content:
                with gr.Column(elem_classes=["chat-container"]):
                    # 聊天头部
                    with gr.Row(elem_classes=["chat-header"]):
                        gr.Markdown("Below is an intelligent assistant demonstration. You can ask continuous contextual questions.")
                    
                    # 聊天区域
                    with gr.Column(elem_classes=["chatbot-area"]):
                        with gr.Column(elem_classes=["chatbot-wrapper"]):
                            # 聊天组件 - 移除头像
                            chatbot = gr.Chatbot(
                                label="Smart Agent Conversation (Continuous Chat)",
                                render=format_message,
                                show_copy_button=True,
                                avatar_images=(None, None),  # 移除头像
                                type="messages",
                                height="100%",
                                elem_classes=["chatbot-component"]  # 用于自定义样式
                            )
                            
                    # 设置区域
                    with gr.Accordion("Settings", open=False, elem_classes=["settings-container"]):
                        hide_tools_toggle = gr.Checkbox(
                            label="Hide TOOLS instruction content", 
                            value=AppConfig.HIDE_TOOLS_CONTENT,
                            info="When checked, [[TOOLS:...][...]] instruction content will be hidden in replies"
                        )
                    
                    # 状态管理组件
                    conv_state = gr.State([])  # 对话历史
                    generating_state = gr.State(False)  # 生成状态标记
                    
                    # 输入区域
                    with gr.Row(elem_classes=["input-area"]):
                        user_input = gr.Textbox(
                            label="Please enter your question",
                            placeholder="Example: How to interpret this year's financial report?", 
                            lines=1
                        )
                        
                        with gr.Column(scale=1, min_width=100):
                            send_btn = gr.Button("Send", elem_classes=["action-btn", "send-btn"])
                            stop_btn = gr.Button("Stop", visible=False, elem_classes=["action-btn", "stop-btn"])
            
            # 右侧边栏
            with gr.Column(elem_classes=["right-sidebar"]) as right_sidebar:
                with gr.Column(elem_classes=["files-area"]):
                    # 文件上传区域
                    with gr.Column(elem_classes=["upload-section"]):
                        gr.Markdown("### Upload Files", elem_classes=["sidebar-title"])
                        with gr.Column(elem_classes=["upload-area"]):
                            file_upload = gr.File(
                                label="Drag & Drop Files Here",
                                file_count="multiple",
                                type="filepath"
                            )
                    
                    # 文件浏览区域
                    with gr.Column(elem_classes=["files-section"]):
                        with gr.Row(elem_classes=["files-header"]):
                            gr.Markdown("### Files Browser", elem_classes=["sidebar-title"])
                            refresh_btn = gr.Button("🔄 Refresh", elem_classes=["refresh-btn"])
                        
                        with gr.Column(elem_classes=["files-browser"]):
                            file_list = gr.HTML()
        
        # =====================================================================
        # 事件绑定部分
        # =====================================================================
        
        # 初始化UI增强功能
        js_helper = gr.HTML(get_ui_js() + get_sidebar_js())
        
        # 初始化文件列表和窗口大小检测
        demo.load(
            fn=lambda session_dir: (refresh_file_list(session_dir), ""),
            inputs=[session_dir_state],
            outputs=[file_list, gr.HTML()]
        )
        
        # 隐藏TOOLS内容切换事件
        hide_tools_toggle.change(
            fn=update_hide_tools_setting,
            inputs=[hide_tools_toggle],
            outputs=[]
        )
        
        # 左侧边栏切换事件
        left_toggle_btn.click(
            fn=toggle_left_sidebar,
            inputs=[left_sidebar_visible, right_sidebar_visible, is_small_screen],
            outputs=[left_sidebar, center_content, left_sidebar_visible]
        )
        
        # 右侧边栏切换事件
        right_toggle_btn.click(
            fn=toggle_right_sidebar,
            inputs=[right_sidebar_visible, left_sidebar_visible, is_small_screen],
            outputs=[right_sidebar, center_content, right_sidebar_visible]
        )
        
        # 文件上传事件
        file_upload.upload(
            fn=upload_and_update,
            inputs=[file_upload, session_dir_state],
            outputs=[file_list]
        )
        
        # 文件列表刷新事件
        refresh_btn.click(
            fn=refresh_file_list,
            inputs=[session_dir_state],
            outputs=[file_list]
        )
        
        # 发送按钮点击事件
        send_event = send_btn.click(
            fn=toggle_button_visibility,
            inputs=[gr.State(True)],
            outputs=[send_btn, stop_btn],
        ).then(
            fn=respond,
            inputs=[user_input, conv_state, generating_state],
            outputs=[chatbot, conv_state, user_input, generating_state],
            queue=True
        ).then(
            fn=toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn],
        )
        
        # 停止按钮点击事件
        stop_btn.click(
            fn=stop_generation,
            inputs=[conv_state],
            outputs=[conv_state, generating_state]
        ).then(
            fn=toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn]
        )
        
        # 输入框回车事件
        user_input.submit(
            fn=toggle_button_visibility,
            inputs=[gr.State(True)],
            outputs=[send_btn, stop_btn],
        ).then(
            fn=respond,
            inputs=[user_input, conv_state, generating_state],
            outputs=[chatbot, conv_state, user_input, generating_state],
            queue=True
        ).then(
            fn=toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn],
        )
        
    return demo

# =====================================================================
# 辅助函数部分
# =====================================================================

# 更新TOOLS内容显示设置
def update_hide_tools_setting(value):
    """更新是否隐藏TOOLS指令内容的设置"""
    AppConfig.HIDE_TOOLS_CONTENT = value

# 左侧边栏切换函数
def toggle_left_sidebar(visible, right_visible, is_small):
    """切换左侧边栏显示状态"""
    if visible:
        # 当前可见，需要隐藏
        center_classes = ["center-content", "left-hidden"]
        if not right_visible:
            center_classes.append("right-hidden")
            
        return (
            gr.update(elem_classes=["left-sidebar", "hidden"]),
            gr.update(elem_classes=center_classes),
            False
        )
    else:
        # 当前隐藏，需要显示
        center_classes = ["center-content"]
        if not right_visible:
            center_classes.append("right-hidden")
        
        # 如果是小屏幕，使用全屏模式
        sidebar_classes = ["left-sidebar"]
        if is_small:
            sidebar_classes.append("fullscreen-mobile")
            
        return (
            gr.update(elem_classes=sidebar_classes),
            gr.update(elem_classes=center_classes),
            True
        )

# 右侧边栏切换函数
def toggle_right_sidebar(visible, left_visible, is_small):
    """切换右侧边栏显示状态"""
    if visible:
        # 当前可见，需要隐藏
        center_classes = ["center-content", "right-hidden"]
        if not left_visible:
            center_classes.append("left-hidden")
            
        return (
            gr.update(elem_classes=["right-sidebar", "hidden"]),
            gr.update(elem_classes=center_classes),
            False
        )
    else:
        # 当前隐藏，需要显示
        center_classes = ["center-content"]
        if not left_visible:
            center_classes.append("left-hidden")
        
        # 如果是小屏幕，使用全屏模式
        sidebar_classes = ["right-sidebar"]
        if is_small:
            sidebar_classes.append("fullscreen-mobile")
            
        return (
            gr.update(elem_classes=sidebar_classes),
            gr.update(elem_classes=center_classes),
            True
        )

# 处理文件上传并更新文件列表
def upload_and_update(files, session_dir):
    """上传文件并更新文件列表"""
    handle_file_upload(files, session_dir)
    files = get_directory_files(Path(session_dir))
    return generate_file_list_html(files)

# 刷新文件列表
def refresh_file_list(session_dir):
    """刷新文件列表"""
    files = get_directory_files(Path(session_dir))
    return generate_file_list_html(files)

# 消息格式转换
def convert_to_messages_format(conversation):
    """将对话历史转换为消息格式"""
    messages = []
    for msg in conversation:
        # 只包含用户和助手消息（跳过系统消息）
        if msg["role"] in ["user", "assistant"]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    return messages

# 消息渲染函数
def format_message(msg):
    """格式化聊天消息，增强工具进度显示"""
    # 提取消息内容
    if isinstance(msg, dict) and 'content' in msg:
        content = msg['content']
    elif isinstance(msg, tuple) and len(msg) == 2:
        content = msg[1] if msg[0] != 'assistant' else msg[0]
    else:
        content = str(msg)
    
    # 处理工具进度信息
    if "[Tool Processing Progress]" in content:
        parts = content.split("[Tool Processing Progress]", 1)
        progress_parts = parts[1].split("[Tool Execution Complete]", 1)
        progress_content = progress_parts[0].strip()
        
        formatted_content = f"""
        {parts[0]}
        <div class="tool-progress">
            <div><strong>Tool Processing Progress:</strong></div>
            <pre>{progress_content}</pre>
        </div>
        """
        
        # 添加执行摘要（如果存在）
        if len(progress_parts) > 1 and "[Tool Execution Summary]" in progress_parts[1]:
            summary_parts = progress_parts[1].split("[Tool Execution Summary]", 1)
            summary_content = summary_parts[1].strip()
            
            formatted_content += f"""
            <div class="tool-summary">
                <div><strong>Tool Execution Summary:</strong></div>
                <div>{summary_content}</div>
            </div>
            """
        elif len(progress_parts) > 1:
            formatted_content += progress_parts[1]
        
        # 返回格式化后的内容
        if isinstance(msg, dict):
            return {**msg, 'content': formatted_content}
        elif isinstance(msg, tuple):
            return (msg[0], formatted_content)
        return formatted_content
        
    # 处理工具摘要（无进度部分）
    elif "[Tool Execution Summary]" in content:
        parts = content.split("[Tool Execution Summary]", 1)
        
        formatted_content = f"""
        {parts[0]}
        <div class="tool-summary">
            <div><strong>Tool Execution Summary:</strong></div>
            <div>{parts[1]}</div>
        </div>
        """
        
        if isinstance(msg, dict):
            return {**msg, 'content': formatted_content}
        elif isinstance(msg, tuple):
            return (msg[0], formatted_content)
        return formatted_content
        
    # 处理错误消息
    elif "[Error]" in content:
        parts = content.split("[Error]", 1)
        
        formatted_content = f"""
        {parts[0]}
        <div class="error-message">
            <div><strong>Error:</strong></div>
            <div>{parts[1]}</div>
        </div>
        """
        
        if isinstance(msg, dict):
            return {**msg, 'content': formatted_content}
        elif isinstance(msg, tuple):
            return (msg[0], formatted_content)
        return formatted_content
        
    # 常规消息不需要特殊处理
    return msg

# 异步响应用户消息
async def respond(user_message, conversation, generating):
    """处理用户输入并获取助手回复"""
    # 如果已经在生成，忽略新请求
    if generating:
        yield convert_to_messages_format(conversation), conversation, user_message, generating
        return
    
    # 调用chat_with_cfo函数获取流式回复
    async for updated_conv, _debug, is_generating in chat_with_cfo(conversation, user_message):
        # 返回更新后的对话历史和状态
        yield convert_to_messages_format(updated_conv), updated_conv, "", is_generating

# 切换按钮可见性
def toggle_button_visibility(generating):
    """根据生成状态切换按钮可见性"""
    return gr.update(visible=not generating), gr.update(visible=generating)

# 停止生成
def stop_generation(conversation):
    """停止回复生成"""
    return conversation, False

# =====================================================================
# 应用入口
# =====================================================================
def main():
    """应用主函数"""
    demo = create_interface()
    # 添加应用关闭时的清理函数
    def cleanup():
        """在应用关闭时清理资源"""
        if 'observer' in globals():
            observer.stop()
            observer.join()

    # 注册清理函数
    import atexit
    atexit.register(cleanup)
    
    # 启动应用
    demo.launch()
    
    return demo

# 导出Web应用实例
web_app = create_interface()

if __name__ == "__main__":
    main()