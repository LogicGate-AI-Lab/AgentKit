import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional

from pydantic import Field
from langdetect import detect
from open_manus.app.llm import LLM
from open_manus.app.tool.base import BaseTool, ToolResult


class Analyze_PDF_File(BaseTool):
    name: str = "analyze_pdf_file"
    description: str = (
        "Analyze a downloaded PDF file by sending it to LLM. "
        "The tool extracts the full text and asks LLM to generate a Markdown summary."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "Path to the PDF file to analyze."
            }
        },
        "required": ["filepath"]
    }

    llm: LLM = Field(default_factory=LLM)

    def extract_text_from_pdf(self, filepath: Path) -> str:
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except Exception:
            return "unknown"

    def get_workspace_path(self, filename: str) -> Path:
        script_dir = Path(__file__).resolve().parent
        open_manus_dir = script_dir.parents[1]  # -> open_manus/
        workspace_dir = open_manus_dir / "workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        return workspace_dir / filename

    async def execute(self, **kwargs) -> ToolResult:
        filepath_str = kwargs.get("filepath")
        if not filepath_str:
            return ToolResult(error="Missing filepath parameter.")

        file_path = Path(filepath_str)
        if not file_path.exists():
            return ToolResult(error=f"File does not exist: {file_path}")

        try:
            text = self.extract_text_from_pdf(file_path)
            if len(text.strip()) < 200:
                return ToolResult(output="📄 文件内容太少，可能不是有效的财报。")

            lang = self.detect_language(text)

            # 根据语言选择 Prompt
            if lang.startswith("zh"):
                 prompt = (
                    "你是一名专业的文档分析助理。请阅读以下从 PDF 文件中提取的内容，提炼出关键要点，并整理成结构化的 Markdown 报告。\n\n"
                    "报告应包括（根据内容选择合适部分）：\n"
                    "- 文档标题或主题（如能识别）\n"
                    "- 内容摘要\n"
                    "- 主要章节或结构（如适用）\n"
                    "- 关键信息、数据或观点\n"
                    "- 结论或重点提示\n\n"
                    "请确保输出为 Markdown 格式，结构清晰、条理明确，便于阅读和进一步处理。\n\n"
                    f"以下是提取自 PDF 的内容：\n{text[:8000]}..."
                )
            else:
                prompt = (
                    "You are a professional document analysis assistant. Please review the following extracted content from a PDF file, "
                    "and generate a structured summary in Markdown format.\n\n"
                    "The report should include (as applicable):\n"
                    "- Document title or topic (if identifiable)\n"
                    "- Content summary\n"
                    "- Main sections or structure (if present)\n"
                    "- Key information, data points, or arguments\n"
                    "- Conclusion or key takeaways\n\n"
                    "Ensure the output is clean, structured, and formatted in Markdown for easy readability and further use.\n\n"
                    f"Here is the content extracted from the PDF:\n{text[:8000]}..."
                )


            # markdown_output = await self.llm.ask(prompt) 这里注意要符合写法规范
            markdown_output = await self.llm.ask([{"role": "user", "content": prompt}])


            output_filename = file_path.stem + ".analysis.md"
            output_path = self.get_workspace_path(output_filename)
            output_path.write_text(markdown_output, encoding="utf-8")

            return ToolResult(
                output=f"✅ PDF FINISHED, SAVED: \n📄 {output_path.resolve()}"
            )

        except Exception as e:
            return ToolResult(error=f"Error analyzing report with LLM: {str(e)}")
