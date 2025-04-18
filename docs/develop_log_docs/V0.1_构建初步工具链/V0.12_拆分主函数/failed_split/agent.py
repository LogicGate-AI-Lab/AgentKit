# Standard library imports
import asyncio
import logging

# 导入配置和服务
from app.config import HIDE_TOOLS_CONTENT
from app.llm_service import llm_service
from app.tool_manager.processor import ToolsProcessor

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

class Agent:
    """代理类，管理与用户的对话和工具调用"""
    
    def __init__(self):
        """初始化代理"""
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self):
        """获取系统提示"""
        return """
        You are a professional, patient, knowledgeable and intelligent assistant.
        Your areas of expertise include Finance, Pharmaceuticals, Computer Science, and other professional domains.
        Users will ask you questions, and you can answer them.
        You can have normal conversations with users, answering whatever they ask, just remember you're a professional assistant.
        If you don't know the answer, it's okay to say you're not certain.

        【About You】
        Your role: A very smart Agent
        Your name: Users can give you one, otherwise you're just Smart Agent
        What you can do: You're an AI Agent with an LLM core that can use tools, with expertise in multiple domains including Finance, Pharmaceuticals, and Computer Science.
        Your strength is utilizing specialized tools to complete complex tasks in professional domains.
        Your current LLM core is: DeepSeek
        Your current tools library (TOOLS) is: OpenManus
        Languages you're proficient in: Chinese, English

        【About the Tools Library (TOOLS)】
        When replying to users, you can respond normally. Only when you think a task requires using the tools library (TOOLS) should you activate your tools.
        These tasks include but are not limited to:
        1. Using a browser to search for information (LLM cores have time limitations, but by searching yourself you can get the latest information)
        2. Operating a browser to do things (like looking up a file, etc.)
        3. Downloading files
        4. Performing professional analysis on files

        User messages are sent directly to you, but your replies go through a filter that can recognize key information and activate the tools library TOOLS.
        You can write the tool operations you want to perform in hidden statements.
        Your answers will contain hidden responses at the end of each dialogue segment, wrapped in special symbols.
        Hidden response format: [[TOOLS:TRUE/FALSE][hidden content]]
        Example responses:
        "Would you like to check the latest Tesla stock information? I can help you look that up. [[TOOLS:TRUE][Search for the latest Tesla stock information]]"
        "I know the answer to your question, no need for special search. [[TOOLS:FALSE][none]]"
        "I can help you search and download the paper Attention is All You Need [[TOOLS:TRUE][Use browser to search for the paper Attention is All You Need and find the pdf file and download it]]"
        "Let me help you organize Tesla's latest financial report [[TOOLS:TRUE][Search and download Tesla's latest financial report]]"
        "Your question is simple, it can be calculated using Excel. I'll help you calculate it. [[TOOLS:TRUE][Use Excel to calculate the user's requested data...]]"
        "I know the answer to your question, no need for special search. [[TOOLS:FALSE][none]]"

        Always include [[TOOLS STATUS][PROMPT]]
        Please always mark [[TOOLS STATUS][PROMPT]] at the end of your response
        For PROMPT with specific content, please include specific tool requests and the content of the request in the PROMPT.
        """
    
    async def chat_with_user(self, conversation, user_message, collect_all=False):
        """
        与用户进行对话的异步生成器函数
        
        Parameters:
            conversation (list): 当前对话历史
            user_message (str): 用户当前输入的消息
            collect_all (bool): 是否收集所有中间结果，用于非流式处理
            
        Generator Returns:
            tuple: (更新的对话历史, 调试信息(未使用), 生成状态)
        """
        # 如果不需要收集所有结果，就正常使用生成器
        if not collect_all:
            # 复制对话历史以避免修改原始列表
            updated_conv = list(conversation)
            
            # 将用户的新消息添加到对话历史中
            updated_conv.append({"role": "user", "content": user_message})

            # 构造完整的消息列表，包括系统提示和对话历史
            messages = [{"role": "system", "content": self.system_prompt}] + updated_conv

            try:
                # 获取流式响应
                partial_response = []
                
                async for content in llm_service.generate_streaming_response(messages):
                    if content:
                        # 将新内容添加到部分响应中
                        partial_response.append(content)
                        current_text = "".join(partial_response)
                        
                        # 处理对话历史：如果最后一条消息来自用户，添加助手回复；否则更新助手回复
                        if updated_conv[-1]["role"] == "user":
                            updated_conv.append({"role": "assistant", "content": current_text})
                        else:
                            updated_conv[-1]["content"] = current_text

                        # 返回更新的对话历史和生成状态
                        yield updated_conv, "", True
            except Exception as e:
                # 捕获API调用异常，将错误消息添加到对话历史并返回
                updated_conv.append({"role": "assistant", "content": f"Smart Agent: Interface call exception: {e}"})
                yield updated_conv, "", False  # 返回更新的对话历史，无调试信息，非生成状态
                return
            
            # 完整的LLM响应
            final_response = "".join(partial_response)
            
            # 检查是否需要处理工具
            if "[[TOOLS:TRUE" in final_response:
                # 提取工具指令
                cleaned_message, tools_status, tools_content = ToolsProcessor.extract_tools_content(final_response)
                
                if tools_status:
                    # 显示工具处理已开始
                    if updated_conv[-1]["role"] == "assistant":
                        updated_conv[-1]["content"] = f"{cleaned_message}\n\n[Tool Processing Started...]"
                    else:
                        updated_conv.append({"role": "assistant", "content": f"{cleaned_message}\n\n[Tool Processing Started...]"})
                    
                    # 返回更新，显示工具处理已开始
                    yield updated_conv, "", True
                    
                    # 设置进度跟踪
                    progress_updates = []
                    
                    # 进度回调函数
                    def progress_handler(message):
                        progress_updates.append(message)
                        # 实时更新对话中的进度
                        if updated_conv[-1]["role"] == "assistant":
                            current_content = updated_conv[-1]["content"]
                            if "[Tool Processing Progress]" not in current_content:
                                updated_content = f"{current_content}\n\n[Tool Processing Progress]\n{message}"
                            else:
                                parts = current_content.split("[Tool Processing Progress]")
                                updated_content = f"{parts[0]}[Tool Processing Progress]{parts[1]}\n{message}"
                            
                            updated_conv[-1]["content"] = updated_content
                            # 我们不能直接在这里yield - 我们将存储更新并稍后处理它们
                    
                    # 处理带有进度跟踪的工具请求
                    tools_result = await ToolsProcessor.process_tools_request_async_with_progress(
                        tools_content, progress_callback=progress_handler
                    )
                    
                    # 工具执行后，用最新进度更新对话
                    if updated_conv[-1]["role"] == "assistant":
                        current_content = updated_conv[-1]["content"]
                        if "[Tool Processing Progress]" in current_content:
                            progress_text = "\n".join(progress_updates)
                            parts = current_content.split("[Tool Processing Progress]")
                            updated_content = f"{parts[0]}[Tool Processing Progress]\n{progress_text}\n\n[Tool Execution Complete]"
                        else:
                            progress_text = "\n".join(progress_updates)
                            updated_content = f"{current_content}\n\n[Tool Processing Progress]\n{progress_text}\n\n[Tool Execution Complete]"
                        
                        updated_conv[-1]["content"] = updated_content
                        yield updated_conv, "", True
                    
                    # 现在生成工具结果的摘要
                    summary_prompt = f"""
                    You have just used tools to accomplish a task for the user. 
                    Here is the original request: "{user_message}"
                    
                    The tools executed with the following result:
                    {tools_result}
                    
                    Please provide a clear, concise, and helpful summary of:
                    1. What tools were used and why
                    2. What was accomplished
                    3. Key findings or insights from the tool execution
                    4. Any relevant next steps or recommendations
                    
                    Format your response as a professional summary that focuses on the most important information.
                    """
                    
                    # 添加摘要请求到消息中
                    summary_messages = [{"role": "system", "content": self.system_prompt}] + [
                        {"role": "assistant", "content": cleaned_message},
                        {"role": "user", "content": summary_prompt}
                    ]
                    
                    # 更新UI以显示正在生成摘要
                    if updated_conv[-1]["role"] == "assistant":
                        current_content = updated_conv[-1]["content"]
                        updated_conv[-1]["content"] = f"{current_content}\n\n[Generating Summary...]"
                        yield updated_conv, "", True
                    
                    try:
                        # 获取摘要
                        final_summary = await llm_service.generate_response(summary_messages)
                        
                        # 更新对话中的摘要
                        current_content = updated_conv[-1]["content"]
                        if "[Generating Summary...]" in current_content:
                            parts = current_content.split("[Generating Summary...]")
                            updated_conv[-1]["content"] = f"{parts[0]}\n\n[Tool Execution Summary]\n{final_summary}"
                        else:
                            updated_conv[-1]["content"] = f"{current_content}\n\n[Tool Execution Summary]\n{final_summary}"
                        
                        yield updated_conv, "", True
                        
                        # 使用工具结果和摘要格式化最终处理的响应
                        processed_response = f"""
{cleaned_message}

[Tool Execution Complete]

[Tool Execution Summary]
{final_summary}
"""
                        
                    except Exception as e:
                        logger.error(f"Error generating summary: {e}")
                        # 如果摘要生成失败，使用更简单的格式
                        processed_response = f"""
{cleaned_message}

[Tool Execution Complete]

[Tool Results]
{tools_result}

[Note: Summary generation failed - {str(e)}]
"""
                else:
                    # 如果没有使用工具（FALSE），只是正常处理消息
                    processed_response = ToolsProcessor.process_message(final_response)
            else:
                # 如果根本没有工具标记，照原样使用响应
                processed_response = final_response
            
            # 用处理后的响应更新最终的助手消息
            if updated_conv[-1]["role"] == "assistant":
                updated_conv[-1]["content"] = processed_response
            else:
                updated_conv.append({"role": "assistant", "content": processed_response})
            
            logger.info(f"🧾 processed_response = {processed_response[:100]}..." if len(processed_response) > 100 else f"🧾 processed_response = {processed_response}")
            logger.info(f"📝 updated_conv[-1] = {updated_conv[-1]}")
            logger.info(f"📤 yield to frontend: {updated_conv[-1]['content'][:100]}..." if len(updated_conv[-1]['content']) > 100 else f"📤 yield to frontend: {updated_conv[-1]['content']}")
            
            # 最终返回完整的对话历史，生成结束
            yield updated_conv, "", False
        else:
            # 收集模式：运行所有生成步骤，但只返回最终结果
            results = []
            async for result in self.chat_with_user(conversation, user_message, collect_all=False):
                results.append(result)
            
            if results:
                # 只返回最终结果
                yield results[-1]
            else:
                # 如果没有结果，返回初始状态
                updated_conv = list(conversation)
                updated_conv.append({"role": "user", "content": user_message})
                yield updated_conv, "", False

# 创建代理实例
agent = Agent()

# 导出公共接口
__all__ = ['Agent', 'agent']