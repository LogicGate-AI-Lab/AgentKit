import gradio as gr
from . import formatters
from . import handlers

def create_ui_components(config, agent):
    """
    创建UI组件并绑定事件
    
    Parameters:
        config: 配置对象，包含UI配置选项
        agent: 代理对象，处理对话
        
    Returns:
        demo: Gradio应用对象
    """
    # 创建Gradio块
    demo = gr.Blocks(title="Smart Agent", css="""
        /* Tool processing progress styles */
        .tool-progress {
            background-color: #f5f7ff;
            border-left: 3px solid #4a6fa5;
            padding: 8px 12px;
            margin-top: 10px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
        }
        
        /* Tool execution summary styles */
        .tool-summary {
            background-color: #f0f7f0;
            border-left: 3px solid #4caf50;
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
        }
        
        /* Error message styles */
        .error-message {
            background-color: #fff0f0;
            border-left: 3px solid #ff5252;
            padding: 10px;
            margin-top: 10px;
            border-radius: 4px;
        }
    """)
    
    with demo:
        # 页面标题和描述
        gr.Markdown("## Smart Agent\nBelow is an intelligent assistant demonstration. You can ask continuous contextual questions.")

        # 聊天界面组件，使用自定义消息渲染
        chatbot = gr.Chatbot(
            label="Smart Agent Conversation (Continuous Chat)", 
            render=formatters.format_message,
            height=600,
        )
        
        # 状态管理组件
        conv_state = gr.State([])  # 初始为空列表
        generating_state = gr.State(False)  # 初始非生成状态

        # 功能设置部分
        with gr.Accordion("Settings", open=False):
            hide_tools_toggle = gr.Checkbox(
                label="Hide TOOLS instruction content", 
                value=config.HIDE_TOOLS_CONTENT,
                info="When checked, [[TOOLS:...][...]] instruction content will be hidden in replies"
            )
            
            # 添加工具类型选择
            tool_type = gr.Radio(
                choices=["OpenManus", "LangGraph"],
                value="OpenManus",
                label="Tool Library",
                info="Select which tool library to use for executing tasks"
            )
        
        # 输入和控制按钮行
        with gr.Row():
            # 用户输入文本框
            user_input = gr.Textbox(
                label="Please enter your question",
                placeholder="Example: How to interpret this year's financial report?", 
                lines=1  # 单行输入
            )
            # 发送按钮
            send_btn = gr.Button("Send")
            # 停止按钮（初始隐藏）
            stop_btn = gr.Button("Stop", visible=False)
        
        # 绑定事件处理函数
        
        # 隐藏TOOLS内容切换事件
        hide_tools_toggle.change(
            fn=lambda x: handlers.update_hide_tools_setting(x, config),
            inputs=[hide_tools_toggle],
            outputs=[]
        )
        
        # 工具类型选择事件
        tool_type.change(
            fn=lambda x: handlers.update_tool_type(x, config),
            inputs=[tool_type],
            outputs=[]
        )
        
        # 发送按钮点击事件
        send_btn.click(
            fn=handlers.toggle_button_visibility,
            inputs=[gr.State(True)],
            outputs=[send_btn, stop_btn],
        ).then(
            fn=lambda msg, conv, gen: handlers.respond(agent, msg, conv, gen),
            inputs=[user_input, conv_state, generating_state],
            outputs=[chatbot, conv_state, user_input, generating_state],
            queue=True
        ).then(
            fn=handlers.toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn],
        )
        
        # 停止按钮点击事件
        stop_btn.click(
            fn=handlers.stop_generation,
            inputs=[conv_state],
            outputs=[conv_state, generating_state]
        ).then(
            fn=handlers.toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn]
        )
        
        # 用户输入框回车键事件
        user_input.submit(
            fn=handlers.toggle_button_visibility,
            inputs=[gr.State(True)],
            outputs=[send_btn, stop_btn],
        ).then(
            fn=lambda msg, conv, gen: handlers.respond(agent, msg, conv, gen),
            inputs=[user_input, conv_state, generating_state],
            outputs=[chatbot, conv_state, user_input, generating_state],
            queue=True
        ).then(
            fn=handlers.toggle_button_visibility,
            inputs=[gr.State(False)],
            outputs=[send_btn, stop_btn],
        )
    
    return demo