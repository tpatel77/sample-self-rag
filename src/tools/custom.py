"""Custom tools for your workflows.

Add your custom Python functions here using the @register_tool decorator.
They will be automatically available in workflows as tool agents.
"""

from src.tools.registry import register_tool


@register_tool("text_transform")
def text_transform(text: str, operation: str = "uppercase") -> str:
    """
    Transform text with various operations.
    
    Args:
        text: Input text to transform
        operation: One of 'uppercase', 'lowercase', 'reverse', 'title'
    
    Returns:
        Transformed text
    """
    operations = {
        "uppercase": lambda t: t.upper(),
        "lowercase": lambda t: t.lower(),
        "reverse": lambda t: t[::-1],
        "title": lambda t: t.title(),
    }
    
    transform_func = operations.get(operation, lambda t: t)
    return transform_func(text)


@register_tool("word_count")
def word_count(text: str) -> str:
    """
    Count words, characters, and lines in text.
    
    Args:
        text: Input text to analyze
    
    Returns:
        JSON string with counts
    """
    import json
    
    return json.dumps({
        "words": len(text.split()),
        "characters": len(text),
        "lines": len(text.splitlines()) or 1,
    })


@register_tool("extract_code_blocks")
def extract_code_blocks(text: str) -> str:
    """
    Extract code blocks from markdown-formatted text.
    
    Args:
        text: Text containing markdown code blocks
    
    Returns:
        Extracted code (first block found)
    """
    import re
    
    # Match ```language\ncode\n``` pattern
    pattern = r'```(?:\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    return text  # Return original if no code blocks found
