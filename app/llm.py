import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.logger import logger
from app.config import client
from app.tools.ToolsProcessor import ToolsProcessor
import asyncio


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

