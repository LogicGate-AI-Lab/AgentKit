# Standard library imports
import asyncio
import logging
import os
import time
import re
import sys
from pathlib import Path

# Third-party library imports
import gradio as gr
from openai import OpenAI

# Add project root directory to Python path to ensure open_manus module can be imported
project_root = Path(__file__).parent.parent  # Assuming current file is in app directory
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Local application imports
try:
    from open_manus.app.agent.manus import Manus
    from open_manus.app.logger import logger as manus_logger
except ImportError as e:
    print(f"Warning: Unable to import open_manus module: {e}")
    # Create a mock Manus class to avoid runtime errors
    class Manus:
        async def run(self, prompt):
            print(f"Simulating Manus execution: {prompt}")
            return f"Simulated Manus result: {prompt}"
        
        async def cleanup(self):
            print("Simulating cleanup of Manus resources")


# =====================================================================
# API Client Initialization
# =====================================================================
# Initialize OpenAI client, configured to use DeepSeek's API service
# Note: API key is hardcoded; in production, use environment variables or config files
# IMPORT APP MAIN KEY
try:
    from key.key import MAIN_APP_KEY, MAIN_APP_URL
except ImportError:
    print(f"ERROR: NO KEY CAN BE IMPORTED")


client = OpenAI(
    api_key=MAIN_APP_KEY,
    base_url=MAIN_APP_URL
)

# =====================================================================
# Configuration Section
# =====================================================================
# Switch to control whether to hide TOOLS instruction content
HIDE_TOOLS_CONTENT = False


# =====================================================================
# Logging Configuration Section
# =====================================================================
# More detailed logging configuration for troubleshooting
from logging.handlers import RotatingFileHandler

# Create log directory
log_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(log_dir, exist_ok=True)

# Generate log filename in format: YYYY-MM-DD_HH-MM-SS.log
log_filename = time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
log_filepath = os.path.join(log_dir, log_filename)

# Create specific open_manus log file handler
manus_log_filepath = os.path.join(log_dir, f"manus_{log_filename}")

# Configure root logger - configure root logger first to ensure global settings take effect
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Clear any existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create and configure console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# Create and configure file handler
file_handler = RotatingFileHandler(
    log_filepath,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,  # Keep 5 backup files
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)  # Use the same formatter
root_logger.addHandler(file_handler)

# Capture warnings to log
logging.captureWarnings(True)

# Ensure third-party library logs are captured
for logger_name in ['urllib3', 'browser_use', 'openai', 'asyncio']:
    third_party_logger = logging.getLogger(logger_name)
    third_party_logger.setLevel(logging.INFO)
    # Ensure propagation to root logger
    third_party_logger.propagate = True

# Configure open_manus log output
manus_file_handler = RotatingFileHandler(
    manus_log_filepath,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding='utf-8'
)
manus_file_handler.setLevel(logging.INFO)
manus_file_handler.setFormatter(formatter)

# Configure open_manus related loggers
for logger_name in [
    'open_manus', 
    'open_manus.app.agent.base', 
    'open_manus.app.agent.manus', 
    'open_manus.app.agent.toolcall',
    'open_manus.app.llm', 
    'open_manus.app.tool'
]:
    try:
        manus_logger = logging.getLogger(logger_name)
        manus_logger.setLevel(logging.INFO)
        manus_logger.addHandler(manus_file_handler)
        manus_logger.addHandler(console_handler)  # Also output to console
        # Set to not propagate to root logger to avoid duplicate logging
        manus_logger.propagate = False
    except Exception as e:
        print(f"Unable to configure {logger_name} logger: {e}")

# Configure module-level logger
logger = logging.getLogger(__name__)

# Record application startup log
logger.info(f"Application started, logs saved to: {log_filepath}")
logger.info(f"Open Manus logs saved to: {manus_log_filepath}")


