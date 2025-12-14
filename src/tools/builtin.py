"""Built-in tools that ship with the ADK Workflow Framework."""

import json
import os
from typing import Any

from src.tools.registry import register_tool
from src.core.callbacks.registry import register_callback


@register_tool("read_file")
# ... (existing code)

@register_tool("debug_callback")
@register_callback("debug_callback")
def debug_callback(context: Any = None, **kwargs: Any) -> str:
    """
    Simple callback tool for debugging.
    
    Args:
        context: The CallbackContext (if available)
        **kwargs: Event data
        
    Returns:
        Confirmation string
    """
    msg = "DEBUG CALLBACK TRIGGERED"
    print(f"\n*** {msg} ***\n")
    
    if context and hasattr(context, "state"):
        try:
            # Write to state to prove persistence
            name = kwargs.get("tool_name") or kwargs.get("agent_name") or "unknown"
            # Append to log to see sequence? Or just overwrite.
            # "Callback fired for X"
            context.state["debug_log"] = f"Callback fired for {name}" 
            context.state["dummy"] = "callback_value"
            print(f"Saved 'debug_log' and 'dummy' to session state via context!")
        except Exception as e:
            print(f"Failed to save to context: {e}")
            
    return msg
def read_file(file_path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
    
    Returns:
        The contents of the file as a string
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@register_tool("write_file")
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    
    Returns:
        Success message or error
    """
    try:
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@register_tool("list_directory")
def list_directory(directory_path: str) -> str:
    """
    List contents of a directory.
    
    Args:
        directory_path: Path to the directory
    
    Returns:
        JSON list of directory contents
    """
    try:
        contents = os.listdir(directory_path)
        result = []
        for item in contents:
            full_path = os.path.join(directory_path, item)
            result.append({
                "name": item,
                "type": "directory" if os.path.isdir(full_path) else "file",
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None
            })
        return json.dumps(result, indent=2)
    except FileNotFoundError:
        return f"Error: Directory not found: {directory_path}"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@register_tool("format_as_json")
def format_as_json(data: Any, indent: int = 2) -> str:
    """
    Format data as a JSON string.
    
    Args:
        data: Data to format (dict, list, etc.)
        indent: Number of spaces for indentation
    
    Returns:
        JSON formatted string
    """
    try:
        if isinstance(data, str):
            # Try to parse string as JSON first
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                pass
        return json.dumps(data, indent=indent, default=str)
    except Exception as e:
        return f"Error formatting JSON: {str(e)}"


@register_tool("get_env_var")
def get_env_var(var_name: str, default: str = "") -> str:
    """
    Get an environment variable value.
    
    Args:
        var_name: Name of the environment variable
        default: Default value if not found
    
    Returns:
        The environment variable value or default
    """
    try:
        return os.environ.get(var_name, default)
    except Exception as e:
        return f"Error getting env var: {str(e)}"


@register_tool("echo_tool")
def echo_tool(message: str) -> str:
    """
    Simple echo tool for testing.
    
    Args:
        message: The message to echo
        
    Returns:
        The same message
    """
    print(f"Echoing message: {message}")
    return str(message)


