# controller.py
import asyncio
import json
import traceback
from config import APP_CONFIG
from llm_handler import LLMHandler
from mcp_handler import MCPHandler
# ui.py is imported dynamically in __init__ or main to avoid circular dependency if needed,
# but direct import is usually fine if structure is correct.
from ui import AppGUI

SYSTEM_PROMPT = """You are 'Assistant', a helpful, conversational AI assistant interacting with a user via a chat interface.
Your goal is to provide accurate information and complete tasks as requested.

**Core Capabilities:**
1.  Engage in conversation and answer general questions using your internal knowledge.
2.  Utilize available tools to fetch specific, real-time, or calculated information when necessary.

**Tool Usage Policy:**
* Analyze the user's request to determine if it requires capabilities beyond your internal knowledge (e.g., calculating current travel time between specific locations).
* If a tool is appropriate:
    * Identify the correct tool (e.g., `get_travel_time`).
    * Extract all required parameters accurately from the user's message (e.g., for `get_travel_time`, you need `origin`, `destination`, and `mode`).
    * If essential parameters are missing, ask the user clarifying questions *before* attempting to use the tool.
    * Once the tool provides a result, synthesize that information into a friendly, easy-to-understand response for the user. Do not just output the raw tool result unless specifically asked.
* If the request can be fully answered without a tool, do so directly.

**Response Guidelines:**
* Be polite, helpful, and clear.
* Keep responses concise but informative.
* Acknowledge the use of a tool subtly if it adds clarity (e.g., "According to the travel time tool...").
* Do not invent information or pretend to have capabilities you lack.
"""