# =====================================================================
# Tools Processing Module
# =====================================================================
class ToolsProcessor:
    """
    Class for handling tool-related content in LLM responses
    
    This class is responsible for extracting and processing TOOLS instructions
    from LLM responses and determining subsequent actions based on instruction status
    """
    
    @staticmethod
    def extract_tools_content(message):
        """Extract TOOLS instruction content from a message"""
        # Use regex to match TOOLS instruction format
        import re
        pattern = r'\[\[TOOLS:(TRUE|FALSE)\]\[(.*?)\]\]'
        match = re.search(pattern, message, re.DOTALL)
        
        if match:
            tools_status = match.group(1) == "TRUE"  # Extract TOOLS status
            tools_content = match.group(2)  # Extract TOOLS content
            
            # Debug output to verify content extraction
            logger.info(f"Extracted tool status: {tools_status}")
            logger.info(f"Extracted tool content: {tools_content}")
            
            # Based on HIDE_TOOLS_CONTENT, decide whether to remove TOOLS instruction from message
            if HIDE_TOOLS_CONTENT:
                # Remove the matched TOOLS instruction part
                cleaned_message = re.sub(pattern, '', message, flags=re.DOTALL).strip()
            else:
                # Keep original message
                cleaned_message = message
                
            return cleaned_message, tools_status, tools_content
        
        # If no TOOLS instruction matched, return original message and default values
        logger.warning("No TOOLS instruction content detected")
        return message, False, ""
    
    @staticmethod
    def configure_manus_logging():
        """Configure open_manus logging system, forwarding its output to the main program"""
        try:
            # Get the main program's root logger
            root_logger = logging.getLogger()
            
            # Try to import open_manus logging module
            import importlib
            
            # Get loggers for each open_manus module that needs handling
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
            
            # Save original configurations for later restoration
            original_configs = {}
            
            for logger_name in loggers_to_configure:
                try:
                    manus_logger = logging.getLogger(logger_name)
                    
                    # Save original configuration
                    original_configs[logger_name] = {
                        'level': manus_logger.level,
                        'handlers': list(manus_logger.handlers),
                        'propagate': manus_logger.propagate
                    }
                    
                    # Set log level to INFO or higher
                    manus_logger.setLevel(logging.INFO)
                    
                    # Ensure logs propagate to root logger
                    manus_logger.propagate = True
                    
                    # Add main program's handlers
                    for handler in root_logger.handlers:
                        if handler not in manus_logger.handlers:
                            # If it's a file handler, create a new handler pointing to the same file
                            # This avoids potential file locking issues
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
                                # For non-file handlers (e.g., console handlers), just add reference
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
        """Restore original open_manus logging configuration"""
        if not original_configs:
            return
            
        for logger_name, config in original_configs.items():
            try:
                manus_logger = logging.getLogger(logger_name)
                
                # Restore original level
                manus_logger.setLevel(config['level'])
                
                # Restore original handlers
                for handler in list(manus_logger.handlers):
                    if handler not in config['handlers']:
                        manus_logger.removeHandler(handler)
                
                # Restore propagation setting
                manus_logger.propagate = config['propagate']
                
            except Exception as e:
                logger.warning(f"Error restoring {logger_name} logger configuration: {e}")
    
    @staticmethod
    async def process_tools_request_async_with_progress(content, progress_callback=None):
        """
        Asynchronously process tool requests with progress reporting
        
        Parameters:
            content (str): Tool request content to pass to Manus
            progress_callback (callable): Function to call with progress updates
            
        Returns:
            str: Tool execution result
        """
        logger.info(f"Starting tool request processing: {content}")
        
        # Configure open_manus logging system
        original_configs = ToolsProcessor.configure_manus_logging()
        
        try:
            # Dynamically import Manus
            try:
                from open_manus.app.agent.manus import Manus
            except ImportError as e:
                logger.error(f"Unable to import Manus: {e}")
                if progress_callback:
                    progress_callback(f"Failed to import Manus module: {e}")
                return f"Tool initialization failed: Cannot import Manus module ({e})"
            
            # Create Manus agent instance
            agent = Manus()
            
            # Set progress callback if provided
            if progress_callback:
                agent.set_progress_callback(progress_callback)
                progress_callback("Manus agent initialized")
            
            try:
                # Ensure prompt is not empty
                if not content.strip():
                    logger.warning("Received empty tool request")
                    if progress_callback:
                        progress_callback("Tool request content is empty")
                    return "Tool request content is empty, cannot process"
                
                logger.info(f"Submitting request to Open Manus: {content}")
                if progress_callback:
                    progress_callback(f"Starting execution with prompt: {content[:100]}...")
                
                # Run the agent with the provided content
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
                # Ensure resources are cleaned up
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
            # Restore original logging configuration
            ToolsProcessor.restore_manus_logging(original_configs)
            if progress_callback:
                progress_callback("Resource cleanup and logging restoration complete")
    
    @staticmethod
    def process_tools_request(content):
        """Synchronous wrapper function for processing tool requests with progress"""
        # Record received tool request content
        logger.info(f"Received tool request: {content}")
        
        # Use thread pool executor to run asynchronous function
        import concurrent.futures
        import threading
        
        logger.info("Creating thread pool executor")
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            # Create a shared result container
            result_container = []
            progress_updates = []
            
            # Progress callback function
            def progress_handler(message):
                progress_updates.append(message)
                logger.info(f"Progress update: {message}")
            
            # Define thread function
            def run_async_in_thread():
                try:
                    logger.info("Thread execution started")
                    # Create new event loop
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    # Execute asynchronous function with progress
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
            
            # Submit thread task
            future = executor.submit(run_async_in_thread)
            
            try:
                # Wait for task completion, set timeout
                logger.info("Waiting for tool execution to complete, timeout 300 seconds")
                future.result(timeout=300)
                
                # If there's a result, return it with progress info; otherwise return default message
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
Tool execution timeout, forcibly terminated after 300 seconds.

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
        Process complete LLM response message
        
        Parameters:
            message (str): Original LLM response message
            
        Returns:
            str: Processed message
        """
        # Log original message for debugging
        logger.info(f"Processing original message: {message[:100]}..." if len(message) > 100 else f"Processing original message: {message}")
        
        # Extract TOOLS instruction content
        cleaned_message, tools_status, tools_content = ToolsProcessor.extract_tools_content(message)
        
        # Determine subsequent processing based on TOOLS status
        if tools_status:
            # If TOOLS status is TRUE, process tool request and add result to message
            tools_result = ToolsProcessor.process_tools_request(tools_content)
            # Build final response, adding tool execution result after cleaned message
            final_message = f"{cleaned_message}\n\n[Tool Execution Result]: {tools_result}"
            return final_message
        else:
            # If TOOLS status is FALSE, just return cleaned message
            return cleaned_message
        
# =====================================================================
# Core Dialog Function Implementation
# =====================================================================
async def chat_with_cfo(conversation, user_message: str):
    """
    Asynchronous generator function for dialogue with CFO assistant.
    
    Parameters:
        conversation (list): Current dialogue history, each item is a dictionary in format {"role": "user"/"assistant", "content": "message content"}
        user_message (str): User's current input message
        
    Generator Returns:
        tuple: (updated dialogue history, debug info (unused), generation status)
    
    Workflow:
        1. Add user message to dialogue history
        2. Construct complete message list, including system prompt and dialogue history
        3. Call DeepSeek API to get streaming response
        4. Receive and process response incrementally, update dialogue history
        5. Return updated dialogue history in real-time
    """
    # System prompt, defines the Smart Agent's role, capabilities, and behavior
    system_prompt = (
        """
        You are a professional, patient, knowledgeable and intelligent assistant.
        Your areas of expertise include Finance, Pharmaceuticals, Computer Science, and other professional domains.
        Users will ask you questions, and you can answer them.
        You can have normal conversations with users, answering whatever they ask, just remember you're a professional assistant.
        If you don't know the answer, it's okay to say you're not certain.

        【About You】
        Your role: A very smart Agent
        Your name: Users can give you one, otherwise you're just Smart Agent
        What you can do: You're an AI Agent with an LLM core that can use tools, with expertise in multiple domains including Finance, Pharmaceuticals, and Computer Science.
        Your strength is utilizing specialized tools to complete complex tasks in professional domains.
        Your current LLM core is: DeepSeek
        Your current tools library (TOOLS) is: OpenManus
        Languages you're proficient in: Chinese, English

        【About the Tools Library (TOOLS)】
        When replying to users, you can respond normally. Only when you think a task requires using the tools library (TOOLS) should you activate your tools.
        These tasks include but are not limited to:
        1. Using a browser to search for information (LLM cores have time limitations, but by searching yourself you can get the latest information)
        2. Operating a browser to do things (like looking up a file, etc.)
        3. Downloading files
        4. Performing professional analysis on files

        User messages are sent directly to you, but your replies go through a filter that can recognize key information and activate the tools library TOOLS.
        You can write the tool operations you want to perform in hidden statements.
        Your answers will contain hidden responses at the end of each dialogue segment, wrapped in special symbols.
        Hidden response format: [[TOOLS:TRUE/FALSE][hidden content]]
        Example responses:
        "Would you like to check the latest Tesla stock information? I can help you look that up. [[TOOLS:TRUE][Search for the latest Tesla stock information]]"
        "I know the answer to your question, no need for special search. [[TOOLS:FALSE][none]]"
        "I can help you search and download the paper Attention is All You Need [[TOOLS:TRUE][Use browser to search for the paper Attention is All You Need and find the pdf file and download it]]"
        "Let me help you organize Tesla's latest financial report [[TOOLS:TRUE][Search and download Tesla's latest financial report]]"
        "Your question is simple, it can be calculated using Excel. I'll help you calculate it. [[TOOLS:TRUE][Use Excel to calculate the user's requested data...]]"
        "I know the answer to your question, no need for special search. [[TOOLS:FALSE][none]]"

        Always include [[TOOLS STATUS][PROMPT]]
        Please always mark [[TOOLS STATUS][PROMPT]] at the end of your response
        For PROMPT with specific content, please include specific tool requests and the content of the request in the PROMPT.
        """
    )

    # Copy dialogue history to avoid modifying original list
    updated_conv = list(conversation)
    
    # Add user's new message to dialogue history
    updated_conv.append({"role": "user", "content": user_message})

    # Construct complete message list, including system prompt and dialogue history
    messages = [{"role": "system", "content": system_prompt}] + updated_conv

    try:
        # Call DeepSeek API, enable streaming response
        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=True,
            max_tokens=512,
            timeout=30
        )
    except Exception as e:
        # Catch API call exceptions, add error message to dialogue history and return
        updated_conv.append({"role": "assistant", "content": f"Smart Agent: Interface call exception: {e}"})
        yield updated_conv, "", False  # Return updated dialogue history, no debug info, not in generating state
        return

    # List for accumulating partial responses
    partial_response = []
    
    # Process streaming response chunk by chunk
    for chunk in stream:
        # Safely extract this increment's content
        try:
            content = chunk.choices[0].delta.content
        except Exception:
            content = ""  # If extraction fails, use empty string

        if content:
            # Add new content to partial response
            partial_response.append(content)
            current_text = "".join(partial_response)
            
            # Process dialogue history: if last message is from user, add assistant reply; otherwise update assistant reply
            if updated_conv[-1]["role"] == "user":
                updated_conv.append({"role": "assistant", "content": current_text})
            else:
                updated_conv[-1]["content"] = current_text

            # Return updated dialogue history, generating state
            yield updated_conv, "", True
            
            # Brief delay to avoid interface becoming unresponsive due to too frequent updates
            await asyncio.sleep(0.05)

    # Complete LLM response
    final_response = "".join(partial_response)
    
    # Check if we need to process tools
    if "[[TOOLS:TRUE" in final_response:
        # Extract the tool instructions
        cleaned_message, tools_status, tools_content = ToolsProcessor.extract_tools_content(final_response)
        
        if tools_status:
            # Show that tool processing is starting
            if updated_conv[-1]["role"] == "assistant":
                updated_conv[-1]["content"] = f"{cleaned_message}\n\n[Tool Processing Started...]"
            else:
                updated_conv.append({"role": "assistant", "content": f"{cleaned_message}\n\n[Tool Processing Started...]"})
            
            # Return update to show tool processing has started
            yield updated_conv, "", True
            
            # Set up progress tracking
            progress_updates = []
            
            # Progress callback function
            def progress_handler(message):
                progress_updates.append(message)
                # Update conversation with progress in real-time
                if updated_conv[-1]["role"] == "assistant":
                    current_content = updated_conv[-1]["content"]
                    if "[Tool Processing Progress]" not in current_content:
                        updated_content = f"{current_content}\n\n[Tool Processing Progress]\n{message}"
                    else:
                        parts = current_content.split("[Tool Processing Progress]")
                        updated_content = f"{parts[0]}[Tool Processing Progress]{parts[1]}\n{message}"
                    
                    updated_conv[-1]["content"] = updated_content
                    # We can't yield here directly - we'll store updates and process them later
            
            # Process the tool request with progress tracking
            tools_result = await ToolsProcessor.process_tools_request_async_with_progress(
                tools_content, progress_callback=progress_handler
            )
            
            # After tool execution, update conversation with latest progress
            if updated_conv[-1]["role"] == "assistant":
                current_content = updated_conv[-1]["content"]
                if "[Tool Processing Progress]" in current_content:
                    progress_text = "\n".join(progress_updates)
                    parts = current_content.split("[Tool Processing Progress]")
                    updated_content = f"{parts[0]}[Tool Processing Progress]\n{progress_text}\n\n[Tool Execution Complete]"
                else:
                    progress_text = "\n".join(progress_updates)
                    updated_content = f"{current_content}\n\n[Tool Processing Progress]\n{progress_text}\n\n[Tool Execution Complete]"
                
                updated_conv[-1]["content"] = updated_content
                yield updated_conv, "", True
            
            # Now generate a summary of the tool results
            summary_prompt = f"""
            You have just used tools to accomplish a task for the user. 
            Here is the original request: "{user_message}"
            
            The tools executed with the following result:
            {tools_result}
            
            Please provide a clear, concise, and helpful summary of:
            1. What tools were used and why
            2. What was accomplished
            3. Key findings or insights from the tool execution
            4. Any relevant next steps or recommendations
            
            Format your response as a professional summary that focuses on the most important information.
            """
            
            # Add summary request to messages
            summary_messages = [{"role": "system", "content": system_prompt}] + [
                {"role": "assistant", "content": cleaned_message},
                {"role": "user", "content": summary_prompt}
            ]
            
            # Update the UI to show summary is being generated
            if updated_conv[-1]["role"] == "assistant":
                current_content = updated_conv[-1]["content"]
                updated_conv[-1]["content"] = f"{current_content}\n\n[Generating Summary...]"
                yield updated_conv, "", True
            
            try:
                # Call DeepSeek API for summary
                summary_stream = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=summary_messages,
                    stream=True,
                    max_tokens=512,
                    timeout=30
                )
                
                # Process summary stream
                summary_parts = []
                
                for chunk in summary_stream:
                    try:
                        content = chunk.choices[0].delta.content
                    except Exception:
                        content = ""
                    
                    if content:
                        summary_parts.append(content)
                        current_summary = "".join(summary_parts)
                        
                        # Update conversation with ongoing summary
                        current_content = updated_conv[-1]["content"]
                        if "[Generating Summary...]" in current_content:
                            parts = current_content.split("[Generating Summary...]")
                            updated_conv[-1]["content"] = f"{parts[0]}\n\n[Tool Execution Summary]\n{current_summary}"
                        else:
                            updated_conv[-1]["content"] = f"{current_content}\n\n[Tool Execution Summary]\n{current_summary}"
                        
                        yield updated_conv, "", True
                        await asyncio.sleep(0.05)
                
                # Final summary
                final_summary = "".join(summary_parts)
                
                # Format the final processed response with tool results and summary
                processed_response = f"""
{cleaned_message}

