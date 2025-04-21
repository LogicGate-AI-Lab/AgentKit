import sys 
from pathlib import Path 
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# dependencies
import gradio as gr
from app.llm import chat_with_cfo
from app.config import AppConfig



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
        # For the messages format, msg is a dictionary with 'role' and 'content' keys
        if isinstance(msg, dict) and 'content' in msg:
            content = msg['content']
        elif isinstance(msg, tuple) and len(msg) == 2:
            # Handle legacy tuple format for backwards compatibility
            content = msg[1] if msg[0] != 'assistant' else msg[0]
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
            
            # For message format, return updated content
            if isinstance(msg, dict):
                return {**msg, 'content': formatted_content}
            # For legacy tuple format
            elif isinstance(msg, tuple):
                return (msg[0], formatted_content)
            return formatted_content
            
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
            
            # Return appropriate format
            if isinstance(msg, dict):
                return {**msg, 'content': formatted_content}
            elif isinstance(msg, tuple):
                return (msg[0], formatted_content)
            return formatted_content
            
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
            
            # Return appropriate format
            if isinstance(msg, dict):
                return {**msg, 'content': formatted_content}
            elif isinstance(msg, tuple):
                return (msg[0], formatted_content)
            return formatted_content
            
        # Regular message - no formatting needed
        return msg
    
    # Create chatbot with messages type
    chatbot = gr.Chatbot(
        label="Smart Agent Conversation (Continuous Chat)", 
        render=format_message,
        height=600,
        type="messages"  # Use the recommended format
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
            value=AppConfig.HIDE_TOOLS_CONTENT,
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
        AppConfig.HIDE_TOOLS_CONTENT = value
    
    # Helper function to convert message format from dictionary to messages format for Gradio Chatbot
    def convert_to_messages_format(conversation):
        """Convert conversation to messages format for Gradio Chatbot"""
        messages = []
        for msg in conversation:
            # Only include user and assistant messages (skip system messages if present)
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        return messages
    
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
            yield convert_to_messages_format(conversation), conversation, user_message, generating
            return
        
        # Call chat_with_cfo function to get streaming reply
        async for updated_conv, _debug, is_generating in chat_with_cfo(conversation, user_message):
            # Return updated dialogue history and state
            yield convert_to_messages_format(updated_conv), updated_conv, "", is_generating
    
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



########## 可调用模块
web_app = demo