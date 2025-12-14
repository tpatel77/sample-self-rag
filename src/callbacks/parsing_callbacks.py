
import json
from src.core.callbacks.registry import register_callback

@register_callback("parse_json_output")
def parse_json_output(event_type: str, data: tuple):
    """
    Parses the model response assuming it is JSON.
    Expected data tuple: (response_object,)
    """
    if not data:
        return

    response = data[0]
    
    # 1. Extract the text content from the response object
    # The structure depends on the specific model client, but usually has .text
    content = ""
    if hasattr(response, "text"):
        content = response.text
    elif hasattr(response, "candidates") and response.candidates:
        # Fallback for raw API responses
        content = response.candidates[0].content.parts[0].text
    else:
        content = str(response)

    # 2. Parse JSON
    try:
        # Clean up markdown code blocks if present (e.g. ```json ... ```)
        cleaned_content = content.replace("```json", "").replace("```", "").strip()
        
        parsed_data = json.loads(cleaned_content)
        print(f"\n[Callback] Successfully parsed JSON output:")
        print(json.dumps(parsed_data, indent=2))
        
        # You could also side-effect here, e.g., save to database or update a global store
        
    except json.JSONDecodeError:
        print(f"\n[Callback] Failed to parse output as JSON. Raw content: {content[:100]}...")