[Tool Execution Complete]

[Tool Execution Summary]
{final_summary}
"""
                
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                # If summary generation fails, use a simpler format
                processed_response = f"""
{cleaned_message}

[Tool Execution Complete]

[Tool Results]
{tools_result}

[Note: Summary generation failed - {str(e)}]
"""
        else:
            # If no tools were used (FALSE), just process the message normally
            processed_response = ToolsProcessor.process_message(final_response)
    else:
        # If no tool markers at all, use the response as is
        processed_response = final_response
    
    # Update the final assistant message with the processed response
    if updated_conv[-1]["role"] == "assistant":
        updated_conv[-1]["content"] = processed_response
    else:
        updated_conv.append({"role": "assistant", "content": processed_response})
    
    print("🧾 processed_response =", processed_response)
    print("📝 updated_conv[-1]:", updated_conv[-1])
    print("📤 yield to frontend:\n", updated_conv[-1]["content"])
    
    # Final return of complete dialogue history, generation ended
    yield updated_conv, "", False



# =====================================================================
# Gradio User Interface Section
# =====================================================================
# Create Gradio block, set application title
with gr.Blocks(title="Smart Agent", css="""
    /* Tool processing progress styles */
    .tool-progress {
        background-color: #f5f7ff;
        border-left: 3px solid #4a6fa5;
        padding: 8px 12px;
        margin-top: 10px;
        border-radius: 4px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    
    /* Tool execution summary styles */
    .tool-summary {
        background-color: #f0f7f0;
        border-left: 3px solid #4caf50;
        padding: 10px;
        margin-top: 10px;
        border-radius: 4px;
    }
    
    /* Error message styles */
    .error-message {
        background-color: #fff0f0;
        border-left: 3px solid #ff5252;
        padding: 10px;
        margin-top: 10px;
        border-radius: 4px;
    }
""") as demo:
    # Page title and description
    gr.Markdown("## Smart Agent\nBelow is an intelligent assistant demonstration. You can ask continuous contextual questions.")

    # Chat interface component with custom message rendering
    def format_message(msg):
        """Format chat messages to enhance tool progress display"""
        if isinstance(msg, tuple) and len(msg) == 2:
            # In tuples format, msg is (user_message, assistant_message)
            # We'll only format the assistant's message
            content = msg[1]
        else:
            # Fallback - shouldn't happen with correct format
            content = str(msg)
        
        # Replace tool processing sections with styled divs
        if "[Tool Processing Progress]" in content:
            parts = content.split("[Tool Processing Progress]", 1)
            progress_parts = parts[1].split("[Tool Execution Complete]", 1)
            progress_content = progress_parts[0].strip()
            
            formatted_content = f"""
            {parts[0]}
            <div class="tool-progress">
                <div><strong>Tool Processing Progress:</strong></div>
                <pre>{progress_content}</pre>
            </div>
            """
            
            # Add execution complete and summary if available
            if len(progress_parts) > 1 and "[Tool Execution Summary]" in progress_parts[1]:
                summary_parts = progress_parts[1].split("[Tool Execution Summary]", 1)
                summary_content = summary_parts[1].strip()
                
                formatted_content += f"""
                <div class="tool-summary">
                    <div><strong>Tool Execution Summary:</strong></div>
                    <div>{summary_content}</div>
                </div>
                """
            elif len(progress_parts) > 1:
                formatted_content += progress_parts[1]
                
            return (msg[0], formatted_content)
            
        # Handle execution summary without progress
        elif "[Tool Execution Summary]" in content:
            parts = content.split("[Tool Execution Summary]", 1)
            
            formatted_content = f"""
            {parts[0]}
            <div class="tool-summary">
                <div><strong>Tool Execution Summary:</strong></div>
                <div>{parts[1]}</div>
            </div>
            """
            return (msg[0], formatted_content)
            
        # Handle error messages
        elif "[Error]" in content:
            parts = content.split("[Error]", 1)
            
            formatted_content = f"""
            {parts[0]}
            <div class="error-message">
                <div><strong>Error:</strong></div>
                <div>{parts[1]}</div>
            </div>
            """
            return (msg[0], formatted_content)
            
        # Regular message - no formatting needed
        return msg
    
    # Create chatbot with default type (tuples)
    chatbot = gr.Chatbot(
        label="Smart Agent Conversation (Continuous Chat)", 
        render=format_message,
        height=600,
    )
    
    # State management components
    # - conv_state: state variable for storing complete dialogue history
    # - generating_state: state variable marking whether reply is being generated
    conv_state = gr.State([])  # Initially empty list
    generating_state = gr.State(False)  # Initially not generating

    # Function settings section
    with gr.Accordion("Settings", open=False):
        hide_tools_toggle = gr.Checkbox(
            label="Hide TOOLS instruction content", 
            value=HIDE_TOOLS_CONTENT,
            info="When checked, [[TOOLS:...][...]] instruction content will be hidden in replies"
        )
    
    # Input and control button row
    with gr.Row():
        # User input text box
        user_input = gr.Textbox(
            label="Please enter your question",
            placeholder="Example: How to interpret this year's financial report?", 
            lines=1  # Single line input
        )
        # Send button
        send_btn = gr.Button("Send")
        # Stop button (initially hidden)
        stop_btn = gr.Button("Stop", visible=False)

    # =====================================================================
    # Interactive Functionality Implementation
    # =====================================================================
    
    # Function to update HIDE_TOOLS_CONTENT setting
    def update_hide_tools_setting(value):
        """
        Update setting for whether to hide TOOLS instruction content
        
        Parameters:
            value (bool): Whether to hide TOOLS instruction content
            
        Returns:
            None
        """
        global HIDE_TOOLS_CONTENT
        HIDE_TOOLS_CONTENT = value
    
    # Helper function to convert message format from dictionary to tuples
    def convert_to_tuples(conversation):
        """Convert conversation from dict format to tuples format for Gradio Chatbot"""
        tuples = []
        for i in range(0, len(conversation), 2):
            if i+1 < len(conversation):
                if conversation[i]["role"] == "user" and conversation[i+1]["role"] == "assistant":
                    tuples.append((conversation[i]["content"], conversation[i+1]["content"]))
        return tuples
    
    # Asynchronous function to respond to user messages
    async def respond(user_message, conversation, generating):
        """
        Asynchronous function to process user input messages and get assistant replies
        
        Parameters:
            user_message (str): User input message
            conversation (list): Current dialogue history
            generating (bool): Whether reply is being generated
            
        Generator Returns:
            tuple: (dialogue history for display, stored dialogue history, cleared user input, generation state)
        """
        # If already generating, ignore new request
        if generating:
            yield convert_to_tuples(conversation), conversation, user_message, generating
            return
        
        # Call chat_with_cfo function to get streaming reply
        async for updated_conv, _debug, is_generating in chat_with_cfo(conversation, user_message):
            # Return updated dialogue history and state
            yield convert_to_tuples(updated_conv), updated_conv, "", is_generating
    
    # Function to toggle button visibility
    def toggle_button_visibility(generating):
        """
        Toggle send and stop button visibility based on generation state
        
        Parameters:
            generating (bool): Whether reply is being generated
            
        Returns:
            tuple: (send button update, stop button update)
        """
        # Use gr.update() instead of gr.Button.update()
        return gr.update(visible=not generating), gr.update(visible=generating)
    
    # Function to stop generation
    def stop_generation(conversation):
        """
        Function to stop reply generation
        
        Parameters:
            conversation (list): Current dialogue history
            
        Returns:
            tuple: (dialogue history, generation state set to False)
        """
        return conversation, False
    
    # =====================================================================
    # Event Binding Section
    # =====================================================================
    
    # Hide TOOLS content toggle event handler
    hide_tools_toggle.change(
        fn=update_hide_tools_setting,
        inputs=[hide_tools_toggle],
        outputs=[]
    )
    
    # Send button click event handler
    # 1. Toggle button visibility (show stop button)
    # 2. Call respond function to process message
    # 3. Toggle button visibility (show send button)
    send_event = send_btn.click(
        fn=toggle_button_visibility,
        inputs=[gr.State(True)],
        outputs=[send_btn, stop_btn],
    ).then(
        fn=respond,
        inputs=[user_input, conv_state, generating_state],
        outputs=[chatbot, conv_state, user_input, generating_state],
        queue=True  # Enable queue to avoid request conflicts
    ).then(
        fn=toggle_button_visibility,
        inputs=[gr.State(False)],
        outputs=[send_btn, stop_btn],
    )
    
    # Stop button click event handler
    # 1. Call stop_generation function to stop generation
    # 2. Toggle button visibility
    stop_btn.click(
        fn=stop_generation,
        inputs=[conv_state],
        outputs=[conv_state, generating_state]
    ).then(
        fn=toggle_button_visibility,
        inputs=[gr.State(False)],
        outputs=[send_btn, stop_btn]
    )
    
    # User input box enter key event handler (same behavior as send button click)
    user_input.submit(
        fn=toggle_button_visibility,
        inputs=[gr.State(True)],
        outputs=[send_btn, stop_btn],
    ).then(
        fn=respond,
        inputs=[user_input, conv_state, generating_state],
        outputs=[chatbot, conv_state, user_input, generating_state],
        queue=True
    ).then(
        fn=toggle_button_visibility,
        inputs=[gr.State(False)],
        outputs=[send_btn, stop_btn],
    )



# =====================================================================
# Application Launch Section
# =====================================================================
# Enable Gradio queue functionality, support concurrent request processing
demo.queue()
# Start web service
demo.launch()