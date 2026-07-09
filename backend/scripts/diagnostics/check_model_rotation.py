"""Check model rotation status and API call patterns.

Usage: python check_model_rotation.py

This script shows:
- Which models are in the rotation
- Current rotation index
- API call count
- Model rate limits on free tier
"""

from app.services.llm import _FALLBACK_MODELS, _MODEL_ROTATION_INDEX, get_call_count

print("\n" + "="*80)
print("MODEL ROTATION STATUS")
print("="*80)

print(f"\nAvailable models (round-robin rotation):")
for idx, model in enumerate(_FALLBACK_MODELS, 1):
    current_marker = " <- NEXT" if idx == (_MODEL_ROTATION_INDEX % len(_FALLBACK_MODELS)) + 1 else ""
    print(f"  {idx}. {model}{current_marker}")

print(f"\nRotation index: {_MODEL_ROTATION_INDEX}")
print(f"Total API calls this session: {get_call_count()}")

print("\n" + "-"*80)
print("FREE TIER RATE LIMITS (requests per minute)")
print("-"*80)
print("  gemini-2.5-flash:     15 RPM")
print("  gemini-2.0-flash-exp: Higher (experimental)")
print("  gemini-2.0-flash:     ~15 RPM")
print("-"*80)

print("\nSTRATEGY:")
print("  When a model hits quota (429/RESOURCE_EXHAUSTED), the system")
print("  automatically switches to the next model in rotation.")
print("  This effectively triples available request capacity.")
print("="*80 + "\n")

