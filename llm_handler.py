# llm_handler.py
import json
from openai import AzureOpenAI, APIError, AuthenticationError

class LLMHandler:
    """Handles interactions with the Azure OpenAI LLM."""

    def __init__(self):
        self.llm = None

    def initialize(self, api_key, endpoint):
        """Initializes the Azure OpenAI client."""
        if not api_key or not endpoint:
            print("Warning: Azure OpenAI client not initialized (missing API key or endpoint).")
            self.llm = None
            return False, "Missing API key or endpoint"

        try:
            self.llm = AzureOpenAI(
                api_key=api_key,
                api_version="2024-08-01-preview",
                azure_endpoint=endpoint
            )
            # Perform a simple test call if needed, or just assume success
            print("Azure OpenAI client initialized successfully.")
            return True, "Azure OpenAI client initialized."
        except (APIError, AuthenticationError) as e:
            print(f"Error initializing Azure OpenAI client: {e}")
            self.llm = None
            return False, f"Error initializing Azure OpenAI client: {e}"
        except Exception as e:
            print(f"Unexpected error initializing Azure OpenAI client: {e}")
            self.llm = None
            return False, f"Unexpected error initializing Azure OpenAI client: {e}"

    def is_initialized(self):
        """Checks if the LLM client is initialized."""
        return self.llm is not None

    def format_tools_for_openai(self, mcp_tools):
        """Formats MCP tools list into OpenAI tool format."""
        openai_tools = []
        if not mcp_tools:
            return []
        for tool in mcp_tools:
             # Ensure inputSchema exists and is serializable, default to basic object if not
            parameters = getattr(tool, 'inputSchema', {"type": "object", "properties": {}})
            # Basic validation/handling if parameters are not dict-like
            if not isinstance(parameters, dict):
                 parameters = {"type": "object", "properties": {}} # Fallback

            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters
                }
            })
        return openai_tools

    async def get_completion(self, deployment, messages, tools=None):
        """Gets a completion from the LLM, potentially using tools."""
        if not self.llm:
            raise ValueError("LLM client is not initialized.")

        try:
            if tools:
                response = self.llm.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                )
            else:
                 response = self.llm.chat.completions.create(
                    model=deployment,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800,
                )
            return response.choices[0].message
        except Exception as e:
            print(f"Error during LLM completion: {e}")
            # Return a structured error message if possible
            error_message = {"role": "assistant", "content": f"Error communicating with LLM: {e}"}
            # Mimic the structure of a message object if needed by the caller
            from types import SimpleNamespace
            return SimpleNamespace(role="assistant", content=f"Error communicating with LLM: {e}", tool_calls=None)