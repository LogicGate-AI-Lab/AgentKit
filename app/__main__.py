# 标准库导入
import asyncio
import logging
import os
import time
import re
import sys
from pathlib import Path

# 第三方库导入
import gradio as gr
from openai import OpenAI

# 添加项目根目录到Python路径，确保可以导入open_manus模块
project_root = Path(__file__).parent.parent  # 假设当前文件是在app目录下
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 本地应用导入
try:
    from open_manus.app.agent.manus import Manus
    from open_manus.app.logger import logger as manus_logger
except ImportError as e:
    print(f"警告: 无法导入open_manus模块: {e}")
    # 创建一个模拟的Manus类以避免运行时错误
    class Manus:
        async def run(self, prompt):
            print(f"模拟运行Manus: {prompt}")
            return f"模拟Manus结果: {prompt}"
        
        async def cleanup(self):
            print("模拟清理Manus资源")


# =====================================================================
# API客户端初始化部分
# =====================================================================
# 初始化OpenAI客户端，配置为使用DeepSeek的API服务
# 注意：这里的API密钥是硬编码的，在实际应用中应使用环境变量或配置文件
# IMPORT APP MAIN KEY
try:
    from key.key import MAIN_APP_KEY, MAIN_APP_URL
except ImportError:
    print(f"ERROR: NO KEY CAN BE IMPORTED")


client = OpenAI(
    api_key=MAIN_APP_KEY,
    base_url=MAIN_APP_URL
)

# =====================================================================
# 配置部分
# =====================================================================
# 用于控制是否隐藏TOOLS指令内容的开关
HIDE_TOOLS_CONTENT = False


# =====================================================================
# 日志配置部分
# =====================================================================
# 使用更详细的日志配置，方便排查问题
from logging.handlers import RotatingFileHandler

# 创建日志目录
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# 生成日志文件名，格式为: YYYY-MM-DD_HH-MM-SS.log
log_filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_filepath = os.path.join(log_dir, log_filename)

# 创建专门的open_manus日志文件处理器
manus_log_filepath = os.path.join(log_dir, f"manus_{log_filename}")

# 配置根日志记录器 - 先配置根记录器，确保全局设置生效
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 清除任何现有的处理器
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 创建和配置控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# 创建和配置文件处理器
file_handler = RotatingFileHandler(
    log_filepath,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,  # 保留5个备份文件
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)  # 使用相同的格式器
root_logger.addHandler(file_handler)

# 捕获警告信息到日志
logging.captureWarnings(True)

# 确保第三方库的日志也能被捕获
for logger_name in ['urllib3', 'browser_use', 'openai', 'asyncio']:
    third_party_logger = logging.getLogger(logger_name)
    third_party_logger.setLevel(logging.INFO)
    # 确保传播到根记录器
    third_party_logger.propagate = True

