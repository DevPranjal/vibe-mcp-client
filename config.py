# config.py
import os
from dotenv import load_dotenv

def load_configuration():
    """Loads configuration from environment variables."""
    load_dotenv()
    return {
        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
        "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        "default_server_script": "server.py" # Default script name
    }

# Load configuration once when the module is imported
APP_CONFIG = load_configuration()

def get_api_key():
    return APP_CONFIG.get("api_key")

def get_endpoint():
    return APP_CONFIG.get("endpoint")

def get_deployment():
    return APP_CONFIG.get("deployment")

def get_default_server_script():
    return APP_CONFIG.get("default_server_script")