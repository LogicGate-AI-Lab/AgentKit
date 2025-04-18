import asyncio
import json
from typing import Any, Callable, List, Optional, Union

from pydantic import Field

from open_manus.app.agent.react import ReActAgent
from open_manus.app.exceptions import TokenLimitExceeded
from open_manus.app.logger import logger
from open_manus.app.prompt.toolcall import NEXT_STEP_PROMPT, SYSTEM_PROMPT
# -----------------------------------------------------------------------------
# 新增：引入 Role 以便后面修改 memory 中的 assistant 消息
# -----------------------------------------------------------------------------
from open_manus.app.schema import (
    TOOL_CHOICE_TYPE,
    AgentState,
    Message,
    ToolCall,
    ToolChoice,
    Role,           # ★ 新增
)
from open_manus.app.tool import CreateChatCompletion, Terminate, ToolCollection

TOOL_CALL_REQUIRED = "Tool calls required but none provided"


class ToolCallAgent(ReActAgent):
    """Agent that can reason with LLM, invoke tools, and handle their outputs."""

    # -------------------------------------------------------------------------
    # 基本属性
    # -------------------------------------------------------------------------
    name: str = "toolcall"
    description: str = "an agent that can execute tool calls."

    system_prompt: str = SYSTEM_PROMPT
    next_step_prompt: str = NEXT_STEP_PROMPT

    available_tools: ToolCollection = ToolCollection(
        CreateChatCompletion(), Terminate()
    )
    tool_choices: TOOL_CHOICE_TYPE = ToolChoice.AUTO  # type: ignore
    special_tool_names: List[str] = Field(default_factory=lambda: [Terminate().name])

    tool_calls: List[ToolCall] = Field(default_factory=list)
    _current_base64_image: Optional[str] = None

    max_steps: int = 30
    max_observe: Optional[Union[int, bool]] = None

    # 进度回调（供外部 UI 实时展示）
    _progress_callback: Optional[Callable[[str], None]] = None

    # -------------------------------------------------------------------------
    # 进度上报辅助
    # -------------------------------------------------------------------------
    def set_progress_callback(self, callback: Callable[[str], None]):
        """允许 UI 传入进度回调函数"""
        self._progress_callback = callback

    async def report_progress(self, tool_name: str, progress_msg: str):
        """在工具执行过程中上报进度（写日志并回调 UI）"""
        progress_message = f"[Progress - {tool_name}]: {progress_msg}"
        logger.info(progress_message)

        if self._progress_callback:
            self._progress_callback(progress_message)

        # 不把进度信息写入 memory，避免干扰后续消息配对
        return progress_message

    # -------------------------------------------------------------------------
    # THINK 阶段：决定是否/如何调用工具
    # -------------------------------------------------------------------------
    async def think(self) -> bool:
        """Ask the LLM what to do next (possibly create tool calls)."""
        # （1）把 next_step_prompt 注入为 user 消息，给 LLM 更多上下文
        if self.next_step_prompt:
            self.messages += [Message.user_message(self.next_step_prompt)]

        # （2）请求 LLM，携带可用工具、tool_choice
        try:
            response = await self.llm.ask_tool(
                messages=self.messages,
                system_msgs=([Message.system_message(self.system_prompt)]
                             if self.system_prompt else None),
                tools=self.available_tools.to_params(),
                tool_choice=self.tool_choices,
            )
        except ValueError:
            raise
        except Exception as e:
            # 捕获 RetryError 内嵌的 TokenLimitExceeded
            if hasattr(e, "__cause__") and isinstance(e.__cause__, TokenLimitExceeded):
                token_limit_error = e.__cause__
                logger.error(f"🚨 Token limit error: {token_limit_error}")
                self.memory.add_message(
                    Message.assistant_message(
                        f"Maximum token limit reached: {token_limit_error}"
                    )
                )
                self.state = AgentState.FINISHED
                return False
            raise

        # （3）解析 LLM 返回
        self.tool_calls = tool_calls = response.tool_calls or []
        content = response.content or ""

        # 日志
        logger.info(f"✨ {self.name}'s thoughts: {content}")
        logger.info(f"🛠️ {self.name} selected {len(tool_calls)} tools to use")
        if tool_calls:
            logger.info(
                f"🧰 Tools being prepared: {[call.function.name for call in tool_calls]}"
            )
            logger.info(f"🔧 Tool arguments: {tool_calls[0].function.arguments}")

        # （4）根据 tool_choice 策略决定下一步
        assistant_msg = (
            Message.from_tool_calls(content=content, tool_calls=tool_calls)
            if tool_calls
            else Message.assistant_message(content)
        )
        self.memory.add_message(assistant_msg)

        if self.tool_choices == ToolChoice.NONE:
            return bool(content)

        if self.tool_choices == ToolChoice.REQUIRED and not tool_calls:
            return True  # 交给 act() 抛错

        if self.tool_choices == ToolChoice.AUTO and not tool_calls:
            return bool(content)

        return bool(tool_calls)

    # -------------------------------------------------------------------------
    # 摘要单个工具运行结果
    # -------------------------------------------------------------------------
    async def summarize_tool_results(self, tool_name: str, result: str) -> str:
        summary_prompt = (
            f"You executed the tool '{tool_name}' and got the result below:\n\n"
            f"{result}\n\n"
            "Give a concise, user‑friendly summary of what this result means."
        )

        response = await self.llm.ask(
            messages=[Message.user_message(summary_prompt)],
            system_msgs=[Message.system_message(
                "Summarize the tool execution result concisely."
            )],
            stream=False,
        )
        self.memory.add_message(Message.assistant_message(response))
        return response

    # -------------------------------------------------------------------------
    # ACT 阶段：真正调用工具 & 处理结果
    # -------------------------------------------------------------------------
    async def act(self) -> str:
        # ---------- 0. 没有 tool_call ----------
        if not self.tool_calls:
            if self.tool_choices == ToolChoice.REQUIRED:
                raise ValueError(TOOL_CALL_REQUIRED)
            return self.messages[-1].content or "No content or commands to execute"

        results: List[str] = []
        summaries: List[str] = []

        # ---------- 1. 逐个执行工具 ----------
        for command in self.tool_calls:
            self._current_base64_image = None
            await self.report_progress(command.function.name, "Starting tool execution")

            result = await self.execute_tool(command)
            if self.max_observe:
                result = result[: self.max_observe]

            logger.info(
                f"🎯 Tool '{command.function.name}' completed. Result: {result}"
            )

            # 把 tool 消息写进 memory
            self.memory.add_message(
                Message.tool_message(
                    content=result,
                    tool_call_id=command.id,
                    name=command.function.name,
                    base64_image=self._current_base64_image,
                )
            )
            results.append(result)

            await self.report_progress(
                command.function.name, "Tool execution completed"
            )

            # 如非特殊工具，生成一段摘要
            if not self._is_special_tool(command.function.name):
                await self.report_progress(command.function.name, "Generating summary")
                summaries.append(
                    await self.summarize_tool_results(command.function.name, result)
                )

        # ---------- 2. ★ 关键修复：移除上一条带 tool_calls 的 assistant 标记 ----------
        # for msg in reversed(self.memory.messages):
        #     if msg.role == Role.ASSISTANT and msg.tool_calls:
        #         msg.tool_calls = None  # ★ 删掉字段，配对完成
        #         break

        # ---------- 3. 返回 ----------
        return "\n\n".join(summaries) if summaries else "\n\n".join(results)

    # -------------------------------------------------------------------------
    # 单个工具执行
    # -------------------------------------------------------------------------
    async def execute_tool(self, command: ToolCall) -> str:
        if not command or not command.function or not command.function.name:
            return "Error: Invalid command format"

        name = command.function.name
        if name not in self.available_tools.tool_map:
            return f"Error: Unknown tool '{name}'"

        try:
            args = json.loads(command.function.arguments or "{}")

            await self.report_progress(name, f"Executing with arguments: {args}")

            tool = self.available_tools.tool_map[name]

            # 若工具自身支持 progress_callback，则注入
            if hasattr(tool, "set_progress_callback"):
                tool.set_progress_callback(
                    lambda m: asyncio.create_task(self.report_progress(name, m))
                )

            logger.info(f"🔧 Activating tool: '{name}'...")
            result = await self.available_tools.execute(name=name, tool_input=args)

            # 处理特殊工具
            await self._handle_special_tool(name=name, result=result)

            # 如返回对象带 base64_image，则保存
            if getattr(result, "base64_image", None):
                self._current_base64_image = result.base64_image

            observation = (
                f"Observed output of cmd `{name}` executed:\n{result}"
                if result else f"Cmd `{name}` completed with no output"
            )
            return observation

        except json.JSONDecodeError:
            logger.error(f"📝 Invalid JSON for '{name}': {command.function.arguments}")
            return f"Error: Invalid JSON arguments for '{name}'"
        except Exception as e:
            logger.exception(f"⚠️ Tool '{name}' error: {e}")
            return f"Error: Tool '{name}' encountered a problem: {e}"

    # -------------------------------------------------------------------------
    # 最终总结
    # -------------------------------------------------------------------------
    async def generate_final_summary(self) -> str:
        prompt = (
            "Provide a clear, well‑formatted report of everything done in this session:\n"
            "1. Overview of accomplishments\n"
            "2. Tools used & their purpose\n"
            "3. Key findings\n"
            "4. Conclusions / recommendations"
        )
        self.memory.add_message(Message.user_message(prompt))
        summary = await self.llm.ask(
            messages=self.memory.messages,
            system_msgs=[Message.system_message(
                "Create a professional final report."
            )],
            stream=False,
        )
        self.memory.add_message(Message.assistant_message(summary))
        return summary

    # -------------------------------------------------------------------------
    # 特殊工具处理 / 收尾
    # -------------------------------------------------------------------------
    async def _handle_special_tool(self, name: str, result: Any, **kwargs):
        if not self._is_special_tool(name):
            return
        if self._should_finish_execution(name=name, result=result, **kwargs):
            logger.info(f"🏁 Special tool '{name}' finished the task.")
            self.state = AgentState.FINISHED

    @staticmethod
    def _should_finish_execution(**kwargs) -> bool:
        return True

    def _is_special_tool(self, name: str) -> bool:
        return name.lower() in (n.lower() for n in self.special_tool_names)

    async def cleanup(self):
        logger.info(f"🧹 Cleaning up resources for agent '{self.name}'...")
        for tool_name, tool in self.available_tools.tool_map.items():
            if hasattr(tool, "cleanup") and asyncio.iscoroutinefunction(tool.cleanup):
                try:
                    await tool.cleanup()
                except Exception as e:
                    logger.error(f"🚨 Error cleaning tool '{tool_name}': {e}")
        logger.info(f"✨ Cleanup complete for agent '{self.name}'.")

    # -------------------------------------------------------------------------
    # 顶层 run：执行 + 自动 cleanup + 最终总结
    # -------------------------------------------------------------------------
    async def run(self, request: Optional[str] = None) -> str:
        try:
            result = await super().run(request)
            if self.state == AgentState.FINISHED:
                try:
                    return await self.generate_final_summary()
                except Exception as e:
                    logger.error(f"Error generating final summary: {e}")
                    return result + "\n\n[Final summary generation failed]"
            return result
        finally:
            await self.cleanup()
