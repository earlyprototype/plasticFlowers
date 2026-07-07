import sys
import asyncio
# Ensure backend is in path
sys.path.insert(0, r'c:\Users\Fab2\Desktop\AI\_plasticFlower\backend')

from app.config import get_settings
from google import genai
from google.genai import types

async def main():
    s = get_settings()
    api_key = s.gemini_api_key.get_secret_value()
    client = genai.Client(api_key=api_key)

    print("--- 1. Listing ALL available models (raw names) ---")
    try:
        # Pager object, iterate to get all
        for m in client.models.list():
            print(f"ID: {m.name} | Display: {getattr(m, 'display_name', 'N/A')}")
    except Exception as e:
        print(f"List failed: {e}")

    print("\n--- 2. Explicit Generation Test ---")
    
    models_to_test = ["gemini-3-flash", "gemini-3-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"]
    
    for model_name in models_to_test:
        print(f"\nTesting: {model_name}")
        try:
            # Simple synchronous call for verification
            response = client.models.generate_content(
                model=model_name,
                contents="Test."
            )
            print(f"SUCCESS. Response: {response.text[:20]}...")
        except Exception as e:
            print(f"FAILED: {e}")

if __name__ == "__main__":
    # The client.models.list is sync or async? The SDK has both. 
    # client.models.list() is usually sync in this SDK or returns an iterator.
    # generate_content is sync on client.models, async on client.aio.models.
    # We'll use the synchronous methods for this script for simplicity as per SDK usage in previous files.
    
    # Actually, previous files used client.aio.models.generate_content.
    # But list() is usually available on the sync client.
    # Let's check imports. `from google import genai`.
    # Based on migration, we have `google-genai`.
    
    # Re-writing main to be sync since we aren't running a server.
    s = get_settings()
    api_key = s.gemini_api_key.get_secret_value()
    client = genai.Client(api_key=api_key)

    print("--- 1. Listing ALL available models (raw names) ---")
    try:
        for m in client.models.list():
            # The object returned might have .name or .id
            print(f"Model: {m.name}")
    except Exception as e:
        print(f"List failed: {e}")

    print("\n--- 2. Explicit Generation Test ---")
    models_to_test = ["gemini-3-flash", "gemini-3-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"]
    
    for model_name in models_to_test:
        print(f"\nTesting: {model_name}")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Test."
            )
            print(f"SUCCESS: {model_name} works.")
        except Exception as e:
            # We want to see the specific error (404, 400, etc.)
            print(f"FAILED: {model_name} - {e}")



