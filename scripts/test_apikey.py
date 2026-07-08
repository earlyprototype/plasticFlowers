
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import google.genai as genai

# Define paths
root_env_path = Path(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
backend_env_path = Path(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend\.env")

print(f"--- Checking Environment Files ---")

# 1. Check ROOT .env (Used by start scripts)
root_config = {}
if root_env_path.exists():
    print(f"ROOT .env found at: {root_env_path}")
    root_config = dotenv_values(root_env_path)
    root_key = root_config.get("GEMINI_API_KEY", "")
    if root_key:
        print(f"  > Key present: {root_key[:4]}...{root_key[-4:]}")
    else:
        print(f"  > GEMINI_API_KEY is EMPTY or MISSING")
else:
    print(f"ROOT .env NOT found at: {root_env_path}")
    root_key = ""

# 2. Check BACKEND .env (User might be editing this)
backend_config = {}
if backend_env_path.exists():
    print(f"\nBACKEND .env found at: {backend_env_path}")
    backend_config = dotenv_values(backend_env_path)
    backend_key = backend_config.get("GEMINI_API_KEY", "")
    if backend_key:
        print(f"  > Key present: {backend_key[:4]}...{backend_key[-4:]}")
    else:
        print(f"  > GEMINI_API_KEY is EMPTY or MISSING")
else:
    print(f"\nBACKEND .env NOT found (This is fine, usually)")
    backend_key = ""

# 3. Warning if they differ
if root_key and backend_key and root_key != backend_key:
    print("\n[!] WARNING: Root .env and Backend .env have DIFFERENT keys.")
    print("    The startup scripts use the ROOT .env file.")
    print("    Please ensure you updated c:\\Users\\Fab2\\Desktop\\AI\\_plasticFlower\\.env")

# 4. Test the Key from Root .env (since that's what the system uses)
key_to_test = root_key or backend_key
print(f"\n--- Testing Key ({'Root' if root_key else 'Backend'}) ---")

if not key_to_test:
    print("No key found to test.")
    sys.exit(1)

try:
    client = genai.Client(api_key=key_to_test)
    print("Attempting to generate content with model 'gemini-2.0-flash'...")
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Reply with 'API KEY WORKING'"
    )
    print(f"\nSUCCESS:\n{response.text}")
except Exception as e:
    print(f"\nFAILED:\n{e}")
