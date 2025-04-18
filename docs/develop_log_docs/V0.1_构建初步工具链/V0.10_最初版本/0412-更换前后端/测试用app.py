import asyncio
import logging
from io import StringIO

import gradio as gr
from openai import OpenAI  # 假定你依然使用 OpenAI SDK 兼容 DeepSeek
from open_manus.app.agent.manus import Manus  # 请确保这个模块能够被正确导入

# ----------------------------
# 1. 日志与内存日志处理器
# ----------------------------
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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------
# 2. 初始化 OpenAI 客户端
# ----------------------------
# 注意：请替换成你自己的 API 密钥和 base_url
client = OpenAI(
    api_key="sk-你的密钥",
    base_url="https://api.deepseek.com"
)

# ----------------------------
# 3. 核心业务函数：与 CFO 对话并调用 manus
# ----------------------------
async def chat_with_cfo(question: str):
    """
    此异步生成器函数接收用户问题，先调用 DeepSeek 流式接口，
    判断是否需要调用高级助手（manus）。
    在生成流式响应的同时，会返回两个字符串：
      - 第一个字符串为用户最终看到的“CFO 回答”（包括必要的更新信息）
      - 第二个字符串为后台的调试日志（展示 manus 的思考过程）
    """
    # 系统隐藏提示（加入指导，提示在必要时调用 manus 高级助手）
    system_prompt = (
        "你是一个专业、耐心、懂财务的CFO助手。\n"
        "用户会向你提问，你可以回答他的问题。\n"
        "你可以正常和用户对话，他问什么你就答什么，只要记住自己是个专业的CFO就行了。\n"
        "但是，如果用户的问题是一种行为请求，仅靠你回答无法解决（比如下载、分析财务报表、找资料等），\n"
        "你就可以调用高级助手 manus，这个高级助手能够调用很多工具和函数来执行动作性指令。\n"
        "在对话中，有一个隐藏层，你可以把不想让用户看到的内容存储在隐藏层中。\n"
        "（隐藏提示：如果你认为当前问题需要调用高级助手【MANUS-TOOL-REQ】，请在你的回答末尾附加【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】）"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

    try:
        # 调用 DeepSeek 流式接口（返回生成器对象）
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            max_tokens=512,
            timeout=30
        )
    except Exception as e:
        yield ("CFO：接口调用异常：" + str(e), "")
        return

    result_buffer = []
    # 分块接收流式回复并实时更新前端显示
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            result_buffer.append(content)
            current_response = "".join(result_buffer)
            # 此处每收到一块内容都更新 CFO 回答，同时提示 manus 正在处理（调试信息暂时为占位）
            yield ("CFO：" + current_response, "Manus 调试信息：处理中...")
            await asyncio.sleep(0.05)

    # 全量回复
    full_response = "".join(result_buffer)
    hidden_log = full_response  # 包含了完整的隐藏层内容
    cleaned_response = full_response.replace("【MANUS-TOOL-REQ】", "")
    marker = "【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】【MANUS-TOOL-REQ】"

    # 若检测到需要调用 manus，则进行高级助手调用
    if marker in full_response:
        marker_text = "特殊标记已识别"
        # 添加自定义日志捕获 handler，用于记录 manus 过程
        in_mem_handler = InMemoryHandler()
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        in_mem_handler.setFormatter(log_formatter)
        logger.addHandler(in_mem_handler)

        manus_agent = Manus()
        manus_task = asyncio.create_task(manus_agent.run(question))

        # 在 manus 任务完成前，持续返回等待动画
        while not manus_task.done():
            current_response = "CFO：" + cleaned_response
            yield (current_response, "⌛ 正在处理高级任务，请稍候...")
            await asyncio.sleep(0.5)

        # manus 执行完毕，获取结果与捕获的日志
        manus_result = await manus_task
        await manus_agent.cleanup()
        logs_collected = in_mem_handler.get_log()
        logger.removeHandler(in_mem_handler)

        debug_text = (
            "------ （调试用）回答层 -------\n" + manus_result + "\n\n" +
            "------- （调试用）隐藏层 -------\n" + hidden_log + "\n\n" +
            "标记识别层：" + marker_text + "\n\n" +
            "------- （调试用）日志输出 -------\n" + logs_collected
        )
        # 最后一次更新，将 manus 结果附加显示
        yield ("CFO：" + cleaned_response + "\n\n== Manus 结果 ==\n" + manus_result, debug_text)
    else:
        marker_text = "未识别到特殊标记"
        debug_text = (
            "------ （调试用）回答层 -------\n" + cleaned_response + "\n\n" +
            "------- （调试用）隐藏层 -------\n" + hidden_log + "\n\n" +
            "标记识别层：" + marker_text
        )
        yield ("CFO：" + cleaned_response, debug_text)


# ----------------------------
# 4. 使用 Gradio 构建前端界面
# ----------------------------
# 采用 Blocks 构建对话 + 显示 manus 思考过程（调试日志）的双栏页面
with gr.Blocks(title="问CFO") as demo:
    gr.Markdown("## 问CFO 🤖\n请输入您的问题，系统会调用内部模块进行对话。")
    
    with gr.Row():
        with gr.Column():
            chatbot = gr.Chatbot(label="CFO 对话")
            user_input = gr.Textbox(label="请输入您的问题", placeholder="例如：今年的财报如何解读？", lines=1)
            send_btn = gr.Button("发送")
        with gr.Column():
            debug_box = gr.Textbox(label="Manus 思考过程（调试日志）", interactive=False, lines=15)
    
    # 在用户提交提问时，将当前对话记录（聊天记录）与新问题一同传入处理函数，
    # 然后由生成器 yield 的每个元组更新 chat 和 debug_box（streaming 模式）
    async def process_input(history, user_message):
        # history 为聊天记录列表，每个元素为 (用户输入, CFO 回复)
        history = history + [(user_message, "")]
        # 使用 async for 遍历 chat_with_cfo 异步生成器得到的更新结果
        async for response, debug in chat_with_cfo(user_message):
            # 更新当前聊天记录中最后一条 CFO 回复
            history[-1] = (user_message, response)
            yield history, debug

    send_btn.click(
        process_input, 
        inputs=[chatbot, user_input],
        outputs=[chatbot, debug_box],
        stream=True
    )

demo.launch()