# 配置open_manus的日志输出
manus_file_handler = RotatingFileHandler(
    manus_log_filepath,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
manus_file_handler.setLevel(logging.INFO)
manus_file_handler.setFormatter(formatter)

# 配置open_manus相关的日志记录器
for logger_name in [
    'open_manus', 
    'open_manus.app.agent.base', 
    'open_manus.app.agent.manus', 
    'open_manus.app.agent.toolcall',
    'open_manus.app.llm', 
    'open_manus.app.tool'
]:
    try:
        manus_logger = logging.getLogger(logger_name)
        manus_logger.setLevel(logging.INFO)
        manus_logger.addHandler(manus_file_handler)
        manus_logger.addHandler(console_handler)  # 同时输出到控制台
        # 设置为不传播到根记录器，避免重复记录
        manus_logger.propagate = False
    except Exception as e:
        print(f"无法配置{logger_name}日志记录器: {e}")

# 配置模块级别的日志记录器
logger = logging.getLogger(__name__)

# 记录应用启动日志
logger.info(f"应用启动，日志保存至: {log_filepath}")
logger.info(f"Open Manus日志保存至: {manus_log_filepath}")


# =====================================================================
# 工具处理模块
# =====================================================================
class ToolsProcessor:
    """
    处理LLM回复中工具相关内容的类
    
    这个类负责提取并处理LLM回复中的TOOLS指令，并根据指令状态决定后续操作
    """
    
    @staticmethod
    def extract_tools_content(message):
        """从消息中提取TOOLS指令内容"""
        # 使用正则表达式匹配TOOLS指令格式
        import re
        pattern = r'\[\[TOOLS:(TRUE|FALSE)\]\[(.*?)\]\]'
        match = re.search(pattern, message, re.DOTALL)
        
        if match:
            tools_status = match.group(1) == "TRUE"  # 提取TOOLS状态
            tools_content = match.group(2)  # 提取TOOLS内容
            
            # 调试输出以验证内容提取
            logger.info(f"提取的工具状态: {tools_status}")
            logger.info(f"提取的工具内容: {tools_content}")
            
            # 根据HIDE_TOOLS_CONTENT决定是否从消息中移除TOOLS指令
            if HIDE_TOOLS_CONTENT:
                # 移除匹配到的TOOLS指令部分
                cleaned_message = re.sub(pattern, '', message, flags=re.DOTALL).strip()
            else:
                # 保留原始消息
                cleaned_message = message
                
            return cleaned_message, tools_status, tools_content
        
        # 如果没有匹配到TOOLS指令，返回原始消息和默认值
        logger.warning("未检测到TOOLS指令内容")
        return message, False, ""
    
    @staticmethod
    def configure_manus_logging():
        """配置open_manus的日志系统，将其输出转发到主程序"""
        try:
            # 获取主程序的根日志记录器
            root_logger = logging.getLogger()
            
            # 尝试导入open_manus日志模块
            import importlib
            
            # 获取各个需要处理的open_manus模块的日志记录器
            loggers_to_configure = [
                'open_manus',
                'open_manus.app.agent.base',
                'open_manus.app.agent.manus',
                'open_manus.app.agent.toolcall',
                'open_manus.app.llm',
                'open_manus.app.tool',
                'browser_use',
                'root'
            ]
            
            # 保存原始配置以便稍后还原
            original_configs = {}
            
            for logger_name in loggers_to_configure:
                try:
                    manus_logger = logging.getLogger(logger_name)
                    
                    # 保存原始配置
                    original_configs[logger_name] = {
                        'level': manus_logger.level,
                        'handlers': list(manus_logger.handlers),
                        'propagate': manus_logger.propagate
                    }
                    
                    # 设置日志级别为INFO或更高
                    manus_logger.setLevel(logging.INFO)
                    
                    # 确保日志能传播到根记录器
                    manus_logger.propagate = True
                    
                    # 添加主程序的处理器
                    for handler in root_logger.handlers:
                        if handler not in manus_logger.handlers:
                            # 如果是文件处理器，创建一个新的处理器指向同一个文件
                            # 这样可以避免潜在的文件锁定问题
                            if isinstance(handler, logging.FileHandler):
                                try:
                                    file_path = handler.baseFilename
                                    new_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
                                    new_handler.setFormatter(handler.formatter)
                                    new_handler.setLevel(handler.level)
                                    manus_logger.addHandler(new_handler)
                                except (AttributeError, IOError) as e:
                                    logger.warning(f"为{logger_name}创建文件处理器时出错: {e}")
                            else:
                                # 对于非文件处理器(如控制台处理器)，直接添加引用
                                manus_logger.addHandler(handler)
                    
                except Exception as e:
                    logger.warning(f"配置{logger_name}日志时出错: {e}")
            
            logger.info("已配置Open Manus日志转发到主程序")
            return original_configs
            
        except ImportError as e:
            logger.warning(f"无法导入Open Manus日志模块: {e}")
            return {}
        except Exception as e:
            logger.warning(f"配置Open Manus日志时出错: {e}")
            return {}
        


    @staticmethod
    def restore_manus_logging(original_configs):
        """恢复open_manus的原始日志配置"""
        if not original_configs:
            return
            
        for logger_name, config in original_configs.items():
            try:
                manus_logger = logging.getLogger(logger_name)
                
                # 恢复原始级别
                manus_logger.setLevel(config['level'])
                
                # 恢复原始处理器
                for handler in list(manus_logger.handlers):
                    if handler not in config['handlers']:
                        manus_logger.removeHandler(handler)
                
                # 恢复传播设置
                manus_logger.propagate = config['propagate']
                
            except Exception as e:
                logger.warning(f"恢复{logger_name}日志配置时出错: {e}")
    
    @staticmethod
    async def process_tools_request_async(content):
        """
        异步处理工具请求，调用Open Manus工具链
        
        参数:
            content (str): 工具请求内容，将作为prompt传递给Manus
            
        返回值:
            str: 工具执行结果
        """
        logger.info(f"开始处理工具请求: {content}")
        
        # 配置open_manus的日志系统
        original_configs = ToolsProcessor.configure_manus_logging()
        
        try:
            # 动态导入Manus以避免模块级别的导入问题
            try:
                from open_manus.app.agent.manus import Manus
            except ImportError as e:
                logger.error(f"无法导入Manus: {e}")
                return f"工具初始化失败: 无法导入Manus模块 ({e})"
            
            # 创建Manus代理实例
            agent = Manus()
            


            #########################################
            ########### TOOLS CHAIN - MANUS #########
            #########################################
            try:
                # 确保prompt非空
                if not content.strip():
                    logger.warning("收到空的工具请求")
                    return "工具请求内容为空，无法处理"
                
                logger.info(f"向Open Manus提交请求: {content}")
                
                """
                这里是把整理好的工具PROMPT内容发送给Manus
                """

                # 调用Manus代理的run方法执行工具链
                await agent.run(content)
                
                # 这里返回固定的成功消息
                logger.info("Open Manus工具链执行完成")

                print("FLAG-2")
                print("FLAG-2")
                print("FLAG-2")
                print("FLAG-2")
                print("FLAG-2")

                return "工具使用已经完毕，请参考控制台获悉具体操作内容和结果。"
                # return "{工具已经调用！}"
                
            except Exception as e:
                logger.error(f"执行Open Manus工具链时出错: {e}")
                return f"工具执行失败: {str(e)}"
            finally:
                # 确保资源被清理
                logger.info("清理Open Manus资源")
                await agent.cleanup()
                
        except Exception as e:
            logger.error(f"初始化Open Manus代理时出错: {e}")
            return f"工具初始化失败: {str(e)}"
        finally:
            # 恢复原始日志配置
            ToolsProcessor.restore_manus_logging(original_configs)
    
    @staticmethod
    def process_tools_request(content):
        """处理工具请求的同步包装函数"""
        # 记录接收到的工具请求内容
        logger.info(f"接收到工具请求: {content}")
        
        # 使用线程池执行器来运行异步函数
        import concurrent.futures
        import threading
        
        logger.info("创建线程池执行器")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            # 创建一个可以共享的结果变量
            result_container = []
            
            # 定义线程函数
            def run_async_in_thread():
                try:
                    logger.info("线程开始执行")
                    # 创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    # 执行异步函数
                    result = new_loop.run_until_complete(
                        ToolsProcessor.process_tools_request_async(content)
                    )
                    result_container.append(result)
                    logger.info("异步任务执行完成")

                    # 工具执行完毕，回到这里


                except Exception as e:
                    logger.error(f"线程执行出错: {e}")
                    result_container.append(f"工具处理出错: {str(e)}")
                finally:
                    logger.info("线程结束")
            
            # 提交线程任务
            future = executor.submit(run_async_in_thread)
            
            try:
                # 等待任务完成，设置超时
                logger.info("等待工具执行完成，超时时间300秒")
                future.result(timeout=300)
                
                # 如果有结果，返回结果；否则返回默认消息
                if result_container:
                    return result_container[0]
                else:
                    return "工具执行完成，但没有返回结果"
            except concurrent.futures.TimeoutError:
                logger.error("工具执行超时")
                return "工具执行超时，已强制终止"
            except Exception as e:
                logger.error(f"等待工具执行结果时出错: {e}")
                return f"工具处理过程出错: {str(e)}"
            
    @staticmethod
    def process_message(message):
        """
        处理完整的LLM回复消息
        
        参数:
            message (str): 原始LLM回复消息
            
        返回值:
            str: 处理后的消息
        """
        # 记录原始消息以进行调试
        logger.info(f"处理原始消息: {message[:100]}..." if len(message) > 100 else f"处理原始消息: {message}")
        
        # 提取TOOLS指令内容
        cleaned_message, tools_status, tools_content = ToolsProcessor.extract_tools_content(message)
        
        # 根据TOOLS状态决定后续处理
        if tools_status:
            # 如果TOOLS状态为TRUE，则处理工具请求并将结果添加到消息中
            tools_result = ToolsProcessor.process_tools_request(tools_content)
            # 构建最终回复，将工具执行结果添加到清理后的消息后面
            final_message = f"{cleaned_message}\n\n[工具执行结果]: {tools_result}"
            return final_message
        else:
            # 如果TOOLS状态为FALSE，则直接返回清理后的消息
            return cleaned_message
        
# =====================================================================
# 核心对话函数实现部分
# =====================================================================
async def chat_with_cfo(conversation, user_message: str):
    """
    与CFO助手进行对话的异步生成器函数。
    
    参数:
        conversation (list): 当前对话历史，列表中每项为字典，格式为{"role": "user"/"assistant", "content": "消息内容"}
        user_message (str): 用户当前输入的消息
        
    生成器返回值:
        tuple: (更新后的对话历史, debug信息(未使用), 是否正在生成)
    
    工作流程:
        1. 将用户消息添加到对话历史
        2. 构造完整的消息列表，包括系统提示和对话历史
        3. 调用DeepSeek API获取流式响应
        4. 逐步接收和处理响应，更新对话历史
        5. 实时返回更新后的对话历史
    """
    # 系统提示，定义了CFO助手的角色、功能和行为
    system_prompt = (
        """
        你是一个专业、耐心、懂财务的CFO助手。
        你的专长领域是Finance、财务、金融等。
        用户会向你提问，你可以回答他的问题。
        你可以正常和用户对话，他问什么你就答什么，只要记住自己是个专业的CFO就行了。
        如果答案暂时不知道，也可以先说不确定。

        【关于你的信息】
        你的角色：CFO
        你的名字：用户可以帮你起，不帮你起的话就是CFO
        你会什么：你是以LLM为内核，会使用工具的AI Agent，专精于Finance（财务、金融）方向。
        你现在的LLM内核是：DeepSeek
        你现在的工具库（TOOLS）是：OpenManus
        你擅长使用的语言：中文，English

        【关于工具库TOOLS】
        当你回复用户时，可以正常回复。当且仅当你觉得该任务需要用工具库（TOOLS）才能完成时，你可以启动你的工具库。
        这些任务包括但不限于：
        1、使用浏览器查询信息（LLM内核有时间限制，而你自己去查的话可以获得最新消息）
        2、操作浏览器来做一些事情（比如查询一个文件等）
        3、下载文件
        4、对文件进行专业分析

        用户说的话会直接发送给你，但是你回复的话会经过一道过滤器，该过滤器能识别关键信息，并进而启用工具库TOOLS。
        你可以将你想进行的工具操作写在隐藏语句中。
        在你的回答中，将包含隐藏回答，隐藏回答在每段对话的最后，并用特殊符号包裹。
        隐藏回答的格式：[[TOOLS:TRUE/FALSE][隐藏内容]]
        Example responses 示例回答：
        "你想要查询最新的特斯拉股票信息吗？那么我可以帮你查询。[[TOOLS:TRUE][搜索最新的特斯拉股票信息]]"
        "我知道你问的问题，不需要特别搜索。[[TOOLS:FALSE][无]]"
        "我可以帮你搜索并下载论文Attention is All You Need[[TOOLS:TRUE][使用浏览器搜索论文 Attention is All you Need并找到pdf文件并下载]]"
        "让我来帮你整理特斯拉的最新财报[[TOOLS:TRUE][搜索并下载特斯拉最新财报]]"
        "您的问题很简单，用Excel就能计算。我来帮您进行计算。[[TOOLS:TRUE][用Excel计算用户请求的数据...]]"
        "我知道你问的问题，不需要特别搜索。[[TOOLS:FALSE][无]]"

        Always include [[TOOLS STATUS][PROMPT]]
        请总是在回复的最后标注[[TOOLS STATUS][PROMPT]]
        对于包含具体内容的PROMPT，请在PROMPT中包含具体的工具请求和请求的内容。
        """
    )

    # 复制对话历史，避免修改原始列表
    updated_conv = list(conversation)
    
    # 将用户新消息添加到对话历史
    updated_conv.append({"role": "user", "content": user_message})

    # 构造完整的消息列表，包括系统提示和对话历史
    messages = [{"role": "system", "content": system_prompt}] + updated_conv

    try:
        # 调用DeepSeek API，启用流式响应
        # - model: 使用的模型
        # - messages: 完整的消息列表
        # - stream: 启用流式传输
        # - max_tokens: 生成文本的最大长度
        # - timeout: 接口超时时间(秒)
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            max_tokens=512,
            timeout=30
        )
    except Exception as e:
        # 捕获API调用异常，添加错误信息到对话历史并返回
        updated_conv.append({"role": "assistant", "content": f"CFO：接口调用异常：{e}"})
        yield updated_conv, "", False  # 返回更新后的对话历史，无debug信息，不在生成状态
        return

    # 用于累积部分响应的列表
    partial_response = []
    
    # 逐块处理流式响应
    for chunk in stream:
        # 安全提取本次增量内容
        try:
            content = chunk.choices[0].delta.content
        except Exception:
            content = ""  # 如果提取失败，使用空字符串

        if content:
            # 将新内容添加到部分响应中
            partial_response.append(content)
            current_text = "".join(partial_response)
            
            # 处理对话历史：如果最后一条是用户消息，添加助手回复；否则更新助手回复
            if updated_conv[-1]["role"] == "user":
                updated_conv.append({"role": "assistant", "content": current_text})
            else:
                updated_conv[-1]["content"] = current_text

            # 返回更新后的对话历史，正在生成状态
            yield updated_conv, "", True
            
            # 短暂延迟，避免过快更新导致界面不响应
            await asyncio.sleep(0.05)

    """
    聊天窗口回复流程/聊天对话/聊天框/对话框
    """

    # 完整的LLM回复
    final_response = "".join(partial_response)
    
    # 使用ToolsProcessor处理LLM回复 (识别隐藏内容)
    processed_response = ToolsProcessor.process_message(final_response)
    
    # 更新对话历史中的最后一条助手回复
    if updated_conv[-1]["role"] == "assistant":
        updated_conv[-1]["content"] = processed_response
    
    print("🧾 processed_response =", processed_response)
    print("📝 updated_conv[-1]:", updated_conv[-1])
    print("📤 yield to frontend:\n", updated_conv[-1]["content"])

    
    # 最后一次返回完整对话历史，生成已结束
    yield updated_conv, "", False



