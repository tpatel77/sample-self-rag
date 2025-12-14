"""Standard lifecycle callbacks."""

from src.core.callbacks.registry import register_callback

@register_callback("log_model_start")
def log_model_start(event_type: str, data: tuple):
    """Log when a model starts generating."""
    print(f"\n[Callback] Model Generation Started: {event_type}")
    # data[0] is args, data[1] is kwargs usually in the wrapper
    # But wrapper implementation: self._run_callbacks(..., args, kwargs) -> data=(args, kwargs)
    # So data[0] is args (tuple), data[1] is kwargs (dict)
    if len(data) > 0:
        prompts = data[0]
        print(f"  Input: {str(prompts)[:100]}...")

@register_callback("log_model_finish")
def log_model_finish(event_type: str, data: tuple):
    """Log when a model finishes generating."""
    print(f"\n[Callback] Model Generation Finished")
    # data[0] is result
    if len(data) > 0:
        result = data[0]
        # Try to extract text if it's a ModelResponse
        text = str(result)
        if hasattr(result, "text"):
            text = result.text
        print(f"  Output: {text[:100]}...")

@register_callback("log_tool_start")
def log_tool_start(event_type: str, tool_name: str, data: tuple):
    """Log when a tool starts."""
    print(f"\n[Callback] Tool '{tool_name}' Started")
    if len(data) > 0:
        print(f"  Args: {data}")

@register_callback("log_tool_finish")
def log_tool_finish(event_type: str, tool_name: str, data: tuple):
    """Log when a tool finishes."""
    print(f"\n[Callback] Tool '{tool_name}' Finished")
    if len(data) > 0:
        print(f"  Result: {str(data[0])[:100]}...")
