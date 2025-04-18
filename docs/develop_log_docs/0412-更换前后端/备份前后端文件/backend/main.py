import asyncio
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from openai import OpenAI, OpenAIError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from open_manus.app.agent.manus import Manus  # 请确保 open_manus 内部使用相对导入

"""
注意：本文件使用了硬编码，请不要将本文件直接上传到云端
在上传云端前，请记得先进行密钥分离和管理
"""

# 初始化日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 根据需要调整
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限速器：每个 IP 每分钟最多 5 次
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc):
    return JSONResponse(status_code=429, content={"answer": "访问过于频繁，请稍后再试。"})

# 初始化 DeepSeek（兼容 OpenAI SDK）
client = OpenAI(
    api_key="s1",
    base_url="https://api.deepseek.com"
)

# -----------------------------------------
# 自定义 InMemoryHandler 用于捕获日志输出到内存
from io import StringIO

class InMemoryHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.stream = StringIO()
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + "\n")
        except Exception:
            self.handleError(record)
    def get_log(self):
        return self.stream.getvalue()
    def clear(self):
        self.stream.truncate(0)
        self.stream.seek(0)
# -----------------------------------------

@app.post("/api/chat")
@limiter.limit("5/minute")
async def chat(request: Request):
    try:
        data = await request.json()
        question = data.get("question")
        if not question:
            return JSONResponse(status_code=400, content={"error": "问题不能为空。"})

        # 使用系统提示增加隐藏层指令，指导 LLM 在必要时在回答末尾附加隐藏标记
        system_prompt = (
            """
            你是一个专业、耐心、懂财务的CFO助手。
            用户会向你提问，你可以回答他的问题。
            你可以正常和用户对话，他问什么你就答什么，只要记住自己是个专业的CFO就行了。
            但是，如果用户的问题是一种行为请求，仅靠你回答无法解决的话，比如说：
            用户想让你帮他下载一个东西、分析一个财务报表、找一个资料等，
            你就可以调用高级助手manus，这个高级助手manus是你的系统中的一个功能模块，
            它可以调用很多工具和函数来执行动作性指令。
            在对话中，有一个隐藏层，你可以把不想让用户看到的内容存储在隐藏层中。
            （隐藏提示：如果你认为当前问题需要调用高级助手【MANUS-TOOL-REQ】，请在你的回答末尾附加【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】。）
            -------------------------------
            举例说明：
            假如你想向用户回复：好的，我现在就帮你完成该任务，并想调用manus工具，
            那么就在你的回答中写：
            好的，我现在就帮你完成该任务。【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】
            """
        )
        
        # 构造消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        # 调用 DeepSeek 流式接口（使用同步迭代）
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            max_tokens=512,
            timeout=30
        )
        
        result_buffer = []
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                result_buffer.append(content)
        full_response = "".join(result_buffer)
        
        # 构造返回文本：分为回答层、隐藏层和标记识别层
        hidden_log = full_response  # 原始完整输出（含隐藏标记）
        cleaned_response = full_response.replace("【MANUS-TOOL-REQ】", "")
        
        marker = "【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】"
        
        # 如果检测到隐藏标记，则调用 Manus 代理
        if marker in full_response:
            marker_text = "-------- 标记识别层 ----------\n已识别到特殊标记" + marker
            # 添加自定义日志捕获 handler
            in_mem_handler = InMemoryHandler()
            log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            in_mem_handler.setFormatter(log_formatter)
            logger.addHandler(in_mem_handler)
            
            manus_agent = Manus()
            manus_task = asyncio.create_task(manus_agent.run(question))
            
            async def waiting_stream():
                # 在 Manus 任务未完成期间，不断输出等待动画
                while not manus_task.done():
                    yield "⌛ 正在处理高级任务，请稍候...\n"
                    await asyncio.sleep(0.5)
                manus_result = await manus_task
                await manus_agent.cleanup()
                # 获取捕获的日志内容
                logs_collected = in_mem_handler.get_log()
                logger.removeHandler(in_mem_handler)
                final_text = (
                    "------ （调试用）回答层 -------\n" + manus_result + "\n\n" +
                    "------- （调试用） 隐藏层 -------\n" + hidden_log + "\n\n" +
                    marker_text + "\n\n" +
                    "------- （调试用） 日志输出 -------\n" + logs_collected
                )
                yield final_text
            
            return StreamingResponse(waiting_stream(), media_type="text/plain")
        else:
            marker_text = "-------- 标记识别层 ----------\n未识别到特殊标记"
            final_text = (
                "------ （调试用）回答层 -------\n" + cleaned_response + "\n\n" +
                "------- （调试用） 隐藏层 -------\n" + hidden_log + "\n\n" +
                marker_text
            )
            def token_stream():
                yield final_text
            return StreamingResponse(token_stream(), media_type="text/plain")
        
    except Exception as e:
        logging.error(f"流式响应错误：{e}")
        return JSONResponse(status_code=500, content={"error": "服务端异常，请稍后再试。"})



# ########################################################
# ######## 备份：4/10， 2025 —— 没有增加判断层之前的代码如下：

# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from openai import OpenAI, OpenAIError
# from slowapi import Limiter
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded
# import logging

# """
# 注意：本文件使用了硬编码，请不要将本文件直接上传到云端
# 在上传云端前，请记得先进行密钥分离和管理
# """

# # ✅ 初始化日志（可选）
# logging.basicConfig(level=logging.INFO)

# app = FastAPI()

# # ✅ 跨域配置 | 部署在线上的话需要修改
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # allow_origins=["https://logicgate.com.cn"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ 限速器：每个 IP 每分钟最多 5 次
# limiter = Limiter(key_func=get_remote_address)
# app.state.limiter = limiter

# @app.exception_handler(RateLimitExceeded)
# async def rate_limit_exceeded_handler(request: Request, exc):
#     return JSONResponse(status_code=429, content={"answer": "访问过于频繁，请稍后再试。"})

# # ✅ 初始化 DeepSeek（兼容 OpenAI SDK）
# client = OpenAI(
#     api_key="sk-9d7449254ec14790a086ed6dd90c9a21",
#     base_url="https://api.deepseek.com"
# )

# from fastapi.responses import StreamingResponse

# @app.post("/api/chat")
# @limiter.limit("5/minute")
# async def chat(request: Request):
#     try:
#         data = await request.json()
#         question = data.get("question")

#         if not question:
#             return JSONResponse(status_code=400, content={"error": "问题不能为空。"})

#         # ✅ 调用 DeepSeek 流式接口
#         stream = client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": "你是一个专业、耐心、懂财务的CFO助手。"},
#                 {"role": "user", "content": question}
#             ],
#             stream=True,
#             max_tokens=512,
#             timeout=30
#         )

#         # ✅ 定义生成器函数，把内容逐块 yield 出去
#         def token_stream():
#             for chunk in stream:
#                 content = chunk.choices[0].delta.content
#                 if content:
#                     yield content

#         return StreamingResponse(token_stream(), media_type="text/plain")

#     except Exception as e:
#         logging.error(f"流式响应错误：{e}")
#         return JSONResponse(status_code=500, content={"error": "服务端异常，请稍后再试。"})
# #################################################################

