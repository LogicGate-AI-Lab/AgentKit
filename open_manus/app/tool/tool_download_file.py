import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import date

import aiohttp
from pydantic import Field

# Import BaseTool and ToolResult from the project's base tool module.
from open_manus.app.tool.base import BaseTool, ToolResult


class DownloadFile(BaseTool):
    name: str = "download_file"
    description: str = (
        "Download a file from a given URL. Supports PDF and other file types. "
        "Downloads the file from the provided URL and saves it locally. "
        "If filename is not provided, the file name is derived from the URL."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL of the file to download.",
            },
            "filename": {
                "type": "string",
                "description": "Optional: The filename to save the file as. "
                               "If not provided, the filename will be extracted from the URL.",
            },
        },
        "required": ["url"],
    }

    async def execute(self, **kwargs) -> ToolResult:
        url: Optional[str] = kwargs.get("url")
        if not url:
            return ToolResult(error="URL is required.")

        filename: Optional[str] = kwargs.get("filename")
        if not filename:
            filename = os.path.basename(url) or "downloaded_file"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return ToolResult(
                            error=f"Failed to download file. HTTP status code: {response.status}"
                        )

                    file_data = await response.read()

                    # Construct download path based on script's location
                    script_dir = Path(__file__).resolve().parent  # -> app/tool
                    project_root = script_dir.parents[2]          # -> project root
                    today_str = date.today().isoformat()          # e.g., "2025-04-10"
                    download_dir = project_root / "open_manus" / "workspace" / "downloads" / today_str

                    # Create the directory if it doesn't exist
                    if not download_dir.exists():
                        print(f"Creating directory: {download_dir}")
                        download_dir.mkdir(parents=True, exist_ok=True)

                    save_path = download_dir / filename

                    # Save the file
                    with save_path.open("wb") as f:
                        f.write(file_data)

                    print(f"✅ File downloaded and saved to: {save_path.resolve()}")

                    return ToolResult(
                        output=(
                            f"✅ Download successful!\n"
                            f"📄 File name: {filename}\n"
                            f"📁 Saved at: {save_path.resolve()}"
                        )
                    )

        except Exception as e:
            return ToolResult(error=f"Error downloading file: {str(e)}")
