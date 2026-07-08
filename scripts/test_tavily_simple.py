import json
import os
import urllib.request
import urllib.error
from pathlib import Path

# Load env to get key
env_path = Path("backend/.env")
api_key = ""
if env_path.exists():
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("TAVILY_API_KEY="):
                api_key = line.strip().split("=", 1)[1]
                break

OUTPUT_FILE = "tavily_test.txt"

def log(msg):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Starting Tavily Simple Test\n")

if not api_key:
    log("❌ TAVILY_API_KEY not found")
    exit(1)

log(f"Testing Tavily API with key: {api_key[:4]}...{api_key[-4:]}")

url = "https://api.tavily.com/search"
payload = {
    "api_key": api_key,
    "query": "DeepMind Gemini",
    "search_depth": "basic",
    "max_results": 1
}

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        if response.status == 200:
            data = json.load(response)
            log("✅ Tavily API Test: SUCCESS")
            log(f"Results found: {len(data.get('results', []))}")
            if data.get('results'):
                log(f"Title: {data['results'][0]['title']}")
        else:
            log(f"❌ Tavily API Test: FAILED (Status {response.status})")

except urllib.error.HTTPError as e:
    log(f"❌ Tavily API Test: FAILED (HTTP {e.code})")
    # log(e.read().decode()) # skipped to avoid decoding issues
except Exception as e:
    log(f"❌ Tavily API Test: FAILED ({e})")
