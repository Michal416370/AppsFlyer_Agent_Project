import json
import re
from typing import Any, Dict

def clean_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    if isinstance(text, dict):
        return text
    if not isinstance(text, str):
        return {}

    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        return {}