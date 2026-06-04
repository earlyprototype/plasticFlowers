"""Centralised Gemini configuration helpers (ADR-012).

This module provides shared configuration for Gemini API calls to ensure
consistent settings across all agents, particularly the critical
`thinking_budget=0` setting that prevents 60+ second delays.
"""

from __future__ import annotations

from typing import Any, Dict, Type, Union

from google.genai import types
from pydantic import BaseModel

from ..config import get_settings

# Type alias for Pydantic schema or dict
SchemaType = Union[Type[BaseModel], Dict[str, Any], None]


def create_gemini_config(
    *,
    schema: SchemaType = None,
    temperature: float | None = None,
    top_p: float | None = None,
    max_output_tokens: int | None = None,
) -> types.GenerateContentConfig:
    """Create a standardised Gemini GenerateContentConfig.
    
    This helper ensures all Gemini calls use consistent settings, especially:
    - thinking_budget=0: Disables Gemini 2.5 "thinking mode" which adds 60+ seconds
    - response_mime_type: Always JSON for structured output
    
    Args:
        schema: Pydantic model class, dict for response_schema, or None
        temperature: Override default temperature (optional)
        top_p: Override default top_p (optional)
        max_output_tokens: Override default max tokens (optional)
    
    Returns:
        Configured GenerateContentConfig ready for Gemini API calls
    """
    settings = get_settings()
    
    return types.GenerateContentConfig(
        temperature=temperature if temperature is not None else settings.gemini_temperature,
        top_p=top_p if top_p is not None else settings.gemini_top_p,
        max_output_tokens=max_output_tokens if max_output_tokens is not None else settings.gemini_max_output_tokens,
        response_mime_type="application/json",
        response_schema=schema,
        # CRITICAL: Disable thinking mode to prevent 60+ second delays (ADR-012)
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )


__all__ = ["create_gemini_config"]


