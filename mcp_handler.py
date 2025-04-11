# mcp_handler.py
import asyncio
import json
import traceback
import anyio
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

class MCPHandler:
    """Handles interactions with the MCP server."""

    def __init__(self, update_callback):
        """
        Initializes the MCPHandler.

        Args:
            update_callback: A function to call for sending status/log updates to the UI.
                             Expected signature: update_callback(message: str, role: str)
        """
        self.session = None
        self._update_callback = update_callback
        self._connection_task = None

    def is_connected(self):
        """Checks if the MCP connection task is active and session object exists."""
        # Check if the session object was successfully created AND
        # if the background task managing the connection is still running.
        return (self.session is not None and
                self._connection_task is not None and
                not self._connection_task.done())

    def _log(self, message, role="system"):
        """Uses the callback to log messages."""
        if self._update_callback:
            self._update_callback(message, role)
        else:
            print(f"[{role.upper()}] {message}") # Fallback to console

    async def _mcp_session_runner(self, server_script_path):
        """The core task that maintains the MCP connection."""
        try:
            self._log(f"Attempting to start MCP server: {server_script_path}")
            # Basic check if the script path seems valid (optional)
            # if not os.path.exists(server_script_path): # Requires importing os
            #     self._log(f"Error: Server script not found at {server_script_path}", "system")
            #     return

            server_params = StdioServerParameters(
                 # Ensure 'uv' is in PATH or provide full path
                command="uv",
                 # Ensure server.py is in the correct relative path or use absolute path
                args=["run", "--with", "mcp", "mcp", "run", server_script_path],
                env=None # Inherit environment
            )
            # Construct the command line string manually for logging
            cmd_parts = [server_params.command] + server_params.args
            self._log(f"Executing command: {' '.join(cmd_parts)}")

            async with stdio_client(server_params) as (read, write):
                self._log("MCP transport initialized.")
                async with ClientSession(read, write) as session:
                    self._log("MCP session created.")
                    self.session = session
                    await session.initialize()
                    self._log("MCP session initialized successfully.")

                    # Optionally list tools upon connection
                    # await self.list_tools()

                    self._update_callback("Connected", "status") # Update status bar via controller

                    # Keep the session context alive. This task will exit automatically
                    # when the stdio_client or ClientSession contexts exit
                    # (e.g., on connection close or error).
                    # We just need to yield control periodically.
                    while True:
                        # This loop will be broken when an exception (like ClosedResourceError)
                        # is raised by the context managers exiting the 'try' block,
                        # or if the task is cancelled.
                        await asyncio.sleep(1) # Sleep for a second to yield control

        except FileNotFoundError:
             self._log(f"Error: 'uv' command not found. Make sure uv is installed and in your PATH.", "system")
        except anyio.ClosedResourceError:
            self._log("MCP connection was closed (likely by the server).", "system")
        except Exception as e:
            self._log(f"MCP connection error: {str(e)}", "system")
            self._log(f"Traceback: {traceback.format_exc()}", "system")
        finally:
            self._log("MCP connection closed.", "system")
            self.session = None
            self._connection_task = None
            self._update_callback("Disconnected", "status") # Update status bar via controller

    async def connect(self, server_script_path):
        """Initiates the connection to the MCP server."""
        if self.is_connected() or self._connection_task:
            self._log("Already connected or connection attempt in progress.", "system")
            return

        self._update_callback("Connecting...", "status") # Update status bar via controller
        # Run the connection logic in a background task
        self._connection_task = asyncio.create_task(
            self._mcp_session_runner(server_script_path),
            name="mcp_session_runner"
        )
        # Optionally, add a callback for when the task finishes/fails
        self._connection_task.add_done_callback(self._handle_connection_task_completion)

    def _handle_connection_task_completion(self, task):
        """Callback executed when the connection task finishes."""
        try:
            task.result() # Raise exceptions if the task failed
            self._log("MCP connection task finished normally.", "system")
        except asyncio.CancelledError:
            self._log("MCP connection task was cancelled.", "system")
        except Exception as e:
            self._log(f"MCP connection task failed: {e}", "system")
            # Log traceback if needed self._log(f"Traceback: {traceback.format_exc()}", "system")
        finally:
            # Ensure state is cleaned up regardless of how the task ended
            self.session = None
            self._connection_task = None
            if self._update_callback: # Check if callback exists before calling
                 self._update_callback("Disconnected", "status")


    async def disconnect(self):
        """Disconnects from the MCP server."""
        if self._connection_task and not self._connection_task.done():
            self._connection_task.cancel()
            try:
                await self._connection_task # Wait for cancellation
            except asyncio.CancelledError:
                self._log("MCP connection cancelled.", "system")
        if self.session and not self.session.is_closed:
            try:
                 # MCP session doesn't have an explicit close, relies on transport closing
                 pass # stdio_client context manager handles process termination
            except Exception as e:
                 self._log(f"Error during MCP session shutdown (ignored): {e}", "system")
        self.session = None
        self._connection_task = None
        self._update_callback("Disconnected", "status")

    async def list_tools(self, log=False):
        """Lists available tools from the connected MCP server."""
        if not self.is_connected():
            self._log("Not connected to MCP server.", "system")
            return None

        try:
            tools_result = await self.session.list_tools()
            tools_list = tools_result.tools
            # Format for display/logging
            tools_dict_for_log = {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": getattr(tool, 'inputSchema', None) # Use getattr for safety
                    } for tool in tools_list
                ]
            }
            # Log the tools if requested
            if log:
                self._log(f"Available tools:\n{json.dumps(tools_dict_for_log, indent=2)}", "system")
            return tools_list # Return the raw list
        except Exception as e:
            self._log(f"Error listing tools: {str(e)}", "system")
            self._log(traceback.format_exc(), "system")
            return None

    async def call_tool(self, tool_name, arguments):
        """Calls a specific tool on the MCP server."""
        if not self.is_connected():
            self._log("Not connected to MCP server.", "system")
            return {"error": "Not connected to MCP server."}

        try:
            # self._log(f"Calling tool: {tool_name} with args: {json.dumps(arguments, indent=2)}", "system")
            tool_result = await self.session.call_tool(tool_name, arguments=arguments)

            # Process result for serialization (handle different content types)
            serializable_content = []
            for item in tool_result.content:
                 if isinstance(item, types.TextContent): # Check specific type
                     serializable_content.append({"type": "text", "text": item.text})
                 elif isinstance(item, types.JsonContent):
                      serializable_content.append({"type": "json", "json": item.json_value})
                 elif isinstance(item, types.ImageContent):
                      # Decide how to represent image: path, base64, etc.
                      # For now, just indicate an image was received.
                      serializable_content.append({"type": "image", "format": item.format, "description": "Image data (not serialized)"})
                 else:
                      # Handle other potential types or just represent as string
                      serializable_content.append({"type": "unknown", "content": str(item)})


            # self._log(f"Tool '{tool_name}' response: {json.dumps(serializable_content, indent=2)}", "system")
            return serializable_content # Return the processed, serializable result

        except Exception as e:
            self._log(f"Error calling tool '{tool_name}': {str(e)}", "system")
            self._log(traceback.format_exc(), "system")
            return {"error": str(e)}