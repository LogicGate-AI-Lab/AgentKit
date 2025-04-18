from typing import Optional, Callable

from pydantic import Field, model_validator

from open_manus.app.agent.browser import BrowserContextHelper
from open_manus.app.agent.toolcall import ToolCallAgent
from open_manus.app.config import config
from open_manus.app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from open_manus.app.schema import Message
from open_manus.app.tool import Terminate, ToolCollection
from open_manus.app.tool.browser_use_tool import BrowserUseTool
from open_manus.app.tool.python_execute import PythonExecute
from open_manus.app.tool.str_replace_editor import StrReplaceEditor
from open_manus.app.tool.tool_download_file import DownloadFile
from open_manus.app.tool.analyze_pdf_file import Analyze_PDF_File
from open_manus.app.logger import logger


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
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(), 
            BrowserUseTool(), 
            StrReplaceEditor(), 
            Terminate(), 
            DownloadFile(), 
            Analyze_PDF_File()
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    browser_context_helper: Optional[BrowserContextHelper] = None
    
    # Add progress tracking variables
    _last_progress_update: str = ""
    _progress_callback: Optional[Callable[[str], None]] = None
    _current_tool: str = ""
    
    @model_validator(mode="after")
    def initialize_helper(self) -> "Manus":
        self.browser_context_helper = BrowserContextHelper(self)
        return self
    
    def set_progress_callback(self, callback: Callable[[str], None]):
        """Set a callback function to report progress during tool execution"""
        self._progress_callback = callback
        logger.info("Progress callback set for Manus agent")

    async def report_progress(self, tool_name: str, progress_msg: str):
        """Override to add enhanced progress reporting"""
        self._current_tool = tool_name
        self._last_progress_update = progress_msg
        
        # Call the parent method first
        await super().report_progress(tool_name, progress_msg)
        
        # Add additional handling if needed
        if self._progress_callback:
            self._progress_callback(f"[{tool_name}] {progress_msg}")
        
        logger.info(f"Progress update: [{tool_name}] {progress_msg}")
        return f"[{tool_name}] {progress_msg}"

    async def think(self) -> bool:
        """Process current state and decide next actions with appropriate context."""
        original_prompt = self.next_step_prompt
        recent_messages = self.memory.messages[-3:] if self.memory.messages else []
        browser_in_use = any(
            tc.function.name == BrowserUseTool().name
            for msg in recent_messages
            if hasattr(msg, 'tool_calls') and msg.tool_calls
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
    
    async def execute_tool(self, command) -> str:
        """Override to add enhanced progress tracking"""
        tool_name = command.function.name
        await self.report_progress(tool_name, f"Starting execution of {tool_name}")
        
        result = await super().execute_tool(command)
        
        await self.report_progress(tool_name, f"Completed execution of {tool_name}")
        return result
    
    async def summarize_tool_results(self, tool_name: str, result: str) -> str:
        """Override to add progress reporting for summarization"""
        await self.report_progress(tool_name, "Generating summary of tool results")
        summary = await super().summarize_tool_results(tool_name, result) 
        await self.report_progress(tool_name, "Summary generation complete")
        return summary
    
    async def generate_final_summary(self) -> str:
        """Override to add progress reporting for final summary"""
        await self.report_progress("FinalSummary", "Generating comprehensive final report")
        summary = await super().generate_final_summary()
        await self.report_progress("FinalSummary", "Final report complete")
        return summary

    async def cleanup(self):
        """Clean up Manus agent resources."""
        await self.report_progress("Cleanup", "Starting resource cleanup")
        if self.browser_context_helper:
            await self.browser_context_helper.cleanup_browser()
        await super().cleanup()
        await self.report_progress("Cleanup", "Resource cleanup complete")