def format_message(msg):
    """
    格式化聊天消息以增强工具进度显示
    
    Parameters:
        msg: 消息对象，格式为(user_message, assistant_message)元组
        
    Returns:
        格式化后的消息对象
    """
    if isinstance(msg, tuple) and len(msg) == 2:
        # 元组格式，msg是(user_message, assistant_message)
        # 我们只需格式化助手的消息
        content = msg[1]
    else:
        # 备用方案 - 标准格式不应发生
        content = str(msg)
    
    # 使用样式化的div替换工具处理部分
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
        
        # 如果可用，添加执行完成和摘要
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
            
        return (msg[0], formatted_content)
        
    # 处理没有进度的执行摘要
    elif "[Tool Execution Summary]" in content:
        parts = content.split("[Tool Execution Summary]", 1)
        
        formatted_content = f"""
        {parts[0]}
        <div class="tool-summary">
            <div><strong>Tool Execution Summary:</strong></div>
            <div>{parts[1]}</div>
        </div>
        """
        return (msg[0], formatted_content)
        
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
        return (msg[0], formatted_content)
        
    # 普通消息 - 不需要格式化
    return msg

def convert_to_tuples(conversation):
    """
    将对话从字典格式转换为元组格式，用于Gradio Chatbot
    
    Parameters:
        conversation (list): 对话历史，格式为字典列表
        
    Returns:
        list: 转换后的元组列表
    """
    tuples = []
    for i in range(0, len(conversation), 2):
        if i+1 < len(conversation):
            if conversation[i]["role"] == "user" and conversation[i+1]["role"] == "assistant":
                tuples.append((conversation[i]["content"], conversation[i+1]["content"]))
    return tuples