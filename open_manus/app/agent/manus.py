from typing import Optional

from pydantic import Field, model_validator

from open_manus.app.agent.browser import BrowserContextHelper
from open_manus.app.agent.toolcall import ToolCallAgent
from open_manus.app.config import config
from open_manus.app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from open_manus.app.tool import Terminate, ToolCollection
from open_manus.app.tool.browser_use_tool import BrowserUseTool
from open_manus.app.tool.python_execute import PythonExecute
from open_manus.app.tool.str_replace_editor import StrReplaceEditor

# 添加更多的工具
from open_manus.app.tool.tool_download_file import DownloadFile
from open_manus.app.tool.analyze_pdf_file import Analyze_PDF_File


class Manus(ToolCallAgent):
    """A versatile general-purpose agent."""

    name: str = "Manus"
    description: str = (
        "A versatile agent that can solve various tasks using multiple tools"
    )

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 20

    # Add general-purpose tools to the tool collection
    # 在这里添加工具到 TOOL COLLECTION 工具集中
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(), BrowserUseTool(), StrReplaceEditor(), Terminate(), 
            DownloadFile(),
            Analyze_PDF_File()
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    browser_context_helper: Optional[BrowserContextHelper] = None

    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        self.browser_context_helper = BrowserContextHelper(self)
        return self

    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if msg.tool_calls
            for tc in msg.tool_calls
        )

        if browser_in_use:
            self.next_step_prompt = (
                await self.browser_context_helper.format_next_step_prompt()
            )

        result = await super().think()

        # Restore original prompt
        self.next_step_prompt = original_prompt

        return result

    async def cleanup(self):
        """Clean up Manus agent resources."""
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
