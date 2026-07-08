
import os
import json
import urllib.request
import urllib.error
from dotenv import dotenv_values

print("DEBUG: Starting raw HTTP test...", flush=True)

# Load Key
env_path = r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env"
config = dotenv_values(env_path)
api_key = config.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No API Key found", flush=True)
    exit(1)

print(f"DEBUG: Key found: {api_key[:4]}...", flush=True)

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}
data = {
    "contents": [{
        "parts": [{"text": "Hello"}]
    }]
}

try:
    print("DEBUG: Sending request...", flush=True)
    req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        result = response.read().decode("utf-8")
        print("SUCCESS:", flush=True)
        print(result[:200], flush=True)
except urllib.error.HTTPError as e:
    print(f"HTTP ERROR: {e.code} {e.reason}", flush=True)
    print(e.read().decode("utf-8"), flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
