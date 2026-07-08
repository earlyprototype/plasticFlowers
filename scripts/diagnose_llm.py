
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio

# Manually load .env since we can't see it but python can read it
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")
vertex_project = os.getenv("VERTEX_PROJECT_ID")
vertex_location = os.getenv("VERTEX_LOCATION", "us-central1")

print(f"DEBUG: GEMINI_API_KEY present: {bool(api_key)}")
if api_key:
    print(f"DEBUG: GEMINI_API_KEY prefix: {api_key[:4]}...")
print(f"DEBUG: VERTEX_PROJECT_ID: {vertex_project}")

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("ERROR: google-genai not installed")
    sys.exit(1)

async def test_genai():
    print("\n--- Testing Google GenAI Client ---")
    
    if vertex_project:
        print(f"Mode: Vertex AI (Project: {vertex_project})")
        client = genai.Client(
            vertexai=True,
            project=vertex_project,
            location=vertex_location,
            api_key=api_key
        )
    else:
        print("Mode: AI Studio (Direct API Key)")
        client = genai.Client(api_key=api_key)

    try:
        # Simple text generation
        print("Attempting generate_content ('gemini-2.0-flash')...")
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, reply with 'OK'."
        )
        print(f"RESPONSE: {response.text}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_genai())