# =====================================================================
# Gradio用户界面部分
# =====================================================================
# 创建Gradio块，设置应用标题
with gr.Blocks(title="问CFO") as demo:
    # 页面标题和描述
    gr.Markdown("## 问CFO\n以下是一个财务智能聊天演示。可以连续上下文提问。")

    # 聊天界面组件：显示对话历史
    chatbot = gr.Chatbot(
        label="CFO 对话（连续聊天）", 
        type="messages",  # 使用消息类型展示样式 
        height=600  # 设置聊天窗口高度
    )
    
    # 状态管理组件
    # - conv_state: 存储完整对话历史的状态变量
    # - generating_state: 标记是否正在生成回复的状态变量
    conv_state = gr.State([])  # 初始为空列表
    generating_state = gr.State(False)  # 初始为非生成状态

    # 功能设置部分
    with gr.Accordion("设置", open=False):
        hide_tools_toggle = gr.Checkbox(
            label="隐藏TOOLS指令内容", 
            value=HIDE_TOOLS_CONTENT,
            info="选中时将隐藏回复中的[[TOOLS:...][...]]指令内容"
        )
    
    # 输入和控制按钮行
    with gr.Row():
        # 用户输入文本框
        user_input = gr.Textbox(
            label="请输入您的问题",
            placeholder="例如：今年的财报如何解读？", 
            lines=1  # 单行输入
        )
        # 发送按钮
        send_btn = gr.Button("发送")
        # 停止按钮(初始隐藏)
        stop_btn = gr.Button("停止", visible=False)

    # =====================================================================
    # 交互功能实现部分
    # =====================================================================
    
    # 更新HIDE_TOOLS_CONTENT设置的函数
    def update_hide_tools_setting(value):
        """
        更新是否隐藏TOOLS指令内容的设置
        
        参数:
            value (bool): 是否隐藏TOOLS指令内容
            
        返回值:
            None
        """
        global HIDE_TOOLS_CONTENT
        HIDE_TOOLS_CONTENT = value
    
    # 响应用户消息的异步函数
    async def respond(user_message, conversation, generating):
        """
        处理用户输入消息并获取助手回复的异步函数
        
        参数:
            user_message (str): 用户输入的消息
            conversation (list): 当前对话历史
            generating (bool): 是否正在生成回复
            
        生成器返回值:
            tuple: (用于显示的对话历史, 存储的对话历史, 清空后的用户输入, 生成状态)
        """
        # 如果已经在生成中，忽略新请求
        if generating:
            yield conversation, conversation, user_message, generating
            return
        
        # 调用chat_with_cfo函数获取流式回复
        async for updated_conv, _debug, is_generating in chat_with_cfo(conversation, user_message):
            # 返回更新后的对话历史和状态
            yield updated_conv, updated_conv, "", is_generating
    
    # 切换按钮可见性的函数
    def toggle_button_visibility(generating):
        """
        根据生成状态切换发送和停止按钮的可见性
        
        参数:
            generating (bool): 是否正在生成回复
            
        返回值:
            tuple: (发送按钮更新, 停止按钮更新)
        """
        # 使用 gr.update() 而不是 gr.Button.update()
        return gr.update(visible=not generating), gr.update(visible=generating)
    
    # 停止生成的函数
    def stop_generation(conversation):
        """
        停止生成回复的函数
        
        参数:
            conversation (list): 当前对话历史
            
        返回值:
            tuple: (对话历史, 生成状态设为False)
        """
        return conversation, False
    
    # =====================================================================
    # 事件绑定部分
    # =====================================================================
    
    # 隐藏TOOLS内容切换事件处理
    hide_tools_toggle.change(
        fn=update_hide_tools_setting,
        inputs=[hide_tools_toggle],
        outputs=[]
    )
    
    # 发送按钮点击事件处理
    # 1. 切换按钮可见性(显示停止按钮)
    # 2. 调用respond函数处理消息
    # 3. 切换按钮可见性(显示发送按钮)
    send_event = send_btn.click(
        fn=toggle_button_visibility,
        inputs=[gr.State(True)],
        outputs=[send_btn, stop_btn],
    ).then(
        fn=respond,
        inputs=[user_input, conv_state, generating_state],
        outputs=[chatbot, conv_state, user_input, generating_state],
        queue=True  # 启用队列，避免多个请求冲突
    ).then(
        fn=toggle_button_visibility,
        inputs=[gr.State(False)],
        outputs=[send_btn, stop_btn],
    )
    
    # 停止按钮点击事件处理
    # 1. 调用stop_generation函数停止生成
    # 2. 切换按钮可见性
    stop_btn.click(
        fn=stop_generation,
        inputs=[conv_state],
        outputs=[conv_state, generating_state]
    ).then(
        fn=toggle_button_visibility,
        inputs=[gr.State(False)],
        outputs=[send_btn, stop_btn]
    )
    
    # 用户输入框回车键事件处理(与发送按钮点击行为相同)
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

# =====================================================================
# 应用启动部分
# =====================================================================
# 启用Gradio队列功能，支持并发请求处理
demo.queue()
# 启动Web服务
demo.launch()