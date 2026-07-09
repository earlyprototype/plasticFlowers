
import sys
import os
import time

print("[DEBUG] Script Started", flush=True)

try:
    print("[DEBUG] Importing pydantic...", flush=True)
    from pydantic import BaseModel
    print("[DEBUG] Importing google.genai...", flush=True)
    import google.genai as genai
    print("[DEBUG] Imports done.", flush=True)
except Exception as e:
    print(f"[ERROR] Import failed: {e}", flush=True)
    sys.exit(1)

from dotenv import dotenv_values
try:
    print("[DEBUG] Loading .env...", flush=True)
    config = dotenv_values(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
    key = config.get("GEMINI_API_KEY")
    print(f"[DEBUG] Key found: {bool(key)}", flush=True)
    
    print("[DEBUG] Initializing Client...", flush=True)
    # Force synchronous client
    client = genai.Client(api_key=key)
    
    print("[DEBUG] Generating Content...", flush=True)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Hello"
    )
    print(f"[SUCCESS] Response: {response.text}", flush=True)

except Exception as e:
    print(f"[FAIL] Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
