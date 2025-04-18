# LLM服务，处理与LLM的交互

# Standard library imports
import asyncio
import logging

# 第三方库导入
from openai import OpenAI

# 导入配置
from app.config import MAIN_APP_KEY, MAIN_APP_URL, LLM_MODEL, LLM_MAX_TOKENS, LLM_TIMEOUT

# 配置模块级日志记录器
logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务类，处理与语言模型的交互"""
    
    def __init__(self):
        """初始化LLM服务，创建API客户端"""
        self.client = OpenAI(
            api_key=MAIN_APP_KEY,
            base_url=MAIN_APP_URL
        )
        self.model = LLM_MODEL
        self.max_tokens = LLM_MAX_TOKENS
        self.timeout = LLM_TIMEOUT
    
    async def generate_streaming_response(self, messages):
        """
        生成流式响应
        
        Parameters:
            messages (list): 消息列表，用于LLM输入
            
        Returns:
            generator: 一个生成器，产生流式响应片段
        """
        try:
            # 调用DeepSeek API，启用流式响应
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            for chunk in stream:
                try:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
                except Exception:
                    yield ""  # 如果提取失败，使用空字符串
                    
                # 短暂延迟以避免界面因更新过于频繁而变得无响应
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"Error generating response: {e}"
    
    async def generate_response(self, messages):
        """
        生成完整响应（非流式）
        
        Parameters:
            messages (list): 消息列表，用于LLM输入
            
        Returns:
            str: 完整的LLM响应
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"

# 创建单例实例
llm_service = LLMService()

# 导出公共接口
__all__ = ['llm_service']