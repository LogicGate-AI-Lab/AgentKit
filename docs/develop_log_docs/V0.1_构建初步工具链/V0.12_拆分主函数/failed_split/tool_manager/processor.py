# Standard library imports
import asyncio
import concurrent.futures
import logging
import re
import threading

# 导入配置
from app.config import HIDE_TOOLS_CONTENT, TOOL_EXECUTION_TIMEOUT

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

class ToolsProcessor:
    """
    用于处理LLM响应中工具相关内容的类
    
    此类负责提取和处理来自LLM响应的TOOLS指令，并根据指令状态确定后续操作
    """
    
    @staticmethod
    def extract_tools_content(message):
        """提取消息中的TOOLS指令内容"""
        # 使用正则表达式匹配TOOLS指令格式
        pattern = r'\[\[TOOLS:(TRUE|FALSE)\]\[(.*?)\]\]'
        match = re.search(pattern, message, re.DOTALL)
        
        if match:
            tools_status = match.group(1) == "TRUE"  # 提取TOOLS状态
            tools_content = match.group(2)  # 提取TOOLS内容
            
            # 调试输出以验证内容提取
            logger.info(f"Extracted tool status: {tools_status}")
            logger.info(f"Extracted tool content: {tools_content}")
            
            # 根据HIDE_TOOLS_CONTENT决定是否从消息中移除TOOLS指令
            if HIDE_TOOLS_CONTENT:
                # 移除匹配的TOOLS指令部分
                cleaned_message = re.sub(pattern, '', message, flags=re.DOTALL).strip()
            else:
                # 保留原始消息
                cleaned_message = message
                
            return cleaned_message, tools_status, tools_content
        
        # 如果没有匹配的TOOLS指令，返回原始消息和默认值
        logger.warning("No TOOLS instruction content detected")
        return message, False, ""
    
    @staticmethod
    def configure_manus_logging():
        """配置open_manus日志系统，将其输出转发到主程序"""
        try:
            # 获取主程序的根日志记录器
            root_logger = logging.getLogger()
            
            # 尝试导入open_manus日志模块
            import importlib
            
            # 获取需要处理的每个open_manus模块的日志记录器
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
            
            # 保存原始配置以便稍后恢复
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
                    
                    # 将日志级别设置为INFO或更高
                    manus_logger.setLevel(logging.INFO)
                    
                    # 确保日志传播到根日志记录器
                    manus_logger.propagate = True
                    
                    # 添加主程序的处理器
                    for handler in root_logger.handlers:
                        if handler not in manus_logger.handlers:
                            # 如果是文件处理器，创建一个指向同一文件的新处理器
                            # 这样可以避免潜在的文件锁定问题
                            if isinstance(handler, logging.FileHandler):
                                try:
                                    file_path = handler.baseFilename
                                    new_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
                                    new_handler.setFormatter(handler.formatter)
                                    new_handler.setLevel(handler.level)
                                    manus_logger.addHandler(new_handler)
                                except (AttributeError, IOError) as e:
                                    logger.warning(f"Error creating file handler for {logger_name}: {e}")
                            else:
                                # 对于非文件处理器（例如，控制台处理器），只添加引用
                                manus_logger.addHandler(handler)
                    
                except Exception as e:
                    logger.warning(f"Error configuring {logger_name} logger: {e}")
            
            logger.info("Configured Open Manus logging to forward to main program")
            return original_configs
            
        except ImportError as e:
            logger.warning(f"Unable to import Open Manus logging module: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Error configuring Open Manus logging: {e}")
            return {}
        
    @staticmethod
    def restore_manus_logging(original_configs):
        """恢复原始的open_manus日志配置"""
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
                logger.warning(f"Error restoring {logger_name} logger configuration: {e}")
    
    @staticmethod
    async def process_tools_request_async_with_progress(content, progress_callback=None):
        """
        异步处理工具请求并报告进度
        
        Parameters:
            content (str): 传递给Manus的工具请求内容
            progress_callback (callable): 用于进度更新的回调函数
            
        Returns:
            str: 工具执行结果
        """
        logger.info(f"Starting tool request processing: {content}")
        
        # 配置open_manus日志系统
        original_configs = ToolsProcessor.configure_manus_logging()
        
        try:
            # 动态导入Manus
            try:
                from open_manus.app.agent.manus import Manus
            except ImportError as e:
                logger.error(f"Unable to import Manus: {e}")
                if progress_callback:
                    progress_callback(f"Failed to import Manus module: {e}")
                return f"Tool initialization failed: Cannot import Manus module ({e})"
            
            # 创建Manus代理实例
            agent = Manus()
            
            # 如果提供了进度回调，则设置
            if progress_callback:
                agent.set_progress_callback(progress_callback)
                progress_callback("Manus agent initialized")
            
            try:
                # 确保提示不为空
                if not content.strip():
                    logger.warning("Received empty tool request")
                    if progress_callback:
                        progress_callback("Tool request content is empty")
                    return "Tool request content is empty, cannot process"
                
                logger.info(f"Submitting request to Open Manus: {content}")
                if progress_callback:
                    progress_callback(f"Starting execution with prompt: {content[:100]}...")
                
                # 用提供的内容运行代理
                result = await agent.run(content)
                
                logger.info("Open Manus toolchain execution completed")
                if progress_callback:
                    progress_callback("Tool execution completed successfully")
                
                return result
                
            except Exception as e:
                logger.error(f"Error executing Open Manus toolchain: {e}")
                if progress_callback:
                    progress_callback(f"Error during execution: {str(e)}")
                return f"Tool execution failed: {str(e)}"
            finally:
                # 确保资源被清理
                logger.info("Cleaning up Open Manus resources")
                if progress_callback:
                    progress_callback("Cleaning up resources")
                await agent.cleanup()
                
        except Exception as e:
            logger.error(f"Error initializing Open Manus agent: {e}")
            if progress_callback:
                progress_callback(f"Tool initialization error: {str(e)}")
            return f"Tool initialization failed: {str(e)}"
        finally:
            # 恢复原始日志配置
            ToolsProcessor.restore_manus_logging(original_configs)
            if progress_callback:
                progress_callback("Resource cleanup and logging restoration complete")
    
    @staticmethod
    def process_tools_request(content):
        """处理工具请求的同步包装函数，带有进度"""
        # 记录收到的工具请求内容
        logger.info(f"Received tool request: {content}")
        
        # 使用线程池执行器运行异步函数
        import concurrent.futures
        import threading
        
        logger.info("Creating thread pool executor")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            # 创建共享结果容器
            result_container = []
            progress_updates = []
            
            # 进度回调函数
            def progress_handler(message):
                progress_updates.append(message)
                logger.info(f"Progress update: {message}")
            
            # 定义线程函数
            def run_async_in_thread():
                try:
                    logger.info("Thread execution started")
                    # 创建新的事件循环
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    # 执行带有进度的异步函数
                    result = new_loop.run_until_complete(
                        ToolsProcessor.process_tools_request_async_with_progress(
                            content, progress_callback=progress_handler
                        )
                    )
                    result_container.append(result)
                    logger.info("Asynchronous task completed")

                except Exception as e:
                    logger.error(f"Thread execution error: {e}")
                    result_container.append(f"Tool processing error: {str(e)}")
                finally:
                    logger.info("Thread ended")
            
            # 提交线程任务
            future = executor.submit(run_async_in_thread)
            
            try:
                # 等待任务完成，设置超时
                logger.info(f"Waiting for tool execution to complete, timeout {TOOL_EXECUTION_TIMEOUT} seconds")
                future.result(timeout=TOOL_EXECUTION_TIMEOUT)
                
                # 如果有结果，返回结果和进度信息；否则返回默认消息
                if result_container:
                    progress_summary = "\n".join(progress_updates) if progress_updates else "No detailed progress available"
                    return f"""
Tool execution completed.

Progress Log:
{progress_summary}

Result:
{result_container[0]}
"""
                else:
                    return "Tool execution completed, but no result returned"
            except concurrent.futures.TimeoutError:
                logger.error("Tool execution timeout")
                progress_summary = "\n".join(progress_updates) if progress_updates else "No progress information available"
                return f"""
Tool execution timeout, forcibly terminated after {TOOL_EXECUTION_TIMEOUT} seconds.

Last recorded progress:
{progress_summary}
"""
            except Exception as e:
                logger.error(f"Error waiting for tool execution result: {e}")
                progress_summary = "\n".join(progress_updates) if progress_updates else "No progress information available"
                return f"""
Error during tool processing: {str(e)}

Progress before error:
{progress_summary}
"""
    
    @staticmethod
    def process_message(message):
        """
        处理完整的LLM响应消息
        
        Parameters:
            message (str): 原始LLM响应消息
            
        Returns:
            str: 处理后的消息
        """
        # A记录用于调试的原始消息
        logger.info(f"Processing original message: {message[:100]}..." if len(message) > 100 else f"Processing original message: {message}")
        
        # 提取TOOLS指令内容
        cleaned_message, tools_status, tools_content = ToolsProcessor.extract_tools_content(message)
        
        # 根据TOOLS状态确定后续处理
        if tools_status:
            # 如果TOOLS状态为TRUE，处理工具请求并将结果添加到消息中
            tools_result = ToolsProcessor.process_tools_request(tools_content)
            # 构建最终响应，在清理过的消息后添加工具执行结果
            final_message = f"{cleaned_message}\n\n[Tool Execution Result]: {tools_result}"
            return final_message
        else:
            # 如果TOOLS状态为FALSE，只返回清理过的消息
            return cleaned_message

# 创建工具处理器实例
tools_processor = ToolsProcessor()

# 导出公共接口
__all__ = ['ToolsProcessor', 'tools_processor']