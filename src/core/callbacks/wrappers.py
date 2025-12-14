"""
Wrappers for Models and Tools to enable lifecycle callbacks.
"""

from typing import Any, Callable
import inspect

from google.adk.models import BaseLlm
from src.core.callbacks.registry import CallbackRegistry

class CallbackModelWrapper:
    """Wraps an ADK Model object to trigger callbacks."""
    
    def __init__(self, inner_model: BaseLlm, on_start: list[str], on_finish: list[str]):
        self._inner_model = inner_model
        self._on_start = on_start
        self._on_finish = on_finish
        
    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._inner_model, name)
        
        # We only wrap generate_content methods
        if name in ["generate_content", "generate_content_async"]: # Add others if needed
            return self._wrap_method(attr, name)
            
        return attr
            
    def _wrap_method(self, method: Callable, method_name: str) -> Callable:
        """Wraps the generation method."""
        is_async = inspect.iscoroutinefunction(method) or method_name.endswith("async")
        
        if is_async:
            async def wrapped(*args, **kwargs):
                self._run_callbacks(self._on_start, "start", args, kwargs)
                try:
                    result = await method(*args, **kwargs)
                    self._run_callbacks(self._on_finish, "finish", result)
                    return result
                except Exception as e:
                    # Could add on_error callback here too
                    raise e
            return wrapped
        else:
            def wrapped(*args, **kwargs):
                self._run_callbacks(self._on_start, "start", args, kwargs)
                try:
                    result = method(*args, **kwargs)
                    self._run_callbacks(self._on_finish, "finish", result)
                    return result
                except Exception as e:
                    raise e
            return wrapped

    def _run_callbacks(self, callback_names: list[str], event_type: str, *data):
        """Execute registered callbacks."""
        for name in callback_names:
            func = CallbackRegistry.get(name)
            if func:
                try:
                    # We pass event info. 
                    # Signature: (event_type: str, component: str, data: Any)
                    func(event_type=f"model_{event_type}", data=data)
                except Exception as e:
                    print(f"Error in callback '{name}': {e}")


class CallbackToolWrapper:
    """Wraps a tool function to trigger callbacks."""
    
    def __init__(self, tool_func: Callable, name: str, on_start: list[str], on_finish: list[str]):
        self._tool_func = tool_func
        self._name = name
        self._on_start = on_start
        self._on_finish = on_finish
        
        # Mimic the wrapped function's metadata
        self.__name__ = getattr(tool_func, "__name__", "wrapped_tool")
        self.__doc__ = getattr(tool_func, "__doc__", "")
        
    def __call__(self, *args, **kwargs) -> Any:
        self._run_callbacks(self._on_start, "start", args, kwargs)
        try:
            result = self._tool_func(*args, **kwargs)
            self._run_callbacks(self._on_finish, "finish", result)
            return result
        except Exception as e:
            raise e
            
    def _run_callbacks(self, callback_names: list[str], event_type: str, *data):
        """Execute registered callbacks."""
        for name in callback_names:
            func = CallbackRegistry.get(name)
            if func:
                try:
                    func(event_type=f"tool_{event_type}", tool_name=self._name, data=data) 
                except Exception as e:
                    print(f"Error in callback '{name}': {e}")
