"""Gemini JSON-mode client for Gate 4 builder/gardener agents."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import threading
from typing import Any, Mapping, MutableMapping

from google import genai

from ..config import get_settings
from .llm_utils import create_gemini_config

logger = logging.getLogger(__name__)

SchemaInput = Mapping[str, Any] | type | Any

_FAKE_LLM_ENABLED = bool(
    os.getenv("PLASTICFLOWER_FAKE_LLM", "").strip().lower()
    in {"1", "true", "yes", "on"}
)
if _FAKE_LLM_ENABLED:
    logger.warning("PLASTICFLOWER_FAKE_LLM enabled - using heuristic responses")


class LLMError(RuntimeError):
    """Raised when the Gemini API cannot produce a structured response."""


_CLIENT: genai.Client | None = None
_CLIENT_LOCK = threading.Lock()

# API call counter for debugging quota issues
_CALL_COUNT = 0
_CALL_COUNT_LOCK = threading.Lock()

# Model rotation for quota management
# These models all support 1M context, different RPM limits on free tier
_MODEL_ROTATION_INDEX = 0
_MODEL_ROTATION_LOCK = threading.Lock()
_FALLBACK_MODELS = [
    "gemini-2.5-flash",      # 15 RPM free tier
    "gemini-2.0-flash-exp",  # Experimental, likely higher limits
    "gemini-2.0-flash",      # Stable, similar to 2.5-flash
]

def get_call_count() -> int:
    """Return total API calls made this session."""
    with _CALL_COUNT_LOCK:
        return _CALL_COUNT

def reset_call_count() -> None:
    """Reset API call counter."""
    global _CALL_COUNT
    with _CALL_COUNT_LOCK:
        _CALL_COUNT = 0

def get_next_fallback_model() -> str:
    """Get the next model in rotation (round-robin)."""
    global _MODEL_ROTATION_INDEX
    with _MODEL_ROTATION_LOCK:
        model = _FALLBACK_MODELS[_MODEL_ROTATION_INDEX % len(_FALLBACK_MODELS)]
        _MODEL_ROTATION_INDEX += 1
        logger.info("MODEL_ROTATION: switching to %s (index=%d)", model, _MODEL_ROTATION_INDEX)
        return model


def _get_client(settings) -> genai.Client:
    """Get or create a thread-safe singleton Client instance."""
    global _CLIENT
    if _CLIENT:
        return _CLIENT
    
    with _CLIENT_LOCK:
        if _CLIENT:
            return _CLIENT

        api_key = settings.gemini_api_key.get_secret_value()
        if not api_key:
            raise LLMError("GEMINI_API_KEY is not configured")

        # Unified client handles both AI Studio and Vertex AI (including Express Mode if api_key is provided)
        if settings.vertex_project_id:
            logger.info("Initializing Gemini Client in Vertex AI mode (Express)")
            _CLIENT = genai.Client(
                vertexai=True,
                project=settings.vertex_project_id,
                location=settings.vertex_location,
                api_key=api_key, 
            )
        else:
            logger.info("Initializing Gemini Client in AI Studio mode")
            _CLIENT = genai.Client(
                api_key=api_key
            )
        return _CLIENT


def get_gemini_client() -> genai.Client:
    """Public accessor for the shared Gemini client."""
    return _get_client(get_settings())


async def generate_structured_json(
    prompt: str,
    *,
    schema: SchemaInput,
    model: str | None = None,
) -> Mapping[str, Any]:
    """Call Gemini in JSON mode and return the parsed payload.
    
    Args:
        prompt: The text prompt to send to Gemini.
        schema: Pydantic model or dict defining expected JSON structure.
        model: Optional model name override (defaults to settings.gemini_model).
    """

    stripped = prompt.strip()
    if not stripped:
        raise ValueError("prompt must not be empty")

    if _FAKE_LLM_ENABLED:
        return _fake_structured_json(stripped)

    settings = get_settings()
    # Handle legacy model names or defaults
    model_name = model or settings.gemini_model

    retries = max(0, int(settings.gemini_max_retries))
    attempt = 0
    last_error: Exception | None = None
    models_tried: list[str] = []
    
    client = _get_client(settings)
    current_model = model_name

    while attempt <= retries:
        try:
            return await _generate_content_async(client, stripped, schema, settings, current_model)
        except (asyncio.TimeoutError, Exception) as exc:  # noqa: PERF203 - broad on purpose
            last_error = exc
            error_str = str(exc)
            is_quota_error = "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str
            
            if is_quota_error and current_model not in models_tried:
                # Try next model in rotation for quota errors
                models_tried.append(current_model)
                current_model = get_next_fallback_model()
                logger.warning(
                    "QUOTA ERROR on %s (attempt %s/%s) - switching to %s",
                    models_tried[-1],
                    attempt + 1,
                    retries + 1,
                    current_model,
                )
                await _sleep(0.5)  # Brief pause before trying new model
                # Don't increment attempt counter for model switches
                continue
            
            if attempt >= retries:
                break
            delay = _compute_backoff(attempt)
            logger.warning(
                "Gemini request failed (attempt %s/%s, model=%s): %s",
                attempt + 1,
                retries + 1,
                current_model,
                exc,
            )
            await _sleep(delay)
            attempt += 1

    if models_tried:
        raise LLMError(f"Gemini request failed after trying models: {', '.join(models_tried + [current_model])}") from last_error
    raise LLMError("Gemini request failed after retries") from last_error


async def _generate_content_async(
    client: genai.Client, 
    prompt: str, 
    schema: SchemaInput, 
    settings, 
    model_name: str
) -> Mapping[str, Any]:
    global _CALL_COUNT
    from time import perf_counter
    
    t0 = perf_counter()
    
    # Increment call counter
    with _CALL_COUNT_LOCK:
        _CALL_COUNT += 1
        call_num = _CALL_COUNT
    
    t1 = perf_counter()
    logger.info("LLM_TIMING call=%d lock_ms=%.0f", call_num, (t1-t0)*1000)

    # Configure generation using centralised helper (ADR-012)
    config = create_gemini_config(schema=schema)
    
    t2 = perf_counter()
    logger.info(
        "LLM_TIMING call=%d config_built model=%s prompt_chars=%d timeout=%.0fs",
        call_num, model_name, len(prompt), settings.gemini_request_timeout
    )

    try:
        # The new SDK has an async interface via client.aio
        async with asyncio.timeout(settings.gemini_request_timeout):
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
        t3 = perf_counter()
        logger.info("LLM_TIMING call=%d api_response_ms=%.0f", call_num, (t3-t2)*1000)
    except asyncio.TimeoutError:
        logger.error(
            "Gemini API TIMEOUT after %.1fs (model=%s, prompt_chars=%d, prompt_preview=%s...)", 
            settings.gemini_request_timeout, 
            model_name, 
            len(prompt),
            prompt[:200].replace('\n', ' ')
        )
        raise LLMError(f"Gemini request timed out after {settings.gemini_request_timeout}s")
    except Exception as exc:
        error_str = str(exc)
        if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
            logger.warning("QUOTA LIMIT HIT (model=%s): %s", model_name, exc)
            raise LLMError(f"QUOTA_EXCEEDED: {exc}") from exc
        else:
            logger.error("Gemini API error (model=%s): %s", model_name, exc)
            raise LLMError(f"Gemini request failed: {exc}") from exc

    if not response.text:
         # Check for safety blocks
        if response.candidates and response.candidates[0].finish_reason:
             raise LLMError(f"Blocked: {response.candidates[0].finish_reason}")
        raise LLMError("Gemini returned an empty response")

    text = response.text

    try:
        # Code fences might still be present even in JSON mode sometimes
        text_content = _strip_code_fences(text)
        payload = json.loads(text_content)
    except json.JSONDecodeError as exc:
        logger.error("Gemini returned invalid JSON. Raw response: %s", text)
        # Try to find JSON object if mixed with text
        try:
            match = re.search(r'(\{.*\})', text_content, re.DOTALL)
            if match:
                payload = json.loads(match.group(1))
            else:
                raise exc
        except (json.JSONDecodeError, AttributeError):
             raise LLMError(f"Gemini returned invalid JSON: {exc}") from exc

    if not isinstance(payload, MutableMapping):
        raise LLMError("Gemini JSON payload must be an object")

    return payload


def _compute_backoff(attempt: int) -> float:
    base = 0.5 * 2**attempt
    jitter = random.uniform(0, 0.25)
    return min(4.0, base) + jitter


async def _sleep(delay: float) -> None:
    await asyncio.sleep(delay)


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines:
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _fake_structured_json(prompt: str) -> Mapping[str, Any]:
    """Heuristic, deterministic fallback for offline development."""

    chunk_text = _extract_chunk_text(prompt)
    nodes = _synthesise_nodes(chunk_text)
    relationships = _synthesise_relationships(nodes, chunk_text)
    return {"nodes": nodes, "relationships": relationships}


def _extract_chunk_text(prompt: str) -> str:
    marker = "## TRANSCRIPT CHUNK"
    if marker not in prompt:
        return prompt
    after_marker = prompt.split(marker, 1)[1]
    # Cut at the next section header (## INSTRUCTIONS, ## OUTPUT, ...) so the
    # instruction/output scaffolding never leaks into synthesised nodes.
    next_section = re.search(r"\n##\s", after_marker)
    if next_section:
        after_marker = after_marker[: next_section.start()]
    return after_marker.strip()


def _synthesise_nodes(chunk_text: str) -> list[dict[str, Any]]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"[.!?]+", chunk_text)
        if sentence and sentence.strip()
    ]
    nodes: list[dict[str, Any]] = []
    for idx, sentence in enumerate(sentences[:5]):
        words = [word for word in re.split(r"[^A-Za-z0-9]+", sentence.lower()) if word]
        if not words:
            continue
        label_words = words[: min(4, len(words))]
        label = " ".join(label_words)
        inferred_type = f"{words[0]}_concept" if words else "concept"
        confidence = max(0.5, round(0.85 - idx * 0.05, 2))
        nodes.append(
            {
                "label": label,
                "inferred_type": inferred_type,
                "confidence": confidence,
            }
        )
    if not nodes:
        nodes.append(
            {
                "label": chunk_text.strip()[:30].lower() or "generic concept",
                "inferred_type": "concept",
                "confidence": 0.6,
            }
        )
    return nodes


def _synthesise_relationships(
    nodes: list[dict[str, Any]], chunk_text: str
) -> list[dict[str, Any]]:
    if len(nodes) < 2:
        return []
    relationships: list[dict[str, Any]] = []
    evidence = chunk_text.strip()
    evidence = evidence if len(evidence) <= 200 else f"{evidence[:197]}..."
    for idx in range(len(nodes) - 1):
        relationships.append(
            {
                "source": nodes[idx]["label"],
                "target": nodes[idx + 1]["label"],
                "category": "ASSOCIATIVE",
                "description": "related to",
                "confidence": 0.65,
                "evidence": evidence or "synthetic evidence",
            }
        )
    return relationships


def is_fake_llm_enabled() -> bool:
    return _FAKE_LLM_ENABLED


__all__ = ["generate_structured_json", "LLMError", "is_fake_llm_enabled", "get_gemini_client"]