class AppController:
    """Orchestrates the UI, LLM, and MCP interactions."""

    def __init__(self, root):
        """
        Initializes the controller, setting up components.

        Args:
            root: The main Tkinter window (tk.Tk instance).
        """
        self.root = root
        self.config = APP_CONFIG # Load config from config.py
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}] # Stores the conversation history for the LLM

        # --- Initialize Handlers ---
        # Pass a lambda or method reference for UI updates
        self.mcp_handler = MCPHandler(update_callback=self._handle_handler_update)
        self.llm_handler = LLMHandler()

        # --- Initialize UI ---
        # Pass self (the controller) to the GUI
        self.gui = AppGUI(root, self)

        # --- Initial Setup ---
        self._initialize_llm_from_config()


    def _handle_handler_update(self, message, role):
        """Callback for MCP/LLM handlers to send updates to the UI."""
        if role == "status":
            self.gui.update_status(message)
        else:
            # Map handler roles (system, etc.) to UI roles if needed, or pass directly
            self.gui.update_output(message, role)

    def _initialize_llm_from_config(self):
        """Attempts to initialize the LLM using config values."""
        api_key = self.config.get("api_key")
        endpoint = self.config.get("endpoint")
        success, message = self.llm_handler.initialize(api_key, endpoint)
        self.gui.update_output(message, "system")
        if not success:
            self.gui.update_status("LLM Init Failed")
        else:
             self.gui.update_status("LLM Ready")


    def get_config_value(self, key, default=None):
        """Safely gets a value from the loaded configuration."""
        return self.config.get(key, default)

    # --- Actions Triggered by UI ---

    def connect_mcp(self):
        """Handles the 'Connect' button click."""
        server_script = self.gui.get_server_script_path()
        if not server_script:
            self.gui.update_output("Please specify the MCP server script path.", "system")
            return
        # Run the async connection method in the background
        asyncio.create_task(self.mcp_handler.connect(server_script))

    def disconnect_mcp(self):
        """Handles the 'Disconnect' button click."""
         # Run the async disconnect method in the background
        asyncio.create_task(self.mcp_handler.disconnect())


    def list_mcp_tools(self):
        """Handles the 'List Tools' button click."""
        if not self.mcp_handler.is_connected():
            self.gui.update_output("Not connected to MCP server.", "system")
            return
        # Run the async list_tools method
        asyncio.create_task(self.mcp_handler.list_tools(log=True))

    def update_azure_config(self, api_key, endpoint, deployment):
        """Handles applying new Azure settings from the UI."""
        # Update internal config representation (optional, if needed elsewhere)
        self.config["api_key"] = api_key
        self.config["endpoint"] = endpoint
        self.config["deployment"] = deployment
        # Re-initialize the LLM client
        self.gui.update_status("Re-initializing LLM...")
        success, message = self.llm_handler.initialize(api_key, endpoint)
        self.gui.update_output(message, "system")
        self.gui.update_status("LLM Ready" if success else "LLM Init Failed")


    def send_message_to_llm(self, user_input):
        """Handles sending user input to the LLM process."""
        if not user_input:
            return

        self.gui.update_output(user_input, "user") # Display user message immediately

        # Add user message to conversation history
        self.messages.append({"role": "user", "content": user_input})

        # Check if LLM is initialized
        if not self.llm_handler.is_initialized():
             self.gui.update_output("Azure OpenAI client is not initialized. Please check settings.", "system")
             # Remove the user message we optimistically added if we can't process it
             if self.messages and self.messages[-1]["role"] == "user":
                 self.messages.pop()
             return

        # Start the asynchronous processing in the background
        self.gui.update_status("Processing...")
        asyncio.create_task(self._process_llm_interaction())

    # --- Core Asynchronous Logic ---

    async def _process_llm_interaction(self):
        """Processes the conversation with the LLM, handling potential tool calls."""
        try:
            current_tools = []
            openai_tool_definitions = []

            # 1. Check MCP connection and get tools if connected
            if self.mcp_handler.is_connected():
                current_tools = await self.mcp_handler.list_tools() # Get MCP Tool objects
                if current_tools:
                     openai_tool_definitions = self.llm_handler.format_tools_for_openai(current_tools)
                    #  self.gui.update_output(f"Using {len(current_tools)} tools from MCP server.", "system")
                else:
                     self.gui.update_output("Connected to MCP, but no tools found or error listing tools.", "system")
            else:
                self.gui.update_output("Not connected to MCP server. Proceeding without tools.", "system")


            max_iterations = 5 # Safety limit for tool call loops
            iterations = 0

            while iterations < max_iterations:
                iterations += 1
                self.gui.update_status(f"LLM Call {iterations}...")

                # 2. Call LLM
                response_message = await self.llm_handler.get_completion(
                    deployment=self.gui.get_azure_config()["deployment"], # Get current deployment name
                    messages=self.messages,
                    tools=openai_tool_definitions if openai_tool_definitions else None
                )

                # Check for errors from get_completion itself
                if not hasattr(response_message, 'role'): # Basic check if it's not a valid message structure
                     self.gui.update_output(f"Failed to get LLM response: {response_message}", "system")
                     break

                # Add response to history *before* processing tool calls
                # Use model_dump() if available (Pydantic v2) or convert manually
                response_dump = {}
                if hasattr(response_message, 'model_dump'):
                     response_dump = response_message.model_dump(exclude_unset=True) # exclude_unset avoids nulls for non-present fields
                else: # Manual conversion for older versions or simple objects
                     response_dump = {
                          "role": getattr(response_message, 'role', 'assistant'),
                          "content": getattr(response_message, 'content', None),
                          "tool_calls": getattr(response_message, 'tool_calls', None)
                     }
                     # Clean up None values
                     response_dump = {k: v for k, v in response_dump.items() if v is not None}


                # Display assistant's textual response (if any)
                if response_message.content:
                    self.gui.update_output(response_message.content, "assistant")

                # 3. Check for Tool Calls
                tool_calls = getattr(response_message, 'tool_calls', None)

                if not tool_calls:
                    # No tool calls, conversation turn ends
                     if not response_message.content: # Handle case where only tool call was expected but didn't happen
                          self.gui.update_output("(No text response and no tool call)", "system")
                     break # Exit the loop


                # Add the assistant message with tool calls to history *before* adding tool responses
                # Ensure the message added includes the tool_calls part
                if "tool_calls" in response_dump and response_dump["tool_calls"]:
                     # Check if message already in history to avoid duplicates if logic runs unexpectedly fast
                     if not self.messages or self.messages[-1] != response_dump:
                           self.messages.append(response_dump)
                elif not response_message.content:
                     # If no content and no tool calls, log and break (already handled above)
                     # This case might indicate an LLM issue or unexpected state
                     self.gui.update_output("(Assistant message has no content or tool calls)", "system")
                     break


                # 4. Execute Tool Calls
                if not self.mcp_handler.is_connected():
                     self.gui.update_output("LLM requested tool call, but not connected to MCP server.", "system")
                     # Add a generic error response for the tool call to messages
                     for tool_call in tool_calls:
                          self.messages.append({
                               "tool_call_id": tool_call.id,
                               "role": "tool",
                               "name": tool_call.function.name,
                               "content": json.dumps({"error": "MCP server not connected."})
                          })
                     continue # Go to the next LLM iteration with the error


                # Process each tool call requested in this turn
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        self.gui.update_output(f"Error decoding arguments for tool {function_name}: {tool_call.function.arguments}", "system")
                        tool_response_content = json.dumps({"error": "Invalid arguments JSON"})
                    else:
                        tool_call_display = f"Tool Call:\n  Name: {function_name}\n  Args: {json.dumps(function_args, indent=2)}"
                        self.gui.update_output(tool_call_display, "tool_call")

                        # Call the actual tool via MCP Handler
                        tool_result = await self.mcp_handler.call_tool(
                            tool_name=function_name,
                            arguments=function_args
                        )
                        # Result should already be serializable JSON/dict from mcp_handler
                        tool_response_content = json.dumps(tool_result)
                        self.gui.update_output(f"Tool Response:\n{json.dumps(tool_result, indent=2)}", "tool_response")


                    # Add the tool response message to the history for the next LLM call
                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_response_content,
                    })
                # Loop back to call LLM again with the tool responses included in messages

            if iterations >= max_iterations:
                self.gui.update_output(f"Reached maximum tool call iterations ({max_iterations}).", "system")

        except Exception as e:
            self.gui.update_output(f"Error during LLM processing: {str(e)}", "system")
            self.gui.update_output(f"Traceback: {traceback.format_exc()}", "system")
        finally:
            self.gui.update_status("Ready") # Reset status bar