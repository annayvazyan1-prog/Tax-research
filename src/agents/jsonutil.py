"""Lenient JSON parsing — no external deps, so it's unit-testable offline."""

from __future__ import annotations

import json
import re
from typing import Any


def parse_json(text: str, default: Any) -> Any:
    """Best-effort JSON parse; strips code fences and finds the first array/object.
    Models occasionally wrap JSON in prose despite instructions, so we're lenient."""
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return default
    return default
