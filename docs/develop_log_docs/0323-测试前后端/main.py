from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAI, OpenAIError
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

# ✅ 初始化日志（可选）
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# ✅ 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # allow_origins=["https://logicgate.com.cn"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 限速器：每个 IP 每分钟最多 5 次
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc):
    return JSONResponse(status_code=429, content={"answer": "访问过于频繁，请稍后再试。"})

# ✅ 初始化 DeepSeek（兼容 OpenAI SDK）
client = OpenAI(
    api_key="..."
    base_url="https://api.deepseek.com"
)

from fastapi.responses import StreamingResponse

@app.post("/api/chat")
@limiter.limit("5/minute")
async def chat(request: Request):
    try:
        data = await request.json()
        question = data.get("question")

        if not question:
            return JSONResponse(status_code=400, content={"error": "问题不能为空。"})

        # ✅ 调用 DeepSeek 流式接口
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业、耐心、懂财务的CFO助手。"},
                {"role": "user", "content": question}
            ],
            stream=True,
            max_tokens=512,
            timeout=30
        )

        # ✅ 定义生成器函数，把内容逐块 yield 出去
        def token_stream():
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        return StreamingResponse(token_stream(), media_type="text/plain")

    except Exception as e:
        logging.error(f"流式响应错误：{e}")
        return JSONResponse(status_code=500, content={"error": "服务端异常，请稍后再试。"})
