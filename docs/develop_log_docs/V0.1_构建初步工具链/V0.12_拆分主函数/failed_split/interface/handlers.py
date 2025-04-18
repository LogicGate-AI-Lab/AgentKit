import gradio as gr
import asyncio
from . import formatters

# 事件处理函数
def update_hide_tools_setting(value, config):
    """
    更新是否隐藏TOOLS指令内容的设置
    
    Parameters:
        value (bool): 是否隐藏TOOLS指令内容
        config: 配置对象
        
    Returns:
        None
    """
    config.HIDE_TOOLS_CONTENT = value

def update_tool_type(value, config):
    """
    更新工具类型设置
    
    Parameters:
        value (str): 工具类型
        config: 配置对象
        
    Returns:
        None
    """
    config.TOOL_TYPE = value.lower()

def toggle_button_visibility(generating):
    """
    根据生成状态切换按钮可见性
    
    Parameters:
        generating (bool): 是否正在生成回复
        
    Returns:
        tuple: (发送按钮更新, 停止按钮更新)
    """
    return gr.update(visible=not generating), gr.update(visible=generating)

def stop_generation(conversation):
    """
    停止回复生成
    
    Parameters:
        conversation (list): 当前对话历史
        
    Returns:
        tuple: (对话历史, 设置为False的生成状态)
    """
    return conversation, False

def respond(agent, user_message, conversation, generating):
    """
    处理用户输入消息并获取助手回复
    
    Parameters:
        agent: 代理对象，处理对话流程
        user_message (str): 用户输入消息
        conversation (list): 当前对话历史
        generating (bool): 是否正在生成回复
        
    Returns:
        tuple: (用于显示的对话历史, 存储的对话历史, 清除用户输入, 生成状态)
    """
    # 创建新的事件循环来运行异步函数
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 如果已经在生成，忽略新请求
    if generating:
        return formatters.convert_to_tuples(conversation), conversation, user_message, generating
    
    # 收集所有结果
    all_results = []
    
    async def collect_results():
        async for updated_conv, _debug, is_generating in agent.chat_with_user(conversation, user_message):
            all_results.append((updated_conv, is_generating))
    
    # 运行直到完成
    loop.run_until_complete(collect_results())
    
    # 获取最后一个结果
    if all_results:
        updated_conv, is_generating = all_results[-1]
        return formatters.convert_to_tuples(updated_conv), updated_conv, "", is_generating
    else:
        # 如果没有结果，返回原始对话
        return formatters.convert_to_tuples(conversation), conversation, user_message, generating